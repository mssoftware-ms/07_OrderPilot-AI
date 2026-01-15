"""Profile configuration for OrderPilot-AI.

Contains ProfileConfig - the complete trading profile configuration model.
"""

from __future__ import annotations

import logging
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .config_types import (
    AIConfig,
    AlertConfig,
    BacktestConfig,
    BrokerConfig,
    BrokerType,
    DatabaseConfig,
    ExecutionConfig,
    MarketDataProviderConfig,
    MonitoringConfig,
    TradingConfig,
    TradingEnvironment,
    TradingMode,
    UIConfig,
)

logger = logging.getLogger(__name__)


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
    def validate_trading_mode_config(self) -> ProfileConfig:
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
    ) -> ProfileConfig:
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
    ) -> ProfileConfig:
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
    ) -> ProfileConfig:
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
