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


class BacktestTabExportMixin:
    """Export functions (CSV, JSON, batch results)"""

    def _export_csv(self) -> None:
        """Exportiert Trades als CSV."""
        if not self._current_result:
            QMessageBox.warning(self, "Kein Ergebnis", "Bitte erst einen Backtest durchführen.")
            return

        try:
            from pathlib import Path
            import csv

            output_dir = Path("data/backtest_results")
            output_dir.mkdir(parents=True, exist_ok=True)

            filename = output_dir / f"trades_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

            if hasattr(self._current_result, 'trades'):
                with open(filename, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(["ID", "Symbol", "Side", "Entry Price", "Exit Price", "Size", "P&L", "R-Multiple"])

                    for trade in self._current_result.trades:
                        writer.writerow([
                            trade.id,
                            trade.symbol,
                            trade.side.value,
                            trade.entry_price,
                            trade.exit_price or "",
                            trade.size,
                            trade.realized_pnl,
                            trade.r_multiple or "",
                        ])

                self._log(f"✅ Exported: {filename}")
                QMessageBox.information(self, "Export", f"Trades exportiert nach:\n{filename}")
            else:
                QMessageBox.warning(self, "Keine Trades", "Keine Trades zum Exportieren.")

        except Exception as e:
            logger.exception("Export failed")
            QMessageBox.critical(self, "Export Fehler", str(e))
    def _export_equity_csv(self) -> None:
        """Exportiert Equity Curve als CSV."""
        if not self._current_result:
            QMessageBox.warning(self, "Kein Ergebnis", "Bitte erst einen Backtest durchführen.")
            return

        try:
            import csv

            output_dir = Path("data/backtest_results")
            output_dir.mkdir(parents=True, exist_ok=True)

            filename = output_dir / f"equity_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

            if hasattr(self._current_result, 'equity_curve') and self._current_result.equity_curve:
                with open(filename, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(["Timestamp", "Equity", "Drawdown %", "Drawdown $"])

                    peak = self._current_result.initial_capital
                    for point in self._current_result.equity_curve:
                        ts = point.time.isoformat() if hasattr(point.time, 'isoformat') else str(point.time)
                        equity = point.equity
                        peak = max(peak, equity)
                        dd_pct = ((equity - peak) / peak) * 100 if peak > 0 else 0
                        dd_abs = equity - peak

                        writer.writerow([ts, f"{equity:.2f}", f"{dd_pct:.2f}", f"{dd_abs:.2f}"])

                self._log(f"✅ Equity Exported: {filename}")
                QMessageBox.information(self, "Export", f"Equity Curve exportiert nach:\n{filename}")
            else:
                QMessageBox.warning(self, "Keine Equity Curve", "Keine Equity Curve zum Exportieren.")

        except Exception as e:
            logger.exception("Equity export failed")
            QMessageBox.critical(self, "Export Fehler", str(e))
    def _export_json(self) -> None:
        """Exportiert Ergebnis als JSON."""
        if not self._current_result:
            QMessageBox.warning(self, "Kein Ergebnis", "Bitte erst einen Backtest durchführen.")
            return

        try:
            from pathlib import Path

            output_dir = Path("data/backtest_results")
            output_dir.mkdir(parents=True, exist_ok=True)

            filename = output_dir / f"result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

            if hasattr(self._current_result, 'model_dump'):
                data = self._current_result.model_dump(mode='json')
            elif hasattr(self._current_result, 'dict'):
                data = self._current_result.dict()
            else:
                data = {"error": "Cannot serialize result"}

            with open(filename, 'w') as f:
                json.dump(data, f, indent=2, default=str)

            self._log(f"✅ Exported: {filename}")
            QMessageBox.information(self, "Export", f"Ergebnis exportiert nach:\n{filename}")

        except Exception as e:
            logger.exception("Export failed")
    def _export_batch_results(self, summary, results: list, output_dir: Path) -> dict[str, Path]:
        """Exportiert Batch-Ergebnisse basierend auf Worker-Resultaten."""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        exports: dict[str, Path] = {}

        summary_path = output_dir / f"{summary.batch_id}_summary.json"
        summary_data = {
            "batch_id": summary.batch_id,
            "total_runs": summary.total_runs,
            "target_metric": summary.config_summary.get("target_metric"),
            "search_method": summary.config_summary.get("search_method"),
        }
        with open(summary_path, "w") as file:
            json.dump(summary_data, file, indent=2, default=str)
        exports["summary"] = summary_path

        results_path = output_dir / f"{summary.batch_id}_results.csv"
        runs_to_export = results[:20]
        with open(results_path, "w", newline="") as file:
            import csv

            writer = csv.writer(file)
            if runs_to_export:
                param_keys = list(runs_to_export[0].parameters.keys())
                metric_keys = [
                    "total_trades",
                    "win_rate",
                    "profit_factor",
                    "expectancy",
                    "max_drawdown_pct",
                    "total_return_pct",
                ]
                writer.writerow(["rank", "run_id"] + param_keys + metric_keys + ["error"])

                for rank, run in enumerate(runs_to_export, 1):
                    param_values = [run.parameters.get(k, "") for k in param_keys]
                    if run.metrics:
                        metric_values = [
                            run.metrics.total_trades,
                            f"{run.metrics.win_rate:.3f}",
                            f"{run.metrics.profit_factor:.2f}",
                            f"{run.metrics.expectancy:.2f}" if run.metrics.expectancy else "",
                            f"{run.metrics.max_drawdown_pct:.2f}",
                            f"{run.metrics.total_return_pct:.2f}",
                        ]
                    else:
                        metric_values = [""] * len(metric_keys)
                    writer.writerow([rank, run.run_id] + param_values + metric_values + [run.error or ""])
        exports["results"] = results_path

        if results:
            top_path = output_dir / f"{summary.batch_id}_top_params.json"
            top_data = []
            for run in results[:5]:
                if run.metrics:
                    top_data.append({
                        "parameters": run.parameters,
                        "expectancy": run.metrics.expectancy,
                        "profit_factor": run.metrics.profit_factor,
                        "win_rate": run.metrics.win_rate,
                        "total_return_pct": run.metrics.total_return_pct,
                    })
            with open(top_path, "w") as file:
                json.dump(top_data, file, indent=2)
            exports["top_params"] = top_path

        return exports

    def _export_variants_json(self, variants: list) -> None:
        """Exportiert Varianten als JSON-Datei."""
        try:
            output_dir = Path("data/backtest_results")
            output_dir.mkdir(parents=True, exist_ok=True)

            filename = output_dir / f"test_variants_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

            with open(filename, 'w') as f:
                json.dump(variants, f, indent=2)

            self._log(f"📄 Varianten exportiert: {filename}")
            QMessageBox.information(self, "Export", f"Varianten exportiert nach:\n{filename}")

        except Exception as e:
            logger.exception("Failed to export variants")
            QMessageBox.critical(self, "Fehler", f"Export fehlgeschlagen:\n{e}")
