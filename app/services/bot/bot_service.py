"""
Bot Service - Bot management and backtesting
Save as: app/services/bot/bot_service.py
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal
import logging
import pandas as pd
import numpy as np

from app.models.bot import Bot, BotTrade, BotBacktest, BotLog, BotStatus, BotStrategyType, TradeAction
from app.models.portfolio import Portfolio
from app.schemas.bot import BotCreate, BotUpdate, BacktestRequest
from app.services.bot.strategy_engine import strategy_engine, StrategySignal
from app.services.market_data_service import enhanced_market_service

logger = logging.getLogger(__name__)


class BotService:
    """Bot management and backtesting service"""
    
    def __init__(self, db: Session):
        self.db = db
        self.strategy_engine = strategy_engine
    
    # ==================== Bot CRUD Operations ====================
    
    def create_bot(self, user_id: int, bot_data: BotCreate) -> Bot:
        """Create a new trading bot"""
        try:
            portfolio = self.db.query(Portfolio).filter(
                Portfolio.user_id == user_id
            ).first()
            
            if not portfolio:
                raise ValueError("Portfolio not found")
            
            bot = Bot(
                user_id=user_id,
                portfolio_id=portfolio.id,
                name=bot_data.name,
                description=bot_data.description,
                strategy_type=bot_data.strategy_type,
                strategy_params=bot_data.strategy_params,
                symbol=bot_data.symbol.upper(),
                asset_type=bot_data.asset_type,
                max_position_size=bot_data.max_position_size,
                max_open_trades=getattr(bot_data, 'max_open_trades', 3),
                stop_loss_pct=bot_data.stop_loss_pct,
                take_profit_pct=bot_data.take_profit_pct,
                max_daily_trades=bot_data.max_daily_trades,
                max_daily_loss=bot_data.max_daily_loss,
                use_leverage=bot_data.use_leverage,
                leverage=bot_data.leverage,
                interval=bot_data.interval,
                status=BotStatus.PAUSED,
                bot_initial_capital=bot_data.max_position_size * 3,  # Initial capital = 3 positions worth
                bot_current_value=bot_data.max_position_size * 3,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            self.db.add(bot)
            self.db.commit()
            self.db.refresh(bot)
            
            self._log_bot_event(bot.id, "INFO", f"Bot '{bot.name}' created successfully")
            
            logger.info(f"Bot created: ID={bot.id}, Name={bot.name}")
            return bot
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create bot: {str(e)}", exc_info=True)
            raise
    
    def update_bot(self, user_id: int, bot_id: int, bot_data: BotUpdate) -> Bot:
        """Update bot configuration"""
        try:
            bot = self.db.query(Bot).filter(
                and_(Bot.id == bot_id, Bot.user_id == user_id)
            ).first()
            
            if not bot:
                raise ValueError("Bot not found")
            
            # Only allow updates if bot is paused or stopped
            if bot.status == BotStatus.ACTIVE:
                raise ValueError("Cannot update active bot. Pause it first.")
            
            # Update fields
            update_fields = [
                'name', 'description', 'strategy_params', 'max_position_size',
                'stop_loss_pct', 'take_profit_pct', 'max_daily_trades',
                'max_daily_loss', 'leverage', 'interval'
            ]
            
            for field in update_fields:
                value = getattr(bot_data, field, None)
                if value is not None:
                    setattr(bot, field, value)
            
            # Update max_open_trades if present
            if hasattr(bot_data, 'max_open_trades') and bot_data.max_open_trades is not None:
                bot.max_open_trades = bot_data.max_open_trades
            
            bot.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(bot)
            
            self._log_bot_event(bot.id, "INFO", "Bot configuration updated")
            
            logger.info(f"Bot updated: ID={bot.id}")
            return bot
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update bot: {str(e)}", exc_info=True)
            raise
    
    def delete_bot(self, user_id: int, bot_id: int) -> bool:
        """Delete a bot"""
        try:
            bot = self.db.query(Bot).filter(
                and_(Bot.id == bot_id, Bot.user_id == user_id)
            ).first()
            
            if not bot:
                raise ValueError("Bot not found")
            
            # Stop bot if active
            if bot.status == BotStatus.ACTIVE:
                self.stop_bot(user_id, bot_id)
            
            # Delete bot (cascades to trades, backtests, logs)
            self.db.delete(bot)
            self.db.commit()
            
            logger.info(f"Bot deleted: ID={bot_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete bot: {str(e)}", exc_info=True)
            raise
    
    def get_bot(self, user_id: int, bot_id: int) -> Optional[Bot]:
        """Get bot by ID"""
        return self.db.query(Bot).filter(
            and_(Bot.id == bot_id, Bot.user_id == user_id)
        ).first()
    
    def get_user_bots(
        self,
        user_id: int,
        status: Optional[BotStatus] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Bot]:
        """Get user's bots with optional filters"""
        query = self.db.query(Bot).filter(Bot.user_id == user_id)
        
        if status:
            query = query.filter(Bot.status == status)
        
        return query.order_by(desc(Bot.created_at)).limit(limit).offset(offset).all()
    
    # ==================== Bot Control ====================
    
    def start_bot(self, user_id: int, bot_id: int) -> Bot:
        """Start/activate a bot"""
        try:
            bot = self.get_bot(user_id, bot_id)
            if not bot:
                raise ValueError("Bot not found")
            
            if bot.status == BotStatus.ACTIVE:
                return bot
            
            # Validate bot configuration
            self._validate_bot_config(bot)
            
            bot.status = BotStatus.ACTIVE
            bot.activated_at = datetime.utcnow()
            bot.stopped_at = None
            bot.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(bot)
            
            self._log_bot_event(bot.id, "INFO", "Bot activated")
            
            logger.info(f"Bot started: ID={bot.id}")
            return bot
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to start bot: {str(e)}", exc_info=True)
            raise
    
    def pause_bot(self, user_id: int, bot_id: int) -> Bot:
        """Pause a bot"""
        try:
            bot = self.get_bot(user_id, bot_id)
            if not bot:
                raise ValueError("Bot not found")
            
            bot.status = BotStatus.PAUSED
            bot.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(bot)
            
            self._log_bot_event(bot.id, "INFO", "Bot paused")
            
            logger.info(f"Bot paused: ID={bot.id}")
            return bot
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to pause bot: {str(e)}", exc_info=True)
            raise
    
    def stop_bot(self, user_id: int, bot_id: int) -> Bot:
        """Stop a bot and close any open positions"""
        try:
            bot = self.get_bot(user_id, bot_id)
            if not bot:
                raise ValueError("Bot not found")
            
            # Close open positions
            open_trades = self.db.query(BotTrade).filter(
                and_(BotTrade.bot_id == bot_id, BotTrade.is_open == True)
            ).all()
            
            for trade in open_trades:
                # In a real implementation, this would execute actual trades
                trade.is_open = False
                trade.closed_at = datetime.utcnow()
                trade.exit_reason = "BOT_STOPPED"
            
            bot.status = BotStatus.STOPPED
            bot.stopped_at = datetime.utcnow()
            bot.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(bot)
            
            self._log_bot_event(bot.id, "INFO", f"Bot stopped. Closed {len(open_trades)} positions")
            
            logger.info(f"Bot stopped: ID={bot.id}")
            return bot
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to stop bot: {str(e)}", exc_info=True)
            raise
    
    # ==================== Backtesting ====================
    
    async def run_backtest(
        self,
        user_id: int,
        bot_id: int,
        backtest_request: BacktestRequest
    ) -> BotBacktest:
        """
        Run backtest simulation on historical data
        """
        try:
            bot = self.get_bot(user_id, bot_id)
            if not bot:
                raise ValueError("Bot not found")
            
            logger.info(
                f"Starting backtest for bot {bot_id}: "
                f"{backtest_request.start_date} to {backtest_request.end_date}"
            )
            
            # Create backtest record
            backtest = BotBacktest(
                bot_id=bot_id,
                user_id=user_id,
                start_date=backtest_request.start_date,
                end_date=backtest_request.end_date,
                initial_capital=backtest_request.initial_capital,
                status="RUNNING",
                started_at=datetime.utcnow()
            )
            
            self.db.add(backtest)
            self.db.commit()
            self.db.refresh(backtest)
            
            try:
                # Fetch historical data
                historical_data = await self._fetch_historical_data(
                    bot.symbol,
                    bot.asset_type,
                    backtest_request.start_date,
                    backtest_request.end_date,
                    bot.interval
                )
                
                if historical_data.empty:
                    raise ValueError("No historical data available")
                
                # Run backtest simulation
                results = self._simulate_backtest(
                    bot,
                    historical_data,
                    backtest_request.initial_capital
                )
                
                # Update backtest with results
                backtest.final_capital = results['final_capital']
                backtest.total_return = results['total_return']
                backtest.total_return_pct = results['total_return_pct']
                backtest.total_trades = results['total_trades']
                backtest.winning_trades = results['winning_trades']
                backtest.losing_trades = results['losing_trades']
                backtest.win_rate = results['win_rate']
                backtest.avg_win = results['avg_win']
                backtest.avg_loss = results['avg_loss']
                backtest.largest_win = results['largest_win']
                backtest.largest_loss = results['largest_loss']
                backtest.profit_factor = results['profit_factor']
                backtest.sharpe_ratio = results['sharpe_ratio']
                backtest.max_drawdown = results['max_drawdown']
                backtest.max_drawdown_pct = results['max_drawdown_pct']
                backtest.performance_metrics = results['performance_metrics']
                backtest.trade_history = results['trade_history']
                backtest.status = "COMPLETED"
                backtest.completed_at = datetime.utcnow()
                
                self.db.commit()
                self.db.refresh(backtest)
                
                self._log_bot_event(
                    bot.id,
                    "INFO",
                    f"Backtest completed: {results['total_trades']} trades, "
                    f"{results['total_return_pct']:.2f}% return"
                )
                
                logger.info(f"Backtest completed: ID={backtest.id}")
                return backtest
                
            except Exception as e:
                backtest.status = "FAILED"
                backtest.error_message = str(e)
                backtest.completed_at = datetime.utcnow()
                self.db.commit()
                raise
                
        except Exception as e:
            self.db.rollback()
            logger.error(f"Backtest failed: {str(e)}", exc_info=True)
            raise
    
    def _simulate_backtest(
        self,
        bot: Bot,
        historical_data: pd.DataFrame,
        initial_capital: float
    ) -> Dict[str, Any]:
        """
        FIXED: Simulate bot trading with multiple positions and LONG/SHORT tracking
        """
        capital = Decimal(str(initial_capital))
        open_positions = []  # List of open position dicts
        trades = []
        equity_curve = [float(capital)]
        
        max_open_trades = getattr(bot, 'max_open_trades', 3)
        
        # Strategy-specific settings
        is_rapid_test = bot.strategy_type == BotStrategyType.RAPID_TEST
        signal_strength_threshold = 0.2 if is_rapid_test else 0.3
        position_size_percent = 0.15 if is_rapid_test else 0.30
        
        logger.info(f"Backtest: capital=${initial_capital}, max_open={max_open_trades}")
        
        # Process each candle
        for i in range(len(historical_data)):
            if i < 50:
                equity_curve.append(float(capital))
                continue
            
            window_data = historical_data.iloc[:i+1].copy()
            
            signal = self.strategy_engine.execute_strategy(
                bot.strategy_type.value,
                bot.strategy_params,
                window_data,
                {'open_positions': len(open_positions)} if open_positions else None
            )
            
            current_price = Decimal(str(signal.price))
            
            # === 1. CHECK STOP-LOSS AND TAKE-PROFIT ===
            positions_to_close = []
            for pos in open_positions:
                entry_price = Decimal(str(pos['entry_price']))
                position_side = pos.get('position_side', 'LONG')
                
                if position_side == 'LONG':
                    # For LONG: SL below entry, TP above entry
                    if bot.stop_loss_pct:
                        sl_price = entry_price * (Decimal('1') - Decimal(str(bot.stop_loss_pct)) / Decimal('100'))
                        if current_price <= sl_price:
                            positions_to_close.append((pos, 'STOP_LOSS'))
                            continue
                    
                    if bot.take_profit_pct:
                        tp_price = entry_price * (Decimal('1') + Decimal(str(bot.take_profit_pct)) / Decimal('100'))
                        if current_price >= tp_price:
                            positions_to_close.append((pos, 'TAKE_PROFIT'))
                            continue
                else:  # SHORT
                    # For SHORT: SL above entry, TP below entry
                    if bot.stop_loss_pct:
                        sl_price = entry_price * (Decimal('1') + Decimal(str(bot.stop_loss_pct)) / Decimal('100'))
                        if current_price >= sl_price:
                            positions_to_close.append((pos, 'STOP_LOSS'))
                            continue
                    
                    if bot.take_profit_pct:
                        tp_price = entry_price * (Decimal('1') - Decimal(str(bot.take_profit_pct)) / Decimal('100'))
                        if current_price <= tp_price:
                            positions_to_close.append((pos, 'TAKE_PROFIT'))
                            continue
            
            # === 2. CLOSE POSITIONS ===
            for pos, reason in positions_to_close:
                exit_price = current_price
                quantity = Decimal(str(pos['quantity']))
                entry_price = Decimal(str(pos['entry_price']))
                position_side = pos.get('position_side', 'LONG')
                
                position_value = quantity * exit_price
                fee = position_value * Decimal("0.001")
                
                # Calculate PnL based on position side
                if position_side == 'LONG':
                    pnl = position_value - entry_price * quantity - fee
                else:  # SHORT
                    pnl = entry_price * quantity - position_value - fee
                
                capital += position_value - fee
                
                entry_timestamp = historical_data.iloc[pos['entry_idx']]['timestamp']
                exit_timestamp = historical_data.iloc[i]['timestamp']
                
                trades.append({
                    'entry_price': float(entry_price),
                    'exit_price': float(exit_price),
                    'quantity': float(quantity),
                    'position_side': position_side,
                    'pnl': float(pnl),
                    'pnl_pct': float((pnl / (entry_price * quantity)) * 100),
                    'exit_reason': reason,
                    'entry_date': str(entry_timestamp),
                    'exit_date': str(exit_timestamp)
                })
                
                open_positions.remove(pos)
            
            # === 3. EXECUTE NEW SIGNALS ===
            if signal.action == "BUY" and signal.strength >= signal_strength_threshold:
                if len(open_positions) < max_open_trades:
                    position_size = min(
                        Decimal(str(bot.max_position_size)),
                        capital * Decimal(str(position_size_percent))
                    )
                    
                    if position_size > Decimal('10'):
                        quantity = position_size / current_price
                        fee = position_size * Decimal("0.001")
                        
                        if capital >= (position_size + fee):
                            position = {
                                'entry_price': float(current_price),
                                'quantity': float(quantity),
                                'position_side': 'LONG',
                                'entry_capital': float(capital),
                                'entry_idx': i
                            }
                            
                            open_positions.append(position)
                            capital -= (position_size + fee)
                            
                            logger.debug(
                                f"Opened LONG #{len(open_positions)}: "
                                f"{quantity:.4f} @ ${current_price:.2f}"
                            )
            
            elif signal.action == "SELL" and signal.strength >= signal_strength_threshold:
                if open_positions:
                    # Close oldest LONG position or open SHORT
                    long_positions = [p for p in open_positions if p.get('position_side') == 'LONG']
                    
                    if long_positions:
                        # Close oldest LONG
                        pos = min(long_positions, key=lambda x: x['entry_idx'])
                        exit_price = current_price
                        quantity = Decimal(str(pos['quantity']))
                        entry_price = Decimal(str(pos['entry_price']))
                        
                        position_value = quantity * exit_price
                        fee = position_value * Decimal("0.001")
                        pnl = position_value - entry_price * quantity - fee
                        capital += position_value - fee
                        
                        trades.append({
                            'entry_price': float(entry_price),
                            'exit_price': float(exit_price),
                            'quantity': float(quantity),
                            'position_side': 'LONG',
                            'pnl': float(pnl),
                            'pnl_pct': float((pnl / (entry_price * quantity)) * 100),
                            'exit_reason': 'SIGNAL',
                            'entry_date': str(historical_data.iloc[pos['entry_idx']]['timestamp']),
                            'exit_date': str(historical_data.iloc[i]['timestamp'])
                        })
                        
                        open_positions.remove(pos)
            
            # === 4. UPDATE EQUITY CURVE ===
            open_positions_value = Decimal('0')
            for p in open_positions:
                quantity = Decimal(str(p['quantity']))
                entry_price = Decimal(str(p['entry_price']))
                position_side = p.get('position_side', 'LONG')
                
                if position_side == 'LONG':
                    open_positions_value += quantity * current_price
                else:  # SHORT
                    # For short: profit = entry_value - current_value
                    open_positions_value += Decimal('2') * entry_price * quantity - quantity * current_price
            
            equity_curve.append(float(capital + open_positions_value))
        
        # === 5. CLOSE REMAINING POSITIONS ===
        if open_positions:
            final_price = Decimal(str(historical_data.iloc[-1]['close']))
            for pos in open_positions:
                quantity = Decimal(str(pos['quantity']))
                entry_price = Decimal(str(pos['entry_price']))
                position_side = pos.get('position_side', 'LONG')
                
                position_value = quantity * final_price
                fee = position_value * Decimal("0.001")
                
                if position_side == 'LONG':
                    pnl = position_value - entry_price * quantity - fee
                else:
                    pnl = entry_price * quantity - position_value - fee
                
                capital += position_value - fee
                
                trades.append({
                    'entry_price': float(entry_price),
                    'exit_price': float(final_price),
                    'quantity': float(quantity),
                    'position_side': position_side,
                    'pnl': float(pnl),
                    'pnl_pct': float((pnl / (entry_price * quantity)) * 100),
                    'exit_reason': 'END_OF_BACKTEST',
                    'entry_date': str(historical_data.iloc[pos['entry_idx']]['timestamp']),
                    'exit_date': str(historical_data.iloc[-1]['timestamp'])
                })
        
        logger.info(f"Backtest completed: {len(trades)} trades")
        
        # === 6. CALCULATE METRICS ===
        final_capital = float(capital)
        total_return = final_capital - initial_capital
        total_return_pct = (total_return / initial_capital) * 100
        
        winning_trades = [t for t in trades if t['pnl'] > 0]
        losing_trades = [t for t in trades if t['pnl'] <= 0]
        
        win_rate = (len(winning_trades) / len(trades) * 100) if trades else 0
        avg_win = float(np.mean([t['pnl'] for t in winning_trades])) if winning_trades else 0.0
        avg_loss = float(np.mean([t['pnl'] for t in losing_trades])) if losing_trades else 0.0
        largest_win = float(max([t['pnl'] for t in winning_trades])) if winning_trades else 0.0
        largest_loss = float(min([t['pnl'] for t in losing_trades])) if losing_trades else 0.0
        
        total_wins = sum([t['pnl'] for t in winning_trades])
        total_losses = abs(sum([t['pnl'] for t in losing_trades]))
        profit_factor = float(total_wins / total_losses) if total_losses > 0 else 0.0
        
        # Sharpe ratio
        returns = np.diff(equity_curve) / np.array(equity_curve[:-1])
        sharpe_ratio = float((np.mean(returns) / np.std(returns) * np.sqrt(252))) if len(returns) > 0 and np.std(returns) > 0 else 0.0
        
        # Max drawdown
        peak = np.maximum.accumulate(equity_curve)
        drawdown = (np.array(equity_curve) - peak) / peak * 100
        max_drawdown = float(np.min(drawdown))
        max_drawdown_pct = abs(max_drawdown)
        
        return {
            'final_capital': final_capital,
            'total_return': total_return,
            'total_return_pct': total_return_pct,
            'total_trades': len(trades),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'largest_win': largest_win,
            'largest_loss': largest_loss,
            'profit_factor': profit_factor,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'max_drawdown_pct': max_drawdown_pct,
            'performance_metrics': {
                'equity_curve': [float(x) for x in equity_curve],
                'returns': [float(x) for x in returns.tolist()] if len(returns) > 0 else []
            },
            'trade_history': trades
        }
    
    async def _fetch_historical_data(
        self,
        symbol: str,
        asset_type: str,
        start_date: datetime,
        end_date: datetime,
        interval: str
    ) -> pd.DataFrame:
        """
        Fetch historical price data from real sources
        """
        from app.services.bot.historical_data_service import historical_data_service
        
        try:
            logger.info(f"Fetching historical data for {symbol} from {start_date.date()} to {end_date.date()}")
            
            data = await historical_data_service.get_historical_data(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                interval=interval
            )
            
            if data.empty:
                raise ValueError(f"No historical data available for {symbol}")
            
            logger.info(f"✓ Fetched {len(data)} candles for {symbol}")
            return data
            
        except Exception as e:
            logger.error(f"Error fetching historical data: {str(e)}")
            raise
    
    # ==================== Helper Methods ====================
    
    def _validate_bot_config(self, bot: Bot) -> None:
        """Validate bot configuration before starting"""
        if not bot.strategy_params:
            # Allow RAPID_TEST to have empty strategy_params
            if bot.strategy_type != BotStrategyType.RAPID_TEST:
                raise ValueError("Bot strategy parameters not configured")
        
        if bot.max_position_size <= 0:
            raise ValueError("Invalid max position size")
        
        # Validate max_open_trades is set
        if not hasattr(bot, 'max_open_trades') or bot.max_open_trades is None:
            bot.max_open_trades = 3  # Set default
        
        # Add more validations as needed
    
    def _log_bot_event(
        self,
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
            self.db.add(log)
            self.db.commit()
        except Exception as e:
            logger.error(f"Failed to log event: {str(e)}")
    
    def get_bot_logs(
        self,
        user_id: int,
        bot_id: int,
        limit: int = 100
    ) -> List[BotLog]:
        """Get bot execution logs"""
        bot = self.get_bot(user_id, bot_id)
        if not bot:
            raise ValueError("Bot not found")
        
        return self.db.query(BotLog).filter(
            BotLog.bot_id == bot_id
        ).order_by(desc(BotLog.timestamp)).limit(limit).all()
    
    def get_bot_trades(
        self,
        user_id: int,
        bot_id: int,
        is_open: Optional[bool] = None,
        limit: int = 100
    ) -> List[BotTrade]:
        """Get bot trades"""
        bot = self.get_bot(user_id, bot_id)
        if not bot:
            raise ValueError("Bot not found")
        
        query = self.db.query(BotTrade).filter(BotTrade.bot_id == bot_id)
        
        if is_open is not None:
            query = query.filter(BotTrade.is_open == is_open)
        
        return query.order_by(desc(BotTrade.opened_at)).limit(limit).all()
    
    def get_bot_backtests(
        self,
        user_id: int,
        bot_id: int,
        limit: int = 10
    ) -> List[BotBacktest]:
        """Get bot backtests"""
        bot = self.get_bot(user_id, bot_id)
        if not bot:
            raise ValueError("Bot not found")
        
        return self.db.query(BotBacktest).filter(
            BotBacktest.bot_id == bot_id
        ).order_by(desc(BotBacktest.started_at)).limit(limit).all()