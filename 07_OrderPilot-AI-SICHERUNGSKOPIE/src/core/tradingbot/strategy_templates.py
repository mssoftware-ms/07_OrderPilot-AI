"""Strategy Templates Mixin.

Contains pre-built strategy template creation methods for StrategyCatalog.
"""

from __future__ import annotations

from .config import TrailingMode
from .models import RegimeType, StrategyProfile, VolatilityLevel
from .strategy_definitions import (
    EntryRule,
    ExitRule,
    StrategyDefinition,
    StrategyType,
)


class StrategyTemplatesMixin:
    """Mixin providing strategy template creation methods."""

    # ==================== Trend Following Strategies ====================

    def _create_trend_following_conservative(self) -> StrategyDefinition:
        """Conservative trend following strategy."""
        return StrategyDefinition(
            profile=StrategyProfile(
                name="trend_following_conservative",
                description="Conservative trend following using MA crossovers and ADX confirmation",
                regimes=[RegimeType.TREND_UP, RegimeType.TREND_DOWN],
                volatility_levels=[VolatilityLevel.NORMAL, VolatilityLevel.LOW],
                entry_threshold=0.65,
                trailing_mode=TrailingMode.ATR,
                trailing_multiplier=1.5,
            ),
            strategy_type=StrategyType.TREND_FOLLOWING,
            entry_rules=[
                EntryRule(
                    name="ma_alignment",
                    description="Price above/below SMA20 and SMA50 aligned",
                    weight=1.5,
                    indicator="sma_alignment",
                    condition="aligned",
                ),
                EntryRule(
                    name="adx_strength",
                    description="ADX above 25 confirming trend strength",
                    weight=1.2,
                    indicator="adx",
                    condition="above",
                    threshold=25.0,
                ),
                EntryRule(
                    name="macd_confirmation",
                    description="MACD histogram positive/negative for direction",
                    weight=1.0,
                    indicator="macd_hist",
                    condition="direction_match",
                ),
                EntryRule(
                    name="rsi_not_extreme",
                    description="RSI not in extreme zone (30-70)",
                    weight=0.8,
                    indicator="rsi_14",
                    condition="between",
                    threshold=70.0,  # upper bound
                ),
            ],
            exit_rules=[
                ExitRule(
                    name="ma_cross_exit",
                    description="Exit on MA cross against position",
                    priority=2,
                    rule_type="indicator",
                    params={"indicator": "sma_20", "condition": "crosses_against"},
                ),
                ExitRule(
                    name="adx_weakening",
                    description="Exit when ADX drops below 20",
                    priority=3,
                    rule_type="indicator",
                    params={"indicator": "adx", "condition": "below", "threshold": 20},
                ),
                ExitRule(
                    name="trailing_stop",
                    description="ATR-based trailing stop",
                    priority=1,
                    rule_type="trailing",
                    params={"mode": "atr", "multiplier": 2.0},
                ),
            ],
            trailing_mode=TrailingMode.ATR,
            trailing_params={"multiplier": 2.0, "min_distance_pct": 1.0},
            stop_loss_pct=2.5,
            min_entry_score=0.65,
        )

    def _create_trend_following_aggressive(self) -> StrategyDefinition:
        """Aggressive trend following for strong trends."""
        return StrategyDefinition(
            profile=StrategyProfile(
                name="trend_following_aggressive",
                description="Aggressive trend following for strong directional moves",
                regimes=[RegimeType.TREND_UP, RegimeType.TREND_DOWN],
                volatility_levels=[VolatilityLevel.NORMAL, VolatilityLevel.HIGH],
                entry_threshold=0.55,
                trailing_mode=TrailingMode.ATR,
                trailing_multiplier=1.2,
            ),
            strategy_type=StrategyType.TREND_FOLLOWING,
            entry_rules=[
                EntryRule(
                    name="strong_adx",
                    description="ADX above 30 for strong trend",
                    weight=1.8,
                    indicator="adx",
                    condition="above",
                    threshold=30.0,
                ),
                EntryRule(
                    name="di_spread",
                    description="Large DI+ vs DI- spread",
                    weight=1.5,
                    indicator="di_spread",
                    condition="above",
                    threshold=10.0,
                ),
                EntryRule(
                    name="momentum_rsi",
                    description="RSI confirming momentum (>60 long, <40 short)",
                    weight=1.2,
                    indicator="rsi_momentum",
                    condition="direction_match",
                ),
                EntryRule(
                    name="volume_surge",
                    description="Above average volume",
                    weight=1.0,
                    indicator="volume_ratio",
                    condition="above",
                    threshold=1.2,
                ),
            ],
            exit_rules=[
                ExitRule(
                    name="momentum_reversal",
                    description="Exit on RSI divergence",
                    priority=2,
                    rule_type="indicator",
                    params={"indicator": "rsi_divergence", "condition": "detected"},
                ),
                ExitRule(
                    name="trailing_tight",
                    description="Tighter ATR trailing",
                    priority=1,
                    rule_type="trailing",
                    params={"mode": "atr", "multiplier": 1.5},
                ),
            ],
            trailing_mode=TrailingMode.ATR,
            trailing_params={"multiplier": 1.5, "min_distance_pct": 0.8},
            stop_loss_pct=2.0,
            min_entry_score=0.55,
        )

    # ==================== Mean Reversion Strategies ====================

    def _create_mean_reversion_bb(self) -> StrategyDefinition:
        """Mean reversion using Bollinger Bands."""
        return StrategyDefinition(
            profile=StrategyProfile(
                name="mean_reversion_bb",
                description="Mean reversion on Bollinger Band touches in ranging markets",
                regimes=[RegimeType.RANGE],
                volatility_levels=[VolatilityLevel.LOW, VolatilityLevel.NORMAL],
                entry_threshold=0.6,
                trailing_mode=TrailingMode.PCT,
                trailing_multiplier=1.0,
            ),
            strategy_type=StrategyType.MEAN_REVERSION,
            entry_rules=[
                EntryRule(
                    name="bb_touch",
                    description="Price at BB upper/lower band",
                    weight=2.0,
                    indicator="bb_pct",
                    condition="extreme",
                    threshold=0.05,  # within 5% of band
                ),
                EntryRule(
                    name="rsi_oversold_overbought",
                    description="RSI in oversold/overbought zone",
                    weight=1.5,
                    indicator="rsi_14",
                    condition="extreme",
                    threshold=30.0,
                ),
                EntryRule(
                    name="adx_weak",
                    description="ADX below 25 (ranging)",
                    weight=1.2,
                    indicator="adx",
                    condition="below",
                    threshold=25.0,
                ),
                EntryRule(
                    name="stoch_extreme",
                    description="Stochastic in extreme zone",
                    weight=1.0,
                    indicator="stoch_k",
                    condition="extreme",
                    threshold=20.0,
                ),
            ],
            exit_rules=[
                ExitRule(
                    name="bb_middle",
                    description="Exit at BB middle band",
                    priority=2,
                    rule_type="indicator",
                    params={"indicator": "bb_middle", "condition": "reached"},
                ),
                ExitRule(
                    name="rsi_neutral",
                    description="Exit when RSI returns to neutral",
                    priority=3,
                    rule_type="indicator",
                    params={"indicator": "rsi_14", "condition": "between", "low": 40, "high": 60},
                ),
                ExitRule(
                    name="trailing_pct",
                    description="Percentage trailing stop",
                    priority=1,
                    rule_type="trailing",
                    params={"mode": "pct", "distance": 1.5},
                ),
            ],
            trailing_mode=TrailingMode.PCT,
            trailing_params={"distance_pct": 1.5, "activation_profit_pct": 0.5},
            stop_loss_pct=1.5,
            min_entry_score=0.6,
        )

    def _create_mean_reversion_rsi(self) -> StrategyDefinition:
        """Mean reversion using RSI extremes."""
        return StrategyDefinition(
            profile=StrategyProfile(
                name="mean_reversion_rsi",
                description="RSI-based mean reversion in ranging markets",
                regimes=[RegimeType.RANGE],
                volatility_levels=[VolatilityLevel.LOW, VolatilityLevel.NORMAL],
                entry_threshold=0.6,
                trailing_mode=TrailingMode.PCT,
                trailing_multiplier=1.0,
            ),
            strategy_type=StrategyType.MEAN_REVERSION,
            entry_rules=[
                EntryRule(
                    name="rsi_extreme",
                    description="RSI below 25 or above 75",
                    weight=2.0,
                    indicator="rsi_14",
                    condition="extreme",
                    threshold=25.0,
                ),
                EntryRule(
                    name="price_at_support_resistance",
                    description="Price near recent support/resistance",
                    weight=1.5,
                    indicator="price_vs_sma20",
                    condition="extreme",
                    threshold=2.0,
                ),
                EntryRule(
                    name="volume_declining",
                    description="Volume below average (exhaustion)",
                    weight=1.0,
                    indicator="volume_ratio",
                    condition="below",
                    threshold=0.8,
                ),
            ],
            exit_rules=[
                ExitRule(
                    name="rsi_neutral",
                    description="Exit when RSI returns to 50",
                    priority=2,
                    rule_type="indicator",
                    params={"indicator": "rsi_14", "condition": "near", "target": 50},
                ),
                ExitRule(
                    name="trailing",
                    description="Percentage trailing stop",
                    priority=1,
                    rule_type="trailing",
                    params={"mode": "pct", "distance": 1.2},
                ),
            ],
            trailing_mode=TrailingMode.PCT,
            trailing_params={"distance_pct": 1.2},
            stop_loss_pct=1.5,
            min_entry_score=0.6,
        )

    # ==================== Breakout Strategies ====================

    def _create_breakout_volatility(self) -> StrategyDefinition:
        """Breakout strategy for volatility expansion."""
        return StrategyDefinition(
            profile=StrategyProfile(
                name="breakout_volatility",
                description="Breakout on volatility expansion (BB squeeze breakout)",
                regimes=[RegimeType.RANGE, RegimeType.TREND_UP, RegimeType.TREND_DOWN],
                volatility_levels=[VolatilityLevel.LOW, VolatilityLevel.NORMAL],
                entry_threshold=0.7,
                trailing_mode=TrailingMode.ATR,
                trailing_multiplier=1.5,
            ),
            strategy_type=StrategyType.BREAKOUT,
            entry_rules=[
                EntryRule(
                    name="bb_squeeze_release",
                    description="BB width expanding from squeeze",
                    weight=2.0,
                    indicator="bb_width",
                    condition="expanding",
                    threshold=0.03,
                ),
                EntryRule(
                    name="price_breakout",
                    description="Price breaking BB band",
                    weight=1.8,
                    indicator="bb_pct",
                    condition="breakout",
                    threshold=1.0,
                ),
                EntryRule(
                    name="volume_confirmation",
                    description="Above average volume on breakout",
                    weight=1.5,
                    indicator="volume_ratio",
                    condition="above",
                    threshold=1.5,
                ),
                EntryRule(
                    name="momentum_confirmation",
                    description="Momentum supporting breakout direction",
                    weight=1.2,
                    indicator="macd_hist",
                    condition="direction_match",
                ),
            ],
            exit_rules=[
                ExitRule(
                    name="failed_breakout",
                    description="Exit if price returns inside BB",
                    priority=1,
                    rule_type="indicator",
                    params={"indicator": "bb_pct", "condition": "inside", "threshold": 0.9},
                ),
                ExitRule(
                    name="momentum_fade",
                    description="Exit on momentum fade",
                    priority=2,
                    rule_type="indicator",
                    params={"indicator": "macd_hist", "condition": "divergence"},
                ),
                ExitRule(
                    name="trailing_atr",
                    description="ATR trailing stop",
                    priority=3,
                    rule_type="trailing",
                    params={"mode": "atr", "multiplier": 2.0},
                ),
            ],
            trailing_mode=TrailingMode.ATR,
            trailing_params={"multiplier": 2.0},
            stop_loss_pct=2.0,
            min_entry_score=0.7,
        )

    def _create_breakout_momentum(self) -> StrategyDefinition:
        """Momentum breakout strategy."""
        return StrategyDefinition(
            profile=StrategyProfile(
                name="breakout_momentum",
                description="Momentum-driven breakout with volume confirmation",
                regimes=[RegimeType.TREND_UP, RegimeType.TREND_DOWN],
                volatility_levels=[VolatilityLevel.NORMAL, VolatilityLevel.HIGH],
                entry_threshold=0.65,
                trailing_mode=TrailingMode.ATR,
                trailing_multiplier=1.3,
            ),
            strategy_type=StrategyType.BREAKOUT,
            entry_rules=[
                EntryRule(
                    name="new_high_low",
                    description="Price at N-period high/low",
                    weight=1.8,
                    indicator="price_position",
                    condition="extreme",
                    threshold=20,  # 20-period high/low
                ),
                EntryRule(
                    name="macd_strong",
                    description="Strong MACD histogram",
                    weight=1.5,
                    indicator="macd_hist",
                    condition="strong",
                ),
                EntryRule(
                    name="volume_surge",
                    description="Volume spike on breakout",
                    weight=1.5,
                    indicator="volume_ratio",
                    condition="above",
                    threshold=2.0,
                ),
            ],
            exit_rules=[
                ExitRule(
                    name="momentum_loss",
                    description="Exit on MACD cross",
                    priority=2,
                    rule_type="indicator",
                    params={"indicator": "macd", "condition": "cross_against"},
                ),
                ExitRule(
                    name="trailing",
                    description="ATR trailing",
                    priority=1,
                    rule_type="trailing",
                    params={"mode": "atr", "multiplier": 1.5},
                ),
            ],
            trailing_mode=TrailingMode.ATR,
            trailing_params={"multiplier": 1.5},
            stop_loss_pct=2.5,
            min_entry_score=0.65,
        )

    # ==================== Momentum Strategy ====================

    def _create_momentum_macd(self) -> StrategyDefinition:
        """MACD-based momentum strategy."""
        return StrategyDefinition(
            profile=StrategyProfile(
                name="momentum_macd",
                description="MACD crossover momentum strategy",
                regimes=[RegimeType.TREND_UP, RegimeType.TREND_DOWN],
                volatility_levels=[VolatilityLevel.NORMAL],
                entry_threshold=0.6,
                trailing_mode=TrailingMode.ATR,
                trailing_multiplier=1.5,
            ),
            strategy_type=StrategyType.MOMENTUM,
            entry_rules=[
                EntryRule(
                    name="macd_cross",
                    description="MACD line crosses signal line",
                    weight=2.0,
                    indicator="macd",
                    condition="crosses",
                ),
                EntryRule(
                    name="macd_hist_direction",
                    description="Histogram growing in direction",
                    weight=1.5,
                    indicator="macd_hist",
                    condition="growing",
                ),
                EntryRule(
                    name="adx_trending",
                    description="ADX above 20",
                    weight=1.2,
                    indicator="adx",
                    condition="above",
                    threshold=20.0,
                ),
            ],
            exit_rules=[
                ExitRule(
                    name="macd_cross_against",
                    description="Exit on MACD cross against",
                    priority=2,
                    rule_type="indicator",
                    params={"indicator": "macd", "condition": "crosses_against"},
                ),
                ExitRule(
                    name="histogram_shrinking",
                    description="Exit on histogram shrinking",
                    priority=3,
                    rule_type="indicator",
                    params={"indicator": "macd_hist", "condition": "shrinking", "bars": 3},
                ),
                ExitRule(
                    name="trailing",
                    description="ATR trailing",
                    priority=1,
                    rule_type="trailing",
                    params={"mode": "atr", "multiplier": 1.8},
                ),
            ],
            trailing_mode=TrailingMode.ATR,
            trailing_params={"multiplier": 1.8},
            stop_loss_pct=2.0,
            min_entry_score=0.6,
        )

    # ==================== Scalping Strategy ====================

    def _create_scalping_range(self) -> StrategyDefinition:
        """Scalping strategy for tight ranges."""
        return StrategyDefinition(
            profile=StrategyProfile(
                name="scalping_range",
                description="Quick scalping in tight ranges with tight stops",
                regimes=[RegimeType.RANGE],
                volatility_levels=[VolatilityLevel.LOW],
                entry_threshold=0.55,
                trailing_mode=TrailingMode.PCT,
                trailing_multiplier=0.8,
            ),
            strategy_type=StrategyType.SCALPING,
            entry_rules=[
                EntryRule(
                    name="stoch_extreme",
                    description="Stochastic at extreme",
                    weight=1.8,
                    indicator="stoch_k",
                    condition="extreme",
                    threshold=15.0,
                ),
                EntryRule(
                    name="bb_touch",
                    description="Price touching BB band",
                    weight=1.5,
                    indicator="bb_pct",
                    condition="extreme",
                    threshold=0.02,
                ),
                EntryRule(
                    name="low_volatility",
                    description="ATR below average",
                    weight=1.2,
                    indicator="atr_ratio",
                    condition="below",
                    threshold=0.8,
                ),
            ],
            exit_rules=[
                ExitRule(
                    name="quick_profit",
                    description="Exit at small profit target",
                    priority=1,
                    rule_type="profit",
                    params={"target_pct": 0.5},
                ),
                ExitRule(
                    name="stoch_neutral",
                    description="Exit when stoch returns to 50",
                    priority=2,
                    rule_type="indicator",
                    params={"indicator": "stoch_k", "condition": "near", "target": 50},
                ),
                ExitRule(
                    name="tight_stop",
                    description="Tight percentage stop",
                    priority=1,
                    rule_type="trailing",
                    params={"mode": "pct", "distance": 0.5},
                ),
            ],
            trailing_mode=TrailingMode.PCT,
            trailing_params={"distance_pct": 0.5},
            stop_loss_pct=0.8,
            min_entry_score=0.55,
        )

    # ==================== Sideways/Range Market Strategy ====================

    def _create_sideways_range_bounce(self) -> StrategyDefinition:
        """Sideways market strategy for ranging markets with max 0.6% range.

        Uses a comprehensive indicator set optimized for sideways markets:
        - SMA 20/50 for short-term/medium-term trend identification
        - RSI 14 for overbought/oversold conditions
        - Bollinger Bands 20-period with 2 StdDev for volatility
        - Stochastic Oscillator 14 for reversal points
        - Volume indicators for market participant interest
        - MACD 12/26/9 for buy/sell signals

        Designed for markets in consolidation with low ADX (<20).
        """
        return StrategyDefinition(
            profile=StrategyProfile(
                name="sideways_range_bounce",
                description=(
                    "Range-bound trading strategy for sideways markets with max 0.6% range. "
                    "Combines SMA 20/50, RSI 14, Bollinger Bands, Stochastic, Volume, and MACD "
                    "for comprehensive analysis in consolidating markets."
                ),
                regimes=[RegimeType.RANGE],
                volatility_levels=[VolatilityLevel.LOW, VolatilityLevel.NORMAL],
                entry_threshold=0.55,
                trailing_mode=TrailingMode.PCT,
                trailing_multiplier=0.8,
            ),
            strategy_type=StrategyType.MEAN_REVERSION,
            entry_rules=[
                # Primary: Bollinger Bands touch for entry signal
                EntryRule(
                    name="bb_band_touch",
                    description="Price touching upper/lower Bollinger Band (20, 2 StdDev)",
                    weight=1.8,
                    indicator="bb_pct",
                    condition="extreme",
                    threshold=0.05,  # within 5% of band
                ),
                # RSI confirmation for oversold/overbought
                EntryRule(
                    name="rsi_extreme",
                    description="RSI 14 below 30 (oversold) or above 70 (overbought)",
                    weight=1.5,
                    indicator="rsi_14",
                    condition="extreme",
                    threshold=30.0,
                ),
                # Stochastic Oscillator for reversal timing
                EntryRule(
                    name="stoch_reversal",
                    description="Stochastic 14 in extreme zone indicating reversal",
                    weight=1.3,
                    indicator="stoch_k",
                    condition="extreme",
                    threshold=20.0,
                ),
                # SMA proximity - price near SMA 20/50
                EntryRule(
                    name="sma_alignment",
                    description="Price between SMA 20 and SMA 50 in ranging market",
                    weight=1.0,
                    indicator="sma_distance",
                    condition="near",
                    threshold=0.5,  # within 0.5% of MA
                ),
                # ADX low confirming sideways market
                EntryRule(
                    name="adx_sideways",
                    description="ADX below 20 confirming ranging/sideways market",
                    weight=1.2,
                    indicator="adx",
                    condition="below",
                    threshold=20.0,
                ),
                # Volume analysis
                EntryRule(
                    name="volume_interest",
                    description="Volume profile showing market interest at level",
                    weight=0.8,
                    indicator="volume_ratio",
                    condition="above",
                    threshold=0.7,  # at least 70% of average
                ),
                # MACD histogram direction
                EntryRule(
                    name="macd_direction",
                    description="MACD 12/26/9 histogram confirming direction",
                    weight=1.0,
                    indicator="macd_hist",
                    condition="direction_match",
                ),
            ],
            exit_rules=[
                # Exit at middle Bollinger Band (SMA 20)
                ExitRule(
                    name="bb_middle_exit",
                    description="Exit when price reaches BB middle band (SMA 20)",
                    priority=2,
                    rule_type="indicator",
                    params={"indicator": "bb_middle", "condition": "reached"},
                ),
                # Exit when RSI returns to neutral
                ExitRule(
                    name="rsi_neutral",
                    description="Exit when RSI returns to 40-60 neutral zone",
                    priority=3,
                    rule_type="indicator",
                    params={"indicator": "rsi_14", "condition": "between", "low": 40, "high": 60},
                ),
                # Exit on stochastic neutral
                ExitRule(
                    name="stoch_neutral",
                    description="Exit when Stochastic returns to 40-60 zone",
                    priority=4,
                    rule_type="indicator",
                    params={"indicator": "stoch_k", "condition": "between", "low": 40, "high": 60},
                ),
                # MACD cross against position
                ExitRule(
                    name="macd_cross_exit",
                    description="Exit on MACD signal line cross against position",
                    priority=2,
                    rule_type="indicator",
                    params={"indicator": "macd", "condition": "crosses_against"},
                ),
                # Percentage trailing stop
                ExitRule(
                    name="trailing_pct",
                    description="Percentage-based trailing stop for range trading",
                    priority=1,
                    rule_type="trailing",
                    params={"mode": "pct", "distance": 0.4},  # tight for ranging market
                ),
            ],
            trailing_mode=TrailingMode.PCT,
            trailing_params={"distance_pct": 0.4, "activation_profit_pct": 0.2},
            stop_loss_pct=0.6,  # max 0.6% as specified for sideways range
            min_entry_score=0.55,
        )
