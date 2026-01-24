"""Optimization Waiting Dialog - Shows while processing results after optimization.

Displays a fun waiting screen with animated spinner and trading jokes
while the optimization results are being processed.
"""

from __future__ import annotations

import logging
import math
import time
from pathlib import Path
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QPainter, QPen, QFontMetrics, QPixmap
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QWidget,
    QGraphicsDropShadowEffect,
    QApplication,
)

logger = logging.getLogger(__name__)

# Joke display duration in milliseconds
JOKE_DISPLAY_DURATION_MS = 10000


def _get_app_icon_path() -> Path:
    """Get the app icon path for the spinner logo."""
    root_dir = Path(__file__).resolve().parents[3]
    return root_dir / "02_Marketing" / "Icons" / "Icon-Orderpilot-AI-Arrow-256x256.png"


class SpinnerWidget(QWidget):
    """Animated spinner widget with rotating logo in center."""

    def __init__(self, parent=None, logo_path: Path | None = None):
        super().__init__(parent)
        self.setFixedSize(120, 120)  # Larger to accommodate logo
        self._angle = 0
        self._logo_pixmap = None
        self._logo_size = 50  # Logo size in pixels

        # Load logo
        if logo_path is None:
            logo_path = _get_app_icon_path()

        if logo_path.exists():
            pixmap = QPixmap(str(logo_path))
            if not pixmap.isNull():
                # Scale logo to fit in center of spinner
                self._logo_pixmap = pixmap.scaled(
                    self._logo_size, self._logo_size,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                logger.debug(f"Loaded spinner logo: {logo_path}")
            else:
                logger.warning(f"Could not load spinner logo: {logo_path}")
        else:
            logger.warning(f"Spinner logo not found: {logo_path}")

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._rotate)
        self._timer.start(30)  # ~33 FPS

    def _rotate(self):
        self._angle = (self._angle + 3) % 360  # Slightly slower rotation
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        center = self.rect().center()
        outer_radius = 50  # Outer spinner radius
        inner_radius = 35  # Inner spinner radius (where arcs start)

        # Draw spinning arcs (outer ring)
        for i in range(12):  # 12 segments for smoother look
            angle = self._angle + i * 30
            opacity = 1.0 - (i * 0.07)
            color = QColor("#F29F05")
            color.setAlphaF(max(0.2, opacity))

            pen = QPen(color)
            pen.setWidth(4)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)

            # Calculate arc position
            rad = math.radians(angle)
            x1 = center.x() + int(inner_radius * math.cos(rad))
            y1 = center.y() + int(inner_radius * math.sin(rad))
            x2 = center.x() + int(outer_radius * math.cos(rad))
            y2 = center.y() + int(outer_radius * math.sin(rad))

            painter.drawLine(x1, y1, x2, y2)

        # Draw rotating logo in center
        if self._logo_pixmap and not self._logo_pixmap.isNull():
            painter.save()

            # Move origin to center
            painter.translate(center)

            # Rotate around center
            painter.rotate(self._angle)

            # Draw logo centered at origin
            logo_x = -self._logo_pixmap.width() // 2
            logo_y = -self._logo_pixmap.height() // 2
            painter.drawPixmap(logo_x, logo_y, self._logo_pixmap)

            painter.restore()

    def stop(self):
        """Stop the spinner animation."""
        self._timer.stop()


class OptimizationWaitingDialog(QDialog):
    """Dialog shown while processing optimization results."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Verarbeite Ergebnisse...")
        self.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setMinimumSize(450, 320)
        self.setMaximumWidth(500)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        # Track when current joke was loaded and prevent repeats
        self._joke_loaded_at = time.time()
        self._close_requested = False
        self._shown_joke_ids: list[int] = []  # Track shown jokes to prevent repeats

        # Main container
        self._container = QWidget()
        self._container.setObjectName("waitingContainer")
        self._container.setStyleSheet("""
            QWidget#waitingContainer {
                background-color: white;
                border-radius: 15px;
            }
        """)

        # Drop shadow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 5)
        self._container.setGraphicsEffect(shadow)

        # Layout
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(15, 15, 15, 15)
        outer_layout.addWidget(self._container)

        layout = QVBoxLayout(self._container)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(15)

        # Title
        title = QLabel("Ergebnisse werden verarbeitet...")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #333;
            font-family: 'Segoe UI', Arial;
        """)
        layout.addWidget(title)

        # Spinner with rotating logo
        spinner_container = QWidget()
        spinner_container.setFixedHeight(130)  # Accommodate larger spinner
        spinner_layout = QVBoxLayout(spinner_container)
        spinner_layout.setContentsMargins(0, 0, 0, 0)
        spinner_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._spinner = SpinnerWidget()
        spinner_layout.addWidget(self._spinner, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(spinner_container)

        # Status label
        self._status_label = QLabel("Tabellen werden aktualisiert...")
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status_label.setStyleSheet("""
            font-size: 12px;
            color: #666;
            font-family: 'Segoe UI', Arial;
        """)
        layout.addWidget(self._status_label)

        layout.addSpacing(10)

        # Joke label - with dynamic height
        self._joke_label = QLabel()
        self._joke_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._joke_label.setWordWrap(True)
        self._joke_label.setMinimumHeight(60)  # Minimum for single line
        self._joke_label.setStyleSheet("""
            font-size: 11px;
            font-style: italic;
            color: #555;
            font-family: 'Segoe UI', Arial;
            background-color: #FFF8E7;
            border: 1px solid #F29F05;
            border-radius: 10px;
            padding: 15px;
            margin: 5px;
        """)
        self._load_random_joke()
        layout.addWidget(self._joke_label)

        # Joke rotation timer - 10 seconds
        self._joke_timer = QTimer(self)
        self._joke_timer.timeout.connect(self._load_random_joke)
        self._joke_timer.start(JOKE_DISPLAY_DURATION_MS)

        # Center on parent
        self._center_on_parent()

    def _center_on_parent(self):
        """Center dialog on parent window."""
        if self.parent():
            parent_geo = self.parent().geometry()
            x = parent_geo.x() + (parent_geo.width() - self.width()) // 2
            y = parent_geo.y() + (parent_geo.height() - self.height()) // 2
            self.move(x, y)

    def _load_random_joke(self):
        """Load a random trading joke and adjust dialog height.

        Prevents repeating jokes during the same session by tracking shown IDs.
        """
        try:
            from src.core.jokes import get_random_trading_joke

            # Get joke excluding already shown ones
            joke, joke_id = get_random_trading_joke("de", exclude_ids=self._shown_joke_ids)

            # Track this joke ID to prevent repeats
            if joke_id > 0:
                self._shown_joke_ids.append(joke_id)

            self._joke_label.setText(f'"{joke}"')

            # Track when this joke was loaded
            self._joke_loaded_at = time.time()

            # Adjust label and dialog height based on text
            self._adjust_height_for_joke()

            logger.debug(f"Loaded joke ID {joke_id}, {len(self._shown_joke_ids)} jokes shown this session")

        except Exception as e:
            logger.warning(f"Could not load joke: {e}")
            self._joke_label.setText('"Der Markt hat immer recht. Außer wenn ich long bin."')
            self._joke_loaded_at = time.time()

    def _adjust_height_for_joke(self):
        """Dynamically adjust dialog height based on joke text length."""
        # Calculate required height for the joke text
        font_metrics = QFontMetrics(self._joke_label.font())
        text = self._joke_label.text()

        # Available width for text (label width minus padding)
        available_width = self._joke_label.width() - 40  # 15px padding on each side + margin
        if available_width < 200:
            available_width = 350  # Default if not yet sized

        # Calculate bounding rect for wrapped text
        bounding_rect = font_metrics.boundingRect(
            0, 0, available_width, 1000,
            Qt.TextFlag.TextWordWrap,
            text
        )

        # Required height: text height + padding (30px top/bottom)
        required_label_height = bounding_rect.height() + 40
        min_height = 60

        # Set label minimum height
        new_label_height = max(min_height, required_label_height)
        self._joke_label.setMinimumHeight(new_label_height)

        # Adjust dialog height: base height + extra for multi-line jokes
        base_dialog_height = 320
        extra_height = max(0, new_label_height - min_height)
        new_dialog_height = base_dialog_height + extra_height

        # Apply new size
        self.setMinimumHeight(new_dialog_height)
        self.adjustSize()

        # Re-center after resize
        self._center_on_parent()

        # Process events to update display
        QApplication.processEvents()

    def set_status(self, status: str):
        """Update the status text and keep animation running."""
        self._status_label.setText(status)
        # Force repaint of spinner to keep animation smooth
        self._spinner.update()
        self._spinner.repaint()
        QApplication.processEvents()

    def close_with_delay(self, delay_ms: int = 500):
        """Close dialog after ensuring minimum joke display time.

        If a joke was recently loaded, wait for the remainder of the 10 second
        display time before closing.
        """
        self._close_requested = True
        self._joke_timer.stop()
        self._spinner.stop()
        self._status_label.setText("Fertig!")

        # Calculate how long the current joke has been displayed
        elapsed_ms = int((time.time() - self._joke_loaded_at) * 1000)
        remaining_ms = JOKE_DISPLAY_DURATION_MS - elapsed_ms

        # Wait at least the minimum delay, or the remaining joke time
        actual_delay = max(delay_ms, remaining_ms)

        logger.debug(f"Closing dialog: joke displayed for {elapsed_ms}ms, waiting {actual_delay}ms more")

        QTimer.singleShot(actual_delay, self.accept)

    def closeEvent(self, event):
        """Clean up on close."""
        self._joke_timer.stop()
        self._spinner.stop()
        super().closeEvent(event)
