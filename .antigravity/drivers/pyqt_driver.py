"""
PyQt/PySide UI Driver for Antigravity.

Provides UI introspection for PyQt5, PyQt6, PySide2, and PySide6 applications.
Uses in-process introspection via QApplication.widgetAt() and findChildren().

Usage:
    from drivers.pyqt_driver import PyQtDriver

    driver = PyQtDriver()
    if driver.is_available:
        tree = driver.get_ui_tree()
        element = driver.find_element("btn_start")
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional, Any

from .base import (
    BaseUIDriver,
    UITree,
    UIElement,
    ElementType,
    Geometry,
    ElementState,
    Selectors,
)

if TYPE_CHECKING:
    from ..core.environment import Stack

logger = logging.getLogger(__name__)

# Type mapping from Qt widget classes to unified ElementType
QT_TYPE_MAP: dict[str, ElementType] = {
    # Buttons
    "QPushButton": ElementType.BUTTON,
    "QToolButton": ElementType.BUTTON,
    "QRadioButton": ElementType.RADIO,
    "QCheckBox": ElementType.CHECKBOX,
    # Text
    "QLabel": ElementType.LABEL,
    "QLineEdit": ElementType.TEXT_INPUT,
    "QTextEdit": ElementType.TEXT_AREA,
    "QPlainTextEdit": ElementType.TEXT_AREA,
    "QSpinBox": ElementType.SPINBOX,
    "QDoubleSpinBox": ElementType.SPINBOX,
    # Selection
    "QComboBox": ElementType.COMBOBOX,
    "QSlider": ElementType.SLIDER,
    "QDial": ElementType.SLIDER,
    # Lists/Trees
    "QListWidget": ElementType.LIST,
    "QListView": ElementType.LIST,
    "QTreeWidget": ElementType.TREE,
    "QTreeView": ElementType.TREE,
    "QTableWidget": ElementType.TABLE,
    "QTableView": ElementType.TABLE,
    # Containers
    "QMainWindow": ElementType.WINDOW,
    "QDialog": ElementType.DIALOG,
    "QWidget": ElementType.CONTAINER,
    "QFrame": ElementType.CONTAINER,
    "QGroupBox": ElementType.GROUP,
    "QScrollArea": ElementType.CONTAINER,
    "QSplitter": ElementType.CONTAINER,
    # Tabs
    "QTabWidget": ElementType.TAB,
    "QTabBar": ElementType.TAB,
    "QStackedWidget": ElementType.TAB_PANEL,
    # Menus
    "QMenuBar": ElementType.MENU,
    "QMenu": ElementType.MENU,
    "QAction": ElementType.MENU_ITEM,
    "QToolBar": ElementType.TOOLBAR,
    # Progress
    "QProgressBar": ElementType.PROGRESS,
    # Graphics
    "QGraphicsView": ElementType.CANVAS,
}


class PyQtDriver(BaseUIDriver):
    """
    UI driver for PyQt5/6 and PySide2/6 applications.

    Supports:
    - PyQt6, PyQt5
    - PySide6, PySide2

    Features:
    - In-process widget introspection
    - Full widget tree traversal
    - Element search by objectName
    """

    def __init__(self, stack: Optional["Stack"] = None):
        """
        Initialize PyQt driver.

        Args:
            stack: Detected stack (PYQT6, PYQT5, PYSIDE6, PYSIDE2).
                  Auto-detected if not provided.
        """
        self._stack = stack
        self._qt_module: Optional[Any] = None
        self._widgets_module: Optional[Any] = None
        self._app: Optional[Any] = None

    @property
    def name(self) -> str:
        return "pyqt"

    @property
    def is_available(self) -> bool:
        """Check if Qt is available and an app instance exists."""
        if self._try_import():
            return self._get_app() is not None
        return False

    @property
    def stack_name(self) -> str:
        """Get the detected Qt stack name."""
        if self._stack:
            return self._stack.name.lower()
        return "pyqt"

    def get_ui_tree(self) -> UITree:
        """Get complete UI tree from all top-level widgets."""
        if not self.is_available:
            return UITree(stack=self.stack_name)

        app = self._get_app()
        if not app:
            return UITree(stack=self.stack_name)

        elements: list[UIElement] = []

        # Get all top-level widgets
        for widget in app.topLevelWidgets():
            if widget.isVisible():
                element = self._widget_to_element(widget, "")
                if element:
                    elements.append(element)

        return UITree(
            stack=self.stack_name,
            elements=elements,
            root=elements[0] if len(elements) == 1 else None,
        )

    def find_element(self, identifier: str) -> Optional[UIElement]:
        """Find element by objectName."""
        if not self.is_available:
            return None

        widget = self._find_widget_by_name(identifier)
        if widget:
            return self._widget_to_element(widget, self._get_widget_path(widget))

        return None

    def find_elements(self, identifier: str) -> list[UIElement]:
        """Find all elements matching objectName pattern."""
        if not self.is_available:
            return []

        results: list[UIElement] = []
        app = self._get_app()
        if not app:
            return results

        for widget in app.topLevelWidgets():
            self._find_matching_widgets(widget, identifier, results)

        return results

    def _perform_click(self, element: UIElement) -> bool:
        """Simulate click on widget."""
        widget = self._find_widget_by_name(element.id)
        if widget and hasattr(widget, "click"):
            widget.click()
            return True
        return False

    def _perform_set_text(self, element: UIElement, text: str) -> bool:
        """Set text on input widget."""
        widget = self._find_widget_by_name(element.id)
        if widget:
            if hasattr(widget, "setText"):
                widget.setText(text)
                return True
            elif hasattr(widget, "setPlainText"):
                widget.setPlainText(text)
                return True
        return False

    def _try_import(self) -> bool:
        """Try to import Qt modules."""
        if self._qt_module is not None:
            return True

        # Try imports in order of preference
        import_order = [
            ("PyQt6.QtWidgets", "PyQt6.QtCore"),
            ("PyQt5.QtWidgets", "PyQt5.QtCore"),
            ("PySide6.QtWidgets", "PySide6.QtCore"),
            ("PySide2.QtWidgets", "PySide2.QtCore"),
        ]

        for widgets_name, core_name in import_order:
            try:
                import importlib
                self._widgets_module = importlib.import_module(widgets_name)
                self._qt_module = importlib.import_module(core_name)
                logger.debug(f"Using Qt bindings: {widgets_name}")
                return True
            except ImportError:
                continue

        return False

    def _get_app(self) -> Optional[Any]:
        """Get QApplication instance."""
        if self._app is not None:
            return self._app

        if not self._widgets_module:
            return None

        QApplication = getattr(self._widgets_module, "QApplication", None)
        if QApplication:
            self._app = QApplication.instance()
            return self._app

        return None

    def _widget_to_element(self, widget: Any, parent_path: str) -> Optional[UIElement]:
        """Convert Qt widget to UIElement."""
        if widget is None:
            return None

        class_name = widget.__class__.__name__
        object_name = widget.objectName() or ""

        # Build path
        name_part = object_name or f"<{class_name}>"
        path = f"{parent_path}.{name_part}" if parent_path else name_part

        # Get geometry
        geom = widget.geometry()
        geometry = Geometry(
            x=geom.x(),
            y=geom.y(),
            width=geom.width(),
            height=geom.height(),
        )

        # Get state
        state = ElementState(
            visible=widget.isVisible(),
            enabled=widget.isEnabled(),
            focused=widget.hasFocus(),
        )

        # Check for checkable state
        if hasattr(widget, "isChecked"):
            state.checked = widget.isChecked()

        # Get text content
        text = ""
        if hasattr(widget, "text") and callable(widget.text):
            try:
                text = widget.text() or ""
            except Exception:
                pass
        elif hasattr(widget, "toPlainText"):
            try:
                text = widget.toPlainText() or ""
            except Exception:
                pass
        elif hasattr(widget, "windowTitle"):
            try:
                text = widget.windowTitle() or ""
            except Exception:
                pass

        # Build selectors
        selectors = Selectors(
            pyqt=f"findChild(QWidget, '{object_name}')" if object_name else None,
        )

        # Map to unified type
        element_type = QT_TYPE_MAP.get(class_name, ElementType.UNKNOWN)

        # Get children
        children: list[UIElement] = []
        if hasattr(widget, "children"):
            for child in widget.children():
                # Only include QWidget subclasses
                if hasattr(child, "isVisible") and hasattr(child, "geometry"):
                    child_element = self._widget_to_element(child, path)
                    if child_element:
                        children.append(child_element)

        return UIElement(
            id=object_name or f"_{class_name}_{id(widget)}",
            element_type=element_type,
            native_type=class_name,
            path=path,
            text=text,
            geometry=geometry,
            state=state,
            selectors=selectors,
            children=children,
        )

    def _find_widget_by_name(self, name: str) -> Optional[Any]:
        """Find widget by objectName across all top-level widgets."""
        app = self._get_app()
        if not app:
            return None

        for widget in app.topLevelWidgets():
            found = self._search_widget_tree(widget, name)
            if found:
                return found

        return None

    def _search_widget_tree(self, widget: Any, name: str) -> Optional[Any]:
        """Recursively search widget tree for objectName."""
        if widget.objectName() == name:
            return widget

        if hasattr(widget, "findChild"):
            # Use Qt's built-in findChild for efficiency
            QWidget = getattr(self._widgets_module, "QWidget", None)
            if QWidget:
                found = widget.findChild(QWidget, name)
                if found:
                    return found

        return None

    def _find_matching_widgets(
        self,
        widget: Any,
        pattern: str,
        results: list[UIElement],
    ) -> None:
        """Find all widgets matching pattern (supports * wildcard)."""
        import fnmatch

        object_name = widget.objectName() or ""

        if fnmatch.fnmatch(object_name, pattern):
            element = self._widget_to_element(widget, self._get_widget_path(widget))
            if element:
                results.append(element)

        # Recurse into children
        if hasattr(widget, "children"):
            for child in widget.children():
                if hasattr(child, "objectName"):
                    self._find_matching_widgets(child, pattern, results)

    def _get_widget_path(self, widget: Any) -> str:
        """Build full path from root to widget."""
        parts: list[str] = []
        current = widget

        while current is not None:
            name = current.objectName() or f"<{current.__class__.__name__}>"
            parts.append(name)
            current = current.parent() if hasattr(current, "parent") else None

        parts.reverse()
        return ".".join(parts)
