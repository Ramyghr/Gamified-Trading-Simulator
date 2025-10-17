from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from sqlalchemy import and_

from app.config.database import get_db
from app.models.user import User
from app.models.orders import OrderStatus, OrderType, OrderSide
from app.schemas.order import (
    OrderCreate, 
    OrderResponse, 
    OrderCancelRequest,
    StockTransactionResponse,
    ExitPositionRequest,
    ExitPositionResponse
)
from app.services.trading_service import (
    TradingService,
#    InsufficientFundsError,
#    InsufficientSharesError,
    # InvalidOrderError
)
from app.middleware.jwt_middleware import get_current_user
from app.models.stock_transaction import StockTransaction
from app.models.portfolio import Holding as StockHolding
import logging
from decimal import Decimal  

router = APIRouter(prefix="/orders", tags=["Orders"])
logger = logging.getLogger(__name__)


@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    order_data: OrderCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new order (market/limit/stop/stop-limit/take-profit).
    """
    trading_service = TradingService(db)

    try:
        order = await trading_service.create_order(current_user.id, order_data)

        if not order:
            logger.warning(f"Order creation failed for user {current_user.id}")
            raise HTTPException(status_code=400, detail="Order creation failed")

        logger.info(f"Order created successfully: {getattr(order, 'id', 'N/A')}")
        return order

    except Exception as e:
        logger.error(f"Unexpected error in router: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/exit-position", response_model=ExitPositionResponse, status_code=status.HTTP_200_OK)
async def exit_position(
    request: ExitPositionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Exit a position by selling all shares of a symbol.
    Closes out the entire position at market or limit price.
    """
    try:
        trading_service = TradingService(db)
        
        # Get portfolio
        from app.models.portfolio import Portfolio
        portfolio = db.query(Portfolio).filter(
            Portfolio.user_id == current_user.id
        ).first()
        
        if not portfolio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Portfolio not found"
            )
        
        # Get holding
        holding = db.query(StockHolding).filter(
            and_(
                StockHolding.portfolio_id == portfolio.id,
                StockHolding.symbol == request.symbol
            )
        ).first()
        
        if not holding:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No position found for {request.symbol}"
            )
        
        # Calculate available quantity
        available_quantity = Decimal(str(holding.quantity)) - Decimal(str(holding.reserved_quantity))
        
        if available_quantity <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No available shares to sell. All shares are reserved in pending orders."
            )
        
        # Create sell order for full position
        order_data = OrderCreate(
            symbol=request.symbol,
            order_type=request.order_type,
            side=OrderSide.SELL,
            quantity=available_quantity,
            price=request.price,
            time_in_force="GTC"
        )
        
        # Execute the order
        order = await trading_service.create_order(current_user.id, order_data)
        
        # Calculate estimated proceeds
        estimated_proceeds = None
        if order.status == OrderStatus.FILLED:
            estimated_proceeds = float(order.filled_quantity) * float(order.average_fill_price) - float(order.total_fees)
        
        return ExitPositionResponse(
            success=True,
            message=f"Successfully closed position for {request.symbol}",
            order=order,
            closed_quantity=available_quantity,
            estimated_proceeds=Decimal(str(estimated_proceeds)) if estimated_proceeds else None
        )
        
    except HTTPException:
        raise
    except InsufficientSharesError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except InvalidOrderError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error exiting position: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to exit position: {str(e)}"
        )


@router.get("/", response_model=List[OrderResponse])
async def get_orders(
    status: Optional[OrderStatus] = Query(None, description="Filter by order status"),
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    order_type: Optional[OrderType] = Query(None, description="Filter by order type"),
    side: Optional[OrderSide] = Query(None, description="Filter by side (BUY/SELL)"),
    limit: int = Query(50, ge=1, le=500, description="Number of orders to return"),
    offset: int = Query(0, ge=0, description="Number of orders to skip"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user's orders with optional filters.
    Returns orders sorted by creation date (newest first).
    """
    try:
        trading_service = TradingService(db)
        orders = trading_service.get_user_orders(
            user_id=current_user.id,
            status=status,
            symbol=symbol,
            order_type=order_type,
            side=side,
            limit=limit,
            offset=offset
        )
        
        logger.info(f"Fetched {len(orders)} orders for user {current_user.id}")
        return orders
        
    except Exception as e:
        logger.error(f"Error fetching orders: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch orders"
        )


@router.get("/pending", response_model=List[OrderResponse])
async def get_pending_orders(
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all pending and partially filled orders for the current user.
    """
    try:
        from sqlalchemy import or_
        from app.models.orders import Order
        
        query = db.query(Order).filter(
            Order.user_id == current_user.id,
            or_(
                Order.status == OrderStatus.PENDING,
                Order.status == OrderStatus.PARTIALLY_FILLED
            )
        )
        
        if symbol:
            query = query.filter(Order.symbol == symbol.upper())
        
        orders = query.order_by(Order.created_at.desc()).all()
        
        logger.info(f"Found {len(orders)} pending orders for user {current_user.id}")
        return orders
        
    except Exception as e:
        logger.error(f"Error fetching pending orders: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch pending orders"
        )


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific order by ID.
    """
    try:
        trading_service = TradingService(db)
        order = trading_service.get_order_by_id(current_user.id, order_id)
        
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        
        return order
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching order {order_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch order"
        )


@router.delete("/{order_id}", response_model=OrderResponse)
async def cancel_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Cancel a pending or partially filled order.
    Releases reserved cash or shares back to the portfolio.
    """
    try:
        trading_service = TradingService(db)
        order = trading_service.cancel_order(current_user.id, order_id)
        
        logger.info(f"Order {order_id} canceled for user {current_user.id}")
        return order
        
    except InvalidOrderError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error canceling order {order_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel order"
        )


@router.get("/{order_id}/transactions", response_model=List[StockTransactionResponse])
async def get_order_transactions(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all transactions (fills) for a specific order.
    Useful for partially filled orders.
    """
    try:
        # Verify order belongs to user
        trading_service = TradingService(db)
        order = trading_service.get_order_by_id(current_user.id, order_id)
        
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        
        # Get transactions
        transactions = db.query(StockTransaction).filter(
            StockTransaction.order_id == order_id
        ).order_by(StockTransaction.executed_at.desc()).all()
        
        return transactions
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching transactions for order {order_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch transactions"
        )


@router.get("/history/transactions", response_model=List[StockTransactionResponse])
async def get_transaction_history(
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get transaction history with optional filters.
    Returns all executed trades for the user.
    """
    try:
        query = db.query(StockTransaction).filter(
            StockTransaction.user_id == current_user.id
        )
        
        if symbol:
            query = query.filter(StockTransaction.symbol == symbol.upper())
        
        if start_date:
            query = query.filter(StockTransaction.executed_at >= start_date)
        
        if end_date:
            query = query.filter(StockTransaction.executed_at <= end_date)
        
        transactions = query.order_by(
            StockTransaction.executed_at.desc()
        ).limit(limit).offset(offset).all()
        
        return transactions
        
    except Exception as e:
        logger.error(f"Error fetching transaction history: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch transaction history"
        )


@router.post("/validate", status_code=status.HTTP_200_OK)
async def validate_order(
    order_data: OrderCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Validate order without placing it.
    Useful for frontend validation and showing estimated costs.
    """
    try:
        trading_service = TradingService(db)
        
        # Calculate estimated cost
        estimated_cost = await trading_service.calculate_estimated_cost(
            order_data.symbol,
            order_data.order_type,
            order_data.side,
            order_data.quantity,
            order_data.price
        )
        
        # Get current portfolio to check availability
        from app.models.portfolio import Portfolio
        portfolio = db.query(Portfolio).filter(
            Portfolio.user_id == current_user.id
        ).first()
        
        if not portfolio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Portfolio not found"
            )
        
        # Convert everything to float for consistent arithmetic
        estimated_cost_float = float(estimated_cost) if estimated_cost else 0.0
        
        response = {
            "valid": True,
            "estimated_cost": estimated_cost_float,
            "estimated_fee": 0.0,
        }
        
        # Check availability
        if order_data.side == OrderSide.BUY:
            available_cash = float(portfolio.cash_balance) - float(portfolio.reserved_cash)
            response["available_cash"] = available_cash
            response["sufficient_funds"] = available_cash >= estimated_cost_float
        else:
            holding = db.query(StockHolding).filter(
                and_(
                    StockHolding.portfolio_id == portfolio.id,
                    StockHolding.symbol == order_data.symbol
                )
            ).first()
            
            if holding:
                available_shares = float(holding.quantity) - float(holding.reserved_quantity)
            else:
                available_shares = 0.0
                
            response["available_shares"] = available_shares
            response["sufficient_shares"] = available_shares >= float(order_data.quantity)
        
        return response
        
    except Exception as e:
        logger.error(f"Error validating order: {str(e)}", exc_info=True)
        return {
            "valid": False,
            "error": str(e)
        }