"""Database Models for OrderPilot-AI Trading Application.

Defines SQLAlchemy models for market data, orders, trades, alerts,
AI telemetry, and other persistent data structures.
"""

import enum
from datetime import datetime

from sqlalchemy import (
    DECIMAL,
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class OrderStatus(enum.Enum):
    """Order status enumeration."""
    PENDING = "pending"
    SUBMITTED = "submitted"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"


class OrderSide(enum.Enum):
    """Order side (buy/sell)."""
    BUY = "buy"
    SELL = "sell"


class OrderType(enum.Enum):
    """Order type enumeration."""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class TimeInForce(enum.Enum):
    """Time in force for orders."""
    DAY = "DAY"
    GTC = "GTC"  # Good Till Cancelled
    IOC = "IOC"  # Immediate or Cancel
    FOK = "FOK"  # Fill or Kill


class AlertPriority(enum.Enum):
    """Alert priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class MarketBar(Base):
    """1-second market data bars."""
    __tablename__ = 'market_bars'

    id = Column(Integer, primary_key=True)
    symbol = Column(String(50), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    open = Column(DECIMAL(20, 8), nullable=False)
    high = Column(DECIMAL(20, 8), nullable=False)
    low = Column(DECIMAL(20, 8), nullable=False)
    close = Column(DECIMAL(20, 8), nullable=False)
    volume = Column(Integer, nullable=False, default=0)

    # Additional fields
    vwap = Column(DECIMAL(20, 8))  # Volume Weighted Average Price
    bid = Column(DECIMAL(20, 8))
    ask = Column(DECIMAL(20, 8))
    bid_size = Column(Integer)
    ask_size = Column(Integer)

    # Metadata
    source = Column(String(50))  # Data source (IBKR, TR, etc.)
    is_interpolated = Column(Boolean, default=False)  # For filled gaps
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('symbol', 'timestamp', name='uq_symbol_timestamp'),
        Index('idx_symbol_timestamp', 'symbol', 'timestamp'),
    )


class Order(Base):
    """Trading orders."""
    __tablename__ = 'orders'

    id = Column(Integer, primary_key=True)
    order_id = Column(String(100), unique=True, nullable=False, index=True)
    broker_order_id = Column(String(100), index=True)  # Broker's order ID

    # Order details
    symbol = Column(String(50), nullable=False, index=True)
    side = Column(SQLEnum(OrderSide), nullable=False)
    order_type = Column(SQLEnum(OrderType), nullable=False)
    quantity = Column(DECIMAL(20, 8), nullable=False)
    limit_price = Column(DECIMAL(20, 8))
    stop_price = Column(DECIMAL(20, 8))
    time_in_force = Column(SQLEnum(TimeInForce), nullable=False)

    # Status
    status = Column(SQLEnum(OrderStatus), nullable=False, default=OrderStatus.PENDING)
    filled_quantity = Column(DECIMAL(20, 8), default=0)
    average_fill_price = Column(DECIMAL(20, 8))
    commission = Column(DECIMAL(20, 8), default=0)

    # Strategy info
    strategy_name = Column(String(100), index=True)
    signal_confidence = Column(Float)

    # AI Analysis
    ai_analysis = Column(JSON)  # Structured output from AI
    ai_approved = Column(Boolean)
    ai_rejection_reason = Column(Text)
    manual_override = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    submitted_at = Column(DateTime)
    filled_at = Column(DateTime)
    cancelled_at = Column(DateTime)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Risk management
    stop_loss_price = Column(DECIMAL(20, 8))
    take_profit_price = Column(DECIMAL(20, 8))
    max_loss_amount = Column(DECIMAL(20, 8))

    # Metadata
    notes = Column(Text)
    meta_data = Column(JSON)

    # Relationships
    executions = relationship("Execution", back_populates="order", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_order_status', 'status'),
        Index('idx_order_created', 'created_at'),
    )


class Execution(Base):
    """Order executions/fills."""
    __tablename__ = 'executions'

    id = Column(Integer, primary_key=True)
    execution_id = Column(String(100), unique=True, nullable=False)
    order_id = Column(String(100), ForeignKey('orders.order_id'), nullable=False)

    # Execution details
    symbol = Column(String(50), nullable=False)
    side = Column(SQLEnum(OrderSide), nullable=False)
    quantity = Column(DECIMAL(20, 8), nullable=False)
    price = Column(DECIMAL(20, 8), nullable=False)
    commission = Column(DECIMAL(20, 8), default=0)

    # Broker info
    broker = Column(String(50))
    broker_execution_id = Column(String(100))

    # Timestamps
    executed_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Metadata
    meta_data = Column(JSON)

    # Relationships
    order = relationship("Order", back_populates="executions")

    __table_args__ = (
        Index('idx_exec_order', 'order_id'),
        Index('idx_exec_time', 'executed_at'),
    )


class Position(Base):
    """Current positions."""
    __tablename__ = 'positions'

    id = Column(Integer, primary_key=True)
    symbol = Column(String(50), nullable=False, unique=True, index=True)

    # Position details
    quantity = Column(DECIMAL(20, 8), nullable=False)
    average_cost = Column(DECIMAL(20, 8), nullable=False)
    current_price = Column(DECIMAL(20, 8))
    market_value = Column(DECIMAL(20, 8))

    # P&L
    unrealized_pnl = Column(DECIMAL(20, 8))
    realized_pnl = Column(DECIMAL(20, 8), default=0)

    # Risk metrics
    max_position_value = Column(DECIMAL(20, 8))
    stop_loss_price = Column(DECIMAL(20, 8))
    take_profit_price = Column(DECIMAL(20, 8))

    # Timestamps
    opened_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Strategy
    strategy_name = Column(String(100))

    # Metadata
    meta_data = Column(JSON)


class Alert(Base):
    """Trading alerts and notifications."""
    __tablename__ = 'alerts'

    id = Column(Integer, primary_key=True)
    alert_id = Column(String(100), unique=True, nullable=False)

    # Alert details
    symbol = Column(String(50), index=True)
    alert_type = Column(String(50), nullable=False)  # price_cross, indicator_signal, etc.
    priority = Column(SQLEnum(AlertPriority), nullable=False)

    # Trigger conditions
    condition = Column(JSON, nullable=False)  # Condition that triggered the alert
    triggered_value = Column(DECIMAL(20, 8))

    # AI Triage
    ai_triage_score = Column(Float)  # 0-1 importance score
    ai_reasoning = Column(Text)
    ai_suggested_action = Column(JSON)

    # Status
    is_active = Column(Boolean, default=True)
    is_acknowledged = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    triggered_at = Column(DateTime)
    acknowledged_at = Column(DateTime)
    cleared_at = Column(DateTime)

    # Metadata
    notes = Column(Text)
    meta_data = Column(JSON)

    __table_args__ = (
        Index('idx_alert_active', 'is_active'),
        Index('idx_alert_priority', 'priority'),
        Index('idx_alert_created', 'created_at'),
    )


class Strategy(Base):
    """Strategy configurations and parameters."""
    __tablename__ = 'strategies'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)

    # Configuration
    is_active = Column(Boolean, default=False)
    parameters = Column(JSON, nullable=False)

    # Performance tracking
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    total_pnl = Column(DECIMAL(20, 8), default=0)
    sharpe_ratio = Column(Float)
    max_drawdown = Column(Float)

    # AI Enhancement
    ai_optimization_enabled = Column(Boolean, default=False)
    ai_suggested_params = Column(JSON)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_signal_at = Column(DateTime)

    # Metadata
    description = Column(Text)
    meta_data = Column(JSON)


class BacktestResult(Base):
    """Backtesting results."""
    __tablename__ = 'backtest_results'

    id = Column(Integer, primary_key=True)
    backtest_id = Column(String(100), unique=True, nullable=False)

    # Test parameters
    strategy_name = Column(String(100), nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    initial_capital = Column(DECIMAL(20, 8), nullable=False)
    parameters = Column(JSON, nullable=False)

    # Results
    final_capital = Column(DECIMAL(20, 8))
    total_return = Column(Float)
    annual_return = Column(Float)
    total_trades = Column(Integer)
    winning_trades = Column(Integer)
    losing_trades = Column(Integer)

    # Risk metrics
    sharpe_ratio = Column(Float)
    sortino_ratio = Column(Float)
    max_drawdown = Column(Float)
    volatility = Column(Float)

    # Trade statistics
    avg_trade_return = Column(Float)
    best_trade = Column(Float)
    worst_trade = Column(Float)
    avg_win = Column(Float)
    avg_loss = Column(Float)
    win_rate = Column(Float)

    # AI Review
    ai_review = Column(JSON)  # Structured AI review
    ai_insights = Column(Text)
    ai_suggested_improvements = Column(JSON)

    # Execution details
    execution_time_seconds = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Full results
    trade_log = Column(JSON)  # Detailed trade-by-trade log
    equity_curve = Column(JSON)  # Time series of portfolio value
    meta_data = Column(JSON)

    __table_args__ = (
        Index('idx_backtest_strategy', 'strategy_name'),
        Index('idx_backtest_created', 'created_at'),
    )


class AITelemetry(Base):
    """AI API usage telemetry and cost tracking."""
    __tablename__ = 'ai_telemetry'

    id = Column(Integer, primary_key=True)
    request_id = Column(String(100), unique=True, nullable=False)

    # Request details
    request_type = Column(String(50), nullable=False)  # order_analysis, alert_triage, etc.
    model = Column(String(50), nullable=False)
    prompt_version = Column(String(20))

    # Usage metrics
    input_tokens = Column(Integer)
    output_tokens = Column(Integer)
    total_tokens = Column(Integer)
    estimated_cost = Column(DECIMAL(10, 6))  # In EUR

    # Performance
    latency_ms = Column(Integer)
    success = Column(Boolean)
    error_message = Column(Text)

    # Context
    context_type = Column(String(50))  # order, alert, backtest, etc.
    context_id = Column(String(100))  # ID of the related entity

    # Structured I/O
    request_payload = Column(JSON)
    response_payload = Column(JSON)

    # Timestamps
    requested_at = Column(DateTime, nullable=False)
    responded_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Metadata
    meta_data = Column(JSON)

    __table_args__ = (
        Index('idx_ai_telemetry_type', 'request_type'),
        Index('idx_ai_telemetry_requested', 'requested_at'),
        Index('idx_ai_telemetry_context', 'context_type', 'context_id'),
    )


class AICache(Base):
    """Cache for AI responses to reduce API calls."""
    __tablename__ = 'ai_cache'

    id = Column(Integer, primary_key=True)
    cache_key = Column(String(255), unique=True, nullable=False, index=True)

    # Cache content
    request_hash = Column(String(64), nullable=False)  # SHA256 of request
    response = Column(JSON, nullable=False)

    # Metadata
    request_type = Column(String(50))
    model = Column(String(50))

    # Expiration
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    hit_count = Column(Integer, default=0)

    # Storage optimization
    is_compressed = Column(Boolean, default=False)

    __table_args__ = (
        Index('idx_ai_cache_expires', 'expires_at'),
    )


class AuditLog(Base):
    """Comprehensive audit trail for all trading activities."""
    __tablename__ = 'audit_log'

    id = Column(Integer, primary_key=True)
    event_id = Column(String(100), unique=True, nullable=False)

    # Event details
    event_type = Column(String(50), nullable=False)  # order_created, position_closed, etc.
    entity_type = Column(String(50))  # order, position, alert, etc.
    entity_id = Column(String(100))

    # Action details
    action = Column(String(100), nullable=False)
    actor = Column(String(100))  # user, strategy, ai, system

    # State tracking
    previous_state = Column(JSON)
    new_state = Column(JSON)
    changes = Column(JSON)

    # Context
    ip_address = Column(String(45))
    user_agent = Column(String(255))
    session_id = Column(String(100))

    # Timestamps
    occurred_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Metadata
    meta_data = Column(JSON)

    __table_args__ = (
        Index('idx_audit_event_type', 'event_type'),
        Index('idx_audit_entity', 'entity_type', 'entity_id'),
        Index('idx_audit_occurred', 'occurred_at'),
    )


class SystemMetrics(Base):
    """System performance and health metrics."""
    __tablename__ = 'system_metrics'

    id = Column(Integer, primary_key=True)

    # Performance metrics
    cpu_usage_percent = Column(Float)
    memory_usage_mb = Column(Float)
    disk_usage_percent = Column(Float)

    # Trading metrics
    active_orders = Column(Integer)
    open_positions = Column(Integer)
    total_portfolio_value = Column(DECIMAL(20, 8))
    daily_pnl = Column(DECIMAL(20, 8))

    # Connection health
    broker_connected = Column(Boolean)
    market_data_connected = Column(Boolean)
    ai_service_healthy = Column(Boolean)

    # Latency metrics
    order_latency_ms = Column(Float)
    market_data_latency_ms = Column(Float)
    ai_response_latency_ms = Column(Float)

    # Rate limiting
    api_calls_remaining = Column(Integer)
    ai_budget_remaining = Column(DECIMAL(10, 2))

    # Timestamp
    recorded_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_metrics_recorded', 'recorded_at'),
    )