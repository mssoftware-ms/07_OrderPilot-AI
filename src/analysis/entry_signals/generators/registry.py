"""Registry for entry signal generators.

Central dispatch system for routing entry generation to appropriate generators.
"""

from __future__ import annotations

from typing import Any

from ..entry_signal_engine import EntryEvent, OptimParams, RegimeType
from .base_generator import BaseEntryGenerator


class EntryGeneratorRegistry:
    """Registry for entry signal generators.

    Maintains a list of generators and dispatches generation
    requests to the appropriate generator based on regime type.

    Attributes:
        _generators: List of registered generators.
    """

    def __init__(self):
        """Initialize empty registry."""
        self._generators: list[BaseEntryGenerator] = []

    def register(self, generator: BaseEntryGenerator) -> None:
        """Register a new generator.

        Args:
            generator: The generator to register.
        """
        self._generators.append(generator)

    def generate(
        self,
        candles: list[dict[str, Any]],
        features: dict[str, list[float]],
        regime: RegimeType,
        params: OptimParams,
    ) -> list[EntryEvent]:
        """Generate entries using the appropriate generator.

        Args:
            candles: OHLCV candles.
            features: Calculated features.
            regime: Market regime.
            params: Entry parameters.

        Returns:
            List of entry events from the matched generator.

        Raises:
            ValueError: If no generator can handle the regime.
        """
        for generator in self._generators:
            if generator.can_generate(regime):
                return generator.generate(candles, features, params)

        # No generator found - return empty list (graceful fallback)
        return []

    def has_generator_for(self, regime: RegimeType) -> bool:
        """Check if a generator exists for the given regime.

        Args:
            regime: The regime to check.

        Returns:
            True if a generator can handle the regime.
        """
        return any(g.can_generate(regime) for g in self._generators)
