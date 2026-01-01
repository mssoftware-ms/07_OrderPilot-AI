from __future__ import annotations

import asyncio
import json
import logging
import subprocess
from datetime import datetime
from typing import Optional

from PyQt6.QtCore import Qt, QTimer, QSettings
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QPushButton,
    QTabWidget,
    QMessageBox,
    QListWidget,
    QListWidgetItem,
)

from .pattern_db_tabs_mixin import PatternDbTabsMixin
from .pattern_db_worker import DatabaseBuildWorker

logger = logging.getLogger(__name__)

QDRANT_CONTAINER_NAME = "09_rag-system-ai_cl-qdrant-1"
QDRANT_IMAGE = "qdrant/qdrant"
QDRANT_PORT = 6333
COLLECTION_NAME = "trading_patterns"


class PatternDbBuildMixin:
    """PatternDbBuildMixin extracted from PatternDatabaseDialog."""
    def _refresh_stats(self):
        """Refresh database statistics."""
        try:
            async def get_stats():
                from src.core.pattern_db.qdrant_client import TradingPatternDB
                db = TradingPatternDB()
                return await db.get_collection_info()

            # Try to get stats
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            info = loop.run_until_complete(get_stats())

            if "error" in info:
                self.collection_name_label.setText("trading_patterns")
                self.patterns_count_label.setText("N/A (not connected)")
                self.collection_status_label.setText(info.get("error", "Unknown error"))
            else:
                self.collection_name_label.setText(info.get("name", "trading_patterns"))
                self.patterns_count_label.setText(f"{info.get('points_count', 0):,}")
                self.collection_status_label.setText(info.get("status", "unknown"))

        except Exception as e:
            self.collection_name_label.setText("trading_patterns")
            self.patterns_count_label.setText("Error")
            self.collection_status_label.setText(str(e)[:50])
    def _start_build(self):
        """Start building the database."""
        stock_symbols, crypto_symbols = self._collect_symbols()
        if not stock_symbols and not crypto_symbols:
            QMessageBox.warning(self, "No Symbols", "Please select at least one symbol.")
            return

        timeframes = self._collect_timeframes()
        if not timeframes:
            QMessageBox.warning(self, "No Timeframes", "Please select at least one timeframe.")
            return

        if not self._confirm_build(stock_symbols, crypto_symbols, timeframes):
            return

        self._reset_build_progress(stock_symbols, crypto_symbols, timeframes)
        self._toggle_build_controls(False)
        self._queue_builds(stock_symbols, crypto_symbols, timeframes)

    def _collect_symbols(self) -> tuple[list[str], list[str]]:
        stock_symbols: list[str] = []
        crypto_symbols: list[str] = []

        if self.stock_radio.isChecked():
            stock_symbols = [
                self.stock_list.item(i).text()
                for i in range(self.stock_list.count())
                if self.stock_list.item(i).isSelected()
            ]
            if not stock_symbols:
                stock_symbols = [
                    self.stock_list.item(i).text()
                    for i in range(self.stock_list.count())
                ]

        if self.crypto_radio.isChecked():
            crypto_symbols = [
                self.crypto_list.item(i).text()
                for i in range(self.crypto_list.count())
                if self.crypto_list.item(i).isSelected()
            ]
            if not crypto_symbols:
                crypto_symbols = [
                    self.crypto_list.item(i).text()
                    for i in range(self.crypto_list.count())
                ]

        return stock_symbols, crypto_symbols

    def _collect_timeframes(self) -> list[str]:
        timeframes: list[str] = []
        if self.tf_1min.isChecked():
            timeframes.append("1Min")
        if self.tf_5min.isChecked():
            timeframes.append("5Min")
        if self.tf_15min.isChecked():
            timeframes.append("15Min")
        if self.tf_30min.isChecked():
            timeframes.append("30Min")
        if self.tf_1hour.isChecked():
            timeframes.append("1Hour")
        return timeframes

    def _confirm_build(
        self, stock_symbols: list[str], crypto_symbols: list[str], timeframes: list[str]
    ) -> bool:
        stock_preview = ", ".join(stock_symbols[:8]) + (" ..." if len(stock_symbols) > 8 else "")
        crypto_preview = ", ".join(crypto_symbols[:8]) + (" ..." if len(crypto_symbols) > 8 else "")
        msg = (
            f"Build database with:\n"
            f"- {len(stock_symbols)} stock symbols"
            f"{' (' + stock_preview + ')' if stock_symbols else ''}\n"
            f"- {len(crypto_symbols)} crypto symbols"
            f"{' (' + crypto_preview + ')' if crypto_symbols else ''}\n"
            f"- {len(timeframes)} timeframes\n"
            f"- {self.days_spin.value()} days of history\n\n"
            f"This may take a while. Continue?"
        )
        return QMessageBox.question(self, "Confirm Build", msg) == QMessageBox.StandardButton.Yes

    def _reset_build_progress(
        self,
        stock_symbols: list[str],
        crypto_symbols: list[str],
        timeframes: list[str],
    ) -> None:
        self.log_text.clear()
        self.progress_bar.setValue(0)
        self._progress_offset = 0
        self._current_worker_total = 0
        self._progress_total_tasks = (
            len(stock_symbols) * len(timeframes) + len(crypto_symbols) * len(timeframes)
        )

    def _toggle_build_controls(self, enabled: bool) -> None:
        self.build_btn.setEnabled(enabled)
        self.cancel_btn.setEnabled(not enabled)

    def _queue_builds(
        self,
        stock_symbols: list[str],
        crypto_symbols: list[str],
        timeframes: list[str],
    ) -> None:
        if stock_symbols:
            if crypto_symbols:
                self._pending_crypto_symbols = crypto_symbols
                self._pending_timeframes = timeframes
                self._pending_days_back = self.days_spin.value()
            self._run_build(stock_symbols, timeframes, False)
        elif crypto_symbols:
            self._run_build(crypto_symbols, timeframes, True)
    def _run_build(self, symbols: list[str], timeframes: list[str], is_crypto: bool):
        """Run the build worker."""
        self._current_worker_total = len(symbols) * len(timeframes)
        self._build_worker = DatabaseBuildWorker(
            symbols=symbols,
            timeframes=timeframes,
            days_back=self.days_spin.value(),
            is_crypto=is_crypto,
            window_size=self.window_spin.value(),
            step_size=self.step_spin.value(),
        )

        self._build_worker.progress.connect(self._log)
        self._build_worker.progress_value.connect(self._update_progress)
        self._build_worker.finished.connect(self._on_build_finished)
        self._build_worker.start()
    def _cancel_build(self):
        """Cancel the build process."""
        if self._build_worker:
            self._build_worker.cancel()
            self._log("Cancelling build...")
    def _on_build_finished(self, success: bool, message: str):
        """Handle build completion."""
        self.build_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)

        if success:
            self._log(f"SUCCESS: {message}")
            self._refresh_stats()
            self._progress_offset += self._current_worker_total
        else:
            self._log(f"FAILED: {message}")

        self._build_worker = None

        # If stocks completed successfully and crypto is pending, run crypto build next
        if success and self._pending_crypto_symbols:
            symbols = self._pending_crypto_symbols
            timeframes = self._pending_timeframes
            days_back = self._pending_days_back
            # Clear pending before starting
            self._pending_crypto_symbols = []
            self._pending_timeframes = []
            self._pending_days_back = 0

            self._log(f"Starting crypto build: {len(symbols)} symbols")
            self._run_build(symbols, timeframes, True)
    def _update_progress(self, current: int, total: int):
        """Update progress bar."""
        worker_total = self._current_worker_total or total
        global_total = self._progress_total_tasks or worker_total
        if global_total > 0:
            global_current = min(self._progress_offset + current, global_total)
            self.progress_bar.setValue(int(global_current / global_total * 100))
