"""
PyQt/PySide UI Templates for Antigravity.

Contains:
- UIInspectorMixin: F12 inspect mode for discovering widget objectNames

Usage:
    # Option 1: Copy to your project
    cp .antigravity/templates/pyqt/ui_inspector.py src/ui/debug/

    # Option 2: Direct import (only in PyQt projects)
    from .antigravity.templates.pyqt import get_inspector_mixin
    UIInspectorMixin = get_inspector_mixin()

Note: This module uses lazy loading to avoid crashes in non-PyQt projects.
"""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    # Type hint only - not imported at runtime
    from .ui_inspector import UIInspectorMixin as _UIInspectorMixin

__all__ = ['get_inspector_mixin', 'get_template_path']

# Cached mixin class
_inspector_mixin: Optional[type] = None


def get_template_path() -> Path:
    """Get path to ui_inspector.py template file."""
    return Path(__file__).parent / "ui_inspector.py"


def get_inspector_mixin() -> Optional[type]:
    """
    Lazy-load UIInspectorMixin class.

    Returns:
        UIInspectorMixin class if PyQt/PySide is available, None otherwise.

    Example:
        mixin = get_inspector_mixin()
        if mixin:
            class MyWindow(QMainWindow, mixin):
                ...
    """
    global _inspector_mixin

    if _inspector_mixin is not None:
        return _inspector_mixin

    # Try to import - will fail gracefully in non-PyQt environments
    try:
        from .ui_inspector import UIInspectorMixin
        _inspector_mixin = UIInspectorMixin
        return _inspector_mixin
    except ImportError:
        # PyQt/PySide not available
        return None


def is_pyqt_available() -> bool:
    """Check if PyQt/PySide is available in current environment."""
    try:
        # Try PyQt6 first
        import PyQt6.QtWidgets
        return True
    except ImportError:
        pass

    try:
        # Try PyQt5
        import PyQt5.QtWidgets
        return True
    except ImportError:
        pass

    try:
        # Try PySide6
        import PySide6.QtWidgets
        return True
    except ImportError:
        pass

    try:
        # Try PySide2
        import PySide2.QtWidgets
        return True
    except ImportError:
        pass

    return False
