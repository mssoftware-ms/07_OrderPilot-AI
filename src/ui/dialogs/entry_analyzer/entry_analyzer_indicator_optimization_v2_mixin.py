"""Entry Analyzer - Indicator Optimization V2 Mixin (Rebuilt for Indicator Sets).

Optimiert Long/Short Entry/Exit-Indikatorensets ohne Regime-Abhängigkeit.
- Datenquelle wählbar: Live-Chart oder Historical SQLite (BTCUSDT 1m, 365d)
- Max-Trials Feld (hartes Limit 1000)
- Fortschrittsbalken pro Signal-Typ, Live-Results-Tabelle
"""

from __future__ import annotations

import json
import logging
import sqlite3
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.ui.icons import get_icon

if TYPE_CHECKING:
    from PyQt6.QtCore import QThread

logger = logging.getLogger(__name__)


class IndicatorOptimizationV2Mixin:
    """Stage 2: Indicator Optimization Execution (Indicators only)."""

    # Injected from parent
    _ind_v2_signal_types: dict[str, QCheckBox]
    _ind_v2_params_table: QTableWidget
    _ind_v2_indicator_config: dict | None
    _ind_v2_start_btn: QPushButton
    _ind_v2_stop_btn: QPushButton
    _ind_v2_signal_progress: dict[str, QProgressBar]
    _ind_v2_live_results_table: QTableWidget
    _ind_v2_worker: QThread | None
    _ind_v2_optimization_results: dict
    _ind_v2_max_trials: QSpinBox
    _ind_v2_source_live: QRadioButton
    _ind_v2_source_hist: QRadioButton
    _ind_v2_historical_cache: list | None
    _candles: list[dict]
    _symbol: str
    _timeframe: str

    def _setup_indicator_optimization_v2_tab(self, tab: QWidget) -> None:
        """Setup Indicator Optimization tab (Indicators only)."""
        layout = QVBoxLayout(tab)

        # ===== Controls =====
        control_layout = QHBoxLayout()

        source_group = QGroupBox("Data Source")
        source_layout = QHBoxLayout(source_group)
        self._ind_v2_source_live = QRadioButton("Live Chart")
        self._ind_v2_source_hist = QRadioButton("Historical (SQLite)")
        self._ind_v2_source_live.setChecked(True)
        source_layout.addWidget(self._ind_v2_source_live)
        source_layout.addWidget(self._ind_v2_source_hist)
        source_layout.addStretch()
        control_layout.addWidget(source_group)

        control_layout.addWidget(QLabel("Max Trials"))
        self._ind_v2_max_trials = QSpinBox()
        self._ind_v2_max_trials.setRange(0, 10000)
        self._ind_v2_max_trials.setValue(150)
        self._ind_v2_max_trials.setToolTip("Maximale Kombinationen/Loops (0 = unbegrenzt, 10-10000)")
        control_layout.addWidget(self._ind_v2_max_trials)

        # Optimization mode
        mode_group = QGroupBox("Mode")
        mode_layout = QHBoxLayout(mode_group)
        self._ind_v2_mode_global = QRadioButton("Global (bisher)")
        self._ind_v2_mode_best = QRadioButton("Pro Indikator (fair share)")
        self._ind_v2_mode_global.setChecked(True)
        mode_layout.addWidget(self._ind_v2_mode_global)
        mode_layout.addWidget(self._ind_v2_mode_best)
        mode_layout.addStretch()
        control_layout.addWidget(mode_group)

        control_layout.addStretch()

        self._ind_v2_start_btn = QPushButton(" Start Optimization")
        self._ind_v2_start_btn.setIcon(get_icon("play_arrow"))
        self._ind_v2_start_btn.setProperty("class", "success")
        self._ind_v2_start_btn.clicked.connect(self._on_start_indicator_v2_optimization)
        control_layout.addWidget(self._ind_v2_start_btn)

        self._ind_v2_stop_btn = QPushButton(" Stop")
        self._ind_v2_stop_btn.setIcon(get_icon("stop"))
        self._ind_v2_stop_btn.setProperty("class", "danger")
        self._ind_v2_stop_btn.setEnabled(False)
        self._ind_v2_stop_btn.clicked.connect(self._on_stop_indicator_v2_optimization)
        control_layout.addWidget(self._ind_v2_stop_btn)

        layout.addLayout(control_layout)

        # ===== Progress Group =====
        progress_group = QGroupBox("Optimization Progress (Per Signal Type)")
        progress_layout = QFormLayout(progress_group)

        self._ind_v2_signal_progress = {}
        signal_labels = {
            "entry_long": "Entry Long:",
            "entry_short": "Entry Short:",
            "exit_long": "Exit Long:",
            "exit_short": "Exit Short:",
        }

        for signal_type, label in signal_labels.items():
            progress_bar = QProgressBar()
            progress_bar.setFormat("%p% (%v/%m)")
            progress_bar.setTextVisible(True)
            self._ind_v2_signal_progress[signal_type] = progress_bar
            progress_layout.addRow(label, progress_bar)

        layout.addWidget(progress_group)

        # ===== Best-Set Table =====
        best_label = QLabel("<b>Best per Indicator (Set)</b>")
        layout.addWidget(best_label)
        self._ind_v2_best_set_table = QTableWidget()
        self._ind_v2_best_set_table.setColumnCount(6)
        self._ind_v2_best_set_table.setHorizontalHeaderLabels(
            ["Signal", "Indicator", "Score", "Win%", "PF", "Params"]
        )
        best_header = self._ind_v2_best_set_table.horizontalHeader()
        if best_header:
            best_header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        self._ind_v2_best_set_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self._ind_v2_best_set_table.setAlternatingRowColors(True)
        layout.addWidget(self._ind_v2_best_set_table)

        self._ind_v2_export_btn = QPushButton("Export Best Set (JSON)")
        self._ind_v2_export_btn.setIcon(get_icon("save"))
        self._ind_v2_export_btn.clicked.connect(self._on_export_best_set)
        self._ind_v2_export_btn.setEnabled(False)
        layout.addWidget(self._ind_v2_export_btn)

        # ===== Live Results Table =====
        results_label = QLabel("<b>Live Results (Auto-Updated)</b>")
        layout.addWidget(results_label)

        self._ind_v2_live_results_table = QTableWidget()
        self._ind_v2_live_results_table.setColumnCount(8)
        self._ind_v2_live_results_table.setHorizontalHeaderLabels(
            [
                "Signal Type",
                "Indicator",
                "Score",
                "Win Rate",
                "Profit Factor",
                "Sharpe",
                "Trades",
                "Parameters",
            ]
        )

        header = self._ind_v2_live_results_table.horizontalHeader()
        if header:
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(7, QHeaderView.ResizeMode.Stretch)

        self._ind_v2_live_results_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self._ind_v2_live_results_table.setAlternatingRowColors(True)
        self._ind_v2_live_results_table.setSortingEnabled(True)

        layout.addWidget(self._ind_v2_live_results_table)

        # State
        self._ind_v2_worker = None
        self._ind_v2_optimization_results = {}
        self._ind_v2_historical_cache = None
        self._ind_v2_best_set_data: dict[str, list[dict]] = {}
        self._ind_v2_last_param_ranges: dict | None = None

    # ------------------------------------------------------------------ Actions
    def _on_start_indicator_v2_optimization(self) -> None:
        """Handle start optimization click."""
        enabled_signal_types = [
            s for s, cb in self._ind_v2_signal_types.items() if cb.isChecked()
        ]
        if not enabled_signal_types:
            QMessageBox.warning(self, "No Signal Types", "Select at least one signal type.")
            return

        if not getattr(self, "_ind_v2_indicator_config", None):
            QMessageBox.warning(
                self, "No Indicator Config", "Load an indicator config in Tab 4 first."
            )
            return

        if not hasattr(self, "_get_indicator_param_ranges"):
            QMessageBox.critical(self, "Missing method", "Parameter reader missing.")
            return
        param_ranges = self._get_indicator_param_ranges()
        selected_indicators = list(param_ranges.keys())
        if not selected_indicators:
            QMessageBox.warning(self, "No Parameters", "Please fill parameter ranges in Tab 4.")
            return

        # Candles source
        if self._ind_v2_source_live.isChecked():
            candles = getattr(self, "_candles", None) or []
            if not candles:
                QMessageBox.warning(self, "No Chart Data", "Load chart data before optimizing.")
                return
        else:
            candles = self._load_indicator_hist_candles()
            if not candles:
                QMessageBox.warning(self, "No Historical Data", "Historical dataset not available.")
                return

        max_trials = self._ind_v2_max_trials.value()

        config = {
            "signal_types": enabled_signal_types,
            "indicators": selected_indicators,
            "param_ranges": param_ranges,
            "symbol": getattr(self, "_symbol", "BTCUSDT"),
            "timeframe": getattr(self, "_timeframe", "1m"),
            "candles": candles,
            "max_trials": max_trials,
            "mode_best_per_indicator": self._ind_v2_mode_best.isChecked(),
        }

        from src.ui.dialogs.entry_analyzer.entry_analyzer_indicator_worker import (
            IndicatorOptimizationWorkerV2,
        )

        self._ind_v2_worker = IndicatorOptimizationWorkerV2(config, parent=self)
        self._ind_v2_worker.progress.connect(self._on_indicator_v2_progress)
        self._ind_v2_worker.result_ready.connect(self._on_indicator_v2_result)
        self._ind_v2_worker.best_set_ready.connect(self._on_indicator_v2_best_set)
        self._ind_v2_worker.finished.connect(self._on_indicator_v2_finished)
        self._ind_v2_worker.error.connect(self._on_indicator_v2_error)

        # Reset UI
        for _, progress_bar in self._ind_v2_signal_progress.items():
            progress_bar.setMaximum(max_trials)
            progress_bar.setValue(0)
            progress_bar.setEnabled(True)

        self._ind_v2_live_results_table.setRowCount(0)
        self._ind_v2_optimization_results = {}
        self._ind_v2_best_set_data = {}
        self._ind_v2_last_param_ranges = param_ranges
        self._ind_v2_best_set_table.setRowCount(0)
        self._ind_v2_export_btn.setEnabled(False)
        self._ind_v2_start_btn.setEnabled(False)
        self._ind_v2_stop_btn.setEnabled(True)

        self._ind_v2_worker.start()
        logger.info(
            "Started indicator optimization: signals=%s, indicators=%s, max_trials=%s, source=%s",
            enabled_signal_types,
            selected_indicators,
            max_trials,
            "live" if self._ind_v2_source_live.isChecked() else "historical",
        )

    def _on_stop_indicator_v2_optimization(self) -> None:
        """Stop worker gracefully."""
        if self._ind_v2_worker and self._ind_v2_worker.isRunning():
            self._ind_v2_worker.stop()
            logger.info("Requested Stage 2 optimization stop")

    # ------------------------------------------------------------------ Worker Callbacks
    def _on_indicator_v2_progress(
        self, signal_type: str, current: int, total: int, best_score: float
    ) -> None:
        if signal_type in self._ind_v2_signal_progress:
            progress_bar = self._ind_v2_signal_progress[signal_type]
            if progress_bar.maximum() != total:
                progress_bar.setMaximum(total)
            progress_bar.setValue(current)
            progress_bar.setFormat(f"%p% ({current}/{total}) - Best: {best_score:.1f}")

    def _on_indicator_v2_result(self, signal_type: str, result: dict) -> None:
        if signal_type not in self._ind_v2_optimization_results:
            self._ind_v2_optimization_results[signal_type] = []
        self._ind_v2_optimization_results[signal_type].append(result)

        row = self._ind_v2_live_results_table.rowCount()
        self._ind_v2_live_results_table.insertRow(row)
        self._ind_v2_live_results_table.setItem(
            row, 0, QTableWidgetItem(signal_type.replace("_", " ").title())
        )
        self._ind_v2_live_results_table.setItem(
            row, 1, QTableWidgetItem(result.get("indicator", "N/A"))
        )

        score = result.get("score", 0.0)
        score_item = QTableWidgetItem(f"{score:.1f}")
        score_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        if score >= 70:
            score_item.setBackground(Qt.GlobalColor.green)
        elif score >= 50:
            score_item.setBackground(Qt.GlobalColor.yellow)
        else:
            score_item.setBackground(Qt.GlobalColor.red)
        self._ind_v2_live_results_table.setItem(row, 2, score_item)

        win_rate = result.get("win_rate", 0.0)
        self._ind_v2_live_results_table.setItem(row, 3, QTableWidgetItem(f"{win_rate:.1%}"))

        profit_factor = result.get("profit_factor", 0.0)
        self._ind_v2_live_results_table.setItem(
            row, 4, QTableWidgetItem(f"{profit_factor:.2f}")
        )

        sharpe = result.get("sharpe_ratio", 0.0)
        self._ind_v2_live_results_table.setItem(row, 5, QTableWidgetItem(f"{sharpe:.2f}"))

        trades = result.get("trades", 0)
        self._ind_v2_live_results_table.setItem(row, 6, QTableWidgetItem(str(trades)))

        params = result.get("params", {})
        params_str = ", ".join([f"{k}={v}" for k, v in params.items()])
        self._ind_v2_live_results_table.setItem(row, 7, QTableWidgetItem(params_str))
        self._ind_v2_live_results_table.scrollToBottom()

    def _on_indicator_v2_best_set(self, signal_type: str, best_list: list[dict]) -> None:
        """Display best-per-indicator set for a signal type."""
        # Remove rows of this signal_type to avoid duplicates
        to_keep = []
        for r in range(self._ind_v2_best_set_table.rowCount()):
            if self._ind_v2_best_set_table.item(r, 0).text() != signal_type:
                row_data = []
                for c in range(self._ind_v2_best_set_table.columnCount()):
                    itm = self._ind_v2_best_set_table.item(r, c)
                    row_data.append(itm.text() if itm else "")
                to_keep.append(row_data)

        self._ind_v2_best_set_table.setRowCount(0)
        # Re-add kept rows
        for row_data in to_keep:
            r = self._ind_v2_best_set_table.rowCount()
            self._ind_v2_best_set_table.insertRow(r)
            for c, val in enumerate(row_data):
                self._ind_v2_best_set_table.setItem(r, c, QTableWidgetItem(val))

        # Add new best set rows
        for res in best_list:
            r = self._ind_v2_best_set_table.rowCount()
            self._ind_v2_best_set_table.insertRow(r)
            self._ind_v2_best_set_table.setItem(r, 0, QTableWidgetItem(signal_type))
            self._ind_v2_best_set_table.setItem(
                r, 1, QTableWidgetItem(res.get("indicator", ""))
            )
            score = res.get("score", 0.0)
            self._ind_v2_best_set_table.setItem(r, 2, QTableWidgetItem(f"{score:.1f}"))
            win_rate = res.get("win_rate", 0.0)
            self._ind_v2_best_set_table.setItem(r, 3, QTableWidgetItem(f"{win_rate:.1%}"))
            pf = res.get("profit_factor", 0.0)
            self._ind_v2_best_set_table.setItem(r, 4, QTableWidgetItem(f"{pf:.2f}"))
            params = res.get("params", {})
            params_str = ", ".join([f"{k}={v}" for k, v in params.items()])
            self._ind_v2_best_set_table.setItem(r, 5, QTableWidgetItem(params_str))
        self._ind_v2_best_set_table.scrollToBottom()
        if best_list:
            self._ind_v2_best_set_data[signal_type] = best_list
        if self._ind_v2_best_set_data:
            self._ind_v2_export_btn.setEnabled(True)

    def _on_export_best_set(self) -> None:
        """Export current best set to JSON using the template format."""
        if not self._ind_v2_best_set_data:
            QMessageBox.warning(self, "No Data", "Keine Best-Set-Daten zum Export.")
            return

        selected_row = self._ind_v2_best_set_table.currentRow()
        selected_rank = selected_row + 1 if selected_row >= 0 else 1

        symbol = getattr(self, "_symbol", "BTCUSDT")
        timeframe = getattr(self, "_timeframe", "1m")
        mode = "best_per_indicator" if self._ind_v2_mode_best.isChecked() else "global"

        # Build JSON payload
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)
        timestamp_str = now.strftime("%y%m%d%H%M%S")
        filename = (
            f"{timestamp_str}_INDICATOR_optimization_results_"
            f"{symbol}_{timeframe}_#{selected_rank}.json"
        )

        payload = {
            "schema_version": "1.0.0",
            "metadata": {
                "author": "OrderPilot-AI",
                "created_at": now.isoformat().replace("+00:00", "Z"),
                "updated_at": now.isoformat().replace("+00:00", "Z"),
                "symbol": symbol,
                "timeframe": timeframe,
                "source": "indicator_optimization_v2",
                "mode": mode,
                "notes": "Auto-exported best indicator set",
            },
            "signal_sets": [],
        }

        for signal_type, best_list in self._ind_v2_best_set_data.items():
            indicators_payload = []
            for res in best_list:
                params_payload = []
                params = res.get("params", {})
                for pname, pval in params.items():
                    range_obj = None
                    if self._ind_v2_last_param_ranges and res.get("indicator") in self._ind_v2_last_param_ranges:
                        rng = self._ind_v2_last_param_ranges[res["indicator"]].get(pname)
                        if rng:
                            rng_min = rng.get("min")
                            rng_max = rng.get("max")
                            rng_step = rng.get("step")
                            if rng_min is not None and rng_max is not None and rng_step is not None:
                                range_obj = {
                                    "min": rng_min,
                                    "max": rng_max,
                                    "step": rng_step,
                                }
                    param_entry = {"name": pname, "value": pval}
                    if range_obj:
                        param_entry["range"] = range_obj
                    params_payload.append(param_entry)

                indicators_payload.append(
                    {
                        "name": res.get("indicator", ""),
                        "params": params_payload,
                        "score": res.get("score", 0.0),
                        "win_rate": res.get("win_rate", 0.0),
                        "profit_factor": res.get("profit_factor", 0.0),
                    }
                )

            payload["signal_sets"].append(
                {
                    "signal_type": signal_type,
                    "indicators": indicators_payload,
                }
            )

        target_dir = Path(__file__).parents[4] / "03_JSON" / "Trading_Indicatorsets"
        try:
            target_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:  # pragma: no cover - UI feedback
            QMessageBox.critical(self, "Export Fehler", f"Kann Zielordner nicht erstellen:\n{e}")
            return

        target_path = target_dir / filename
        try:
            target_path.write_text(
                self._json_dumps(payload), encoding="utf-8"
            )
        except Exception as e:  # pragma: no cover - UI feedback
            QMessageBox.critical(self, "Export Fehler", f"Konnte Datei nicht speichern:\n{e}")
            return

        QMessageBox.information(
            self,
            "Export erfolgreich",
            f"Best-Set exportiert nach:\n{target_path}",
        )

    @staticmethod
    def _json_dumps(payload: dict) -> str:
        """Compact JSON dumper with UTF-8 support."""
        return json.dumps(payload, ensure_ascii=False, indent=2)

    def _on_indicator_v2_finished(self, all_results: dict) -> None:
        self._ind_v2_start_btn.setEnabled(True)
        self._ind_v2_stop_btn.setEnabled(False)

        for signal_type, progress_bar in self._ind_v2_signal_progress.items():
            if signal_type in all_results:
                progress_bar.setValue(progress_bar.maximum())

        total_results = sum(len(v) for v in all_results.values())
        best_overall = None
        best_score = 0.0
        for signal_type, results in all_results.items():
            if results:
                best_in_type = max(results, key=lambda r: r.get("score", 0.0))
                if best_in_type.get("score", 0.0) > best_score:
                    best_score = best_in_type["score"]
                    best_overall = (signal_type, best_in_type)

        msg = f"Optimization Complete!\nTotal Results: {total_results}\n"
        if best_overall:
            signal_type, best_result = best_overall
            msg += (
                f"\nBest:\n"
                f"• Signal: {signal_type.replace('_', ' ').title()}\n"
                f"• Indicator: {best_result.get('indicator', 'N/A')}\n"
                f"• Score: {best_result.get('score', 0.0):.1f}\n"
                f"• Win Rate: {best_result.get('win_rate', 0.0):.1%}\n"
                f"• Profit Factor: {best_result.get('profit_factor', 0.0):.2f}"
            )

        QMessageBox.information(self, "Optimization Complete", msg)
        logger.info("Stage 2 optimization completed with %s total results", total_results)
        if hasattr(self, "_load_indicator_v2_results"):
            self._load_indicator_v2_results()

    def _on_indicator_v2_error(self, error_message: str) -> None:
        self._ind_v2_start_btn.setEnabled(True)
        self._ind_v2_stop_btn.setEnabled(False)
        QMessageBox.critical(
            self,
            "Optimization Error",
            f"An error occurred during optimization:\n\n{error_message}",
        )
        logger.error("Stage 2 optimization error: %s", error_message)

    # ------------------------------------------------------------------ Data Loading
    def _load_indicator_hist_candles(self) -> List[Dict]:
        """Load historical candles from SQLite (default BTCUSDT 1m, 365d)."""
        if self._ind_v2_historical_cache is not None:
            return self._ind_v2_historical_cache

        project_root = Path(__file__).parents[4]
        db_path = project_root / "data" / "orderpilot_historical.db"
        if not db_path.exists():
            logger.warning("Historical DB not found: %s", db_path)
            return []

        try:
            conn = sqlite3.connect(db_path)
            cur = conn.cursor()
            symbol = getattr(self, "_symbol", "BTCUSDT")
            if ":" not in symbol:
                symbol = f"bitunix:{symbol}"
            cur.execute(
                """
                SELECT timestamp, open, high, low, close, volume
                FROM market_bars
                WHERE symbol = ?
                ORDER BY timestamp
                """,
                (symbol,),
            )
            rows = cur.fetchall()
            conn.close()
        except Exception as e:
            logger.error("Failed to load historical bars: %s", e, exc_info=True)
            return []

        candles = []
        for ts, o, h, l, c, v in rows:
            candles.append(
                {
                    "timestamp": ts,
                    "open": float(o),
                    "high": float(h),
                    "low": float(l),
                    "close": float(c),
                    "volume": float(v),
                }
            )

        self._ind_v2_historical_cache = candles
        logger.info("Loaded %s historical candles from SQLite", len(candles))
        return candles

    def _on_export_best_set(self) -> None:
        """Export the best indicator set to JSON file."""
        from PyQt6.QtWidgets import QFileDialog
        import json
        from datetime import datetime

        # Check if we have results
        if not hasattr(self, "_ind_v2_best_results") or not self._ind_v2_best_results:
            QMessageBox.warning(
                self,
                "No Results",
                "No optimization results to export. Run optimization first."
            )
            return

        # Default filename
        symbol = getattr(self, "_current_symbol", "BTCUSDT")
        timeframe = getattr(self, "_current_timeframe", "5m")
        timestamp = datetime.now().strftime("%y%m%d%H%M%S")
        default_name = f"{timestamp}_indicator_best_set_{symbol}_{timeframe}.json"

        # Get save path
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Best Indicator Set",
            default_name,
            "JSON Files (*.json)"
        )

        if not file_path:
            return

        try:
            # Build export data
            export_data = {
                "schema_version": "2.0.0",
                "metadata": {
                    "author": "OrderPilot-AI",
                    "created_at": datetime.utcnow().isoformat() + "Z",
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "type": "indicator_optimization_results"
                },
                "best_results": self._ind_v2_best_results
            }

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)

            logger.info(f"Exported best indicator set to: {file_path}")
            QMessageBox.information(
                self,
                "Export Successful",
                f"Best indicator set exported to:\n{file_path}"
            )

        except Exception as e:
            logger.error(f"Failed to export best set: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Export Failed",
                f"Failed to export best indicator set:\n{str(e)}"
            )
