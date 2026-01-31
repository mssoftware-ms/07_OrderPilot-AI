"""OHLC Validation Worker.

Background worker for validating and fixing OHLC data without blocking the UI.
"""

import logging
from typing import Optional

from src.ui.workers.base_worker import BaseWorker

logger = logging.getLogger(__name__)


class OHLCValidationWorker(BaseWorker):
    """Worker for validating and fixing OHLC data in background."""

    def __init__(self, symbol: Optional[str] = None, dry_run: bool = False):
        """Initialize validation worker.

        Args:
            symbol: Optional symbol to validate (None = all symbols)
            dry_run: If True, only report issues without fixing
        """
        super().__init__()
        self.symbol = symbol
        self.dry_run = dry_run

    def _execute(self):
        """Validation implementation."""
        from src.database.ohlc_validator import validate_and_fix_ohlc

        self.progress.emit(10, "Starting OHLC validation...")

        # Progress callback
        def progress_callback(current: int, total: int, message: str):
            if self.is_cancelled():
                return
            if total > 0:
                pct = int((current / total) * 80) + 10  # 10-90% range
                self.progress.emit(pct, message)

        if self.is_cancelled():
            self.emit_cancellation_result("Validation cancelled")
            return

        # Run validation
        results = validate_and_fix_ohlc(
            symbol=self.symbol,
            dry_run=self.dry_run,
            progress_callback=progress_callback
        )

        if self.is_cancelled():
            self.emit_cancellation_result("Validation cancelled")
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


# Use WorkerThread from base_worker module instead of custom thread wrapper
from src.ui.workers.base_worker import WorkerThread

# Alias for backward compatibility
ValidationThread = WorkerThread
