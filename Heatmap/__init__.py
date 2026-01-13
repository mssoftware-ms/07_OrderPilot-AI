"""
Binance BTCUSDT Liquidation Heatmap Module

This module provides a background liquidation heatmap feature that:
- Streams Binance USD-M Futures liquidation data (btcusdt@forceOrder)
- Persists events to SQLite for historical analysis
- Renders as a background layer in Lightweight Charts
- Supports on/off toggle with continuous background ingestion

All files follow max 600 lines limit for maintainability.
"""

__version__ = "1.0.0"

from .heatmap_service import HeatmapService
from .heatmap_settings import HeatmapSettings

__all__ = [
    "HeatmapService",
    "HeatmapSettings",
]
