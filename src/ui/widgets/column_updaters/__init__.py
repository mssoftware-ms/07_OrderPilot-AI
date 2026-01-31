"""Column updaters for table display.

This package provides specialized column updaters following the Strategy Pattern
to handle different types of table column updates (status, P&L, fees, etc.).
"""

from __future__ import annotations

from .base_updater import BaseColumnUpdater
from .registry import ColumnUpdaterRegistry

__all__ = [
    "BaseColumnUpdater",
    "ColumnUpdaterRegistry",
]
