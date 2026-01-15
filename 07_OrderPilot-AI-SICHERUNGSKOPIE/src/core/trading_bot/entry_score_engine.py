"""
Entry Score Engine - Main Engine and Result Class

Calculates normalized entry scores (0.0 - 1.0) from market data with:
- Multi-component technical analysis
- Weighted scoring system
- Regime-based gates and modifiers
- EntryScoreResult with complete breakdown

This is the main orchestrator that uses EntryScoreCalculators for
component calculations.

Module 4/4 of entry_score_engine.py split (Lines 1-40, 269-489, 1001-1149)
"""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional

import pandas as pd

if TYPE_CHECKING:
    from src.core.trading_bot.regime_detector import RegimeResult

from src.core.trading_bot.entry_score_calculators import EntryScoreCalculators
from src.core.trading_bot.entry_score_config import (
    EntryScoreConfig,
    load_entry_score_config,
    save_entry_score_config,
)
from src.core.trading_bot.entry_score_types import (
    ComponentScore,
    GateResult,
    GateStatus,
    ScoreDirection,
    ScoreQuality,
)

logger = logging.getLogger(__name__)


# =============================================================================
# ENTRY SCORE RESULT
# =============================================================================


@dataclass
class EntryScoreResult:
    """Complete result of entry score calculation."""

    # Final score and direction
    raw_score: float  # Before regime modifiers
    final_score: float  # After regime modifiers (0.0 - 1.0)
    direction: ScoreDirection
    quality: ScoreQuality

    # Component breakdown
    components: List[ComponentScore] = field(default_factory=list)

    # Gate results
    gate_result: Optional[GateResult] = None

    # Metadata
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    symbol: str = ""
    timeframe: str = ""
    current_price: float = 0.0
    regime: str = ""

    @property
    def is_valid_for_entry(self) -> bool:
        """Check if score is valid for entry."""
        if self.gate_result and not self.gate_result.allows_entry:
            return False
        return self.final_score >= 0.50 and self.direction != ScoreDirection.NEUTRAL

    @property
    def long_score(self) -> float:
        """Get score if direction is LONG."""
        if self.direction == ScoreDirection.LONG:
            return self.final_score
        return 0.0

    @property
    def short_score(self) -> float:
        """Get score if direction is SHORT."""
        if self.direction == ScoreDirection.SHORT:
            return self.final_score
        return 0.0

    def get_components_summary(self) -> Dict[str, Dict[str, Any]]:
        """Get summary of all component scores."""
        return {
            c.name: {
                "raw": round(c.raw_score, 3),
                "weight": round(c.weight, 2),
                "weighted": round(c.weighted_score, 3),
                "direction": c.direction.value,
                "details": c.details,
            }
            for c in self.components
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "raw_score": round(self.raw_score, 4),
            "final_score": round(self.final_score, 4),
            "direction": self.direction.value,
            "quality": self.quality.value,
            "is_valid_for_entry": self.is_valid_for_entry,
            "components": self.get_components_summary(),
            "gate": {
                "status": self.gate_result.status.value if self.gate_result else "NONE",
                "reason": self.gate_result.reason if self.gate_result else "",
                "allows_entry": self.gate_result.allows_entry if self.gate_result else True,
            },
            "metadata": {
                "timestamp": self.timestamp.isoformat(),
                "symbol": self.symbol,
                "timeframe": self.timeframe,
                "current_price": self.current_price,
                "regime": self.regime,
            }
        }

    def get_reasoning(self) -> str:
        """Generate human-readable reasoning for the score."""
        lines = [f"Entry Score: {self.final_score:.2%} ({self.quality.value})"]
        lines.append(f"Direction: {self.direction.value}")
        lines.append("")
        lines.append("Components:")

        for c in sorted(self.components, key=lambda x: x.weighted_score, reverse=True):
            lines.append(f"  - {c.name}: {c.raw_score:.2f} × {c.weight:.2f} = {c.weighted_score:.3f}")
            if c.details:
                lines.append(f"    → {c.details}")

        if self.gate_result:
            lines.append("")
            lines.append(f"Gate: {self.gate_result.status.value}")
            lines.append(f"  → {self.gate_result.reason}")

        return "\n".join(lines)


# =============================================================================
# ENTRY SCORE ENGINE
# =============================================================================


class EntryScoreEngine:
    """
    Calculates normalized entry scores (0.0 - 1.0) from market data.

    The engine evaluates multiple technical components, weights them,
    and applies regime-based gates and modifiers.

    Usage:
        engine = EntryScoreEngine()
        result = engine.calculate_score(df, regime_result)

        if result.is_valid_for_entry:
            print(f"Entry signal: {result.direction.value} @ {result.final_score:.2%}")
    """

    def __init__(self, config: Optional[EntryScoreConfig] = None):
        """
        Initialize Entry Score Engine.

        Args:
            config: Optional configuration (uses defaults if None)
        """
        self.config = config or EntryScoreConfig()
        self.config.validate()
        self.calculators = EntryScoreCalculators(self.config)
        logger.info(f"EntryScoreEngine initialized with config validation: {self.config.validate()}")

    def calculate(
        self,
        df: pd.DataFrame,
        regime_result: Optional["RegimeResult"] = None,
        symbol: str = "",
        timeframe: str = "",
    ) -> EntryScoreResult:
        """
        Calculate entry score from OHLCV DataFrame.

        Args:
            df: DataFrame with OHLCV data and indicators
            regime_result: Optional regime detection result
            symbol: Trading symbol
            timeframe: Timeframe

        Returns:
            EntryScoreResult with complete breakdown
        """
        if df.empty or len(df) < 50:
            return self._create_neutral_result("Insufficient data", symbol, timeframe)

        current = df.iloc[-1]
        current_price = float(current.get("close", 0))

        if current_price <= 0:
            return self._create_neutral_result("Invalid price", symbol, timeframe)

        # Calculate component scores for both directions
        long_components = self.calculators.calculate_long_components(df, current)
        short_components = self.calculators.calculate_short_components(df, current)

        # Sum weighted scores
        long_total = sum(c.weighted_score for c in long_components)
        short_total = sum(c.weighted_score for c in short_components)

        # Determine direction
        if long_total > short_total and long_total >= self.config.min_score_for_entry:
            direction = ScoreDirection.LONG
            raw_score = long_total
            components = long_components
        elif short_total > long_total and short_total >= self.config.min_score_for_entry:
            direction = ScoreDirection.SHORT
            raw_score = short_total
            components = short_components
        else:
            direction = ScoreDirection.NEUTRAL
            raw_score = max(long_total, short_total)
            components = long_components if long_total >= short_total else short_components

        # Apply regime gates and modifiers
        regime_str = ""
        gate_result = GateResult.passed()
        final_score = raw_score

        if regime_result:
            regime_str = regime_result.regime.value if hasattr(regime_result.regime, "value") else str(regime_result.regime)
            gate_result = self._evaluate_gates(direction, regime_result)

            if gate_result.allows_entry:
                # Apply regime modifier
                final_score = min(1.0, max(0.0, raw_score + gate_result.modifier))

        # Clamp final score
        final_score = min(1.0, max(0.0, final_score))

        # Determine quality tier
        quality = self._score_to_quality(final_score)

        result = EntryScoreResult(
            raw_score=raw_score,
            final_score=final_score,
            direction=direction,
            quality=quality,
            components=components,
            gate_result=gate_result,
            symbol=symbol,
            timeframe=timeframe,
            current_price=current_price,
            regime=regime_str,
        )

        logger.debug(
            f"Entry score calculated: {result.direction.value} "
            f"raw={result.raw_score:.3f} final={result.final_score:.3f} "
            f"quality={result.quality.value}"
        )

        return result

    # =========================================================================
    # GATES & MODIFIERS
    # =========================================================================

    def _evaluate_gates(
        self, direction: ScoreDirection, regime_result: "RegimeResult"
    ) -> GateResult:
        """
        Evaluate regime-based gates.

        Gates can:
        - Block entry entirely
        - Reduce score (penalty)
        - Boost score (favorable regime)
        """
        regime_str = regime_result.regime.value if hasattr(regime_result.regime, "value") else str(regime_result.regime)
        regime_upper = regime_str.upper()

        # Gate 1: Block in CHOP/RANGE
        if self.config.block_in_chop_range:
            if "CHOP" in regime_upper or "RANGE" in regime_upper:
                return GateResult.blocked(
                    f"Entry blocked: Market in {regime_str} - wait for breakout/trend"
                )

        # Gate 2: Block against strong trend
        if self.config.block_against_strong_trend:
            if direction == ScoreDirection.LONG and "STRONG_TREND_BEAR" in regime_upper:
                if not self.config.allow_counter_trend_sfp:
                    return GateResult.blocked(
                        "Entry blocked: LONG against STRONG_TREND_BEAR"
                    )
            elif direction == ScoreDirection.SHORT and "STRONG_TREND_BULL" in regime_upper:
                if not self.config.allow_counter_trend_sfp:
                    return GateResult.blocked(
                        "Entry blocked: SHORT against STRONG_TREND_BULL"
                    )

        # Modifier: Boost in strong aligned trend
        if direction == ScoreDirection.LONG and "STRONG_TREND_BULL" in regime_upper:
            return GateResult.boosted(
                f"Regime boost: LONG in {regime_str}",
                self.config.regime_boost_strong_trend
            )
        elif direction == ScoreDirection.SHORT and "STRONG_TREND_BEAR" in regime_upper:
            return GateResult.boosted(
                f"Regime boost: SHORT in {regime_str}",
                self.config.regime_boost_strong_trend
            )

        # Modifier: Penalty in volatile regime
        if "VOLATILITY" in regime_upper or "EXPLOSIVE" in regime_upper:
            return GateResult.reduced(
                f"Regime penalty: {regime_str} - increased risk",
                self.config.regime_penalty_volatile
            )

        # Check regime allows_market_entry
        if hasattr(regime_result, "allows_market_entry") and not regime_result.allows_market_entry:
            return GateResult.reduced(
                f"Regime caution: {regime_result.gate_reason}",
                self.config.regime_penalty_chop
            )

        return GateResult.passed()

    # =========================================================================
    # HELPERS
    # =========================================================================

    def _score_to_quality(self, score: float) -> ScoreQuality:
        """Convert score to quality tier."""
        if score >= self.config.threshold_excellent:
            return ScoreQuality.EXCELLENT
        elif score >= self.config.threshold_good:
            return ScoreQuality.GOOD
        elif score >= self.config.threshold_moderate:
            return ScoreQuality.MODERATE
        elif score >= self.config.threshold_weak:
            return ScoreQuality.WEAK
        else:
            return ScoreQuality.NO_SIGNAL

    def _create_neutral_result(
        self, reason: str, symbol: str, timeframe: str
    ) -> EntryScoreResult:
        """Create neutral result when calculation fails."""
        return EntryScoreResult(
            raw_score=0.0,
            final_score=0.0,
            direction=ScoreDirection.NEUTRAL,
            quality=ScoreQuality.NO_SIGNAL,
            components=[],
            gate_result=GateResult.blocked(reason),
            symbol=symbol,
            timeframe=timeframe,
        )


# =============================================================================
# GLOBAL SINGLETON & FACTORY
# =============================================================================

_global_engine: Optional[EntryScoreEngine] = None
_engine_lock = threading.Lock()


def get_entry_score_engine(config: Optional[EntryScoreConfig] = None) -> EntryScoreEngine:
    """
    Get global EntryScoreEngine singleton.

    Args:
        config: Optional config (only used on first call)

    Returns:
        Global EntryScoreEngine instance
    """
    global _global_engine

    with _engine_lock:
        if _global_engine is None:
            _global_engine = EntryScoreEngine(config)
            logger.info("Global EntryScoreEngine created")
        return _global_engine


def calculate_entry_score(
    df: pd.DataFrame,
    regime_result: Optional["RegimeResult"] = None,
    symbol: str = "",
    timeframe: str = "",
) -> EntryScoreResult:
    """
    Convenience function to calculate entry score.

    Uses global engine singleton.
    """
    engine = get_entry_score_engine()
    return engine.calculate(df, regime_result, symbol, timeframe)


# =============================================================================
# CONFIG EXPORT (Re-export from entry_score_config)
# =============================================================================

__all__ = [
    # Main classes
    "EntryScoreEngine",
    "EntryScoreResult",
    "EntryScoreConfig",
    # Types
    "ScoreDirection",
    "ScoreQuality",
    "GateStatus",
    "ComponentScore",
    "GateResult",
    # Functions
    "get_entry_score_engine",
    "calculate_entry_score",
    "load_entry_score_config",
    "save_entry_score_config",
]
