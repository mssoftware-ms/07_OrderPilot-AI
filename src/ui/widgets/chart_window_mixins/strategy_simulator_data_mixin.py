from __future__ import annotations

import logging
import pandas as pd
from PyQt6.QtWidgets import QMessageBox

logger = logging.getLogger(__name__)

class StrategySimulatorDataMixin:
    """Data filtering and chart access"""

    def _filter_data_to_time_range(
        self, full_data: pd.DataFrame, hours: int
    ) -> pd.DataFrame:
        """Filter DataFrame to the last N hours of data.

        Args:
            full_data: Full chart DataFrame
            hours: Number of hours to include

        Returns:
            Filtered DataFrame containing the last N hours
        """
        # Calculate number of bars needed
        bars_needed = self._calculate_bars_for_time_range(hours)

        # Take the last N bars
        if len(full_data) <= bars_needed:
            logger.info(
                f"Data has only {len(full_data)} bars, "
                f"using all (requested {bars_needed} for {hours}h)"
            )
            return full_data

        filtered_data = full_data.iloc[-bars_needed:].copy()
        logger.info(
            f"Filtered data to last {hours}h: {len(filtered_data)} bars "
            f"(from {len(full_data)} total)"
        )
        return filtered_data

    def _filter_data_to_visible_range(
        self, full_data: pd.DataFrame, visible_range: dict | None
    ) -> pd.DataFrame:
        """Filter DataFrame to only include data in the visible chart range.

        Args:
            full_data: Full chart DataFrame
            visible_range: Dict with 'from' and 'to' logical indices

        Returns:
            Filtered DataFrame containing only visible data
        """
        if visible_range is None:
            logger.info("No visible range available - using all data")
            return full_data

        # Get from/to indices from visible range
        from_idx = visible_range.get("from")
        to_idx = visible_range.get("to")

        if from_idx is None or to_idx is None:
            logger.warning("Invalid visible range - using all data")
            return full_data

        # Convert to integers and clamp to valid range
        from_idx = max(0, int(from_idx))
        to_idx = min(len(full_data), int(to_idx) + 1)  # +1 because iloc is exclusive

        if from_idx >= to_idx:
            logger.warning(f"Invalid range [{from_idx}:{to_idx}] - using all data")
            return full_data

        # Filter using iloc (position-based indexing)
        filtered_data = full_data.iloc[from_idx:to_idx].copy()

        logger.info(
            f"Filtered data to visible range: [{from_idx}:{to_idx}] "
            f"({len(filtered_data)} of {len(full_data)} bars)"
        )

        return filtered_data

    def _get_chart_dataframe(self):
        """Get chart dataframe - for backward compatibility.

        Note: This returns all data. Use _get_full_chart_dataframe() explicitly
        when you need all data, or use _on_run_simulation() which handles
        visible range filtering automatically.
        """
        return self._get_full_chart_dataframe()

    def _get_full_chart_dataframe(self):
        """Get the full chart DataFrame without visible range filtering."""
        if hasattr(self.chart_widget, "data") and self.chart_widget.data is not None:
            return self.chart_widget.data
        if hasattr(self.chart_widget, "get_dataframe"):
            return self.chart_widget.get_dataframe()
        if hasattr(self.chart_widget, "_df"):
            return self.chart_widget._df
        return None

    def _get_simulation_symbol(self) -> str:
        symbol = getattr(self, "symbol", "UNKNOWN")
        if hasattr(self.chart_widget, "current_symbol") and self.chart_widget.current_symbol:
            return self.chart_widget.current_symbol
        if hasattr(self.chart_widget, "symbol"):
            return self.chart_widget.symbol
        return symbol

    def _get_data_range_info(self) -> dict:
        """Get information about the data range based on selected time range.

        Returns:
            Dictionary with data range information for the SELECTED time range,
            not the full data.
        """
        info = {
            "symbol": "N/A",
            "timeframe": "N/A",
            "total_bars": 0,
            "selected_bars": 0,
            "visible_bars": "N/A",
            "start_date": None,
            "end_date": None,
        }

        # Get symbol
        info["symbol"] = self._get_simulation_symbol()

        # Get timeframe from chart
        timeframe = self._get_chart_timeframe()
        info["timeframe"] = timeframe

        # Get full data info
        full_data = self._get_full_chart_dataframe()
        if full_data is None or full_data.empty:
            return info

        info["total_bars"] = len(full_data)

        # Get selected time range from UI
        time_range = self._get_selected_time_range()

        # Calculate bars and dates based on selected time range
        if time_range == "visible":
            # For visible range, estimate based on typical chart view
            info["selected_bars"] = f"~{min(200, len(full_data))} (sichtbar)"
            info["visible_bars"] = info["selected_bars"]
            # Show last portion of data as estimate
            estimate_bars = min(200, len(full_data))
            if estimate_bars > 0:
                subset = full_data.iloc[-estimate_bars:]
                self._fill_date_range(info, subset)
        elif time_range == "all":
            # All data
            info["selected_bars"] = len(full_data)
            info["visible_bars"] = len(full_data)
            self._fill_date_range(info, full_data)
        else:
            # Fixed time range in hours
            hours = int(time_range)
            bars_needed = self._calculate_bars_for_time_range(hours)
            actual_bars = min(bars_needed, len(full_data))
            info["selected_bars"] = actual_bars
            info["visible_bars"] = actual_bars

            # Get the subset of data that will actually be used
            if actual_bars > 0:
                subset = full_data.iloc[-actual_bars:]
                self._fill_date_range(info, subset)

        return info

    def _fill_date_range(self, info: dict, data) -> None:
        """Fill start_date and end_date in info dict from DataFrame.

        Args:
            info: Dictionary to update with date information
            data: DataFrame with datetime index
        """
        try:
            if data is not None and not data.empty:
                if hasattr(data.index, "min") and hasattr(data.index, "max"):
                    start = data.index.min()
                    end = data.index.max()
                    if hasattr(start, "strftime"):
                        info["start_date"] = start.strftime("%Y-%m-%d %H:%M")
                        info["end_date"] = end.strftime("%Y-%m-%d %H:%M")
                    else:
                        info["start_date"] = str(start)
                        info["end_date"] = str(end)
        except Exception as e:
            logger.debug(f"Could not get date range: {e}")

