"""Settings Tabs - Bitunix Futures Market Data Provider.

Refactored from 820 LOC monolith using composition pattern.

Module 4/7 of settings_tabs_mixin.py split.

Contains:
- _build_bitunix_tab(): Bitunix API settings + historical download
- Download Worker management (start, cancel, progress, finish, error)
- Download estimate calculation
"""

import logging

from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

logger = logging.getLogger(__name__)


class SettingsTabsBitunix:
    """Helper für Bitunix Market Data Tab (inkl. Download-Worker)."""

    def __init__(self, parent):
        """
        Args:
            parent: SettingsDialog Instanz
        """
        self.parent = parent
        self._bitunix_download_thread = None
        self._bitunix_download_worker = None

    def build_bitunix_tab(self) -> QWidget:
        """Create Bitunix Futures settings tab with download functionality."""
        bitunix_tab = QWidget()
        bitunix_layout = QVBoxLayout(bitunix_tab)

        # API Settings Group
        api_group = QGroupBox("API Settings (only for trading)")
        api_layout = QFormLayout(api_group)

        self.parent.bitunix_enabled = QCheckBox("Enable Bitunix Futures provider")
        api_layout.addRow(self.parent.bitunix_enabled)

        self.parent.bitunix_api_key = QLineEdit()
        self.parent.bitunix_api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.parent.bitunix_api_key.setPlaceholderText("Enter Bitunix API key (not required for market data)")
        api_layout.addRow("API Key:", self.parent.bitunix_api_key)

        self.parent.bitunix_api_secret = QLineEdit()
        self.parent.bitunix_api_secret.setEchoMode(QLineEdit.EchoMode.Password)
        self.parent.bitunix_api_secret.setPlaceholderText("Enter Bitunix API secret")
        api_layout.addRow("API Secret:", self.parent.bitunix_api_secret)

        self.parent.bitunix_testnet = QCheckBox("Use Testnet (Recommended for testing)")
        self.parent.bitunix_testnet.setChecked(True)
        self.parent.bitunix_testnet.setToolTip(
            "When enabled, uses Bitunix testnet environment for safe testing. "
            "Uncheck only when you want to trade with real money!"
        )
        api_layout.addRow(self.parent.bitunix_testnet)

        bitunix_info = QLabel(
            "<b>Bitunix Futures Trading</b><br>"
            "API keys are only needed for trading. Market data (kline) is public.<br>"
            "Get keys from: <a href='https://www.bitunix.com/api'>bitunix.com/api</a>"
        )
        bitunix_info.setWordWrap(True)
        bitunix_info.setOpenExternalLinks(True)
        api_layout.addRow(bitunix_info)
        bitunix_layout.addWidget(api_group)

        # Historical Data Download Group
        download_group = QGroupBox("Historical Data Download (no API key required)")
        download_layout = QFormLayout(download_group)

        # Symbol input
        self.parent.bitunix_dl_symbol = QComboBox()
        self.parent.bitunix_dl_symbol.setEditable(True)
        self.parent.bitunix_dl_symbol.addItems(
            ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "DOGEUSDT", "ADAUSDT", "AVAXUSDT"]
        )
        self.parent.bitunix_dl_symbol.setToolTip("Enter Bitunix futures symbol (e.g., BTCUSDT)")
        download_layout.addRow("Symbol:", self.parent.bitunix_dl_symbol)

        # Time period
        period_layout = QHBoxLayout()
        self.parent.bitunix_dl_days = QSpinBox()
        self.parent.bitunix_dl_days.setRange(1, 730)
        self.parent.bitunix_dl_days.setValue(365)
        self.parent.bitunix_dl_days.setSuffix(" days")
        period_layout.addWidget(self.parent.bitunix_dl_days)
        download_layout.addRow("Period:", period_layout)

        # Timeframe
        self.parent.bitunix_dl_timeframe = QComboBox()
        self.parent.bitunix_dl_timeframe.addItems(["1min", "5min", "15min", "1h", "4h", "1d"])
        self.parent.bitunix_dl_timeframe.setCurrentText("1min")
        download_layout.addRow("Timeframe:", self.parent.bitunix_dl_timeframe)

        # Bad Tick Filter Checkbox
        self.parent.bitunix_filter_bad_ticks = QCheckBox("Enable Bad Tick Filter (Hampel)")
        self.parent.bitunix_filter_bad_ticks.setChecked(True)
        self.parent.bitunix_filter_bad_ticks.setToolTip(
            "Automatically detect and clean bad price ticks using Hampel filter. "
            "Uncheck to download raw data without filtering."
        )
        download_layout.addRow(self.parent.bitunix_filter_bad_ticks)

        # Estimated info
        self.parent.bitunix_dl_estimate = QLabel("")
        self._update_bitunix_estimate()
        self.parent.bitunix_dl_days.valueChanged.connect(self._update_bitunix_estimate)
        self.parent.bitunix_dl_timeframe.currentTextChanged.connect(self._update_bitunix_estimate)
        download_layout.addRow("Estimated:", self.parent.bitunix_dl_estimate)

        # Download button and progress
        btn_layout = QHBoxLayout()
        self.parent.bitunix_dl_btn = QPushButton("Download Full History")
        self.parent.bitunix_dl_btn.setToolTip("Deletes existing data and downloads full history (slow)")
        self.parent.bitunix_dl_btn.clicked.connect(self._start_bitunix_download)
        btn_layout.addWidget(self.parent.bitunix_dl_btn)

        self.parent.bitunix_sync_btn = QPushButton("Sync -> Today")
        self.parent.bitunix_sync_btn.setToolTip("Updates existing data with missing recent candles (fast)")
        self.parent.bitunix_sync_btn.clicked.connect(self._start_bitunix_sync)
        btn_layout.addWidget(self.parent.bitunix_sync_btn)

        self.parent.bitunix_dl_cancel_btn = QPushButton("Cancel")
        self.parent.bitunix_dl_cancel_btn.setEnabled(False)
        self.parent.bitunix_dl_cancel_btn.clicked.connect(self._cancel_bitunix_download)
        btn_layout.addWidget(self.parent.bitunix_dl_cancel_btn)
        download_layout.addRow(btn_layout)

        # Progress bar
        self.parent.bitunix_dl_progress = QProgressBar()
        self.parent.bitunix_dl_progress.setRange(0, 100)
        self.parent.bitunix_dl_progress.setValue(0)
        download_layout.addRow(self.parent.bitunix_dl_progress)

        # Status label
        self.parent.bitunix_dl_status = QLabel("Ready to download (public API, no keys needed)")
        self.parent.bitunix_dl_status.setWordWrap(True)
        download_layout.addRow(self.parent.bitunix_dl_status)

        bitunix_layout.addWidget(download_group)
        bitunix_layout.addStretch()

        return bitunix_tab

    def _update_bitunix_estimate(self):
        """Update download estimate label."""
        days = self.parent.bitunix_dl_days.value()
        timeframe = self.parent.bitunix_dl_timeframe.currentText()

        # Calculate bars per day
        bars_per_day = {
            "1min": 1440,
            "5min": 288,
            "15min": 96,
            "1h": 24,
            "4h": 6,
            "1d": 1,
        }
        bpd = bars_per_day.get(timeframe, 1440)
        total_bars = days * bpd
        requests = (total_bars // 200) + 1

        self.parent.bitunix_dl_estimate.setText(f"~{total_bars:,} bars, ~{requests:,} API requests")

    def _start_bitunix_download(self):
        """Start Bitunix historical data download."""
        self._start_download_worker(mode="download")

    def _start_bitunix_sync(self):
        """Start Bitunix sync (update only)."""
        self._start_download_worker(mode="sync")

    def _start_download_worker(self, mode: str):
        """Start the download worker with specified mode."""
        from src.ui.workers.historical_download_worker import DownloadThread, HistoricalDownloadWorker

        symbol = self.parent.bitunix_dl_symbol.currentText().strip()
        if not symbol:
            QMessageBox.warning(self.parent, "Input Error", "Please enter a symbol.")
            return

        days = self.parent.bitunix_dl_days.value()
        timeframe = self.parent.bitunix_dl_timeframe.currentText()
        enable_filter = self.parent.bitunix_filter_bad_ticks.isChecked()

        # Create worker
        self._bitunix_download_worker = HistoricalDownloadWorker(
            provider_type="bitunix",
            symbols=[symbol],
            days=days,
            timeframe=timeframe,
            mode=mode,
            enable_bad_tick_filter=enable_filter,
        )

        # Connect signals
        self._bitunix_download_worker.progress.connect(self._on_bitunix_progress)
        self._bitunix_download_worker.finished.connect(self._on_bitunix_finished)
        self._bitunix_download_worker.error.connect(self._on_bitunix_error)

        # Create and start thread
        self._bitunix_download_thread = DownloadThread(self._bitunix_download_worker)
        self._bitunix_download_thread.start()

        # Update UI
        self.parent.bitunix_dl_btn.setEnabled(False)
        self.parent.bitunix_sync_btn.setEnabled(False)
        self.parent.bitunix_dl_cancel_btn.setEnabled(True)
        self.parent.bitunix_dl_progress.setValue(0)
        
        action = "download" if mode == "download" else "sync"
        self.parent.bitunix_dl_status.setText(f"Starting {action} for {symbol}...")

    def _cancel_bitunix_download(self):
        """Cancel Bitunix download."""
        if self._bitunix_download_worker:
            self._bitunix_download_worker.cancel()
        self.parent.bitunix_dl_status.setText("Cancelling...")

    def _on_bitunix_progress(self, percentage: int, message: str):
        """Handle Bitunix download progress."""
        self.parent.bitunix_dl_progress.setValue(percentage)
        self.parent.bitunix_dl_status.setText(message)

    def _on_bitunix_finished(self, success: bool, message: str, results: dict):
        """Handle Bitunix download completion."""
        self.parent.bitunix_dl_btn.setEnabled(True)
        self.parent.bitunix_sync_btn.setEnabled(True)
        self.parent.bitunix_dl_cancel_btn.setEnabled(False)
        self.parent.bitunix_dl_progress.setValue(100 if success else 0)
        self.parent.bitunix_dl_status.setText(message)

        if success:
            QMessageBox.information(self.parent, "Operation Complete", message)
        else:
            QMessageBox.warning(self.parent, "Operation Failed", message)

        self._bitunix_download_thread = None
        self._bitunix_download_worker = None

    def _on_bitunix_error(self, error_message: str):
        """Handle Bitunix download error."""
        self.parent.bitunix_dl_btn.setEnabled(True)
        self.parent.bitunix_sync_btn.setEnabled(True)
        self.parent.bitunix_dl_cancel_btn.setEnabled(False)
        self.parent.bitunix_dl_progress.setValue(0)
        self.parent.bitunix_dl_status.setText(f"Error: {error_message}")
        QMessageBox.critical(self.parent, "Error", error_message)
        self._bitunix_download_thread = None
        self._bitunix_download_worker = None
