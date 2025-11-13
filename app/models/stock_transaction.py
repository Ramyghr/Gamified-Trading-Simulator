from sqlalchemy import Column, Integer, String, Numeric, DateTime, Enum, ForeignKey, Index, CheckConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.config.database import Base


class TransactionType(str, enum.Enum):
    BUY = "BUY"
    SELL = "SELL"


class StockTransaction(Base):
    __tablename__ = "stock_transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="SET NULL"), nullable=True, index=True)
    symbol = Column(String(10), nullable=False, index=True)
    
    # Transaction details
    transaction_type = Column(Enum(TransactionType), nullable=False)
    quantity = Column(Numeric(20, 8), nullable=False)
    price = Column(Numeric(20, 8), nullable=False)  # Execution price per share
    
    # Financial breakdown
    total_amount = Column(Numeric(20, 2), nullable=False)  # quantity * price
    fee = Column(Numeric(20, 8), nullable=False, default=0)
    net_amount = Column(Numeric(20, 2), nullable=False)  # total_amount ± fee
    
    # Portfolio impact
    cash_before = Column(Numeric(20, 2), nullable=False)
    cash_after = Column(Numeric(20, 2), nullable=False)
    shares_before = Column(Numeric(20, 8), nullable=False, default=0)
    shares_after = Column(Numeric(20, 8), nullable=False)
    
    # Metadata
    execution_venue = Column(String(50), nullable=True, default="SIMULATED")  # SIMULATED, MARKET_FEED, INTERNAL_MATCH
    notes = Column(String(500), nullable=True)
    
    # Timestamps
    executed_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="transactions")
    order = relationship("Order", back_populates="transactions")
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_user_symbol_executed', 'user_id', 'symbol', 'executed_at'),
        Index('idx_user_executed', 'user_id', 'executed_at'),
        CheckConstraint('quantity > 0', name='check_transaction_quantity_positive'),
        CheckConstraint('price > 0', name='check_transaction_price_positive'),
        CheckConstraint('total_amount > 0', name='check_total_amount_positive'),
        CheckConstraint('fee >= 0', name='check_fee_non_negative'),
    )

    def __repr__(self):
        return f"<StockTransaction(id={self.id}, user_id={self.user_id}, symbol={self.symbol}, type={self.transaction_type}, quantity={self.quantity}, price={self.price})>"
    
    @property
    def cash_change(self):
        """Calculate cash change from transaction"""
        return self.cash_after - self.cash_before
    
    @property
    def shares_change(self):
        """Calculate shares change from transaction"""
        return self.shares_after - self.shares_before