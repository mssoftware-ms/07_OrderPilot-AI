"""
UI-Komponenten für den KO-Finder.

Enthält:
- KOProductTableModel: TableModel für Produktliste
- KOFilterPanel: Filter-Controls
- KOResultPanel: Ergebnis-Anzeige mit Tabelle
- KOSettingsDialog: Einstellungs-Dialog für Score-Parameter
"""

from .filter_panel import KOFilterPanel
from .result_panel import KOResultPanel
from .settings_dialog import KOSettingsDialog
from .table_model import KOProductTableModel

__all__ = [
    "KOProductTableModel",
    "KOFilterPanel",
    "KOResultPanel",
    "KOSettingsDialog",
]
