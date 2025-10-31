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
from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


class TradingEnvironment(Enum):
    """Trading environment modes."""
    DEVELOPMENT = "development"
    PAPER = "paper"  # Paper trading / simulation
    PRODUCTION = "production"  # Live trading with real money


class BrokerType(Enum):
    """Supported broker types."""
    MOCK = "mock"
    IBKR = "ibkr"  # Interactive Brokers
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
    timeout: int = 30  # seconds
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
        use_enum_values=True
    )

    profile_name: str = "default"
    description: str = "Default trading profile"
    environment: TradingEnvironment = TradingEnvironment.PAPER
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


class AppSettings(BaseSettings):
    """Application-wide settings from environment variables."""
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )

    app_env: str = Field(default="dev", alias="TRADING_ENV")
    app_log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    profile: str = Field(default="paper", alias="TRADING_PROFILE")
    config_dir: str = Field(default="./config", alias="CONFIG_DIR")


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
        """Retrieve a credential from Windows Credential Manager.

        Args:
            key: Credential key (e.g., 'openai_api_key')
            service: Service name for keyring

        Returns:
            Credential value or None if not found
        """
        if key in self._credentials:
            return self._credentials[key]

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

    @property
    def profile(self) -> ProfileConfig:
        """Get the current profile configuration."""
        if not self._profile_config:
            self.load_profile()
        return self._profile_config


# Global configuration instance
config_manager = ConfigManager()
