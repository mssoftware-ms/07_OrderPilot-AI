"""Collapsible Section Widget for accordion-style UI.

A clickable header that expands/collapses its content.
Only one section can be expanded at a time in an accordion group.
"""

from __future__ import annotations

from typing import Optional
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QSizePolicy,
)
from PyQt6.QtGui import QFont


class CollapsibleSection(QFrame):
    """A collapsible section with clickable header.

    Features:
    - Click header to expand/collapse
    - Animated expand/collapse
    - Icon indicator (arrow)
    - Can be part of an accordion group

    Signals:
        expanded: Emitted when section is expanded (passes self)
        collapsed: Emitted when section is collapsed
    """

    expanded = pyqtSignal(object)  # Emits self when expanded
    collapsed = pyqtSignal()

    def __init__(
        self,
        title: str,
        parent: Optional[QWidget] = None,
        expanded: bool = False,
        icon: Optional[str] = None
    ):
        super().__init__(parent)
        self._title = title
        self._is_expanded = expanded
        self._content_widget: Optional[QWidget] = None
        self._animation: Optional[QPropertyAnimation] = None

        self._setup_ui(icon)

    def _setup_ui(self, icon: Optional[str] = None) -> None:
        """Create the collapsible section UI."""
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            CollapsibleSection {
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                margin: 2px 0;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header (clickable)
        self._header = QFrame()
        self._header.setStyleSheet("""
            QFrame {
                background-color: #2d2d2d;
                border: none;
                border-radius: 4px 4px 0 0;
                padding: 8px;
            }
            QFrame:hover {
                background-color: #3d3d3d;
            }
        """)
        self._header.setCursor(Qt.CursorShape.PointingHandCursor)
        self._header.mousePressEvent = self._on_header_clicked

        header_layout = QHBoxLayout(self._header)
        header_layout.setContentsMargins(10, 5, 10, 5)

        # Arrow indicator
        self._arrow = QLabel("▶" if not self._is_expanded else "▼")
        self._arrow.setStyleSheet("color: #888; font-size: 10px;")
        self._arrow.setFixedWidth(15)
        header_layout.addWidget(self._arrow)

        # Optional icon (skip silently if not found)
        if icon:
            try:
                from src.ui.icons import get_icon
                icon_obj = get_icon(icon)
                if icon_obj and not icon_obj.isNull():
                    icon_label = QLabel()
                    icon_label.setPixmap(icon_obj.pixmap(16, 16))
                    header_layout.addWidget(icon_label)
            except Exception:
                pass  # Skip icon if not found

        # Title
        self._title_label = QLabel(self._title)
        self._title_label.setStyleSheet("font-weight: bold; font-size: 11pt;")
        header_layout.addWidget(self._title_label)

        header_layout.addStretch()

        layout.addWidget(self._header)

        # Content container
        self._content_container = QFrame()
        self._content_container.setStyleSheet("""
            QFrame {
                background-color: transparent;
                border: none;
            }
        """)
        self._content_layout = QVBoxLayout(self._content_container)
        self._content_layout.setContentsMargins(5, 5, 5, 5)

        layout.addWidget(self._content_container)

        # Set initial state
        self._content_container.setVisible(self._is_expanded)

    def _on_header_clicked(self, event) -> None:
        """Handle header click to toggle expand/collapse."""
        self.toggle()

    def toggle(self) -> None:
        """Toggle expanded/collapsed state."""
        if self._is_expanded:
            self.collapse()
        else:
            self.expand()

    def expand(self) -> None:
        """Expand the section."""
        if self._is_expanded:
            return
        self._is_expanded = True
        self._arrow.setText("▼")
        self._content_container.setVisible(True)
        self.expanded.emit(self)

    def collapse(self) -> None:
        """Collapse the section."""
        if not self._is_expanded:
            return
        self._is_expanded = False
        self._arrow.setText("▶")
        self._content_container.setVisible(False)
        self.collapsed.emit()

    def is_expanded(self) -> bool:
        """Check if section is expanded."""
        return self._is_expanded

    def set_content(self, widget: QWidget) -> None:
        """Set the content widget.

        Args:
            widget: Widget to show when expanded
        """
        # Remove old content
        if self._content_widget:
            self._content_layout.removeWidget(self._content_widget)
            self._content_widget.setParent(None)

        self._content_widget = widget
        self._content_layout.addWidget(widget)

    def content_layout(self) -> QVBoxLayout:
        """Get the content layout to add widgets directly."""
        return self._content_layout

    def set_title(self, title: str) -> None:
        """Update the section title."""
        self._title = title
        self._title_label.setText(title)


class AccordionWidget(QWidget):
    """Container that manages multiple CollapsibleSections as an accordion.

    Only one section can be expanded at a time.
    """

    def __init__(self, parent: Optional[QWidget] = None, allow_all_collapsed: bool = True):
        super().__init__(parent)
        self._sections: list[CollapsibleSection] = []
        self._allow_all_collapsed = allow_all_collapsed

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(2)

    def add_section(self, section: CollapsibleSection) -> None:
        """Add a section to the accordion.

        Args:
            section: CollapsibleSection to add
        """
        section.expanded.connect(self._on_section_expanded)
        self._sections.append(section)
        self._layout.addWidget(section)

    def _on_section_expanded(self, expanded_section: CollapsibleSection) -> None:
        """Collapse all other sections when one expands."""
        for section in self._sections:
            if section is not expanded_section and section.is_expanded():
                section.collapse()

    def add_stretch(self) -> None:
        """Add stretch at the end."""
        self._layout.addStretch()

    def collapse_all(self) -> None:
        """Collapse all sections."""
        for section in self._sections:
            section.collapse()

    def expand_first(self) -> None:
        """Expand the first section."""
        if self._sections:
            self._sections[0].expand()
