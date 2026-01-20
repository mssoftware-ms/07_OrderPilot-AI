"""Triple Bottom pattern detector.

Detects the Triple Bottom reversal pattern with high success rate (87%).
"""

from __future__ import annotations

from typing import List
import pandas as pd
import numpy as np

from src.analysis.patterns.base_detector import (
    BaseDetector,
    Pattern,
    Pivot,
    DirectionBias
)


class TripleBottomDetector(BaseDetector):
    """Detector for Triple Bottom pattern.

    Pattern characteristics:
    - Three similar lows (bottoms) separated by two intermediate highs
    - Bottoms should be within 2-3% of each other
    - Bullish reversal pattern
    - Success rate: ~87%
    - Breakout above neckline (intermediate highs) confirms pattern
    """

    def __init__(
        self,
        min_pattern_bars: int = 30,
        min_score: float = 75.0,
        pivot_window: int = 5,
        max_bottom_variance_pct: float = 0.03
    ):
        """Initialize Triple Bottom detector.

        Args:
            min_pattern_bars: Minimum bars (30+ recommended)
            min_score: Minimum confidence score
            pivot_window: Window for pivot detection
            max_bottom_variance_pct: Max allowed variance between bottoms (3%)
        """
        super().__init__(min_pattern_bars, min_score, pivot_window)
        self.max_bottom_variance_pct = max_bottom_variance_pct

    def detect(self, df: pd.DataFrame) -> List[Pattern]:
        """Detect Triple Bottom patterns.

        Args:
            df: OHLCV DataFrame

        Returns:
            List of detected patterns
        """
        if len(df) < self.min_pattern_bars:
            return []

        pivots = self.detect_pivots(df)
        if len(pivots) < 5:  # Need at least 5 pivots
            return []

        patterns = []

        # Scan for triple bottom formations
        for i in range(len(pivots) - 4):
            pattern_pivots = pivots[i:i + 5]

            # Triple bottom structure: Low -> High -> Low -> High -> Low
            if not self._is_triple_bottom_structure(pattern_pivots):
                continue

            if not self._validate_geometry(pattern_pivots, df):
                continue

            score = self._calculate_score(pattern_pivots, df)
            if score < self.min_score:
                continue

            pattern = Pattern(
                pattern_type="triple_bottom",
                score=score,
                direction_bias=DirectionBias.UP,
                pivots=pattern_pivots,
                start_index=pattern_pivots[0].index,
                end_index=pattern_pivots[-1].index,
                metadata=self._extract_metadata(pattern_pivots, df)
            )
            patterns.append(pattern)

        return patterns

    def _is_triple_bottom_structure(self, pivots: List[Pivot]) -> bool:
        """Check if pivots form triple bottom structure.

        Expected structure (5 pivots):
        P0 (low) -> P1 (high) -> P2 (low) -> P3 (high) -> P4 (low)

        Args:
            pivots: List of 5 pivots

        Returns:
            True if structure matches
        """
        if len(pivots) != 5:
            return False

        # Pattern: Low -> High -> Low -> High -> Low
        structure_correct = (
            not pivots[0].is_high and
            pivots[1].is_high and
            not pivots[2].is_high and
            pivots[3].is_high and
            not pivots[4].is_high
        )

        if not structure_correct:
            return False

        # Three bottoms should be at similar levels
        bottom1 = pivots[0].price
        bottom2 = pivots[2].price
        bottom3 = pivots[4].price

        avg_bottom = (bottom1 + bottom2 + bottom3) / 3
        max_deviation = max(
            abs(bottom1 - avg_bottom),
            abs(bottom2 - avg_bottom),
            abs(bottom3 - avg_bottom)
        )

        variance_pct = max_deviation / avg_bottom
        return variance_pct <= self.max_bottom_variance_pct

    def _validate_geometry(self, pivots: List[Pivot], df: pd.DataFrame) -> bool:
        """Validate Triple Bottom geometry.

        Args:
            pivots: 5 pivots [P0, P1, P2, P3, P4]
            df: Price DataFrame

        Returns:
            True if geometry is valid
        """
        # Bottom measurements
        bottoms = [pivots[0].price, pivots[2].price, pivots[4].price]
        avg_bottom = np.mean(bottoms)

        # Intermediate highs (neckline)
        highs = [pivots[1].price, pivots[3].price]
        avg_high = np.mean(highs)

        # Pattern height (neckline to bottoms)
        pattern_height = avg_high - avg_bottom

        # Pattern height should be significant (at least 3% of price)
        if pattern_height / avg_bottom < 0.03:
            return False

        # Neckline should be relatively horizontal
        neckline_slope = abs(pivots[3].price - pivots[1].price) / pattern_height
        if neckline_slope > 0.3:  # Neckline too slanted
            return False

        # Pattern duration should be adequate
        pattern_duration = pivots[4].index - pivots[0].index
        if pattern_duration < self.min_pattern_bars * 0.7:
            return False

        # Bottoms should not be ascending (would be wedge, not triple bottom)
        if bottoms[0] < bottoms[1] < bottoms[2]:
            return False

        # Bottoms should not be descending (would be bearish)
        if bottoms[0] > bottoms[1] > bottoms[2]:
            return False

        return True

    def _calculate_score(self, pivots: List[Pivot], df: pd.DataFrame) -> float:
        """Calculate Triple Bottom confidence score.

        Components:
        - Bottom Alignment (35%): How similar are the three bottoms?
        - Neckline Quality (25%): How horizontal is the neckline?
        - Spacing (20%): Are bottoms evenly spaced?
        - Volume (15%): Volume decrease on each bottom, increase on breakout?
        - Pattern Height (5%): Is pattern height significant?

        Args:
            pivots: 5 pivots
            df: Price DataFrame

        Returns:
            Confidence score (0-100)
        """
        scores = {}

        bottoms = [pivots[0].price, pivots[2].price, pivots[4].price]
        avg_bottom = np.mean(bottoms)

        # 1. Bottom Alignment score (35%)
        max_deviation = max(abs(b - avg_bottom) for b in bottoms)
        alignment_variance_pct = max_deviation / avg_bottom

        if alignment_variance_pct < 0.01:  # Within 1%
            scores['alignment'] = 100.0 * 0.35
        elif alignment_variance_pct < 0.02:  # Within 2%
            scores['alignment'] = 85.0 * 0.35
        elif alignment_variance_pct <= self.max_bottom_variance_pct:  # Within 3%
            scores['alignment'] = 70.0 * 0.35
        else:
            scores['alignment'] = 40.0 * 0.35

        # 2. Neckline Quality score (25%)
        highs = [pivots[1].price, pivots[3].price]
        avg_high = np.mean(highs)
        pattern_height = avg_high - avg_bottom
        neckline_slope = abs(pivots[3].price - pivots[1].price) / pattern_height

        if neckline_slope < 0.05:  # Very horizontal
            scores['neckline'] = 100.0 * 0.25
        elif neckline_slope < 0.15:
            scores['neckline'] = 80.0 * 0.25
        elif neckline_slope < 0.30:
            scores['neckline'] = 60.0 * 0.25
        else:
            scores['neckline'] = 30.0 * 0.25

        # 3. Spacing score (20%)
        spacing1 = pivots[2].index - pivots[0].index
        spacing2 = pivots[4].index - pivots[2].index
        spacing_symmetry = min(spacing1, spacing2) / max(spacing1, spacing2)

        scores['spacing'] = spacing_symmetry * 100.0 * 0.20

        # 4. Volume score (15%)
        # Ideal: Volume decreases on successive bottoms (selling exhaustion)
        try:
            vol_bottom1 = df.loc[pivots[0].index, 'volume']
            vol_bottom2 = df.loc[pivots[2].index, 'volume']
            vol_bottom3 = df.loc[pivots[4].index, 'volume']

            if vol_bottom3 < vol_bottom2 < vol_bottom1:  # Decreasing volume
                scores['volume'] = 100.0 * 0.15
            elif vol_bottom3 < vol_bottom1:  # Partial decrease
                scores['volume'] = 70.0 * 0.15
            else:
                scores['volume'] = 40.0 * 0.15
        except (KeyError, IndexError):
            scores['volume'] = 50.0 * 0.15  # Neutral if volume unavailable

        # 5. Pattern Height score (5%)
        height_pct = pattern_height / avg_bottom
        if height_pct > 0.10:  # Significant height (>10%)
            scores['height'] = 100.0 * 0.05
        elif height_pct > 0.05:
            scores['height'] = 80.0 * 0.05
        else:
            scores['height'] = 50.0 * 0.05

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
        bottoms = [pivots[0].price, pivots[2].price, pivots[4].price]
        avg_bottom = np.mean(bottoms)

        highs = [pivots[1].price, pivots[3].price]
        neckline = np.mean(highs)

        pattern_height = neckline - avg_bottom

        return {
            'avg_bottom_price': avg_bottom,
            'neckline_price': neckline,
            'pattern_height': pattern_height,
            'pattern_duration': pivots[4].index - pivots[0].index,
            'bottom_variance_pct': np.std(bottoms) / avg_bottom,
            'target_price': neckline + pattern_height  # Measured move
        }
