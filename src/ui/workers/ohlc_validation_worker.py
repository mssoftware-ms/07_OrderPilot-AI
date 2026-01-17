"""OHLC Validation Worker.

Background worker for validating and fixing OHLC data without blocking the UI.
"""

import logging
from typing import Optional

from PyQt6.QtCore import QObject, QThread, pyqtSignal

logger = logging.getLogger(__name__)


class OHLCValidationWorker(QObject):
    """Worker for validating and fixing OHLC data in background."""

    # Signals
    progress = pyqtSignal(int, str)  # (percentage, status_message)
    finished = pyqtSignal(bool, str, dict)  # (success, message, results)
    error = pyqtSignal(str)  # error_message

    def __init__(self, symbol: Optional[str] = None, dry_run: bool = False):
        """Initialize validation worker.

        Args:
            symbol: Optional symbol to validate (None = all symbols)
            dry_run: If True, only report issues without fixing
        """
        super().__init__()
        self.symbol = symbol
        self.dry_run = dry_run
        self._cancelled = False

    def cancel(self):
        """Cancel the validation."""
        self._cancelled = True

    def run(self):
        """Execute the validation in background thread."""
        try:
            self._validate()
        except Exception as e:
            logger.error(f"Validation worker error: {e}", exc_info=True)
            self.error.emit(str(e))

    def _validate(self):
        """Validation implementation."""
        from src.database.ohlc_validator import validate_and_fix_ohlc

        self.progress.emit(10, "Starting OHLC validation...")

        # Progress callback
        def progress_callback(current: int, total: int, message: str):
            if self._cancelled:
                return
            if total > 0:
                pct = int((current / total) * 80) + 10  # 10-90% range
                self.progress.emit(pct, message)

        if self._cancelled:
            self.finished.emit(False, "Validation cancelled", {})
            return

        # Run validation
        results = validate_and_fix_ohlc(
            symbol=self.symbol,
            dry_run=self.dry_run,
            progress_callback=progress_callback
        )

        if self._cancelled:
            self.finished.emit(False, "Validation cancelled", {})
            return

        # Build result message
        invalid_bars = results['invalid_bars']
        fixed_bars = results['fixed_bars']
        symbols = results['symbols_affected']

        if invalid_bars == 0:
            message = "✅ All data is valid! No OHLC inconsistencies found."
        elif self.dry_run:
            message = f"Found {invalid_bars} OHLC inconsistencies (dry run - not fixed)"
        else:
            message = f"✅ Fixed {fixed_bars} OHLC inconsistencies!"

        if symbols:
            message += f"\n\nSymbols: {', '.join(symbols[:5])}"
            if len(symbols) > 5:
                message += f" (+{len(symbols)-5} more)"

        self.progress.emit(100, "Validation complete!")
        self.finished.emit(True, message, results)


class ValidationThread(QThread):
    """Thread wrapper for validation worker."""

    def __init__(self, worker: OHLCValidationWorker):
        super().__init__()
        self.worker = worker

    def run(self):
        """Run the worker."""
        self.worker.run()
