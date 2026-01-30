"""Base class for entry signal generators.

Provides the interface for rule-type-specific entry generation.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from ..entry_signal_engine import EntryEvent, OptimParams, RegimeType


class BaseEntryGenerator(ABC):
    """Abstract base class for entry signal generators.

    Each generator handles a specific regime type or pattern,
    reducing complexity compared to the monolithic approach.

    Attributes:
        regime: The regime type this generator handles.
    """

    def __init__(self, regime: RegimeType):
        """Initialize generator.

        Args:
            regime: The regime type this generator handles.
        """
        self.regime = regime

    @abstractmethod
    def can_generate(self, regime: RegimeType) -> bool:
        """Check if this generator handles the given regime type.

        Args:
            regime: The regime to check.

        Returns:
            True if this generator can handle the regime.
        """
        pass

    @abstractmethod
    def generate(
        self,
        candles: list[dict[str, Any]],
        features: dict[str, list[float]],
        params: OptimParams,
    ) -> list[EntryEvent]:
        """Generate entry signals for this regime type.

        Args:
            candles: OHLCV candles.
            features: Calculated technical features.
            params: Entry parameters.

        Returns:
            List of entry events.
        """
        pass

    def _safe_float(self, x: Any, default: float = 0.0) -> float:
        """Safely convert to float.

        Args:
            x: Value to convert.
            default: Default value if conversion fails.

        Returns:
            Float value or default.
        """
        try:
            return float(x)
        except Exception:
            return default

    def _clamp(self, x: float, lo: float, hi: float) -> float:
        """Clamp value to range.

        Args:
            x: Value to clamp.
            lo: Lower bound.
            hi: Upper bound.

        Returns:
            Clamped value.
        """
        return lo if x < lo else hi if x > hi else x
