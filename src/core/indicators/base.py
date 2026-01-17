"""Base Indicator Calculator.

Provides common functionality for all indicator calculators.
"""

import logging
import warnings
from datetime import datetime
from typing import Any

import pandas as pd

# Try to import TA-Lib (optional dependency)
try:
    import talib
    TALIB_AVAILABLE = True
except ImportError:
    TALIB_AVAILABLE = False
    logger.debug("TA-Lib not installed. Some indicators will be unavailable.")

# Try to import pandas_ta (fallback for TA-Lib)
try:
    import pandas_ta as ta
    PANDAS_TA_AVAILABLE = True
except ImportError:
    PANDAS_TA_AVAILABLE = False
    logger.debug("pandas_ta not installed. Some indicators will be unavailable.")

from .types import IndicatorConfig, IndicatorResult, IndicatorType

logger = logging.getLogger(__name__)


class BaseIndicatorCalculator:
    """Base class for indicator calculators.

    Provides common utilities and validation logic.
    """

    @staticmethod
    def validate_data(data: pd.DataFrame, config: IndicatorConfig) -> bool:
        """Validate input data.

        Args:
            data: OHLCV DataFrame
            config: Indicator configuration

        Returns:
            True if valid
        """
        required_columns = ['open', 'high', 'low', 'close', 'volume']

        if not all(col in data.columns for col in required_columns):
            return False

        if config.min_periods and len(data) < config.min_periods:
            return False

        return True

    @staticmethod
    def create_result(
        indicator_type: IndicatorType,
        values: pd.Series | pd.DataFrame | dict[str, Any],
        params: dict[str, Any],
        metadata: dict[str, Any] | None = None
    ) -> IndicatorResult:
        """Create indicator result.

        Args:
            indicator_type: Type of indicator
            values: Calculated values
            params: Calculation parameters
            metadata: Optional metadata

        Returns:
            Indicator result
        """
        return IndicatorResult(
            indicator_type=indicator_type,
            values=values,
            timestamp=datetime.utcnow(),
            params=params,
            metadata=metadata
        )


# Export library availability flags
__all__ = [
    'BaseIndicatorCalculator',
    'TALIB_AVAILABLE',
    'PANDAS_TA_AVAILABLE'
]

# Only export talib if available
if TALIB_AVAILABLE:
    __all__.append('talib')

# Only export pandas_ta if available
if PANDAS_TA_AVAILABLE:
    __all__.append('ta')
