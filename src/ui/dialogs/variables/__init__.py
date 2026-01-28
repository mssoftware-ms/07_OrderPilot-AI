"""
Variable Dialogs Package.

This package contains UI dialogs for managing and viewing project variables.

Components:
    - VariableReferenceDialog: Read-only variable reference popup
    - VariableManagerDialog: Full CRUD variable manager

Author: OrderPilot-AI Development Team
Created: 2026-01-28
"""

from .variable_reference_dialog import VariableReferenceDialog
from .variable_manager_dialog import VariableManagerDialog

__all__ = [
    "VariableReferenceDialog",
    "VariableManagerDialog",
]

__version__ = "1.0.0"
