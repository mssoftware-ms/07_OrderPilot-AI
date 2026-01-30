"""Indicator Optimization Thread for background processing.

Runs indicator parameter optimization in the background with:
- Entry/Exit mode selection
- Long/Short side selection
- Chart data support
- Regime-based scoring (0-100)

REFACTORED: _generate_signals() now uses Strategy Pattern with 20 focused generators.
CC reduced from 157 → 3 (98% improvement).
"""

import logging
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any, Optional
from PyQt6.QtCore import QThread, pyqtSignal

# Import signal generator registry (replaces 322-line monster function)
from src.strategies.signal_generators import SignalGeneratorRegistry

logger = logging.getLogger(__name__)


class IndicatorOptimizationThread(QThread):
    """Background thread for indicator parameter optimization.

    Tests individual indicators with different parameter sets across
    different market regimes to find optimal configurations.

    Signals:
        finished: Emitted when optimization completes with results list
        progress: Emitted during processing (percentage, status message)
        error: Emitted on errors (error message)
        regime_history_ready: Emitted when regime detection is complete with regime boundaries
    """

    finished = pyqtSignal(list)  # List[Dict] of optimization results
    progress = pyqtSignal(int, str)  # (percentage: int, message: str)
    error = pyqtSignal(str)  # error message
    regime_history_ready = pyqtSignal(list)  # List[Dict] of regime changes

    def __init__(
        self,
        selected_indicators: List[str],
        param_ranges: Dict[str, Dict[str, int]],
        json_config_path: Optional[str] = None,  # Regime config for JSON-based regime detection
        symbol: str = "",
        start_date: datetime = None,
        end_date: datetime = None,
        initial_capital: float = 10000.0,
        test_type: str = "entry",  # "entry" or "exit"
        trade_side: str = "long",  # "long" or "short"
        chart_data: Optional[pd.DataFrame] = None,
        data_timeframe: Optional[str] = None,
        parent=None
    ):
        """Initialize optimization thread.

        Args:
            selected_indicators: List of indicator types to optimize (e.g. ['RSI', 'MACD', 'ADX'])
            param_ranges: Parameter ranges for each indicator
            json_config_path: Path to JSON regime config (required for regime labels)
            symbol: Trading symbol
            start_date: Backtest start date
            end_date: Backtest end date
            initial_capital: Starting capital
            test_type: "entry" or "exit" - what phase to optimize
            trade_side: "long" or "short" - which trade direction
            chart_data: Pre-loaded chart data (optional)
            data_timeframe: Timeframe of chart data (e.g. "15m")
            parent: Parent QObject
        """
        super().__init__(parent)
        self.selected_indicators = selected_indicators
        self.param_ranges = param_ranges
        self.json_config_path = json_config_path
        self.symbol = symbol
        self.start_date = start_date
        self.end_date = end_date
        self.initial_capital = initial_capital
        self.test_type = test_type
        self.trade_side = trade_side
        self.chart_data = chart_data
        self.data_timeframe = data_timeframe

        self.results: List[Dict[str, Any]] = []
        self._stop_requested = False

        # Initialize signal generator registry (Strategy Pattern)
        # Replaces 322-line _generate_signals() monster function (CC=157)
        self._signal_registry = SignalGeneratorRegistry()

    def stop(self):
        """Request thread to stop."""
        self._stop_requested = True
        logger.info("Optimization stop requested")

    def run(self):
        """Main optimization loop - runs in background thread."""
        try:
            logger.info(
                f"Starting optimization: {self.test_type} {self.trade_side} for "
                f"{len(self.selected_indicators)} indicators"
            )

            # Import required modules
            from src.backtesting.engine import BacktestEngine
            engine = BacktestEngine()

            # Load or use chart data
            if self.chart_data is not None:
                df = self.chart_data.copy()
                logger.info(f"Using chart data: {len(df)} candles, timeframe={self.data_timeframe}")
            else:
                df = engine.data_loader.load_data(self.symbol, self.start_date, self.end_date)
                logger.info(f"Loaded {len(df)} candles from database")

            if df.empty:
                self.error.emit("No data available for optimization")
                return

            # Detect regimes across the data (JSON-based)
            self.progress.emit(5, "Detecting market regimes...")
            if not self.json_config_path:
                raise RuntimeError(
                    "No regime config provided. Load a JSON regime config before optimization."
                )
            regime_labels = self._detect_regimes(df)

            # Build regime history (track regime changes for visualization)
            regime_history = self._build_regime_history(df, regime_labels)
            logger.info(f"Detected {len(regime_history)} regime changes")

            # Emit regime history for visualization
            self.regime_history_ready.emit(regime_history)

            # Get unique regimes
            unique_regimes = sorted(set(regime_labels))
            logger.info(f"Found {len(unique_regimes)} unique regimes: {unique_regimes}")

            # Generate parameter combinations
            param_combinations = self._generate_parameter_combinations()

            # Calculate REAL total: sum of all parameter lists across all indicators × regimes
            total_param_count = sum(len(params) for params in param_combinations.values())
            total_combinations = total_param_count * len(unique_regimes)

            logger.info(
                f"Testing {total_param_count} parameter combinations "
                f"({len(param_combinations)} indicators) across {len(unique_regimes)} regimes = "
                f"{total_combinations} total tests"
            )

            all_results = []
            completed = 0

            # Test each parameter combination in each regime
            for indicator_type in self.selected_indicators:
                if self._stop_requested:
                    return

                for params in param_combinations.get(indicator_type, []):
                    if self._stop_requested:
                        return

                    # Calculate indicator
                    indicator_df = self._calculate_indicator(df, indicator_type, params)

                    # Test in each regime
                    for regime in unique_regimes:
                        if self._stop_requested:
                            return

                        completed += 1
                        progress_pct = int(completed / total_combinations * 100)

                        self.progress.emit(
                            progress_pct,
                            f"Testing {indicator_type}{params} in {regime} ({completed}/{total_combinations})"
                        )

                        # Filter data for this regime (align indices after dropna)
                        aligned_mask = regime_labels.loc[indicator_df.index] == regime
                        regime_df = indicator_df[aligned_mask]

                        if len(regime_df) < 10:  # Skip if too few bars
                            continue

                        # Score this indicator for this regime
                        score_data = self._score_indicator(
                            regime_df,
                            indicator_type,
                            params,
                            regime
                        )

                        if score_data:
                            all_results.append(score_data)

            # Sort by score (descending)
            all_results.sort(key=lambda x: x['score'], reverse=True)

            self.results = all_results
            logger.info(f"Optimization completed: {len(self.results)} results")
            self.finished.emit(self.results)

        except Exception as e:
            error_msg = f"Optimization error: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.error.emit(error_msg)

    def _detect_regimes(self, df: pd.DataFrame) -> pd.Series:
        """Detect regime for each bar using JSON config if available.

        Returns:
            Series with regime labels (e.g., "STRONG_UPTREND", "RANGE", etc.)
        """
        try:
            return self._detect_regimes_json(df, self.json_config_path)
        except Exception as e:
            logger.error(f"Regime detection via JSON failed: {e}", exc_info=True)
            raise

    def _detect_regimes_json(self, df: pd.DataFrame, config_path: str) -> pd.Series:
        """Detect regimes using RegimeEngineJSON and a JSON config."""
        import pandas as pd
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
            if pd.isna(value):
                return float("nan")
            return float(value)

        def _indicator_values_at(index: int) -> dict[str, dict[str, float]]:
            values: dict[str, dict[str, float]] = {}
            for ind_id, result in indicator_results.items():
                if isinstance(result, pd.Series):
                    val = result.iloc[index] if index < len(result) else float("nan")
                    values[ind_id] = {"value": _safe_value(val)}
                elif isinstance(result, pd.DataFrame):
                    values[ind_id] = {}
                    for col in result.columns:
                        val = result[col].iloc[index] if index < len(result) else float("nan")
                        values[ind_id][col] = _safe_value(val)
                    if 'bandwidth' in values[ind_id]:
                        values[ind_id]['width'] = values[ind_id]['bandwidth']
                elif isinstance(result, dict):
                    values[ind_id] = result
                else:
                    values[ind_id] = {"value": float("nan")}
            return values

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
            detector_logger.setLevel(prev_level)

        return pd.Series(regimes, index=df.index)


    def _build_regime_history(self, df: pd.DataFrame, regime_labels: pd.Series) -> List[Dict[str, Any]]:
        """Build regime history from regime labels for visualization.

        Args:
            df: DataFrame with timestamp index
            regime_labels: Series with regime labels for each bar

        Returns:
            List of regime change events with timestamp, regime_ids, and regimes
        """
        regime_history = []
        prev_regime = None

        for i in range(len(df)):
            current_regime = regime_labels.iloc[i]

            # Track regime changes
            if current_regime != prev_regime:
                timestamp = df.index[i]

                # Convert pandas Timestamp to datetime if needed (floor to seconds to avoid nanosecond warning)
                if hasattr(timestamp, 'to_pydatetime'):
                    timestamp = timestamp.floor('s').to_pydatetime()  # Round to seconds
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

    def _generate_parameter_combinations(self) -> Dict[str, List[Dict[str, int]]]:
        """Generate all parameter combinations using Iterator Pattern.

        REFACTORED from 153 lines of nested loops (CC=47) to clean delegation.
        Now uses IndicatorParameterFactory with itertools.product() for cartesian products.

        Handles UI param_ranges structure:
        {
            'IndicatorName': {
                'param1': {'min': x, 'max': y, 'step': z},
                'param2': {'min': a, 'max': b, 'step': c}
            }
        }

        Returns:
            Dict mapping indicator names to lists of parameter combinations

        Complexity: CC = 2 (loop + factory call)
        Original: CC = 47, 153 lines
        Improvement: 95.7% complexity reduction
        """
        from src.optimization.parameter_generator import IndicatorParameterFactory

        combinations = {}

        for indicator in self.selected_indicators:
            # Get indicator's param ranges from UI (nested structure)
            indicator_ranges = self.param_ranges.get(indicator, {})

            # Create generator for this indicator
            generator = IndicatorParameterFactory.create_generator(
                indicator,
                indicator_ranges
            )

            # Generate all combinations (convert iterator to list)
            combinations[indicator] = list(generator.generate())

        return combinations

    def _calculate_indicator(
        self, df: pd.DataFrame, indicator_type: str, params: Dict[str, int]
    ) -> pd.DataFrame:
        """Calculate indicator using Factory Pattern.

        REFACTORED from 197-line if-elif chain (CC=86) to clean delegation.
        Now uses IndicatorCalculatorFactory with 20 focused calculators (CC < 5 each).

        Args:
            df: DataFrame with OHLCV data
            indicator_type: Indicator type (e.g., 'RSI', 'MACD', 'SMA')
            params: Indicator parameters

        Returns:
            DataFrame with 'indicator_value' column (+ optional auxiliary columns)

        Complexity: CC = 2 (initialization check + factory call)
        Original: CC = 86, 197 lines
        Improvement: 97.7% complexity reduction
        """
        # Lazy initialization of calculator factory (only once per thread)
        if not hasattr(self, '_calculator_factory'):
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

        logger.info(f"Initialized calculator factory with {len(self._calculator_factory.calculators)} calculators")

    def _score_indicator(
        self, df: pd.DataFrame, indicator_type: str, params: Dict[str, int], regime: str
    ) -> Optional[Dict[str, Any]]:
        """Score indicator performance for given regime.

        Scoring based on:
        - Entry Long: Low RSI values (<30), bullish signals
        - Entry Short: High RSI values (>70), bearish signals
        - Exit Long: High RSI values (>70), overbought
        - Exit Short: Low RSI values (<30), oversold
        - Proximity to extremes: Closer to lows (long) or highs (short) = higher score

        Returns:
            Dict with score (0-100), win_rate, profit_factor, total_trades
        """
        if 'indicator_value' not in df.columns or df['indicator_value'].isna().all():
            return None

        signals = self._generate_signals(df, indicator_type, self.test_type, self.trade_side)

        if signals.sum() == 0:
            return None

        # Calculate performance metrics
        metrics = self._calculate_metrics(df, signals)

        if metrics['total_trades'] == 0:
            return None

        # Calculate proximity to extremes (for entry signals)
        proximity_score = 0.0
        if self.test_type == 'entry':
            proximity_score = self._calculate_proximity_score(df, signals, self.trade_side)
            metrics['proximity_score'] = proximity_score

        # Calculate composite score (0-100)
        score = self._calculate_composite_score(metrics)

        return {
            'indicator': indicator_type,
            'params': params,
            'regime': regime,
            'score': int(score),  # No decimal places
            'win_rate': metrics['win_rate'],
            'profit_factor': metrics['profit_factor'],
            'total_trades': metrics['total_trades'],
            'proximity_score': proximity_score,
            'test_type': self.test_type,
            'trade_side': self.trade_side
        }

    def _generate_signals(
        self, df: pd.DataFrame, indicator_type: str, test_type: str, trade_side: str
    ) -> pd.Series:
        """Generate trading signals using Strategy Pattern.

        REFACTORED from 322-line monster function (CC=157) to clean delegation.
        Now uses SignalGeneratorRegistry with 20 focused generators (CC < 5 each).

        Args:
            df: DataFrame with price and indicator data
            indicator_type: Indicator type (e.g., 'RSI', 'MACD', 'SMA')
            test_type: 'entry' or 'exit'
            trade_side: 'long' or 'short'

        Returns:
            Boolean Series with signals (True = signal fired)

        Complexity: CC = 1 (single delegation call)
        Original: CC = 157, 322 lines
        Improvement: 98% complexity reduction
        """
        return self._signal_registry.generate_signals(
            df, indicator_type, test_type, trade_side
        )

    def _calculate_metrics(self, df: pd.DataFrame, signals: pd.Series) -> Dict[str, float]:
        """Calculate performance metrics for signals."""
        import numpy as np

        # Simple forward returns calculation
        forward_returns = df['close'].pct_change().shift(-1)  # Next bar return

        # Get returns where signals fired
        signal_returns = forward_returns[signals]

        if len(signal_returns) == 0:
            return {
                'total_trades': 0,
                'win_rate': 0.0,
                'profit_factor': 0.0,
                'avg_return': 0.0,
                'sharpe_ratio': 0.0
            }

        # Calculate metrics
        wins = signal_returns[signal_returns > 0]
        losses = signal_returns[signal_returns <= 0]

        win_rate = len(wins) / len(signal_returns) if len(signal_returns) > 0 else 0.0

        total_wins = wins.sum() if len(wins) > 0 else 0.0
        total_losses = abs(losses.sum()) if len(losses) > 0 else 0.0
        profit_factor = total_wins / total_losses if total_losses > 0 else 0.0

        avg_return = signal_returns.mean()
        sharpe_ratio = signal_returns.mean() / signal_returns.std() if signal_returns.std() > 0 else 0.0

        return {
            'total_trades': len(signal_returns),
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'avg_return': avg_return,
            'sharpe_ratio': sharpe_ratio
        }

    def _calculate_proximity_score(
        self, df: pd.DataFrame, signals: pd.Series, trade_side: str
    ) -> float:
        """Calculate proximity score based on distance to price extremes.

        For LONG signals: Higher score if signal is closer to local lows
        For SHORT signals: Higher score if signal is closer to local highs

        Returns:
            Score 0-1 (higher = better proximity)
        """
        if signals.sum() == 0:
            return 0.0

        # Get signal indices
        signal_indices = df[signals].index

        proximity_scores = []

        for idx in signal_indices:
            try:
                # Get position in dataframe
                pos = df.index.get_loc(idx)

                # Define lookback/forward window (e.g., 20 bars each side)
                window = 20
                start = max(0, pos - window)
                end = min(len(df), pos + window + 1)

                window_df = df.iloc[start:end]

                if trade_side == 'long':
                    # For LONG: Find nearest low
                    low_price = window_df['low'].min()
                    signal_price = df.loc[idx, 'close']

                    # Calculate distance in bars to the low
                    low_idx = window_df['low'].idxmin()
                    low_pos = df.index.get_loc(low_idx)
                    distance_bars = abs(pos - low_pos)

                    # Score: Closer = better (inverse relationship)
                    # 0 bars distance = 1.0 score, 20 bars = 0.0 score
                    proximity = 1.0 - (distance_bars / window)
                    proximity = max(0.0, proximity)

                else:  # short
                    # For SHORT: Find nearest high
                    high_price = window_df['high'].max()
                    signal_price = df.loc[idx, 'close']

                    # Calculate distance in bars to the high
                    high_idx = window_df['high'].idxmax()
                    high_pos = df.index.get_loc(high_idx)
                    distance_bars = abs(pos - high_pos)

                    # Score: Closer = better (inverse relationship)
                    proximity = 1.0 - (distance_bars / window)
                    proximity = max(0.0, proximity)

                proximity_scores.append(proximity)

            except Exception as e:
                logger.warning(f"Failed to calculate proximity for signal at {idx}: {e}")
                continue

        if not proximity_scores:
            return 0.0

        # Return average proximity score
        return sum(proximity_scores) / len(proximity_scores)

    def _calculate_composite_score(self, metrics: Dict[str, float]) -> float:
        """Calculate composite score (0-100) from metrics.

        Weighting:
        - Win Rate: 25%
        - Profit Factor: 25%
        - Sharpe Ratio: 20%
        - Total Trades: 10% (more trades = better)
        - Proximity to Extremes: 20% (closer to lows/highs = better)
        """
        # Normalize metrics to 0-1
        win_rate_score = min(metrics['win_rate'], 1.0)  # Already 0-1

        # Profit factor: 2.0 = 100%, capped at 5.0
        profit_factor_score = min(metrics['profit_factor'] / 5.0, 1.0)

        # Sharpe: 2.0 = 100%, capped at 3.0
        sharpe_score = min(max(metrics['sharpe_ratio'], 0) / 3.0, 1.0)

        # Trades: 50 trades = 100%, capped at 100
        trades_score = min(metrics['total_trades'] / 50.0, 1.0)

        # Proximity score (0-1, already normalized)
        proximity_score = metrics.get('proximity_score', 0.0)

        # Weighted composite
        composite = (
            win_rate_score * 0.25 +
            profit_factor_score * 0.25 +
            sharpe_score * 0.20 +
            trades_score * 0.10 +
            proximity_score * 0.20
        )

        return composite * 100  # Convert to 0-100 scale
