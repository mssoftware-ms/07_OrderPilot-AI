"""Settings Dialog - Data Quality Tab.

Provides:
- Provider selection (Alpaca, Bitunix)
- Database verification tool
- Manual OHLC validation
"""

import logging
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

logger = logging.getLogger(__name__)


class DataQualityVerificationWorker(QThread):
    """Worker thread for database verification."""

    progress = pyqtSignal(str)  # status message
    finished = pyqtSignal(bool, str)  # success, message

    def __init__(self, db_path: str, symbol: str, timeframe: str):
        super().__init__()
        self.db_path = db_path
        self.symbol = symbol
        self.timeframe = timeframe

    def run(self):
        """Run verification in background."""
        try:
            import sqlite3
            from datetime import datetime

            self.progress.emit("Connecting to database...")
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            self.progress.emit(f"Querying data for {self.symbol}...")
            cursor.execute(
                "SELECT timestamp, open, high, low, close, volume FROM market_bars WHERE symbol = ? ORDER BY timestamp ASC",
                (self.symbol,)
            )
            bars = cursor.fetchall()

            if not bars:
                self.finished.emit(False, f"No data found for {self.symbol}")
                conn.close()
                return

            total_bars = len(bars)
            first_ts = datetime.fromisoformat(bars[0][0])
            last_ts = datetime.fromisoformat(bars[-1][0])
            time_span = last_ts - first_ts
            days = time_span.days + (time_span.seconds / 86400)

            # Timeframe intervals
            timeframe_minutes = {
                "1min": 1, "5min": 5, "15min": 15,
                "1h": 60, "4h": 240, "1d": 1440,
            }
            expected_interval = timeframe_minutes.get(self.timeframe, 1)

            self.progress.emit("Analyzing intervals...")

            # Calculate expected bars
            total_minutes = time_span.total_seconds() / 60
            expected_bars = int(total_minutes / expected_interval) + 1
            coverage_pct = (total_bars / expected_bars) * 100 if expected_bars > 0 else 0
            missing_bars = expected_bars - total_bars

            # Analyze intervals
            intervals = []
            for i in range(1, len(bars)):
                prev_ts = datetime.fromisoformat(bars[i-1][0])
                curr_ts = datetime.fromisoformat(bars[i][0])
                interval_minutes = (curr_ts - prev_ts).total_seconds() / 60
                intervals.append(interval_minutes)

            avg_interval = sum(intervals) / len(intervals) if intervals else 0
            correct_intervals = sum(1 for i in intervals if abs(i - expected_interval) < 0.1)

            self.progress.emit("Detecting gaps...")

            # Detect gaps
            gap_threshold = expected_interval * 2
            gaps = []
            for i in range(1, len(bars)):
                prev_ts = datetime.fromisoformat(bars[i-1][0])
                curr_ts = datetime.fromisoformat(bars[i][0])
                interval_minutes = (curr_ts - prev_ts).total_seconds() / 60
                if interval_minutes > gap_threshold:
                    gaps.append({
                        'start': prev_ts,
                        'end': curr_ts,
                        'duration_min': interval_minutes,
                    })

            self.progress.emit("Checking OHLC consistency...")

            # OHLC consistency
            ohlc_errors = 0
            for bar in bars:
                o, h, l, c = float(bar[1]), float(bar[2]), float(bar[3]), float(bar[4])
                if h < max(o, c) or l > min(o, c):
                    ohlc_errors += 1

            conn.close()

            # Build result message
            result = [
                f"✅ Verification Complete for {self.symbol}",
                f"",
                f"📊 Statistics:",
                f"  Total bars: {total_bars:,}",
                f"  Time span: {days:.1f} days",
                f"  Coverage: {coverage_pct:.2f}% ({missing_bars:,} missing)",
                f"",
                f"⏱️  Intervals:",
                f"  Average: {avg_interval:.2f} min (expected: {expected_interval} min)",
                f"  Correct: {correct_intervals:,}/{len(intervals):,} ({100*correct_intervals/len(intervals):.1f}%)",
                f"",
                f"🔍 Data Quality:",
                f"  Gaps (>{gap_threshold:.0f}min): {len(gaps)}",
                f"  OHLC errors: {ohlc_errors}",
            ]

            # Status indicators
            status = []
            if abs(avg_interval - expected_interval) < 0.5:
                status.append("✅ Timeframe verified")
            else:
                status.append(f"⚠️  Timeframe mismatch")

            if coverage_pct >= 99.0:
                status.append("✅ Excellent coverage")
            elif coverage_pct >= 95.0:
                status.append("⚠️  Good coverage")
            else:
                status.append("❌ Poor coverage")

            if not gaps:
                status.append("✅ No gaps")
            else:
                status.append(f"⚠️  {len(gaps)} gaps found")

            if ohlc_errors == 0:
                status.append("✅ OHLC valid")
            else:
                status.append(f"❌ {ohlc_errors} OHLC errors")

            result.append("")
            result.extend(status)

            self.finished.emit(True, "\n".join(result))

        except Exception as e:
            logger.error(f"Verification error: {e}", exc_info=True)
            self.finished.emit(False, f"Error: {str(e)}")


class SettingsTabsDataQuality:
    """Helper class for Data Quality tab creation."""

    def __init__(self, parent):
        """Initialize with parent SettingsDialog reference.

        Args:
            parent: Parent SettingsDialog instance
        """
        self.parent = parent
        self._verification_worker = None
        self._verification_thread = None
        self._validation_worker = None
        self._validation_thread = None

    def create_data_quality_tab(self) -> QWidget:
        """Create data quality tab.

        Returns:
            QWidget containing data quality settings
        """
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Provider selection
        provider_group = QGroupBox("Provider Selection")
        provider_layout = QFormLayout()

        self.parent.dq_provider = QComboBox()
        self.parent.dq_provider.addItems(["Bitunix", "Alpaca"])
        self.parent.dq_provider.setToolTip("Select data provider to verify")
        self.parent.dq_provider.currentTextChanged.connect(self._update_provider_info)
        provider_layout.addRow("Provider:", self.parent.dq_provider)

        self.parent.dq_provider_info = QLabel("Database: data/orderpilot.db")
        self.parent.dq_provider_info.setWordWrap(True)
        self.parent.dq_provider_info.setStyleSheet("color: #888;")
        provider_layout.addRow("", self.parent.dq_provider_info)

        provider_group.setLayout(provider_layout)
        layout.addWidget(provider_group)

        # Database Verification
        verify_group = QGroupBox("Database Verification")
        verify_layout = QFormLayout()

        # Symbol input
        self.parent.dq_verify_symbol = QComboBox()
        self.parent.dq_verify_symbol.setEditable(True)
        self.parent.dq_verify_symbol.addItems(["bitunix:BTCUSDT", "bitunix:ETHUSDT", "alpaca:BTC/USD", "alpaca:ETH/USD"])
        self.parent.dq_verify_symbol.setToolTip("Symbol to verify (provider prefix will be added if missing)")
        verify_layout.addRow("Symbol:", self.parent.dq_verify_symbol)

        # Timeframe selection
        self.parent.dq_verify_timeframe = QComboBox()
        self.parent.dq_verify_timeframe.addItems(["1min", "5min", "15min", "1h", "4h", "1d"])
        self.parent.dq_verify_timeframe.setCurrentText("1min")
        self.parent.dq_verify_timeframe.setToolTip("Expected timeframe to verify")
        verify_layout.addRow("Timeframe:", self.parent.dq_verify_timeframe)

        # Verify button
        verify_btn_layout = QHBoxLayout()
        self.parent.dq_verify_btn = QPushButton("Verify Data")
        self.parent.dq_verify_btn.clicked.connect(self._start_verification)
        verify_btn_layout.addWidget(self.parent.dq_verify_btn)
        verify_btn_layout.addStretch()
        verify_layout.addRow("Action:", verify_btn_layout)

        # Status
        self.parent.dq_verify_status = QLabel("Ready")
        self.parent.dq_verify_status.setWordWrap(True)
        verify_layout.addRow("Status:", self.parent.dq_verify_status)

        verify_group.setLayout(verify_layout)
        layout.addWidget(verify_group)

        # Manual OHLC Validation (moved from Bitunix tab)
        validation_group = QGroupBox("Manual OHLC Validation")
        validation_layout = QFormLayout()

        # Description
        desc_label = QLabel("Fix OHLC inconsistencies in database (high < open/close, low > open/close)")
        desc_label.setWordWrap(True)
        validation_layout.addRow("", desc_label)

        # Buttons
        btn_layout = QHBoxLayout()
        self.parent.dq_validate_btn = QPushButton("Validate & Fix")
        self.parent.dq_validate_btn.clicked.connect(self._start_validation)
        btn_layout.addWidget(self.parent.dq_validate_btn)

        self.parent.dq_validate_cancel_btn = QPushButton("Cancel")
        self.parent.dq_validate_cancel_btn.setEnabled(False)
        self.parent.dq_validate_cancel_btn.clicked.connect(self._cancel_validation)
        btn_layout.addWidget(self.parent.dq_validate_cancel_btn)

        btn_layout.addStretch()
        validation_layout.addRow("Action:", btn_layout)

        # Progress
        self.parent.dq_validate_progress = QProgressBar()
        self.parent.dq_validate_progress.setMaximumHeight(18)
        validation_layout.addRow("Progress:", self.parent.dq_validate_progress)

        # Status
        self.parent.dq_validate_status = QLabel("Ready")
        self.parent.dq_validate_status.setWordWrap(True)
        validation_layout.addRow("Status:", self.parent.dq_validate_status)

        validation_group.setLayout(validation_layout)
        layout.addWidget(validation_group)

        layout.addStretch()
        return tab

    def _update_provider_info(self):
        """Update provider info label."""
        provider = self.parent.dq_provider.currentText().lower()

        # Update symbol prefix example
        if provider == "bitunix":
            self.parent.dq_verify_symbol.setEditText("bitunix:BTCUSDT")
        elif provider == "alpaca":
            self.parent.dq_verify_symbol.setEditText("alpaca:BTC/USD")

        self.parent.dq_provider_info.setText(f"Database: data/orderpilot.db (provider: {provider})")

    def _start_verification(self):
        """Start database verification."""
        symbol = self.parent.dq_verify_symbol.currentText().strip()
        if not symbol:
            QMessageBox.warning(self.parent, "Input Error", "Please enter a symbol.")
            return

        # Add provider prefix if missing
        provider = self.parent.dq_provider.currentText().lower()
        if ":" not in symbol:
            symbol = f"{provider}:{symbol}"

        timeframe = self.parent.dq_verify_timeframe.currentText()
        db_path = "data/orderpilot.db"

        # Create and start worker
        self._verification_worker = DataQualityVerificationWorker(db_path, symbol, timeframe)
        self._verification_worker.progress.connect(self._on_verification_progress)
        self._verification_worker.finished.connect(self._on_verification_finished)
        self._verification_worker.start()

        # Update UI
        self.parent.dq_verify_btn.setEnabled(False)
        self.parent.dq_verify_status.setText(f"Verifying {symbol}...")

    def _on_verification_progress(self, message: str):
        """Handle verification progress."""
        self.parent.dq_verify_status.setText(message)

    def _on_verification_finished(self, success: bool, message: str):
        """Handle verification completion."""
        self.parent.dq_verify_btn.setEnabled(True)
        self.parent.dq_verify_status.setText("Completed")

        if success:
            QMessageBox.information(self.parent, "Verification Results", message)
        else:
            QMessageBox.warning(self.parent, "Verification Error", message)

    def _start_validation(self):
        """Start OHLC validation."""
        from src.ui.workers.ohlc_validation_worker import OHLCValidationThread, OHLCValidationWorker

        # Get provider selection for filtering
        provider = self.parent.dq_provider.currentText().lower()
        symbol_filter = None  # Validate all by default

        # Create worker
        self._validation_worker = OHLCValidationWorker(
            symbol=symbol_filter,
            dry_run=False
        )

        # Connect signals
        self._validation_worker.progress.connect(self._on_validation_progress)
        self._validation_worker.finished.connect(self._on_validation_finished)
        self._validation_worker.error.connect(self._on_validation_error)

        # Create and start thread
        self._validation_thread = OHLCValidationThread(self._validation_worker)
        self._validation_thread.start()

        # Update UI
        self.parent.dq_validate_btn.setEnabled(False)
        self.parent.dq_validate_cancel_btn.setEnabled(True)
        self.parent.dq_validate_progress.setValue(0)
        self.parent.dq_validate_status.setText("Starting OHLC validation...")

    def _cancel_validation(self):
        """Cancel OHLC validation."""
        if self._validation_worker:
            self._validation_worker.cancel()
        self.parent.dq_validate_status.setText("Cancelling...")

    def _on_validation_progress(self, percentage: int, message: str):
        """Handle validation progress."""
        self.parent.dq_validate_progress.setValue(percentage)
        self.parent.dq_validate_status.setText(message)

    def _on_validation_finished(self, success: bool, message: str, results: dict):
        """Handle validation completion."""
        self.parent.dq_validate_btn.setEnabled(True)
        self.parent.dq_validate_cancel_btn.setEnabled(False)
        self.parent.dq_validate_progress.setValue(100 if success else 0)
        self.parent.dq_validate_status.setText(message)

        if success:
            details = [
                f"Invalid bars found: {results.get('invalid_bars', 0)}",
                f"Bars fixed: {results.get('fixed_bars', 0)}",
                f"Symbols affected: {', '.join(results.get('symbols_affected', [])) if results.get('symbols_affected') else 'None'}",
            ]
            QMessageBox.information(
                self.parent,
                "OHLC Validation Complete",
                f"{message}\n\n" + "\n".join(details)
            )

    def _on_validation_error(self, error_msg: str):
        """Handle validation error."""
        self.parent.dq_validate_btn.setEnabled(True)
        self.parent.dq_validate_cancel_btn.setEnabled(False)
        self.parent.dq_validate_status.setText(f"Error: {error_msg}")
        QMessageBox.critical(self.parent, "Validation Error", error_msg)
