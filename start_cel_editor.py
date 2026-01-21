#!/usr/bin/env python
"""
CEL Editor Standalone Launcher
Startet das CEL Editor Fenster direkt ohne die Hauptanwendung
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

# Set high DPI scaling
QApplication.setHighDpiScaleFactorRoundingPolicy(
    Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
)

def main():
    """Start CEL Editor window."""
    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("OrderPilot-AI CEL Editor")
    app.setOrganizationName("OrderPilot")

    # Import and create CEL Editor window
    from ui.windows.cel_editor import CelEditorWindow

    # Create and show window
    window = CelEditorWindow(strategy_name="New Strategy")
    window.show()

    # Run application
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())
