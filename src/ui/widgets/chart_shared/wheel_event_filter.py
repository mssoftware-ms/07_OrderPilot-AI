"""Wheel Event Filter for QSpinBox and QFontComboBox.

Issue #13: Prevents mouse wheel from changing values in specific widgets.
This filter blocks wheel events for controlled widgets to prevent
accidental value changes when scrolling over combo boxes or spinboxes.
"""

from PyQt6.QtCore import QObject, QEvent
from PyQt6.QtGui import QWheelEvent


class WheelEventFilter(QObject):
    """Event filter that blocks wheel events for combo boxes and spinboxes.

    Usage:
        filter_obj = WheelEventFilter()
        combo_box.installEventFilter(filter_obj)
        spin_box.installEventFilter(filter_obj)
    """

    def eventFilter(self, obj, event: QEvent) -> bool:
        """Block wheel events while passing through other events.

        Args:
            obj: The object that received the event
            event: The event to process

        Returns:
            True if event was blocked (wheel event), False to pass through
        """
        if isinstance(event, QWheelEvent):
            # Block wheel event
            return True

        # Pass through all other events
        return super().eventFilter(obj, event)
