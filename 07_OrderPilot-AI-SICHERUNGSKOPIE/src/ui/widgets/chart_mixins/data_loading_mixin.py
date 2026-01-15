"""Data Loading Mixin for EmbeddedTradingViewChart.

Contains data loading methods (load_data, load_symbol).

REFACTORED: Split into 6 helper modules using composition pattern:
- data_loading_utils.py: Timezone utilities
- data_loading_cleaning.py: Bad tick cleaning
- data_loading_series.py: Chart series building
- data_loading_resolution.py: Resolution helpers (asset class, timeframe, provider, date range)
- data_loading_symbol.py: Main load_symbol orchestration
- data_loading_mixin.py: Orchestrator + event handlers
"""

from __future__ import annotations

import asyncio
import logging
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd

from .data_loading_cleaning import DataLoadingCleaning
from .data_loading_series import DataLoadingSeries
from .data_loading_resolution import DataLoadingResolution
from .data_loading_symbol import DataLoadingSymbol
from .data_loading_utils import get_local_timezone_offset_seconds  # Re-export for backward compatibility

logger = logging.getLogger(__name__)

# Re-export for backward compatibility
__all__ = ["DataLoadingMixin", "get_local_timezone_offset_seconds"]


class DataLoadingMixin:
    """Mixin providing data loading functionality for EmbeddedTradingViewChart."""

    def _setup_data_loading(self) -> None:
        """Initialize data loading helpers (composition pattern)."""
        # Composition pattern
        self._cleaning = DataLoadingCleaning(parent=self)
        self._series = DataLoadingSeries(parent=self)
        self._resolution = DataLoadingResolution(parent=self)
        self._symbol_loader = DataLoadingSymbol(parent=self)

    # =============================================================================
    # PUBLIC API - DELEGATES TO HELPERS
    # =============================================================================

    def _clean_bad_ticks(self, data: "pd.DataFrame") -> "pd.DataFrame":
        """Delegate to cleaning helper."""
        return self._cleaning.clean_bad_ticks(data)

    def load_data(self, data: "pd.DataFrame"):
        """Load market data into chart.

        Args:
            data: OHLCV DataFrame with DatetimeIndex
        """
        # Wait for page + chart initialization before setting data
        if not (self.page_loaded and self.chart_initialized):
            logger.info("Chart not ready yet, deferring data load")
            self.pending_data_load = data
            return

        try:
            data = self._series.prepare_chart_data(data)
            candle_data, volume_data = self._series.build_chart_series(data)
            # Issue #5: Pass volume_data to create volume panel
            self._series.update_chart_series(candle_data, volume_data)
            self.volume_data = volume_data
            self._series.finalize_chart_load(data, candle_data)

        except Exception as e:
            logger.error(f"Error loading data: {e}", exc_info=True)
            self.market_status_label.setText(f"Error: {str(e)[:30]}")
            self.market_status_label.setStyleSheet("color: #FF0000; font-weight: bold; padding: 5px;")

    async def load_symbol(self, symbol: str, data_provider: Optional[str] = None):
        """Delegate to symbol loader helper."""
        await self._symbol_loader.load_symbol(symbol, data_provider)

    async def refresh_data(self):
        """Public method to refresh chart data (called by main app)."""
        if self.current_symbol:
            await self.load_symbol(self.current_symbol, self.current_data_provider)
        else:
            logger.warning("No symbol loaded to refresh")

    # =============================================================================
    # EVENT HANDLERS
    # =============================================================================

    def _on_symbol_change(self, symbol: str):
        """Handle symbol change."""
        # Ignore separator line
        if symbol == "───────" or not symbol.strip():
            # Revert to previous symbol
            if hasattr(self, 'symbol_combo'):
                self.symbol_combo.setCurrentText(self.current_symbol)
            return

        self.current_symbol = symbol
        self.symbol_changed.emit(symbol)
        logger.info(f"Symbol changed to: {symbol}")

    def _on_timeframe_change(self, timeframe: str):
        """Handle timeframe (candle size) change."""
        self.current_timeframe = timeframe
        self.timeframe_changed.emit(timeframe)
        logger.info(f"Candle size changed to: {timeframe}")

    def _on_period_change(self, period: str):
        """Handle time period change."""
        self.current_period = period
        logger.info(f"Time period changed to: {period}")

    def _on_load_chart(self):
        """Load chart data for current symbol."""
        try:
            # Schedule async task without blocking UI
            asyncio.ensure_future(self._load_chart_async())
        except Exception as e:
            logger.error(f"Failed to schedule chart load: {e}")

    async def _load_chart_async(self):
        """Async implementation of chart loading."""
        try:
            await self.load_symbol(self.current_symbol, self.current_data_provider)
        except Exception as e:
            logger.error(f"Failed to load chart: {e}")

    def _on_refresh(self):
        """Refresh current chart."""
        if self.data is not None:
            self.load_data(self.data)
        else:
            self._on_load_chart()
