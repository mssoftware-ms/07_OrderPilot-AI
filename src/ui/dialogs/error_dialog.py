"""Simple Error Dialog Helper for showing provider errors."""

import logging
from PyQt6.QtWidgets import QMessageBox

logger = logging.getLogger(__name__)


def show_error_dialog(title: str, message: str, parent=None):
    """Show a critical error dialog to the user.

    Args:
        title: Dialog title
        message: Error message to display
        parent: Parent widget (optional)
    """
    try:
        msg_box = QMessageBox(parent)
        msg_box.setIcon(QMessageBox.Icon.Critical)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg_box.exec()
    except Exception as e:
        # Fallback: If dialog fails, at least log the error
        logger.error(f"{title}: {message}")
        logger.error(f"Failed to show error dialog: {e}")
