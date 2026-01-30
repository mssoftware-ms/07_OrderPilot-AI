"""
Chart Data Provider for CEL Expressions.

This module provides access to chart data (OHLCV) for use in CEL expressions
through the chart.* namespace.

Available Variables:
    chart.price         - Current close price
    chart.high          - Current high price
    chart.low           - Current low price
    chart.open          - Current open price
    chart.volume        - Current volume
    chart.symbol        - Trading symbol
    chart.timeframe     - Current timeframe
    chart.candle_count  - Number of loaded candles

Author: OrderPilot-AI Development Team
Created: 2026-01-28
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Dict, Optional

import pandas as pd

if TYPE_CHECKING:
    from src.ui.widgets.chart_window import ChartWindow

logger = logging.getLogger(__name__)


class ChartDataProvider:
    """
    Provides chart data for CEL expressions via chart.* namespace.

    This provider extracts current OHLCV data from the ChartWindow's
    chart_widget and makes it available for CEL expressions.

    Examples:
        >>> provider = ChartDataProvider()
        >>> context = provider.get_context(chart_window)
        >>> print(context['chart.price'])
        95234.50

    Attributes:
        namespace: Namespace prefix for variables (default: 'chart')
    """

    def __init__(self, namespace: str = "chart"):
        """
        Initialize chart data provider.

        Args:
            namespace: Namespace prefix for variables (default: 'chart')
        """
        self.namespace = namespace

    def get_context(self, chart_window: ChartWindow) -> Dict[str, Any]:
        """
        Extract chart data from ChartWindow and return CEL context.

        Args:
            chart_window: ChartWindow instance

        Returns:
            Dictionary with chart.* variables

        Examples:
            >>> context = provider.get_context(chart_window)
            >>> print(context.keys())
            dict_keys(['chart.price', 'chart.high', 'chart.low', 'chart.open',
                       'chart.volume', 'chart.symbol', 'chart.timeframe', ...])
        """
        context = {}

        try:
            # Get chart widget
            if not hasattr(chart_window, "chart_widget") or chart_window.chart_widget is None:
                logger.warning("ChartWindow has no chart_widget")
                return self._get_empty_context()

            chart_widget = chart_window.chart_widget

            # Get DataFrame with OHLCV data
            if not hasattr(chart_widget, "data") or chart_widget.data is None:
                logger.warning("ChartWidget has no data loaded")
                return self._get_empty_context()

            data: pd.DataFrame = chart_widget.data

            if data.empty:
                logger.warning("ChartWidget data is empty")
                return self._get_empty_context()

            # Get latest candle (last row)
            latest = data.iloc[-1]

            # Extract OHLCV values
            context[f"{self.namespace}.price"] = float(latest["close"])
            context[f"{self.namespace}.open"] = float(latest["open"])
            context[f"{self.namespace}.high"] = float(latest["high"])
            context[f"{self.namespace}.low"] = float(latest["low"])
            context[f"{self.namespace}.volume"] = float(latest["volume"])

            # Symbol information
            context[f"{self.namespace}.symbol"] = chart_window.symbol

            # Timeframe (if available)
            if hasattr(chart_widget, "timeframe"):
                context[f"{self.namespace}.timeframe"] = chart_widget.timeframe
            else:
                context[f"{self.namespace}.timeframe"] = "unknown"

            # Candle count
            context[f"{self.namespace}.candle_count"] = len(data)

            # Additional useful metrics
            context[f"{self.namespace}.range"] = float(
                latest["high"] - latest["low"]
            )

            context[f"{self.namespace}.body"] = abs(
                float(latest["close"] - latest["open"])
            )

            # Candle type (bullish/bearish)
            is_bullish = latest["close"] >= latest["open"]
            context[f"{self.namespace}.is_bullish"] = is_bullish
            context[f"{self.namespace}.is_bearish"] = not is_bullish

            # Upper/lower wicks
            if is_bullish:
                context[f"{self.namespace}.upper_wick"] = float(
                    latest["high"] - latest["close"]
                )
                context[f"{self.namespace}.lower_wick"] = float(
                    latest["open"] - latest["low"]
                )
            else:
                context[f"{self.namespace}.upper_wick"] = float(
                    latest["high"] - latest["open"]
                )
                context[f"{self.namespace}.lower_wick"] = float(
                    latest["close"] - latest["low"]
                )

            # Previous candle (if available)
            if len(data) >= 2:
                prev = data.iloc[-2]
                context[f"{self.namespace}.prev_close"] = float(prev["close"])
                context[f"{self.namespace}.prev_high"] = float(prev["high"])
                context[f"{self.namespace}.prev_low"] = float(prev["low"])

                # Price change
                price_change = latest["close"] - prev["close"]
                price_change_pct = (price_change / prev["close"]) * 100

                context[f"{self.namespace}.change"] = float(price_change)
                context[f"{self.namespace}.change_pct"] = float(price_change_pct)
            else:
                context[f"{self.namespace}.prev_close"] = None
                context[f"{self.namespace}.prev_high"] = None
                context[f"{self.namespace}.prev_low"] = None
                context[f"{self.namespace}.change"] = 0.0
                context[f"{self.namespace}.change_pct"] = 0.0

            logger.debug(
                f"ChartDataProvider extracted {len(context)} variables "
                f"from {chart_window.symbol}"
            )

            return context

        except Exception as e:
            logger.error(f"Error extracting chart data: {e}", exc_info=True)
            return self._get_empty_context()

    def _get_empty_context(self) -> Dict[str, Any]:
        """
        Return empty/placeholder context when chart data is unavailable.

        Returns:
            Dictionary with None/default values
        """
        return {
            f"{self.namespace}.price": None,
            f"{self.namespace}.open": None,
            f"{self.namespace}.high": None,
            f"{self.namespace}.low": None,
            f"{self.namespace}.volume": None,
            f"{self.namespace}.symbol": None,
            f"{self.namespace}.timeframe": None,
            f"{self.namespace}.candle_count": 0,
            f"{self.namespace}.range": None,
            f"{self.namespace}.body": None,
            f"{self.namespace}.is_bullish": None,
            f"{self.namespace}.is_bearish": None,
            f"{self.namespace}.upper_wick": None,
            f"{self.namespace}.lower_wick": None,
            f"{self.namespace}.prev_close": None,
            f"{self.namespace}.prev_high": None,
            f"{self.namespace}.prev_low": None,
            f"{self.namespace}.change": None,
            f"{self.namespace}.change_pct": None,
        }

    def get_variable_names(self) -> list[str]:
        """
        Get list of all available variable names.

        Returns:
            List of fully qualified variable names

        Examples:
            >>> provider = ChartDataProvider()
            >>> print(provider.get_variable_names())
            ['chart.price', 'chart.high', 'chart.low', ...]
        """
        empty = self._get_empty_context()
        return sorted(empty.keys())

    def get_available_variables(self) -> Dict[str, Dict[str, str]]:
        """Alias for get_variable_info to match interface expectation."""
        return self.get_variable_info()

    def get_variable_info(self) -> Dict[str, Dict[str, str]]:
        """
        Get metadata for all variables.

        Returns:
            Dictionary of variable_name -> {description, type, unit}

        Examples:
            >>> provider = ChartDataProvider()
            >>> info = provider.get_variable_info()
            >>> print(info['chart.price'])
            {'description': 'Current close price', 'type': 'float', 'unit': 'USD'}
        """
        return {
            f"{self.namespace}.price": {
                "description": "Current close price",
                "type": "float",
                "unit": "USD",
            },
            f"{self.namespace}.open": {
                "description": "Current open price",
                "type": "float",
                "unit": "USD",
            },
            f"{self.namespace}.high": {
                "description": "Current high price",
                "type": "float",
                "unit": "USD",
            },
            f"{self.namespace}.low": {
                "description": "Current low price",
                "type": "float",
                "unit": "USD",
            },
            f"{self.namespace}.volume": {
                "description": "Current volume",
                "type": "float",
                "unit": "BTC",
            },
            f"{self.namespace}.symbol": {
                "description": "Trading symbol",
                "type": "string",
                "unit": None,
            },
            f"{self.namespace}.timeframe": {
                "description": "Current timeframe",
                "type": "string",
                "unit": None,
            },
            f"{self.namespace}.candle_count": {
                "description": "Number of loaded candles",
                "type": "int",
                "unit": None,
            },
            f"{self.namespace}.range": {
                "description": "High-Low range",
                "type": "float",
                "unit": "USD",
            },
            f"{self.namespace}.body": {
                "description": "Absolute candle body size",
                "type": "float",
                "unit": "USD",
            },
            f"{self.namespace}.is_bullish": {
                "description": "Is current candle bullish?",
                "type": "bool",
                "unit": None,
            },
            f"{self.namespace}.is_bearish": {
                "description": "Is current candle bearish?",
                "type": "bool",
                "unit": None,
            },
            f"{self.namespace}.upper_wick": {
                "description": "Upper wick size",
                "type": "float",
                "unit": "USD",
            },
            f"{self.namespace}.lower_wick": {
                "description": "Lower wick size",
                "type": "float",
                "unit": "USD",
            },
            f"{self.namespace}.prev_close": {
                "description": "Previous candle close",
                "type": "float",
                "unit": "USD",
            },
            f"{self.namespace}.prev_high": {
                "description": "Previous candle high",
                "type": "float",
                "unit": "USD",
            },
            f"{self.namespace}.prev_low": {
                "description": "Previous candle low",
                "type": "float",
                "unit": "USD",
            },
            f"{self.namespace}.change": {
                "description": "Price change from previous candle",
                "type": "float",
                "unit": "USD",
            },
            f"{self.namespace}.change_pct": {
                "description": "Price change percentage",
                "type": "float",
                "unit": "%",
            },
        }
