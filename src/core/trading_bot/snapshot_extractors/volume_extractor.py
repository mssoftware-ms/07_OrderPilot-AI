"""
Volume Field Extractor.

Extracts volume data and calculates volume ratio.
"""

from typing import Dict, Any
import pandas as pd
from .base_extractor import BaseFieldExtractor


class VolumeExtractor(BaseFieldExtractor):
    """Extracts volume indicator fields."""

    def extract(self, current: pd.Series, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Extract volume fields.

        Fields:
        - volume: Current volume
        - volume_sma_20: 20-period volume SMA
        - volume_ratio: Ratio of current volume to SMA

        Args:
            current: Current row
            df: Complete DataFrame

        Returns:
            Dict with volume fields
        """
        volume = current.get("volume")
        volume_sma = current.get("volume_sma_20")

        volume_ratio = None
        if volume is not None and volume_sma is not None:
            volume_float = self._to_float(volume)
            sma_float = self._to_float(volume_sma)
            if volume_float is not None and sma_float is not None and sma_float > 0:
                volume_ratio = volume_float / sma_float

        return {
            "volume": self._to_float(volume),
            "volume_sma_20": self._to_float(volume_sma),
            "volume_ratio": self._to_float(volume_ratio),
        }
