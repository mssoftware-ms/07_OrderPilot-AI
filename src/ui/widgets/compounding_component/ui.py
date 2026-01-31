"""ui.py
PyQt6 UI-Komponente (einbettbar) für den Compounding-Rechner.

Refactored to use mixin pattern for better organization:
- CompoundingUISetupMixin: UI widget creation
- CompoundingUIEventsMixin: Event handlers & exports
- CompoundingUIPlotsMixin: Chart rendering

- 2 Tabs: (Eingaben + KPIs) und (Details mit modernem Chart).
- Live-Updates; keine Signal-Endlosschleifen (QSignalBlocker/Guard).
- Theme-kompatibel: keine hardcodierten Farben; Qt-Palette wird übernommen.
- Matplotlib-Embedding via FigureCanvasQTAgg (backend_qtagg).
- Modernes Chart-Design mit Gradient-Fills und mehreren Datenserien.
"""

from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import QSettings
from PyQt6.QtWidgets import QWidget, QTabWidget, QVBoxLayout

from .compounding_ui_setup import CompoundingUISetupMixin
from .compounding_ui_events import CompoundingUIEventsMixin
from .compounding_ui_plots import CompoundingUIPlotsMixin


class CompoundingPanel(
    CompoundingUISetupMixin,
    CompoundingUIEventsMixin,
    CompoundingUIPlotsMixin,
    QWidget
):
    """Compounding/P&L Calculator Panel with settings persistence.

    This widget combines three mixins:
    1. Setup: UI widget creation and layout
    2. Events: User interaction and business logic
    3. Plots: Chart rendering and visualization

    The mixins are applied in Method Resolution Order (MRO):
    CompoundingUISetupMixin -> CompoundingUIEventsMixin -> CompoundingUIPlotsMixin -> QWidget
    """

    SETTINGS_KEY = "CompoundingPanel"

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)

        # State variables
        self._last_edited: Optional[str] = None  # "daily" oder "target"
        self._suppress_updates: bool = False
        self._settings = QSettings("OrderPilot", "CompoundingPanel")

        # Main UI structure
        self.tabs = QTabWidget(self)
        self.tab_inputs = QWidget()
        self.tab_details = QWidget()
        self.tabs.addTab(self.tab_inputs, "Compounding")
        self.tabs.addTab(self.tab_details, "Details")

        # Save settings when switching tabs
        self.tabs.currentChanged.connect(self._on_tab_changed)

        root = QVBoxLayout(self)
        root.addWidget(self.tabs)

        # Build UI (methods from CompoundingUISetupMixin)
        # Build details tab first (creates self.table used by recompute)
        self._build_tab_details()
        self._build_tab_inputs()

        # Load saved settings after UI is built (method from CompoundingUIEventsMixin)
        self._load_settings()

        # Initial calculation (method from CompoundingUIEventsMixin)
        self.recompute(origin="init")


if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication, QMainWindow

    app = QApplication(sys.argv)
    win = QMainWindow()
    win.setWindowTitle("CompoundingPanel Demo")
    win.setCentralWidget(CompoundingPanel())
    win.resize(1100, 750)
    win.show()
    sys.exit(app.exec())
