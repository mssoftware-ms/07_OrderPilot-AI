"""Configuration management for OrderPilot-AI Trading Application.

Manages trading profiles, broker credentials, API keys, and runtime settings.
Uses Pydantic for validation and supports YAML/JSON file formats.
"""

import json
import logging
import os
from datetime import datetime
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Any

import keyring
import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


class TradingEnvironment(Enum):
    """Trading environment modes."""
    DEVELOPMENT = "development"
    PAPER = "paper"  # Paper trading / simulation
    PRODUCTION = "production"  # Live trading with real money


class TradingMode(Enum):
    """Trading execution modes.

    BACKTEST: Historical backtesting with synthetic data
    PAPER: Real-time paper trading with simulated execution
    LIVE: Real-time live trading with actual money
    """
    BACKTEST = "backtest"
    PAPER = "paper"
    LIVE = "live"


class BrokerType(Enum):
    """Supported broker types."""
    MOCK = "mock"
    IBKR = "ibkr"  # Interactive Brokers
    ALPACA = "alpaca"  # Alpaca Markets
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
    start_date: datetime | None = None
    end_date: datetime | None = None
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


class ProfileConfig(BaseModel):
    """Complete trading profile configuration."""
    model_config = ConfigDict(
        validate_assignment=True,
        use_enum_values=False  # Keep enums as enum instances
    )

    profile_name: str = "default"
    description: str = "Default trading profile"
    environment: TradingEnvironment = TradingEnvironment.PAPER
    trading_mode: TradingMode = TradingMode.PAPER
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Sub-configurations
    broker: BrokerConfig = Field(default_factory=BrokerConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    ai: AIConfig = Field(default_factory=AIConfig)
    trading: TradingConfig = Field(default_factory=TradingConfig)
    backtest: BacktestConfig = Field(default_factory=BacktestConfig)
    alerts: AlertConfig = Field(default_factory=AlertConfig)
    ui: UIConfig = Field(default_factory=UIConfig)
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)
    execution: ExecutionConfig = Field(default_factory=ExecutionConfig)
    market_data: MarketDataProviderConfig = Field(default_factory=MarketDataProviderConfig)

    # Feature flags
    features: dict[str, bool] = Field(default_factory=lambda: {
        "paper_trading": True,
        "live_trading": False,
        "backtesting": True,
        "optimization": True,
        "ai_analysis": True,
        "advanced_charts": True,
        "options_trading": False,
        "futures_trading": False,
        "crypto_trading": False,
        "news_sentiment": False
    })

    @field_validator('environment')
    @classmethod
    def validate_environment(cls, v: TradingEnvironment, info) -> TradingEnvironment:
        """Ensure production environment has proper safeguards."""
        if v == TradingEnvironment.PRODUCTION:
            values = info.data
            if 'execution' in values and not values['execution'].manual_approval_default:
                logger.warning("Auto-approval enabled in production - high risk!")
        return v

    @field_validator('trading_mode')
    @classmethod
    def validate_trading_mode_field(cls, v: TradingMode | str) -> TradingMode:
        """Convert string to enum if needed."""
        if isinstance(v, str):
            v = TradingMode(v)
        return v

    @model_validator(mode='after')
    def validate_trading_mode_config(self) -> 'ProfileConfig':
        """Ensure trading mode has appropriate safety settings."""
        mode = self.trading_mode

        if mode == TradingMode.LIVE:
            # Live trading requires strict safeguards
            if not self.execution.manual_approval_default:
                raise ValueError(
                    "Live trading mode requires manual_approval_default=True"
                )
            if not self.execution.emergency_stop_active:
                logger.warning("Emergency stop disabled in LIVE mode - high risk!")

            if self.broker.paper_trading:
                raise ValueError(
                    "Live trading mode incompatible with paper_trading=True"
                )

        elif mode == TradingMode.BACKTEST:
            # Backtest mode should use mock broker
            if self.broker.broker_type != BrokerType.MOCK:
                logger.warning(
                    f"Backtest mode should use MOCK broker, got {self.broker.broker_type}"
                )

        elif mode == TradingMode.PAPER:
            # Paper trading should have paper_trading enabled
            if not self.broker.paper_trading:
                logger.warning(
                    "Paper mode should have paper_trading=True"
                )

        return self

    def is_safe_for_mode(self, mode: TradingMode) -> tuple[bool, list[str]]:
        """Check if current configuration is safe for specified mode.

        Args:
            mode: Trading mode to validate

        Returns:
            Tuple of (is_safe, list of warnings/errors)
        """
        issues = []

        if mode == TradingMode.LIVE:
            if not self.execution.manual_approval_default:
                issues.append("Live mode requires manual approval for orders")
            if not self.execution.emergency_stop_active:
                issues.append("Emergency stop should be active in live mode")
            if self.broker.paper_trading:
                issues.append("Paper trading must be disabled for live mode")
            if self.broker.broker_type == BrokerType.MOCK:
                issues.append("Mock broker cannot be used for live trading")

        elif mode == TradingMode.BACKTEST:
            if self.broker.broker_type != BrokerType.MOCK:
                issues.append("Backtest mode should use mock broker")

        elif mode == TradingMode.PAPER:
            if not self.broker.paper_trading:
                issues.append("Paper trading should be enabled for paper mode")

        return len(issues) == 0, issues

    def switch_to_mode(self, mode: TradingMode, validate: bool = True) -> None:
        """Switch to specified trading mode with safety checks.

        Args:
            mode: Trading mode to switch to
            validate: Whether to validate the switch (default: True)

        Raises:
            ValueError: If validation fails and validate=True
        """
        if validate:
            is_safe, issues = self.is_safe_for_mode(mode)
            if not is_safe:
                raise ValueError(
                    f"Cannot switch to {mode.value} mode:\n" +
                    "\n".join(f"  - {issue}" for issue in issues)
                )

        # Use object.__setattr__ to bypass Pydantic validation when validate=False
        if validate:
            self.trading_mode = mode
        else:
            object.__setattr__(self, 'trading_mode', mode)

        object.__setattr__(self, 'updated_at', datetime.utcnow())
        logger.info(f"Switched to trading mode: {mode.value}")

    @staticmethod
    def create_backtest_profile(
        name: str = "backtest",
        initial_capital: Decimal = Decimal("10000")
    ) -> "ProfileConfig":
        """Create a profile optimized for backtesting.

        Args:
            name: Profile name
            initial_capital: Initial capital for backtest

        Returns:
            ProfileConfig configured for backtesting
        """
        return ProfileConfig(
            profile_name=name,
            description="Backtesting profile",
            environment=TradingEnvironment.DEVELOPMENT,
            trading_mode=TradingMode.BACKTEST,
            broker=BrokerConfig(
                broker_type=BrokerType.MOCK,
                paper_trading=True
            ),
            backtest=BacktestConfig(
                initial_capital=initial_capital,
                include_commissions=True,
                include_slippage=True
            ),
            execution=ExecutionConfig(
                manual_approval_default=False,  # Auto-execute in backtest
                emergency_stop_active=False
            )
        )

    @staticmethod
    def create_paper_profile(
        name: str = "paper",
        broker_type: BrokerType = BrokerType.ALPACA
    ) -> "ProfileConfig":
        """Create a profile for paper trading.

        Args:
            name: Profile name
            broker_type: Broker to use for paper trading

        Returns:
            ProfileConfig configured for paper trading
        """
        return ProfileConfig(
            profile_name=name,
            description="Paper trading profile",
            environment=TradingEnvironment.PAPER,
            trading_mode=TradingMode.PAPER,
            broker=BrokerConfig(
                broker_type=broker_type,
                paper_trading=True,
                auto_reconnect=True
            ),
            execution=ExecutionConfig(
                manual_approval_default=True,
                emergency_stop_active=True,
                cancel_on_disconnect=True
            )
        )

    @staticmethod
    def create_live_profile(
        name: str = "live",
        broker_type: BrokerType = BrokerType.ALPACA
    ) -> "ProfileConfig":
        """Create a profile for live trading with maximum safety.

        Args:
            name: Profile name
            broker_type: Broker to use for live trading

        Returns:
            ProfileConfig configured for live trading

        Warning:
            Live trading involves real money. Ensure all settings are correct.
        """
        return ProfileConfig(
            profile_name=name,
            description="Live trading profile - REAL MONEY",
            environment=TradingEnvironment.PRODUCTION,
            trading_mode=TradingMode.LIVE,
            broker=BrokerConfig(
                broker_type=broker_type,
                paper_trading=False,  # REAL TRADING
                auto_reconnect=True
            ),
            execution=ExecutionConfig(
                manual_approval_default=True,  # REQUIRED
                emergency_stop_active=True,    # REQUIRED
                cancel_on_disconnect=True,
                flatten_on_disconnect=False,
                max_retry_attempts=1  # Limit retries in live
            ),
            trading=TradingConfig(
                max_daily_loss=Decimal("500"),
                max_position_size=Decimal("10000"),
                max_open_positions=5,
                allow_short_selling=False
            )
        )


class AppSettings(BaseSettings):
    """Application-wide settings from environment variables."""
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra='allow'  # Allow additional fields like watchlist
    )

    app_env: str = Field(default="dev", alias="TRADING_ENV")
    app_log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    profile: str = Field(default="paper", alias="TRADING_PROFILE")
    config_dir: str = Field(default="./config", alias="CONFIG_DIR")
    watchlist: list[str] = Field(default_factory=list)


class ConfigManager:
    """Manages application configuration and profiles."""

    def __init__(self, config_dir: Path | None = None):
        """Initialize the configuration manager.

        Args:
            config_dir: Directory containing configuration files
        """
        self.config_dir = Path(config_dir) if config_dir else Path("./config")
        self.config_dir.mkdir(parents=True, exist_ok=True)

        self.settings = AppSettings()
        self._profile_config: ProfileConfig | None = None
        self._credentials: dict[str, str] = {}

    def load_profile(self, profile_name: str | None = None) -> ProfileConfig:
        """Load a configuration profile.

        Args:
            profile_name: Name of the profile to load

        Returns:
            Loaded profile configuration
        """
        profile_name = profile_name or self.settings.profile
        profile_path = self.config_dir / f"{profile_name}.yaml"

        if profile_path.exists():
            logger.info(f"Loading profile from {profile_path}")
            with open(profile_path, encoding="utf-8") as f:
                data = yaml.safe_load(f)
                self._profile_config = ProfileConfig(**data)
        else:
            logger.info(f"Profile {profile_name} not found, using defaults")
            self._profile_config = ProfileConfig(profile_name=profile_name)
            self.save_profile()

        return self._profile_config

    def save_profile(self, profile: ProfileConfig | None = None) -> None:
        """Save the current profile to disk.

        Args:
            profile: Profile to save (uses current if not provided)
        """
        profile = profile or self._profile_config
        if not profile:
            raise ValueError("No profile to save")

        profile_path = self.config_dir / f"{profile.profile_name}.yaml"

        # Convert to dict for YAML serialization (enums to values)
        config_dict = profile.model_dump(mode='json')

        with open(profile_path, "w", encoding="utf-8") as f:
            yaml.dump(config_dict, f, default_flow_style=False, allow_unicode=True)

        logger.info(f"Profile saved to {profile_path}")

    def get_credential(self, key: str, service: str = "OrderPilot-AI") -> str | None:
        """Retrieve a credential from .env file or Windows Credential Manager.

        Priority:
        1. Check in-memory cache
        2. Check .env file in config/secrets/
        3. Check Windows Credential Manager

        Args:
            key: Credential key (e.g., 'openai_api_key', 'alpaca_api_key')
            service: Service name for keyring

        Returns:
            Credential value or None if not found
        """
        # Check cache first
        if key in self._credentials:
            return self._credentials[key]

        # Try loading from .env file
        env_file = self.config_dir / "secrets" / ".env"
        if env_file.exists():
            try:
                # Convert key to uppercase for .env format
                env_key = key.upper()
                with open(env_file, encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            if "=" in line:
                                k, v = line.split("=", 1)
                                if k.strip() == env_key:
                                    value = v.strip()
                                    # Skip placeholder values
                                    if value and not value.startswith("YOUR_") and not value.endswith("_HERE"):
                                        self._credentials[key] = value
                                        logger.debug(f"Credential {key} loaded from .env")
                                        return value
            except Exception as e:
                logger.warning(f"Failed to read .env file: {e}")

        # Fall back to keyring
        try:
            value = keyring.get_password(service, key)
            if value:
                self._credentials[key] = value
                logger.debug(f"Credential {key} loaded from keyring")
            return value
        except Exception as e:
            logger.error(f"Failed to get credential {key}: {e}")
            return None

    def set_credential(self, key: str, value: str, service: str = "OrderPilot-AI") -> None:
        """Store a credential in Windows Credential Manager.

        Args:
            key: Credential key
            value: Credential value
            service: Service name for keyring
        """
        try:
            keyring.set_password(service, key, value)
            self._credentials[key] = value
            logger.info(f"Credential {key} saved to keyring")
        except Exception as e:
            logger.error(f"Failed to set credential {key}: {e}")
            raise

    def list_profiles(self) -> list[str]:
        """List available configuration profiles.

        Returns:
            List of profile names
        """
        profiles = []

        # Get all YAML and JSON files in config directory
        for file in self.config_dir.glob("*.yaml"):
            profiles.append(file.stem)
        for file in self.config_dir.glob("*.json"):
            profiles.append(file.stem)

        # Remove duplicates and return sorted list
        return sorted(list(set(profiles)))

    def export_config(self, path: Path) -> None:
        """Export current configuration (without secrets).

        Args:
            path: Path to export configuration to
        """
        if not self._profile_config:
            raise ValueError("No profile loaded")

        config_dict = self._profile_config.model_dump(mode='json')
        config_dict['exported_at'] = datetime.utcnow().isoformat()
        config_dict['version'] = "1.0.0"

        with open(path, "w", encoding="utf-8") as f:
            json.dump(config_dict, f, indent=2, default=str)

        logger.info(f"Configuration exported to {path}")

    def save_watchlist(self) -> None:
        """Save watchlist to persistent storage."""
        watchlist_path = self.config_dir / "watchlist.json"

        try:
            with open(watchlist_path, "w", encoding="utf-8") as f:
                json.dump({"watchlist": self.settings.watchlist}, f, indent=2)
            logger.debug(f"Watchlist saved to {watchlist_path}")
        except Exception as e:
            logger.error(f"Failed to save watchlist: {e}")
            raise

    def load_watchlist(self) -> list[str]:
        """Load watchlist from persistent storage.

        Returns:
            List of symbols in watchlist
        """
        watchlist_path = self.config_dir / "watchlist.json"

        if not watchlist_path.exists():
            return []

        try:
            with open(watchlist_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                watchlist = data.get("watchlist", [])
                self.settings.watchlist = watchlist
                logger.debug(f"Loaded {len(watchlist)} symbols from watchlist")
                return watchlist
        except Exception as e:
            logger.error(f"Failed to load watchlist: {e}")
            return []

    @property
    def profile(self) -> ProfileConfig:
        """Get the current profile configuration."""
        if not self._profile_config:
            self.load_profile()
        return self._profile_config


# Global configuration instance
config_manager = ConfigManager()
