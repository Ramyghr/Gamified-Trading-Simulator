"""
Order schemas without circular imports
"""
from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime
from decimal import Decimal
from app.models.orders import OrderType, OrderSide, OrderStatus, TimeInForce


class OrderCreate(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=10, description="Stock symbol")
    order_type: OrderType
    side: OrderSide
    quantity: Decimal = Field(..., gt=0, description="Number of shares")
    price: Optional[Decimal] = Field(None, gt=0, description="Limit price (required for LIMIT/STOP_LIMIT)")
    stop_price: Optional[Decimal] = Field(None, gt=0, description="Stop trigger price (required for STOP/STOP_LIMIT)")
    time_in_force: TimeInForce = TimeInForce.GTC
    idempotency_key: Optional[str] = Field(None, max_length=100, description="Unique key to prevent duplicate orders")

    @validator('symbol')
    def symbol_uppercase(cls, v):
        return v.upper().strip()

    @validator('price')
    def validate_price_for_type(cls, v, values):
        order_type = values.get('order_type')
        if order_type in [OrderType.LIMIT, OrderType.STOP_LIMIT, OrderType.TAKE_PROFIT]:
            if v is None:
                raise ValueError(f"price is required for {order_type} orders")
        return v

    @validator('stop_price')
    def validate_stop_price_for_type(cls, v, values):
        order_type = values.get('order_type')
        if order_type in [OrderType.STOP, OrderType.STOP_LIMIT]:
            if v is None:
                raise ValueError(f"stop_price is required for {order_type} orders")
        return v

    @validator('quantity')
    def validate_quantity_precision(cls, v):
        """Limit quantity to 8 decimal places"""
        if v.as_tuple().exponent < -8:
            raise ValueError("Quantity cannot have more than 8 decimal places")
        return v

    class Config:
        use_enum_values = True


class OrderResponse(BaseModel):
    id: int
    user_id: int
    symbol: str
    order_type: OrderType
    side: OrderSide
    quantity: Decimal
    filled_quantity: Decimal
    price: Optional[Decimal]
    stop_price: Optional[Decimal]
    average_fill_price: Optional[Decimal]
    status: OrderStatus
    time_in_force: TimeInForce
    reserved_amount: Decimal
    estimated_cost: Optional[Decimal]
    total_fees: Decimal
    created_at: datetime
    updated_at: datetime
    executed_at: Optional[datetime]
    canceled_at: Optional[datetime]
    expires_at: Optional[datetime]
    rejection_reason: Optional[str]
    remaining_quantity: Decimal
    fill_percentage: float

    class Config:
        from_attributes = True
        use_enum_values = True


class OrderUpdate(BaseModel):
    quantity: Optional[Decimal] = Field(None, gt=0)
    price: Optional[Decimal] = Field(None, gt=0)
    stop_price: Optional[Decimal] = Field(None, gt=0)


class OrderCancelRequest(BaseModel):
    order_id: int


class OrderListQuery(BaseModel):
    symbol: Optional[str] = None
    status: Optional[OrderStatus] = None
    order_type: Optional[OrderType] = None
    side: Optional[OrderSide] = None
    limit: int = Field(50, ge=1, le=500)
    offset: int = Field(0, ge=0)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class StockTransactionResponse(BaseModel):
    id: int
    user_id: int
    order_id: Optional[int]
    symbol: str
    transaction_type: str
    quantity: Decimal
    price: Decimal
    total_amount: Decimal
    fee: Decimal
    net_amount: Decimal
    cash_before: Decimal
    cash_after: Decimal
    shares_before: Decimal
    shares_after: Decimal
    executed_at: datetime
    execution_venue: Optional[str]
    notes: Optional[str]

    class Config:
        from_attributes = True
class ExitPositionRequest(BaseModel):
    """Request to close a position (sell all shares of a symbol)"""
    symbol: str = Field(..., min_length=1, max_length=10, description="Stock symbol to exit")
    order_type: OrderType = Field(OrderType.MARKET, description="Order type (MARKET or LIMIT)")
    price: Optional[Decimal] = Field(None, gt=0, description="Limit price if using LIMIT order")
    
    @validator('symbol')
    def symbol_uppercase(cls, v):
        return v.upper().strip()
    
    @validator('price')
    def validate_limit_price(cls, v, values):
        order_type = values.get('order_type')
        if order_type == OrderType.LIMIT and v is None:
            raise ValueError("price is required for LIMIT orders")
        return v

    class Config:
        use_enum_values = True


class ExitPositionResponse(BaseModel):
    """Response after closing a position"""
    success: bool
    message: str
    order: Optional[OrderResponse]
    closed_quantity: Decimal
    estimated_proceeds: Optional[Decimal]

    class Config:
        from_attributes = True
