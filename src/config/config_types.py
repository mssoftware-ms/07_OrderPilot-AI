"""Configuration types and sub-models for OrderPilot-AI.

Contains enums and Pydantic sub-configuration models used by ProfileConfig.
"""

from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field


class TradingEnvironment(str, Enum):
    """Trading environment modes."""
    DEVELOPMENT = "development"
    PAPER = "paper"  # Paper trading / simulation
    PRODUCTION = "production"  # Live trading with real money


class TradingMode(str, Enum):
    """Trading execution modes.

    BACKTEST: Historical backtesting with synthetic data
    PAPER: Real-time paper trading with simulated execution
    LIVE: Real-time live trading with actual money
    """
    BACKTEST = "backtest"
    PAPER = "paper"
    LIVE = "live"


class BrokerType(str, Enum):
    """Supported broker types."""
    MOCK = "mock"
    IBKR = "ibkr"  # Interactive Brokers
    ALPACA = "alpaca"  # Alpaca Markets
    BITUNIX = "bitunix"  # Bitunix Futures
    TRADE_REPUBLIC = "trade_republic"
    DEGIRO = "degiro"
    COMDIRECT = "comdirect"
    SCALABLE_CAPITAL = "scalable_capital"


# Sub-configurations as Pydantic models

class BrokerConfig(BaseModel):
    """Broker connection configuration."""
    broker_type: BrokerType = BrokerType.MOCK
    host: str = "localhost"
    port: int = 7497  # Default IBKR TWS port
    client_id: int = 1
    account_id: str | None = None
    paper_trading: bool = True
    auto_reconnect: bool = True
    reconnect_interval: int = 10  # seconds
    order_routing: str = "SMART"  # IBKR specific
    market_data_type: int = 3  # 3 = Delayed, 1 = Live (IBKR)


class DatabaseConfig(BaseModel):
    """Database configuration."""
    engine: str = "sqlite"  # sqlite, postgresql, mysql
    path: str = "./data/orderpilot.db"  # For SQLite
    host: str | None = None  # For network databases
    port: int | None = None
    database: str | None = None
    username: str | None = None
    password: str | None = None
    pool_size: int = 5
    max_overflow: int = 10
    pool_timeout_seconds: int = 30
    auto_vacuum: bool = False
    echo: bool = False  # SQL logging


class MarketDataProviderConfig(BaseModel):
    """Market data provider configuration and toggles."""
    alpaca_enabled: bool = False
    bitunix_enabled: bool = False
    bitunix_testnet: bool = True  # DEFAULT: TESTNET for safety!
    alpha_vantage_enabled: bool = False
    finnhub_enabled: bool = False
    yahoo_enabled: bool = True
    prefer_live_broker: bool = False  # Use broker data when available


class AIConfig(BaseModel):
    """OpenAI API configuration."""
    enabled: bool = True
    model: str = "gpt-4-turbo-preview"
    temperature: float = 0.2  # Lower = more deterministic
    max_tokens: int = 4000
    timeout: int = 30  # seconds (deprecated, use timeouts dict)
    timeouts: dict[str, int] = {
        "read_ms": 30000,      # 30 seconds for read timeout
        "connect_ms": 10000    # 10 seconds for connect timeout
    }
    retry_attempts: int = 3
    retry_delay: int = 1  # seconds
    cost_limit_monthly: float = 100.0  # EUR
    cost_limit_daily: float = 20.0  # EUR
    log_prompts: bool = False
    cache_responses: bool = True
    cache_ttl: int = 3600  # seconds


class TradingConfig(BaseModel):
    """Trading parameters and risk management."""
    max_position_size: Decimal = Field(default=Decimal("10000"))
    max_portfolio_risk: float = 0.02  # 2% max portfolio risk
    max_daily_loss: Decimal = Field(default=Decimal("500"))
    max_open_positions: int = 10
    default_stop_loss_pct: float = 0.02  # 2% stop loss
    default_take_profit_pct: float = 0.05  # 5% take profit
    allow_short_selling: bool = False
    use_margin: bool = False
    margin_multiplier: float = 1.0
    slippage_model: str = "fixed"  # fixed, percentage, market_impact
    slippage_value: float = 0.001  # 0.1% for percentage model
    commission_model: str = "fixed"  # fixed, percentage, tiered
    commission_value: float = 1.0  # EUR per trade for fixed


class BacktestConfig(BaseModel):
    """Backtesting configuration."""
    initial_capital: Decimal = Field(default=Decimal("10000"))
    start_date: "datetime | None" = None
    end_date: "datetime | None" = None
    data_frequency: str = "1m"  # 1m, 5m, 15m, 30m, 1h, 1d
    include_commissions: bool = True
    include_slippage: bool = True
    benchmark: str = "SPY"  # Benchmark symbol for comparison
    random_seed: int | None = 42  # For reproducible results
    walk_forward_periods: int = 0  # 0 = no walk-forward
    optimization_metric: str = "sharpe"  # sharpe, sortino, profit, win_rate


class AlertConfig(BaseModel):
    """Alert and notification settings."""
    email_enabled: bool = False
    email_smtp_host: str = "smtp.gmail.com"
    email_smtp_port: int = 587
    email_from: str | None = None
    email_to: list[str] = Field(default_factory=list)
    push_enabled: bool = False
    push_service: str = "pushbullet"  # pushbullet, telegram, discord
    sound_enabled: bool = True
    popup_enabled: bool = True
    alert_on_order_fill: bool = True
    alert_on_stop_loss: bool = True
    alert_on_target_hit: bool = True
    alert_on_error: bool = True
    alert_on_disconnect: bool = True


class UIConfig(BaseModel):
    """User interface configuration."""
    theme: str = "dark"  # dark, light, auto
    language: str = "en"  # en, de
    chart_style: str = "candlestick"  # candlestick, ohlc, line, heikin_ashi
    default_timeframe: str = "5m"
    show_volume: bool = True
    show_indicators: bool = True
    auto_save_layout: bool = True
    confirm_orders: bool = True
    confirm_cancel: bool = False
    show_pnl_percentage: bool = True
    decimal_places: int = 2
    timezone: str = "Europe/Berlin"
    date_format: str = "%Y-%m-%d"
    time_format: str = "%H:%M:%S"


class MonitoringConfig(BaseModel):
    """Performance monitoring and metrics."""
    track_metrics: bool = True
    metrics_interval: int = 60  # seconds
    export_metrics: bool = True
    export_format: str = "json"  # json, csv, parquet
    export_path: str = "./metrics"
    track_latency: bool = True
    track_memory: bool = True
    track_cpu: bool = False
    alert_on_high_latency: bool = True
    latency_threshold_ms: int = 100
    memory_threshold_mb: int = 1000


class ExecutionConfig(BaseModel):
    """Order execution settings."""
    execution_algo: str = "market"  # market, limit, twap, vwap, iceberg
    smart_routing: bool = True
    allow_partial_fills: bool = True
    cancel_on_disconnect: bool = True
    flatten_on_disconnect: bool = False
    retry_failed_orders: bool = True
    max_retry_attempts: int = 3
    order_timeout_seconds: int = 60
    use_native_stops: bool = True  # Broker-side stop orders
    trail_stop_atr_multiplier: float = 2.0
    manual_approval_default: bool = True  # Require manual approval
    emergency_stop_active: bool = True
    kill_switch_active: bool = False


# Import datetime for forward reference resolution
from datetime import datetime  # noqa: E402

# Update forward references
BacktestConfig.model_rebuild()
