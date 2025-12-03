"""Crisis Simulation Database Models - Fixed Version"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.models.base import Base

class CrisisType(enum.Enum):
    GREAT_DEPRESSION = "great_depression"
    BLACK_MONDAY = "black_monday" 
    DOTCOM_BUBBLE = "dotcom_bubble"
    FINANCIAL_CRISIS_2008 = "financial_crisis_2008"
    COVID_CRASH = "covid_crash"

class SimulationStatus(enum.Enum):
    PENDING = "pending"
    ACTIVE = "active" 
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class CrisisSimulation(Base):
    __tablename__ = "crisis_simulations" 

    id = Column(Integer, primary_key=True, index=True)
    crisis_type = Column(SQLEnum(CrisisType), nullable=False)
    status = Column(SQLEnum(SimulationStatus), default=SimulationStatus.PENDING)
    
    # Time Management
    real_start_time = Column(DateTime, nullable=True)
    real_end_time = Column(DateTime, nullable=True)
    historical_start_date = Column(DateTime, nullable=False)
    historical_end_date = Column(DateTime, nullable=False)
    current_historical_time = Column(DateTime, nullable=True)
    
    # Simulation Configuration
    duration_minutes = Column(Integer, default=60)
    time_compression_ratio = Column(Float, nullable=False)
    
    # Phase tracking
    phase_config = Column(JSON, nullable=False)
    current_phase = Column(String(50), nullable=True)
    
    # Admin Control
    created_by = Column(Integer, nullable=False)  # No FK - just user_id
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Metadata
    max_participants = Column(Integer, default=100)
    is_competitive = Column(Boolean, default=True)
    
    # Relationships
    participants = relationship("SimulationParticipant", back_populates="simulation", cascade="all, delete-orphan")
    leaderboard = relationship("SimulationLeaderboard", back_populates="simulation", cascade="all, delete-orphan")

class SimulationParticipant(Base):
    __tablename__ = "simulation_participants"

    id = Column(Integer, primary_key=True, index=True)
    simulation_id = Column(Integer, ForeignKey("crisis_simulations.id"), nullable=False)
    user_id = Column(Integer, nullable=False, index=True)  # No FK - just reference
    
    # Participation Status
    joined_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    finished_at = Column(DateTime, nullable=True)
    
    # Portfolio values
    initial_cash = Column(Float, default=100000.0)
    initial_portfolio_value = Column(Float, default=100000.0)
    current_cash = Column(Float, default=100000.0)
    current_portfolio_value = Column(Float, nullable=True)
    current_total_value = Column(Float, nullable=True)
    
    # Performance Metrics
    total_return_pct = Column(Float, default=0.0)
    max_drawdown_pct = Column(Float, default=0.0)
    sharpe_ratio = Column(Float, nullable=True)
    total_trades = Column(Integer, default=0)
    profitable_trades = Column(Integer, default=0)
    
    # Risk Metrics
    max_leverage_used = Column(Float, default=1.0)
    margin_calls_count = Column(Integer, default=0)
    
    # Behavioral Tracking
    detected_biases = Column(JSON, default={})
    
    # Final Ranking
    final_rank = Column(Integer, nullable=True)
    final_score = Column(Float, nullable=True)
    
    # Relationships
    simulation = relationship("CrisisSimulation", back_populates="participants")
    orders = relationship("SimulationOrder", back_populates="participant", cascade="all, delete-orphan")
    positions = relationship("SimulationPosition", back_populates="participant", cascade="all, delete-orphan")


class SimulationOrder(Base):
    """
    Orders placed during simulations
    Completely isolated from live trading orders
    """
    __tablename__ = "simulation_orders"

    id = Column(Integer, primary_key=True, index=True)
    participant_id = Column(Integer, ForeignKey("simulation_participants.id"), nullable=False)
    
    # Order Details
    symbol = Column(String(20), nullable=False, index=True)
    order_type = Column(String(20), nullable=False)  # MARKET, LIMIT, STOP
    side = Column(String(10), nullable=False)  # BUY, SELL
    quantity = Column(Float, nullable=False)
    
    # Pricing
    limit_price = Column(Float, nullable=True)
    stop_price = Column(Float, nullable=True)
    filled_price = Column(Float, nullable=True)
    filled_quantity = Column(Float, default=0.0)
    
    # Status
    status = Column(String(20), default="PENDING")  # PENDING, FILLED, PARTIAL, REJECTED, CANCELLED
    
    # Timestamps (Historical Time)
    placed_at_historical = Column(DateTime, nullable=False)
    filled_at_historical = Column(DateTime, nullable=True)
    
    # Timestamps (Real Time)
    placed_at_real = Column(DateTime, default=datetime.utcnow)
    filled_at_real = Column(DateTime, nullable=True)
    
    # Execution Details
    commission = Column(Float, default=0.0)
    rejection_reason = Column(String(255), nullable=True)
    
    # Relationships
    participant = relationship("SimulationParticipant", back_populates="orders")


class SimulationPosition(Base):
    """
    Current positions held during simulation
    """
    __tablename__ = "simulation_positions"

    id = Column(Integer, primary_key=True, index=True)
    participant_id = Column(Integer, ForeignKey("simulation_participants.id"), nullable=False)
    
    # Position Details
    symbol = Column(String(20), nullable=False, index=True)
    quantity = Column(Float, nullable=False)
    average_cost = Column(Float, nullable=False)
    current_price = Column(Float, nullable=True)
    
    # P&L
    unrealized_pnl = Column(Float, default=0.0)
    unrealized_pnl_pct = Column(Float, default=0.0)
    realized_pnl = Column(Float, default=0.0)
    
    # Timestamps
    opened_at = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    participant = relationship("SimulationParticipant", back_populates="positions")


class SimulationLeaderboard(Base):
    """
    Real-time leaderboard for competitive simulations
    Updated periodically during simulation
    """
    __tablename__ = "simulation_leaderboard"

    id = Column(Integer, primary_key=True, index=True)
    simulation_id = Column(Integer, ForeignKey("crisis_simulations.id"), nullable=False)
    user_id = Column(Integer, nullable=False, index=True)  # No FK - just reference
    
    # Rankings
    current_rank = Column(Integer, nullable=False)
    previous_rank = Column(Integer, nullable=True)
    
    # Performance Metrics
    total_value = Column(Float, nullable=False)
    total_return_pct = Column(Float, nullable=False)
    sharpe_ratio = Column(Float, nullable=True)
    
    # Competition Score (weighted combination of metrics)
    competition_score = Column(Float, nullable=False)
    
    # Snapshot Time
    snapshot_at_historical = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    simulation = relationship("CrisisSimulation", back_populates="leaderboard")


class SimulationSnapshot(Base):
    """
    Periodic snapshots of participant state for time-travel/replay
    """
    __tablename__ = "simulation_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    participant_id = Column(Integer, ForeignKey("simulation_participants.id"), nullable=False)
    
    # Snapshot Timing
    historical_time = Column(DateTime, nullable=False)
    real_time = Column(DateTime, default=datetime.utcnow)
    
    # Portfolio State (JSON)
    portfolio_state = Column(JSON, nullable=False)  # {cash, positions: [{symbol, qty, price}], total_value}
    
    # Performance at this point
    total_return_pct = Column(Float, default=0.0)
    total_value = Column(Float, nullable=False)