"""Optimization phases for indicator optimization.

Handles:
- Regime detection (JSON-based)
- Regime history building (visualization)
- Parameter combination generation
- Indicator calculation (delegates to factory)

Separated from main thread to improve maintainability.
Pure logic - no PyQt6 signal emissions (handled by core thread).
"""

import logging
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .indicator_optimization_core import IndicatorOptimizationThread

logger = logging.getLogger(__name__)


class OptimizationPhaseHandler:
    """Handles optimization phases: regime detection, parameter generation, indicator calculation.

    Pure logic class with no signal emissions - delegates to parent thread for signals.
    """

    def __init__(self, thread: 'IndicatorOptimizationThread'):
        """Initialize with reference to parent thread.

        Args:
            thread: Parent IndicatorOptimizationThread (for config access)
        """
        self.thread = thread
        self._calculator_factory = None  # Lazy initialization

    def detect_regimes(self, df: pd.DataFrame) -> pd.Series:
        """Detect regime for each bar using JSON config if available.

        Args:
            df: DataFrame with OHLCV data

        Returns:
            Series with regime labels (e.g., "STRONG_UPTREND", "RANGE", etc.)

        Raises:
            RuntimeError: If regime detection fails
        """
        try:
            return self._detect_regimes_json(df, self.thread.json_config_path)
        except Exception as e:
            logger.error(f"Regime detection via JSON failed: {e}", exc_info=True)
            raise

    def _detect_regimes_json(self, df: pd.DataFrame, config_path: str) -> pd.Series:
        """Detect regimes using RegimeEngineJSON and a JSON config.

        Args:
            df: DataFrame with OHLCV data
            config_path: Path to JSON regime configuration file

        Returns:
            Series with regime labels for each bar

        Raises:
            RuntimeError: If config loading or regime detection fails
        """
        from src.core.tradingbot.regime_engine_json import RegimeEngineJSON
        from src.core.tradingbot.config.detector import RegimeDetector
        from src.core.tradingbot.config.loader import ConfigLoadError
        from src.core.indicators.types import IndicatorConfig, IndicatorType

        engine = RegimeEngineJSON()
        try:
            config = engine._load_config(config_path)
        except ConfigLoadError as e:
            raise RuntimeError(f"Failed to load regime config: {e}") from e

        detector = RegimeDetector(config.regimes)

        # Pre-calculate indicator results for full dataset
        indicator_results = {}
        for ind_def in config.indicators:
            ind_config = IndicatorConfig(
                indicator_type=IndicatorType(ind_def.type.lower()),
                params=ind_def.params,
                use_talib=False,
                cache_results=True
            )
            result = engine.indicator_engine.calculate(df, ind_config)
            indicator_results[ind_def.id] = result.values

        def _safe_value(value) -> float:
            """Convert value to float, handling NaN."""
            if pd.isna(value):
                return float("nan")
            return float(value)

        def _indicator_values_at(index: int) -> dict[str, dict[str, float]]:
            """Get indicator values at specific index."""
            values: dict[str, dict[str, float]] = {}
            for ind_id, result in indicator_results.items():
                if isinstance(result, pd.Series):
                    val = result.iloc[index] if index < len(result) else float("nan")
                    values[ind_id] = {"value": _safe_value(val)}
                elif isinstance(result, pd.DataFrame):
                    values[ind_id] = {}
                    for col in result.columns:
                        val = (
                            result[col].iloc[index]
                            if index < len(result) else float("nan")
                        )
                        values[ind_id][col] = _safe_value(val)
                    # Special handling for bandwidth->width mapping
                    if 'bandwidth' in values[ind_id]:
                        values[ind_id]['width'] = values[ind_id]['bandwidth']
                elif isinstance(result, dict):
                    values[ind_id] = result
                else:
                    values[ind_id] = {"value": float("nan")}
            return values

        # Suppress detector logging (too verbose during optimization)
        detector_logger = logging.getLogger("src.core.tradingbot.config.detector")
        prev_level = detector_logger.level
        detector_logger.setLevel(logging.WARNING)

        try:
            regimes: list[str] = []
            for i in range(len(df)):
                indicator_values = _indicator_values_at(i)
                active = detector.detect_active_regimes(indicator_values, scope="entry")
                if active:
                    regime_label = active[0].id.upper()
                else:
                    regime_label = "UNKNOWN"
                regimes.append(regime_label)
        finally:
            # Restore original logging level
            detector_logger.setLevel(prev_level)

        return pd.Series(regimes, index=df.index)

    def build_regime_history(
        self, df: pd.DataFrame, regime_labels: pd.Series
    ) -> List[Dict[str, Any]]:
        """Build regime history from regime labels for visualization.

        Tracks regime changes over time for charting.

        Args:
            df: DataFrame with timestamp index
            regime_labels: Series with regime labels for each bar

        Returns:
            List of regime change events with timestamp, regime_ids, and regimes
            Example:
            [
                {
                    'timestamp': datetime(...),
                    'regime_ids': ['regime_strong_uptrend'],
                    'regimes': [{'id': 'regime_strong_uptrend', 'name': 'STRONG_UPTREND'}]
                },
                ...
            ]
        """
        regime_history = []
        prev_regime = None

        for i in range(len(df)):
            current_regime = regime_labels.iloc[i]

            # Track regime changes
            if current_regime != prev_regime:
                timestamp = df.index[i]

                # Convert pandas Timestamp to datetime if needed
                # Floor to seconds to avoid nanosecond precision warnings
                if hasattr(timestamp, 'to_pydatetime'):
                    timestamp = timestamp.floor('s').to_pydatetime()
                elif hasattr(timestamp, 'to_datetime64'):
                    timestamp = pd.Timestamp(timestamp).floor('s').to_pydatetime()

                # Build regime change record
                regime_id = f"regime_{current_regime.lower()}"
                regime_history.append({
                    'timestamp': timestamp,
                    'regime_ids': [regime_id],
                    'regimes': [
                        {
                            'id': regime_id,
                            'name': current_regime
                        }
                    ]
                })

                prev_regime = current_regime

        return regime_history

    def generate_parameter_combinations(self) -> Dict[str, List[Dict[str, int]]]:
        """Generate all parameter combinations using Iterator Pattern.

        DELEGATES to IndicatorParameterFactory which uses itertools.product()
        for efficient cartesian products.

        Handles UI param_ranges structure:
        {
            'IndicatorName': {
                'param1': {'min': x, 'max': y, 'step': z},
                'param2': {'min': a, 'max': b, 'step': c}
            }
        }

        Returns:
            Dict mapping indicator names to lists of parameter combinations
            Example:
            {
                'RSI': [{'period': 10}, {'period': 12}, {'period': 14}],
                'MACD': [{'fast': 10, 'slow': 24, 'signal': 8}, ...]
            }

        Complexity: CC = 2 (loop + factory call)
        """
        from src.optimization.parameter_generator import IndicatorParameterFactory

        combinations = {}

        for indicator in self.thread.selected_indicators:
            # Get indicator's param ranges from UI (nested structure)
            indicator_ranges = self.thread.param_ranges.get(indicator, {})

            # Create generator for this indicator
            generator = IndicatorParameterFactory.create_generator(
                indicator,
                indicator_ranges
            )

            # Generate all combinations (convert iterator to list)
            combinations[indicator] = list(generator.generate())

        return combinations

    def calculate_indicator(
        self, df: pd.DataFrame, indicator_type: str, params: Dict[str, int]
    ) -> pd.DataFrame:
        """Calculate indicator using Factory Pattern.

        DELEGATES to IndicatorCalculatorFactory with 20 focused calculators.

        Args:
            df: DataFrame with OHLCV data
            indicator_type: Indicator type (e.g., 'RSI', 'MACD', 'SMA')
            params: Indicator parameters

        Returns:
            DataFrame with 'indicator_value' column (+ optional auxiliary columns)

        Complexity: CC = 2 (initialization check + factory call)
        """
        # Lazy initialization of calculator factory (only once per thread)
        if self._calculator_factory is None:
            self._init_calculator_factory()

        # Delegate to factory
        return self._calculator_factory.calculate(indicator_type, df, params)

    def _init_calculator_factory(self):
        """Initialize calculator factory with all calculators.

        Registers all 20 indicator calculators grouped by category:
        - Momentum: RSI, MACD, STOCH, CCI
        - Trend: SMA, EMA, ICHIMOKU, VWAP
        - Volume: OBV, MFI, AD, CMF
        - Volatility: ATR, BB, KC, BB_WIDTH, CHOP, PSAR
        - Other: ADX, PIVOTS

        Complexity: CC = 1 (simple registration loop)
        """
        from src.strategies.indicator_calculators.calculator_factory import (
            IndicatorCalculatorFactory
        )
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

        self._calculator_factory = IndicatorCalculatorFactory()

        # Register all calculators (order doesn't matter - factory uses can_calculate())
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
            self._calculator_factory.register(calc_class())

        logger.info(
            f"Initialized calculator factory with "
            f"{len(self._calculator_factory.calculators)} calculators"
        )
