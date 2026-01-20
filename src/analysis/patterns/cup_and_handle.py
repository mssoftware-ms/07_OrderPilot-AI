"""Cup and Handle pattern detector.

Detects the classic Cup and Handle continuation pattern with high success rate (95%).
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


class CupAndHandleDetector(BaseDetector):
    """Detector for Cup and Handle pattern.

    Pattern characteristics:
    - U-shaped bottom (cup) with rounded base
    - Handle forms after cup completion
    - Bullish continuation pattern
    - Success rate: ~95%
    - Ideal cup depth: 15-33% of pattern height
    - Handle should be shallow (<50% of cup depth)
    """

    def __init__(
        self,
        min_pattern_bars: int = 40,
        min_score: float = 80.0,
        pivot_window: int = 5,
        min_cup_depth_pct: float = 0.15,
        max_cup_depth_pct: float = 0.33,
        max_handle_depth_pct: float = 0.50
    ):
        """Initialize Cup and Handle detector.

        Args:
            min_pattern_bars: Minimum bars (40+ recommended)
            min_score: Minimum confidence score
            pivot_window: Window for pivot detection
            min_cup_depth_pct: Minimum cup depth (15%)
            max_cup_depth_pct: Maximum cup depth (33%)
            max_handle_depth_pct: Maximum handle depth relative to cup (50%)
        """
        super().__init__(min_pattern_bars, min_score, pivot_window)
        self.min_cup_depth_pct = min_cup_depth_pct
        self.max_cup_depth_pct = max_cup_depth_pct
        self.max_handle_depth_pct = max_handle_depth_pct

    def detect(self, df: pd.DataFrame) -> List[Pattern]:
        """Detect Cup and Handle patterns.

        Args:
            df: OHLCV DataFrame

        Returns:
            List of detected patterns
        """
        if len(df) < self.min_pattern_bars:
            return []

        pivots = self.detect_pivots(df)
        if len(pivots) < 5:  # Need at least 5 pivots for cup + handle
            return []

        patterns = []

        # Scan for cup and handle formations
        for i in range(len(pivots) - 4):
            pattern_pivots = pivots[i:i + 5]

            # Cup structure: High -> Low -> High
            # Handle structure: High -> Low
            if not self._is_cup_and_handle_structure(pattern_pivots):
                continue

            if not self._validate_geometry(pattern_pivots, df):
                continue

            score = self._calculate_score(pattern_pivots, df)
            if score < self.min_score:
                continue

            pattern = Pattern(
                pattern_type="cup_and_handle",
                score=score,
                direction_bias=DirectionBias.UP,
                pivots=pattern_pivots,
                start_index=pattern_pivots[0].index,
                end_index=pattern_pivots[-1].index,
                metadata=self._extract_metadata(pattern_pivots, df)
            )
            patterns.append(pattern)

        return patterns

    def _is_cup_and_handle_structure(self, pivots: List[Pivot]) -> bool:
        """Check if pivots form cup and handle structure.

        Expected structure (5 pivots):
        P0 (high) -> P1 (low) -> P2 (high) -> P3 (high) -> P4 (low)
        [------- Cup -------] [---- Handle ----]

        Args:
            pivots: List of 5 pivots

        Returns:
            True if structure matches
        """
        if len(pivots) != 5:
            return False

        # Cup: High -> Low -> High
        cup_structure = (
            pivots[0].is_high and
            not pivots[1].is_high and
            pivots[2].is_high
        )

        # Handle: High -> Low
        handle_structure = (
            pivots[3].is_high and
            not pivots[4].is_high
        )

        # Cup rim heights should be similar
        left_rim = pivots[0].price
        right_rim = pivots[2].price
        rim_difference = abs(left_rim - right_rim) / left_rim
        rim_similar = rim_difference < 0.05  # Within 5%

        return cup_structure and handle_structure and rim_similar

    def _validate_geometry(self, pivots: List[Pivot], df: pd.DataFrame) -> bool:
        """Validate Cup and Handle geometry.

        Args:
            pivots: 5 pivots [P0, P1, P2, P3, P4]
            df: Price DataFrame

        Returns:
            True if geometry is valid
        """
        # Cup measurements
        left_rim = pivots[0].price
        cup_bottom = pivots[1].price
        right_rim = pivots[2].price
        cup_height = (left_rim + right_rim) / 2 - cup_bottom
        cup_depth_pct = cup_height / ((left_rim + right_rim) / 2)

        # Cup depth must be in valid range
        if not (self.min_cup_depth_pct <= cup_depth_pct <= self.max_cup_depth_pct):
            return False

        # Handle measurements
        handle_top = pivots[3].price
        handle_bottom = pivots[4].price
        handle_depth = handle_top - handle_bottom
        handle_depth_pct = handle_depth / cup_height

        # Handle should be shallow
        if handle_depth_pct > self.max_handle_depth_pct:
            return False

        # Handle should be above cup bottom
        if handle_bottom < cup_bottom:
            return False

        # Cup should be U-shaped (rounded, not V-shaped)
        cup_duration = pivots[2].index - pivots[0].index
        if cup_duration < self.min_pattern_bars * 0.6:  # Cup too narrow
            return False

        return True

    def _calculate_score(self, pivots: List[Pivot], df: pd.DataFrame) -> float:
        """Calculate Cup and Handle confidence score.

        Components:
        - Symmetry (30%): How symmetric are cup sides?
        - Depth (25%): Is cup depth in ideal range?
        - Handle (20%): Is handle shallow and clean?
        - Volume (15%): Volume decrease in cup, increase on breakout?
        - Rim (10%): Are rims at similar level?

        Args:
            pivots: 5 pivots
            df: Price DataFrame

        Returns:
            Confidence score (0-100)
        """
        scores = {}

        # 1. Symmetry score (30%)
        left_side_duration = pivots[1].index - pivots[0].index
        right_side_duration = pivots[2].index - pivots[1].index
        scores['symmetry'] = self._calculate_symmetry_score(
            left_side_duration, right_side_duration
        ) * 0.30

        # 2. Depth score (25%)
        left_rim = pivots[0].price
        right_rim = pivots[2].price
        cup_bottom = pivots[1].price
        cup_height = (left_rim + right_rim) / 2 - cup_bottom
        cup_depth_pct = cup_height / ((left_rim + right_rim) / 2)

        scores['depth'] = self._calculate_depth_score(
            cup_depth_pct,
            self.min_cup_depth_pct,
            self.max_cup_depth_pct
        ) * 0.25

        # 3. Handle score (20%)
        handle_top = pivots[3].price
        handle_bottom = pivots[4].price
        handle_depth = handle_top - handle_bottom
        handle_depth_pct = handle_depth / cup_height

        if handle_depth_pct < 0.25:  # Ideal: shallow handle
            scores['handle'] = 100.0 * 0.20
        elif handle_depth_pct < self.max_handle_depth_pct:
            scores['handle'] = 70.0 * 0.20
        else:
            scores['handle'] = 30.0 * 0.20

        # 4. Volume score (15%)
        # Ideal: Volume decreases during cup formation, increases on breakout
        cup_start = pivots[0].index
        cup_end = pivots[2].index
        handle_end = pivots[4].index

        cup_volume = df.loc[cup_start:cup_end, 'volume'].mean()
        handle_volume = df.loc[cup_end:handle_end, 'volume'].mean()

        if handle_volume > cup_volume * 1.2:  # Volume increase
            scores['volume'] = 100.0 * 0.15
        elif handle_volume > cup_volume:
            scores['volume'] = 70.0 * 0.15
        else:
            scores['volume'] = 40.0 * 0.15

        # 5. Rim score (10%)
        rim_difference = abs(left_rim - right_rim) / left_rim
        if rim_difference < 0.02:  # Within 2%
            scores['rim'] = 100.0 * 0.10
        elif rim_difference < 0.05:  # Within 5%
            scores['rim'] = 80.0 * 0.10
        else:
            scores['rim'] = 50.0 * 0.10

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
        left_rim = pivots[0].price
        right_rim = pivots[2].price
        cup_bottom = pivots[1].price
        handle_bottom = pivots[4].price

        cup_depth = (left_rim + right_rim) / 2 - cup_bottom
        breakout_level = pivots[3].price

        return {
            'cup_depth_pct': cup_depth / ((left_rim + right_rim) / 2),
            'cup_duration': pivots[2].index - pivots[0].index,
            'handle_duration': pivots[4].index - pivots[2].index,
            'breakout_price': breakout_level,
            'target_price': breakout_level + cup_depth  # Measured move
        }
