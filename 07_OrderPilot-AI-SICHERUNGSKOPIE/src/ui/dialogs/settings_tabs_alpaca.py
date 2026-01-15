"""Settings Tabs - Alpaca Market Data Provider.

Refactored from 820 LOC monolith using composition pattern.

Module 3/7 of settings_tabs_mixin.py split.

Contains:
- _build_alpaca_tab(): Alpaca API settings + historical download
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


class SettingsTabsAlpaca:
    """Helper für Alpaca Market Data Tab (inkl. Download-Worker)."""

    def __init__(self, parent):
        """
        Args:
            parent: SettingsDialog Instanz
        """
        self.parent = parent
        self._alpaca_download_thread = None
        self._alpaca_download_worker = None

    def build_alpaca_tab(self) -> QWidget:
        """Build Alpaca market data settings tab with download functionality."""
        alpaca_tab = QWidget()
        alpaca_layout = QVBoxLayout(alpaca_tab)

        # API Settings Group
        api_group = QGroupBox("API Settings")
        api_layout = QFormLayout(api_group)

        self.parent.alpaca_enabled = QCheckBox("Enable Alpaca provider")
        api_layout.addRow(self.parent.alpaca_enabled)

        self.parent.alpaca_api_key = QLineEdit()
        self.parent.alpaca_api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.parent.alpaca_api_key.setPlaceholderText("Enter Alpaca API key")
        api_layout.addRow("API Key:", self.parent.alpaca_api_key)

        self.parent.alpaca_api_secret = QLineEdit()
        self.parent.alpaca_api_secret.setEchoMode(QLineEdit.EchoMode.Password)
        self.parent.alpaca_api_secret.setPlaceholderText("Enter Alpaca API secret")
        api_layout.addRow("API Secret:", self.parent.alpaca_api_secret)

        alpaca_info = QLabel(
            "Alpaca provides real-time and historical market data for US stocks and crypto. "
            "Free tier includes IEX real-time data. Crypto market data works without API keys."
        )
        alpaca_info.setWordWrap(True)
        api_layout.addRow(alpaca_info)
        alpaca_layout.addWidget(api_group)

        # Historical Data Download Group
        download_group = QGroupBox("Historical Data Download")
        download_layout = QFormLayout(download_group)

        # Symbol input
        self.parent.alpaca_dl_symbol = QComboBox()
        self.parent.alpaca_dl_symbol.setEditable(True)
        self.parent.alpaca_dl_symbol.addItems(["BTC/USD", "ETH/USD", "SOL/USD", "DOGE/USD"])
        self.parent.alpaca_dl_symbol.setToolTip("Enter crypto symbol (e.g., BTC/USD, ETH/USD)")
        download_layout.addRow("Symbol:", self.parent.alpaca_dl_symbol)

        # Time period
        period_layout = QHBoxLayout()
        self.parent.alpaca_dl_days = QSpinBox()
        self.parent.alpaca_dl_days.setRange(1, 730)
        self.parent.alpaca_dl_days.setValue(365)
        self.parent.alpaca_dl_days.setSuffix(" days")
        period_layout.addWidget(self.parent.alpaca_dl_days)
        download_layout.addRow("Period:", period_layout)

        # Timeframe
        self.parent.alpaca_dl_timeframe = QComboBox()
        self.parent.alpaca_dl_timeframe.addItems(["1min", "5min", "15min", "1h", "4h", "1d"])
        self.parent.alpaca_dl_timeframe.setCurrentText("1min")
        download_layout.addRow("Timeframe:", self.parent.alpaca_dl_timeframe)

        # Estimated info
        self.parent.alpaca_dl_estimate = QLabel("")
        self._update_alpaca_estimate()
        self.parent.alpaca_dl_days.valueChanged.connect(self._update_alpaca_estimate)
        self.parent.alpaca_dl_timeframe.currentTextChanged.connect(self._update_alpaca_estimate)
        download_layout.addRow("Estimated:", self.parent.alpaca_dl_estimate)

        # Download button and progress
        btn_layout = QHBoxLayout()
        self.parent.alpaca_dl_btn = QPushButton("Download Historical Data")
        self.parent.alpaca_dl_btn.clicked.connect(self._start_alpaca_download)
        btn_layout.addWidget(self.parent.alpaca_dl_btn)

        self.parent.alpaca_dl_cancel_btn = QPushButton("Cancel")
        self.parent.alpaca_dl_cancel_btn.setEnabled(False)
        self.parent.alpaca_dl_cancel_btn.clicked.connect(self._cancel_alpaca_download)
        btn_layout.addWidget(self.parent.alpaca_dl_cancel_btn)
        download_layout.addRow(btn_layout)

        # Progress bar
        self.parent.alpaca_dl_progress = QProgressBar()
        self.parent.alpaca_dl_progress.setRange(0, 100)
        self.parent.alpaca_dl_progress.setValue(0)
        download_layout.addRow(self.parent.alpaca_dl_progress)

        # Status label
        self.parent.alpaca_dl_status = QLabel("Ready to download")
        self.parent.alpaca_dl_status.setWordWrap(True)
        download_layout.addRow(self.parent.alpaca_dl_status)

        alpaca_layout.addWidget(download_group)
        alpaca_layout.addStretch()

        return alpaca_tab

    def _start_alpaca_download(self):
        """Start Alpaca historical data download."""
        from src.ui.workers.historical_download_worker import DownloadThread, HistoricalDownloadWorker

        symbol = self.parent.alpaca_dl_symbol.currentText().strip()
        if not symbol:
            QMessageBox.warning(self.parent, "Input Error", "Please enter a symbol.")
            return

        days = self.parent.alpaca_dl_days.value()
        timeframe = self.parent.alpaca_dl_timeframe.currentText()

        # Create worker
        self._alpaca_download_worker = HistoricalDownloadWorker(
            provider_type="alpaca",
            symbols=[symbol],
            days=days,
            timeframe=timeframe,
        )

        # Connect signals
        self._alpaca_download_worker.progress.connect(self._on_alpaca_progress)
        self._alpaca_download_worker.finished.connect(self._on_alpaca_finished)
        self._alpaca_download_worker.error.connect(self._on_alpaca_error)

        # Create and start thread
        self._alpaca_download_thread = DownloadThread(self._alpaca_download_worker)
        self._alpaca_download_thread.start()

        # Update UI
        self.parent.alpaca_dl_btn.setEnabled(False)
        self.parent.alpaca_dl_cancel_btn.setEnabled(True)
        self.parent.alpaca_dl_progress.setValue(0)
        self.parent.alpaca_dl_status.setText(f"Starting download for {symbol}...")

    def _cancel_alpaca_download(self):
        """Cancel Alpaca download."""
        if self._alpaca_download_worker:
            self._alpaca_download_worker.cancel()
        self.parent.alpaca_dl_status.setText("Cancelling...")

    def _on_alpaca_progress(self, percentage: int, message: str):
        """Handle Alpaca download progress."""
        self.parent.alpaca_dl_progress.setValue(percentage)
        self.parent.alpaca_dl_status.setText(message)

    def _on_alpaca_finished(self, success: bool, message: str, results: dict):
        """Handle Alpaca download completion."""
        self.parent.alpaca_dl_btn.setEnabled(True)
        self.parent.alpaca_dl_cancel_btn.setEnabled(False)
        self.parent.alpaca_dl_progress.setValue(100 if success else 0)
        self.parent.alpaca_dl_status.setText(message)

        if success:
            QMessageBox.information(self.parent, "Download Complete", message)
        else:
            QMessageBox.warning(self.parent, "Download Failed", message)

        self._alpaca_download_thread = None
        self._alpaca_download_worker = None

    def _on_alpaca_error(self, error_message: str):
        """Handle Alpaca download error."""
        self.parent.alpaca_dl_btn.setEnabled(True)
        self.parent.alpaca_dl_cancel_btn.setEnabled(False)
        self.parent.alpaca_dl_progress.setValue(0)
        self.parent.alpaca_dl_status.setText(f"Error: {error_message}")
        QMessageBox.critical(self.parent, "Download Error", error_message)
        self._alpaca_download_thread = None
        self._alpaca_download_worker = None

    def _update_alpaca_estimate(self):
        """Update Alpaca download estimate label."""
        days = self.parent.alpaca_dl_days.value()
        timeframe = self.parent.alpaca_dl_timeframe.currentText()

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

        self.parent.alpaca_dl_estimate.setText(f"~{total_bars:,} bars")
