"""LLM Validation Prompt Builder.

Refactored from 727 LOC monolith using composition pattern.

Module 2/4 of llm_validation_service.py split.

Contains:
- _build_context_prompt(): Builds optimized prompt from MarketContext
- SETUP_TYPES: List of recognized trading setup types
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .market_context import MarketContext
    from .entry_score_engine import EntryScoreResult
    from .level_engine import LevelsResult


class LLMValidationPrompt:
    """Helper für Prompt Building aus MarketContext."""

    # Setup types recognized
    SETUP_TYPES = [
        "BREAKOUT",
        "BREAKDOWN",
        "PULLBACK_SUPPORT",
        "PULLBACK_RESISTANCE",
        "SWING_FAILURE_PATTERN",
        "TREND_CONTINUATION",
        "MEAN_REVERSION",
        "MOMENTUM",
        "DIVERGENCE",
        "ABSORPTION",
        "RANGE_PLAY",
        "NO_SETUP",
    ]

    def __init__(self, parent):
        """
        Args:
            parent: LLMValidationService Instanz
        """
        self.parent = parent

    def build_context_prompt(
        self,
        context: "MarketContext",
        entry_score: Optional["EntryScoreResult"],
        levels_result: Optional["LevelsResult"],
    ) -> str:
        """Build optimized prompt from MarketContext."""

        # Symbol and timeframe
        header = f"""## Trading Signal Validation Request
Symbol: {context.symbol}
Timeframe: {context.timeframe}
Current Price: {context.current_price:.2f}
Timestamp: {context.timestamp.isoformat()}
"""

        # Regime info
        regime_section = f"""## Market Regime
Regime: {context.regime.value if hasattr(context.regime, 'value') else context.regime}
Trend Direction: {context.trend_direction.value if hasattr(context.trend_direction, 'value') else context.trend_direction}
"""

        # Entry score info
        score_section = ""
        if entry_score:
            score_section = f"""## Entry Score Analysis
Direction: {entry_score.direction.value}
Raw Score: {entry_score.raw_score:.3f}
Final Score: {entry_score.final_score:.3f}
Quality: {entry_score.quality.value}
Gate Status: {entry_score.gate_result.status.value if entry_score.gate_result else 'N/A'}
"""
            # Add component breakdown
            if entry_score.components:
                score_section += "\nScore Components:\n"
                for comp in entry_score.components:
                    score_section += f"  - {comp.name}: {comp.raw_score:.2f} x {comp.weight:.2f} = {comp.weighted_score:.3f}\n"

        # Indicators
        indicators_section = ""
        if self.parent.config.include_indicators and context.indicators:
            ind = context.indicators
            indicators_section = f"""## Technical Indicators
RSI(14): {ind.rsi_14:.1f if ind.rsi_14 else 'N/A'} ({ind.rsi_state or 'N/A'})
MACD: {ind.macd_line:.4f if ind.macd_line else 'N/A'} / Signal: {ind.macd_signal:.4f if ind.macd_signal else 'N/A'} ({ind.macd_crossover or 'N/A'})
EMA20: {ind.ema_20:.2f if ind.ema_20 else 'N/A'} (Distance: {ind.ema_20_distance_pct:.2f}% if ind.ema_20_distance_pct else 'N/A')
EMA50: {ind.ema_50:.2f if ind.ema_50 else 'N/A'}
EMA200: {ind.ema_200:.2f if ind.ema_200 else 'N/A'}
ADX(14): {ind.adx_14:.1f if ind.adx_14 else 'N/A'}
ATR(14): {ind.atr_14:.2f if ind.atr_14 else 'N/A'} ({ind.atr_percent:.2f}% if ind.atr_percent else 'N/A')
BB %B: {ind.bb_pct_b:.2f if ind.bb_pct_b else 'N/A'}
Volume Ratio: {ind.volume_ratio:.2f if ind.volume_ratio else 'N/A'}x
"""

        # Levels
        levels_section = ""
        if self.parent.config.include_levels and levels_result:
            levels_section = "## Support/Resistance Levels\n"
            for level in levels_result.get_top_n(5):
                level_type = level.level_type.value if hasattr(level.level_type, 'value') else str(level.level_type)
                strength = level.strength.value if hasattr(level.strength, 'value') else str(level.strength)
                levels_section += f"  - {level_type.upper()} @ {level.price_low:.2f}-{level.price_high:.2f} ({strength})\n"

        # Candles summary
        candles_section = ""
        if context.candles and len(context.candles) > 0:
            candles_section = f"""## Recent Price Action
Last {len(context.candles)} candles summary available in context.
Latest candle: O={context.candles[-1].open:.2f} H={context.candles[-1].high:.2f} L={context.candles[-1].low:.2f} C={context.candles[-1].close:.2f}
"""

        # Instructions
        instructions = f"""## Your Task
1. Evaluate the signal quality for a {entry_score.direction.value if entry_score else 'potential'} trade
2. Identify the setup type
3. Assess key risk factors
4. Provide a confidence score (0-100)
5. Determine: APPROVE, BOOST, CAUTION, or VETO

## Response Format (JSON only)
{{
    "confidence": <0-100>,
    "action": "<approve|boost|caution|veto>",
    "setup_type": "<one of: {', '.join(self.SETUP_TYPES)}>",
    "reasoning": "<1-2 sentence explanation>",
    "key_factors": ["<factor1>", "<factor2>"],
    "risks": ["<risk1>", "<risk2>"],
    "invalidation_level": <price level that invalidates the setup, or null>
}}

IMPORTANT:
- You are a VALIDATOR, not an executor. Your job is to assess signal quality.
- Be conservative: when in doubt, VETO or CAUTION.
- BOOST only for high-quality setups with strong confluence.
- Response MUST be valid JSON only, no markdown."""

        return header + regime_section + score_section + indicators_section + levels_section + candles_section + instructions
