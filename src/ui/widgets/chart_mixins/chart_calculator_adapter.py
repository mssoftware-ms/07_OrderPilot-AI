"""
Chart Calculator Adapter for UI Indicator Display.

Adapter layer that connects the chart display mixins to the shared
IndicatorCalculatorFactory, eliminating code duplication.

This is the THIRD adapter after:
- RegimeCalculatorAdapter (Task 2.1.3)
- IndicatorOptimizationThread's direct usage (Task 2.1.2)

All three now share the same 20 Calculator classes for Single Source of Truth.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pandas as pd

from src.strategies.indicator_calculators.calculator_factory import IndicatorCalculatorFactory
from src.strategies.indicator_calculators.momentum import (
    RSICalculator, MACDCalculator, StochasticCalculator, CCICalculator
)
from src.strategies.indicator_calculators.trend import (
    SMACalculator, EMACalculator, IchimokuCalculator, VWAPCalculator
)
from src.strategies.indicator_calculators.volume import (
    OBVCalculator, MFICalculator, ADCalculator, CMFCalculator
)
from src.strategies.indicator_calculators.volatility import (
    ATRCalculator, BollingerCalculator, KeltnerCalculator,
    BBWidthCalculator, ChopCalculator, PSARCalculator
)
from src.strategies.indicator_calculators.other import (
    ADXCalculator, PivotsCalculator
)

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class ChartCalculatorAdapter:
    """
    Adapter for using IndicatorCalculatorFactory in chart display mixins.

    Converts JSON optimizer indicator definitions to Calculator Factory calls,
    handling the parameter mapping and result formatting needed by chart widgets.

    This eliminates the massive if-elif chains in chart_mixins.
    """

    def __init__(self):
        """Initialize adapter with registered calculators."""
        self.factory = IndicatorCalculatorFactory()
        self._register_calculators()

    def _register_calculators(self):
        """Register all available calculators."""
        for calc_class in [
            # Momentum
            RSICalculator, MACDCalculator, StochasticCalculator, CCICalculator,
            # Trend
            SMACalculator, EMACalculator, IchimokuCalculator, VWAPCalculator,
            # Volume
            OBVCalculator, MFICalculator, ADCalculator, CMFCalculator,
            # Volatility
            ATRCalculator, BollingerCalculator, KeltnerCalculator,
            BBWidthCalculator, ChopCalculator, PSARCalculator,
            # Other
            ADXCalculator, PivotsCalculator
        ]:
            self.factory.register(calc_class())

    def compute_indicator_series(
        self, df: pd.DataFrame, indicators_def: list[dict]
    ) -> dict[str, dict[str, pd.Series]]:
        """
        Compute indicator series for chart display from JSON optimizer format.

        Converts JSON indicator definitions to Calculator Factory calls and
        returns results in the format expected by chart widgets.

        Args:
            df: DataFrame with OHLCV data
            indicators_def: List of indicator definitions from optimizer JSON
                Format: [{"name": "rsi_14", "type": "RSI", "params": [...]}]

        Returns:
            Dict mapping indicator names to their series dicts:
            {
                "rsi_14": {"rsi": Series},
                "adx_14": {"adx": Series, "di_diff": Series},
                "macd": {"macd": Series, "signal": Series, "hist": Series}
            }

        Raises:
            ValueError: If indicator definition is invalid or unsupported
        """
        indicator_series: dict[str, dict[str, pd.Series]] = {}

        for ind in indicators_def:
            name = ind.get("name")
            ind_type = (ind.get("type") or "").upper()
            params = ind.get("params") or []

            if not name or not ind_type:
                raise ValueError("Indicator definition missing name or type")

            # Convert JSON params list to dict
            params_dict = self._convert_params(params)

            try:
                # Calculate using Factory
                result = self.factory.calculate(ind_type, df, params_dict)

                # Convert result to chart display format
                indicator_series[name] = self._format_result(ind_type, result)

            except ValueError as e:
                raise ValueError(f"Failed to calculate {name} ({ind_type}): {e}")

        return indicator_series

    def _convert_params(self, params: list[dict]) -> dict:
        """
        Convert JSON params list to dict for Calculator Factory.

        Args:
            params: List of param dicts [{"name": "period", "value": 14}]

        Returns:
            Dict of params {"period": 14}
        """
        params_dict = {}
        for p in params:
            param_name = p.get("name")
            param_value = p.get("value")
            if param_name:
                params_dict[param_name] = param_value
        return params_dict

    def _format_result(self, ind_type: str, result: pd.Series | pd.DataFrame) -> dict[str, pd.Series]:
        """
        Format Calculator Factory result for chart display.

        Different indicators return different structures:
        - Simple: RSI, EMA, SMA → DataFrame with 'indicator_value' column
        - Multi: MACD, BB, ADX → DataFrame with multiple columns

        Args:
            ind_type: Indicator type (e.g., "RSI", "MACD")
            result: Calculator result (Series or DataFrame)

        Returns:
            Dict mapping field names to Series (e.g., {"value": Series})
        """
        if isinstance(result, pd.Series):
            # Rare case: Simple Series
            return {"value": result}

        # Multi-column indicators: return all columns
        if isinstance(result, pd.DataFrame):
            # Map DataFrame columns to lowercase keys for consistency
            formatted = {}

            # Track which columns we've processed to avoid duplicates
            processed_cols = set()

            # Handle common patterns
            for col in result.columns:
                if col in processed_cols:
                    continue

                col_lower = col.lower()

                # Generic indicator_value column (RSI, EMA, SMA, etc.)
                if "indicator_value" in col_lower:
                    # Map based on indicator type for backward compatibility
                    if ind_type in ("RSI",):
                        formatted["rsi"] = result[col]
                    elif ind_type in ("EMA", "SMA"):
                        formatted["value"] = result[col]
                    elif ind_type in ("MFI",):
                        formatted["mfi"] = result[col]
                    elif ind_type in ("CCI",):
                        formatted["cci"] = result[col]
                    elif ind_type in ("CHOP",):
                        formatted["chop"] = result[col]
                    elif ind_type in ("ADX",):
                        formatted["adx"] = result[col]
                    elif ind_type in ("ATR",):
                        formatted["atr"] = result[col]
                    elif ind_type in ("MACD",):
                        formatted["macd"] = result[col]
                    else:
                        # Generic fallback
                        formatted["value"] = result[col]
                    processed_cols.add(col)

                # ADX special handling
                elif "adx" in col_lower and "adx" not in formatted:
                    formatted["adx"] = result[col]
                    processed_cols.add(col)
                elif "dmp" in col_lower:
                    dmp_col = col
                    dmn_col = next((c for c in result.columns if "dmn" in c.lower()), None)
                    if dmn_col:
                        formatted["di_diff"] = (result[dmp_col] - result[dmn_col]).abs()
                        processed_cols.add(dmp_col)
                        processed_cols.add(dmn_col)
                elif "dmn" in col_lower:
                    processed_cols.add(col)  # Already handled in DMP

                # MACD special handling
                elif "macd" in col_lower and "signal" not in col_lower and "hist" not in col_lower:
                    formatted["macd"] = result[col]
                    processed_cols.add(col)
                elif "signal" in col_lower:
                    formatted["signal"] = result[col]
                    processed_cols.add(col)
                elif "hist" in col_lower:
                    formatted["hist"] = result[col]
                    processed_cols.add(col)

                # Bollinger Bands special handling
                elif "upper" in col_lower:
                    formatted["upper"] = result[col]
                    processed_cols.add(col)
                elif "lower" in col_lower:
                    formatted["lower"] = result[col]
                    processed_cols.add(col)
                elif "mid" in col_lower or "middle" in col_lower:
                    formatted["middle"] = result[col]
                    processed_cols.add(col)
                elif "width" in col_lower:
                    formatted["width"] = result[col]
                    processed_cols.add(col)

                # Stochastic special handling (check for exact k/d columns)
                elif "stoch" in col_lower and ("_k" in col_lower or col_lower.endswith("_k")):
                    formatted["k"] = result[col]
                    processed_cols.add(col)
                elif "stoch" in col_lower and ("_d" in col_lower or col_lower.endswith("_d")):
                    formatted["d"] = result[col]
                    processed_cols.add(col)

                # ATR special handling (ATR calculator returns atr + atr_percent)
                elif "atr_percent" in col_lower or "atr_pct" in col_lower:
                    formatted["atr_percent"] = result[col]
                    processed_cols.add(col)
                elif "atr" in col_lower and "atr" not in formatted and "percent" not in col_lower:
                    formatted["atr"] = result[col]
                    processed_cols.add(col)

            # Ensure ATR has atr_percent if missing
            if ind_type == "ATR" and "atr_percent" not in formatted and "atr" in formatted:
                # Calculate on the fly from atr / close
                # Note: This assumes df is still in scope - NOT IDEAL
                # Better: ATRCalculator should ALWAYS return atr_percent
                logger.warning("ATR result missing atr_percent - ATRCalculator should provide it")

            return formatted

        # Fallback: empty result
        logger.warning(f"Unexpected result type for {ind_type}: {type(result)}")
        return {}
