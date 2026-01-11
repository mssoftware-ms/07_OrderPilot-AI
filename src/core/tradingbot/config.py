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
        default=False,  # DISABLED for daytrading - use directional bias instead
        description="Enable fixed daily strategy selection (DISABLED for daytrading)"
    )
    bias_override_threshold: float = Field(
        default=0.8,
        ge=0.5,
        le=1.0,
        description="Signal score threshold (0-1) to override daily bias. "
        "E.g., 0.8 means an 80% signal can trade against daily bias."
    )
    auto_trade: bool = Field(
        default=False,
        description="Enable automatic trade execution"
    )
    show_debug_hud: bool = Field(
        default=False,
        description="Show debug HUD on chart"
    )
    disable_restrictions: bool = Field(
        default=True,
        description="Disable max trades/loss limits (for paper trading)"
    )
    disable_macd_exit: bool = Field(
        default=False,
        description="Disable automatic exit on MACD cross (use stop-loss only)"
    )
    entry_score_threshold: float = Field(
        default=0.6,
        ge=0.0,
        le=1.0,
        description="Minimum normalized score (0-1) required to enter a trade"
    )
    use_pattern_check: bool = Field(
        default=False,
        description="Enable pattern-database validation before signals"
    )
    pattern_similarity_threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Minimum similarity for pattern matches"
    )
    pattern_min_matches: int = Field(
        default=5,
        ge=1,
        le=200,
        description="Minimum number of similar patterns required"
    )
    pattern_min_win_rate: float = Field(
        default=0.55,
        ge=0.0,
        le=1.0,
        description="Minimum historical win-rate of matched patterns"
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
        le=100.0,
        description="Risk per trade as % of account (invested capital per trade)"
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
    trailing_activation_pct: float = Field(
        default=0.0,
        ge=0.0,
        le=20.0,
        description="Minimum profit % before trailing stop activates (0 = activate immediately when in profit)"
    )
    trailing_pct_distance: float = Field(
        default=1.5,
        ge=0.1,
        le=20.0,
        description="Trailing stop distance in % (PCT mode)"
    )
    trailing_atr_multiple: float = Field(
        default=2.5,
        ge=0.5,
        le=10.0,
        description="ATR multiple for trailing (ATR mode)"
    )
    trailing_min_step_pct: float = Field(
        default=0.3,
        ge=0.01,
        le=2.0,
        description="Minimum step for trailing stop updates"
    )
    trailing_cooldown_bars: int = Field(
        default=3,
        ge=1,
        le=20,
        description="Cooldown bars between trailing updates"
    )

    # Regime-Adaptive Trailing Stop Settings
    regime_adaptive_trailing: bool = Field(
        default=True,
        description="Enable regime-based ATR multiplier adjustment"
    )
    trailing_atr_trending: float = Field(
        default=2.0,
        ge=0.5,
        le=5.0,
        description="ATR multiplier for trending markets (tighter)"
    )
    trailing_atr_ranging: float = Field(
        default=3.5,
        ge=1.0,
        le=8.0,
        description="ATR multiplier for ranging/choppy markets (wider)"
    )
    trailing_volatility_bonus: float = Field(
        default=0.5,
        ge=0.0,
        le=2.0,
        description="Extra ATR multiplier added during high volatility"
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
            trailing_min_step_pct=0.3,
            regime_adaptive_trailing=True,
            trailing_atr_trending=2.0,
            trailing_atr_ranging=3.5,
            trailing_volatility_bonus=0.5,
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
            trailing_min_step_pct=0.1,
            regime_adaptive_trailing=True,
            trailing_atr_trending=1.5,
            trailing_atr_ranging=2.5,
            trailing_volatility_bonus=0.3,
            expected_slippage_pct=0.02,
            commission_pct=0.0  # Commission-free on many platforms
        )


class LLMPolicyConfig(BaseModel):
    """LLM/KI call policy configuration.

    WICHTIG: Provider und Model werden aus QSettings geladen!
             Einstellbar über: File -> Settings -> AI
             KEINE hardcodierten Modelle oder Limits hier!
    """
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

    # Model settings - KEINE hardcodierten Modelle!
    # Model wird aus QSettings geladen (File -> Settings -> AI)
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

    # Fallback
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
