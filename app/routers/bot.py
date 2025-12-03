"""
Bot Trading API Router
Save as: app/routers/bot.py
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.config.database import get_db
from app.middleware.jwt_middleware import get_current_user
from app.models.user import User
from app.models.bot import BotStatus
from app.schemas.bot import (
    BotCreate, BotUpdate, BotResponse, BotListResponse,
    BotTradeResponse, BacktestRequest, BacktestResponse,
    BotPerformance, BotSignal, StrategyTemplate, BotControlRequest,
    BotStatusUpdate, BotStrategyType
)
from app.services.bot.bot_service import BotService
from app.services.bot.bot_executor import bot_executor
import logging 
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/bots", tags=["Bot Trading"])


# ==================== Bot CRUD ====================

@router.post("/", response_model=BotResponse, status_code=status.HTTP_201_CREATED)
async def create_bot(
    bot_data: BotCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new trading bot
    
    The bot will be created in PAUSED state.
    Use the start endpoint to activate it.
    """
    bot_service = BotService(db)
    bot = bot_service.create_bot(current_user.id, bot_data)
    return bot


@router.get("/", response_model=BotListResponse)
async def get_bots(
    status_filter: Optional[BotStatus] = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user's bots with optional status filter"""
    bot_service = BotService(db)
    
    bots = bot_service.get_user_bots(
        current_user.id,
        status=status_filter,
        limit=limit,
        offset=offset
    )
    
    # Convert SQLAlchemy objects to Pydantic
    bot_responses = [BotResponse.from_orm(bot) for bot in bots]

    # Count by status
    all_bots = bot_service.get_user_bots(current_user.id, limit=1000)
    active_count = sum(1 for b in all_bots if b.status == BotStatus.ACTIVE)
    paused_count = sum(1 for b in all_bots if b.status == BotStatus.PAUSED)
    
    return BotListResponse(
        bots=bot_responses,
        total=len(all_bots),
        active_count=active_count,
        paused_count=paused_count
    )



@router.get("/{bot_id}", response_model=BotResponse)
async def get_bot(
    bot_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get bot by ID"""
    bot_service = BotService(db)
    bot = bot_service.get_bot(current_user.id, bot_id)
    
    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bot not found"
        )
    
    return bot


@router.put("/{bot_id}", response_model=BotResponse)
async def update_bot(
    bot_id: int,
    bot_data: BotUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update bot configuration
    
    Bot must be PAUSED or STOPPED to update.
    """
    bot_service = BotService(db)
    
    try:
        bot = bot_service.update_bot(current_user.id, bot_id, bot_data)
        return bot
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{bot_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bot(
    bot_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a bot
    
    This will also delete all associated trades, backtests, and logs.
    """
    bot_service = BotService(db)
    
    try:
        bot_service.delete_bot(current_user.id, bot_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


# ==================== Bot Control ====================

@router.post("/{bot_id}/start", response_model=BotStatusUpdate)
async def start_bot(
    bot_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Start/activate a bot
    
    Bot will begin executing trades based on its strategy.
    """
    bot_service = BotService(db)
    
    try:
        bot = bot_service.start_bot(current_user.id, bot_id)
        return BotStatusUpdate(
            status=bot.status,
            message=f"Bot '{bot.name}' started successfully"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
@router.post("/{bot_id}/start_rapid_test", response_model=BotStatusUpdate)
async def start_rapid_test_bot(
    bot_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Start a RAPID_TEST bot immediately
    
    This endpoint ignores strategy parameters and starts the bot instantly.
    """
    bot_service = BotService(db)

    # Get the bot
    bot = bot_service.get_bot(current_user.id, bot_id)
    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bot not found"
        )
    
    # Ensure it's a RAPID_TEST bot
    if bot.strategy_type != BotStrategyType.RAPID_TEST:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This endpoint is only for RAPID_TEST bots"
        )
    
    try:
        # Directly start the bot
        bot = bot_service.start_bot(current_user.id, bot_id)
        return BotStatusUpdate(
            status=bot.status,
            message=f"Rapid Test Bot '{bot.name}' started successfully"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/{bot_id}/pause", response_model=BotStatusUpdate)
async def pause_bot(
    bot_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Pause a bot
    
    Bot will stop executing new trades but keep existing positions open.
    """
    bot_service = BotService(db)
    
    try:
        bot = bot_service.pause_bot(current_user.id, bot_id)
        return BotStatusUpdate(
            status=bot.status,
            message=f"Bot '{bot.name}' paused successfully"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/{bot_id}/stop", response_model=BotStatusUpdate)
async def stop_bot(
    bot_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Stop a bot
    
    Bot will close all open positions and stop executing.
    """
    bot_service = BotService(db)
    
    try:
        bot = bot_service.stop_bot(current_user.id, bot_id)
        return BotStatusUpdate(
            status=bot.status,
            message=f"Bot '{bot.name}' stopped successfully"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/{bot_id}/execute", response_model=BotStatusUpdate)
async def manually_execute_bot(
    bot_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Manually trigger bot execution (for testing)
    
    This will execute the bot immediately regardless of schedule.
    """
    bot_service = BotService(db)
    bot = bot_service.get_bot(current_user.id, bot_id)
    
    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bot not found"
        )
    
    try:
        result = await bot_executor.execute_bot(bot, db)
        
        if result:
            return BotStatusUpdate(
                status=bot.status,
                message="Bot executed successfully"
            )
        else:
            return BotStatusUpdate(
                status=bot.status,
                message="Bot execution skipped (conditions not met)"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Execution failed: {str(e)}"
        )


# ==================== Bot Performance ====================

@router.get("/{bot_id}/performance", response_model=BotPerformance)
async def get_bot_performance(
    bot_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get bot performance metrics"""
    bot_service = BotService(db)
    bot = bot_service.get_bot(current_user.id, bot_id)
    
    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bot not found"
        )
    
    # Calculate uptime
    uptime_hours = 0.0
    if bot.activated_at:
        end_time = bot.stopped_at or datetime.utcnow()
        uptime_hours = (end_time - bot.activated_at).total_seconds() / 3600
    
    # Calculate average P&L
    avg_pnl_per_trade = bot.total_pnl / bot.total_trades if bot.total_trades > 0 else 0.0
    
    # Get best/worst trades
    trades = bot_service.get_bot_trades(current_user.id, bot_id, is_open=False, limit=1000)
    best_trade = max([t.pnl for t in trades]) if trades else 0.0
    worst_trade = min([t.pnl for t in trades]) if trades else 0.0
    
    total_return_pct = 0.0
    if trades:
        initial_capital = sum(t.trade_value for t in trades[:5]) / 5 if len(trades) >= 5 else 10000
        total_return_pct = (bot.total_pnl / initial_capital) * 100 if initial_capital > 0 else 0.0
    
    return BotPerformance(
        bot_id=bot.id,
        bot_name=bot.name,
        symbol=bot.symbol,
        total_trades=bot.total_trades,
        winning_trades=bot.winning_trades,
        losing_trades=bot.losing_trades,
        win_rate=(bot.winning_trades / bot.total_trades * 100) if bot.total_trades > 0 else 0.0,
        total_pnl=bot.total_pnl,
        total_pnl_pct=total_return_pct,
        avg_pnl_per_trade=avg_pnl_per_trade,
        best_trade=best_trade,
        worst_trade=worst_trade,
        total_fees=bot.total_fees,
        status=bot.status,
        uptime_hours=uptime_hours,
        last_execution=bot.last_execution
    )


@router.get("/{bot_id}/trades", response_model=List[BotTradeResponse])
async def get_bot_trades(
    bot_id: int,
    is_open: Optional[bool] = None,
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get bot's trade history"""
    bot_service = BotService(db)
    
    # Verify bot ownership
    bot = bot_service.get_bot(current_user.id, bot_id)
    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bot not found"
        )
    
    trades = bot_service.get_bot_trades(current_user.id, bot_id, is_open, limit)
    return trades


@router.get("/{bot_id}/logs")
async def get_bot_logs(
    bot_id: int,
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get bot execution logs"""
    bot_service = BotService(db)
    
    # Verify bot ownership
    bot = bot_service.get_bot(current_user.id, bot_id)
    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bot not found"
        )
    
    logs = bot_service.get_bot_logs(current_user.id, bot_id, limit)
    
    return {
        "bot_id": bot_id,
        "logs": [
            {
                "id": log.id,
                "level": log.level,
                "message": log.message,
                "details": log.details,
                "timestamp": log.timestamp
            }
            for log in logs
        ]
    }


# ==================== Backtesting ====================

@router.post("/{bot_id}/backtest", response_model=BacktestResponse, status_code=status.HTTP_202_ACCEPTED)
async def run_backtest(
    bot_id: int,
    backtest_request: BacktestRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Run backtest simulation
    
    Tests the bot's strategy on historical data.
    """
    bot_service = BotService(db)
    
    # Verify bot ownership
    bot = bot_service.get_bot(current_user.id, bot_id)
    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bot not found"
        )
    
    try:
        backtest = await bot_service.run_backtest(
            current_user.id,
            bot_id,
            backtest_request
        )
        return backtest
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Backtest failed: {str(e)}"
        )


@router.get("/{bot_id}/backtests", response_model=List[BacktestResponse])
async def get_backtests(
    bot_id: int,
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get bot's backtest history"""
    bot_service = BotService(db)
    
    # Verify bot ownership
    bot = bot_service.get_bot(current_user.id, bot_id)
    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bot not found"
        )
    
    backtests = bot_service.get_bot_backtests(current_user.id, bot_id, limit)
    return backtests


@router.get("/{bot_id}/backtests/{backtest_id}", response_model=BacktestResponse)
async def get_backtest(
    bot_id: int,
    backtest_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get specific backtest results"""
    bot_service = BotService(db)
    
    # Verify bot ownership
    bot = bot_service.get_bot(current_user.id, bot_id)
    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bot not found"
        )
    
    from app.models.bot import BotBacktest
    backtest = db.query(BotBacktest).filter(
        BotBacktest.id == backtest_id,
        BotBacktest.bot_id == bot_id
    ).first()
    
    if not backtest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Backtest not found"
        )
    
    return backtest


# ==================== Strategy Templates ====================

@router.get("/templates/strategies", response_model=List[StrategyTemplate])
async def get_strategy_templates():
    """
    Get available strategy templates with default parameters
    
    Use these templates to quickly create bots with pre-configured strategies.
    """
    templates = [
        StrategyTemplate(
            strategy_type=BotStrategyType.MA_CROSSOVER,
            name="Moving Average Crossover",
            description="Classic trend-following strategy. Buys when short MA crosses above long MA.",
            default_params={
                "short_window": 5,
                "long_window": 20
            },
            param_descriptions={
                "short_window": "Fast moving average period (e.g., 5)",
                "long_window": "Slow moving average period (e.g., 20)"
            },
            recommended_intervals=["5m", "15m", "1h"],
            risk_level="LOW"
        ),
        StrategyTemplate(
            strategy_type=BotStrategyType.RSI_OVERSOLD_OVERBOUGHT,
            name="RSI Oscillator",
            description="Buys at oversold levels, sells at overbought levels using RSI indicator.",
            default_params={
                "period": 14,
                "oversold": 30,
                "overbought": 70
            },
            param_descriptions={
                "period": "RSI calculation period (typically 14)",
                "oversold": "Oversold threshold (e.g., 30)",
                "overbought": "Overbought threshold (e.g., 70)"
            },
            recommended_intervals=["15m", "1h", "4h"],
            risk_level="MEDIUM"
        ),
        StrategyTemplate(
            strategy_type=BotStrategyType.BOLLINGER_BANDS,
            name="Bollinger Bands",
            description="Mean reversion strategy. Buys at lower band, sells at upper band.",
            default_params={
                "period": 20,
                "std_dev": 2
            },
            param_descriptions={
                "period": "Moving average period for bands (e.g., 20)",
                "std_dev": "Standard deviations for bands (typically 2)"
            },
            recommended_intervals=["15m", "1h"],
            risk_level="MEDIUM"
        ),
        StrategyTemplate(
            strategy_type=BotStrategyType.MACD_CROSSOVER,
            name="MACD Crossover",
            description="Momentum strategy using MACD indicator crossovers.",
            default_params={
                "fast_period": 12,
                "slow_period": 26,
                "signal_period": 9
            },
            param_descriptions={
                "fast_period": "Fast EMA period (typically 12)",
                "slow_period": "Slow EMA period (typically 26)",
                "signal_period": "Signal line period (typically 9)"
            },
            recommended_intervals=["1h", "4h"],
            risk_level="MEDIUM"
        ),
        StrategyTemplate(
            strategy_type=BotStrategyType.VOLUME_BREAKOUT,
            name="Volume Breakout",
            description="Trades on volume spikes combined with price movement.",
            default_params={
                "volume_threshold": 2.0,
                "lookback_period": 20
            },
            param_descriptions={
                "volume_threshold": "Volume multiplier for breakout (e.g., 2.0 = 2x average)",
                "lookback_period": "Period for average volume calculation"
            },
            recommended_intervals=["5m", "15m"],
            risk_level="HIGH"
        ),
        StrategyTemplate(
            strategy_type=BotStrategyType.MEAN_REVERSION,
            name="Mean Reversion",
            description="Buys when price deviates significantly below mean, sells when above.",
            default_params={
                "period": 20,
                "std_threshold": 2
            },
            param_descriptions={
                "period": "Period for mean calculation",
                "std_threshold": "Standard deviation threshold for entry"
            },
            recommended_intervals=["15m", "1h"],
            risk_level="MEDIUM"
        ),
        StrategyTemplate(
            strategy_type=BotStrategyType.MOMENTUM,
            name="Momentum Trading",
            description="Follows strong price momentum in either direction.",
            default_params={
                "period": 10,
                "threshold": 5
            },
            param_descriptions={
                "period": "Lookback period for momentum calculation",
                "threshold": "Momentum threshold % for entry"
            },
            recommended_intervals=["5m", "15m", "1h"],
            risk_level="HIGH"
        ),
        StrategyTemplate(
            strategy_type=BotStrategyType.GRID_TRADING,
            name="Grid Trading",
            description="Places buy/sell orders at predetermined price levels.",
            default_params={
                "grid_levels": 5,
                "grid_spacing_pct": 2
            },
            param_descriptions={
                "grid_levels": "Number of grid levels above/below current price",
                "grid_spacing_pct": "Spacing between grid levels in %"
            },
            recommended_intervals=["15m", "1h"],
            risk_level="MEDIUM"
        ),
        StrategyTemplate(
            strategy_type=BotStrategyType.DCA,
            name="Dollar Cost Averaging",
            description="Buys fixed amount at regular intervals regardless of price.",
            default_params={
                "buy_interval": 20,
                "buy_amount": 100
            },
            param_descriptions={
                "buy_interval": "Interval in candles between buys (e.g., 20)",
                "buy_amount": "Fixed dollar amount per buy"
            },
            recommended_intervals=["1h", "4h", "1d"],
            risk_level="LOW"
        ),
        StrategyTemplate(
            strategy_type=BotStrategyType.SUPPORT_RESISTANCE,
            name="Support & Resistance",
            description="Buys at support levels, sells at resistance levels.",
            default_params={
                "lookback_period": 50,
                "tolerance": 2
            },
            param_descriptions={
                "lookback_period": "Period to identify support/resistance",
                "tolerance": "Price tolerance % for level detection"
            },
            recommended_intervals=["1h", "4h"],
            risk_level="MEDIUM"
        ),
        StrategyTemplate(
            strategy_type=BotStrategyType.RAPID_TEST,
            name="Rapid Test Strategy",
            description="Ultra-fast strategy for testing bot execution, latency, and signal flow.",
            default_params={},   # no params
            param_descriptions={},  # nothing to describe
            recommended_intervals=["1m", "5m"],
            risk_level="NONE"
        )

    ]
    
    return templates


# ==================== Bot Trade Control ====================

@router.post("/{bot_id}/trades/{trade_id}/close", response_model=BotTradeResponse)
async def close_bot_trade(
    bot_id: int,
    trade_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Manually close a specific bot trade
    
    Gives user direct control to close positions
    """
    from app.models.bot import BotTrade
    from app.services.leverage_trading_service import LeverageTradingService
    from app.services.trading_service import TradingService
    from app.schemas.order import OrderCreate
    from app.models.orders import OrderType, OrderSide, TimeInForce
    
    # Verify bot ownership
    bot_service = BotService(db)
    bot = bot_service.get_bot(current_user.id, bot_id)
    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bot not found"
        )
    
    # Get the trade
    trade = db.query(BotTrade).filter(
        BotTrade.id == trade_id,
        BotTrade.bot_id == bot_id,
        BotTrade.is_open == True
    ).first()
    
    if not trade:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Open trade not found"
        )
    
    try:
        # Get current price
        from app.services.market_data_service import enhanced_market_service
        current_price = await enhanced_market_service.get_price(
            trade.symbol,
            "STOCK",
            force_refresh=True
        )
        
        if not current_price:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not get current price"
            )
        
        # Close the position
        if trade.leverage_used > 1.0:
            # Leveraged position
            leverage_service = LeverageTradingService(db)
            result = await leverage_service.close_leveraged_position(
                user_id=current_user.id,
                position_id=trade.id,
                exit_price=current_price
            )
            pnl = result['net_pnl']
        else:
            # Spot position
            trading_service = TradingService(db)
            order_data = OrderCreate(
                symbol=trade.symbol,
                order_type=OrderType.MARKET,
                side=OrderSide.SELL,
                quantity=trade.quantity,
                time_in_force=TimeInForce.GTC
            )
            order = await trading_service.create_order(current_user.id, order_data)
            
            # Calculate P&L
            entry_value = trade.entry_price * trade.quantity
            exit_value = current_price * trade.quantity
            pnl = exit_value - entry_value - order.total_fees
        
        # Update trade
        trade.exit_price = current_price
        trade.pnl = pnl
        trade.pnl_pct = (pnl / (trade.entry_price * trade.quantity)) * 100
        trade.is_open = False
        trade.closed_at = datetime.utcnow()
        trade.exit_reason = "MANUAL"
        
        # Update bot stats
        bot.total_pnl += pnl
        if pnl > 0:
            bot.winning_trades += 1
        else:
            bot.losing_trades += 1
        
        db.commit()
        db.refresh(trade)
        
        return trade
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to close trade: {str(e)}"
        )


@router.post("/{bot_id}/emergency-stop", response_model=BotStatusUpdate)
async def emergency_stop_bot(
    bot_id: int,
    close_positions: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Emergency stop - immediately halt bot and optionally close all positions
    
    Use this for urgent situations where bot needs to be stopped immediately
    """
    bot_service = BotService(db)
    bot = bot_service.get_bot(current_user.id, bot_id)
    
    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bot not found"
        )
    
    from app.models.bot import BotTrade
    
    try:
        # Stop the bot
        bot.status = BotStatus.STOPPED
        bot.stopped_at = datetime.utcnow()
        
        closed_count = 0
        
        if close_positions:
            # Close all open trades
            open_trades = db.query(BotTrade).filter(
                BotTrade.bot_id == bot_id,
                BotTrade.is_open == True
            ).all()
            
            from app.services.market_data_service import enhanced_market_service
            
            for trade in open_trades:
                try:
                    current_price = await enhanced_market_service.get_price(
                        trade.symbol,
                        "STOCK",
                        force_refresh=True
                    )
                    
                    if current_price:
                        # Calculate P&L
                        entry_value = trade.entry_price * trade.quantity
                        exit_value = current_price * trade.quantity
                        pnl = exit_value - entry_value
                        
                        trade.exit_price = current_price
                        trade.pnl = pnl
                        trade.pnl_pct = (pnl / entry_value) * 100 if entry_value > 0 else 0
                        trade.is_open = False
                        trade.closed_at = datetime.utcnow()
                        trade.exit_reason = "EMERGENCY_STOP"
                        
                        bot.total_pnl += pnl
                        if pnl > 0:
                            bot.winning_trades += 1
                        else:
                            bot.losing_trades += 1
                        
                        closed_count += 1
                except Exception as e:
                    logger.error(f"Failed to close trade {trade.id}: {str(e)}")
        
        db.commit()
        
        message = f"Bot emergency stopped. "
        if close_positions:
            message += f"Closed {closed_count} positions."
        
        bot_service._log_bot_event(db, bot_id, "WARNING", message)
        
        return BotStatusUpdate(
            status=bot.status,
            message=message
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Emergency stop failed: {str(e)}"
        )


@router.get("/{bot_id}/live-status")
async def get_bot_live_status(
    bot_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get real-time bot status including current positions and recent activity
    
    This gives users live visibility into what their bot is doing
    """
    bot_service = BotService(db)
    bot = bot_service.get_bot(current_user.id, bot_id)
    
    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bot not found"
        )
    
    from app.models.bot import BotTrade
    
    # Get open positions
    open_trades = db.query(BotTrade).filter(
        BotTrade.bot_id == bot_id,
        BotTrade.is_open == True
    ).all()
    
    # Calculate current P&L for open trades
    total_unrealized_pnl = 0.0
    positions = []
    
    from app.services.market_data_service import enhanced_market_service
    
    for trade in open_trades:
        try:
            current_price = await enhanced_market_service.get_price(
                trade.symbol,
                "STOCK",
                force_refresh=True
            )
            
            if current_price:
                unrealized_pnl = (current_price - trade.entry_price) * trade.quantity
                unrealized_pnl_pct = (unrealized_pnl / (trade.entry_price * trade.quantity)) * 100
                
                total_unrealized_pnl += unrealized_pnl
                
                positions.append({
                    "trade_id": trade.id,
                    "symbol": trade.symbol,
                    "quantity": trade.quantity,
                    "entry_price": trade.entry_price,
                    "current_price": current_price,
                    "unrealized_pnl": unrealized_pnl,
                    "unrealized_pnl_pct": unrealized_pnl_pct,
                    "opened_at": trade.opened_at,
                    "duration_minutes": (datetime.utcnow() - trade.opened_at).total_seconds() / 60
                })
        except Exception as e:
            logger.error(f"Error getting price for {trade.symbol}: {str(e)}")
    
    # NEW: Calculate open trades percentage
    open_trades_count = len(positions)
    max_open_trades = bot.max_open_trades
    open_trades_percentage = (open_trades_count / max_open_trades * 100) if max_open_trades > 0 else 0
    open_trades_limit_status = "OK"
    if open_trades_percentage >= 90:
        open_trades_limit_status = "WARNING"
    elif open_trades_percentage >= 100:
        open_trades_limit_status = "LIMIT_REACHED"
    
    # Get recent closed trades (last 5)
    recent_trades = db.query(BotTrade).filter(
        BotTrade.bot_id == bot_id,
        BotTrade.is_open == False
    ).order_by(BotTrade.closed_at.desc()).limit(5).all()
    
    recent_activity = [{
        "trade_id": t.id,
        "symbol": t.symbol,
        "pnl": t.pnl,
        "pnl_pct": t.pnl_pct,
        "closed_at": t.closed_at,
        "exit_reason": t.exit_reason
    } for t in recent_trades]
    
    # Get today's stats
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_trades = db.query(BotTrade).filter(
        BotTrade.bot_id == bot_id,
        BotTrade.opened_at >= today_start
    ).all()
    
    today_pnl = sum(t.pnl for t in today_trades if not t.is_open)
    today_trade_count = len(today_trades)
    
    return {
        "bot_id": bot.id,
        "bot_name": bot.name,
        "status": bot.status.value,
        "strategy": bot.strategy_type.value,
        "symbol": bot.symbol,
        
        # NEW: Max open trades info
        "max_open_trades": max_open_trades,
        "open_trades_count": open_trades_count,
        "open_trades_limit": f"{open_trades_count}/{max_open_trades}",
        "open_trades_percentage": round(open_trades_percentage, 1),
        "open_trades_limit_status": open_trades_limit_status,
        
        "last_execution": bot.last_execution,
        "next_execution": bot.next_execution,
        "last_signal": bot.last_signal.value if bot.last_signal else None,
        
        "open_positions": {
            "count": open_trades_count,
            "positions": positions,
            "total_unrealized_pnl": total_unrealized_pnl
        },
        
        "recent_activity": recent_activity,
        
        "today_stats": {
            "trades": today_trade_count,
            "pnl": today_pnl,
            "remaining_trades": bot.max_daily_trades - today_trade_count,
            "daily_loss_limit": bot.max_daily_loss,
            "daily_loss_used": abs(today_pnl) if today_pnl < 0 else 0
        },
        
        "overall_stats": {
            "total_trades": bot.total_trades,
            "winning_trades": bot.winning_trades,
            "losing_trades": bot.losing_trades,
            "win_rate": (bot.winning_trades / bot.total_trades * 100) if bot.total_trades > 0 else 0,
            "total_pnl": bot.total_pnl,
            "total_fees": bot.total_fees,
            "max_open_trades": max_open_trades,  # Include here too for completeness
            "average_position_duration_minutes": calculate_average_position_duration(bot_id, db)
        }
    }


# def _calculate_average_position_duration(self, bot_id: int, db: Session) -> float:
#     """Calculate average position duration for a bot"""
#     from app.models.bot import BotTrade
#     from sqlalchemy import func
    
#     closed_trades = db.query(BotTrade).filter(
#         BotTrade.bot_id == bot_id,
#         BotTrade.is_open == False,
#         BotTrade.closed_at.isnot(None)
#     ).all()
    
#     if not closed_trades:
#         return 0.0
    
#     total_duration = 0.0
#     for trade in closed_trades:
#         duration = (trade.closed_at - trade.opened_at).total_seconds() / 60  # minutes
#         total_duration += duration
    
#     return round(total_duration / len(closed_trades), 1)

def calculate_average_position_duration(bot_id: int, db: Session) -> float:
    """Calculate average position duration for a bot"""
    from app.models.bot import BotTrade
    
    closed_trades = db.query(BotTrade).filter(
        BotTrade.bot_id == bot_id,
        BotTrade.is_open == False,
        BotTrade.closed_at.isnot(None)
    ).all()
    
    if not closed_trades:
        return 0.0
    
    total_duration = 0.0
    for trade in closed_trades:
        duration = (trade.closed_at - trade.opened_at).total_seconds() / 60  # minutes
        total_duration += duration
    
    return round(total_duration / len(closed_trades), 1)

# ==================== System Status ====================

@router.get("/system/status")
async def get_system_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get bot trading system status"""
    from app.models.bot import Bot
    
    total_bots = db.query(Bot).count()
    active_bots = db.query(Bot).filter(Bot.status == BotStatus.ACTIVE).count()
    user_bots = db.query(Bot).filter(Bot.user_id == current_user.id).count()
    
    return {
        "system_status": "operational",
        "executor_running": bot_executor.is_running,
        "total_bots": total_bots,
        "active_bots": active_bots,
        "your_bots": user_bots,
        "supported_strategies": 10,
        "timestamp": datetime.utcnow()
    }