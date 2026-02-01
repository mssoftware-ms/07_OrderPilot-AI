"""
Base UI Driver Protocol for Antigravity.

Defines the abstract interface for UI introspection across all frameworks.
All drivers must implement this protocol to ensure consistent behavior.

Schema Version: antigravity/ui-tree/v1
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from typing import Any, Optional


class ElementType(Enum):
    """Standard UI element types across all frameworks."""
    WINDOW = auto()
    DIALOG = auto()
    BUTTON = auto()
    LABEL = auto()
    TEXT_INPUT = auto()
    TEXT_AREA = auto()
    CHECKBOX = auto()
    RADIO = auto()
    COMBOBOX = auto()
    SLIDER = auto()
    SPINBOX = auto()
    TAB = auto()
    TAB_PANEL = auto()
    LIST = auto()
    LIST_ITEM = auto()
    TABLE = auto()
    TABLE_ROW = auto()
    TABLE_CELL = auto()
    TREE = auto()
    TREE_ITEM = auto()
    MENU = auto()
    MENU_ITEM = auto()
    TOOLBAR = auto()
    SCROLLBAR = auto()
    PROGRESS = auto()
    IMAGE = auto()
    CANVAS = auto()
    CONTAINER = auto()
    GROUP = auto()
    UNKNOWN = auto()


@dataclass
class Geometry:
    """Element geometry/position."""
    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0

    def to_dict(self) -> dict[str, int]:
        return {"x": self.x, "y": self.y, "w": self.width, "h": self.height}


@dataclass
class ElementState:
    """Element state flags."""
    visible: bool = True
    enabled: bool = True
    focused: bool = False
    checked: Optional[bool] = None  # For checkboxes/radios
    selected: Optional[bool] = None  # For list items
    expanded: Optional[bool] = None  # For tree items

    def to_dict(self) -> dict[str, Any]:
        result = {"visible": self.visible, "enabled": self.enabled, "focused": self.focused}
        if self.checked is not None:
            result["checked"] = self.checked
        if self.selected is not None:
            result["selected"] = self.selected
        if self.expanded is not None:
            result["expanded"] = self.expanded
        return result


@dataclass
class Selectors:
    """Multi-framework selectors for the same element."""
    pyqt: Optional[str] = None       # findChild(QWidget, 'name')
    css: Optional[str] = None        # #id, .class, [attr]
    xpath: Optional[str] = None      # //button[@id='x']
    accessibility: Optional[str] = None  # Accessibility name/label

    def to_dict(self) -> dict[str, str]:
        result = {}
        if self.pyqt:
            result["pyqt"] = self.pyqt
        if self.css:
            result["css"] = self.css
        if self.xpath:
            result["xpath"] = self.xpath
        if self.accessibility:
            result["accessibility"] = self.accessibility
        return result


@dataclass
class UIElement:
    """
    Unified UI element representation.

    Works across PyQt, React, Vue, Angular, Electron.
    """
    id: str                          # Unique identifier (objectName, data-testid, etc.)
    element_type: ElementType        # Standardized type
    native_type: str                 # Original type (QPushButton, button, etc.)
    path: str                        # Hierarchical path (Window.Tab.Group.Element)
    text: str = ""                   # Visible text content
    geometry: Geometry = field(default_factory=Geometry)
    state: ElementState = field(default_factory=ElementState)
    selectors: Selectors = field(default_factory=Selectors)
    children: list["UIElement"] = field(default_factory=list)
    attributes: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to JSON-serializable dict following schema v1."""
        result = {
            "id": self.id,
            "type": self.element_type.name.lower(),
            "nativeType": self.native_type,
            "path": self.path,
        }
        if self.text:
            result["text"] = self.text
        result["geometry"] = self.geometry.to_dict()
        result["state"] = self.state.to_dict()
        result["selectors"] = self.selectors.to_dict()
        if self.children:
            result["children"] = [c.to_dict() for c in self.children]
        if self.attributes:
            result["attributes"] = self.attributes
        return result


@dataclass
class UITree:
    """Complete UI tree snapshot."""
    schema: str = "antigravity/ui-tree/v1"
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    stack: str = "unknown"
    root: Optional[UIElement] = None
    elements: list[UIElement] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to JSON-serializable dict."""
        result = {
            "schema": self.schema,
            "timestamp": self.timestamp,
            "stack": self.stack,
        }
        if self.root:
            result["root"] = self.root.to_dict()
        if self.elements:
            result["elements"] = [e.to_dict() for e in self.elements]
        return result


class BaseUIDriver(ABC):
    """
    Abstract base class for UI introspection drivers.

    All framework-specific drivers must implement this interface.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Driver name (e.g., 'pyqt', 'playwright', 'electron')."""
        ...

    @property
    @abstractmethod
    def is_available(self) -> bool:
        """Check if this driver can be used in current environment."""
        ...

    @abstractmethod
    def get_ui_tree(self) -> UITree:
        """
        Get complete UI element tree.

        Returns:
            UITree snapshot of current UI state.
        """
        ...

    @abstractmethod
    def find_element(self, identifier: str) -> Optional[UIElement]:
        """
        Find element by any identifier.

        Args:
            identifier: objectName, CSS selector, XPath, or accessibility name.

        Returns:
            UIElement if found, None otherwise.
        """
        ...

    @abstractmethod
    def find_elements(self, identifier: str) -> list[UIElement]:
        """
        Find all elements matching identifier.

        Args:
            identifier: Pattern to match (supports wildcards).

        Returns:
            List of matching UIElements.
        """
        ...

    def click(self, identifier: str) -> bool:
        """
        Click element by identifier.

        Args:
            identifier: Element identifier.

        Returns:
            True if click succeeded.
        """
        element = self.find_element(identifier)
        return self._perform_click(element) if element else False

    def get_text(self, identifier: str) -> str:
        """
        Get text content of element.

        Args:
            identifier: Element identifier.

        Returns:
            Text content or empty string.
        """
        element = self.find_element(identifier)
        return element.text if element else ""

    def set_text(self, identifier: str, text: str) -> bool:
        """
        Set text content of input element.

        Args:
            identifier: Element identifier.
            text: Text to set.

        Returns:
            True if successful.
        """
        element = self.find_element(identifier)
        return self._perform_set_text(element, text) if element else False

    def _perform_click(self, element: UIElement) -> bool:
        """Override in subclass for actual click implementation."""
        return False

    def _perform_set_text(self, element: UIElement, text: str) -> bool:
        """Override in subclass for actual text input implementation."""
        return False


class NullDriver(BaseUIDriver):
    """
    Null driver for unsupported frameworks.

    Returns empty results without crashing.
    """

    @property
    def name(self) -> str:
        return "null"

    @property
    def is_available(self) -> bool:
        return True  # Always available as fallback

    def get_ui_tree(self) -> UITree:
        return UITree(stack="unsupported")

    def find_element(self, identifier: str) -> Optional[UIElement]:
        return None

    def find_elements(self, identifier: str) -> list[UIElement]:
        return []
