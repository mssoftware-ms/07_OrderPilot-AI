"""
Signal Generator Indicator Snapshot - Indicator Extraction for Trade Logging.

Refactored from signal_generator.py using Field Extractor Pattern.

Contains:
- extract_indicator_snapshot: Extracts all indicators from DataFrame for trade logging

Refactoring History:
- Phase 2.2.1: Extracted to Field Extractor Pattern (CC 61 → ~2)
- Each indicator type has dedicated extractor
- Registry-based coordination for modular extraction
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

import pandas as pd

if TYPE_CHECKING:
    from .signal_generator import SignalGenerator
    from .trade_logger import IndicatorSnapshot


class SignalGeneratorIndicatorSnapshot:
    """Helper for indicator snapshot extraction using Field Extractor Pattern."""

    def __init__(self, parent: SignalGenerator):
        self.parent = parent
        self._extractor_registry = None

    def extract_indicator_snapshot(self, df: pd.DataFrame) -> "IndicatorSnapshot":
        """
        Extrahiert Indikator-Snapshot aus DataFrame using Field Extractor Pattern.

        Für Trade-Logging.

        Refactored to use modular field extractors (CC 61 → 2).
        Each indicator type has dedicated extractor.
        """
        from .trade_logger import IndicatorSnapshot

        if df.empty:
            return IndicatorSnapshot(timestamp=datetime.now(timezone.utc))

        # Initialize registry lazily
        if self._extractor_registry is None:
            self._init_extractor_registry()

        # Extract all fields using registry
        fields = self._extractor_registry.extract_all(df)

        # Build and return snapshot
        return IndicatorSnapshot(**fields)

    def _init_extractor_registry(self) -> None:
        """
        Initialize field extractor registry with all extractors.

        Lazy initialization on first use.
        """
        from .snapshot_extractors import (
            FieldExtractorRegistry,
            EMAExtractor,
            RSIExtractor,
            MACDExtractor,
            BollingerExtractor,
            ATRExtractor,
            ADXExtractor,
            VolumeExtractor,
            PriceTimestampExtractor,
        )

        self._extractor_registry = FieldExtractorRegistry()

        # Register all extractors
        self._extractor_registry.register(PriceTimestampExtractor())
        self._extractor_registry.register(EMAExtractor())
        self._extractor_registry.register(RSIExtractor())
        self._extractor_registry.register(MACDExtractor())
        self._extractor_registry.register(BollingerExtractor())
        self._extractor_registry.register(ATRExtractor())
        self._extractor_registry.register(ADXExtractor())
        self._extractor_registry.register(VolumeExtractor())
