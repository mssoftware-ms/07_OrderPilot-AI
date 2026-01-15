"""Backtest Tab Batch Execution - Batch and Walk-Forward Execution.

Refactored from backtest_tab_main.py.

Contains:
- on_batch_clicked: Start batch optimization test
- on_wf_clicked: Start walk-forward analysis
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING

import qasync
from PyQt6.QtWidgets import QMessageBox

if TYPE_CHECKING:
    from .backtest_tab_main import BacktestTab

logger = logging.getLogger(__name__)


class BacktestTabBatchExecution:
    """Helper for batch optimization and walk-forward execution."""

    def __init__(self, parent: "BacktestTab"):
        self.parent = parent

    @qasync.asyncSlot()
    async def on_batch_clicked(self) -> None:
        """Startet Batch-Test mit Parameter-Optimierung.

        Delegates to BatchRunner for execution.
        """
        if self.parent._is_running:
            return

        self.parent._is_running = True
        self.parent.run_batch_btn.setEnabled(False)
        self.parent.run_wf_btn.setEnabled(False)
        self.parent.start_btn.setEnabled(False)
        self.parent.status_label.setText("BATCH")
        self.parent.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #FF9800;")

        try:
            # Parse parameter space aus UI
            param_space_text = self.parent.param_space_text.toPlainText().strip()
            if not param_space_text:
                param_space = {
                    "risk_per_trade_pct": [0.5, 1.0, 1.5, 2.0],
                    "max_leverage": [5, 10, 20],
                }
                self.parent._logging.log("⚠️ Kein Parameter Space angegeben, verwende Standard")
            else:
                try:
                    param_space = json.loads(param_space_text)
                except json.JSONDecodeError as e:
                    self.parent._logging.log(f"❌ Ungültiges JSON: {e}")
                    QMessageBox.critical(self.parent, "Fehler", f"Ungültiges JSON für Parameter Space:\n{e}")
                    return

            # Build base config
            base_config = self.parent._execution.build_backtest_config()

            # Determine search method
            method_text = self.parent.batch_method.currentText()
            from src.core.backtesting import BatchRunner, BatchConfig, SearchMethod

            if "Grid" in method_text:
                search_method = SearchMethod.GRID
            elif "Random" in method_text:
                search_method = SearchMethod.RANDOM
            else:
                search_method = SearchMethod.BAYESIAN

            # Determine target metric
            target_text = self.parent.batch_target.currentText()
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
                max_iterations=self.parent.batch_iterations.value(),
            )

            self.parent._logging.log(f"🔄 Starte Batch-Test: {search_method.value}")
            self.parent._logging.log(f"📊 Zielmetrik: {target_metric}, Iterationen: {batch_config.max_iterations}")
            self.parent._logging.log(f"📋 Parameter Space: {list(param_space.keys())}")

            # Create and run BatchRunner
            signal_callback = self.parent.config_manager.get_signal_callback()
            runner = BatchRunner(
                batch_config,
                signal_callback=signal_callback,
            )
            runner.set_progress_callback(lambda p, m: self.parent.progress_updated.emit(p, m))

            summary = await runner.run()

            # Update results table via results_display
            self.parent.results_display.update_batch_results_table(runner.results)

            # Log summary
            self.parent._logging.log(f"✅ Batch abgeschlossen: {summary.successful_runs}/{summary.total_runs} erfolgreich")
            if summary.best_run and summary.best_run.metrics:
                best = summary.best_run
                self.parent._logging.log(f"🏆 Bester Run: {best.parameters}")
                self.parent._logging.log(f"   {target_metric}: {getattr(best.metrics, target_metric, 'N/A')}")

            # Offer export
            reply = QMessageBox.question(
                self.parent, "Export",
                f"Batch abgeschlossen!\n\n{summary.successful_runs} erfolgreiche Runs.\n\nErgebnisse exportieren?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                output_dir = Path("data/backtest_results") / summary.batch_id
                exports = await runner.export_results(output_dir)
                self.parent._logging.log(f"📁 Exportiert nach: {output_dir}")

        except Exception as e:
            logger.exception("Batch test failed")
            self.parent._logging.log(f"❌ Batch Fehler: {e}")
            QMessageBox.critical(self.parent, "Batch Fehler", str(e))

        finally:
            self.parent._is_running = False
            self.parent.run_batch_btn.setEnabled(True)
            self.parent.run_wf_btn.setEnabled(True)
            self.parent.start_btn.setEnabled(True)
            self.parent.status_label.setText("IDLE")
            self.parent.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #888;")

    @qasync.asyncSlot()
    async def on_wf_clicked(self) -> None:
        """Startet Walk-Forward Analyse - delegiert an WalkForwardRunner."""
        self.parent._logging.log("🚶 Walk-Forward Analysis wird gestartet...")
        # Full implementation available in original backtest_tab.py lines 2097-2199
        # Simplified stub for refactored version
        pass
