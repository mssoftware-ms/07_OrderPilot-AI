"""
Entry Score Calculators - Component Score Calculation Methods

Handles all technical indicator component calculations:
- LONG components (trend alignment, RSI, MACD)
- SHORT components (inverse signals)
- Shared components (trend strength, volatility, volume)
- Helper methods for indicator extraction

Module 3/4 of entry_score_engine.py split (Lines 494-995)
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, List, Optional

import pandas as pd

if TYPE_CHECKING:
    from src.core.trading_bot.entry_score_config import EntryScoreConfig

from src.core.trading_bot.entry_score_types import (
    ComponentScore,
    ScoreDirection,
)

logger = logging.getLogger(__name__)


# =============================================================================
# ENTRY SCORE CALCULATORS
# =============================================================================


class EntryScoreCalculators:
    """Collection of component score calculation methods."""

    def __init__(self, config: "EntryScoreConfig"):
        """
        Initialize calculators.

        Args:
            config: Entry score configuration
        """
        self.config = config

    # =========================================================================
    # COMPONENT CALCULATIONS - LONG
    # =========================================================================

    def calculate_long_components(
        self, df: pd.DataFrame, current: pd.Series
    ) -> List[ComponentScore]:
        """Calculate all component scores for LONG direction."""
        components = []

        # 1. Trend Alignment (EMA Stack)
        components.append(self.calc_trend_alignment_long(current))

        # 2. RSI Momentum
        components.append(self.calc_rsi_momentum_long(current))

        # 3. MACD Momentum
        components.append(self.calc_macd_momentum_long(current))

        # 4. Trend Strength (ADX)
        components.append(self.calc_trend_strength(current, ScoreDirection.LONG))

        # 5. Volatility
        components.append(self.calc_volatility(current))

        # 6. Volume
        components.append(self.calc_volume(current))

        return components

    def calc_trend_alignment_long(self, current: pd.Series) -> ComponentScore:
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

    def calc_rsi_momentum_long(self, current: pd.Series) -> ComponentScore:
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

    def calc_macd_momentum_long(self, current: pd.Series) -> ComponentScore:
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

    def calculate_short_components(
        self, df: pd.DataFrame, current: pd.Series
    ) -> List[ComponentScore]:
        """Calculate all component scores for SHORT direction."""
        components = []

        # 1. Trend Alignment (EMA Stack - inverse)
        components.append(self.calc_trend_alignment_short(current))

        # 2. RSI Momentum (inverse)
        components.append(self.calc_rsi_momentum_short(current))

        # 3. MACD Momentum (inverse)
        components.append(self.calc_macd_momentum_short(current))

        # 4. Trend Strength (ADX)
        components.append(self.calc_trend_strength(current, ScoreDirection.SHORT))

        # 5. Volatility (same as long)
        components.append(self.calc_volatility(current))

        # 6. Volume (same as long)
        components.append(self.calc_volume(current))

        return components

    def calc_trend_alignment_short(self, current: pd.Series) -> ComponentScore:
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

    def calc_rsi_momentum_short(self, current: pd.Series) -> ComponentScore:
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

    def calc_macd_momentum_short(self, current: pd.Series) -> ComponentScore:
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

    def calc_trend_strength(
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

    def calc_volatility(self, current: pd.Series) -> ComponentScore:
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

    def calc_volume(self, current: pd.Series) -> ComponentScore:
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
    # HELPERS
    # =========================================================================

    def _get_indicator(self, current: pd.Series, *keys) -> Optional[float]:
        """Get indicator value from series, trying multiple key names."""
        for key in keys:
            val = current.get(key)
            if val is not None and not pd.isna(val):
                return float(val)
        return None
