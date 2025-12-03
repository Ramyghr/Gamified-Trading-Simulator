"""
FIXED Bot Executor - Added margin level capping and LONG/SHORT support
Save as: app/services/bot/bot_executor.py
"""
import asyncio
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from decimal import Decimal
import logging
import pandas as pd

from app.config.database import SessionLocal
from app.models.bot import Bot, BotTrade, BotLog, BotStatus, TradeAction, PositionSide
from app.models.portfolio import Portfolio, Holding
from app.services.bot.strategy_engine import strategy_engine, StrategySignal
from app.services.market_data_service import enhanced_market_service
from app.services.trading_service import TradingService
from app.services.leverage_trading_service import LeverageTradingService
from app.schemas.order import OrderCreate
from app.models.orders import OrderType, OrderSide, TimeInForce

logger = logging.getLogger(__name__)


def safe_margin_level(equity: Decimal, margin_used: Decimal, max_value: Decimal = Decimal('999999.9999')) -> Decimal:
    """
    Safely calculate margin level with capping to prevent overflow
    
    margin_level = (equity / margin_used) * 100
    Cap at 999999.9999 to fit in Numeric(20, 4)
    """
    if margin_used <= 0:
        return Decimal('0')
    
    margin_level = (equity / margin_used) * Decimal('100')
    
    # Cap to prevent numeric overflow
    if margin_level > max_value:
        logger.warning(f"Margin level {margin_level} capped to {max_value}")
        return max_value
    
    return margin_level


class BotExecutor:
    """
    FIXED: Executes active trading bots with proper margin level handling
    """
    
    def __init__(self):
        self.is_running = False
        self.strategy_engine = strategy_engine
    
    async def run_forever(self, interval_seconds: int = 60):
        """Run executor continuously"""
        self.is_running = True
        logger.info(f"Bot Executor started (interval: {interval_seconds}s)")
        
        while self.is_running:
            try:
                await self.execute_all_active_bots()
                await asyncio.sleep(interval_seconds)
            except Exception as e:
                logger.error(f"Error in bot executor loop: {str(e)}", exc_info=True)
                await asyncio.sleep(interval_seconds)
    
    def stop(self):
        """Stop the executor"""
        self.is_running = False
        logger.info("Bot Executor stopped")
    
    async def execute_all_active_bots(self) -> Dict[str, int]:
        """Execute all active bots"""
        db = SessionLocal()
        
        try:
            active_bots = db.query(Bot).filter(
                Bot.status == BotStatus.ACTIVE
            ).all()
            
            if not active_bots:
                return {"total": 0, "executed": 0, "skipped": 0, "errors": 0}
            
            logger.info(f"Found {len(active_bots)} active bots")
            
            executed = 0
            skipped = 0
            errors = 0
            
            for bot in active_bots:
                try:
                    if not self._is_bot_ready_to_execute(bot):
                        skipped += 1
                        continue
                    
                    result = await self.execute_bot(bot, db)
                    
                    if result:
                        executed += 1
                    else:
                        skipped += 1
                        
                except Exception as e:
                    errors += 1
                    logger.error(f"Error executing bot {bot.id}: {str(e)}", exc_info=True)
                    self._log_bot_event(db, bot.id, "ERROR", f"Execution error: {str(e)}")
            
            db.commit()
            
            logger.info(
                f"Bot execution cycle completed: "
                f"{executed} executed, {skipped} skipped, {errors} errors"
            )
            
            return {
                "total": len(active_bots),
                "executed": executed,
                "skipped": skipped,
                "errors": errors
            }
            
        except Exception as e:
            logger.error(f"Error in execute_all_active_bots: {str(e)}", exc_info=True)
            return {"total": 0, "executed": 0, "skipped": 0, "errors": 0}
        finally:
            db.close()
    
    async def execute_bot(self, bot: Bot, db: Session) -> bool:
        """Execute a single bot - FIXED with proper margin handling"""
        try:
            logger.info(f"Executing bot: ID={bot.id}, Name={bot.name}, Symbol={bot.symbol}")
            
            # Check daily limits
            if not self._check_daily_limits(bot, db):
                self._log_bot_event(
                    db, bot.id, "WARNING",
                    "Daily limits reached, skipping execution"
                )
                return False
            
            # Check and close SL/TP positions
            await self._check_and_close_sl_tp_positions(bot, db)
            
            # Fetch price data
            price_data = await self._fetch_price_data(bot)
            
            if price_data.empty or len(price_data) < 50:
                self._log_bot_event(
                    db, bot.id, "WARNING",
                    "Insufficient price data for analysis"
                )
                return False
            
            # Get current positions
            current_positions = self._get_all_current_positions(bot, db)
            
            # Get trading signal
            signal = self.strategy_engine.execute_strategy(
                bot.strategy_type.value,
                bot.strategy_params,
                price_data,
                {'open_positions': len(current_positions)} if current_positions else None
            )
            
            logger.info(
                f"Bot {bot.id} signal: {signal.action} "
                f"(strength: {signal.strength:.2f}, reason: {signal.reason})"
            )
            
            # Update bot
            bot.last_signal = TradeAction(signal.action)
            bot.last_execution = datetime.utcnow()
            bot.next_execution = self._calculate_next_execution(bot)
            
            # Execute based on signal
            if signal.action == "BUY" and signal.strength >= 0.5:
                if len(current_positions) < bot.max_open_trades:
                    await self._execute_buy_signal(bot, signal, db)
                else:
                    self._log_bot_event(
                        db, bot.id, "WARNING",
                        f"Cannot open new position: {len(current_positions)}/{bot.max_open_trades} positions open"
                    )
            elif signal.action == "SELL" and signal.strength >= 0.5:
                if current_positions:
                    oldest_position = min(current_positions, key=lambda x: x['trade_id'])
                    await self._execute_sell_signal(bot, signal, oldest_position, db)
                else:
                    self._log_bot_event(
                        db, bot.id, "INFO",
                        "Sell signal but no open positions to close"
                    )
            else:
                self._log_bot_event(
                    db, bot.id, "INFO",
                    f"Signal: {signal.action} (strength: {signal.strength:.2f}, open trades: {len(current_positions)})"
                )
            
            bot.updated_at = datetime.utcnow()
            db.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Error executing bot {bot.id}: {str(e)}", exc_info=True)
            bot.status = BotStatus.ERROR
            bot.updated_at = datetime.utcnow()
            db.commit()
            raise
    
    async def _execute_buy_signal(
        self,
        bot: Bot,
        signal: StrategySignal,
        db: Session
    ) -> Optional[BotTrade]:
        """
        FIXED: Execute buy signal with LONG/SHORT tracking
        """
        try:
            position_size = Decimal(str(bot.max_position_size))
            current_price = Decimal(str(signal.price))
            quantity = position_size / current_price
            
            # Determine position side (always LONG for BUY in this context)
            position_side = PositionSide.LONG
            
            logger.info(
                f"Executing BUY (LONG) for bot {bot.id}: "
                f"{quantity:.4f} {bot.symbol} @ ${current_price:.2f}"
            )
            
            if bot.use_leverage:
                leverage_service = LeverageTradingService(db)
                
                position = await leverage_service.open_leveraged_position(
                    user_id=bot.user_id,
                    symbol=bot.symbol,
                    side="LONG",
                    quantity=quantity,
                    leverage=Decimal(str(bot.leverage)),
                    order_type=OrderType.MARKET,
                    stop_loss=self._calculate_stop_loss(current_price, bot.stop_loss_pct),
                    take_profit=self._calculate_take_profit(current_price, bot.take_profit_pct)
                )
                
                bot_trade = BotTrade(
                    bot_id=bot.id,
                    user_id=bot.user_id,
                    symbol=bot.symbol,
                    action=TradeAction.BUY,
                    position_side=position_side,  # NEW
                    quantity=float(quantity),
                    entry_price=float(current_price),
                    trade_value=float(position_size),
                    fee=0.0,
                    leverage_used=float(bot.leverage),
                    margin_used=float(position.margin_used),
                    stop_loss_price=float(position.stop_loss_price) if position.stop_loss_price else None,
                    take_profit_price=float(position.take_profit_price) if position.take_profit_price else None,
                    position_id=position.id,
                    is_open=True,
                    opened_at=datetime.utcnow()
                )
                
            else:
                trading_service = TradingService(db)
                
                order_data = OrderCreate(
                    symbol=bot.symbol,
                    order_type=OrderType.MARKET,
                    side=OrderSide.BUY,
                    quantity=float(quantity),
                    time_in_force=TimeInForce.GTC
                )
                
                order = await trading_service.create_order(bot.user_id, order_data)
                
                if not order:
                    raise Exception("Failed to create order")
                
                bot_trade = BotTrade(
                    bot_id=bot.id,
                    user_id=bot.user_id,
                    symbol=bot.symbol,
                    action=TradeAction.BUY,
                    position_side=position_side,  # NEW
                    quantity=float(order.quantity),
                    entry_price=float(order.average_fill_price or current_price),
                    trade_value=float(order.quantity * (order.average_fill_price or current_price)),
                    fee=float(order.total_fees),
                    leverage_used=1.0,
                    stop_loss_price=self._calculate_stop_loss(current_price, bot.stop_loss_pct),
                    take_profit_price=self._calculate_take_profit(current_price, bot.take_profit_pct),
                    is_open=True,
                    opened_at=datetime.utcnow()
                )
            
            db.add(bot_trade)
            
            # Update bot stats
            bot.total_trades += 1
            
            # Update bot portfolio tracking
            if bot.bot_initial_capital is None:
                bot.bot_initial_capital = position_size
            bot.bot_current_value = (bot.bot_current_value or Decimal('0')) + position_size
            
            db.commit()
            db.refresh(bot_trade)
            
            self._log_bot_event(
                db, bot.id, "INFO",
                f"BUY (LONG) executed: {quantity:.4f} @ ${current_price:.2f}",
                {"trade_id": bot_trade.id, "signal_strength": signal.strength, "position_side": "LONG"}
            )
            
            logger.info(f"Buy trade created for bot {bot.id}: Trade ID={bot_trade.id}")
            return bot_trade
            
        except Exception as e:
            logger.error(f"Error executing buy signal: {str(e)}", exc_info=True)
            self._log_bot_event(db, bot.id, "ERROR", f"Buy execution failed: {str(e)}")
            raise
    
    async def _execute_sell_signal(
        self,
        bot: Bot,
        signal: StrategySignal,
        current_position: Dict,
        db: Session
    ) -> Optional[BotTrade]:
        """FIXED: Execute sell signal with proper error handling"""
        try:
            bot_trade = db.query(BotTrade).filter(
                and_(
                    BotTrade.id == current_position['trade_id'],
                    BotTrade.is_open == True
                )
            ).first()
            
            if not bot_trade:
                logger.warning(f"Bot trade {current_position['trade_id']} not found")
                return None
            
            exit_price = Decimal(str(signal.price))
            entry_price = Decimal(str(bot_trade.entry_price))
            quantity = Decimal(str(bot_trade.quantity))
            
            logger.info(
                f"Executing SELL for bot {bot.id}: "
                f"{quantity:.4f} {bot.symbol} @ ${exit_price:.2f}"
            )
            
            if bot.use_leverage:
                leverage_service = LeverageTradingService(db)
                
                result = await leverage_service.close_leveraged_position(
                    user_id=bot.user_id,
                    position_id=bot_trade.position_id,
                    close_quantity=quantity,
                    exit_price=exit_price
                )
                
                pnl = Decimal(str(result['net_pnl']))
                fee = Decimal(str(result['fee']))
                
            else:
                trading_service = TradingService(db)
                
                order_data = OrderCreate(
                    symbol=bot.symbol,
                    order_type=OrderType.MARKET,
                    side=OrderSide.SELL,
                    quantity=float(quantity),
                    time_in_force=TimeInForce.GTC
                )
                
                order = await trading_service.create_order(bot.user_id, order_data)
                
                if not order:
                    raise Exception("Failed to create sell order")
                
                sell_value = quantity * exit_price
                buy_value = quantity * entry_price
                fee = Decimal(str(order.total_fees))
                pnl = sell_value - buy_value - fee
            
            # Update trade
            bot_trade.exit_price = float(exit_price)
            bot_trade.pnl = float(pnl)
            bot_trade.pnl_pct = float((pnl / (entry_price * quantity)) * 100)
            bot_trade.is_open = False
            bot_trade.closed_at = datetime.utcnow()
            bot_trade.exit_reason = "SIGNAL"
            
            # Update bot stats
            bot.total_pnl += float(pnl)
            bot.total_fees += float(fee)
            
            if pnl > 0:
                bot.winning_trades += 1
            else:
                bot.losing_trades += 1
            
            # Update bot portfolio value
            exit_value = quantity * exit_price
            bot.bot_current_value = (bot.bot_current_value or Decimal('0')) + exit_value - fee
            
            db.commit()
            
            self._log_bot_event(
                db, bot.id, "INFO",
                f"SELL executed: {quantity:.4f} @ ${exit_price:.2f}, P&L: ${pnl:.2f}",
                {
                    "trade_id": bot_trade.id,
                    "pnl": float(pnl),
                    "pnl_pct": float(bot_trade.pnl_pct),
                    "position_side": bot_trade.position_side.value
                }
            )
            
            return bot_trade
            
        except Exception as e:
            logger.error(f"Error executing sell signal: {str(e)}", exc_info=True)
            self._log_bot_event(db, bot.id, "ERROR", f"Sell execution failed: {str(e)}")
            db.rollback()  # IMPORTANT: Rollback on error
            raise
    
    async def _check_and_close_sl_tp_positions(self, bot: Bot, db: Session) -> None:
        """Check and close positions at stop-loss/take-profit"""
        try:
            current_price = await enhanced_market_service.get_price(
                bot.symbol,
                bot.asset_type,
                force_refresh=True
            )
            
            if not current_price:
                return
            
            open_trades = db.query(BotTrade).filter(
                and_(
                    BotTrade.bot_id == bot.id,
                    BotTrade.is_open == True
                )
            ).all()
            
            for trade in open_trades:
                should_close = False
                exit_reason = None
                
                if trade.stop_loss_price and current_price <= trade.stop_loss_price:
                    should_close = True
                    exit_reason = "STOP_LOSS"
                elif trade.take_profit_price and current_price >= trade.take_profit_price:
                    should_close = True
                    exit_reason = "TAKE_PROFIT"
                
                if should_close:
                    await self._close_position(trade, current_price, exit_reason, db)
                    
        except Exception as e:
            logger.error(f"Error checking SL/TP: {str(e)}", exc_info=True)
    
    async def _close_position(
        self,
        trade: BotTrade,
        exit_price: float,
        exit_reason: str,
        db: Session
    ) -> None:
        """Close a position"""
        try:
            logger.info(f"Closing position {trade.id} @ ${exit_price:.2f} ({exit_reason})")
            
            if trade.leverage_used > 1.0:
                leverage_service = LeverageTradingService(db)
                
                result = await leverage_service.close_leveraged_position(
                    user_id=trade.user_id,
                    position_id=trade.position_id,
                    exit_price=Decimal(str(exit_price))
                )
                
                pnl = result.get('net_pnl', 0)
                fee = result.get('fee', 0)
                
            else:
                trading_service = TradingService(db)
                
                order_data = OrderCreate(
                    symbol=trade.symbol,
                    order_type=OrderType.MARKET,
                    side=OrderSide.SELL,
                    quantity=float(trade.quantity),
                    time_in_force=TimeInForce.GTC
                )
                
                order = await trading_service.create_order(trade.user_id, order_data)
                
                sell_value = trade.quantity * exit_price
                buy_value = trade.quantity * trade.entry_price
                fee = order.total_fees
                pnl = sell_value - buy_value - fee
            
            # Update trade
            trade.exit_price = exit_price
            trade.pnl = pnl
            trade.pnl_pct = (pnl / (trade.entry_price * trade.quantity)) * 100 if trade.entry_price else 0
            trade.is_open = False
            trade.closed_at = datetime.utcnow()
            trade.exit_reason = exit_reason
            
            # Update bot
            bot = db.query(Bot).filter(Bot.id == trade.bot_id).first()
            if bot:
                bot.total_pnl += pnl
                bot.total_fees += fee
                
                if pnl > 0:
                    bot.winning_trades += 1
                else:
                    bot.losing_trades += 1
            
            self._log_bot_event(
                db, trade.bot_id, "INFO",
                f"Position closed: {exit_reason} @ ${exit_price:.2f}, P&L: ${pnl:.2f}",
                {"trade_id": trade.id, "pnl": pnl, "exit_reason": exit_reason}
            )
            
        except Exception as e:
            logger.error(f"Error closing position {trade.id}: {str(e)}", exc_info=True)
            self._log_bot_event(
                db, trade.bot_id, "ERROR",
                f"Failed to close position: {str(e)}"
            )
    
    def _get_all_current_positions(self, bot: Bot, db: Session) -> List[Dict]:
        """Get all open positions"""
        open_trades = db.query(BotTrade).filter(
            and_(
                BotTrade.bot_id == bot.id,
                BotTrade.is_open == True
            )
        ).all()
        
        return [{
            'trade_id': trade.id,
            'position_id': trade.id,
            'quantity': trade.quantity,
            'entry_price': trade.entry_price,
            'stop_loss_price': trade.stop_loss_price,
            'take_profit_price': trade.take_profit_price,
            'position_side': trade.position_side.value,
            'is_open': True
        } for trade in open_trades]
    
    async def _fetch_price_data(self, bot: Bot) -> pd.DataFrame:
        """Fetch historical price data"""
        try:
            from app.services.bot.historical_data_service import historical_data_service
            
            lookback_days = 30
            interval_map = {
                "1m": "1m", "5m": "5m", "15m": "15m", "30m": "30m",
                "1h": "1h", "4h": "4h", "1d": "1d"
            }
            
            fetch_interval = interval_map.get(bot.interval, "1h")
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=lookback_days)
            
            df = await historical_data_service.get_historical_data(
                symbol=bot.symbol,
                start_date=start_date,
                end_date=end_date,
                interval=fetch_interval,
                asset_class=bot.asset_type.lower() if bot.asset_type else "stock"  # ← ADD THIS
            )
            
            if not df.empty:
                current_price = await enhanced_market_service.get_price(
                    bot.symbol,
                    bot.asset_type,
                    force_refresh=True
                )
                
                if current_price:
                    latest_close = float(df.iloc[-1]['close'])
                    if abs(current_price - latest_close) / latest_close > 0.001:
                        new_row = {
                            'timestamp': datetime.utcnow(),
                            'open': latest_close,
                            'high': max(current_price, latest_close),
                            'low': min(current_price, latest_close),
                            'close': current_price,
                            'volume': df.iloc[-1]['volume']
                        }
                        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            
            return df
            
        except Exception as e:
            logger.error(f"Error fetching price data: {str(e)}", exc_info=True)
            return pd.DataFrame()
    
    def _is_bot_ready_to_execute(self, bot: Bot) -> bool:
        """Check if bot is ready"""
        if bot.next_execution is None:
            return True
        return datetime.utcnow() >= bot.next_execution
    
    def _calculate_next_execution(self, bot: Bot) -> datetime:
        """Calculate next execution time"""
        interval_map = {
            "1m": timedelta(minutes=1),
            "5m": timedelta(minutes=5),
            "15m": timedelta(minutes=15),
            "30m": timedelta(minutes=30),
            "1h": timedelta(hours=1),
            "4h": timedelta(hours=4),
            "1d": timedelta(days=1)
        }
        
        interval = interval_map.get(bot.interval, timedelta(minutes=5))
        return datetime.utcnow() + interval
    
    def _check_daily_limits(self, bot: Bot, db: Session) -> bool:
        """Check daily limits"""
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        today_trades = db.query(BotTrade).filter(
            and_(
                BotTrade.bot_id == bot.id,
                BotTrade.opened_at >= today_start
            )
        ).count()
        
        if today_trades >= bot.max_daily_trades:
            return False
        
        today_closed_trades = db.query(BotTrade).filter(
            and_(
                BotTrade.bot_id == bot.id,
                BotTrade.closed_at >= today_start,
                BotTrade.is_open == False
            )
        ).all()
        
        daily_pnl = sum(trade.pnl for trade in today_closed_trades)
        
        if daily_pnl < -bot.max_daily_loss:
            return False
        
        return True
    
    def _calculate_stop_loss(
        self,
        entry_price: Decimal,
        stop_loss_pct: Optional[float]
    ) -> Optional[float]:
        """Calculate stop loss"""
        if not stop_loss_pct:
            return None
        return float(entry_price * (1 - Decimal(str(stop_loss_pct)) / 100))
    
    def _calculate_take_profit(
        self,
        entry_price: Decimal,
        take_profit_pct: Optional[float]
    ) -> Optional[float]:
        """Calculate take profit"""
        if not take_profit_pct:
            return None
        return float(entry_price * (1 + Decimal(str(take_profit_pct)) / 100))
    
    def _log_bot_event(
        self,
        db: Session,
        bot_id: int,
        level: str,
        message: str,
        details: Optional[Dict] = None
    ) -> None:
        """Log bot event"""
        try:
            log = BotLog(
                bot_id=bot_id,
                level=level,
                message=message,
                details=details,
                timestamp=datetime.utcnow()
            )
            db.add(log)
            db.flush()
        except Exception as e:
            logger.error(f"Failed to log event: {str(e)}")


# Singleton
bot_executor = BotExecutor()


async def run_bot_worker():
    """Run as standalone worker"""
    logger.info("Starting Bot Executor Worker...")
    
    try:
        await bot_executor.run_forever(interval_seconds=60)
    except KeyboardInterrupt:
        logger.info("Shutdown signal received")
        bot_executor.stop()
    except Exception as e:
        logger.error(f"Bot executor crashed: {str(e)}", exc_info=True)


if __name__ == "__main__":
    import sys
    sys.path.append(".")
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    asyncio.run(run_bot_worker()) 