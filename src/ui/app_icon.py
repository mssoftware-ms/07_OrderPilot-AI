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
    """Get the main application icon from marketing assets.

    Returns:
        QIcon: Application icon in original colors.
    """
    from .app_resources import _load_app_icon
    return _load_app_icon()


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
