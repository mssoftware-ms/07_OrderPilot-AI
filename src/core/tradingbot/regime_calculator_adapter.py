"""Adapter for using IndicatorCalculatorFactory in regime_engine_json.

Bridges between:
- regime_engine_json's _calculate_opt_indicators() format
- IndicatorCalculatorFactory's calculate() format

Enables code reuse of 20+ calculator classes from Task 2.1.2.
"""

import logging
import pandas as pd
from typing import Dict, Any

logger = logging.getLogger(__name__)


class RegimeCalculatorAdapter:
    """Adapter for using IndicatorCalculatorFactory in regime_engine_json.

    Key Responsibilities:
    1. Lazy-initialize IndicatorCalculatorFactory
    2. Transform params from list[dict] to Dict[str, Any]
    3. Map indicator types to calculator types
    4. Extract indicator values from calculator output

    Usage:
        >>> adapter = RegimeCalculatorAdapter()
        >>> result = adapter.calculate_indicator(
        ...     df,
        ...     indicator_type="RSI",
        ...     params=[{"name": "period", "value": 14}]
        ... )
        >>> result
        {"rsi": 45.2}
    """

    def __init__(self):
        """Initialize adapter with lazy factory creation."""
        self._factory = None
        self._initialized = False

    def _ensure_initialized(self):
        """Lazy-initialize the factory and register all calculators."""
        if self._initialized:
            return

        from src.strategies.indicator_calculators.calculator_factory import (
            IndicatorCalculatorFactory
        )
        from src.strategies.indicator_calculators.momentum import (
            RSICalculator,
            MACDCalculator,
            StochasticCalculator,
            CCICalculator,
        )
        from src.strategies.indicator_calculators.trend import (
            SMACalculator,
            EMACalculator,
            IchimokuCalculator,
            VWAPCalculator,
        )
        from src.strategies.indicator_calculators.volume import (
            OBVCalculator,
            MFICalculator,
            ADCalculator,
            CMFCalculator,
        )
        from src.strategies.indicator_calculators.volatility import (
            ATRCalculator,
            BollingerCalculator,
            KeltnerCalculator,
            BBWidthCalculator,
            ChopCalculator,
            PSARCalculator,
        )
        from src.strategies.indicator_calculators.other import (
            ADXCalculator,
            PivotsCalculator,
        )

        self._factory = IndicatorCalculatorFactory()

        # Register all calculators
        for calc_class in [
            # Momentum
            RSICalculator,
            MACDCalculator,
            StochasticCalculator,
            CCICalculator,
            # Trend
            SMACalculator,
            EMACalculator,
            IchimokuCalculator,
            VWAPCalculator,
            # Volume
            OBVCalculator,
            MFICalculator,
            ADCalculator,
            CMFCalculator,
            # Volatility
            ATRCalculator,
            BollingerCalculator,
            KeltnerCalculator,
            BBWidthCalculator,
            ChopCalculator,
            PSARCalculator,
            # Other
            ADXCalculator,
            PivotsCalculator,
        ]:
            self._factory.register(calc_class())

        self._initialized = True
        logger.debug("RegimeCalculatorAdapter initialized with 20 calculators")

    def _transform_params(self, params: list[dict]) -> Dict[str, Any]:
        """Transform params from list[dict] format to Dict[str, Any].

        Args:
            params: List of param dicts like [{"name": "period", "value": 14}]

        Returns:
            Dict like {"period": 14}

        Example:
            >>> adapter = RegimeCalculatorAdapter()
            >>> adapter._transform_params([{"name": "period", "value": 14}])
            {"period": 14}
        """
        if not params:
            return {}

        result = {}
        for param in params:
            name = param.get("name")
            value = param.get("value")
            if name is not None:
                result[name] = value

        return result

    def _map_indicator_type(self, ind_type: str) -> str:
        """Map regime_engine_json indicator type to calculator type.

        Most types are identical and pass through unchanged.
        The calculators use the same short codes (BB, STOCH) as regime_engine_json.

        Args:
            ind_type: Indicator type from regime_engine_json (e.g., "BB", "RSI")

        Returns:
            Mapped indicator type for calculator (same as input in most cases)
        """
        # All types pass through unchanged - calculators use same codes
        return ind_type

    def _extract_indicator_values(
        self,
        df: pd.DataFrame,
        ind_type: str,
        original_params: list[dict]
    ) -> Dict[str, float]:
        """Extract indicator values from calculator DataFrame output.

        The calculator returns a DataFrame with columns like:
        - indicator_value (single value indicators like RSI, EMA, etc.)
        - For multi-value indicators, column names match the calculator's output

        Args:
            df: DataFrame returned by calculator
            ind_type: Original indicator type (e.g., "RSI", "MACD", "BB")
            original_params: Original params (for special cases like ATR percentage)

        Returns:
            Dict of indicator values (e.g., {"rsi": 45.2} or {"macd": 0.5, "signal": 0.3})

        Raises:
            ValueError: If indicator produced no data
        """
        if df.empty:
            raise ValueError(f"Indicator {ind_type} produced no data")

        # Get last row values (most recent indicator value)
        last_row = df.iloc[-1]

        # Type-specific extraction logic
        if ind_type == "RSI":
            return {"rsi": float(last_row.get("indicator_value", 0))}

        elif ind_type == "MACD":
            # MACD calculator returns: indicator_value (macd line), macd_signal
            # Note: histogram not stored separately in calculator
            macd_val = float(last_row.get("indicator_value", 0))
            signal_val = float(last_row.get("macd_signal", 0))
            hist_val = macd_val - signal_val  # Calculate histogram

            return {
                "macd": macd_val,
                "signal": signal_val,
                "hist": hist_val,
            }

        elif ind_type == "ADX":
            # ADX calculator returns: adx, plus_di, minus_di columns
            plus_di = last_row.get("plus_di", 0)
            minus_di = last_row.get("minus_di", 0)
            di_diff = abs(float(plus_di) - float(minus_di)) if plus_di and minus_di else None

            return {
                "adx": float(last_row.get("indicator_value", 0)),
                "di_diff": di_diff,
            }

        elif ind_type == "ATR":
            # ATR calculator returns: indicator_value (ATR value)
            # Calculate ATR percentage using close price
            atr_val = float(last_row.get("indicator_value", 0))
            close_val = df["close"].iloc[-1] if "close" in df.columns else None
            atr_pct = float(atr_val / close_val * 100) if close_val else None

            return {
                "atr": atr_val,
                "atr_percent": atr_pct,
            }

        elif ind_type in ("BB", "BOLLINGER"):
            # Bollinger Bands calculator returns: bb_upper, bb_middle, bb_lower columns
            return {
                "upper": float(last_row.get("bb_upper", 0)) if last_row.get("bb_upper") is not None else None,
                "lower": float(last_row.get("bb_lower", 0)) if last_row.get("bb_lower") is not None else None,
                "middle": float(last_row.get("bb_middle", 0)) if last_row.get("bb_middle") is not None else None,
                "width": float(last_row.get("bb_width", 0)) if last_row.get("bb_width") is not None else None,
            }

        elif ind_type in ("STOCH", "STOCHASTIC"):
            # Stochastic calculator returns: indicator_value (%K), stoch_d (%D)
            return {
                "k": float(last_row.get("indicator_value", 0)),
                "d": float(last_row.get("stoch_d", 0)),
            }

        elif ind_type == "MFI":
            return {"mfi": float(last_row.get("indicator_value", 0))}

        elif ind_type == "CCI":
            return {"cci": float(last_row.get("indicator_value", 0))}

        elif ind_type == "CHOP":
            return {"chop": float(last_row.get("indicator_value", 0))}

        elif ind_type in ("EMA", "SMA"):
            return {"value": float(last_row.get("indicator_value", 0))}

        else:
            # Default: return indicator_value as single value
            return {"value": float(last_row.get("indicator_value", 0))}

    def calculate_indicator(
        self,
        df: pd.DataFrame,
        indicator_type: str,
        params: list[dict]
    ) -> Dict[str, float]:
        """Calculate indicator using IndicatorCalculatorFactory.

        Main adapter method that:
        1. Ensures factory is initialized
        2. Transforms params to calculator format
        3. Maps indicator type if needed
        4. Calls factory.calculate()
        5. Extracts values in regime_engine_json format

        Args:
            df: OHLCV DataFrame
            indicator_type: Indicator type (e.g., "RSI", "MACD", "BB")
            params: List of param dicts like [{"name": "period", "value": 14}]

        Returns:
            Dict of indicator values (format depends on indicator type)

        Raises:
            ValueError: If indicator type is unsupported or calculation fails

        Example:
            >>> adapter = RegimeCalculatorAdapter()
            >>> result = adapter.calculate_indicator(
            ...     df,
            ...     "RSI",
            ...     [{"name": "period", "value": 14}]
            ... )
            >>> result
            {"rsi": 45.2}
        """
        self._ensure_initialized()

        # Transform params
        params_dict = self._transform_params(params)

        # Map indicator type
        mapped_type = self._map_indicator_type(indicator_type)

        # Calculate using factory
        try:
            result_df = self._factory.calculate(mapped_type, df, params_dict)

            # Check if calculation succeeded (factory returns original df on failure)
            if result_df is df:  # Factory returned original df = no calculator found
                raise ValueError(
                    f"Unsupported indicator type in optimizer JSON: {indicator_type}"
                )

            # Extract values in regime_engine_json format
            return self._extract_indicator_values(result_df, indicator_type, params)

        except Exception as e:
            logger.error(f"Failed to calculate indicator {indicator_type}: {e}")
            raise ValueError(
                f"Indicator calculation failed for {indicator_type}: {e}"
            ) from e
