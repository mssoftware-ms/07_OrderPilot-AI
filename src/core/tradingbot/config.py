"""Tradingbot Configuration Models.

Validated configuration for bot operation, risk management, and LLM policy.
"""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class MarketType(str, Enum):
    """Supported market types."""
    CRYPTO = "crypto"
    NASDAQ = "nasdaq"


class KIMode(str, Enum):
    """KI operation modes.

    NO_KI: Pure rule-based operation, no LLM calls
    LOW_KI: Daily strategy selection only (1 call/day)
    FULL_KI: Daily + intraday events (regime flip, exit candidate, signal change)
    """
    NO_KI = "no_ki"
    LOW_KI = "low_ki"
    FULL_KI = "full_ki"


class TrailingMode(str, Enum):
    """Trailing stop modes."""
    PCT = "pct"          # Percentage-based trailing
    ATR = "atr"          # ATR-based trailing
    SWING = "swing"      # Swing/structure-based trailing


class TradingEnvironment(str, Enum):
    """Trading environment."""
    PAPER = "paper"
    LIVE = "live"


class BotConfig(BaseModel):
    """Main bot configuration.

    Contains all settings for bot operation including market type,
    timeframe, and enabled features.
    """
    # Market settings
    market_type: MarketType = Field(
        default=MarketType.CRYPTO,
        description="Target market type"
    )
    symbol: str = Field(
        ...,
        min_length=1,
        description="Trading symbol (e.g., BTC/USD, AAPL)"
    )
    timeframe: str = Field(
        default="1m",
        pattern=r"^\d+[mhd]$",
        description="Primary timeframe (e.g., 1m, 5m, 1h)"
    )

    # Environment
    environment: TradingEnvironment = Field(
        default=TradingEnvironment.PAPER,
        description="Trading environment (paper/live)"
    )

    # KI settings
    ki_mode: KIMode = Field(
        default=KIMode.NO_KI,
        description="KI operation mode"
    )

    # Trailing stop settings
    trailing_mode: TrailingMode = Field(
        default=TrailingMode.ATR,
        description="Default trailing stop mode"
    )

    # Feature flags
    daily_strategy_selection: bool = Field(
        default=True,
        description="Enable daily strategy selection"
    )
    auto_trade: bool = Field(
        default=False,
        description="Enable automatic trade execution"
    )
    show_debug_hud: bool = Field(
        default=False,
        description="Show debug HUD on chart"
    )

    @field_validator('symbol')
    @classmethod
    def validate_symbol(cls, v: str) -> str:
        """Normalize symbol to uppercase."""
        return v.upper().strip()


class RiskConfig(BaseModel):
    """Risk management configuration.

    Defines position sizing, stop-loss parameters, and risk limits.
    """
    # Position sizing
    risk_per_trade_pct: float = Field(
        default=1.0,
        ge=0.1,
        le=10.0,
        description="Risk per trade as % of account"
    )
    max_position_size_pct: float = Field(
        default=20.0,
        ge=1.0,
        le=100.0,
        description="Maximum position size as % of account"
    )

    # Stop-loss settings
    initial_stop_loss_pct: float = Field(
        default=2.0,
        ge=0.1,
        le=20.0,
        description="Initial stop-loss in %"
    )

    # Trailing stop parameters
    trailing_pct_distance: float = Field(
        default=1.5,
        ge=0.1,
        le=20.0,
        description="Trailing stop distance in % (PCT mode)"
    )
    trailing_atr_multiple: float = Field(
        default=2.0,
        ge=0.5,
        le=10.0,
        description="ATR multiple for trailing (ATR mode)"
    )
    trailing_min_step_pct: float = Field(
        default=0.1,
        ge=0.01,
        le=1.0,
        description="Minimum step for trailing stop updates"
    )
    trailing_cooldown_bars: int = Field(
        default=3,
        ge=1,
        le=20,
        description="Cooldown bars between trailing updates"
    )

    # Risk limits
    max_trades_per_day: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum trades per day"
    )
    max_concurrent_positions: int = Field(
        default=1,
        ge=1,
        le=10,
        description="Maximum concurrent positions"
    )
    max_daily_loss_pct: float = Field(
        default=5.0,
        ge=0.5,
        le=50.0,
        description="Maximum daily loss in % (kill-switch)"
    )
    loss_streak_cooldown: int = Field(
        default=3,
        ge=0,
        le=10,
        description="Cooldown trades after N consecutive losses"
    )

    # Fees/Slippage
    expected_slippage_pct: float = Field(
        default=0.05,
        ge=0.0,
        le=1.0,
        description="Expected slippage in %"
    )
    commission_pct: float = Field(
        default=0.1,
        ge=0.0,
        le=1.0,
        description="Commission per trade in %"
    )

    # Market-specific defaults
    @classmethod
    def crypto_defaults(cls) -> "RiskConfig":
        """Get conservative defaults for crypto trading."""
        return cls(
            initial_stop_loss_pct=3.0,
            trailing_pct_distance=2.0,
            trailing_atr_multiple=2.5,
            expected_slippage_pct=0.1,
            commission_pct=0.1
        )

    @classmethod
    def nasdaq_defaults(cls) -> "RiskConfig":
        """Get conservative defaults for NASDAQ trading."""
        return cls(
            initial_stop_loss_pct=1.5,
            trailing_pct_distance=1.0,
            trailing_atr_multiple=1.5,
            expected_slippage_pct=0.02,
            commission_pct=0.0  # Commission-free on many platforms
        )


class LLMPolicyConfig(BaseModel):
    """LLM/KI call policy configuration.

    Defines when and how LLM is called, with budget and safety limits.
    """
    # Call policy
    daily_calls_max: int = Field(
        default=5,
        ge=1,
        le=50,
        description="Maximum LLM calls per day"
    )
    intraday_cooldown_minutes: int = Field(
        default=15,
        ge=1,
        le=120,
        description="Minimum minutes between intraday calls"
    )

    # Call triggers (for FULL_KI mode)
    call_on_regime_flip: bool = Field(
        default=True,
        description="Call LLM on regime change"
    )
    call_on_exit_candidate: bool = Field(
        default=True,
        description="Call LLM on potential exit signal"
    )
    call_on_signal_change: bool = Field(
        default=False,
        description="Call LLM on entry signal changes"
    )

    # Model settings
    model: str = Field(
        default="gpt-4o-mini",
        description="OpenAI model to use"
    )
    temperature: float = Field(
        default=0.1,
        ge=0.0,
        le=1.0,
        description="Temperature for deterministic outputs"
    )
    max_tokens: int = Field(
        default=500,
        ge=100,
        le=4000,
        description="Maximum response tokens"
    )

    # Budget/Safety
    monthly_budget_eur: float = Field(
        default=10.0,
        ge=0.0,
        le=1000.0,
        description="Monthly LLM budget in EUR"
    )
    retry_limit: int = Field(
        default=2,
        ge=0,
        le=5,
        description="Retry limit for failed calls"
    )
    fallback_on_failure: bool = Field(
        default=True,
        description="Use rule-based fallback on LLM failure"
    )

    # Audit/Logging
    log_prompts: bool = Field(
        default=True,
        description="Log all prompts for audit"
    )
    log_responses: bool = Field(
        default=True,
        description="Log all responses for audit"
    )
    hash_inputs: bool = Field(
        default=True,
        description="Hash inputs for reproducibility tracking"
    )


class FullBotConfig(BaseModel):
    """Complete bot configuration combining all config types."""
    bot: BotConfig
    risk: RiskConfig
    llm_policy: LLMPolicyConfig

    @classmethod
    def create_default(
        cls,
        symbol: str,
        market_type: MarketType = MarketType.CRYPTO
    ) -> "FullBotConfig":
        """Create default configuration for a symbol.

        Args:
            symbol: Trading symbol
            market_type: Target market type

        Returns:
            FullBotConfig with market-appropriate defaults
        """
        bot_config = BotConfig(
            symbol=symbol,
            market_type=market_type
        )

        risk_config = (
            RiskConfig.crypto_defaults()
            if market_type == MarketType.CRYPTO
            else RiskConfig.nasdaq_defaults()
        )

        llm_config = LLMPolicyConfig()

        return cls(
            bot=bot_config,
            risk=risk_config,
            llm_policy=llm_config
        )
