"""Indicator Conversion - Data conversion to chart format.

Refactored from 676 LOC monolith using composition pattern.

Module 3/7 of indicator_mixin.py split.

Contains:
- convert_indicator_result(): Main dispatcher
- convert_macd_data_to_chart_format(): MACD-specific conversion
- convert_multi_series_data_to_chart_format(): Multi-series conversion
- convert_single_series_data_to_chart_format(): Single-series conversion
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pandas as pd

if TYPE_CHECKING:
    from src.core.indicators.engine import IndicatorResult

from .indicator_utils import _ts_to_local_unix

logger = logging.getLogger(__name__)


class IndicatorConversion:
    """Helper für IndicatorMixin data conversion."""

    def __init__(self, parent):
        """
        Args:
            parent: IndicatorMixin Instanz
        """
        self.parent = parent

    def convert_indicator_result(self, ind_id: str, result: "IndicatorResult"):
        """Dispatch to appropriate conversion method based on result type.

        Args:
            ind_id: Indicator ID string
            result: IndicatorResult from engine

        Returns:
            Converted data (list or dict)
        """
        if isinstance(result.values, pd.DataFrame) and ind_id == "MACD":
            return self.convert_macd_data_to_chart_format(result)
        if isinstance(result.values, pd.DataFrame):
            return self.convert_multi_series_data_to_chart_format(result, ind_id)
        return self.convert_single_series_data_to_chart_format(result)

    def convert_macd_data_to_chart_format(self, result: "IndicatorResult"):
        """Convert MACD indicator result to chart format.

        Args:
            result: IndicatorResult with DataFrame values

        Returns:
            Dict with 'macd', 'signal', 'histogram' keys
        """
        col_names = result.values.columns.tolist()
        logger.info(f"MACD columns: {col_names}")

        # Find columns (check histogram and signal first to avoid false matches)
        macd_col = signal_col = hist_col = None
        for col in col_names:
            col_lower = col.lower()
            if 'macdh' in col_lower or 'hist' in col_lower:
                hist_col = col
            elif 'macds' in col_lower or 'signal' in col_lower:
                signal_col = col
            elif 'macd' in col_lower:
                macd_col = col

        macd_series = result.values[macd_col] if macd_col else None
        signal_series = result.values[signal_col] if signal_col else None
        hist_series = result.values[hist_col] if hist_col else None

        logger.info(f"MACD column mapping: macd={macd_col}, signal={signal_col}, hist={hist_col}")

        # Convert each series to chart format
        macd_data = [
            {'time': _ts_to_local_unix(ts), 'value': float(val)}
            for ts, val in zip(self.parent.data.index, macd_series.values if macd_series is not None else [])
            if not pd.isna(val)
        ]

        signal_data = [
            {'time': _ts_to_local_unix(ts), 'value': float(val)}
            for ts, val in zip(self.parent.data.index, signal_series.values if signal_series is not None else [])
            if not pd.isna(val)
        ]

        hist_data = [
            {
                'time': _ts_to_local_unix(ts),
                'value': float(val),
                'color': '#26a69a' if float(val) >= 0 else '#ef5350'
            }
            for ts, val in zip(self.parent.data.index, hist_series.values if hist_series is not None else [])
            if not pd.isna(val)
        ]

        logger.info(f"MACD data prepared: macd={len(macd_data)} points, signal={len(signal_data)} points, histogram={len(hist_data)} points")

        return {
            'macd': macd_data,
            'signal': signal_data,
            'histogram': hist_data
        }

    def convert_multi_series_data_to_chart_format(self, result: "IndicatorResult", ind_id: str):
        """Convert multi-series indicator result to chart format.

        Args:
            result: IndicatorResult with DataFrame values
            ind_id: Indicator ID string

        Returns:
            List of time/value dicts
        """
        col_names = result.values.columns.tolist()

        # Determine which column to use
        if 'k' in col_names:
            main_col = 'k'
        elif any('STOCHk' in col for col in col_names):
            main_col = [col for col in col_names if 'STOCHk' in col][0]
        elif 'middle' in col_names:  # Bollinger Bands
            main_col = 'middle'
        elif any('BBM' in col for col in col_names):  # pandas_ta BB middle
            main_col = [col for col in col_names if 'BBM' in col][0]
        else:
            main_col = col_names[0]  # Fallback to first column

        series_data = result.values[main_col]
        logger.info(f"Using column '{main_col}' from multi-series indicator {ind_id}")

        return [
            {'time': _ts_to_local_unix(ts), 'value': float(val)}
            for ts, val in zip(self.parent.data.index, series_data.values)
            if not pd.isna(val)
        ]

    def convert_single_series_data_to_chart_format(self, result: "IndicatorResult"):
        """Convert single-series indicator result to chart format.

        Args:
            result: IndicatorResult with Series values

        Returns:
            List of time/value dicts
        """
        return [
            {'time': _ts_to_local_unix(ts), 'value': float(val)}
            for ts, val in zip(self.parent.data.index, result.values.values)
            if not pd.isna(val)
        ]
