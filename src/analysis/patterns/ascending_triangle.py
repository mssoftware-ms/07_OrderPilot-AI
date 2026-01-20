"""Ascending Triangle pattern detector.

Detects the Ascending Triangle continuation pattern with high success rate (83%).
"""

from __future__ import annotations

from typing import List, Tuple
import pandas as pd
import numpy as np

from src.analysis.patterns.base_detector import (
    BaseDetector,
    Pattern,
    Pivot,
    DirectionBias
)


def _simple_linregress(x: np.ndarray, y: np.ndarray) -> Tuple[float, float]:
    """Simple linear regression without scipy.

    Args:
        x: Independent variable
        y: Dependent variable

    Returns:
        (slope, r_squared)
    """
    n = len(x)
    if n < 2:
        return 0.0, 0.0

    # Calculate means
    x_mean = np.mean(x)
    y_mean = np.mean(y)

    # Calculate slope
    numerator = np.sum((x - x_mean) * (y - y_mean))
    denominator = np.sum((x - x_mean) ** 2)

    if denominator == 0:
        return 0.0, 0.0

    slope = numerator / denominator

    # Calculate R²
    y_pred = slope * (x - x_mean) + y_mean
    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - y_mean) ** 2)

    if ss_tot == 0:
        r_squared = 0.0
    else:
        r_squared = 1 - (ss_res / ss_tot)

    return slope, r_squared


class AscendingTriangleDetector(BaseDetector):
    """Detector for Ascending Triangle pattern.

    Pattern characteristics:
    - Horizontal resistance line (multiple highs at similar level)
    - Ascending support line (higher lows)
    - Bullish continuation pattern
    - Success rate: ~83%
    - Breakout above resistance confirms pattern
    - Target: Height of triangle projected from breakout
    """

    def __init__(
        self,
        min_pattern_bars: int = 25,
        min_score: float = 70.0,
        pivot_window: int = 5,
        max_resistance_variance_pct: float = 0.02
    ):
        """Initialize Ascending Triangle detector.

        Args:
            min_pattern_bars: Minimum bars (25+ recommended)
            min_score: Minimum confidence score
            pivot_window: Window for pivot detection
            max_resistance_variance_pct: Max variance in resistance line (2%)
        """
        super().__init__(min_pattern_bars, min_score, pivot_window)
        self.max_resistance_variance_pct = max_resistance_variance_pct

    def detect(self, df: pd.DataFrame) -> List[Pattern]:
        """Detect Ascending Triangle patterns.

        Args:
            df: OHLCV DataFrame

        Returns:
            List of detected patterns
        """
        if len(df) < self.min_pattern_bars:
            return []

        pivots = self.detect_pivots(df)
        if len(pivots) < 5:  # Need at least 3 highs + 2 lows
            return []

        patterns = []

        # Scan for ascending triangle formations
        # Need: At least 3 highs at resistance + 2+ lows forming ascending support
        for i in range(len(pivots) - 4):
            # Try windows of 5-8 pivots
            for window_size in [5, 6, 7, 8]:
                if i + window_size > len(pivots):
                    break

                pattern_pivots = pivots[i:i + window_size]

                if not self._is_ascending_triangle_structure(pattern_pivots):
                    continue

                if not self._validate_geometry(pattern_pivots, df):
                    continue

                score = self._calculate_score(pattern_pivots, df)
                if score < self.min_score:
                    continue

                pattern = Pattern(
                    pattern_type="ascending_triangle",
                    score=score,
                    direction_bias=DirectionBias.UP,
                    pivots=pattern_pivots,
                    start_index=pattern_pivots[0].index,
                    end_index=pattern_pivots[-1].index,
                    metadata=self._extract_metadata(pattern_pivots, df)
                )
                patterns.append(pattern)

        return patterns

    def _is_ascending_triangle_structure(self, pivots: List[Pivot]) -> bool:
        """Check if pivots form ascending triangle structure.

        Requirements:
        - At least 3 swing highs at similar level (resistance)
        - At least 2 swing lows forming ascending support
        - Highs and lows should alternate

        Args:
            pivots: List of pivots (5-8)

        Returns:
            True if structure matches
        """
        if len(pivots) < 5:
            return False

        # Separate highs and lows
        highs = [p for p in pivots if p.is_high]
        lows = [p for p in pivots if not p.is_high]

        # Need at least 3 highs and 2 lows
        if len(highs) < 3 or len(lows) < 2:
            return False

        # Check resistance line (highs should be at similar level)
        high_prices = [h.price for h in highs]
        avg_high = np.mean(high_prices)
        max_deviation = max(abs(h - avg_high) for h in high_prices)
        resistance_variance = max_deviation / avg_high

        if resistance_variance > self.max_resistance_variance_pct:
            return False

        # Check support line (lows should be ascending)
        low_prices = [l.price for l in lows]
        if not self._is_ascending(low_prices):
            return False

        return True

    def _is_ascending(self, prices: List[float]) -> bool:
        """Check if prices form ascending pattern.

        Args:
            prices: List of prices

        Returns:
            True if generally ascending
        """
        if len(prices) < 2:
            return False

        # Use linear regression to check upward slope
        indices = np.arange(len(prices))
        slope, r_squared = _simple_linregress(indices, prices)

        # Positive slope with reasonable fit
        return slope > 0 and r_squared > 0.5

    def _validate_geometry(self, pivots: List[Pivot], df: pd.DataFrame) -> bool:
        """Validate Ascending Triangle geometry.

        Args:
            pivots: Pattern pivots
            df: Price DataFrame

        Returns:
            True if geometry is valid
        """
        highs = [p for p in pivots if p.is_high]
        lows = [p for p in pivots if not p.is_high]

        # Calculate triangle height (resistance - first low)
        avg_resistance = np.mean([h.price for h in highs])
        first_low = lows[0].price
        triangle_height = avg_resistance - first_low

        # Height should be significant (at least 3% of price)
        if triangle_height / avg_resistance < 0.03:
            return False

        # Triangle should converge (last low closer to resistance than first)
        last_low = lows[-1].price
        convergence = (last_low - first_low) / triangle_height

        if convergence < 0.3:  # Not converging enough
            return False

        if convergence > 0.9:  # Converged too much (no space left)
            return False

        # Pattern duration should be adequate
        pattern_duration = pivots[-1].index - pivots[0].index
        if pattern_duration < self.min_pattern_bars * 0.7:
            return False

        # Resistance should not be sloping (should be horizontal)
        high_prices = np.array([h.price for h in highs])
        high_indices = np.array([h.index for h in highs])
        slope, _ = _simple_linregress(high_indices, high_prices)
        resistance_slope = abs(slope) * pattern_duration / avg_resistance

        if resistance_slope > 0.05:  # Resistance too slanted (>5%)
            return False

        return True

    def _calculate_score(self, pivots: List[Pivot], df: pd.DataFrame) -> float:
        """Calculate Ascending Triangle confidence score.

        Components:
        - Resistance Quality (30%): How horizontal is the resistance?
        - Support Ascent (25%): How strong is the ascending support?
        - Convergence (20%): Is the triangle converging properly?
        - Volume (15%): Volume contraction during formation?
        - Touch Count (10%): More touches = stronger pattern

        Args:
            pivots: Pattern pivots
            df: Price DataFrame

        Returns:
            Confidence score (0-100)
        """
        scores = {}

        highs = [p for p in pivots if p.is_high]
        lows = [p for p in pivots if not p.is_high]

        avg_resistance = np.mean([h.price for h in highs])
        pattern_duration = pivots[-1].index - pivots[0].index

        # 1. Resistance Quality score (30%)
        high_prices = np.array([h.price for h in highs])
        high_indices = np.array([h.index for h in highs])
        slope, r_squared = _simple_linregress(high_indices, high_prices)
        resistance_slope = abs(slope) * pattern_duration / avg_resistance

        resistance_r2 = r_squared
        if resistance_slope < 0.01 and resistance_r2 > 0.8:  # Very horizontal
            scores['resistance'] = 100.0 * 0.30
        elif resistance_slope < 0.03 and resistance_r2 > 0.6:
            scores['resistance'] = 80.0 * 0.30
        elif resistance_slope < 0.05:
            scores['resistance'] = 60.0 * 0.30
        else:
            scores['resistance'] = 30.0 * 0.30

        # 2. Support Ascent score (25%)
        low_prices = np.array([l.price for l in lows])
        low_indices = np.array([l.index for l in lows])
        slope, r_squared = _simple_linregress(low_indices, low_prices)

        support_r2 = r_squared
        if slope > 0 and support_r2 > 0.8:  # Strong upward trend
            scores['support'] = 100.0 * 0.25
        elif slope > 0 and support_r2 > 0.6:
            scores['support'] = 80.0 * 0.25
        elif slope > 0:
            scores['support'] = 60.0 * 0.25
        else:
            scores['support'] = 20.0 * 0.25

        # 3. Convergence score (20%)
        first_low = lows[0].price
        last_low = lows[-1].price
        triangle_height = avg_resistance - first_low
        convergence = (last_low - first_low) / triangle_height

        if 0.5 <= convergence <= 0.7:  # Ideal convergence
            scores['convergence'] = 100.0 * 0.20
        elif 0.3 <= convergence <= 0.8:
            scores['convergence'] = 80.0 * 0.20
        else:
            scores['convergence'] = 50.0 * 0.20

        # 4. Volume score (15%)
        # Ideal: Volume contracts during triangle formation
        try:
            start_idx = pivots[0].index
            mid_idx = pivots[len(pivots)//2].index
            end_idx = pivots[-1].index

            vol_start = df.loc[start_idx, 'volume']
            vol_mid = df.loc[mid_idx, 'volume']
            vol_end = df.loc[end_idx, 'volume']

            if vol_end < vol_mid < vol_start:  # Contracting volume
                scores['volume'] = 100.0 * 0.15
            elif vol_end < vol_start:  # Partial contraction
                scores['volume'] = 70.0 * 0.15
            else:
                scores['volume'] = 40.0 * 0.15
        except (KeyError, IndexError):
            scores['volume'] = 50.0 * 0.15

        # 5. Touch Count score (10%)
        touch_count = len(highs) + len(lows)
        if touch_count >= 7:  # Many touches
            scores['touches'] = 100.0 * 0.10
        elif touch_count >= 6:
            scores['touches'] = 80.0 * 0.10
        elif touch_count >= 5:
            scores['touches'] = 60.0 * 0.10
        else:
            scores['touches'] = 40.0 * 0.10

        total_score = sum(scores.values())
        return total_score

    def _extract_metadata(self, pivots: List[Pivot], df: pd.DataFrame) -> dict:
        """Extract pattern-specific metadata.

        Args:
            pivots: Pattern pivots
            df: Price DataFrame

        Returns:
            Metadata dict
        """
        highs = [p for p in pivots if p.is_high]
        lows = [p for p in pivots if not p.is_high]

        resistance = np.mean([h.price for h in highs])
        first_low = lows[0].price
        triangle_height = resistance - first_low

        return {
            'resistance_level': resistance,
            'initial_support': first_low,
            'triangle_height': triangle_height,
            'pattern_duration': pivots[-1].index - pivots[0].index,
            'touch_count': len(highs) + len(lows),
            'target_price': resistance + triangle_height  # Measured move
        }
