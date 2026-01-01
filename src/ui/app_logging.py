from __future__ import annotations

import logging
from typing import Any

from PyQt6.QtCore import QObject, pyqtSignal

from .app_console_utils import _show_console_window

class ConsoleOnErrorHandler(logging.Handler):
    """Show console window on errors."""

    def emit(self, record: logging.LogRecord) -> None:
        if record.levelno >= logging.ERROR:
            _show_console_window()

class LogStream(QObject):
    """Redirect stdout/stderr to Qt signal (optional mirror)."""

    text_written = pyqtSignal(str)

    def __init__(self, mirror: Any | None = None) -> None:
        super().__init__()
        self._buffer = ""
        self._mirror = mirror

    def write(self, text: str) -> None:
        if not text:
            return
        if self._mirror is not None:
            try:
                self._mirror.write(text)
                self._mirror.flush()
            except Exception:
                pass
        self._buffer += text
        while "\n" in self._buffer:
            line, self._buffer = self._buffer.split("\n", 1)
            self.text_written.emit(line)

    def flush(self) -> None:
        if self._mirror is not None:
            try:
                self._mirror.flush()
            except Exception:
                pass
        if self._buffer:
            self.text_written.emit(self._buffer)
            self._buffer = ""
