"""
Regime Display Mixin for Chart Widgets.

Adds regime detection and display functionality to chart widgets.

Phase 2.2 der Bot-Integration.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING
import json
import tempfile

from PyQt6.QtCore import QTimer
import pandas as pd
import pandas_ta as ta

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class RegimeDisplayMixin:
    """
    Mixin für Regime-Anzeige in Chart-Widgets.

    Fügt folgende Funktionalität hinzu:
    - Regime Badge in der Toolbar
    - Automatische Regime-Erkennung bei Datenänderung
    - Integration mit RegimeDetectorService

    Usage:
        class MyChartWidget(RegimeDisplayMixin, QWidget):
            def __init__(self):
                super().__init__()
                self._setup_regime_display()
    """

    _regime_badge = None
    _regime_update_timer: QTimer | None = None
    _last_regime_df_hash: str = ""
    _last_regime_name: str | None = None  # Track regime changes for line drawing

    def _setup_regime_display(self) -> None:
        """
        Setup regime display components.

        Should be called after toolbar is created.
        """
        try:
            from src.ui.widgets.regime_badge_widget import RegimeBadgeWidget

            # Create badge
            self._regime_badge = RegimeBadgeWidget(compact=True, show_icon=True)
            self._regime_badge.clicked.connect(self._on_regime_badge_clicked)
            self._regime_badge.regime_changed.connect(self._on_regime_changed)

            # Add to toolbar if exists
            if hasattr(self, "_add_regime_badge_to_toolbar"):
                self._add_regime_badge_to_toolbar()


            # Setup auto-update timer (debounce)
            self._regime_update_timer = QTimer()
            self._regime_update_timer.setSingleShot(True)
            self._regime_update_timer.timeout.connect(self._update_regime_from_data)

            logger.debug("Regime display setup complete")

        except ImportError as e:
            logger.warning(f"Could not setup regime display: {e}")

    def _add_regime_badge_to_toolbar(self) -> None:
        """
        Add regime badge to the second toolbar row.

        Override this method if toolbar structure differs.
        """
        # This method should be implemented in the toolbar mixin
        pass

    def trigger_regime_update(self, debounce_ms: int = 500, force: bool = False) -> None:
        """
        Trigger regime update with debounce.

        Args:
            debounce_ms: Milliseconds to wait before updating.
                         If 0, runs SYNCHRONOUSLY (blocking) so CEL can use result immediately.
            force: If True, bypass hash check and always run detection.
                   Used by CEL trigger_regime_analysis() to ensure regime lines are drawn.
        """
        print(f"[REGIME] trigger_regime_update called (debounce={debounce_ms}ms, force={force})", flush=True)

        # When debounce_ms=0, run SYNCHRONOUSLY so last_closed_regime() gets updated value
        if debounce_ms == 0:
            print("[REGIME] ⚡ SYNC MODE: Running detection immediately", flush=True)
            self._update_regime_from_data(force=force)
            return

        if self._regime_update_timer:
            self._regime_update_timer.stop()
            self._regime_update_timer.start(debounce_ms)
            print(f"[REGIME] Timer started, will update in {debounce_ms}ms", flush=True)
        else:
            print("[REGIME] ❌ No timer available!", flush=True)

    def _update_regime_from_data(self, force: bool = False) -> None:
        """
        Update regime from current chart data.

        Uses the RegimeDetectorService to detect the regime.

        Args:
            force: If True, bypass hash check and always run detection.
        """
        print(f"[REGIME] _update_regime_from_data called (force={force})", flush=True)

        try:
            json_regime_path = getattr(self, "json_regime_config_path", None)
            # Get current DataFrame
            df = self._get_chart_dataframe()
            print(f"[REGIME] DataFrame retrieved: {df is not None}, empty: {df.empty if df is not None else 'N/A'}", flush=True)
            if df is None or df.empty:
                logger.debug("No data available for regime detection")
                print("[REGIME] ❌ No DataFrame available", flush=True)
                if self._regime_badge:
                    self._regime_badge.set_regime("UNKNOWN")
                return

            print(f"[REGIME] ✅ DataFrame available: {len(df)} rows, columns: {list(df.columns)[:5]}", flush=True)

            # If JSON set, align with "Analyze visible chart": slice to visible range first
            if json_regime_path and hasattr(self, "get_visible_range"):
                def _on_range(range_data):
                    try:
                        df_slice = df
                        if range_data and "from" in range_data and "to" in range_data:
                            start_ts = pd.to_datetime(int(range_data["from"]), unit="s")
                            end_ts = pd.to_datetime(int(range_data["to"]), unit="s")
                            df_slice = df[(df.index >= start_ts) & (df.index <= end_ts)]
                            if df_slice.empty:
                                df_slice = df  # fallback to full data if slice empty
                        self._process_regime_detection(df_slice, json_regime_path, force)
                    except Exception as e:
                        logger.error(f"Visible-range regime detection failed: {e}", exc_info=True)
                        self._show_regime_error_popup(str(e))
                    return

                self.get_visible_range(_on_range)
                return

            # Default: process full DF
            self._process_regime_detection(df, json_regime_path, force)

        except Exception as e:
            logger.error(f"Failed to update regime: {e}", exc_info=True)
            if self._regime_badge:
                self._regime_badge.set_regime("UNKNOWN")

    def _process_regime_detection(self, df: pd.DataFrame, json_regime_path: str | None, force: bool) -> None:
        """Shared detection logic on a given DataFrame slice (visible range or full)."""

        # Ensure indicators exist
        df = self._ensure_indicators(df)

        # Check if data changed (simple hash check)
        df_hash = str(hash(tuple(df.tail(5)["close"].values)))
        is_first_detection = self._last_regime_name is None

        if df_hash == self._last_regime_df_hash and not is_first_detection and not force:
            print(f"[REGIME] ⏭️ Data unchanged (hash match), skipping detection", flush=True)
            return

        if force:
            print(f"[REGIME] 💪 FORCE MODE - running regime analysis regardless of hash", flush=True)
        elif is_first_detection:
            print(f"[REGIME] 🎯 FIRST DETECTION - forcing regime analysis regardless of hash", flush=True)
        else:
            print(f"[REGIME] 🔄 Data changed, detecting regime...", flush=True)

        self._last_regime_df_hash = df_hash

        # Detect regime
        result = None
        result_source = "default"
        if json_regime_path:
            try:
                result = self._classify_regime_from_entry_json(df, json_regime_path)
                result_source = "json_entry"
                print(f"[REGIME] JSON regime classification (Entry Analyzer path) via {json_regime_path}", flush=True)
            except Exception as je:
                logger.error(f"JSON regime classification failed: {je}")
                self._show_regime_error_popup(str(je))
                return
        else:
            print("[REGIME] No json_regime_config_path set -> default detector", flush=True)

        if result is None:
            print("[REGIME] ❌ No regime result (JSON path missing). Aborting draw.", flush=True)
            return

        if result and self._regime_badge:
            self._regime_badge.set_regime_from_result(result)

            # Draw regime line if regime changed OR first detection
            if getattr(result, "regime_name", None):
                current_regime = result.regime_name
            else:
                current_regime = result.regime.value if hasattr(result.regime, 'value') else str(result.regime)
            print(f"[REGIME] Source={result_source}, regime_label={current_regime}", flush=True)
            print(f"[REGIME] Current: {current_regime}, Last: {self._last_regime_name}", flush=True)

            if current_regime != self._last_regime_name:
                if self._last_regime_name is None:
                    if json_regime_path:
                        print(f"[REGIME] 🎨 First detection (JSON): Backfilling regimes from JSON", flush=True)
                        last_regime = self._backfill_json_regimes(df, json_regime_path)
                        self._last_regime_name = last_regime
                    else:
                        print(f"[REGIME] 🎨 First detection: Backfilling historical regimes...", flush=True)
                        self._backfill_historical_analysis(df)
                else:
                    print(f"[REGIME] 🎨 Regime changed! Drawing line for {current_regime}", flush=True)
                    self._draw_regime_line_for_change(current_regime, df)
            else:
                print(f"[REGIME] No change (still {current_regime})", flush=True)

            self._last_regime_name = current_regime
            if hasattr(result.regime, "value"):
                logger.debug(f"Regime updated: {result.regime.value}")

    def _backfill_historical_analysis(self, df: pd.DataFrame) -> None:
        """
        Analyze entire chart history and draw lines for past regime changes.
        """
        try:
            from src.core.trading_bot.regime_detector import get_regime_detector
            detector = get_regime_detector()

            last_regime = None

            # Use itertuples for speed
            # Columns needed: timestamp, ema_20, ema_50, adx_14, atr_percent, rsi_14, close
            # We assume these exist. If not, we skip.

            required_cols = {'timestamp', 'ema_20', 'ema_50', 'adx_14', 'atr_percent', 'rsi_14', 'close'}
            missing_required = required_cols - set(df.columns)
            if missing_required:
                # Try to build timestamp from 'time' or datetime index
                if 'timestamp' in missing_required:
                    if 'time' in df.columns:
                        df['timestamp'] = df['time']
                        missing_required -= {'timestamp'}
                    elif isinstance(df.index, pd.DatetimeIndex):
                        df['timestamp'] = (df.index.astype('int64') // 10**9).astype(int)
                        missing_required -= {'timestamp'}
                if missing_required:
                    print(f"[REGIME] ⚠️ Missing columns for backfill: {missing_required}", flush=True)
                    return

            print(f"[REGIME] 🔙 Starting backfill analysis on {len(df)} rows...", flush=True)

            # Iterate through history
            count = 0

            for row in df.itertuples():
                # Skip if essential indicators are NaN (warmup period)
                if pd.isna(row.ema_50) or pd.isna(row.adx_14):
                    continue

                # Detect using scalar values
                result = detector.detect_from_values(
                    ema_20=row.ema_20,
                    ema_50=row.ema_50,
                    adx=row.adx_14,
                    atr_pct=row.atr_percent,
                    rsi=row.rsi_14,
                    close=row.close
                )

                regime_str = result.regime.value if hasattr(result.regime, 'value') else str(result.regime)

                # If regime changed, draw line
                if regime_str != last_regime:
                    if last_regime is not None: # Don't draw for very first valid candle (clutter)
                        # Draw line at this timestamp
                        # We need to construct a 'fake' dataframe or modify _draw method
                        # Easier to just call add_regime_line directly

                        ts = row.timestamp if hasattr(row, 'timestamp') else (row.Index if isinstance(row.Index, (int, float)) else 0)

                        # Fix timestamp format using our robust logic
                        if isinstance(ts, (pd.Timestamp, str)):
                             # skip complex handling here, rely on row data usually being cleaned
                             pass

                        # Use the helper which handles timestamp conversion safely
                        # We construct a mini-series or simple dict wrapper

                        # Optimization: Call add_regime_line directly with timestamp
                        # Need to convert timestamp safely first

                        final_ts = ts
                        try:
                            if hasattr(ts, 'timestamp'):
                                final_ts = ts.timestamp()
                            else:
                                final_ts = float(ts)

                            if final_ts > 1e10:
                                final_ts = int(final_ts / 1000)
                            else:
                                final_ts = int(final_ts)

                            # Safe draw
                            import time
                            line_id = f"hist_{regime_str}_{final_ts}_{int(time.time())}"

                            self.add_regime_line(
                                line_id=line_id,
                                timestamp=final_ts,
                                regime_name=regime_str,
                                color=None,
                                label=regime_str
                            )
                            count += 1

                        except Exception as e:
                            # Ignore timestamp conversion errors in backfill loop
                            pass

                    last_regime = regime_str

            print(f"[REGIME] 🔙 Backfill complete: Drawn {count} historical lines", flush=True)

        except Exception as e:
            logger.error(f"Backfill missing: {e}", exc_info=True)
            print(f"[REGIME] ❌ Backfill failed: {e}", flush=True)

    def _ensure_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Ensure DataFrame has required indicators for regime detection.
        Calculates them if missing using pandas-ta.
        """
        required = ['ema_20', 'ema_50', 'adx_14', 'rsi_14', 'atr_percent']
        missing = [col for col in required if col not in df.columns]

        # Ensure timestamp column exists for downstream drawing/backfill
        if 'timestamp' not in df.columns:
            if 'time' in df.columns:
                df['timestamp'] = df['time']
            elif isinstance(df.index, pd.DatetimeIndex):
                df['timestamp'] = (df.index.astype('int64') // 10**9).astype(int)
            else:
                # Fallback to range index (seconds) to avoid zeros
                df['timestamp'] = range(len(df))

        if not missing:
            return df

        print(f"[REGIME] ⚠️ Missing indicators: {missing}. Calculating on-the-fly...", flush=True)

        try:
            import pandas_ta as ta
            # Make a copy to avoid SettingWithCopy warnings on view
            df = df.copy()

            # EMAs
            if 'ema_20' not in df.columns:
                df['ema_20'] = ta.ema(df['close'], length=20)
            if 'ema_50' not in df.columns:
                df['ema_50'] = ta.ema(df['close'], length=50)
            if 'ema_200' not in df.columns:
                df['ema_200'] = ta.ema(df['close'], length=200)

            # RSI
            if 'rsi_14' not in df.columns:
                df['rsi_14'] = ta.rsi(df['close'], length=14)

            # ADX
            if 'adx_14' not in df.columns:
                # ADX returns columns like ADX_14, DMP_14, DMN_14
                adx_res = ta.adx(df['high'], df['low'], df['close'], length=14)
                if adx_res is not None:
                     # pandas-ta returns uppercase columns usually
                     if 'ADX_14' in adx_res.columns:
                         df['adx_14'] = adx_res['ADX_14']

            # ATR Percent
            if 'atr_percent' not in df.columns:
                atr = ta.atr(df['high'], df['low'], df['close'], length=14)
                if atr is not None:
                    # ATR % = (ATR / Close) * 100
                     df['atr_percent'] = (atr / df['close']) * 100

            print(f"[REGIME] ✅ Indicators calculated successfully", flush=True)
            return df

        except Exception as e:
            logger.error(f"Failed to calculate indicators: {e}")
            print(f"[REGIME] ❌ Indicator calculation failed: {e}", flush=True)
            return df

    def _get_chart_dataframe(self) -> "pd.DataFrame | None":
        """
        Get current DataFrame from chart.

        Override this method to provide the actual DataFrame.

        Returns:
            DataFrame with OHLCV data or None
        """
        # Try common attribute names (priority order)
        if hasattr(self, "data") and self.data is not None:
            return self.data
        if hasattr(self, "_current_df"):
            return self._current_df
        if hasattr(self, "df"):
            return self.df
        if hasattr(self, "_data"):
            return self._data
        if hasattr(self, "chart_data"):
            return self.chart_data

        return None

    def _classify_regime_from_entry_json(self, df: pd.DataFrame, json_path: str):
        """
        Lenient regime classification for Entry Analyzer JSON (v2 optimization result).

        Strips comment/extra fields that are not in the strict schema and calls
        RegimeEngineJSON.classify_from_config on a cleaned temporary JSON file.
        """
        # Load raw JSON
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Remove known extra fields that break schema validation
        for key in ["_comment_entry_expression", "_comment_entry_expression_edited", "entry_expression"]:
            if key in data:
                data.pop(key, None)

        # Also strip these keys in nested optimization_results entries
        if "optimization_results" in data:
            for opt in data.get("optimization_results", []):
                for key in ["_comment_entry_expression", "_comment_entry_expression_edited", "entry_expression"]:
                    opt.pop(key, None)

        # Write cleaned JSON to temp file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as tmp:
            json.dump(data, tmp)
            tmp_path = tmp.name

        try:
            from src.core.tradingbot.regime_engine_json import RegimeEngineJSON
            engine = RegimeEngineJSON()
            return engine.classify_from_config(df, tmp_path)
        finally:
            try:
                import os
                os.unlink(tmp_path)
            except Exception:
                pass

    def _backfill_json_regimes(self, df: pd.DataFrame, json_path: str) -> str | None:
        """
        Backfill regime lines for JSON optimizer configs using the whole DataFrame.

        Draws a line on every regime change, using regime IDs from the JSON.

        Returns:
            Last detected regime id (or None).
        """
        # 1) Load raw JSON
        with open(json_path, "r", encoding="utf-8") as f:
            raw = json.load(f)

        if "optimization_results" not in raw:
            raise ValueError("optimizer JSON missing 'optimization_results'")

        opt = next(
            (o for o in raw["optimization_results"] if o.get("applied")),
            raw["optimization_results"][0],
        )

        indicators_def = opt.get("indicators") or []
        regimes_def = opt.get("regimes") or []

        if not indicators_def or not regimes_def:
            raise ValueError("optimizer JSON missing indicators/regimes")

        # 2) Compute indicator series (full history)
        indicator_series = self._compute_indicator_series(df, indicators_def)

        # 3) Detect regime per bar (priority order)
        regimes_sorted = sorted(regimes_def, key=lambda r: r.get("priority", 0), reverse=True)

        def value_from_threshold(th_name: str, idx: int):
            base = th_name.split("_", 1)[0].lower()

            # direct match in series
            for vals in indicator_series.values():
                if th_name in vals and vals[th_name] is not None:
                    return vals[th_name].iloc[idx]
                if base in vals and vals[base] is not None:
                    return vals[base].iloc[idx]

            # type-based fallback
            adx_key = next((k for k, v in indicator_series.items() if "adx" in k.lower()), None)
            rsi_key = next((k for k, v in indicator_series.items() if "rsi" in k.lower()), None)
            atr_key = next((k for k, v in indicator_series.items() if "atr" in k.lower()), None)

            if "adx" in th_name and adx_key:
                return indicator_series[adx_key].get("adx", pd.Series()).iloc[idx]
            if "di_diff" in th_name and adx_key:
                return indicator_series[adx_key].get("di_diff", pd.Series()).iloc[idx]
            if "rsi" in th_name and rsi_key:
                return indicator_series[rsi_key].get("rsi", pd.Series()).iloc[idx]
            if "atr" in th_name and atr_key:
                if "percent" in th_name:
                    return indicator_series[atr_key].get("atr_percent", pd.Series()).iloc[idx]
                return indicator_series[atr_key].get("atr", pd.Series()).iloc[idx]
            return None

        def regime_at(idx: int):
            for regime in regimes_sorted:
                thresholds = regime.get("thresholds", [])
                active = True
                for th in thresholds:
                    th_name = th.get("name", "")
                    th_value = th.get("value")
                    current = value_from_threshold(th_name, idx)
                    if current is None or pd.isna(current) or th_value is None:
                        active = False
                        break
                    if th_name.endswith("_min"):
                        if current < th_value:
                            active = False
                            break
                    elif th_name.endswith("_max"):
                        if current > th_value:
                            active = False
                            break
                    elif "confirm_bull" in th_name or "exhaustion_min" in th_name:
                        if current < th_value:
                            active = False
                            break
                    elif "confirm_bear" in th_name or "exhaustion_max" in th_name:
                        if current > th_value:
                            active = False
                            break
                    else:
                        active = False
                        break
                if active:
                    return regime.get("id") or regime.get("name") or None
            return None

        # 4) Iterate bars and draw on changes
        last_regime = None
        change_points = []
        for i in range(len(df)):
            regime_id = regime_at(i)
            if regime_id is None:
                continue  # skip bars where no regime can be determined
            if regime_id != last_regime:
                ts_raw = df.index[i]
                if hasattr(ts_raw, "timestamp"):
                    ts_val = int(ts_raw.timestamp())
                else:
                    ts_val = int(ts_raw)
                change_points.append((ts_val, regime_id))
                last_regime = regime_id

        # 5) Clear existing and draw all lines
        if hasattr(self, "clear_regime_lines"):
            self.clear_regime_lines()
        for ts_val, regime_id in change_points:
            line_id = f"regime_{regime_id}_{ts_val}"
            if hasattr(self, "add_regime_line"):
                self.add_regime_line(
                    line_id=line_id,
                    timestamp=ts_val,
                    regime_name=regime_id,
                    label=regime_id
                )

        return last_regime

    def _compute_indicator_series(self, df: pd.DataFrame, indicators_def: list[dict]):
        """Compute pandas Series for all indicators defined in the optimizer JSON."""
        indicator_series: dict[str, dict[str, pd.Series]] = {}

        for ind in indicators_def:
            name = ind.get("name")
            ind_type = (ind.get("type") or "").upper()
            params = ind.get("params") or []

            def _param(pname, default=None):
                for p in params:
                    if p.get("name") == pname:
                        return p.get("value", default)
                return default

            if not name or not ind_type:
                raise ValueError("Indicator definition missing name or type")

            if ind_type == "ADX":
                period = int(_param("period", 14))
                adx_res = ta.adx(df["high"], df["low"], df["close"], length=period)
                if adx_res is None or adx_res.empty:
                    raise ValueError(f"Indicator {name} (ADX) produced no data")
                adx_col = next((c for c in adx_res.columns if "ADX" in c.upper()), None)
                dmp_col = next((c for c in adx_res.columns if "DMP" in c.upper()), None)
                dmn_col = next((c for c in adx_res.columns if "DMN" in c.upper()), None)
                adx_series = adx_res[adx_col] if adx_col else pd.Series([None]*len(df), index=df.index)
                di_diff = None
                if dmp_col and dmn_col:
                    di_diff = (adx_res[dmp_col] - adx_res[dmn_col]).abs()
                indicator_series[name] = {
                    "adx": adx_series,
                    "di_diff": di_diff if di_diff is not None else pd.Series([None]*len(df), index=df.index),
                }

            elif ind_type == "RSI":
                period = int(_param("period", 14))
                rsi_res = ta.rsi(df["close"], length=period)
                if rsi_res is None or rsi_res.empty:
                    raise ValueError(f"Indicator {name} (RSI) produced no data")
                indicator_series[name] = {"rsi": rsi_res}

            elif ind_type == "ATR":
                period = int(_param("period", 14))
                atr_res = ta.atr(df["high"], df["low"], df["close"], length=period)
                if atr_res is None or atr_res.empty:
                    raise ValueError(f"Indicator {name} (ATR) produced no data")
                close_series = df["close"]
                atr_pct = (atr_res / close_series) * 100
                indicator_series[name] = {"atr": atr_res, "atr_percent": atr_pct}

            elif ind_type == "EMA":
                period = int(_param("period", 20))
                ema_res = ta.ema(df["close"], length=period)
                if ema_res is None or ema_res.empty:
                    raise ValueError(f"Indicator {name} (EMA) produced no data")
                indicator_series[name] = {"value": ema_res}

            elif ind_type == "SMA":
                period = int(_param("period", 20))
                sma_res = ta.sma(df["close"], length=period)
                if sma_res is None or sma_res.empty:
                    raise ValueError(f"Indicator {name} (SMA) produced no data")
                indicator_series[name] = {"value": sma_res}

            elif ind_type == "MACD":
                fast = int(_param("fast", 12))
                slow = int(_param("slow", 26))
                signal = int(_param("signal", 9))
                macd_res = ta.macd(df["close"], fast=fast, slow=slow, signal=signal)
                if macd_res is None or macd_res.empty:
                    raise ValueError(f"Indicator {name} (MACD) produced no data")
                macd_col = next((c for c in macd_res.columns if "MACD" in c.upper() and "SIGNAL" not in c.upper() and "HIST" not in c.upper()), None)
                signal_col = next((c for c in macd_res.columns if "SIGNAL" in c.upper()), None)
                hist_col = next((c for c in macd_res.columns if "HIST" in c.upper()), None)
                indicator_series[name] = {
                    "macd": macd_res[macd_col] if macd_col else pd.Series([None]*len(df), index=df.index),
                    "signal": macd_res[signal_col] if signal_col else pd.Series([None]*len(df), index=df.index),
                    "hist": macd_res[hist_col] if hist_col else pd.Series([None]*len(df), index=df.index),
                }

            elif ind_type == "BB":
                length = int(_param("period", 20))
                mult = float(_param("mult", 2.0))
                bb_res = ta.bbands(df["close"], length=length, std=mult)
                if bb_res is None or bb_res.empty:
                    raise ValueError(f"Indicator {name} (BB) produced no data")
                upper = next((c for c in bb_res.columns if "UPPER" in c.upper()), None)
                lower = next((c for c in bb_res.columns if "LOWER" in c.upper()), None)
                mid = next((c for c in bb_res.columns if "MID" in c.upper() or "MIDDLE" in c.upper()), None)
                width = next((c for c in bb_res.columns if "WIDTH" in c.upper()), None)
                indicator_series[name] = {
                    "upper": bb_res[upper] if upper else pd.Series([None]*len(df), index=df.index),
                    "lower": bb_res[lower] if lower else pd.Series([None]*len(df), index=df.index),
                    "middle": bb_res[mid] if mid else pd.Series([None]*len(df), index=df.index),
                    "width": bb_res[width] if width else pd.Series([None]*len(df), index=df.index),
                }

            elif ind_type == "STOCH":
                k = int(_param("k", 14))
                d = int(_param("d", 3))
                stoch_res = ta.stoch(df["high"], df["low"], df["close"], k=k, d=d)
                if stoch_res is None or stoch_res.empty:
                    raise ValueError(f"Indicator {name} (STOCH) produced no data")
                k_col = next((c for c in stoch_res.columns if "K" in c.upper()), None)
                d_col = next((c for c in stoch_res.columns if "D" in c.upper()), None)
                indicator_series[name] = {
                    "k": stoch_res[k_col] if k_col else pd.Series([None]*len(df), index=df.index),
                    "d": stoch_res[d_col] if d_col else pd.Series([None]*len(df), index=df.index),
                }

            elif ind_type == "MFI":
                period = int(_param("period", 14))
                mfi_res = ta.mfi(df["high"], df["low"], df["close"], df["volume"], length=period)
                if mfi_res is None or mfi_res.empty:
                    raise ValueError(f"Indicator {name} (MFI) produced no data")
                indicator_series[name] = {"mfi": mfi_res}

            elif ind_type == "CCI":
                period = int(_param("period", 20))
                cci_res = ta.cci(df["high"], df["low"], df["close"], length=period)
                if cci_res is None or cci_res.empty:
                    raise ValueError(f"Indicator {name} (CCI) produced no data")
                indicator_series[name] = {"cci": cci_res}

            elif ind_type == "CHOP":
                length = int(_param("period", 14))
                chop_res = ta.chop(df["high"], df["low"], df["close"], length=length)
                if chop_res is None or chop_res.empty:
                    raise ValueError(f"Indicator {name} (CHOP) produced no data")
                indicator_series[name] = {"chop": chop_res}

            else:
                raise ValueError(f"Unsupported indicator type in optimizer JSON: {ind_type}")

        return indicator_series

    def _show_regime_error_popup(self, message: str) -> None:
        """Show a blocking popup with regime error info."""
        try:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(None, "Regime JSON Fehler", message)
        except Exception:
            logger.error(f"Failed to show regime error popup: {message}")

    def set_regime_manually(
        self,
        regime: str,
        adx: float | None = None,
        gate_reason: str = "",
        allows_entry: bool = True,
    ) -> None:
        """
        Set regime manually (e.g., from MarketContext).

        Args:
            regime: Regime type string
            adx: Optional ADX value
            gate_reason: Reason for blocking entries
            allows_entry: Whether market entries are allowed
        """
        if self._regime_badge:
            self._regime_badge.set_regime(regime, adx, gate_reason, allows_entry)

    def set_regime_from_context(self, context) -> None:
        """
        Set regime from MarketContext.

        Args:
            context: MarketContext object
        """
        if context is None:
            if self._regime_badge:
                self._regime_badge.set_regime("UNKNOWN")
            return

        regime_str = context.regime.value if hasattr(context.regime, "value") else str(context.regime)
        self.set_regime_manually(
            regime=regime_str,
            adx=context.indicators.adx if context.indicators else None,
            gate_reason="",  # Gate reason not stored in MarketContext
            allows_entry=context.is_valid_for_trading(),
        )

    def get_current_regime(self) -> str | None:
        """
        Get current regime type.

        Returns:
            Regime type string or None
        """
        if self._regime_badge:
            return self._regime_badge.get_regime()
        return None

    def _on_regime_badge_clicked(self) -> None:
        """Handle regime badge click - show details."""
        logger.debug("Regime badge clicked")
        # Could open a details dialog or show extended info
        # For now, just log

    def _on_regime_changed(self, regime: str) -> None:
        """
        Handle regime change event.

        Args:
            regime: New regime type
        """
        logger.info(f"Regime changed to: {regime}")
        # Emit signal or notify other components if needed

    def _draw_regime_line_for_change(self, regime_name: str, df: "pd.DataFrame") -> None:
        """Draw regime line in chart when regime changes.

        Called by trigger_regime_analysis() when a regime change is detected.

        Args:
            regime_name: New regime name
            df: Current chart dataframe
        """
        print(f"[REGIME] _draw_regime_line_for_change called for {regime_name}", flush=True)

        # Check if chart has add_regime_line method (from BotOverlayMixin)
        if not hasattr(self, 'add_regime_line'):
            logger.warning("❌ Chart has no add_regime_line method - skipping regime line drawing")
            print("[REGIME] ❌ No add_regime_line method!", flush=True)
            return

        print(f"[REGIME] ✅ add_regime_line method exists", flush=True)

        try:
            # Get last candle timestamp
            if df is None or df.empty:
                print("[REGIME] ❌ DataFrame is None or empty!", flush=True)
                return

            print(f"[REGIME] DataFrame has {len(df)} rows", flush=True)

            if 'timestamp' in df.columns:
                last_timestamp = df.iloc[-1]['timestamp']
            elif 'time' in df.columns:
                last_timestamp = df.iloc[-1]['time']
            else:
                last_timestamp = df.index[-1]
            print(f"[REGIME] Last timestamp (raw): {last_timestamp}", flush=True)

            # Safe timestamp conversion
            if hasattr(last_timestamp, 'timestamp'):
                ts_value = last_timestamp.timestamp()
            else:
                try:
                    ts_value = float(last_timestamp)
                except (ValueError, TypeError):
                    logger.error(f"Cannot convert timestamp {last_timestamp} to float")
                    print(f"[REGIME] ❌ Cannot convert timestamp {last_timestamp}", flush=True)
                    return

            # Convert to seconds (not ms)
            if ts_value > 1e12:  # nanoseconds
                last_timestamp = int(ts_value / 1_000_000_000)
            elif ts_value > 1e10:  # milliseconds
                last_timestamp = int(ts_value / 1000)
            else:
                last_timestamp = int(ts_value)

            print(f"[REGIME] Last timestamp (converted): {last_timestamp}", flush=True)

            # Generate unique line ID
            import time
            line_id = f"regime_{regime_name}_{int(time.time())}"

            print(f"[REGIME] 🎨 Drawing line: {line_id} at {last_timestamp}", flush=True)

            # Draw line using BotOverlayMixin API
            self.add_regime_line(
                line_id=line_id,
                timestamp=last_timestamp,
                regime_name=regime_name,
                color=None,  # Auto-select color
                label=regime_name
            )
            logger.info(f"✅ Drew regime line for {regime_name} at timestamp {last_timestamp}")
            print(f"[REGIME] ✅ Line drawn successfully!", flush=True)

        except Exception as e:
            logger.error(f"❌ Failed to draw regime line: {e}", exc_info=True)
            print(f"[REGIME] ❌ Error drawing line: {e}", flush=True)

    def get_regime_badge_widget(self):
        """
        Get the regime badge widget for external use.

        Returns:
            RegimeBadgeWidget or None
        """
        return self._regime_badge
