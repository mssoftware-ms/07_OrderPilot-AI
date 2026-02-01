"""
Antigravity UI Drivers.

Provides unified UI introspection across different frameworks:
- PyQt/PySide (desktop)
- Playwright (web)
- Electron (hybrid)

Usage:
    from core.environment import Environment

    env = Environment()
    driver = env.ui_driver  # Auto-detected driver
    tree = driver.get_ui_tree()
"""
from .base import BaseUIDriver, UIElement, NullDriver

__all__ = ['BaseUIDriver', 'UIElement', 'NullDriver']
