"""
UI Inspector Debug Overlay - F12 Inspect Mode für PyQt6.

Aktiviert mit F12: Zeigt bei Hover über UI-Elemente deren objectName und Widget-Pfad.
Klick kopiert den Pfad in die Zwischenablage.

Usage:
    from src.ui.debug.ui_inspector import UIInspectorMixin

    class MyWindow(QMainWindow, UIInspectorMixin):
        def __init__(self):
            super().__init__()
            self.setup_ui_inspector()  # Aktiviert F12-Shortcut
"""
from __future__ import annotations

import logging
from typing import Optional

from PyQt6.QtCore import QEvent, QObject, Qt, QTimer
from PyQt6.QtGui import QCursor, QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QApplication,
    QLabel,
    QMainWindow,
    QToolTip,
    QWidget,
)

logger = logging.getLogger(__name__)


class UIInspectorOverlay(QLabel):
    """Floating overlay label that shows widget info."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.ToolTip |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setStyleSheet("""
            QLabel {
                background-color: rgba(30, 30, 30, 0.95);
                color: #00FF88;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 12px;
                padding: 8px 12px;
                border: 2px solid #00FF88;
                border-radius: 6px;
            }
        """)
        self.hide()


class UIInspectorEventFilter(QObject):
    """Event filter that intercepts mouse events for inspection."""

    def __init__(self, inspector: 'UIInspectorMixin'):
        super().__init__()
        self._inspector = inspector
        self._last_widget: Optional[QWidget] = None
        self._update_timer = QTimer()
        self._update_timer.setInterval(50)  # 50ms debounce
        self._update_timer.setSingleShot(True)
        self._update_timer.timeout.connect(self._do_update)
        self._pending_pos = None

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if not self._inspector._inspect_mode_active:
            return False

        if event.type() == QEvent.Type.MouseMove:
            self._pending_pos = QCursor.pos()
            self._update_timer.start()
            return False

        if event.type() == QEvent.Type.MouseButtonPress:
            widget = QApplication.widgetAt(QCursor.pos())
            if widget:
                path = self._get_widget_path(widget)
                QApplication.clipboard().setText(path)
                self._inspector._show_copy_feedback(path)
                return True  # Consume the click

        return False

    def _do_update(self):
        """Debounced update of the overlay."""
        if not self._pending_pos:
            return

        widget = QApplication.widgetAt(self._pending_pos)
        if widget and widget != self._last_widget:
            self._last_widget = widget
            self._inspector._update_overlay(widget, self._pending_pos)

    def _get_widget_path(self, widget: QWidget) -> str:
        """Build the full path from root to widget."""
        parts = []
        current = widget
        while current:
            name = current.objectName() or f"<{current.__class__.__name__}>"
            parts.append(name)
            current = current.parent()
        parts.reverse()
        return ".".join(parts)


class UIInspectorMixin:
    """
    Mixin für QMainWindow das F12 UI-Inspect-Mode hinzufügt.

    Features:
    - F12 togglet Inspect-Mode
    - Hover zeigt Widget-Pfad + objectName
    - Klick kopiert Pfad in Zwischenablage
    - Visueller Indikator wenn Inspect-Mode aktiv
    """

    _inspect_mode_active: bool = False
    _inspector_overlay: Optional[UIInspectorOverlay] = None
    _inspector_filter: Optional[UIInspectorEventFilter] = None
    _inspect_mode_indicator: Optional[QLabel] = None

    def setup_ui_inspector(self):
        """Initialize the UI inspector. Call this in __init__ after super().__init__()."""
        self._inspect_mode_active = False
        self._inspector_overlay = UIInspectorOverlay()
        self._inspector_filter = UIInspectorEventFilter(self)

        # F12 Shortcut
        shortcut = QShortcut(QKeySequence(Qt.Key.Key_F12), self)
        shortcut.activated.connect(self.toggle_inspect_mode)

        # Mode indicator
        self._inspect_mode_indicator = QLabel("🔍 INSPECT MODE (F12 to exit, click to copy)", self)
        self._inspect_mode_indicator.setStyleSheet("""
            QLabel {
                background-color: #FF6600;
                color: white;
                font-weight: bold;
                font-size: 11px;
                padding: 4px 12px;
                border-radius: 0;
            }
        """)
        self._inspect_mode_indicator.setFixedHeight(24)
        self._inspect_mode_indicator.hide()

        logger.info("UI Inspector initialized - Press F12 to toggle inspect mode")

    def toggle_inspect_mode(self):
        """Toggle the UI inspection mode on/off."""
        self._inspect_mode_active = not self._inspect_mode_active

        if self._inspect_mode_active:
            # Install event filter on application
            QApplication.instance().installEventFilter(self._inspector_filter)
            self._inspect_mode_indicator.show()
            self._inspect_mode_indicator.raise_()
            self._position_indicator()
            logger.info("UI Inspect Mode: ON")
        else:
            QApplication.instance().removeEventFilter(self._inspector_filter)
            self._inspector_overlay.hide()
            self._inspect_mode_indicator.hide()
            logger.info("UI Inspect Mode: OFF")

    def _position_indicator(self):
        """Position the mode indicator at top of window."""
        if hasattr(self, 'width'):
            indicator = self._inspect_mode_indicator
            indicator.setFixedWidth(self.width())
            indicator.move(0, 0)

    def _update_overlay(self, widget: QWidget, global_pos):
        """Update the overlay with widget information."""
        if not self._inspector_overlay:
            return

        # Get widget info
        obj_name = widget.objectName() or "(no objectName)"
        class_name = widget.__class__.__name__
        path = self._inspector_filter._get_widget_path(widget)

        # Get geometry
        geom = widget.geometry()
        size_info = f"{geom.width()}x{geom.height()}"

        # Get widget-specific context info
        context_info = self._get_widget_context(widget)
        context_line = f"\n<span style='color: #00BFFF;'>Content:</span> <b>{context_info}</b>" if context_info else ""

        # Build display text
        text = f"""📋 <b>{obj_name}</b>
<span style='color: #888;'>Class:</span> {class_name}{context_line}
<span style='color: #888;'>Size:</span> {size_info}
<span style='color: #888;'>Path:</span> <span style='color: #FFD700;'>{path}</span>
<span style='color: #666;'>Click to copy path</span>"""

        self._inspector_overlay.setText(text)
        self._inspector_overlay.setTextFormat(Qt.TextFormat.RichText)
        self._inspector_overlay.adjustSize()

        # Position overlay near cursor but not blocking it
        x = global_pos.x() + 20
        y = global_pos.y() + 20

        # Keep on screen
        screen = QApplication.primaryScreen().geometry()
        overlay_width = self._inspector_overlay.width()
        overlay_height = self._inspector_overlay.height()

        if x + overlay_width > screen.right():
            x = global_pos.x() - overlay_width - 10
        if y + overlay_height > screen.bottom():
            y = global_pos.y() - overlay_height - 10

        self._inspector_overlay.move(x, y)
        self._inspector_overlay.show()
        self._inspector_overlay.raise_()

    def _get_widget_context(self, widget: QWidget) -> str:
        """Extract context-specific info from widget (text, title, value, etc.).

        Returns human-readable content for different widget types.
        """
        from PyQt6.QtWidgets import (
            QPushButton, QLabel, QLineEdit, QTextEdit, QPlainTextEdit,
            QCheckBox, QRadioButton, QComboBox, QSpinBox, QDoubleSpinBox,
            QSlider, QProgressBar, QGroupBox, QTabWidget, QTabBar,
            QToolButton, QMenu, QListWidget, QTreeWidget, QTableWidget
        )

        try:
            # Buttons with text
            if isinstance(widget, (QPushButton, QToolButton, QCheckBox, QRadioButton)):
                text = widget.text()
                if text:
                    return f'"{text}"'

            # Labels
            if isinstance(widget, QLabel):
                text = widget.text()
                if text:
                    # Truncate long labels
                    if len(text) > 50:
                        text = text[:47] + "..."
                    return f'"{text}"'

            # Input fields
            if isinstance(widget, QLineEdit):
                text = widget.text() or widget.placeholderText()
                if text:
                    return f'"{text}"' if widget.text() else f'placeholder: "{text}"'

            if isinstance(widget, (QTextEdit, QPlainTextEdit)):
                text = widget.toPlainText()[:30] if hasattr(widget, 'toPlainText') else ""
                if text:
                    return f'"{text}..."'

            # ComboBox
            if isinstance(widget, QComboBox):
                current = widget.currentText()
                count = widget.count()
                if current:
                    return f'"{current}" ({count} items)'

            # Spinners
            if isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                return f"value: {widget.value()}"

            # Slider/Progress
            if isinstance(widget, (QSlider, QProgressBar)):
                return f"value: {widget.value()}"

            # GroupBox
            if isinstance(widget, QGroupBox):
                title = widget.title()
                if title:
                    return f'"{title}"'

            # TabWidget - show current tab
            if isinstance(widget, QTabWidget):
                idx = widget.currentIndex()
                if idx >= 0:
                    tab_text = widget.tabText(idx)
                    return f'Tab: "{tab_text}" ({idx + 1}/{widget.count()})'

            # TabBar
            if isinstance(widget, QTabBar):
                idx = widget.currentIndex()
                if idx >= 0:
                    tab_text = widget.tabText(idx)
                    return f'Tab: "{tab_text}"'

            # List/Tree/Table widgets
            if isinstance(widget, QListWidget):
                count = widget.count()
                current = widget.currentItem()
                if current:
                    return f'"{current.text()}" ({count} items)'
                return f"({count} items)"

            if isinstance(widget, QTableWidget):
                return f"{widget.rowCount()} rows × {widget.columnCount()} cols"

            if isinstance(widget, QTreeWidget):
                return f"{widget.topLevelItemCount()} items"

            # Fallback: check for tooltip
            tooltip = widget.toolTip()
            if tooltip and len(tooltip) < 60:
                return f'tip: "{tooltip}"'

        except Exception:
            pass  # Silently ignore errors in context extraction

        return ""  # No context available

    def _show_copy_feedback(self, path: str):
        """Show feedback when path is copied."""
        self._inspector_overlay.setText(f"✅ Copied!\n{path}")
        self._inspector_overlay.adjustSize()
        QTimer.singleShot(1500, lambda: self._inspector_overlay.hide() if not self._inspect_mode_active else None)
        logger.info(f"Copied to clipboard: {path}")

    def resizeEvent(self, event):
        """Handle resize to reposition indicator."""
        super().resizeEvent(event)
        if hasattr(self, '_inspect_mode_indicator') and self._inspect_mode_indicator:
            self._position_indicator()
