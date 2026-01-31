"""Regime Detection Logic - Core algorithm and analysis.

Extracted from entry_analyzer_backtest_config.py (lines 640-1180)
Handles the core regime detection algorithm for chart analysis.

Components:
- Visible range analysis trigger
- Incremental regime detection (candle-by-candle)
- v2.0 JSON config evaluation
- Indicator calculations (ADX, RSI, DI+/DI-)
- Threshold evaluation logic
- Regime period tracking
- Helper functions (threshold mapping, duration formatting)

Date: 2026-01-31 (Task 3.2.1 - Patch 3)
LOC: ~540
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QMessageBox, QTableWidgetItem

from src.core.indicators.types import IndicatorConfig, IndicatorType
from src.core.tradingbot.regime_engine_json import RegimeEngineJSON

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class RegimeDetectionLogicMixin:
    """Core regime detection algorithm.

    Provides:
    - Visible range analysis trigger
    - v2.0 regime detection algorithm
    - Indicator calculations
    - Threshold evaluation logic
    - Results table population

    Attributes (defined in parent class):
        _candles: list[dict] - Chart candle data
        _symbol: str - Trading symbol
        _timeframe: str - Chart timeframe
        _regime_config: dict | None - Loaded regime config
        _regime_start_day: QLabel - Chart start day
        _regime_end_day: QLabel - Chart end day
        _regime_period_days: QLabel - Period in days
        _regime_num_bars: QLabel - Number of bars
        _detected_regimes_table: QTableWidget - Results table
    """

    def _on_analyze_visible_range_clicked(self) -> None:
        """Analyze visible chart range for regime detection (Issue #21).

        Workflow:
        1. Check for unsaved changes (force save if dirty)
        2. Read chart data (Start Day, End Day, Period, Bars)
        3. Perform incremental regime detection (candle-by-candle)
        4. Display vertical lines with regime labels in chart
        5. Populate results table with timestamps
        """
        # Check for unsaved changes first
        if not self._check_unsaved_changes():
            return

        if not self._candles or len(self._candles) < 50:
            QMessageBox.warning(
                self,
                "Insufficient Data",
                "Need at least 50 candles for regime analysis.\n" "Load more chart data first.",
            )
            return

        try:
            logger.info("Starting visible range regime analysis...")

            # Step 1: Extract chart data information
            start_timestamp = self._candles[0].get("timestamp") or self._candles[0].get("time")
            end_timestamp = self._candles[-1].get("timestamp") or self._candles[-1].get("time")
            num_bars = len(self._candles)

            # Convert timestamps to datetime
            start_dt = (
                datetime.fromtimestamp(start_timestamp / 1000)
                if start_timestamp > 1e10
                else datetime.fromtimestamp(start_timestamp)
            )
            end_dt = (
                datetime.fromtimestamp(end_timestamp / 1000)
                if end_timestamp > 1e10
                else datetime.fromtimestamp(end_timestamp)
            )
            period_days = (end_dt - start_dt).days

            # Update UI fields
            self._regime_start_day.setText(start_dt.strftime("%Y-%m-%d %H:%M"))
            self._regime_start_day.setStyleSheet("color: #10b981;")  # Green
            self._regime_end_day.setText(end_dt.strftime("%Y-%m-%d %H:%M"))
            self._regime_end_day.setStyleSheet("color: #10b981;")
            self._regime_period_days.setText(f"{period_days} days")
            self._regime_period_days.setStyleSheet("color: #10b981;")
            self._regime_num_bars.setText(f"{num_bars} bars")
            self._regime_num_bars.setStyleSheet("color: #10b981;")

            # Step 2: Incremental regime detection (candle-by-candle)
            logger.info("Performing incremental regime detection...")
            detected_regimes = self._perform_incremental_regime_detection()

            # Step 3: Update results table with COMPLETE regime periods (Start + End)
            logger.info(f"About to populate table with {len(detected_regimes)} regime periods")
            logger.info(f"Table widget: {self._detected_regimes_table}")
            logger.info(f"Table column count: {self._detected_regimes_table.columnCount()}")

            self._detected_regimes_table.setRowCount(0)  # Clear existing rows

            if not detected_regimes:
                logger.warning("No regime periods detected in the visible range")
                QMessageBox.warning(
                    self,
                    "No Regimes Detected",
                    "No regime changes were detected in the visible range.\n\n"
                    "Possible reasons:\n"
                    "- Not enough data (need at least 50 candles)\n"
                    "- Regime config is not loaded\n"
                    "- All indicator values are invalid (NaN)\n"
                    "- No regime conditions are met\n\n"
                    f"Candles available: {len(self._candles)}\n"
                    f"Regime config loaded: {'Yes' if self._regime_config else 'No'}"
                )
                return

            logger.info(f"Starting to populate {len(detected_regimes)} rows in table")

            for idx, regime_data in enumerate(detected_regimes):
                try:
                    row = self._detected_regimes_table.rowCount()
                    logger.debug(f"Inserting row {row} (index {idx}) for regime {regime_data.get('regime', 'UNKNOWN')}")
                    self._detected_regimes_table.insertRow(row)

                    # Start Date
                    start_date_item = QTableWidgetItem(regime_data["start_date"])
                    start_date_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self._detected_regimes_table.setItem(row, 0, start_date_item)

                    # Start Time
                    start_time_item = QTableWidgetItem(regime_data["start_time"])
                    start_time_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self._detected_regimes_table.setItem(row, 1, start_time_item)

                    # End Date
                    end_date_item = QTableWidgetItem(regime_data["end_date"])
                    end_date_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self._detected_regimes_table.setItem(row, 2, end_date_item)

                    # End Time
                    end_time_item = QTableWidgetItem(regime_data["end_time"])
                    end_time_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self._detected_regimes_table.setItem(row, 3, end_time_item)

                    # Regime
                    regime_item = QTableWidgetItem(regime_data["regime"])
                    regime_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self._detected_regimes_table.setItem(row, 4, regime_item)

                    # Score
                    score_item = QTableWidgetItem(f"{regime_data['score']:.2f}")
                    score_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self._detected_regimes_table.setItem(row, 5, score_item)

                    # Duration (Bars)
                    duration_bars_item = QTableWidgetItem(str(regime_data["duration_bars"]))
                    duration_bars_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self._detected_regimes_table.setItem(row, 6, duration_bars_item)

                    # Duration (Time)
                    duration_time_item = QTableWidgetItem(regime_data["duration_time"])
                    duration_time_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self._detected_regimes_table.setItem(row, 7, duration_time_item)

                except Exception as row_error:
                    logger.error(f"Error populating row {idx} for regime {regime_data.get('regime', 'UNKNOWN')}: {row_error}", exc_info=True)
                    continue

            # Log table population completion
            final_row_count = self._detected_regimes_table.rowCount()
            logger.info(f"✓ Table population complete! Final row count: {final_row_count}")
            logger.info(f"  Expected: {len(detected_regimes)}, Actual: {final_row_count}")

            if final_row_count == 0:
                logger.error("⚠️ TABLE IS EMPTY after population attempt!")
                logger.error(f"  detected_regimes length: {len(detected_regimes)}")
                logger.error(f"  Table widget valid: {self._detected_regimes_table is not None}")

            # Step 4: Draw vertical lines in chart (Issue #21: Emit signal to chart)
            if hasattr(self, "draw_regime_lines_requested"):
                # Emit signal with regime data for chart visualization
                self.draw_regime_lines_requested.emit(detected_regimes)
                logger.info(f"Emitted signal to draw {len(detected_regimes)} regime lines in chart")

            logger.info(f"Detected {len(detected_regimes)} regime changes")
            QMessageBox.information(
                self,
                "Regime Analysis Complete",
                f"Successfully analyzed {num_bars} candles.\n"
                f"Detected {len(detected_regimes)} regime changes.\n"
                f"Period: {start_dt.strftime('%Y-%m-%d')} to {end_dt.strftime('%Y-%m-%d')} ({period_days} days)",
            )

        except Exception as e:
            logger.error(f"Regime analysis failed: {e}", exc_info=True)
            QMessageBox.critical(
                self, "Analysis Error", f"Failed to analyze visible range:\n\n{str(e)}"
            )

    def _perform_incremental_regime_detection(self) -> list[dict]:
        """Perform regime detection on visible chart range (v2 JSON optimized).

        Evaluates v2.0 regime thresholds directly against calculated indicator values.
        No legacy model conversions - pure v2 format.

        Returns:
            List of regime periods with start, end, duration for each regime.
        """
        # ===== 1. Load and validate v2 config =====
        if self._regime_config is None:
            self._load_default_regime_config()

        config = self._regime_config
        if config is None:
            raise ValueError("Keine Regime-Config geladen. Bitte zuerst eine Config laden.")

        # Extract v2 data from optimization_results
        if "optimization_results" not in config or not config["optimization_results"]:
            raise ValueError("Config hat kein 'optimization_results' - kein v2 Format?")

        applied = [r for r in config["optimization_results"] if r.get('applied', False)]
        opt_result = applied[-1] if applied else config["optimization_results"][0]

        indicators_v2 = opt_result.get('indicators', [])
        regimes_v2 = opt_result.get('regimes', [])

        if not indicators_v2 or not regimes_v2:
            raise ValueError(f"Config enthält keine Indikatoren oder Regimes: {len(indicators_v2)} indicators, {len(regimes_v2)} regimes")

        logger.info(f"V2 Config: {len(indicators_v2)} Indikatoren, {len(regimes_v2)} Regimes")

        # ===== 2. Build DataFrame =====
        df = pd.DataFrame(self._candles)
        if "timestamp" not in df.columns and "time" in df.columns:
            df["timestamp"] = df["time"]

        required = ["open", "high", "low", "close", "volume", "timestamp"]
        missing = [c for c in required if c not in df.columns]
        if missing:
            raise ValueError(f"Fehlende Spalten: {missing}")

        # ===== 3. Calculate all indicators once =====
        engine = RegimeEngineJSON()
        indicator_values = {}  # name -> pd.Series or DataFrame

        for ind in indicators_v2:
            name = ind['name']
            ind_type = ind['type'].upper()
            params = {p['name']: p['value'] for p in ind.get('params', [])}

            try:
                ind_config = IndicatorConfig(
                    indicator_type=IndicatorType(ind_type.lower()),
                    params=params,
                    use_talib=False,
                    cache_results=True,
                )
                result = engine.indicator_engine.calculate(df, ind_config)
                indicator_values[name] = result.values
                logger.debug(f"Indikator {name} ({ind_type}) berechnet: {len(result.values)} Werte")
            except Exception as e:
                logger.error(f"Fehler bei Indikator {name}: {e}")
                indicator_values[name] = pd.Series([np.nan] * len(df))

        # ===== 3b. Calculate ADX/DI components for ADX/DI-based regime detection =====
        # Find ADX indicator config to get period
        adx_period = 14  # Default
        for ind in indicators_v2:
            if ind['type'].upper() == 'ADX':
                for p in ind.get('params', []):
                    if p['name'] == 'period':
                        adx_period = p['value']
                        break
                break

        try:
            import pandas_ta as ta
            # Calculate DI+ and DI-
            adx_df = ta.adx(df['high'], df['low'], df['close'], length=adx_period)
            if adx_df is not None and not adx_df.empty:
                # pandas_ta returns columns like ADX_14, DMP_14, DMN_14
                di_plus_col = f'DMP_{adx_period}'
                di_minus_col = f'DMN_{adx_period}'
                if di_plus_col in adx_df.columns:
                    indicator_values['PLUS_DI'] = adx_df[di_plus_col]
                    indicator_values['MINUS_DI'] = adx_df[di_minus_col]
                    indicator_values['DI_DIFF'] = adx_df[di_plus_col] - adx_df[di_minus_col]
                    logger.debug(f"DI+/DI-/DI_DIFF berechnet mit Periode {adx_period}")
        except Exception as e:
            logger.warning(f"Could not calculate DI+/DI-: {e}")
            indicator_values['PLUS_DI'] = pd.Series([np.nan] * len(df))
            indicator_values['MINUS_DI'] = pd.Series([np.nan] * len(df))
            indicator_values['DI_DIFF'] = pd.Series([np.nan] * len(df))

        # ===== 3c. Calculate price change percentage for extreme move detection =====
        try:
            indicator_values['PRICE_CHANGE_PCT'] = df['close'].pct_change() * 100
            logger.debug("Price change percentage berechnet")
        except Exception as e:
            logger.warning(f"Could not calculate price change %: {e}")
            indicator_values['PRICE_CHANGE_PCT'] = pd.Series([np.nan] * len(df))

        # ===== 4. Build threshold evaluation functions =====
        def get_indicator_value(ind_name: str, idx: int) -> float:
            """Get indicator value at specific bar index."""
            if ind_name not in indicator_values:
                return np.nan
            vals = indicator_values[ind_name]
            if isinstance(vals, pd.DataFrame):
                # Multi-column indicator (e.g., BB) - use first numeric column
                return float(vals.iloc[idx, 0]) if idx < len(vals) else np.nan
            elif isinstance(vals, pd.Series):
                return float(vals.iloc[idx]) if idx < len(vals) else np.nan
            return np.nan

        def evaluate_regime_at(regime: dict, idx: int) -> bool:
            """Evaluate if regime conditions are met at bar index.

            Supports ADX/DI-based thresholds:
            - adx_min: ADX >= value (trend strength)
            - adx_max: ADX < value (weak trend)
            - di_diff_min: (DI+ - DI-) > value (for BULL) or (DI- - DI+) > value (for BEAR)
            - rsi_strong_bull: RSI > value (bullish momentum confirmation)
            - rsi_strong_bear: RSI < value (bearish momentum confirmation)
            - rsi_confirm_bull: RSI > value (confirms STRONG_BULL with momentum)
            - rsi_confirm_bear: RSI < value (confirms STRONG_BEAR with momentum)
            - rsi_exhaustion_max: RSI < value (BULL losing momentum = reversal warning)
            - rsi_exhaustion_min: RSI > value (BEAR losing momentum = reversal warning)
            - extreme_move_pct: |price_change| >= value (extreme price moves)
            """
            thresholds = regime.get('thresholds', [])
            regime_id = regime.get('id', '').upper()

            for thresh in thresholds:
                name = thresh['name']
                value = thresh['value']

                # ===== ADX/DI-based threshold handling =====

                # DI difference threshold (direction confirmation)
                if name == 'di_diff_min':
                    di_diff = get_indicator_value('DI_DIFF', idx)
                    if np.isnan(di_diff):
                        return False
                    # For TF/TREND_FOLLOWING: absolute DI diff >= threshold (either direction)
                    # For BULL: DI+ > DI- (positive diff)
                    # For BEAR: DI- > DI+ (negative diff)
                    if regime_id in ('TF', 'STRONG_TF') or 'TREND' in regime_id or 'FOLLOWING' in regime_id:
                        # Strong trend in either direction (direction-agnostic)
                        if abs(di_diff) < value:
                            return False
                    elif 'BULL' in regime_id:
                        if di_diff < value:  # DI+ - DI- must be > threshold
                            return False
                    elif 'BEAR' in regime_id:
                        if di_diff > -value:  # DI- - DI+ must be > threshold (diff < -threshold)
                            return False
                    else:
                        # Unknown regime type - check absolute value
                        if abs(di_diff) < value:
                            return False
                    continue

                # RSI strong bull threshold
                if name == 'rsi_strong_bull':
                    rsi_val = get_indicator_value('MOMENTUM_RSI', idx)
                    if np.isnan(rsi_val) or rsi_val < value:
                        return False
                    continue

                # RSI strong bear threshold
                if name == 'rsi_strong_bear':
                    rsi_val = get_indicator_value('MOMENTUM_RSI', idx)
                    if np.isnan(rsi_val) or rsi_val > value:
                        return False
                    continue

                # RSI confirmation for bullish momentum (STRONG_BULL)
                if name == 'rsi_confirm_bull':
                    rsi_val = get_indicator_value('MOMENTUM_RSI', idx)
                    if np.isnan(rsi_val) or rsi_val < value:
                        return False
                    continue

                # RSI confirmation for bearish momentum (STRONG_BEAR)
                if name == 'rsi_confirm_bear':
                    rsi_val = get_indicator_value('MOMENTUM_RSI', idx)
                    if np.isnan(rsi_val) or rsi_val > value:
                        return False
                    continue

                # RSI exhaustion for bullish trend (BULL_EXHAUSTION)
                if name == 'rsi_exhaustion_max':
                    rsi_val = get_indicator_value('MOMENTUM_RSI', idx)
                    if np.isnan(rsi_val) or rsi_val > value:
                        return False
                    continue

                # RSI exhaustion for bearish trend (BEAR_EXHAUSTION)
                if name == 'rsi_exhaustion_min':
                    rsi_val = get_indicator_value('MOMENTUM_RSI', idx)
                    if np.isnan(rsi_val) or rsi_val < value:
                        return False
                    continue

                # Extreme price move percentage
                if name == 'extreme_move_pct':
                    price_change = get_indicator_value('PRICE_CHANGE_PCT', idx)
                    if np.isnan(price_change):
                        return False
                    if 'BULL' in regime_id:
                        if price_change < value:
                            return False
                    elif 'BEAR' in regime_id:
                        if price_change > -value:
                            return False
                    continue

                # ===== Standard _min/_max threshold handling =====
                if name.endswith('_min'):
                    base = name[:-4]  # adx, rsi
                    ind_name = self._threshold_to_indicator_name(base)
                    ind_val = get_indicator_value(ind_name, idx)
                    if np.isnan(ind_val) or ind_val < value:
                        return False

                elif name.endswith('_max'):
                    base = name[:-4]
                    ind_name = self._threshold_to_indicator_name(base)
                    ind_val = get_indicator_value(ind_name, idx)
                    if np.isnan(ind_val) or ind_val >= value:
                        return False
                else:
                    # Unknown threshold - log but don't fail
                    logger.debug(f"Unbekanntes Threshold-Format: {name} (ignored)")

            return True  # All thresholds passed

        # ===== 5. Iterate through candles and detect regimes =====
        min_candles = 50  # Warmup for indicator calculation
        regime_periods = []
        current_regime = None

        # Sort regimes by priority (highest first)
        sorted_regimes = sorted(regimes_v2, key=lambda r: r.get('priority', 0), reverse=True)

        # Fallback to lowest priority regime (usually SIDEWAYS) instead of UNKNOWN
        fallback_regime_id = sorted_regimes[-1]['id'] if sorted_regimes else "SIDEWAYS"

        for i in range(min_candles, len(df)):
            # Find first matching regime (highest priority)
            active_regime_id = fallback_regime_id
            for regime in sorted_regimes:
                if evaluate_regime_at(regime, i):
                    active_regime_id = regime['id']
                    break

            # Get timestamp for this bar
            ts = df.iloc[i]["timestamp"]
            dt = datetime.fromtimestamp(ts / 1000 if ts > 1e10 else ts)

            # Track regime changes
            if current_regime is None:
                # First regime
                current_regime = {
                    "regime": active_regime_id,
                    "score": 100.0,
                    "start_timestamp": ts,
                    "start_date": dt.strftime("%Y-%m-%d"),
                    "start_time": dt.strftime("%H:%M:%S"),
                    "start_bar_index": i,
                }
            elif current_regime["regime"] != active_regime_id:
                # Regime changed - close previous
                current_regime["end_timestamp"] = ts
                current_regime["end_date"] = dt.strftime("%Y-%m-%d")
                current_regime["end_time"] = dt.strftime("%H:%M:%S")
                current_regime["end_bar_index"] = i
                current_regime["duration_bars"] = i - current_regime["start_bar_index"]

                duration_s = (ts - current_regime["start_timestamp"])
                if current_regime["start_timestamp"] > 1e10:
                    duration_s /= 1000
                current_regime["duration_time"] = self._format_duration(duration_s)

                regime_periods.append(current_regime)

                # Start new
                current_regime = {
                    "regime": active_regime_id,
                    "score": 100.0,
                    "start_timestamp": ts,
                    "start_date": dt.strftime("%Y-%m-%d"),
                    "start_time": dt.strftime("%H:%M:%S"),
                    "start_bar_index": i,
                }

        # ===== 6. Close final regime =====
        if current_regime is not None:
            last_ts = df.iloc[-1]["timestamp"]
            last_dt = datetime.fromtimestamp(last_ts / 1000 if last_ts > 1e10 else last_ts)

            current_regime["end_timestamp"] = last_ts
            current_regime["end_date"] = last_dt.strftime("%Y-%m-%d")
            current_regime["end_time"] = last_dt.strftime("%H:%M:%S")
            current_regime["end_bar_index"] = len(df)
            current_regime["duration_bars"] = len(df) - current_regime["start_bar_index"]

            duration_s = (last_ts - current_regime["start_timestamp"])
            if current_regime["start_timestamp"] > 1e10:
                duration_s /= 1000
            current_regime["duration_time"] = self._format_duration(duration_s)

            regime_periods.append(current_regime)

        logger.info(f"Regime-Erkennung abgeschlossen: {len(regime_periods)} Perioden aus {len(df)} Kerzen")
        return regime_periods

    def _threshold_to_indicator_name(self, base: str) -> str:
        """Map threshold base name to indicator name from v2 config.

        Args:
            base: Threshold base name like 'adx', 'rsi'

        Returns:
            Indicator name from config like 'STRENGTH_ADX', 'MOMENTUM_RSI'
        """
        # Standard mappings based on common v2 naming conventions
        mappings = {
            'adx': 'STRENGTH_ADX',
            'rsi': 'MOMENTUM_RSI',
            'ema': 'TREND_FILTER',
            'sma': 'TREND_SMA',
            'bb': 'VOLATILITY_BB',
            'atr': 'VOLATILITY_ATR',
        }
        return mappings.get(base.lower(), base.upper())

    def _format_duration(self, seconds: float) -> str:
        """Format duration in seconds to human-readable string.

        Args:
            seconds: Duration in seconds

        Returns:
            Formatted string like "2h 15m" or "45m" or "30s"
        """
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            minutes = int(seconds / 60)
            return f"{minutes}m"
        else:
            hours = int(seconds / 3600)
            minutes = int((seconds % 3600) / 60)
            if minutes > 0:
                return f"{hours}h {minutes}m"
            else:
                return f"{hours}h"
