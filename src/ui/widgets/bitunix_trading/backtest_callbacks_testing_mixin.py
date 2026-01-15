from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QGroupBox,
    QTableWidget, QTableWidgetItem, QTextEdit, QSpinBox, QDoubleSpinBox,
    QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFormLayout,
    QMessageBox, QFileDialog, QProgressBar, QTabWidget, QLineEdit,
    QHeaderView,
)

if TYPE_CHECKING:
    from src.core.market_data.history_provider import HistoryManager

logger = logging.getLogger(__name__)

class BacktestCallbacksTestingMixin:
    """Backtest and optimization testing callbacks"""

    def _on_batch_btn_clicked(self) -> None:
        """Synchroner Button-Handler, startet async Batch-Test."""
        logger.info("🔄 _on_batch_btn_clicked() - starting batch worker")
        self._log("🔄 Batch-Test wird gestartet...")

        if self._is_running:
            self._log("⚠️ Batch läuft bereits")
            return

        # Parse parameter space aus UI
        param_space_text = self.param_space_text.toPlainText().strip()
        if not param_space_text:
            param_space = {
                "risk_per_trade_pct": [0.5, 1.0, 1.5, 2.0],
                "max_leverage": [5, 10, 20],
            }
            self._log("⚠️ Kein Parameter Space angegeben, verwende Standard")
        else:
            try:
                param_space = json.loads(param_space_text)
            except json.JSONDecodeError as exc:
                self._log(f"❌ Ungültiges JSON: {exc}")
                QMessageBox.critical(self, "Fehler", f"Ungültiges JSON für Parameter Space:\n{exc}")
                return

        try:
            base_config = self._build_backtest_config()
        except Exception as exc:
            logger.exception("Failed to build backtest config")
            self._log(f"❌ Fehler beim Erstellen der Backtest-Config: {exc}")
            QMessageBox.critical(self, "Backtest Fehler", str(exc))
            return

        # Determine search method
        method_text = self.batch_method.currentText()
        from src.core.backtesting import BatchConfig, SearchMethod

        if "Grid" in method_text:
            search_method = SearchMethod.GRID
        elif "Random" in method_text:
            search_method = SearchMethod.RANDOM
        else:
            search_method = SearchMethod.BAYESIAN

        # Determine target metric
        target_text = self.batch_target.currentText()
        target_map = {
            "Expectancy": "expectancy",
            "Profit Factor": "profit_factor",
            "Sharpe Ratio": "sharpe_ratio",
            "Min Drawdown": "max_drawdown_pct",
        }
        target_metric = target_map.get(target_text, "expectancy")
        minimize = "Drawdown" in target_text

        batch_config = BatchConfig(
            base_config=base_config,
            parameter_space=param_space,
            search_method=search_method,
            target_metric=target_metric,
            minimize=minimize,
            max_iterations=self.batch_iterations.value(),
        )

        self._log("🧭 Batch-Konfiguration erstellt")
        self._log(f"🔄 Methode: {search_method.value}")
        self._log(f"📊 Zielmetrik: {target_metric}, Iterationen: {batch_config.max_iterations}")
        self._log(f"📋 Parameter Space: {list(param_space.keys()) or ['default']}")

        # Versuche Chart-Daten zu nutzen (User Request)
        initial_data = None
        try:
            chart_window = self._find_chart_window()
            if chart_window and hasattr(chart_window, 'chart_widget') and chart_window.chart_widget.data is not None:
                chart_data = chart_window.chart_widget.data
                if not chart_data.empty:
                    # Kopie erstellen um Original nicht zu verändern
                    initial_data = chart_data.copy()
                    
                    # Check ob timestamp im Index ist
                    if 'timestamp' not in initial_data.columns and initial_data.index.name == 'timestamp':
                        initial_data = initial_data.reset_index()
                        self._log("📊 Timestamp aus Index wiederhergestellt")
                    
                    self._log(f"📊 Nutze geladene Chart-Daten ({len(chart_data)} Bars)")
        except Exception as e:
            logger.warning(f"Could not get chart data: {e}")

        self._is_running = True
        self.run_batch_btn.setEnabled(False)
        self.run_wf_btn.setEnabled(False)
        self.start_btn.setEnabled(False)
        self.status_label.setText("BATCH")
        self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #FF9800;")

        self._batch_worker = BatchTestWorker(
            batch_config,
            signal_callback=self._get_signal_callback(initial_data),
            initial_data=initial_data,
            parent=self,
        )
        self._batch_worker.progress.connect(self.progress_updated.emit)
        self._batch_worker.log.connect(self._log)
        self._batch_worker.finished.connect(self._on_batch_worker_finished)
        self._batch_worker.error.connect(self._on_batch_worker_error)
        self._batch_worker.finished.connect(self._batch_worker.deleteLater)
        self._batch_worker.error.connect(self._batch_worker.deleteLater)
        self._batch_worker.start()

    async def _on_batch_clicked(self) -> None:
        """Startet Batch-Test mit Parameter-Optimierung (async)."""
        logger.info("🔄 _on_batch_clicked() called")
        self._log("🔄 Batch-Test async gestartet...")

        if self._is_running:
            logger.info("Already running, returning")
            return

        self._is_running = True
        logger.info("Starting batch test...")
        self.run_batch_btn.setEnabled(False)
        self.run_wf_btn.setEnabled(False)
        self.start_btn.setEnabled(False)
        self.status_label.setText("BATCH")
        self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #FF9800;")

        try:
            # Parse parameter space aus UI
            param_space_text = self.param_space_text.toPlainText().strip()
            if not param_space_text:
                param_space = {
                    "risk_per_trade_pct": [0.5, 1.0, 1.5, 2.0],
                    "max_leverage": [5, 10, 20],
                }
                self._log("⚠️ Kein Parameter Space angegeben, verwende Standard")
            else:
                try:
                    param_space = json.loads(param_space_text)
                except json.JSONDecodeError as e:
                    self._log(f"❌ Ungültiges JSON: {e}")
                    QMessageBox.critical(self, "Fehler", f"Ungültiges JSON für Parameter Space:\n{e}")
                    return

            # Build base config
            base_config = self._build_backtest_config()

            # Determine search method
            method_text = self.batch_method.currentText()
            from src.core.backtesting import BatchRunner, BatchConfig, SearchMethod

            if "Grid" in method_text:
                search_method = SearchMethod.GRID
            elif "Random" in method_text:
                search_method = SearchMethod.RANDOM
            else:
                search_method = SearchMethod.BAYESIAN

            # Determine target metric
            target_text = self.batch_target.currentText()
            target_map = {
                "Expectancy": "expectancy",
                "Profit Factor": "profit_factor",
                "Sharpe Ratio": "sharpe_ratio",
                "Min Drawdown": "max_drawdown_pct",
            }
            target_metric = target_map.get(target_text, "expectancy")
            minimize = "Drawdown" in target_text

            # Create BatchConfig
            batch_config = BatchConfig(
                base_config=base_config,
                parameter_space=param_space,
                search_method=search_method,
                target_metric=target_metric,
                minimize=minimize,
                max_iterations=self.batch_iterations.value(),
            )

            self._log(f"🔄 Starte Batch-Test: {search_method.value}")
            self._log(f"📊 Zielmetrik: {target_metric}, Iterationen: {batch_config.max_iterations}")
            self._log(f"📋 Parameter Space: {list(param_space.keys())}")

            # Create and run BatchRunner
            runner = BatchRunner(
                batch_config,
                signal_callback=self._get_signal_callback(),
            )
            runner.set_progress_callback(lambda p, m: self.progress_updated.emit(p, m))

            summary = await runner.run()

            # Update results table
            self._update_batch_results_table(runner.results)

            # Log summary
            self._log(f"✅ Batch abgeschlossen: {summary.successful_runs}/{summary.total_runs} erfolgreich")
            if summary.best_run and summary.best_run.metrics:
                best = summary.best_run
                self._log(f"🏆 Bester Run: {best.parameters}")
                self._log(f"   {target_metric}: {getattr(best.metrics, target_metric, 'N/A')}")

            # Offer export
            reply = QMessageBox.question(
                self, "Export",
                f"Batch abgeschlossen!\n\n{summary.successful_runs} erfolgreiche Runs.\n\nErgebnisse exportieren?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                output_dir = Path("data/backtest_results") / summary.batch_id
                exports = await runner.export_results(output_dir)
                self._log(f"📁 Exportiert nach: {output_dir}")

        except Exception as e:
            logger.exception("Batch test failed")
            self._log(f"❌ Batch Fehler: {e}")
            QMessageBox.critical(self, "Batch Fehler", str(e))

        finally:
            self._is_running = False
            self.run_batch_btn.setEnabled(True)
            self.run_wf_btn.setEnabled(True)
            self.start_btn.setEnabled(True)
            self.status_label.setText("IDLE")
            self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #888;")

    def _on_wf_btn_clicked(self) -> None:
        """Synchroner Button-Handler, startet async Walk-Forward Test."""
        logger.info("🚶 _on_wf_btn_clicked() - scheduling async walk-forward")
        self._log("🚶 Walk-Forward wird gestartet...")

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.ensure_future(self._on_wf_clicked())
            else:
                logger.warning("Event loop not running, trying qasync")
                asyncio.ensure_future(self._on_wf_clicked())
        except Exception as e:
            logger.exception(f"Failed to schedule walk-forward: {e}")
            self._log(f"❌ Fehler beim Starten des Walk-Forward: {e}")

    async def _on_wf_clicked(self) -> None:
        """Startet Walk-Forward Analyse mit Rolling Windows (async)."""
        logger.info("🚶 _on_wf_clicked() called")

        if self._is_running:
            logger.info("Already running, returning")
            return

        self._is_running = True
        self.run_batch_btn.setEnabled(False)
        self.run_wf_btn.setEnabled(False)
        self.start_btn.setEnabled(False)
        self.status_label.setText("WALK-FWD")
        self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #9C27B0;")

        try:
            # Build base config
            base_config = self._build_backtest_config()

            # Parse parameter space für Re-Optimization
            param_space_text = self.param_space_text.toPlainText().strip()
            if param_space_text:
                try:
                    param_space = json.loads(param_space_text)
                except json.JSONDecodeError:
                    param_space = {}
            else:
                param_space = {}

            # Walk-Forward Config aus UI
            from src.core.backtesting import WalkForwardRunner, WalkForwardConfig, BatchConfig, SearchMethod

            # BatchConfig für Optimierung erstellen (falls Parameter Space vorhanden)
            batch_config = BatchConfig(
                base_config=base_config,
                search_method=SearchMethod.GRID if param_space else SearchMethod.GRID,
                parameter_space=param_space,
                target_metric="expectancy",
                minimize=False,
            )

            wf_config = WalkForwardConfig(
                base_config=base_config,
                batch_config=batch_config,
                train_window_days=self.wf_train_days.value(),
                test_window_days=self.wf_test_days.value(),
                step_size_days=self.wf_step_days.value(),
                reoptimize_each_fold=self.wf_reoptimize.isChecked(),
            )

            self._log(f"🚶 Starte Walk-Forward Analyse")
            self._log(f"📅 Train: {wf_config.train_window_days}d, Test: {wf_config.test_window_days}d, Step: {wf_config.step_size_days}d")
            self._log(f"🔄 Re-Optimize: {wf_config.reoptimize_each_fold}")

            # Create and run WalkForwardRunner
            runner = WalkForwardRunner(
                wf_config,
                signal_callback=self._get_signal_callback(),
            )
            runner.set_progress_callback(lambda p, m: self.progress_updated.emit(p, m))

            summary = await runner.run()

            # Update results table with fold results
            self._update_wf_results_table(summary.fold_results)

            # Log summary
            self._log(f"✅ Walk-Forward abgeschlossen: {summary.total_folds} Folds")
            self._log(f"📊 Aggregierte OOS-Performance:")
            if summary.aggregated_oos_metrics:
                agg = summary.aggregated_oos_metrics
                self._log(f"   Total Trades: {agg.total_trades}")
                self._log(f"   Win Rate: {agg.win_rate * 100:.1f}%")
                self._log(f"   Profit Factor: {agg.profit_factor:.2f}")
                self._log(f"   Max DD: {agg.max_drawdown_pct:.1f}%")

            # Stability info
            if summary.stable_parameters:
                self._log(f"🔒 Stabile Parameter: {len(summary.stable_parameters)}")
                for param, stability in list(summary.stable_parameters.items())[:3]:
                    self._log(f"   {param}: Stabilität {stability:.1%}")

            # Offer export
            reply = QMessageBox.question(
                self, "Export",
                f"Walk-Forward abgeschlossen!\n\n{summary.total_folds} Folds analysiert.\n\nErgebnisse exportieren?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                output_dir = Path("data/backtest_results") / summary.wf_id
                exports = await runner.export_results(output_dir)
                self._log(f"📁 Exportiert nach: {output_dir}")

        except Exception as e:
            logger.exception("Walk-Forward failed")
            self._log(f"❌ Walk-Forward Fehler: {e}")
            QMessageBox.critical(self, "Walk-Forward Fehler", str(e))

        finally:
            self._is_running = False
            self.run_batch_btn.setEnabled(True)
            self.run_wf_btn.setEnabled(True)
            self.start_btn.setEnabled(True)
            self.status_label.setText("IDLE")
            self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #888;")

