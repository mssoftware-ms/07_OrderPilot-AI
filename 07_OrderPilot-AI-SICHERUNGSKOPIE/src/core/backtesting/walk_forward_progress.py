"""Walk-Forward Runner - Progress Management.

Refactored from walk_forward_runner.py monolith.

Module 2/6 of walk_forward_runner.py split.

Contains:
- Progress callback management
"""

from __future__ import annotations

from collections.abc import Callable


class WalkForwardProgress:
    """Helper für WalkForwardRunner progress management."""

    def __init__(self, parent):
        """
        Args:
            parent: WalkForwardRunner Instanz
        """
        self.parent = parent

    def set_progress_callback(self, callback: Callable[[int, str], None]) -> None:
        """Setzt Callback für Progress-Updates."""
        self.parent._progress_callback = callback

    def emit_progress(self, progress: int, message: str) -> None:
        """Emittiert Progress-Update."""
        if self.parent._progress_callback:
            self.parent._progress_callback(progress, message)
