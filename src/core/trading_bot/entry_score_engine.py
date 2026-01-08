"""
Entry Score Engine - Normalisierter Entry-Score (0.0-1.0)

Phase 3.1: Stabilisierung des Alpaca Entry-Scores als Baseline.

Berechnet einen gewichteten Score aus mehreren Komponenten:
- Trend Alignment (EMA-Stack)
- Momentum (RSI, MACD)
- Trend Strength (ADX)
- Volatility Filter (ATR/BB)
- Volume Confirmation

Der Score ist normalisiert auf 0.0-1.0 und konfigurierbar.
Regime-Gates können den Score blockieren oder modifizieren.
"""

from __future__ import annotations

import json
import logging
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, TYPE_CHECKING

import pandas as pd

if TYPE_CHECKING:
    from .regime_detector import RegimeResult

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS & TYPES
# =============================================================================


class ScoreDirection(str, Enum):
    """Signal direction for entry."""
    LONG = "LONG"
    SHORT = "SHORT"
    NEUTRAL = "NEUTRAL"


class ScoreQuality(str, Enum):
    """Quality tier based on final score."""
    EXCELLENT = "EXCELLENT"  # >= 0.8
    GOOD = "GOOD"            # >= 0.65
    MODERATE = "MODERATE"    # >= 0.5
    WEAK = "WEAK"            # >= 0.35
    NO_SIGNAL = "NO_SIGNAL"  # < 0.35


class GateStatus(str, Enum):
    """Status of regime gates."""
    PASS = "PASS"          # Gate passed, entry allowed
    BLOCKED = "BLOCKED"    # Gate blocked entry
    REDUCED = "REDUCED"    # Score reduced due to regime
    BOOSTED = "BOOSTED"    # Score boosted due to regime


# =============================================================================
# CONFIG
# =============================================================================


@dataclass
class EntryScoreConfig:
    """Configuration for Entry Score calculation."""

    # Component Weights (must sum to 1.0)
    weight_trend_alignment: float = 0.25    # EMA Stack
    weight_momentum_rsi: float = 0.15       # RSI positioning
    weight_momentum_macd: float = 0.15      # MACD crossover/histogram
    weight_trend_strength: float = 0.20     # ADX
    weight_volatility: float = 0.10         # BB/ATR
    weight_volume: float = 0.15             # Volume confirmation

    # Thresholds for quality tiers
    threshold_excellent: float = 0.80
    threshold_good: float = 0.65
    threshold_moderate: float = 0.50
    threshold_weak: float = 0.35

    # Minimum score for valid signal
    min_score_for_entry: float = 0.50

    # Indicator Parameters
    ema_short: int = 20
    ema_medium: int = 50
    ema_long: int = 200
    rsi_period: int = 14
    rsi_overbought: int = 70
    rsi_oversold: int = 30
    adx_strong_trend: float = 25.0
    adx_weak_trend: float = 15.0
    atr_period: int = 14

    # Regime-based modifiers
    regime_boost_strong_trend: float = 0.10    # Boost in strong trend
    regime_penalty_chop: float = -0.15         # Penalty in chop/range
    regime_penalty_volatile: float = -0.10     # Penalty in explosive volatility

    # Gate settings
    block_in_chop_range: bool = True
    block_against_strong_trend: bool = True
    allow_counter_trend_sfp: bool = True  # Allow SFP (Swing Failure Pattern) setups

    def validate(self) -> bool:
        """Validate config - weights must sum to ~1.0."""
        total = (
            self.weight_trend_alignment +
            self.weight_momentum_rsi +
            self.weight_momentum_macd +
            self.weight_trend_strength +
            self.weight_volatility +
            self.weight_volume
        )
        if not (0.99 <= total <= 1.01):
            logger.warning(f"Entry score weights sum to {total:.2f}, should be 1.0")
            return False
        return True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "weights": {
                "trend_alignment": self.weight_trend_alignment,
                "momentum_rsi": self.weight_momentum_rsi,
                "momentum_macd": self.weight_momentum_macd,
                "trend_strength": self.weight_trend_strength,
                "volatility": self.weight_volatility,
                "volume": self.weight_volume,
            },
            "thresholds": {
                "excellent": self.threshold_excellent,
                "good": self.threshold_good,
                "moderate": self.threshold_moderate,
                "weak": self.threshold_weak,
                "min_for_entry": self.min_score_for_entry,
            },
            "indicators": {
                "ema_short": self.ema_short,
                "ema_medium": self.ema_medium,
                "ema_long": self.ema_long,
                "rsi_period": self.rsi_period,
                "rsi_overbought": self.rsi_overbought,
                "rsi_oversold": self.rsi_oversold,
                "adx_strong_trend": self.adx_strong_trend,
                "adx_weak_trend": self.adx_weak_trend,
            },
            "regime_modifiers": {
                "boost_strong_trend": self.regime_boost_strong_trend,
                "penalty_chop": self.regime_penalty_chop,
                "penalty_volatile": self.regime_penalty_volatile,
            },
            "gates": {
                "block_in_chop_range": self.block_in_chop_range,
                "block_against_strong_trend": self.block_against_strong_trend,
                "allow_counter_trend_sfp": self.allow_counter_trend_sfp,
            }
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EntryScoreConfig":
        """Create from dictionary."""
        config = cls()

        if "weights" in data:
            w = data["weights"]
            config.weight_trend_alignment = w.get("trend_alignment", config.weight_trend_alignment)
            config.weight_momentum_rsi = w.get("momentum_rsi", config.weight_momentum_rsi)
            config.weight_momentum_macd = w.get("momentum_macd", config.weight_momentum_macd)
            config.weight_trend_strength = w.get("trend_strength", config.weight_trend_strength)
            config.weight_volatility = w.get("volatility", config.weight_volatility)
            config.weight_volume = w.get("volume", config.weight_volume)

        if "thresholds" in data:
            t = data["thresholds"]
            config.threshold_excellent = t.get("excellent", config.threshold_excellent)
            config.threshold_good = t.get("good", config.threshold_good)
            config.threshold_moderate = t.get("moderate", config.threshold_moderate)
            config.threshold_weak = t.get("weak", config.threshold_weak)
            config.min_score_for_entry = t.get("min_for_entry", config.min_score_for_entry)

        if "indicators" in data:
            i = data["indicators"]
            config.ema_short = i.get("ema_short", config.ema_short)
            config.ema_medium = i.get("ema_medium", config.ema_medium)
            config.ema_long = i.get("ema_long", config.ema_long)
            config.rsi_period = i.get("rsi_period", config.rsi_period)
            config.rsi_overbought = i.get("rsi_overbought", config.rsi_overbought)
            config.rsi_oversold = i.get("rsi_oversold", config.rsi_oversold)
            config.adx_strong_trend = i.get("adx_strong_trend", config.adx_strong_trend)
            config.adx_weak_trend = i.get("adx_weak_trend", config.adx_weak_trend)

        if "regime_modifiers" in data:
            r = data["regime_modifiers"]
            config.regime_boost_strong_trend = r.get("boost_strong_trend", config.regime_boost_strong_trend)
            config.regime_penalty_chop = r.get("penalty_chop", config.regime_penalty_chop)
            config.regime_penalty_volatile = r.get("penalty_volatile", config.regime_penalty_volatile)

        if "gates" in data:
            g = data["gates"]
            config.block_in_chop_range = g.get("block_in_chop_range", config.block_in_chop_range)
            config.block_against_strong_trend = g.get("block_against_strong_trend", config.block_against_strong_trend)
            config.allow_counter_trend_sfp = g.get("allow_counter_trend_sfp", config.allow_counter_trend_sfp)

        return config


# =============================================================================
# COMPONENT SCORES
# =============================================================================


@dataclass
class ComponentScore:
    """Score from a single component."""

    name: str
    raw_score: float  # 0.0 - 1.0
    weight: float
    weighted_score: float  # raw_score * weight
    direction: ScoreDirection  # Direction this component suggests
    details: str = ""
    values: Dict[str, Any] = field(default_factory=dict)

    @property
    def contribution_pct(self) -> float:
        """Contribution percentage to final score."""
        return self.weighted_score * 100


@dataclass
class GateResult:
    """Result of gate evaluation."""

    status: GateStatus
    reason: str
    modifier: float = 0.0  # Score modifier (-1.0 = block, 0.0 = pass, +0.1 = boost 10%)
    allows_entry: bool = True

    @classmethod
    def passed(cls) -> "GateResult":
        return cls(status=GateStatus.PASS, reason="All gates passed", allows_entry=True)

    @classmethod
    def blocked(cls, reason: str) -> "GateResult":
        return cls(status=GateStatus.BLOCKED, reason=reason, modifier=-1.0, allows_entry=False)

    @classmethod
    def reduced(cls, reason: str, penalty: float) -> "GateResult":
        return cls(status=GateStatus.REDUCED, reason=reason, modifier=penalty, allows_entry=True)

    @classmethod
    def boosted(cls, reason: str, boost: float) -> "GateResult":
        return cls(status=GateStatus.BOOSTED, reason=reason, modifier=boost, allows_entry=True)


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
        logger.info(f"EntryScoreEngine initialized with config validation: {self.config.validate()}")

    def calculate_score(
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
        long_components = self._calculate_long_components(df, current)
        short_components = self._calculate_short_components(df, current)

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
    # COMPONENT CALCULATIONS - LONG
    # =========================================================================

    def _calculate_long_components(
        self, df: pd.DataFrame, current: pd.Series
    ) -> List[ComponentScore]:
        """Calculate all component scores for LONG direction."""
        components = []

        # 1. Trend Alignment (EMA Stack)
        components.append(self._calc_trend_alignment_long(current))

        # 2. RSI Momentum
        components.append(self._calc_rsi_momentum_long(current))

        # 3. MACD Momentum
        components.append(self._calc_macd_momentum_long(current))

        # 4. Trend Strength (ADX)
        components.append(self._calc_trend_strength(current, ScoreDirection.LONG))

        # 5. Volatility
        components.append(self._calc_volatility(current))

        # 6. Volume
        components.append(self._calc_volume(current))

        return components

    def _calc_trend_alignment_long(self, current: pd.Series) -> ComponentScore:
        """Calculate EMA stack alignment for LONG."""
        weight = self.config.weight_trend_alignment

        price = float(current.get("close", 0))
        ema20 = self._get_indicator(current, "ema_20", "EMA_20")
        ema50 = self._get_indicator(current, "ema_50", "EMA_50")
        ema200 = self._get_indicator(current, "ema_200", "EMA_200")

        if not all([price, ema20, ema50]):
            return ComponentScore(
                name="trend_alignment",
                raw_score=0.0,
                weight=weight,
                weighted_score=0.0,
                direction=ScoreDirection.NEUTRAL,
                details="EMA data not available",
            )

        score = 0.0
        details_parts = []

        # Price above EMA20: +0.3
        if price > ema20:
            score += 0.3
            details_parts.append("P>EMA20")

        # EMA20 > EMA50: +0.3
        if ema20 > ema50:
            score += 0.3
            details_parts.append("EMA20>50")

        # EMA50 > EMA200 (if available): +0.2
        if ema200:
            if ema50 > ema200:
                score += 0.2
                details_parts.append("EMA50>200")
        else:
            # No EMA200, redistribute weight
            if ema20 > ema50:
                score += 0.1

        # Bonus for perfect stack: +0.2
        if price > ema20 > ema50 and (not ema200 or ema50 > ema200):
            score += 0.2
            details_parts.append("PERFECT_STACK")

        score = min(1.0, score)

        return ComponentScore(
            name="trend_alignment",
            raw_score=score,
            weight=weight,
            weighted_score=score * weight,
            direction=ScoreDirection.LONG if score >= 0.5 else ScoreDirection.NEUTRAL,
            details=" | ".join(details_parts) or "Weak alignment",
            values={"price": price, "ema20": ema20, "ema50": ema50, "ema200": ema200}
        )

    def _calc_rsi_momentum_long(self, current: pd.Series) -> ComponentScore:
        """Calculate RSI score for LONG."""
        weight = self.config.weight_momentum_rsi

        rsi = self._get_indicator(current, "rsi_14", "RSI_14", "rsi")

        if rsi is None:
            return ComponentScore(
                name="momentum_rsi",
                raw_score=0.0,
                weight=weight,
                weighted_score=0.0,
                direction=ScoreDirection.NEUTRAL,
                details="RSI not available",
            )

        # Optimal LONG RSI: 40-65 (not overbought, bullish momentum)
        if 40 <= rsi <= 65:
            score = 1.0
            details = f"RSI {rsi:.1f} - optimal bullish zone"
        elif 30 <= rsi < 40:
            score = 0.7  # Approaching oversold, could bounce
            details = f"RSI {rsi:.1f} - near oversold, potential bounce"
        elif 65 < rsi <= 70:
            score = 0.5  # Getting hot but still tradeable
            details = f"RSI {rsi:.1f} - elevated, caution"
        elif rsi < 30:
            score = 0.4  # Oversold, reversal possible but risky
            details = f"RSI {rsi:.1f} - oversold, reversal play"
        else:  # rsi > 70
            score = 0.2  # Overbought, poor entry
            details = f"RSI {rsi:.1f} - overbought"

        return ComponentScore(
            name="momentum_rsi",
            raw_score=score,
            weight=weight,
            weighted_score=score * weight,
            direction=ScoreDirection.LONG if score >= 0.5 else ScoreDirection.NEUTRAL,
            details=details,
            values={"rsi": rsi}
        )

    def _calc_macd_momentum_long(self, current: pd.Series) -> ComponentScore:
        """Calculate MACD score for LONG."""
        weight = self.config.weight_momentum_macd

        macd = self._get_indicator(current, "macd", "MACD")
        macd_signal = self._get_indicator(current, "macd_signal", "MACD_signal")
        macd_hist = self._get_indicator(current, "macd_hist", "MACD_hist")

        if macd is None or macd_signal is None:
            return ComponentScore(
                name="momentum_macd",
                raw_score=0.0,
                weight=weight,
                weighted_score=0.0,
                direction=ScoreDirection.NEUTRAL,
                details="MACD not available",
            )

        score = 0.0
        details_parts = []

        # MACD above signal: +0.4
        if macd > macd_signal:
            score += 0.4
            details_parts.append("MACD>Signal")

        # MACD above zero: +0.3
        if macd > 0:
            score += 0.3
            details_parts.append("MACD>0")

        # Positive histogram and growing: +0.3
        if macd_hist is not None and macd_hist > 0:
            score += 0.3
            details_parts.append(f"Hist={macd_hist:.4f}")

        score = min(1.0, score)

        return ComponentScore(
            name="momentum_macd",
            raw_score=score,
            weight=weight,
            weighted_score=score * weight,
            direction=ScoreDirection.LONG if score >= 0.5 else ScoreDirection.NEUTRAL,
            details=" | ".join(details_parts) or "Bearish MACD",
            values={"macd": macd, "signal": macd_signal, "hist": macd_hist}
        )

    # =========================================================================
    # COMPONENT CALCULATIONS - SHORT
    # =========================================================================

    def _calculate_short_components(
        self, df: pd.DataFrame, current: pd.Series
    ) -> List[ComponentScore]:
        """Calculate all component scores for SHORT direction."""
        components = []

        # 1. Trend Alignment (EMA Stack - inverse)
        components.append(self._calc_trend_alignment_short(current))

        # 2. RSI Momentum (inverse)
        components.append(self._calc_rsi_momentum_short(current))

        # 3. MACD Momentum (inverse)
        components.append(self._calc_macd_momentum_short(current))

        # 4. Trend Strength (ADX)
        components.append(self._calc_trend_strength(current, ScoreDirection.SHORT))

        # 5. Volatility (same as long)
        components.append(self._calc_volatility(current))

        # 6. Volume (same as long)
        components.append(self._calc_volume(current))

        return components

    def _calc_trend_alignment_short(self, current: pd.Series) -> ComponentScore:
        """Calculate EMA stack alignment for SHORT."""
        weight = self.config.weight_trend_alignment

        price = float(current.get("close", 0))
        ema20 = self._get_indicator(current, "ema_20", "EMA_20")
        ema50 = self._get_indicator(current, "ema_50", "EMA_50")
        ema200 = self._get_indicator(current, "ema_200", "EMA_200")

        if not all([price, ema20, ema50]):
            return ComponentScore(
                name="trend_alignment",
                raw_score=0.0,
                weight=weight,
                weighted_score=0.0,
                direction=ScoreDirection.NEUTRAL,
                details="EMA data not available",
            )

        score = 0.0
        details_parts = []

        # Price below EMA20: +0.3
        if price < ema20:
            score += 0.3
            details_parts.append("P<EMA20")

        # EMA20 < EMA50: +0.3
        if ema20 < ema50:
            score += 0.3
            details_parts.append("EMA20<50")

        # EMA50 < EMA200 (if available): +0.2
        if ema200:
            if ema50 < ema200:
                score += 0.2
                details_parts.append("EMA50<200")
        else:
            if ema20 < ema50:
                score += 0.1

        # Bonus for perfect bearish stack: +0.2
        if price < ema20 < ema50 and (not ema200 or ema50 < ema200):
            score += 0.2
            details_parts.append("PERFECT_BEARISH_STACK")

        score = min(1.0, score)

        return ComponentScore(
            name="trend_alignment",
            raw_score=score,
            weight=weight,
            weighted_score=score * weight,
            direction=ScoreDirection.SHORT if score >= 0.5 else ScoreDirection.NEUTRAL,
            details=" | ".join(details_parts) or "Weak bearish alignment",
            values={"price": price, "ema20": ema20, "ema50": ema50, "ema200": ema200}
        )

    def _calc_rsi_momentum_short(self, current: pd.Series) -> ComponentScore:
        """Calculate RSI score for SHORT."""
        weight = self.config.weight_momentum_rsi

        rsi = self._get_indicator(current, "rsi_14", "RSI_14", "rsi")

        if rsi is None:
            return ComponentScore(
                name="momentum_rsi",
                raw_score=0.0,
                weight=weight,
                weighted_score=0.0,
                direction=ScoreDirection.NEUTRAL,
                details="RSI not available",
            )

        # Optimal SHORT RSI: 35-60 (not oversold, bearish momentum)
        if 35 <= rsi <= 60:
            score = 1.0
            details = f"RSI {rsi:.1f} - optimal bearish zone"
        elif 60 < rsi <= 70:
            score = 0.7  # Approaching overbought, could reverse
            details = f"RSI {rsi:.1f} - near overbought, potential drop"
        elif 30 <= rsi < 35:
            score = 0.5  # Getting cold but still tradeable
            details = f"RSI {rsi:.1f} - lowered, caution"
        elif rsi > 70:
            score = 0.4  # Overbought, reversal possible
            details = f"RSI {rsi:.1f} - overbought, reversal play"
        else:  # rsi < 30
            score = 0.2  # Oversold, poor short entry
            details = f"RSI {rsi:.1f} - oversold"

        return ComponentScore(
            name="momentum_rsi",
            raw_score=score,
            weight=weight,
            weighted_score=score * weight,
            direction=ScoreDirection.SHORT if score >= 0.5 else ScoreDirection.NEUTRAL,
            details=details,
            values={"rsi": rsi}
        )

    def _calc_macd_momentum_short(self, current: pd.Series) -> ComponentScore:
        """Calculate MACD score for SHORT."""
        weight = self.config.weight_momentum_macd

        macd = self._get_indicator(current, "macd", "MACD")
        macd_signal = self._get_indicator(current, "macd_signal", "MACD_signal")
        macd_hist = self._get_indicator(current, "macd_hist", "MACD_hist")

        if macd is None or macd_signal is None:
            return ComponentScore(
                name="momentum_macd",
                raw_score=0.0,
                weight=weight,
                weighted_score=0.0,
                direction=ScoreDirection.NEUTRAL,
                details="MACD not available",
            )

        score = 0.0
        details_parts = []

        # MACD below signal: +0.4
        if macd < macd_signal:
            score += 0.4
            details_parts.append("MACD<Signal")

        # MACD below zero: +0.3
        if macd < 0:
            score += 0.3
            details_parts.append("MACD<0")

        # Negative histogram: +0.3
        if macd_hist is not None and macd_hist < 0:
            score += 0.3
            details_parts.append(f"Hist={macd_hist:.4f}")

        score = min(1.0, score)

        return ComponentScore(
            name="momentum_macd",
            raw_score=score,
            weight=weight,
            weighted_score=score * weight,
            direction=ScoreDirection.SHORT if score >= 0.5 else ScoreDirection.NEUTRAL,
            details=" | ".join(details_parts) or "Bullish MACD",
            values={"macd": macd, "signal": macd_signal, "hist": macd_hist}
        )

    # =========================================================================
    # SHARED COMPONENT CALCULATIONS
    # =========================================================================

    def _calc_trend_strength(
        self, current: pd.Series, direction: ScoreDirection
    ) -> ComponentScore:
        """Calculate ADX-based trend strength score."""
        weight = self.config.weight_trend_strength

        adx = self._get_indicator(current, "adx_14", "ADX_14", "adx")
        plus_di = self._get_indicator(current, "plus_di", "+DI", "DI_plus")
        minus_di = self._get_indicator(current, "minus_di", "-DI", "DI_minus")

        if adx is None:
            return ComponentScore(
                name="trend_strength",
                raw_score=0.0,
                weight=weight,
                weighted_score=0.0,
                direction=ScoreDirection.NEUTRAL,
                details="ADX not available",
            )

        score = 0.0
        details_parts = []

        # ADX strength scoring
        if adx >= self.config.adx_strong_trend:
            score += 0.6
            details_parts.append(f"ADX={adx:.1f} STRONG")
        elif adx >= self.config.adx_weak_trend:
            score += 0.4
            details_parts.append(f"ADX={adx:.1f} moderate")
        else:
            score += 0.1
            details_parts.append(f"ADX={adx:.1f} weak")

        # DI alignment bonus
        if plus_di is not None and minus_di is not None:
            if direction == ScoreDirection.LONG and plus_di > minus_di:
                score += 0.4
                details_parts.append(f"+DI>{minus_di:.1f}")
            elif direction == ScoreDirection.SHORT and minus_di > plus_di:
                score += 0.4
                details_parts.append(f"-DI>{plus_di:.1f}")

        score = min(1.0, score)

        return ComponentScore(
            name="trend_strength",
            raw_score=score,
            weight=weight,
            weighted_score=score * weight,
            direction=direction if score >= 0.5 else ScoreDirection.NEUTRAL,
            details=" | ".join(details_parts),
            values={"adx": adx, "plus_di": plus_di, "minus_di": minus_di}
        )

    def _calc_volatility(self, current: pd.Series) -> ComponentScore:
        """Calculate volatility component score."""
        weight = self.config.weight_volatility

        atr = self._get_indicator(current, "atr_14", "ATR_14", "atr")
        bb_upper = self._get_indicator(current, "bb_upper", "BB_upper")
        bb_lower = self._get_indicator(current, "bb_lower", "BB_lower")
        bb_middle = self._get_indicator(current, "bb_middle", "BB_middle")
        price = float(current.get("close", 0))

        score = 0.5  # Default neutral
        details_parts = []

        # ATR as % of price - prefer moderate volatility
        if atr and price > 0:
            atr_pct = (atr / price) * 100
            if 1.0 <= atr_pct <= 3.0:
                score = 0.9
                details_parts.append(f"ATR%={atr_pct:.2f} optimal")
            elif 0.5 <= atr_pct < 1.0 or 3.0 < atr_pct <= 5.0:
                score = 0.6
                details_parts.append(f"ATR%={atr_pct:.2f} acceptable")
            else:
                score = 0.3
                details_parts.append(f"ATR%={atr_pct:.2f} suboptimal")

        # Bollinger Band width (optional bonus)
        if bb_upper and bb_lower and bb_middle and bb_middle > 0:
            bb_width = (bb_upper - bb_lower) / bb_middle
            if 0.02 <= bb_width <= 0.08:
                score = min(1.0, score + 0.1)
                details_parts.append(f"BB_width={bb_width:.3f}")

        return ComponentScore(
            name="volatility",
            raw_score=score,
            weight=weight,
            weighted_score=score * weight,
            direction=ScoreDirection.NEUTRAL,  # Volatility is direction-neutral
            details=" | ".join(details_parts) or "Volatility data limited",
            values={"atr": atr, "bb_width": bb_upper - bb_lower if bb_upper and bb_lower else None}
        )

    def _calc_volume(self, current: pd.Series) -> ComponentScore:
        """Calculate volume confirmation score."""
        weight = self.config.weight_volume

        volume = current.get("volume")
        volume_sma = current.get("volume_sma_20") or current.get("volume_sma")

        if volume is None:
            return ComponentScore(
                name="volume",
                raw_score=0.5,  # Neutral if no data
                weight=weight,
                weighted_score=0.5 * weight,
                direction=ScoreDirection.NEUTRAL,
                details="Volume data not available",
            )

        score = 0.5
        details = "Normal volume"

        if volume_sma and volume_sma > 0:
            ratio = volume / volume_sma

            if ratio >= 1.5:
                score = 1.0
                details = f"High volume ({ratio:.1f}x avg)"
            elif ratio >= 1.0:
                score = 0.8
                details = f"Above avg volume ({ratio:.1f}x)"
            elif ratio >= 0.7:
                score = 0.5
                details = f"Normal volume ({ratio:.1f}x)"
            else:
                score = 0.3
                details = f"Low volume ({ratio:.1f}x avg)"

        return ComponentScore(
            name="volume",
            raw_score=score,
            weight=weight,
            weighted_score=score * weight,
            direction=ScoreDirection.NEUTRAL,  # Volume is direction-neutral
            details=details,
            values={"volume": volume, "volume_sma": volume_sma}
        )

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

    def _get_indicator(self, current: pd.Series, *keys) -> Optional[float]:
        """Get indicator value from series, trying multiple key names."""
        for key in keys:
            val = current.get(key)
            if val is not None and not pd.isna(val):
                return float(val)
        return None

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

    def update_config(self, config: EntryScoreConfig) -> None:
        """Update engine configuration."""
        self.config = config
        self.config.validate()
        logger.info("EntryScoreEngine config updated")


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
    return engine.calculate_score(df, regime_result, symbol, timeframe)


def load_entry_score_config(path: Optional[Path] = None) -> EntryScoreConfig:
    """
    Load entry score config from JSON file.

    Args:
        path: Config file path (default: config/entry_score_config.json)

    Returns:
        Loaded or default config
    """
    if path is None:
        path = Path("config/entry_score_config.json")

    if path.exists():
        try:
            with open(path, "r") as f:
                data = json.load(f)
            return EntryScoreConfig.from_dict(data)
        except Exception as e:
            logger.warning(f"Failed to load entry score config: {e}")

    return EntryScoreConfig()


def save_entry_score_config(config: EntryScoreConfig, path: Optional[Path] = None) -> bool:
    """
    Save entry score config to JSON file.

    Args:
        config: Config to save
        path: Target path (default: config/entry_score_config.json)

    Returns:
        True if saved successfully
    """
    if path is None:
        path = Path("config/entry_score_config.json")

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(config.to_dict(), f, indent=2)
        logger.info(f"Entry score config saved to {path}")
        return True
    except Exception as e:
        logger.error(f"Failed to save entry score config: {e}")
        return False
