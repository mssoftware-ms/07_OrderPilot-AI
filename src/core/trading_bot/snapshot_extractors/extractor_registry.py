"""
Field Extractor Registry.

Manages collection of field extractors and coordinates extraction.
"""

from typing import Dict, Any, List
import pandas as pd
from .base_extractor import BaseFieldExtractor


class FieldExtractorRegistry:
    """
    Registry for field extractors.

    Coordinates multiple extractors to build complete snapshot.
    """

    def __init__(self):
        """Initialize empty registry."""
        self.extractors: List[BaseFieldExtractor] = []

    def register(self, extractor: BaseFieldExtractor) -> None:
        """
        Register a field extractor.

        Args:
            extractor: Field extractor instance
        """
        self.extractors.append(extractor)

    def extract_all(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Extract all fields from DataFrame using registered extractors.

        Args:
            df: DataFrame with indicator data

        Returns:
            Dict with all extracted fields
        """
        if df.empty:
            return {}

        current = df.iloc[-1]
        result = {}

        for extractor in self.extractors:
            fields = extractor.extract(current, df)
            result.update(fields)

        return result
