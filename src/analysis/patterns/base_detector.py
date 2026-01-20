"""Base detector for chart pattern recognition."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional
import pandas as pd
import numpy as np


class DirectionBias(str, Enum):
    """Pattern direction bias."""
    UP = "UP"
    DOWN = "DOWN"
    NEUTRAL = "NEUTRAL"


@dataclass
class Pivot:
    """Price pivot point (swing high/low)."""
    price: float
    timestamp: pd.Timestamp
    index: int  # Bar index in DataFrame
    is_high: bool  # True for swing high, False for swing low


@dataclass
class Pattern:
    """Detected chart pattern."""
    pattern_type: str
    score: float  # 0-100 confidence score
    direction_bias: DirectionBias
    pivots: List[Pivot]
    start_index: int
    end_index: int
    metadata: dict  # Additional pattern-specific data


class BaseDetector(ABC):
    """Abstract base class for pattern detectors."""

    def __init__(
        self,
        min_pattern_bars: int = 20,
        min_score: float = 70.0,
        pivot_window: int = 5
    ):
        """Initialize detector.

        Args:
            min_pattern_bars: Minimum bars required for pattern
            min_score: Minimum confidence score (0-100)
            pivot_window: Window size for pivot detection
        """
        self.min_pattern_bars = min_pattern_bars
        self.min_score = min_score
        self.pivot_window = pivot_window

    @abstractmethod
    def detect(self, df: pd.DataFrame) -> List[Pattern]:
        """Detect patterns in price data.

        Args:
            df: DataFrame with columns: open, high, low, close, volume

        Returns:
            List of detected Pattern objects
        """
        pass

    @abstractmethod
    def _validate_geometry(self, pivots: List[Pivot], df: pd.DataFrame) -> bool:
        """Validate pattern-specific geometry rules.

        Args:
            pivots: List of pivot points
            df: Price DataFrame

        Returns:
            True if geometry is valid
        """
        pass

    @abstractmethod
    def _calculate_score(self, pivots: List[Pivot], df: pd.DataFrame) -> float:
        """Calculate pattern confidence score.

        Args:
            pivots: List of pivot points
            df: Price DataFrame

        Returns:
            Confidence score (0-100)
        """
        pass

    def detect_pivots(
        self,
        df: pd.DataFrame,
        window: Optional[int] = None
    ) -> List[Pivot]:
        """Detect swing highs and lows (pivot points).

        Args:
            df: DataFrame with high/low columns
            window: Window size (defaults to self.pivot_window)

        Returns:
            List of Pivot objects sorted by index
        """
        if window is None:
            window = self.pivot_window

        pivots = []
        highs = df['high'].values
        lows = df['low'].values

        for i in range(window, len(df) - window):
            # Check for swing high
            if self._is_swing_high(highs, i, window):
                pivots.append(Pivot(
                    price=highs[i],
                    timestamp=df.index[i],
                    index=i,
                    is_high=True
                ))

            # Check for swing low
            if self._is_swing_low(lows, i, window):
                pivots.append(Pivot(
                    price=lows[i],
                    timestamp=df.index[i],
                    index=i,
                    is_high=False
                ))

        return sorted(pivots, key=lambda p: p.index)

    def _is_swing_high(self, highs: np.ndarray, i: int, window: int) -> bool:
        """Check if index i is a swing high.

        Args:
            highs: Array of high prices
            i: Current index
            window: Window size

        Returns:
            True if swing high detected
        """
        center_high = highs[i]
        left_highs = highs[i - window:i]
        right_highs = highs[i + 1:i + window + 1]

        return (
            np.all(center_high > left_highs) and
            np.all(center_high > right_highs)
        )

    def _is_swing_low(self, lows: np.ndarray, i: int, window: int) -> bool:
        """Check if index i is a swing low.

        Args:
            lows: Array of low prices
            i: Current index
            window: Window size

        Returns:
            True if swing low detected
        """
        center_low = lows[i]
        left_lows = lows[i - window:i]
        right_lows = lows[i + 1:i + window + 1]

        return (
            np.all(center_low < left_lows) and
            np.all(center_low < right_lows)
        )

    def _calculate_symmetry_score(
        self,
        left_duration: int,
        right_duration: int
    ) -> float:
        """Calculate symmetry score for pattern sides.

        Args:
            left_duration: Bars on left side
            right_duration: Bars on right side

        Returns:
            Symmetry score (0-100)
        """
        if left_duration == 0 or right_duration == 0:
            return 0.0

        ratio = min(left_duration, right_duration) / max(left_duration, right_duration)
        return ratio * 100.0

    def _calculate_depth_score(
        self,
        depth_pct: float,
        ideal_min: float,
        ideal_max: float
    ) -> float:
        """Calculate score based on pattern depth percentage.

        Args:
            depth_pct: Actual depth as % of pattern height
            ideal_min: Ideal minimum depth %
            ideal_max: Ideal maximum depth %

        Returns:
            Depth score (0-100)
        """
        if depth_pct < ideal_min * 0.5:  # Too shallow
            return 0.0
        elif depth_pct < ideal_min:
            return 50.0
        elif ideal_min <= depth_pct <= ideal_max:
            return 100.0
        elif depth_pct <= ideal_max * 1.5:  # Slightly too deep
            return 70.0
        else:  # Way too deep
            return 30.0
