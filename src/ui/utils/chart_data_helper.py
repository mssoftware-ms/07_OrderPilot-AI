"""Helper utilities for accessing chart data from parent widgets."""

from __future__ import annotations

from typing import Optional, List, Tuple
from PyQt6.QtWidgets import QWidget
import pandas as pd
import logging

logger = logging.getLogger(__name__)


class ChartDataHelper:
    """Helper for accessing chart data from parent widgets."""

    @staticmethod
    def get_bars_from_chart(
        widget: QWidget,
        window_size: Optional[int] = None,
        chart_window=None
    ) -> Tuple[Optional[List], Optional[str], Optional[str]]:
        """
        Extract HistoricalBar objects from parent chart widget.

        Args:
            widget: Widget with parent().chart_widget attribute
            window_size: Number of bars to include, or None to use all available bars
            chart_window: Optional chart window to use directly (if widget.parent() is not chart window)

        Returns:
            Tuple of (bars, symbol, timeframe) or (None, None, None) if data unavailable

        Example:
            >>> # Use all visible bars from chart
            >>> bars, symbol, timeframe = ChartDataHelper.get_bars_from_chart(self, window_size=None)
            >>> # Or with explicit chart window
            >>> bars, symbol, timeframe = ChartDataHelper.get_bars_from_chart(self, window_size=None, chart_window=self.chart_window)
            >>> if bars is None:
            ...     QMessageBox.warning(self, "No Data", "No chart data available")
            ...     return
        """
        # Get chart widget - either from provided chart_window or widget.parent()
        chart_widget = None

        if chart_window is not None and hasattr(chart_window, 'chart_widget'):
            chart_widget = chart_window.chart_widget
            logger.debug("Using provided chart_window")
        elif hasattr(widget, 'chart_window') and widget.chart_window is not None:
            if hasattr(widget.chart_window, 'chart_widget'):
                chart_widget = widget.chart_window.chart_widget
                logger.debug("Using widget.chart_window")
        elif hasattr(widget.parent(), 'chart_widget'):
            chart_widget = widget.parent().chart_widget
            logger.debug("Using widget.parent().chart_widget")

        if chart_widget is None:
            logger.warning("No chart widget found in chart_window, widget.chart_window, or widget.parent()")
            return None, None, None

        if not hasattr(chart_widget, 'data') or chart_widget.data is None:
            logger.warning("Chart widget has no data")
            return None, None, None

        chart_data = chart_widget.data
        if len(chart_data) == 0:
            logger.warning("Chart data is empty")
            return None, None, None

        # Import here to avoid circular imports
        from src.core.market_data.types import HistoricalBar

        # Determine how many bars to extract
        if window_size is None:
            # Use all available bars from chart
            data_to_convert = chart_data
            logger.info(f"Using all {len(chart_data)} available bars from chart")
        else:
            # Use specified window size plus buffer
            data_to_convert = chart_data.tail(window_size + 50)
            logger.info(f"Using last {window_size + 50} bars from chart")

        # Convert to HistoricalBar objects
        bars = []
        try:
            for timestamp, row in data_to_convert.iterrows():
                bar = HistoricalBar(
                    timestamp=timestamp,
                    open=float(row['open']),
                    high=float(row['high']),
                    low=float(row['low']),
                    close=float(row['close']),
                    volume=float(row.get('volume', 0))
                )
                bars.append(bar)
        except Exception as e:
            logger.exception(f"Failed to convert chart data to HistoricalBar objects: {e}")
            return None, None, None

        # Get symbol and timeframe
        symbol = getattr(chart_widget, 'current_symbol', 'UNKNOWN')
        timeframe = getattr(chart_widget, 'timeframe', '1m')

        logger.info(f"Extracted {len(bars)} bars for {symbol} ({timeframe})")
        return bars, symbol, timeframe
