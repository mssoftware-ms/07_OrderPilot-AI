from __future__ import annotations

from collections import deque
from pathlib import Path

from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QFont, QPixmap
from PyQt6.QtWidgets import QLabel, QPlainTextEdit, QVBoxLayout, QWidget

class StartupLogWindow(QWidget):
    """Frameless startup log window."""

    def __init__(self, icon_path: Path):
        super().__init__()
        self._queue: deque[str] = deque()
        self._timer = QTimer(self)
        self._timer.setInterval(500)
        self._timer.timeout.connect(self._drain_queue)

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setFixedSize(520, 420)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setStyleSheet("background: transparent;")

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(10, 10, 10, 10)
        outer_layout.setSpacing(0)

        self._container = QWidget(self)
        self._container.setObjectName("startupContainer")
        self._container.setStyleSheet(
            "QWidget#startupContainer { background-color: white; border-radius: 18px; }"
        )
        outer_layout.addWidget(self._container)

        layout = QVBoxLayout(self._container)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        self._icon_label = QLabel()
        self._icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pixmap = QPixmap(str(icon_path))
        if not pixmap.isNull():
            pixmap = pixmap.scaledToWidth(200, Qt.TransformationMode.SmoothTransformation)
            self._icon_label.setPixmap(pixmap)
        layout.addWidget(self._icon_label)

        self._log_view = QPlainTextEdit()
        self._log_view.setReadOnly(True)
        self._log_view.setMaximumBlockCount(1000)
        self._log_view.setFrameStyle(QPlainTextEdit.Shape.NoFrame)
        self._log_view.setStyleSheet(
            "QPlainTextEdit { background-color: white; color: black; border: none; }"
        )
        self._log_view.setFont(QFont("Aptos", 10))
        layout.addWidget(self._log_view)

    def enqueue_line(self, line: str) -> None:
        if line is None:
            return
        self._queue.append(line)
        if not self._timer.isActive():
            self._timer.start()

    def _drain_queue(self) -> None:
        if not self._queue:
            self._timer.stop()
            return
        line = self._queue.popleft()
        if line != "":
            self._log_view.appendPlainText(line)
