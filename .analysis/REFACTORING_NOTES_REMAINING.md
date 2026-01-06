# Refactoring-Notizen: Verbleibende Komplexe Funktionen

## 1. `_show_evaluation_popup` (chart_chat_actions_mixin.py:231)

**Status:** SEHR KOMPLEX - Benötigt großes Refactoring
- **CC:** 26
- **LOC:** 411 (64% der gesamten Datei!)
- **Problem:** God Method - macht zu viel

### Aktuelle Probleme:
1. Parsing, Validierung, UI-Erstellung, Event-Handling, Export - alles in einer Funktion
2. 10+ verschachtelte Funktionen (Closures)
3. Sehr schwer zu testen
4. Verletzt Single Responsibility Principle massiv

### Empfohlenes Refactoring:
**Neue Klasse: `EvaluationDialog`**

```python
class EvaluationDialog(QDialog):
    """Dialog für Chart-Auswertungen."""

    def __init__(self, parent, entries=None, content=None):
        super().__init__(parent)
        self.entries = self._parse_entries(entries, content)
        self._setup_ui()
        self._setup_color_rules()
        self._connect_signals()

    def _parse_entries(self, entries, content):
        """Parse evaluation entries."""
        # Extract from _show_evaluation_popup lines 243-300
        pass

    def _setup_ui(self):
        """Create dialog UI."""
        # Extract from lines 312-337
        self._create_table()
        self._create_buttons()

    def _create_table(self):
        """Create evaluation table."""
        pass

    def _setup_color_rules(self):
        """Load color rules from settings."""
        # Extract from lines 340-360
        pass

    def _connect_signals(self):
        """Connect all signal handlers."""
        pass

    # Handler methods (extract nested functions)
    def _on_color_double_click(self, row, col):
        pass

    def _auto_assign_colors(self):
        pass

    def _open_palette_dialog(self):
        pass

    def _save_entries(self):
        pass

    def _draw_selected(self):
        pass

    def _export_to_chart(self):
        pass
```

### Dann in Mixin:
```python
def _show_evaluation_popup(self, content=None, entries=None):
    """Show evaluation popup (simplified)."""
    dialog = EvaluationDialog(self, entries=entries, content=content)
    dialog.show()
    self._eval_dialog = dialog
```

**Reduktion:** CC 26 → ~3, LOC 411 → ~15 (im Mixin)

---

## Pragmatische Entscheidung:
Wegen der Größe (411 LOC) und Komplexität dieser Funktion würde ein vollständiges Refactoring mehrere Stunden dauern.

**Nächste Schritte:**
1. Die anderen 5 Funktionen refactoren (einfacher)
2. Dann zurück zu dieser Funktion kommen
3. Oder als separates Task markieren

---

*Notizen erstellt: 2026-01-06*
