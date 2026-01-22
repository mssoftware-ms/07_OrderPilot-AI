"""Indicator Optimization Thread for background processing.

Runs indicator parameter optimization in the background with:
- Entry/Exit mode selection
- Long/Short side selection
- Chart data support
- Regime-based scoring (0-100)
"""

import logging
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any, Optional
from PyQt6.QtCore import QThread, pyqtSignal

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
        """Generate all parameter combinations for selected indicators.

        Handles UI param_ranges structure:
        {
            'IndicatorName': {
                'param1': {'min': x, 'max': y, 'step': z},
                'param2': {'min': a, 'max': b, 'step': c}
            }
        }
        """
        combinations = {}

        for indicator in self.selected_indicators:
            param_list = []

            # Get indicator's param ranges from UI (nested structure)
            indicator_ranges = self.param_ranges.get(indicator, {})

            if indicator == 'RSI':
                period_range = indicator_ranges.get('period', {'min': 10, 'max': 20, 'step': 2})
                for period in range(period_range['min'], period_range['max'] + 1, period_range['step']):
                    param_list.append({'period': period})

            elif indicator == 'MACD':
                fast_range = indicator_ranges.get('fast', {'min': 8, 'max': 16, 'step': 2})
                slow_range = indicator_ranges.get('slow', {'min': 26, 'max': 26, 'step': 1})
                signal_range = indicator_ranges.get('signal', {'min': 9, 'max': 9, 'step': 1})
                for fast in range(fast_range['min'], fast_range['max'] + 1, fast_range['step']):
                    for slow in range(slow_range['min'], slow_range['max'] + 1, slow_range['step']):
                        for signal in range(signal_range['min'], signal_range['max'] + 1, signal_range['step']):
                            param_list.append({'fast': fast, 'slow': slow, 'signal': signal})

            elif indicator == 'ADX':
                period_range = indicator_ranges.get('period', {'min': 10, 'max': 20, 'step': 2})
                for period in range(period_range['min'], period_range['max'] + 1, period_range['step']):
                    param_list.append({'period': period})

            elif indicator == 'SMA':
                period_range = indicator_ranges.get('period', {'min': 10, 'max': 50, 'step': 10})
                for period in range(period_range['min'], period_range['max'] + 1, period_range['step']):
                    param_list.append({'period': period})

            elif indicator == 'EMA':
                period_range = indicator_ranges.get('period', {'min': 10, 'max': 50, 'step': 10})
                for period in range(period_range['min'], period_range['max'] + 1, period_range['step']):
                    param_list.append({'period': period})

            elif indicator == 'BB':
                period_range = indicator_ranges.get('period', {'min': 14, 'max': 28, 'step': 7})
                std_range = indicator_ranges.get('std', {'min': 2.0, 'max': 2.5, 'step': 0.5})
                for period in range(period_range['min'], period_range['max'] + 1, period_range['step']):
                    # Handle float step for std
                    std_val = std_range['min']
                    while std_val <= std_range['max']:
                        param_list.append({'period': period, 'std': round(std_val, 2)})
                        std_val += std_range['step']

            elif indicator == 'ATR':
                period_range = indicator_ranges.get('period', {'min': 10, 'max': 20, 'step': 2})
                for period in range(period_range['min'], period_range['max'] + 1, period_range['step']):
                    param_list.append({'period': period})

            # NEW INDICATORS (13)

            elif indicator == 'ICHIMOKU':
                tenkan_range = indicator_ranges.get('tenkan', {'min': 9, 'max': 27, 'step': 9})
                kijun_range = indicator_ranges.get('kijun', {'min': 26, 'max': 52, 'step': 26})
                for tenkan in range(tenkan_range['min'], tenkan_range['max'] + 1, tenkan_range['step']):
                    for kijun in range(kijun_range['min'], kijun_range['max'] + 1, kijun_range['step']):
                        param_list.append({
                            'tenkan': tenkan,
                            'kijun': kijun,
                            'senkou': kijun * 2
                        })

            elif indicator == 'PSAR':
                accel_range = indicator_ranges.get('accel', {'min': 0.01, 'max': 0.02, 'step': 0.005})
                max_accel_range = indicator_ranges.get('max_accel', {'min': 0.1, 'max': 0.2, 'step': 0.05})
                # Handle float steps
                accel = accel_range['min']
                while accel <= accel_range['max']:
                    max_accel = max_accel_range['min']
                    while max_accel <= max_accel_range['max']:
                        param_list.append({'accel': round(accel, 3), 'max_accel': round(max_accel, 2)})
                        max_accel += max_accel_range['step']
                    accel += accel_range['step']

            elif indicator == 'KC':
                period_range = indicator_ranges.get('period', {'min': 14, 'max': 28, 'step': 7})
                mult_range = indicator_ranges.get('mult', {'min': 2.0, 'max': 2.0, 'step': 0.5})
                for period in range(period_range['min'], period_range['max'] + 1, period_range['step']):
                    mult = mult_range['min']
                    while mult <= mult_range['max']:
                        param_list.append({'period': period, 'mult': round(mult, 1)})
                        mult += mult_range['step']

            elif indicator == 'VWAP':
                # VWAP typically doesn't have parameters (daily reset)
                param_list.append({'anchor': 'D'})

            elif indicator == 'PIVOTS':
                # Pivot Points: Standard, Fibonacci, Camarilla
                for pivot_type in ['standard', 'fibonacci', 'camarilla']:
                    param_list.append({'type': pivot_type})

            elif indicator == 'CHOP':
                period_range = indicator_ranges.get('period', {'min': 10, 'max': 20, 'step': 2})
                for period in range(period_range['min'], period_range['max'] + 1, period_range['step']):
                    param_list.append({'period': period})

            elif indicator == 'STOCH':
                k_range = indicator_ranges.get('k_period', {'min': 10, 'max': 20, 'step': 5})
                d_range = indicator_ranges.get('d_period', {'min': 3, 'max': 7, 'step': 2})
                for k in range(k_range['min'], k_range['max'] + 1, k_range['step']):
                    for d in range(d_range['min'], d_range['max'] + 1, d_range['step']):
                        param_list.append({'k_period': k, 'd_period': d})

            elif indicator == 'CCI':
                period_range = indicator_ranges.get('period', {'min': 14, 'max': 28, 'step': 7})
                for period in range(period_range['min'], period_range['max'] + 1, period_range['step']):
                    param_list.append({'period': period})

            elif indicator == 'BB_WIDTH':
                period_range = indicator_ranges.get('period', {'min': 14, 'max': 28, 'step': 7})
                std_range = indicator_ranges.get('std', {'min': 2.0, 'max': 2.5, 'step': 0.5})
                for period in range(period_range['min'], period_range['max'] + 1, period_range['step']):
                    std = std_range['min']
                    while std <= std_range['max']:
                        param_list.append({'period': period, 'std': round(std, 1)})
                        std += std_range['step']

            elif indicator == 'OBV':
                # OBV doesn't have parameters
                param_list.append({})

            elif indicator == 'MFI':
                period_range = indicator_ranges.get('period', {'min': 10, 'max': 20, 'step': 2})
                for period in range(period_range['min'], period_range['max'] + 1, period_range['step']):
                    param_list.append({'period': period})

            elif indicator == 'AD':
                # A/D Line doesn't have parameters
                param_list.append({})

            elif indicator == 'CMF':
                period_range = indicator_ranges.get('period', {'min': 14, 'max': 28, 'step': 7})
                for period in range(period_range['min'], period_range['max'] + 1, period_range['step']):
                    param_list.append({'period': period})

            combinations[indicator] = param_list

        return combinations

    def _calculate_indicator(
        self, df: pd.DataFrame, indicator_type: str, params: Dict[str, int]
    ) -> pd.DataFrame:
        """Calculate indicator with given parameters."""
        import pandas_ta as ta

        result_df = df.copy()

        if indicator_type == 'RSI':
            period = params.get('period', 14)
            rsi = ta.rsi(df['close'], length=period)
            result_df['indicator_value'] = rsi if rsi is not None else 50.0

        elif indicator_type == 'MACD':
            fast = params.get('fast', 12)
            slow = params.get('slow', 26)
            signal = params.get('signal', 9)
            macd = ta.macd(df['close'], fast=fast, slow=slow, signal=signal)
            if macd is not None and not macd.empty:
                # MACD returns 3 columns: MACD line, signal, histogram
                # Find MACD line column (excludes 'signal' and 'histogram' in name)
                macd_cols = [c for c in macd.columns if 'MACD' in c and 'signal' not in c.lower() and 'histogram' not in c.lower()]
                result_df['indicator_value'] = macd[macd_cols[0]] if macd_cols else 0
                # Store signal line if available
                signal_cols = [c for c in macd.columns if 'signal' in c.lower()]
                if signal_cols:
                    result_df['macd_signal'] = macd[signal_cols[0]]
            else:
                result_df['indicator_value'] = 0

        elif indicator_type == 'ADX':
            period = params.get('period', 14)
            adx = ta.adx(df['high'], df['low'], df['close'], length=period)
            if adx is not None and not adx.empty:
                # Find ADX column (excludes DMP/DMN)
                adx_cols = [c for c in adx.columns if 'ADX' in c and 'DMP' not in c and 'DMN' not in c]
                result_df['indicator_value'] = adx[adx_cols[0]] if adx_cols else 25.0
            else:
                result_df['indicator_value'] = 25.0

        elif indicator_type == 'SMA':
            period = params.get('period', 20)
            sma = ta.sma(df['close'], length=period)
            result_df['indicator_value'] = sma if sma is not None else df['close']

        elif indicator_type == 'EMA':
            period = params.get('period', 20)
            ema = ta.ema(df['close'], length=period)
            result_df['indicator_value'] = ema if ema is not None else df['close']

        elif indicator_type == 'BB':
            period = params.get('period', 20)
            std = params.get('std', 2.0)
            bbands = ta.bbands(df['close'], length=period, std=std)
            if bbands is not None and not bbands.empty and len(bbands.columns) >= 3:
                # Bollinger Bands returns 3 columns: Lower, Middle, Upper (order may vary)
                # Use positional access: typically [0]=Lower, [1]=Middle, [2]=Upper
                result_df['bb_lower'] = bbands.iloc[:, 0]
                result_df['bb_middle'] = bbands.iloc[:, 1]
                result_df['bb_upper'] = bbands.iloc[:, 2]
                result_df['indicator_value'] = bbands.iloc[:, 1]  # Middle band
            else:
                result_df['bb_lower'] = df['close'] * 0.98
                result_df['bb_middle'] = df['close']
                result_df['bb_upper'] = df['close'] * 1.02
                result_df['indicator_value'] = df['close']

        elif indicator_type == 'ATR':
            period = params.get('period', 14)
            atr = ta.atr(df['high'], df['low'], df['close'], length=period)
            result_df['indicator_value'] = atr if atr is not None else df['close'] * 0.02

        # NEW INDICATORS

        elif indicator_type == 'ICHIMOKU':
            tenkan = params.get('tenkan', 9)
            kijun = params.get('kijun', 26)
            senkou = params.get('senkou', 52)
            ichimoku_result = ta.ichimoku(df['high'], df['low'], df['close'],
                                          tenkan=tenkan, kijun=kijun, senkou=senkou)
            if ichimoku_result is not None and len(ichimoku_result) > 0:
                ichimoku = ichimoku_result[0]  # First dataframe
                if ichimoku is not None and not ichimoku.empty:
                    # Find Senkou Span columns (ISA, ISB)
                    isa_cols = [c for c in ichimoku.columns if 'ISA' in c or 'SPAN_A' in c.upper()]
                    isb_cols = [c for c in ichimoku.columns if 'ISB' in c or 'SPAN_B' in c.upper()]

                    if isa_cols and isb_cols:
                        result_df['indicator_value'] = ichimoku[isa_cols[0]]
                        result_df['cloud_top'] = ichimoku[isa_cols[0]].combine(ichimoku[isb_cols[0]], max)
                        result_df['cloud_bottom'] = ichimoku[isa_cols[0]].combine(ichimoku[isb_cols[0]], min)
                    else:
                        result_df['indicator_value'] = df['close']
                else:
                    result_df['indicator_value'] = df['close']
            else:
                result_df['indicator_value'] = df['close']

        elif indicator_type == 'PSAR':
            accel = params.get('accel', 0.02)
            max_accel = params.get('max_accel', 0.2)
            psar = ta.psar(df['high'], df['low'], af=accel, max_af=max_accel)
            if psar is not None and not psar.empty:
                # PSAR returns multiple columns (long/short), use first numeric column
                numeric_cols = [c for c in psar.columns if psar[c].dtype in ['float64', 'float32']]
                result_df['indicator_value'] = psar[numeric_cols[0]] if numeric_cols else df['close']
            else:
                result_df['indicator_value'] = df['close']

        elif indicator_type == 'KC':
            period = params.get('period', 20)
            mult = params.get('mult', 2.0)
            kc = ta.kc(df['high'], df['low'], df['close'], length=period, scalar=mult)
            if kc is not None and not kc.empty and len(kc.columns) >= 3:
                # KC returns lower, basis, upper (positional: 0, 1, 2)
                result_df['kc_lower'] = kc.iloc[:, 0]
                result_df['kc_middle'] = kc.iloc[:, 1]
                result_df['kc_upper'] = kc.iloc[:, 2]
                result_df['indicator_value'] = kc.iloc[:, 1]  # Middle line
            else:
                result_df['indicator_value'] = df['close']

        elif indicator_type == 'VWAP':
            vwap = ta.vwap(df['high'], df['low'], df['close'], df['volume'])
            result_df['indicator_value'] = vwap if vwap is not None else df['close']

        elif indicator_type == 'PIVOTS':
            pivot_type = params.get('type', 'standard')
            # Simplified pivot calculation (using previous day H/L/C)
            if pivot_type == 'standard':
                pivot = (df['high'].shift(1) + df['low'].shift(1) + df['close'].shift(1)) / 3
            elif pivot_type == 'fibonacci':
                pivot = (df['high'].shift(1) + df['low'].shift(1) + df['close'].shift(1)) / 3
            else:  # camarilla
                pivot = df['close'].shift(1)
            result_df['indicator_value'] = pivot

        elif indicator_type == 'CHOP':
            period = params.get('period', 14)
            chop = ta.chop(df['high'], df['low'], df['close'], length=period)
            result_df['indicator_value'] = chop if chop is not None else 50.0

        elif indicator_type == 'STOCH':
            k_period = params.get('k_period', 14)
            d_period = params.get('d_period', 3)
            stoch = ta.stoch(df['high'], df['low'], df['close'], k=k_period, d=d_period)
            if stoch is not None and not stoch.empty:
                # Stochastic returns %K and %D columns
                k_cols = [c for c in stoch.columns if 'K' in c.upper() and 'D' not in c]
                d_cols = [c for c in stoch.columns if 'D' in c.upper()]

                if k_cols:
                    result_df['indicator_value'] = stoch[k_cols[0]]
                    if d_cols:
                        result_df['stoch_d'] = stoch[d_cols[0]]
                else:
                    result_df['indicator_value'] = 50.0
            else:
                result_df['indicator_value'] = 50.0

        elif indicator_type == 'CCI':
            period = params.get('period', 20)
            cci = ta.cci(df['high'], df['low'], df['close'], length=period)
            result_df['indicator_value'] = cci if cci is not None else 0.0

        elif indicator_type == 'BB_WIDTH':
            period = params.get('period', 20)
            std = params.get('std', 2.0)
            bbands = ta.bbands(df['close'], length=period, std=std)
            if bbands is not None and not bbands.empty and len(bbands.columns) >= 3:
                # Positional access: [0]=Lower, [1]=Middle, [2]=Upper
                bb_lower = bbands.iloc[:, 0]
                bb_middle = bbands.iloc[:, 1]
                bb_upper = bbands.iloc[:, 2]
                result_df['indicator_value'] = (bb_upper - bb_lower) / bb_middle * 100
            else:
                result_df['indicator_value'] = 2.0  # Default BB width (2% = normal)

        elif indicator_type == 'OBV':
            obv = ta.obv(df['close'], df['volume'])
            result_df['indicator_value'] = obv if obv is not None else df['volume'].cumsum()

        elif indicator_type == 'MFI':
            period = params.get('period', 14)
            mfi = ta.mfi(df['high'], df['low'], df['close'], df['volume'], length=period)
            result_df['indicator_value'] = mfi if mfi is not None else 50.0

        elif indicator_type == 'AD':
            ad = ta.ad(df['high'], df['low'], df['close'], df['volume'])
            result_df['indicator_value'] = ad if ad is not None else 0.0

        elif indicator_type == 'CMF':
            period = params.get('period', 20)
            cmf = ta.cmf(df['high'], df['low'], df['close'], df['volume'], length=period)
            result_df['indicator_value'] = cmf if cmf is not None else 0.0

        return result_df.dropna()

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
        """Generate trading signals based on indicator, test type, and trade side."""
        signals = pd.Series(False, index=df.index)

        if indicator_type == 'RSI':
            if test_type == 'entry' and trade_side == 'long':
                # Entry Long: RSI < 30 (oversold)
                signals = df['indicator_value'] < 30
            elif test_type == 'entry' and trade_side == 'short':
                # Entry Short: RSI > 70 (overbought)
                signals = df['indicator_value'] > 70
            elif test_type == 'exit' and trade_side == 'long':
                # Exit Long: RSI > 70 (overbought)
                signals = df['indicator_value'] > 70
            elif test_type == 'exit' and trade_side == 'short':
                # Exit Short: RSI < 30 (oversold)
                signals = df['indicator_value'] < 30

        elif indicator_type == 'MACD':
            if test_type == 'entry' and trade_side == 'long':
                # Entry Long: MACD crosses above 0
                signals = (df['indicator_value'] > 0) & (df['indicator_value'].shift(1) <= 0)
            elif test_type == 'entry' and trade_side == 'short':
                # Entry Short: MACD crosses below 0
                signals = (df['indicator_value'] < 0) & (df['indicator_value'].shift(1) >= 0)
            elif test_type == 'exit' and trade_side == 'long':
                # Exit Long: MACD crosses below 0
                signals = (df['indicator_value'] < 0) & (df['indicator_value'].shift(1) >= 0)
            elif test_type == 'exit' and trade_side == 'short':
                # Exit Short: MACD crosses above 0
                signals = (df['indicator_value'] > 0) & (df['indicator_value'].shift(1) <= 0)

        elif indicator_type == 'ADX':
            if test_type == 'entry':
                # Entry: Strong trend (ADX > 25)
                signals = df['indicator_value'] > 25
            else:
                # Exit: Weak trend (ADX < 20)
                signals = df['indicator_value'] < 20

        # TREND & OVERLAY INDICATORS

        elif indicator_type == 'SMA':
            if test_type == 'entry' and trade_side == 'long':
                # Entry Long: Price crosses above SMA
                signals = (df['close'] > df['indicator_value']) & \
                          (df['close'].shift(1) <= df['indicator_value'].shift(1))
            elif test_type == 'entry' and trade_side == 'short':
                # Entry Short: Price crosses below SMA
                signals = (df['close'] < df['indicator_value']) & \
                          (df['close'].shift(1) >= df['indicator_value'].shift(1))
            elif test_type == 'exit' and trade_side == 'long':
                # Exit Long: Price crosses below SMA
                signals = (df['close'] < df['indicator_value']) & \
                          (df['close'].shift(1) >= df['indicator_value'].shift(1))
            elif test_type == 'exit' and trade_side == 'short':
                # Exit Short: Price crosses above SMA
                signals = (df['close'] > df['indicator_value']) & \
                          (df['close'].shift(1) <= df['indicator_value'].shift(1))

        elif indicator_type == 'EMA':
            if test_type == 'entry' and trade_side == 'long':
                # Entry Long: Price crosses above EMA
                signals = (df['close'] > df['indicator_value']) & \
                          (df['close'].shift(1) <= df['indicator_value'].shift(1))
            elif test_type == 'entry' and trade_side == 'short':
                # Entry Short: Price crosses below EMA
                signals = (df['close'] < df['indicator_value']) & \
                          (df['close'].shift(1) >= df['indicator_value'].shift(1))
            elif test_type == 'exit' and trade_side == 'long':
                # Exit Long: Price crosses below EMA
                signals = (df['close'] < df['indicator_value']) & \
                          (df['close'].shift(1) >= df['indicator_value'].shift(1))
            elif test_type == 'exit' and trade_side == 'short':
                # Exit Short: Price crosses above EMA
                signals = (df['close'] > df['indicator_value']) & \
                          (df['close'].shift(1) <= df['indicator_value'].shift(1))

        elif indicator_type == 'ICHIMOKU':
            if test_type == 'entry' and trade_side == 'long':
                # Entry Long: Price crosses above cloud
                signals = (df['close'] > df['cloud_top']) & \
                          (df['close'].shift(1) <= df['cloud_top'].shift(1))
            elif test_type == 'entry' and trade_side == 'short':
                # Entry Short: Price crosses below cloud
                signals = (df['close'] < df['cloud_bottom']) & \
                          (df['close'].shift(1) >= df['cloud_bottom'].shift(1))
            elif test_type == 'exit' and trade_side == 'long':
                # Exit Long: Price enters cloud
                signals = (df['close'] < df['cloud_top']) & \
                          (df['close'].shift(1) >= df['cloud_top'].shift(1))
            elif test_type == 'exit' and trade_side == 'short':
                # Exit Short: Price enters cloud
                signals = (df['close'] > df['cloud_bottom']) & \
                          (df['close'].shift(1) <= df['cloud_bottom'].shift(1))

        elif indicator_type == 'PSAR':
            if test_type == 'entry' and trade_side == 'long':
                # Entry Long: Price crosses above PSAR (reversal)
                signals = (df['close'] > df['indicator_value']) & \
                          (df['close'].shift(1) <= df['indicator_value'].shift(1))
            elif test_type == 'entry' and trade_side == 'short':
                # Entry Short: Price crosses below PSAR (reversal)
                signals = (df['close'] < df['indicator_value']) & \
                          (df['close'].shift(1) >= df['indicator_value'].shift(1))
            elif test_type == 'exit' and trade_side == 'long':
                # Exit Long: PSAR flips
                signals = (df['close'] < df['indicator_value']) & \
                          (df['close'].shift(1) >= df['indicator_value'].shift(1))
            elif test_type == 'exit' and trade_side == 'short':
                # Exit Short: PSAR flips
                signals = (df['close'] > df['indicator_value']) & \
                          (df['close'].shift(1) <= df['indicator_value'].shift(1))

        elif indicator_type == 'VWAP':
            if test_type == 'entry' and trade_side == 'long':
                # Entry Long: Price crosses above VWAP
                signals = (df['close'] > df['indicator_value']) & \
                          (df['close'].shift(1) <= df['indicator_value'].shift(1))
            elif test_type == 'entry' and trade_side == 'short':
                # Entry Short: Price crosses below VWAP
                signals = (df['close'] < df['indicator_value']) & \
                          (df['close'].shift(1) >= df['indicator_value'].shift(1))
            elif test_type == 'exit' and trade_side == 'long':
                # Exit Long: Price crosses below VWAP
                signals = (df['close'] < df['indicator_value']) & \
                          (df['close'].shift(1) >= df['indicator_value'].shift(1))
            elif test_type == 'exit' and trade_side == 'short':
                # Exit Short: Price crosses above VWAP
                signals = (df['close'] > df['indicator_value']) & \
                          (df['close'].shift(1) <= df['indicator_value'].shift(1))

        elif indicator_type == 'PIVOTS':
            if test_type == 'entry' and trade_side == 'long':
                # Entry Long: Price bounces off pivot (above pivot)
                signals = df['close'] > df['indicator_value']
            elif test_type == 'entry' and trade_side == 'short':
                # Entry Short: Price bounces off pivot (below pivot)
                signals = df['close'] < df['indicator_value']
            elif test_type == 'exit' and trade_side == 'long':
                # Exit Long: Price below pivot
                signals = df['close'] < df['indicator_value']
            elif test_type == 'exit' and trade_side == 'short':
                # Exit Short: Price above pivot
                signals = df['close'] > df['indicator_value']

        # BREAKOUT & CHANNELS

        elif indicator_type == 'BB':
            if test_type == 'entry' and trade_side == 'long':
                # Entry Long: Price touches lower band (oversold)
                signals = df['close'] <= df['bb_lower']
            elif test_type == 'entry' and trade_side == 'short':
                # Entry Short: Price touches upper band (overbought)
                signals = df['close'] >= df['bb_upper']
            elif test_type == 'exit' and trade_side == 'long':
                # Exit Long: Price crosses above middle or upper band
                signals = df['close'] >= df['bb_middle']
            elif test_type == 'exit' and trade_side == 'short':
                # Exit Short: Price crosses below middle or lower band
                signals = df['close'] <= df['bb_middle']

        elif indicator_type == 'KC':
            if test_type == 'entry' and trade_side == 'long':
                # Entry Long: Price breaks above upper Keltner
                signals = (df['close'] > df['kc_upper']) & \
                          (df['close'].shift(1) <= df['kc_upper'].shift(1))
            elif test_type == 'entry' and trade_side == 'short':
                # Entry Short: Price breaks below lower Keltner
                signals = (df['close'] < df['kc_lower']) & \
                          (df['close'].shift(1) >= df['kc_lower'].shift(1))
            elif test_type == 'exit' and trade_side == 'long':
                # Exit Long: Price re-enters channel
                signals = (df['close'] < df['kc_upper']) & \
                          (df['close'].shift(1) >= df['kc_upper'].shift(1))
            elif test_type == 'exit' and trade_side == 'short':
                # Exit Short: Price re-enters channel
                signals = (df['close'] > df['kc_lower']) & \
                          (df['close'].shift(1) <= df['kc_lower'].shift(1))

        # REGIME & TREND STRENGTH

        elif indicator_type == 'CHOP':
            if test_type == 'entry' and trade_side == 'long':
                # Entry Long: Low chop (trending), expect continuation
                signals = df['indicator_value'] < 38.2
            elif test_type == 'entry' and trade_side == 'short':
                # Entry Short: Low chop (trending), expect continuation
                signals = df['indicator_value'] < 38.2
            elif test_type == 'exit':
                # Exit: High chop (ranging), exit trend trades
                signals = df['indicator_value'] > 61.8

        # MOMENTUM

        elif indicator_type == 'STOCH':
            if test_type == 'entry' and trade_side == 'long':
                # Entry Long: Stoch crosses above 20 (oversold recovery)
                signals = (df['indicator_value'] > 20) & (df['indicator_value'].shift(1) <= 20)
            elif test_type == 'entry' and trade_side == 'short':
                # Entry Short: Stoch crosses below 80 (overbought reversal)
                signals = (df['indicator_value'] < 80) & (df['indicator_value'].shift(1) >= 80)
            elif test_type == 'exit' and trade_side == 'long':
                # Exit Long: Stoch crosses below 80 (overbought)
                signals = (df['indicator_value'] < 80) & (df['indicator_value'].shift(1) >= 80)
            elif test_type == 'exit' and trade_side == 'short':
                # Exit Short: Stoch crosses above 20 (oversold)
                signals = (df['indicator_value'] > 20) & (df['indicator_value'].shift(1) <= 20)

        elif indicator_type == 'CCI':
            if test_type == 'entry' and trade_side == 'long':
                # Entry Long: CCI crosses above -100 (oversold recovery)
                signals = (df['indicator_value'] > -100) & (df['indicator_value'].shift(1) <= -100)
            elif test_type == 'entry' and trade_side == 'short':
                # Entry Short: CCI crosses below 100 (overbought reversal)
                signals = (df['indicator_value'] < 100) & (df['indicator_value'].shift(1) >= 100)
            elif test_type == 'exit' and trade_side == 'long':
                # Exit Long: CCI crosses below 100
                signals = (df['indicator_value'] < 100) & (df['indicator_value'].shift(1) >= 100)
            elif test_type == 'exit' and trade_side == 'short':
                # Exit Short: CCI crosses above -100
                signals = (df['indicator_value'] > -100) & (df['indicator_value'].shift(1) <= -100)

        # VOLATILITY

        elif indicator_type == 'ATR':
            if test_type == 'entry':
                # Entry: High volatility (ATR expanding)
                atr_sma = df['indicator_value'].rolling(20).mean()
                signals = df['indicator_value'] > atr_sma
            else:
                # Exit: Low volatility (ATR contracting)
                atr_sma = df['indicator_value'].rolling(20).mean()
                signals = df['indicator_value'] < atr_sma

        elif indicator_type == 'BB_WIDTH':
            if test_type == 'entry':
                # Entry: High volatility (wide bands)
                bb_width_sma = df['indicator_value'].rolling(20).mean()
                signals = df['indicator_value'] > bb_width_sma
            else:
                # Exit: Low volatility (narrow bands, squeeze)
                bb_width_sma = df['indicator_value'].rolling(20).mean()
                signals = df['indicator_value'] < bb_width_sma

        # VOLUME

        elif indicator_type == 'OBV':
            if test_type == 'entry' and trade_side == 'long':
                # Entry Long: OBV trending up (accumulation)
                obv_sma = df['indicator_value'].rolling(20).mean()
                signals = (df['indicator_value'] > obv_sma) & \
                          (df['indicator_value'].shift(1) <= obv_sma.shift(1))
            elif test_type == 'entry' and trade_side == 'short':
                # Entry Short: OBV trending down (distribution)
                obv_sma = df['indicator_value'].rolling(20).mean()
                signals = (df['indicator_value'] < obv_sma) & \
                          (df['indicator_value'].shift(1) >= obv_sma.shift(1))
            elif test_type == 'exit' and trade_side == 'long':
                # Exit Long: OBV crosses below SMA
                obv_sma = df['indicator_value'].rolling(20).mean()
                signals = (df['indicator_value'] < obv_sma) & \
                          (df['indicator_value'].shift(1) >= obv_sma.shift(1))
            elif test_type == 'exit' and trade_side == 'short':
                # Exit Short: OBV crosses above SMA
                obv_sma = df['indicator_value'].rolling(20).mean()
                signals = (df['indicator_value'] > obv_sma) & \
                          (df['indicator_value'].shift(1) <= obv_sma.shift(1))

        elif indicator_type == 'MFI':
            if test_type == 'entry' and trade_side == 'long':
                # Entry Long: MFI < 20 (oversold)
                signals = df['indicator_value'] < 20
            elif test_type == 'entry' and trade_side == 'short':
                # Entry Short: MFI > 80 (overbought)
                signals = df['indicator_value'] > 80
            elif test_type == 'exit' and trade_side == 'long':
                # Exit Long: MFI > 80 (overbought)
                signals = df['indicator_value'] > 80
            elif test_type == 'exit' and trade_side == 'short':
                # Exit Short: MFI < 20 (oversold)
                signals = df['indicator_value'] < 20

        elif indicator_type == 'AD':
            if test_type == 'entry' and trade_side == 'long':
                # Entry Long: A/D trending up
                ad_sma = df['indicator_value'].rolling(20).mean()
                signals = (df['indicator_value'] > ad_sma) & \
                          (df['indicator_value'].shift(1) <= ad_sma.shift(1))
            elif test_type == 'entry' and trade_side == 'short':
                # Entry Short: A/D trending down
                ad_sma = df['indicator_value'].rolling(20).mean()
                signals = (df['indicator_value'] < ad_sma) & \
                          (df['indicator_value'].shift(1) >= ad_sma.shift(1))
            elif test_type == 'exit' and trade_side == 'long':
                # Exit Long: A/D crosses below SMA
                ad_sma = df['indicator_value'].rolling(20).mean()
                signals = (df['indicator_value'] < ad_sma) & \
                          (df['indicator_value'].shift(1) >= ad_sma.shift(1))
            elif test_type == 'exit' and trade_side == 'short':
                # Exit Short: A/D crosses above SMA
                ad_sma = df['indicator_value'].rolling(20).mean()
                signals = (df['indicator_value'] > ad_sma) & \
                          (df['indicator_value'].shift(1) <= ad_sma.shift(1))

        elif indicator_type == 'CMF':
            if test_type == 'entry' and trade_side == 'long':
                # Entry Long: CMF crosses above 0 (accumulation)
                signals = (df['indicator_value'] > 0) & (df['indicator_value'].shift(1) <= 0)
            elif test_type == 'entry' and trade_side == 'short':
                # Entry Short: CMF crosses below 0 (distribution)
                signals = (df['indicator_value'] < 0) & (df['indicator_value'].shift(1) >= 0)
            elif test_type == 'exit' and trade_side == 'long':
                # Exit Long: CMF crosses below 0
                signals = (df['indicator_value'] < 0) & (df['indicator_value'].shift(1) >= 0)
            elif test_type == 'exit' and trade_side == 'short':
                # Exit Short: CMF crosses above 0
                signals = (df['indicator_value'] > 0) & (df['indicator_value'].shift(1) <= 0)

        return signals

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
