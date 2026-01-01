"""Pattern Database Management Dialog.

Provides UI for managing the Qdrant-based pattern database:
- Start/Stop Docker Qdrant
- View database statistics
- Add symbols and timeframes
- Build/update the pattern database

REFACTORED: Split into multiple files to meet 600 LOC limit.
- pattern_db_worker.py: DatabaseBuildWorker class
- pattern_db_tabs_mixin.py: Tab creation methods
- pattern_db_dialog.py: Main dialog class (this file)
"""

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

# Docker configuration - uses existing Qdrant from RAG system
QDRANT_CONTAINER_NAME = "09_rag-system-ai_cl-qdrant-1"  # Existing container
QDRANT_IMAGE = "qdrant/qdrant"
QDRANT_PORT = 6333
COLLECTION_NAME = "trading_patterns"  # Separate collection for OrderPilot


class PatternDatabaseDialog(PatternDbTabsMixin, QDialog):
    """Dialog for managing the pattern database."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Pattern Database Manager")
        self.setMinimumSize(800, 600)
        self.resize(900, 700)

        self._settings = QSettings("OrderPilot", "TradingApp")
        self._build_worker: Optional[DatabaseBuildWorker] = None
        self._pending_crypto_symbols: list[str] = []
        self._pending_timeframes: list[str] = []
        self._pending_days_back: int = 0
        self._progress_total_tasks: int = 0
        self._progress_offset: int = 0
        self._current_worker_total: int = 0
        self._status_timer = QTimer(self)
        self._status_timer.timeout.connect(self._update_docker_status)

        self._setup_ui()
        self._load_initial_state()

        # Start status timer
        self._status_timer.start(5000)  # Check every 5 seconds

    def _setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)

        # Create tab widget
        tabs = QTabWidget()
        layout.addWidget(tabs)

        # Tab 1: Status & Docker
        status_tab = self._create_status_tab()
        tabs.addTab(status_tab, "Status")

        # Tab 2: Build Database
        build_tab = self._create_build_tab()
        tabs.addTab(build_tab, "Build Database")

        # Tab 3: Search Test
        search_tab = self._create_search_tab()
        tabs.addTab(search_tab, "Search Test")

        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)

    def _select_all(self, list_widget: QListWidget, select: bool):
        """Select or deselect all items in a list."""
        for i in range(list_widget.count()):
            list_widget.item(i).setSelected(select)

    def _add_custom_crypto(self):
        """Add a custom crypto symbol."""
        symbol = self.custom_crypto_input.text().strip().upper()
        if symbol and "/" in symbol:
            # Check if already exists
            for i in range(self.crypto_list.count()):
                if self.crypto_list.item(i).text() == symbol:
                    return
            from PyQt6.QtWidgets import QListWidgetItem
            item = QListWidgetItem(symbol)
            item.setSelected(True)
            self.crypto_list.addItem(item)
            self.custom_crypto_input.clear()

    def _add_custom_stock(self):
        """Add a custom stock or index symbol."""
        symbol = self.custom_stock_input.text().strip().upper()
        if not symbol:
            return
        for i in range(self.stock_list.count()):
            if self.stock_list.item(i).text() == symbol:
                return
        from PyQt6.QtWidgets import QListWidgetItem
        item = QListWidgetItem(symbol)
        item.setSelected(True)
        self.stock_list.addItem(item)
        self.custom_stock_input.clear()

    def _remove_selected_stocks(self):
        """Remove selected stock symbols from list."""
        for item in self.stock_list.selectedItems():
            row = self.stock_list.row(item)
            self.stock_list.takeItem(row)

    def _clear_stock_list(self):
        """Clear all stock symbols."""
        self.stock_list.clear()

    def _remove_selected_crypto(self):
        """Remove selected crypto symbols from list."""
        for item in self.crypto_list.selectedItems():
            row = self.crypto_list.row(item)
            self.crypto_list.takeItem(row)

    def _clear_crypto_list(self):
        """Clear all crypto symbols."""
        self.crypto_list.clear()

    def _load_initial_state(self):
        """Load initial state on dialog open."""
        self._update_docker_status()
        self._refresh_stats()
        self._load_ui_settings()

    def _load_ui_settings(self) -> None:
        """Load saved UI settings for the Pattern DB dialog."""
        try:
            stock_symbols_json = self._settings.value("pattern_db/stock_symbols")
            crypto_symbols_json = self._settings.value("pattern_db/crypto_symbols")
            stock_selected_json = self._settings.value("pattern_db/stock_selected")
            crypto_selected_json = self._settings.value("pattern_db/crypto_selected")

            if stock_symbols_json:
                symbols = json.loads(stock_symbols_json)
                self.stock_list.clear()
                for s in symbols:
                    item = QListWidgetItem(s)
                    self.stock_list.addItem(item)

            if crypto_symbols_json:
                symbols = json.loads(crypto_symbols_json)
                self.crypto_list.clear()
                for s in symbols:
                    item = QListWidgetItem(s)
                    self.crypto_list.addItem(item)

            if stock_selected_json:
                selected = set(json.loads(stock_selected_json))
                for i in range(self.stock_list.count()):
                    item = self.stock_list.item(i)
                    item.setSelected(item.text() in selected)

            if crypto_selected_json:
                selected = set(json.loads(crypto_selected_json))
                for i in range(self.crypto_list.count()):
                    item = self.crypto_list.item(i)
                    item.setSelected(item.text() in selected)

            self.stock_radio.setChecked(
                self._settings.value("pattern_db/stock_enabled", True, type=bool)
            )
            self.crypto_radio.setChecked(
                self._settings.value("pattern_db/crypto_enabled", True, type=bool)
            )

            # Timeframes
            self.tf_1min.setChecked(self._settings.value("pattern_db/tf_1min", True, type=bool))
            self.tf_5min.setChecked(self._settings.value("pattern_db/tf_5min", True, type=bool))
            self.tf_15min.setChecked(self._settings.value("pattern_db/tf_15min", True, type=bool))
            self.tf_30min.setChecked(self._settings.value("pattern_db/tf_30min", False, type=bool))
            self.tf_1hour.setChecked(self._settings.value("pattern_db/tf_1hour", False, type=bool))

            # Numeric inputs
            days = self._settings.value("pattern_db/days_back", None)
            if days is not None:
                self.days_spin.setValue(int(days))
            window = self._settings.value("pattern_db/window_size", None)
            if window is not None:
                self.window_spin.setValue(int(window))
            step = self._settings.value("pattern_db/step_size", None)
            if step is not None:
                self.step_spin.setValue(int(step))

            # Search tab settings
            search_symbol = self._settings.value("pattern_db/search_symbol")
            if search_symbol:
                idx = self.search_symbol.findText(search_symbol)
                if idx >= 0:
                    self.search_symbol.setCurrentIndex(idx)
                else:
                    self.search_symbol.addItem(search_symbol)
                    self.search_symbol.setCurrentText(search_symbol)

            search_timeframe = self._settings.value("pattern_db/search_timeframe")
            if search_timeframe:
                idx = self.search_timeframe.findText(search_timeframe)
                if idx >= 0:
                    self.search_timeframe.setCurrentIndex(idx)

            threshold = self._settings.value("pattern_db/search_threshold", None)
            if threshold is not None:
                self.search_threshold.setValue(float(threshold))

        except Exception as e:
            logger.error(f"Failed to load Pattern DB settings: {e}")

    def _save_ui_settings(self) -> None:
        """Persist UI settings for the Pattern DB dialog."""
        try:
            stock_symbols = [self.stock_list.item(i).text() for i in range(self.stock_list.count())]
            crypto_symbols = [self.crypto_list.item(i).text() for i in range(self.crypto_list.count())]
            stock_selected = [item.text() for item in self.stock_list.selectedItems()]
            crypto_selected = [item.text() for item in self.crypto_list.selectedItems()]

            self._settings.setValue("pattern_db/stock_symbols", json.dumps(stock_symbols))
            self._settings.setValue("pattern_db/crypto_symbols", json.dumps(crypto_symbols))
            self._settings.setValue("pattern_db/stock_selected", json.dumps(stock_selected))
            self._settings.setValue("pattern_db/crypto_selected", json.dumps(crypto_selected))

            self._settings.setValue("pattern_db/stock_enabled", self.stock_radio.isChecked())
            self._settings.setValue("pattern_db/crypto_enabled", self.crypto_radio.isChecked())

            # Timeframes
            self._settings.setValue("pattern_db/tf_1min", self.tf_1min.isChecked())
            self._settings.setValue("pattern_db/tf_5min", self.tf_5min.isChecked())
            self._settings.setValue("pattern_db/tf_15min", self.tf_15min.isChecked())
            self._settings.setValue("pattern_db/tf_30min", self.tf_30min.isChecked())
            self._settings.setValue("pattern_db/tf_1hour", self.tf_1hour.isChecked())

            # Numeric inputs
            self._settings.setValue("pattern_db/days_back", self.days_spin.value())
            self._settings.setValue("pattern_db/window_size", self.window_spin.value())
            self._settings.setValue("pattern_db/step_size", self.step_spin.value())

            # Search tab
            self._settings.setValue("pattern_db/search_symbol", self.search_symbol.currentText())
            self._settings.setValue("pattern_db/search_timeframe", self.search_timeframe.currentText())
            self._settings.setValue("pattern_db/search_threshold", self.search_threshold.value())

        except Exception as e:
            logger.error(f"Failed to save Pattern DB settings: {e}")

    def closeEvent(self, event):
        """Persist settings on close."""
        self._save_ui_settings()
        super().closeEvent(event)

    def _update_docker_status(self):
        """Update Docker status display."""
        try:
            # Check if container exists and is running
            result = subprocess.run(
                ["docker", "ps", "-a", "--filter", f"name={QDRANT_CONTAINER_NAME}", "--format", "{{.Status}}"],
                capture_output=True,
                text=True,
                timeout=5,
            )

            status = result.stdout.strip()
            if not status:
                self.docker_status_label.setText("Not Created")
                self.docker_status_label.setStyleSheet("color: gray;")
                self.docker_container_label.setText(f"{QDRANT_CONTAINER_NAME} (not found)")
                self.start_docker_btn.setEnabled(True)
                self.stop_docker_btn.setEnabled(False)
            elif "Up" in status:
                self.docker_status_label.setText(f"Running ({status})")
                self.docker_status_label.setStyleSheet("color: green; font-weight: bold;")
                self.docker_container_label.setText(QDRANT_CONTAINER_NAME)
                self.start_docker_btn.setEnabled(False)
                self.stop_docker_btn.setEnabled(True)
            else:
                self.docker_status_label.setText(f"Stopped ({status})")
                self.docker_status_label.setStyleSheet("color: orange;")
                self.docker_container_label.setText(QDRANT_CONTAINER_NAME)
                self.start_docker_btn.setEnabled(True)
                self.stop_docker_btn.setEnabled(False)

        except subprocess.TimeoutExpired:
            self.docker_status_label.setText("Docker not responding")
            self.docker_status_label.setStyleSheet("color: red;")
        except FileNotFoundError:
            self.docker_status_label.setText("Docker not installed")
            self.docker_status_label.setStyleSheet("color: red;")
        except Exception as e:
            self.docker_status_label.setText(f"Error: {e}")
            self.docker_status_label.setStyleSheet("color: red;")

    def _start_docker(self):
        """Start the existing Qdrant Docker container (from RAG-System)."""
        try:
            # Start the existing container
            subprocess.run(["docker", "start", QDRANT_CONTAINER_NAME], check=True)
            self._log(f"Started Qdrant container: {QDRANT_CONTAINER_NAME}")
            self._log(f"Collection for patterns: {COLLECTION_NAME}")
            self._update_docker_status()

        except subprocess.CalledProcessError as e:
            QMessageBox.critical(
                self,
                "Docker Error",
                f"Failed to start Docker container '{QDRANT_CONTAINER_NAME}'.\n\n"
                f"Make sure the RAG-System Docker stack is set up.\n\n"
                f"Error: {e}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _stop_docker(self):
        """Stop the Qdrant Docker container."""
        try:
            subprocess.run(["docker", "stop", QDRANT_CONTAINER_NAME], check=True)
            self._log("Stopped Qdrant container")
            self._update_docker_status()
        except subprocess.CalledProcessError as e:
            QMessageBox.critical(self, "Docker Error", f"Failed to stop Docker:\n{e}")

    def _restart_docker(self):
        """Restart the Qdrant Docker container."""
        try:
            subprocess.run(["docker", "restart", QDRANT_CONTAINER_NAME], check=True)
            self._log("Restarted Qdrant container")
            self._update_docker_status()
        except subprocess.CalledProcessError as e:
            QMessageBox.critical(self, "Docker Error", f"Failed to restart Docker:\n{e}")

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
        # Get selected symbols
        stock_symbols = []
        crypto_symbols = []

        if self.stock_radio.isChecked():
            for i in range(self.stock_list.count()):
                item = self.stock_list.item(i)
                if item.isSelected():
                    stock_symbols.append(item.text())
            # If no explicit selection but checkbox is on, include all by default
            if not stock_symbols:
                stock_symbols = [self.stock_list.item(i).text() for i in range(self.stock_list.count())]

        if self.crypto_radio.isChecked():
            for i in range(self.crypto_list.count()):
                item = self.crypto_list.item(i)
                if item.isSelected():
                    crypto_symbols.append(item.text())
            if not crypto_symbols:
                crypto_symbols = [self.crypto_list.item(i).text() for i in range(self.crypto_list.count())]

        if not stock_symbols and not crypto_symbols:
            QMessageBox.warning(self, "No Symbols", "Please select at least one symbol.")
            return

        # Get selected timeframes
        timeframes = []
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

        if not timeframes:
            QMessageBox.warning(self, "No Timeframes", "Please select at least one timeframe.")
            return

        # Confirm
        # Prepare preview of selections
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
        if QMessageBox.question(self, "Confirm Build", msg) != QMessageBox.StandardButton.Yes:
            return

        # Clear log
        self.log_text.clear()
        self.progress_bar.setValue(0)
        self._progress_offset = 0
        self._current_worker_total = 0
        self._progress_total_tasks = (
            len(stock_symbols) * len(timeframes) + len(crypto_symbols) * len(timeframes)
        )

        # Disable build button, enable cancel
        self.build_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)

        # Build stocks first, then crypto
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

    def _log(self, message: str):
        """Add message to log."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        # Scroll to bottom
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )

    def _clear_database(self):
        """Clear the entire database."""
        result = QMessageBox.warning(
            self,
            "Clear Database",
            "This will delete ALL patterns from the database.\n\nAre you sure?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if result != QMessageBox.StandardButton.Yes:
            return

        try:
            async def clear():
                from src.core.pattern_db.qdrant_client import TradingPatternDB
                db = TradingPatternDB()
                return await db.delete_collection()

            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            success = loop.run_until_complete(clear())

            if success:
                self._log("Database cleared successfully")
                self._refresh_stats()
            else:
                self._log("Failed to clear database")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to clear database:\n{e}")

    def _run_search_test(self):
        """Run a search test."""
        self.search_results.clear()
        self.search_results.append("Running search test...\n")

        try:
            from datetime import timedelta, timezone

            symbol = self.search_symbol.currentText()
            timeframe = self.search_timeframe.currentText()
            threshold = self.search_threshold.value() / 100

            async def run_search():
                from src.core.market_data.types import DataRequest, Timeframe, AssetClass
                from src.core.market_data.history_provider import HistoryManager
                from src.core.pattern_db import get_pattern_service
                from src.core.pattern_db.fetcher import resolve_symbol

                # Determine asset class
                is_crypto = "/" in symbol
                asset_class = AssetClass.CRYPTO if is_crypto else AssetClass.STOCK
                fetch_symbol = resolve_symbol(symbol, asset_class)

                # Fetch recent bars
                tf_map = {
                    "1Min": Timeframe.MINUTE_1,
                    "5Min": Timeframe.MINUTE_5,
                    "15Min": Timeframe.MINUTE_15,
                }

                hm = HistoryManager()
                end = datetime.now(timezone.utc)
                start = end - timedelta(hours=2)

                request = DataRequest(
                    symbol=fetch_symbol,
                    start_date=start,
                    end_date=end,
                    timeframe=tf_map.get(timeframe, Timeframe.MINUTE_1),
                    asset_class=asset_class,
                )

                bars, source = await hm.fetch_data(request)

                if len(bars) < 20:
                    return f"Not enough bars ({len(bars)}). Need at least 20."

                # Get pattern service
                service = await get_pattern_service()

                # Analyze
                analysis = await service.analyze_signal(
                    bars=bars,
                    symbol=symbol,
                    timeframe=timeframe,
                    signal_direction="long",
                )

                if not analysis:
                    return "Analysis failed - check if database has patterns"

                # Format results
                result = f"Symbol: {symbol} | Timeframe: {timeframe}\n"
                if fetch_symbol != symbol:
                    result += f"Data proxy used: {fetch_symbol}\n"
                result += f"Bars analyzed: {len(bars)}\n"
                result += "=" * 50 + "\n\n"
                result += f"Similar Patterns Found: {analysis.similar_patterns_count}\n"
                result += f"Win Rate: {analysis.win_rate:.1%}\n"
                result += f"Avg Return: {analysis.avg_return:.2f}%\n"
                result += f"Confidence: {analysis.confidence:.1%}\n"
                result += f"Signal Boost: {analysis.signal_boost:+.2f}\n"
                result += f"Recommendation: {analysis.recommendation.upper()}\n"
                result += f"Trend Consistency: {analysis.trend_consistency:.1%}\n"
                result += "\n" + "=" * 50 + "\n"
                result += "Top Matches:\n"

                for i, match in enumerate(analysis.best_matches[:5], 1):
                    result += f"\n{i}. {match.symbol} ({match.timeframe})\n"
                    result += f"   Score: {match.score:.3f}\n"
                    result += f"   Trend: {match.trend_direction} | Outcome: {match.outcome_label}\n"
                    result += f"   Return: {match.outcome_return_pct:+.2f}%\n"

                return result

            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            result = loop.run_until_complete(run_search())
            self.search_results.append(result)

        except Exception as e:
            self.search_results.append(f"Error: {e}")
            logger.error(f"Search test error: {e}", exc_info=True)

    def closeEvent(self, event):
        """Handle dialog close."""
        self._status_timer.stop()
        if self._build_worker and self._build_worker.isRunning():
            self._build_worker.cancel()
            self._build_worker.wait(3000)
        super().closeEvent(event)
