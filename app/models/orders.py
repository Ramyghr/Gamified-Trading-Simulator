from sqlalchemy import Column, Integer, String, Numeric, DateTime, Enum, ForeignKey, Index, CheckConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.config.database import Base


class OrderType(str, enum.Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"
    TAKE_PROFIT = "TAKE_PROFIT"


class OrderSide(str, enum.Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderStatus(str, enum.Enum):
    PENDING = "PENDING"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELED = "CANCELED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class TimeInForce(str, enum.Enum):
    GTC = "GTC"  # Good Till Canceled
    IOC = "IOC"  # Immediate or Cancel
    FOK = "FOK"  # Fill or Kill
    DAY = "DAY"  # Day order


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    symbol = Column(String(10), nullable=False, index=True)
    
    # Order details
    order_type = Column(Enum(OrderType), nullable=False)
    side = Column(Enum(OrderSide), nullable=False)
    quantity = Column(Numeric(20, 8), nullable=False)
    filled_quantity = Column(Numeric(20, 8), nullable=False, default=0)
    
    # Pricing
    price = Column(Numeric(20, 8), nullable=True)  # Limit price (for LIMIT/STOP_LIMIT)
    stop_price = Column(Numeric(20, 8), nullable=True)  # Stop trigger price
    average_fill_price = Column(Numeric(20, 8), nullable=True)
    
    # Status and lifecycle
    status = Column(Enum(OrderStatus), nullable=False, default=OrderStatus.PENDING, index=True)
    time_in_force = Column(Enum(TimeInForce), nullable=False, default=TimeInForce.GTC)
    
    # Financial tracking
    reserved_amount = Column(Numeric(20, 2), nullable=False, default=0)  # Cash reserved for BUY
    estimated_cost = Column(Numeric(20, 2), nullable=True)
    total_fees = Column(Numeric(20, 8), nullable=False, default=0)
    
    # Metadata
    idempotency_key = Column(String(100), unique=True, nullable=True, index=True)
    related_order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)  # For OCO pairs
    parent_order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)  # For split orders
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    executed_at = Column(DateTime, nullable=True)
    canceled_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    
    # Failure tracking
    rejection_reason = Column(String(500), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="orders")
    transactions = relationship("StockTransaction", back_populates="order", cascade="all, delete-orphan")
    related_order = relationship("Order", remote_side=[id], foreign_keys=[related_order_id])
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_user_status_created', 'user_id', 'status', 'created_at'),
        Index('idx_symbol_status', 'symbol', 'status'),
        Index('idx_status_created', 'status', 'created_at'),
        CheckConstraint('quantity > 0', name='check_quantity_positive'),
        CheckConstraint('filled_quantity >= 0', name='check_filled_quantity_non_negative'),
        CheckConstraint('filled_quantity <= quantity', name='check_filled_quantity_lte_quantity'),
    )

    def __repr__(self):
        return f"<Order(id={self.id}, user_id={self.user_id}, symbol={self.symbol}, type={self.order_type}, side={self.side}, status={self.status})>"
    
    @property
    def remaining_quantity(self):
        """Calculate unfilled quantity"""
        return self.quantity - self.filled_quantity
    @remaining_quantity.setter
    def remaining_quantity(self, value):
        """Allow setting remaining quantity by adjusting filled_quantity."""
        if value > self.quantity:
            raise ValueError("Remaining quantity cannot exceed total order quantity.")
        self.filled_quantity = self.quantity - value

    @property
    def is_active(self):
        """Check if order is still active"""
        return self.status in [OrderStatus.PENDING, OrderStatus.PARTIALLY_FILLED]
    
    @property
    def fill_percentage(self):
        """Calculate fill percentage"""
        if self.quantity == 0:
            return 0
        return float(self.filled_quantity / self.quantity * 100)