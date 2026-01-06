# Refactoring Plan: `_show_evaluation_popup` → `EvaluationDialog`

**Datum:** 2026-01-06
**Status:** ⚠️ PLANUNG - Nicht implementiert
**Aufwand:** ~3-4 Stunden
**Komplexität:** HOCH
**Priority:** MITTEL

---

## Problem Statement

### Current State:
- **Funktion:** `_show_evaluation_popup` in `chart_chat_actions_mixin.py:231`
- **CC:** 26 (KRITISCH)
- **LOC:** 411 (64% der gesamten Datei!)
- **Verschachtelte Funktionen:** 10+ Closures als Event-Handler
- **Verantwortlichkeiten:** 6+ (God Method Anti-Pattern)

### Issues:
1. **God Method:** Macht zu viel in einer Funktion
   - Parsing
   - Validation
   - UI-Erstellung
   - Event-Handling
   - Settings-Management
   - Chart-Export

2. **Nicht testbar:** 10+ verschachtelte Closures unmöglich zu Unit-testen

3. **Schwer wartbar:** Jede Änderung riskiert Seiteneffekte

4. **Verletzt SRP massiv:** Single Responsibility Principle

---

## Target State

### Neue Architektur:

```
chart_chat_actions_mixin.py
└── _show_evaluation_popup()  (3-5 Zeilen)
     └── erstellt EvaluationDialog

src/ui/dialogs/evaluation_dialog.py  (NEU)
├── EvaluationEntry (dataclass)
├── EvaluationParser
├── ColorManager
├── ColorCellDelegate
└── EvaluationDialog (QDialog)
```

### Ziele:
- **CC:** 26 → ~3 (im Mixin)
- **LOC:** 411 → ~5 (im Mixin), Rest in eigene Klassen
- **Testbarkeit:** Jede Komponente einzeln testbar
- **Wartbarkeit:** Klare Verantwortlichkeiten

---

## Implementation Plan

### Phase 1: Datenmodell extrahieren (30 Min)

**Neue Datei:** `src/ui/dialogs/evaluation_models.py`

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class EvaluationEntry:
    """Single evaluation entry (Support, Resistance, etc.)."""
    label: str
    value: str  # numeric or range like "100-200"
    info: str = ""
    color: str = "#0d6efd55"

    def is_range(self) -> bool:
        """Check if value is a range (e.g., '100-200')."""
        return '-' in self.value

    def get_range(self) -> tuple[float, float] | None:
        """Parse range value into (low, high)."""
        if not self.is_range():
            return None
        try:
            parts = self.value.split('-')
            return (float(parts[0]), float(parts[1]))
        except (ValueError, IndexError):
            return None

    def get_price(self) -> float | None:
        """Parse single price value."""
        if self.is_range():
            return None
        try:
            return float(self.value)
        except ValueError:
            return None

    def to_tuple(self) -> tuple[str, str, str, str]:
        """Convert to tuple for backward compatibility."""
        return (self.label, self.value, self.info, self.color)
```

**Tests:** `tests/ui/dialogs/test_evaluation_models.py`

---

### Phase 2: Parser extrahieren (45 Min)

**Neue Datei:** `src/ui/dialogs/evaluation_parser.py`

```python
import re
from typing import Optional
from .evaluation_models import EvaluationEntry

class EvaluationParser:
    """Parse evaluation entries from text or list."""

    VAR_PATTERN = re.compile(r"^\[#(.+?)\]$")
    NUMERIC_PATTERN = re.compile(r"^-?\d+(?:\.\d+)?(?:-?\d+(?:\.\d+)?)?$")

    @classmethod
    def parse_from_content(cls, content: str) -> tuple[list[EvaluationEntry], list[str]]:
        """Parse entries from text content.

        Returns:
            (valid_entries, invalid_lines)
        """
        entries = []
        invalid = []

        for line in content.splitlines():
            stripped = line.strip()
            if not stripped.startswith("[#") or not stripped.endswith("]"):
                continue

            entry = cls._parse_line(stripped)
            if entry:
                entries.append(entry)
            else:
                invalid.append(stripped)

        return entries, invalid

    @classmethod
    def parse_from_list(cls, entries_list: list) -> list[EvaluationEntry]:
        """Parse entries from list of tuples."""
        entries = []
        for e in entries_list:
            if len(e) >= 4:
                entries.append(EvaluationEntry(e[0], e[1], e[2], e[3]))
            elif len(e) == 3:
                entries.append(EvaluationEntry(e[0], e[1], e[2]))
        return entries

    @classmethod
    def _parse_line(cls, line: str) -> Optional[EvaluationEntry]:
        """Parse a single line like '[#Label; value; info; color]'."""
        m = cls.VAR_PATTERN.match(line)
        if not m:
            return None

        inner = m.group(1)
        parts = [p.strip() for p in inner.split(";")]

        if len(parts) < 2:
            return None

        label = parts[0]
        value = parts[1]
        info = parts[2] if len(parts) > 2 else ""
        color = parts[3] if len(parts) > 3 else "#0d6efd55"

        # Validate numeric pattern
        if not cls.NUMERIC_PATTERN.match(value):
            return None

        return EvaluationEntry(label, value, info, color)
```

**Tests:** `tests/ui/dialogs/test_evaluation_parser.py`

---

### Phase 3: Color Manager extrahieren (30 Min)

**Neue Datei:** `src/ui/dialogs/evaluation_color_manager.py`

```python
from PyQt6.QtCore import QSettings

class ColorManager:
    """Manage color rules and auto-assignment."""

    DEFAULT_RULES = {
        "stop": "#ef5350",
        "take profit": "#26a69a",
        "target": "#26a69a",
        "tp": "#26a69a",
        "support": "#2ca8b1",
        "demand": "#2ca8b1",
        "resistance": "#f39c12",
        "supply": "#f39c12",
        "entry long": "#0d6efd",
        "entry short": "#c2185b",
        "sma": "#9e9e9e",
        "ema": "#9e9e9e",
        "vwap": "#9e9e9e",
    }

    FALLBACK_PALETTE = ["#7e57c2", "#ffca28", "#00897b", "#5c6bc0"]

    def __init__(self):
        self.settings = QSettings("OrderPilot", "TradingApp")
        self.rules = self._load_rules()

    def _load_rules(self) -> dict[str, str]:
        """Load color rules from settings."""
        stored = self.settings.value("eval_color_rules", None)
        if isinstance(stored, dict):
            return {**self.DEFAULT_RULES, **stored}
        return self.DEFAULT_RULES.copy()

    def save_rules(self):
        """Save current rules to settings."""
        self.settings.setValue("eval_color_rules", self.rules)
        self.settings.sync()

    def pick_color_for_label(self, label: str) -> str:
        """Auto-assign color based on label keywords."""
        lbl = label.lower()

        # Check rules
        for key, color in self.rules.items():
            if key in lbl:
                return color

        # Fallback: use hash-based palette
        return self.FALLBACK_PALETTE[hash(lbl) % len(self.FALLBACK_PALETTE)]

    @staticmethod
    def ensure_alpha(color: str) -> str:
        """Ensure color has alpha channel for chart drawing."""
        color = color.strip()
        if color.startswith("#"):
            if len(color) == 7:  # #RRGGBB -> add alpha
                return color + "55"
            return color
        if color.lower().startswith("rgba"):
            return color
        return "#0d6efd55"
```

---

### Phase 4: EvaluationDialog Klasse erstellen (90 Min)

**Neue Datei:** `src/ui/dialogs/evaluation_dialog.py`

```python
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QCheckBox, QMessageBox, QColorDialog, QLabel,
    QHeaderView, QStyledItemDelegate
)
from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtGui import QColor

from .evaluation_models import EvaluationEntry
from .evaluation_parser import EvaluationParser
from .evaluation_color_manager import ColorManager

import logging

logger = logging.getLogger(__name__)


class ColorCellDelegate(QStyledItemDelegate):
    """Custom delegate for color column to prevent selection highlight."""
    def paint(self, painter, option, index):
        # Use base implementation without selection highlight
        opt = option
        opt.state &= ~QStyle.StateFlag.State_Selected
        super().paint(painter, opt, index)


class EvaluationDialog(QDialog):
    """Dialog for viewing and editing chart evaluation entries.

    Displays support/resistance levels, targets, etc. extracted from AI analysis.
    Allows editing values, colors, and exporting to chart.
    """

    def __init__(self, parent, entries: list[EvaluationEntry] = None):
        """Initialize evaluation dialog.

        Args:
            parent: Parent widget (usually ChartWindow)
            entries: List of EvaluationEntry objects
        """
        super().__init__(parent)

        self.parent_window = parent
        self.entries = entries or []
        self.color_manager = ColorManager()
        self.has_changes = False

        self._setup_ui()
        self._populate_table()
        self._connect_signals()

    # ============ UI Setup ============

    def _setup_ui(self):
        """Create dialog UI."""
        self.setWindowTitle("Auswertung")
        self.setModal(False)
        self.setWindowModality(Qt.WindowModality.NonModal)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)

        layout = QVBoxLayout(self)

        # Table
        self.table = self._create_table()
        layout.addWidget(self.table)

        # Buttons
        button_layout = self._create_buttons()
        layout.addLayout(button_layout)

        # Size
        self.resize(int(parent.width() * 1.5), int(parent.height() * 0.5))

    def _create_table(self) -> QTableWidget:
        """Create evaluation table."""
        table = QTableWidget(len(self.entries), 4, self)
        table.setHorizontalHeaderLabels(["Name", "Wert", "Info", "Farbe"])
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.EditTrigger.AllEditTriggers)
        table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        table.setWordWrap(True)

        # Column widths
        table.setColumnWidth(0, 180)
        table.setColumnWidth(1, 130)
        table.setColumnWidth(2, 160)
        table.setColumnWidth(3, 50)
        table.horizontalHeader().setStretchLastSection(False)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)

        # Custom delegate for color column
        table.setItemDelegateForColumn(3, ColorCellDelegate(table))

        return table

    def _create_buttons(self) -> QHBoxLayout:
        """Create button row."""
        layout = QHBoxLayout()

        # Save button (initially disabled)
        self.save_btn = QPushButton("Speichern", self)
        self.save_btn.setDisabled(True)

        # Draw controls
        self.all_draw_cb = QCheckBox("Alle zeichnen", self)
        self.all_draw_cb.setChecked(False)

        draw_btn = QPushButton("In Chart zeichnen", self)
        draw_btn.clicked.connect(self._on_draw_selected)

        # Edit buttons
        del_btn = QPushButton("Löschen", self)
        del_btn.clicked.connect(self._on_delete_selected)

        clear_btn = QPushButton("Leeren", self)
        clear_btn.clicked.connect(self._on_clear_all)

        # Color buttons
        auto_color_btn = QPushButton("Farben setzen", self)
        auto_color_btn.clicked.connect(self._on_auto_assign_colors)

        palette_btn = QPushButton("🎨", self)
        palette_btn.setToolTip("Farbregeln bearbeiten")
        palette_btn.clicked.connect(self._on_open_palette_dialog)

        # Close button
        close_btn = QPushButton("Schließen", self)
        close_btn.clicked.connect(self._on_close)

        # Layout
        layout.addWidget(self.save_btn)
        layout.addWidget(self.all_draw_cb)
        layout.addWidget(draw_btn)
        layout.addWidget(del_btn)
        layout.addWidget(clear_btn)
        layout.addWidget(auto_color_btn)
        layout.addWidget(palette_btn)
        layout.addStretch()
        layout.addWidget(close_btn)

        return layout

    # ============ Table Population ============

    def _populate_table(self):
        """Populate table with entries."""
        self.table.blockSignals(True)

        for row, entry in enumerate(self.entries):
            self.table.setItem(row, 0, QTableWidgetItem(entry.label))
            self.table.setItem(row, 1, QTableWidgetItem(entry.value))

            info_item = QTableWidgetItem(entry.info)
            info_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
            self.table.setItem(row, 2, info_item)

            self._set_color_cell(row, entry.color)

        self.table.blockSignals(False)
        self.table.resizeRowsToContents()
        self.has_changes = False

    def _set_color_cell(self, row: int, color_code: str):
        """Set color for a table row."""
        item = QTableWidgetItem("")
        item.setData(Qt.ItemDataRole.UserRole, color_code)
        item.setBackground(QColor(color_code))
        item.setToolTip(color_code)
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.table.setItem(row, 3, item)

    # ============ Signal Connections ============

    def _connect_signals(self):
        """Connect all signal handlers."""
        self.table.cellChanged.connect(self._on_cell_changed)
        self.table.cellDoubleClicked.connect(self._on_color_double_click)
        self.save_btn.clicked.connect(self._on_save_entries)

    # ============ Event Handlers ============

    def _on_cell_changed(self):
        """Mark as changed when table is edited."""
        self.has_changes = True
        self.save_btn.setDisabled(False)

    def _on_color_double_click(self, row: int, col: int):
        """Open color picker on double-click."""
        if col != 3:
            return

        item = self.table.item(row, 3)
        current = item.data(Qt.ItemDataRole.UserRole) if item else "#0d6efd55"

        chosen = QColorDialog.getColor(QColor(current), self, "Farbe wählen")
        if chosen.isValid():
            self._set_color_cell(row, chosen.name())
            self._on_cell_changed()

    def _on_save_entries(self):
        """Save current table entries."""
        entries, invalid_rows = self._extract_entries_from_table()

        if invalid_rows:
            QMessageBox.warning(
                self,
                "Speichern fehlgeschlagen",
                f"Ungültige Werte in Zeile(n): {', '.join(map(str, invalid_rows))}\n"
                "Erlaubt sind nur Zahlen oder zahl-zahl."
            )
            return

        self.entries = entries
        self.has_changes = False
        self.save_btn.setDisabled(True)

        # Update parent's cached entries
        if hasattr(self.parent_window, '_last_eval_entries'):
            self.parent_window._last_eval_entries = [e.to_tuple() for e in entries]

        QMessageBox.information(self, "Gespeichert", "Auswertung gespeichert.")

    def _on_delete_selected(self):
        """Delete selected row."""
        row = self.table.currentRow()
        if row < 0:
            return
        self.table.removeRow(row)
        self._on_cell_changed()

    def _on_clear_all(self):
        """Clear all entries."""
        self.table.setRowCount(0)
        self.entries = []
        if hasattr(self.parent_window, '_last_eval_entries'):
            self.parent_window._last_eval_entries = []
        self._on_cell_changed()

    def _on_auto_assign_colors(self):
        """Auto-assign colors based on label keywords."""
        for row in range(self.table.rowCount()):
            label_item = self.table.item(row, 0)
            if not label_item:
                continue

            color = self.color_manager.pick_color_for_label(label_item.text())
            self._set_color_cell(row, color)

        self._on_cell_changed()

    def _on_open_palette_dialog(self):
        """Open color palette customization dialog."""
        # TODO: Extract to separate ColorPaletteDialog class
        from .color_palette_dialog import ColorPaletteDialog
        dlg = ColorPaletteDialog(self, self.color_manager)
        dlg.exec()

    def _on_draw_selected(self):
        """Draw selected entry (or all) to chart."""
        if self.all_draw_cb.isChecked():
            self._draw_all_entries()
        else:
            self._draw_single_entry()

    def _on_close(self):
        """Handle close with unsaved changes warning."""
        if self.has_changes:
            res = QMessageBox.question(
                self,
                "Auswertung",
                "Sollen die Änderungen gespeichert werden?",
                QMessageBox.StandardButton.Yes |
                QMessageBox.StandardButton.No |
                QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Yes,
            )
            if res == QMessageBox.StandardButton.Yes:
                self._on_save_entries()
            elif res == QMessageBox.StandardButton.Cancel:
                return  # Abort close

        self.accept()

    # ============ Helper Methods ============

    def _extract_entries_from_table(self) -> tuple[list[EvaluationEntry], list[int]]:
        """Extract entries from table.

        Returns:
            (valid_entries, invalid_row_numbers)
        """
        entries = []
        invalid_rows = []

        for row in range(self.table.rowCount()):
            label_item = self.table.item(row, 0)
            value_item = self.table.item(row, 1)
            info_item = self.table.item(row, 2)
            color_item = self.table.item(row, 3)

            label = label_item.text().strip() if label_item else ""
            value = value_item.text().strip() if value_item else ""
            info = info_item.text().strip() if info_item else ""
            color = color_item.data(Qt.ItemDataRole.UserRole) if color_item else "#0d6efd55"

            # Validate
            if not EvaluationParser.NUMERIC_PATTERN.match(value):
                invalid_rows.append(row + 1)
                continue

            entries.append(EvaluationEntry(label, value, info, color or "#0d6efd55"))

        return entries, invalid_rows

    def _draw_single_entry(self):
        """Draw currently selected entry to chart."""
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Auswertung", "Bitte eine Zeile auswählen.")
            return

        self._draw_entry_at_row(row)

    def _draw_all_entries(self):
        """Draw all entries to chart."""
        for row in range(self.table.rowCount()):
            self._draw_entry_at_row(row)

    def _draw_entry_at_row(self, row: int):
        """Draw entry at specific row to chart."""
        label_item = self.table.item(row, 0)
        value_item = self.table.item(row, 1)
        info_item = self.table.item(row, 2)
        color_item = self.table.item(row, 3)

        if not value_item or not label_item:
            return

        label = label_item.text().strip().replace("'", "\\'")
        info = info_item.text().strip() if info_item else ""
        full_label = f"{label}" + (f" | {info}" if info else "")
        value = value_item.text().strip()
        color = color_item.data(Qt.ItemDataRole.UserRole) if color_item else "#0d6efd55"

        entry = EvaluationEntry(label, value, info, color or "#0d6efd55")

        # Get chart widget
        chart = getattr(self.parent_window.service, "chart_widget", None)
        if not chart:
            logger.warning("No chart_widget found")
            return

        # Draw range or line
        if entry.is_range():
            range_vals = entry.get_range()
            if range_vals:
                self._draw_range(chart, range_vals[0], range_vals[1], full_label, color)
        else:
            price = entry.get_price()
            if price is not None:
                self._draw_line(chart, price, full_label, color)

    def _draw_range(self, chart, low: float, high: float, label: str, color: str):
        """Draw price range rectangle on chart."""
        color_rect = self.color_manager.ensure_alpha(color)

        if hasattr(chart, "add_rect_range"):
            chart.add_rect_range(low, high, label, color_rect)
        elif hasattr(chart, "web_view"):
            js = (
                "window.chartAPI && window.chartAPI.addRectRange("
                f"{low}, {high}, '{color_rect}', '{label}');"
            )
            chart.web_view.page().runJavaScript(js)

    def _draw_line(self, chart, price: float, label: str, color: str):
        """Draw horizontal line on chart."""
        if hasattr(chart, "add_horizontal_line"):
            chart.add_horizontal_line(price, label, color)
        elif hasattr(chart, "web_view"):
            js = (
                "window.chartAPI && window.chartAPI.addHorizontalLine("
                f"{price}, '{color}', '{label}');"
            )
            chart.web_view.page().runJavaScript(js)
```

---

### Phase 5: ColorPaletteDialog extrahieren (30 Min)

**Neue Datei:** `src/ui/dialogs/color_palette_dialog.py`

```python
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QColorDialog
)
from PyQt6.QtGui import QColor

class ColorPaletteDialog(QDialog):
    """Dialog for editing color assignment rules."""

    def __init__(self, parent, color_manager):
        super().__init__(parent)
        self.color_manager = color_manager

        self.setWindowTitle("Farben zuordnen")
        layout = QVBoxLayout(self)

        self.buttons = {}
        for key, color in self.color_manager.rules.items():
            row_layout = self._create_rule_row(key, color)
            layout.addLayout(row_layout)

        # Apply button
        apply_btn = QPushButton("Übernehmen")
        apply_btn.clicked.connect(self._on_save)
        layout.addWidget(apply_btn)

    def _create_rule_row(self, key: str, color: str) -> QHBoxLayout:
        """Create row for one color rule."""
        layout = QHBoxLayout()

        label = QLabel(key)

        btn = QPushButton(" ")
        btn.setFixedWidth(32)
        btn.setStyleSheet(f"background:{color};")
        btn.clicked.connect(lambda: self._on_pick_color(key, btn))

        self.buttons[key] = btn

        layout.addWidget(label)
        layout.addStretch()
        layout.addWidget(btn)

        return layout

    def _on_pick_color(self, key: str, button: QPushButton):
        """Pick color for a rule."""
        current = self.color_manager.rules[key]
        chosen = QColorDialog.getColor(QColor(current), self, f"Farbe für {key}")

        if chosen.isValid():
            self.color_manager.rules[key] = chosen.name()
            button.setStyleSheet(f"background:{chosen.name()};")

    def _on_save(self):
        """Save rules and close."""
        self.color_manager.save_rules()
        self.accept()
```

---

### Phase 6: Mixin vereinfachen (15 Min)

**Geänderte Datei:** `src/chart_chat/chart_chat_actions_mixin.py`

```python
def _show_evaluation_popup(self, content: str | None = None, entries: list | None = None) -> None:
    """Show evaluation popup (simplified - logic moved to EvaluationDialog)."""
    from ui.dialogs.evaluation_dialog import EvaluationDialog
    from ui.dialogs.evaluation_parser import EvaluationParser
    from PyQt6.QtWidgets import QMessageBox

    # Parse entries
    if entries is not None:
        parsed_entries = EvaluationParser.parse_from_list(entries)
        invalid = []
    elif content:
        parsed_entries, invalid = EvaluationParser.parse_from_content(content)
    else:
        parsed_entries, invalid = [], []

    # Show warnings for invalid entries
    if invalid:
        QMessageBox.warning(
            self,
            "Auswertung fehlerhaft",
            "Einige Werte sind nicht numerisch und wurden übersprungen:\n\n" + "\n".join(invalid)
        )

    # Show info if no entries found
    if not parsed_entries:
        if getattr(self, "_evaluate_checkbox", None) and self._evaluate_checkbox.isChecked():
            QMessageBox.information(
                self,
                "Keine Auswertung",
                "Die Checkbox 'Auswertung' ist aktiviert, aber es konnten keine "
                "Auswertungsdaten im Format [#Label; Wert] extrahiert werden.\n\n"
                "Beispiel: [#Support Zone; 87450-87850]"
            )
        return

    # Close existing dialog if any
    if getattr(self, "_eval_dialog", None):
        try:
            self._eval_dialog.close()
        except Exception:
            pass

    # Create and show new dialog
    dlg = EvaluationDialog(self, entries=parsed_entries)
    dlg.destroyed.connect(lambda: setattr(self, "_eval_dialog", None))
    self._eval_dialog = dlg
    dlg.show()
```

**Ergebnis:**
- **CC:** 26 → ~3 (-88%)
- **LOC:** 411 → ~40 (-90%)
- Rest in separate Klassen

---

### Phase 7: Tests erstellen (60 Min)

**Neue Dateien:**

1. `tests/ui/dialogs/test_evaluation_models.py`
2. `tests/ui/dialogs/test_evaluation_parser.py`
3. `tests/ui/dialogs/test_color_manager.py`
4. `tests/ui/dialogs/test_evaluation_dialog.py`

**Test-Coverage Ziel:** >80%

---

## Migration Strategy

### Approach: **Big Bang** (Empfohlen)

**Warum:**
- Alles in einer PR
- Einfacher zu reviewen (zusammenhängende Änderung)
- Keine Zwischenzustände

### Alternative: **Incremental** (Sicherer, aber aufwändiger)

1. PR 1: Datenmodell + Parser (kann parallel zur alten Funktion existieren)
2. PR 2: ColorManager
3. PR 3: EvaluationDialog
4. PR 4: Mixin vereinfachen (alte Funktion löschen)

---

## Risks & Mitigation

### Risks:

1. **UI-Verhalten ändert sich:**
   - **Mitigation:** Pixel-perfekte UI-Tests mit Screenshots
   - **Fallback:** Feature-Flag, um alte Implementierung zu behalten

2. **Settings-Kompatibilität:**
   - **Mitigation:** ColorManager liest weiterhin `eval_color_rules` Key
   - **Migration:** Keine notwendig

3. **Regression in Chart-Export:**
   - **Mitigation:** Integration-Tests mit Mock-Chart
   - **Test:** Alle Kombinationen (Range, Line, Web, Native)

4. **Zeitaufwand unterschätzt:**
   - **Mitigation:** Timeboxing - max. 4h, sonst abbrechen und neu bewerten

---

## Success Criteria

### Must-Have:
- ✅ Alle bestehenden Features funktionieren
- ✅ UI sieht identisch aus
- ✅ Settings-Kompatibilität gewährleistet
- ✅ CC < 10 in allen neuen Klassen
- ✅ Test-Coverage > 70%

### Nice-to-Have:
- ✅ Test-Coverage > 80%
- ✅ Keyboard-Shortcuts (z.B. Ctrl+S für Save)
- ✅ Drag & Drop Reordering
- ✅ Undo/Redo

---

## Timeline (Estimated)

| Phase | Aufwand | Kumulativ |
|-------|---------|-----------|
| 1. Datenmodell | 30 Min | 0.5h |
| 2. Parser | 45 Min | 1.25h |
| 3. ColorManager | 30 Min | 1.75h |
| 4. EvaluationDialog | 90 Min | 3.25h |
| 5. ColorPaletteDialog | 30 Min | 3.75h |
| 6. Mixin vereinfachen | 15 Min | 4h |
| 7. Tests | 60 Min | 5h |
| **GESAMT** | **5h** | |

**Realistisch mit Puffer:** **6-8h** (inkl. Bugfixes, Refactorings, Reviews)

---

## Next Actions

### Immediate:
1. ⏸️ **WARTEN auf User-Freigabe** - Nicht ohne Zustimmung starten
2. 📅 Zeitslot blocken (6-8h ununterbrochen)
3. 🔄 Git Branch erstellen: `refactor/evaluation-dialog-class-extraction`

### Before Starting:
1. ✅ Backup erstellen (Git Stash / Branch)
2. ✅ Feature-Flag vorbereiten (optional)
3. ✅ Screenshots der aktuellen UI machen (Referenz)

### During Implementation:
1. 🧪 Test-Driven: Tests zuerst schreiben
2. 📝 Commits nach jeder Phase
3. ⏱️ Timeboxing: Max. geschätzte Zeit pro Phase

### After Implementation:
1. 🧪 Manual Testing: Alle Workflows durchspielen
2. 📸 Screenshot-Vergleich: UI identisch?
3. 📊 CC-Messung: Ziel erreicht?
4. 📄 Update REFACTORING_FINAL_REPORT

---

## Conclusion

Dieses Refactoring ist **komplex aber notwendig**. Die Funktion ist ein **Wartungs-Albtraum** mit 411 LOC und CC=26.

**Empfehlung:**
- ✅ Durchführen (hoher ROI für Code-Qualität)
- ⏱️ Timeboxing: Max. 8h
- 🎯 Fokus: Funktionalität erhalten, Tests schreiben, CC reduzieren

**Alternative:**
- ⚠️ Status Quo akzeptieren
- 📋 Dokumentieren als "Legacy Code - Do Not Touch"
- 🔒 Funktionalität einfrieren

---

**Status:** ⚠️ PLANUNG ABGESCHLOSSEN - Wartet auf Implementierung
**Nächster Schritt:** User-Entscheidung einholen

