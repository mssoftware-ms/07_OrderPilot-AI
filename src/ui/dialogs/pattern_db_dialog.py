"""Pattern Database Management Dialog.

Provides UI for managing the Qdrant-based pattern database:
- Start/Stop Docker Qdrant
- View database statistics
- Add symbols and timeframes
- Build/update the pattern database
"""

import asyncio
import logging
import subprocess
from datetime import datetime
from typing import Optional

from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QLabel,
    QPushButton,
    QProgressBar,
    QTextEdit,
    QComboBox,
    QSpinBox,
    QCheckBox,
    QListWidget,
    QListWidgetItem,
    QLineEdit,
    QTabWidget,
    QWidget,
    QGridLayout,
    QMessageBox,
    QAbstractItemView,
)

from src.core.pattern_db.fetcher import NASDAQ_100_TOP, CRYPTO_SYMBOLS

logger = logging.getLogger(__name__)

# Docker configuration - uses existing Qdrant from RAG system
QDRANT_CONTAINER_NAME = "09_rag-system-ai_cl-qdrant-1"  # Existing container
QDRANT_IMAGE = "qdrant/qdrant"
QDRANT_PORT = 6333
COLLECTION_NAME = "trading_patterns"  # Separate collection for OrderPilot


class DatabaseBuildWorker(QThread):
    """Worker thread for building the pattern database."""

    progress = pyqtSignal(str)  # Log message
    progress_value = pyqtSignal(int, int)  # current, total
    finished = pyqtSignal(bool, str)  # success, message

    def __init__(
        self,
        symbols: list[str],
        timeframes: list[str],
        days_back: int,
        is_crypto: bool,
        window_size: int = 20,
        step_size: int = 5,
    ):
        super().__init__()
        self.symbols = symbols
        self.timeframes = timeframes
        self.days_back = days_back
        self.is_crypto = is_crypto
        self.window_size = window_size
        self.step_size = step_size
        self._cancelled = False

    def cancel(self):
        """Cancel the build process."""
        self._cancelled = True

    def run(self):
        """Run the database build in a separate thread."""
        try:
            # Run async build in this thread
            asyncio.run(self._build_async())
        except Exception as e:
            self.finished.emit(False, str(e))

    async def _build_async(self):
        """Async build process."""
        from src.core.market_data.types import Timeframe, AssetClass
        from src.core.pattern_db.fetcher import PatternDataFetcher
        from src.core.pattern_db.extractor import PatternExtractor
        from src.core.pattern_db.qdrant_client import TradingPatternDB

        try:
            self.progress.emit("Initializing components...")

            fetcher = PatternDataFetcher()
            extractor = PatternExtractor(
                window_size=self.window_size,
                step_size=self.step_size,
            )
            db = TradingPatternDB()

            # Initialize Qdrant
            self.progress.emit("Connecting to Qdrant...")
            if not await db.initialize():
                self.finished.emit(False, "Failed to connect to Qdrant. Is Docker running?")
                return

            # Map timeframe strings to enum
            tf_map = {
                "1Min": Timeframe.MINUTE_1,
                "5Min": Timeframe.MINUTE_5,
                "15Min": Timeframe.MINUTE_15,
                "30Min": Timeframe.MINUTE_30,
                "1Hour": Timeframe.HOUR_1,
                "4Hour": Timeframe.HOUR_4,
                "1Day": Timeframe.DAY_1,
            }

            timeframe_enums = [tf_map.get(tf, Timeframe.MINUTE_1) for tf in self.timeframes]
            asset_class = AssetClass.CRYPTO if self.is_crypto else AssetClass.STOCK

            total_tasks = len(self.symbols) * len(timeframe_enums)
            completed = 0
            total_patterns = 0

            for symbol in self.symbols:
                if self._cancelled:
                    self.finished.emit(False, "Build cancelled by user")
                    return

                for tf_enum in timeframe_enums:
                    if self._cancelled:
                        self.finished.emit(False, "Build cancelled by user")
                        return

                    self.progress.emit(f"Fetching {symbol} ({tf_enum.value})...")

                    # Fetch bars
                    bars = await fetcher.fetch_symbol_data(
                        symbol=symbol,
                        timeframe=tf_enum,
                        days_back=self.days_back,
                        asset_class=asset_class,
                    )

                    if bars:
                        self.progress.emit(f"  Got {len(bars)} bars, extracting patterns...")

                        # Extract patterns
                        patterns = list(extractor.extract_patterns(
                            bars=bars,
                            symbol=symbol,
                            timeframe=tf_enum.value,
                        ))

                        if patterns:
                            self.progress.emit(f"  Inserting {len(patterns)} patterns...")
                            inserted = await db.insert_patterns_batch(patterns, batch_size=500)
                            total_patterns += inserted
                    else:
                        self.progress.emit(f"  No data for {symbol}")

                    completed += 1
                    self.progress_value.emit(completed, total_tasks)

                    # Small delay to avoid rate limits
                    await asyncio.sleep(0.3)

            # Get final stats
            info = await db.get_collection_info()
            msg = f"Build complete! Added {total_patterns:,} patterns. Total: {info.get('points_count', 0):,}"
            self.progress.emit(msg)
            self.finished.emit(True, msg)

        except Exception as e:
            logger.error(f"Build error: {e}", exc_info=True)
            self.finished.emit(False, str(e))


class PatternDatabaseDialog(QDialog):
    """Dialog for managing the pattern database."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Pattern Database Manager")
        self.setMinimumSize(800, 600)
        self.resize(900, 700)

        self._build_worker: Optional[DatabaseBuildWorker] = None
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

    def _create_status_tab(self) -> QWidget:
        """Create the status tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Docker Status Group
        docker_group = QGroupBox("Docker Qdrant Status")
        docker_layout = QGridLayout(docker_group)

        self.docker_status_label = QLabel("Checking...")
        self.docker_status_label.setFont(QFont("Consolas", 10))
        docker_layout.addWidget(QLabel("Status:"), 0, 0)
        docker_layout.addWidget(self.docker_status_label, 0, 1)

        self.docker_container_label = QLabel("-")
        docker_layout.addWidget(QLabel("Container:"), 1, 0)
        docker_layout.addWidget(self.docker_container_label, 1, 1)

        # Docker control buttons
        docker_btn_layout = QHBoxLayout()
        self.start_docker_btn = QPushButton("Start Qdrant")
        self.start_docker_btn.clicked.connect(self._start_docker)
        docker_btn_layout.addWidget(self.start_docker_btn)

        self.stop_docker_btn = QPushButton("Stop Qdrant")
        self.stop_docker_btn.clicked.connect(self._stop_docker)
        docker_btn_layout.addWidget(self.stop_docker_btn)

        self.restart_docker_btn = QPushButton("Restart")
        self.restart_docker_btn.clicked.connect(self._restart_docker)
        docker_btn_layout.addWidget(self.restart_docker_btn)

        docker_btn_layout.addStretch()
        docker_layout.addLayout(docker_btn_layout, 2, 0, 1, 2)

        layout.addWidget(docker_group)

        # Collection Stats Group
        stats_group = QGroupBox("Pattern Database Statistics")
        stats_layout = QGridLayout(stats_group)

        self.collection_name_label = QLabel("-")
        stats_layout.addWidget(QLabel("Collection:"), 0, 0)
        stats_layout.addWidget(self.collection_name_label, 0, 1)

        self.patterns_count_label = QLabel("-")
        self.patterns_count_label.setFont(QFont("Consolas", 12, QFont.Weight.Bold))
        stats_layout.addWidget(QLabel("Total Patterns:"), 1, 0)
        stats_layout.addWidget(self.patterns_count_label, 1, 1)

        self.collection_status_label = QLabel("-")
        stats_layout.addWidget(QLabel("Collection Status:"), 2, 0)
        stats_layout.addWidget(self.collection_status_label, 2, 1)

        refresh_btn = QPushButton("Refresh Stats")
        refresh_btn.clicked.connect(self._refresh_stats)
        stats_layout.addWidget(refresh_btn, 3, 0, 1, 2)

        layout.addWidget(stats_group)

        # Info/Help
        info_group = QGroupBox("Information")
        info_layout = QVBoxLayout(info_group)
        info_text = QLabel(
            "The Pattern Database stores historical trading patterns as vectors.\n"
            "Similar patterns are matched using cosine similarity to validate trading signals.\n\n"
            f"Uses existing Qdrant Docker instance (RAG-System)\n"
            f"Collection: {COLLECTION_NAME}\n"
            f"Qdrant Port: {QDRANT_PORT}"
        )
        info_text.setWordWrap(True)
        info_layout.addWidget(info_text)
        layout.addWidget(info_group)

        layout.addStretch()
        return widget

    def _create_build_tab(self) -> QWidget:
        """Create the build database tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Asset Selection
        asset_group = QGroupBox("Asset Selection")
        asset_layout = QVBoxLayout(asset_group)

        # Asset type selection
        type_layout = QHBoxLayout()
        self.stock_radio = QCheckBox("Stocks (NASDAQ-100)")
        self.stock_radio.setChecked(True)
        type_layout.addWidget(self.stock_radio)

        self.crypto_radio = QCheckBox("Crypto (BTC, ETH)")
        self.crypto_radio.setChecked(True)
        type_layout.addWidget(self.crypto_radio)
        type_layout.addStretch()
        asset_layout.addLayout(type_layout)

        # Symbol lists
        lists_layout = QHBoxLayout()

        # Stock symbols
        stock_box = QVBoxLayout()
        stock_box.addWidget(QLabel("Stock Symbols:"))
        self.stock_list = QListWidget()
        self.stock_list.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        for symbol in NASDAQ_100_TOP:
            item = QListWidgetItem(symbol)
            item.setSelected(True)
            self.stock_list.addItem(item)
        stock_box.addWidget(self.stock_list)

        # Stock quick actions
        stock_btns = QHBoxLayout()
        select_all_stocks = QPushButton("All")
        select_all_stocks.clicked.connect(lambda: self._select_all(self.stock_list, True))
        stock_btns.addWidget(select_all_stocks)
        select_none_stocks = QPushButton("None")
        select_none_stocks.clicked.connect(lambda: self._select_all(self.stock_list, False))
        stock_btns.addWidget(select_none_stocks)
        stock_box.addLayout(stock_btns)

        lists_layout.addLayout(stock_box)

        # Crypto symbols
        crypto_box = QVBoxLayout()
        crypto_box.addWidget(QLabel("Crypto Symbols:"))
        self.crypto_list = QListWidget()
        self.crypto_list.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        for symbol in CRYPTO_SYMBOLS:
            item = QListWidgetItem(symbol)
            item.setSelected(True)
            self.crypto_list.addItem(item)
        # Add more crypto options
        for symbol in ["SOL/USD", "DOGE/USD", "AVAX/USD", "LINK/USD"]:
            item = QListWidgetItem(symbol)
            item.setSelected(False)
            self.crypto_list.addItem(item)
        crypto_box.addWidget(self.crypto_list)

        # Add custom crypto
        add_crypto_layout = QHBoxLayout()
        self.custom_crypto_input = QLineEdit()
        self.custom_crypto_input.setPlaceholderText("Add custom (e.g., ADA/USD)")
        add_crypto_layout.addWidget(self.custom_crypto_input)
        add_crypto_btn = QPushButton("+")
        add_crypto_btn.setMaximumWidth(30)
        add_crypto_btn.clicked.connect(self._add_custom_crypto)
        add_crypto_layout.addWidget(add_crypto_btn)
        crypto_box.addLayout(add_crypto_layout)

        lists_layout.addLayout(crypto_box)
        asset_layout.addLayout(lists_layout)

        layout.addWidget(asset_group)

        # Timeframe & Settings
        settings_group = QGroupBox("Timeframes & Settings")
        settings_layout = QGridLayout(settings_group)

        # Timeframes
        settings_layout.addWidget(QLabel("Timeframes:"), 0, 0)
        tf_layout = QHBoxLayout()
        self.tf_1min = QCheckBox("1Min")
        self.tf_1min.setChecked(True)
        tf_layout.addWidget(self.tf_1min)
        self.tf_5min = QCheckBox("5Min")
        self.tf_5min.setChecked(True)
        tf_layout.addWidget(self.tf_5min)
        self.tf_15min = QCheckBox("15Min")
        self.tf_15min.setChecked(True)
        tf_layout.addWidget(self.tf_15min)
        self.tf_30min = QCheckBox("30Min")
        tf_layout.addWidget(self.tf_30min)
        self.tf_1hour = QCheckBox("1Hour")
        tf_layout.addWidget(self.tf_1hour)
        tf_layout.addStretch()
        settings_layout.addLayout(tf_layout, 0, 1)

        # Days back
        settings_layout.addWidget(QLabel("Days of History:"), 1, 0)
        self.days_spin = QSpinBox()
        self.days_spin.setRange(30, 1825)  # 1 month to 5 years
        self.days_spin.setValue(365)
        self.days_spin.setSuffix(" days")
        settings_layout.addWidget(self.days_spin, 1, 1)

        # Window size
        settings_layout.addWidget(QLabel("Pattern Window:"), 2, 0)
        self.window_spin = QSpinBox()
        self.window_spin.setRange(10, 100)
        self.window_spin.setValue(20)
        self.window_spin.setSuffix(" bars")
        settings_layout.addWidget(self.window_spin, 2, 1)

        # Step size
        settings_layout.addWidget(QLabel("Step Size:"), 3, 0)
        self.step_spin = QSpinBox()
        self.step_spin.setRange(1, 20)
        self.step_spin.setValue(5)
        self.step_spin.setSuffix(" bars")
        self.step_spin.setToolTip("Higher = fewer patterns, faster build")
        settings_layout.addWidget(self.step_spin, 3, 1)

        layout.addWidget(settings_group)

        # Progress
        progress_group = QGroupBox("Build Progress")
        progress_layout = QVBoxLayout(progress_group)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_bar)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        self.log_text.setFont(QFont("Consolas", 9))
        progress_layout.addWidget(self.log_text)

        # Build buttons
        btn_layout = QHBoxLayout()
        self.build_btn = QPushButton("Build Database")
        self.build_btn.clicked.connect(self._start_build)
        btn_layout.addWidget(self.build_btn)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(self._cancel_build)
        btn_layout.addWidget(self.cancel_btn)

        self.clear_db_btn = QPushButton("Clear Database")
        self.clear_db_btn.clicked.connect(self._clear_database)
        btn_layout.addWidget(self.clear_db_btn)

        btn_layout.addStretch()
        progress_layout.addLayout(btn_layout)

        layout.addWidget(progress_group)

        return widget

    def _create_search_tab(self) -> QWidget:
        """Create the search test tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        info_label = QLabel(
            "Test pattern search functionality.\n"
            "This simulates how the trading bot will query similar patterns."
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        # Search parameters
        search_group = QGroupBox("Search Parameters")
        search_layout = QGridLayout(search_group)

        search_layout.addWidget(QLabel("Symbol:"), 0, 0)
        self.search_symbol = QComboBox()
        self.search_symbol.setEditable(True)
        self.search_symbol.addItems(["AAPL", "MSFT", "NVDA", "BTC/USD", "ETH/USD"])
        search_layout.addWidget(self.search_symbol, 0, 1)

        search_layout.addWidget(QLabel("Timeframe:"), 1, 0)
        self.search_timeframe = QComboBox()
        self.search_timeframe.addItems(["1Min", "5Min", "15Min"])
        search_layout.addWidget(self.search_timeframe, 1, 1)

        search_layout.addWidget(QLabel("Trend Filter:"), 2, 0)
        self.search_trend = QComboBox()
        self.search_trend.addItems(["Any", "up", "down", "sideways"])
        search_layout.addWidget(self.search_trend, 2, 1)

        search_layout.addWidget(QLabel("Min Similarity:"), 3, 0)
        self.search_threshold = QSpinBox()
        self.search_threshold.setRange(50, 99)
        self.search_threshold.setValue(75)
        self.search_threshold.setSuffix("%")
        search_layout.addWidget(self.search_threshold, 3, 1)

        layout.addWidget(search_group)

        # Search button
        search_btn = QPushButton("Search Similar Patterns (Last 20 Bars)")
        search_btn.clicked.connect(self._run_search_test)
        layout.addWidget(search_btn)

        # Results
        results_group = QGroupBox("Search Results")
        results_layout = QVBoxLayout(results_group)

        self.search_results = QTextEdit()
        self.search_results.setReadOnly(True)
        self.search_results.setFont(QFont("Consolas", 9))
        results_layout.addWidget(self.search_results)

        layout.addWidget(results_group)

        return widget

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
            item = QListWidgetItem(symbol)
            item.setSelected(True)
            self.crypto_list.addItem(item)
            self.custom_crypto_input.clear()

    def _load_initial_state(self):
        """Load initial state on dialog open."""
        self._update_docker_status()
        self._refresh_stats()

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
            # Run async in thread
            import asyncio

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

        if self.crypto_radio.isChecked():
            for i in range(self.crypto_list.count()):
                item = self.crypto_list.item(i)
                if item.isSelected():
                    crypto_symbols.append(item.text())

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
        total_symbols = len(stock_symbols) + len(crypto_symbols)
        msg = (
            f"Build database with:\n"
            f"- {len(stock_symbols)} stock symbols\n"
            f"- {len(crypto_symbols)} crypto symbols\n"
            f"- {len(timeframes)} timeframes\n"
            f"- {self.days_spin.value()} days of history\n\n"
            f"This may take a while. Continue?"
        )
        if QMessageBox.question(self, "Confirm Build", msg) != QMessageBox.StandardButton.Yes:
            return

        # Clear log
        self.log_text.clear()
        self.progress_bar.setValue(0)

        # Disable build button, enable cancel
        self.build_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)

        # Build stocks first, then crypto
        all_symbols = stock_symbols + crypto_symbols
        is_crypto_flags = [False] * len(stock_symbols) + [True] * len(crypto_symbols)

        # For simplicity, build all at once (the worker will handle both)
        # We'll run stocks first, then crypto
        if stock_symbols:
            self._run_build(stock_symbols, timeframes, False)
        elif crypto_symbols:
            self._run_build(crypto_symbols, timeframes, True)

    def _run_build(self, symbols: list[str], timeframes: list[str], is_crypto: bool):
        """Run the build worker."""
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
        else:
            self._log(f"FAILED: {message}")

        self._build_worker = None

    def _update_progress(self, current: int, total: int):
        """Update progress bar."""
        if total > 0:
            self.progress_bar.setValue(int(current / total * 100))

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
            import asyncio

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
            import asyncio
            from datetime import timedelta, timezone

            symbol = self.search_symbol.currentText()
            timeframe = self.search_timeframe.currentText()
            trend = self.search_trend.currentText()
            threshold = self.search_threshold.value() / 100

            async def run_search():
                from src.core.market_data.types import DataRequest, Timeframe, AssetClass
                from src.core.market_data.history_provider import HistoryManager
                from src.core.pattern_db import get_pattern_service

                # Determine asset class
                is_crypto = "/" in symbol
                asset_class = AssetClass.CRYPTO if is_crypto else AssetClass.STOCK

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
                    symbol=symbol,
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
