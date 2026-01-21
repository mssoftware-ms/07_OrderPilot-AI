"""Application Icon Management - Issue #29.

Provides candlestick chart icon for all application windows.
Converts black icons to white with transparent background.
"""

import logging
import os
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor

logger = logging.getLogger(__name__)


def get_app_icon() -> QIcon:
    """Get the main application icon (candlestick chart, white on transparent).

    Issue #29: Trading-themed icon for all windows.

    Returns:
        QIcon: Application icon (white candlestick chart on transparent background).
    """
    try:
        # Path to black icon
        icon_path = Path(__file__).parent / "assets" / "app_icons" / "orderpilot_black_48.png"

        if not icon_path.exists():
            logger.warning(f"App icon not found: {icon_path}")
            return QIcon()

        # Load black icon
        black_pixmap = QPixmap(str(icon_path))

        if black_pixmap.isNull():
            logger.warning("Failed to load app icon pixmap")
            return QIcon()

        # Convert black to white with transparency
        # Create a white pixmap with the same alpha channel as the black icon
        white_pixmap = QPixmap(black_pixmap.size())
        white_pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(white_pixmap)

        # Fill with white
        painter.setBrush(QColor(255, 255, 255))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(white_pixmap.rect())

        # Use the black icon's alpha channel as mask
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_DestinationIn)
        painter.drawPixmap(0, 0, black_pixmap)

        painter.end()

        # Create icon from white pixmap
        icon = QIcon(white_pixmap)
        logger.info("App icon loaded: candlestick chart (white)")
        return icon

    except Exception as e:
        logger.error(f"Failed to create app icon: {e}", exc_info=True)
        return QIcon()


def set_window_icon(window) -> None:
    """Set the application icon for a window.

    Issue #29: Apply trading icon to all windows.

    Args:
        window: QWidget or QMainWindow to apply icon to.
    """
    try:
        icon = get_app_icon()
        if not icon.isNull():
            window.setWindowIcon(icon)
            logger.debug(f"Window icon set for {window.__class__.__name__}")
    except Exception as e:
        logger.error(f"Failed to set window icon: {e}")
