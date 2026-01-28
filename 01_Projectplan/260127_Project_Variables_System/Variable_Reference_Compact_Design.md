# 📊 Variable Reference Popup - Compact Design (Theme-Konsistent)

**Version:** 2.0 (Refactored)
**Erstellt:** 2026-01-28
**Theme:** Dark Orange Palette (OrderPilot-AI Standard)

---

## 🎨 Design System Integration

### Color Palette (aus `DARK_ORANGE_PALETTE`)

```python
# Backgrounds
BACKGROUND_MAIN = "#0F1115"        # Main window
BACKGROUND_SURFACE = "#1A1D23"     # Cards, groups
BACKGROUND_INPUT = "#23262E"       # Table cells, inputs

# Borders
BORDER_MAIN = "#32363E"
BORDER_FOCUS = "#F29F05"           # Orange focus

# Text
TEXT_PRIMARY = "#EAECEF"           # High emphasis
TEXT_SECONDARY = "#848E9C"         # Labels, secondary text
TEXT_INVERSE = "#0F1115"           # On orange background

# Accent
PRIMARY = "#F29F05"                # Orange accent
PRIMARY_HOVER = "#FFAD1F"
SUCCESS = "#0ECB81"                # Green
ERROR = "#F6465D"                  # Red
INFO = "#5D6878"                   # Grey-blue

# Components
SELECTION_BG = "rgba(242, 159, 5, 0.2)"  # Orange 20%
BUTTON_BG = "#2A2D33"
BUTTON_HOVER_BORDER = "#F29F05"
```

### Typography

```python
FONT_FAMILY = "'Aptos', 'Segoe UI', sans-serif"
FONT_SIZE_XS = "11px"  # Table cell, secondary
FONT_SIZE_SM = "12px"  # Table header
FONT_SIZE_MD = "14px"  # Normal text
```

### Spacing

```python
SPACING_XS = "2px"
SPACING_SM = "4px"
SPACING_MD = "8px"
SPACING_LG = "16px"
RADIUS_SM = "4px"
```

---

## 🖼️ Compact UI Layout

### Window Dimensions
```
Width:  800px  (vs 900px original - 100px saved)
Height: 600px  (vs 700px original - 100px saved)
Min Width:  600px
Min Height: 400px
```

### Layout Structure (platzsparend)

```
┌──────────────────────────────────────────────────────────────┐
│  📋 Variables          [🔍___________][All ▼] [Defined ▼] [x]│ ← 40px compact header
├──────────────────────────────────────────────────────────────┤
│┌─────────────────────────────────────────────────────────────┐│
││ 📊 Chart (8)   │ Type   │ Value          │ 📋              ││ ← 24px row height
││────────────────┼────────┼────────────────┼─────────────────││
││ chart.price    │ float  │ 95250.0        │ [Copy]          ││
││ chart.volume   │ float  │ 125.5          │ [Copy]          ││
││ ... (6 more collapsed by default)                           ││
│└─────────────────────────────────────────────────────────────┘│
│┌─────────────────────────────────────────────────────────────┐│
││ 🤖 Bot (25)    │ Type   │ Value          │ 📋              ││
││────────────────┼────────┼────────────────┼─────────────────││
││ bot.leverage   │ int    │ 10             │ [Copy]          ││
││ bot.sl_atr_mul.│ float  │ 1.5            │ [Copy]          ││
││ ▼ bot.entry.* (15) ──────────────────────────── [Expand] ▼ ││
│└─────────────────────────────────────────────────────────────┘│
│┌─────────────────────────────────────────────────────────────┐│
││ 🎨 Project (12)│ Type   │ Value          │ 📋              ││
││────────────────┼────────┼────────────────┼─────────────────││
││ proj.my_min_pr.│ float  │ 90000.0        │ [Copy]          ││
││ proj.my_max_le.│ int    │ 15             │ [Copy]          ││
│└─────────────────────────────────────────────────────────────┘│
├──────────────────────────────────────────────────────────────┤
│ 57 vars │ [📋 Copy All] [💾 Export] [🔄 Refresh]     [Close] │ ← 32px compact footer
└──────────────────────────────────────────────────────────────┘
```

---

## 🎯 Platzspar-Optimierungen

### 1. Compact Header (40px statt 60px)
```python
# BEFORE (verbose)
"🔍 Search: [________________]  Category: [All ▼]  Show: [All ▼]"

# AFTER (compact)
"[🔍___________][All ▼] [Defined ▼]"  # Icon-first, inline filters
```

### 2. Smaller Row Height (24px statt 32px)
```python
# Table Row
row_height = 24  # vs 32px standard
font_size = 11   # vs 12px

# Header Row
header_height = 28  # vs 36px
```

### 3. Truncated Variable Names (mit Tooltip)
```python
# Long names werden gekürzt
"project.my_min_price"     → "proj.my_min_pr." (max 16 chars)
"bot.entry.weight_confluenc" → "bot.entry.wei.c."

# Vollständiger Name im Tooltip
tooltip = "project.my_min_price (float) - Minimum BTC Preis für Entry"
```

### 4. Collapsed Subgroups
```python
# Subgroups (z.B. bot.entry.*) standardmäßig collapsed
"▶ bot.entry.* (15 items) ────────────── [Expand]"

# Klick auf Row: Expand inline (keine neue Tabelle)
"▼ bot.entry.* (15 items) ────────────── [Collapse]"
  "  bot.entry.weight_confluence  │ float │ 0.3 │ [Copy]"
  "  bot.entry.weight_regime      │ float │ 0.25│ [Copy]"
  ...
```

### 5. Icon-Only Copy Button (statt Text)
```python
# BEFORE
"[Copy]"  # 50px width

# AFTER
"📋"      # 24px width (icon only, tooltip: "Copy to clipboard")
```

### 6. Compact Footer (32px statt 48px)
```python
# Count Badge + Icon Buttons
"57 vars │ [📋 Copy All] [💾 Export] [🔄 Refresh]     [Close]"
# vs
"Total: 57 variables (8 chart, 25 bot, 12 project, 8 ind, 4 reg)"
```

---

## 🎨 Stylesheet (QSS)

```python
QSS_VARIABLE_REFERENCE = f"""
/* Variable Reference Dialog - Compact Theme */

QDialog {{
    background-color: {BACKGROUND_MAIN};
    color: {TEXT_PRIMARY};
    font-family: {FONT_FAMILY};
    font-size: {FONT_SIZE_MD};
}}

/* ===== HEADER ===== */
QWidget#header {{
    background-color: {BACKGROUND_SURFACE};
    border-bottom: 1px solid {BORDER_MAIN};
    padding: {SPACING_SM};
    min-height: 40px;
    max-height: 40px;
}}

/* Search Input (compact) */
QLineEdit#search {{
    background-color: {BACKGROUND_INPUT};
    border: 1px solid {BORDER_MAIN};
    border-radius: {RADIUS_SM};
    padding: {SPACING_SM};
    font-size: {FONT_SIZE_SM};
    color: {TEXT_PRIMARY};
    min-height: 28px;
    max-height: 28px;
}}

QLineEdit#search:focus {{
    border: 1px solid {BORDER_FOCUS};
}}

/* Filter Dropdowns (compact) */
QComboBox {{
    background-color: {BACKGROUND_INPUT};
    border: 1px solid {BORDER_MAIN};
    border-radius: {RADIUS_SM};
    padding: {SPACING_SM};
    font-size: {FONT_SIZE_SM};
    color: {TEXT_PRIMARY};
    min-height: 28px;
    max-height: 28px;
    min-width: 100px;
}}

QComboBox:hover {{
    border: 1px solid {BUTTON_HOVER_BORDER};
}}

QComboBox::drop-down {{
    border: none;
    width: 20px;
}}

QComboBox::down-arrow {{
    image: url(:/icons/chevron_down_white.png);
    width: 12px;
    height: 12px;
}}

/* ===== CATEGORY GROUPS (Collapsible) ===== */
QGroupBox {{
    background-color: {BACKGROUND_SURFACE};
    border: 1px solid {BORDER_MAIN};
    border-radius: {RADIUS_SM};
    margin-top: {SPACING_MD};
    padding-top: {SPACING_MD};
    font-size: {FONT_SIZE_SM};
    font-weight: 600;
    color: {TEXT_PRIMARY};
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 {SPACING_SM};
    background-color: {BACKGROUND_SURFACE};
    color: {PRIMARY};  /* Orange category titles */
}}

/* ===== TABLE ===== */
QTableWidget {{
    background-color: {BACKGROUND_MAIN};
    alternate-background-color: {BACKGROUND_INPUT};
    gridline-color: {BORDER_MAIN};
    border: none;
    font-size: {FONT_SIZE_XS};  /* Compact font */
}}

/* Table Header */
QHeaderView::section {{
    background-color: {BACKGROUND_SURFACE};
    color: {TEXT_SECONDARY};
    padding: {SPACING_SM};
    border: none;
    border-bottom: 1px solid {BORDER_MAIN};
    font-size: {FONT_SIZE_SM};
    font-weight: 600;
    height: 28px;  /* Compact header */
}}

/* Table Rows */
QTableWidget::item {{
    padding: {SPACING_SM};
    border: none;
    height: 24px;  /* Compact rows */
}}

QTableWidget::item:selected {{
    background-color: {SELECTION_BG};
    color: {TEXT_PRIMARY};
}}

QTableWidget::item:hover {{
    background-color: {BACKGROUND_INPUT};
}}

/* ===== BUTTONS ===== */
QPushButton {{
    background-color: {BUTTON_BG};
    border: 1px solid {BORDER_MAIN};
    border-radius: {RADIUS_SM};
    color: {TEXT_PRIMARY};
    font-size: {FONT_SIZE_SM};
    padding: {SPACING_SM} {SPACING_MD};
    min-height: 28px;  /* Compact buttons */
}}

QPushButton:hover {{
    border: 1px solid {BUTTON_HOVER_BORDER};
    color: {PRIMARY};
}}

QPushButton:pressed {{
    background-color: {BACKGROUND_INPUT};
}}

/* Icon-Only Copy Button (extra compact) */
QPushButton#copy_btn {{
    background: transparent;
    border: none;
    padding: {SPACING_XS};
    min-width: 24px;
    max-width: 24px;
    min-height: 24px;
    max-height: 24px;
    font-size: 14px;  /* Emoji size */
}}

QPushButton#copy_btn:hover {{
    background-color: {BACKGROUND_INPUT};
    border-radius: {RADIUS_SM};
}}

/* Primary Action Button */
QPushButton#primary {{
    background-color: {PRIMARY};
    color: {TEXT_INVERSE};
    border: none;
    font-weight: 600;
}}

QPushButton#primary:hover {{
    background-color: {PRIMARY_HOVER};
}}

/* ===== FOOTER ===== */
QWidget#footer {{
    background-color: {BACKGROUND_SURFACE};
    border-top: 1px solid {BORDER_MAIN};
    padding: {SPACING_SM};
    min-height: 32px;
    max-height: 32px;
}}

QLabel#count_label {{
    color: {TEXT_SECONDARY};
    font-size: {FONT_SIZE_SM};
}}

/* ===== SCROLLBAR (Thin, Minimal) ===== */
QScrollBar:vertical {{
    background: {BACKGROUND_MAIN};
    width: 8px;  /* Thin scrollbar */
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background: {BORDER_MAIN};
    border-radius: 4px;
    min-height: 30px;
}}

QScrollBar::handle:vertical:hover {{
    background: {PRIMARY};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;  /* No arrow buttons */
}}

/* ===== TOOLTIP ===== */
QToolTip {{
    background-color: {BACKGROUND_SURFACE};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER_MAIN};
    padding: {SPACING_SM};
    font-size: {FONT_SIZE_SM};
}}
"""
```

---

## 🛠️ Implementation (Compact Version)

```python
# src/ui/dialogs/variable_reference_dialog.py

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QComboBox,
    QTableWidget, QTableWidgetItem, QPushButton, QGroupBox,
    QLabel, QHeaderView, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QKeySequence, QShortcut
from src.ui.design_system import DARK_ORANGE_PALETTE as THEME


class VariableReferenceDialog(QDialog):
    """Compact Variable Reference Popup - Theme Consistent."""

    variable_inserted = pyqtSignal(str)  # Emit variable name for insertion

    def __init__(self, parent, context_builder):
        super().__init__(parent)
        self.context_builder = context_builder
        self.context = {}
        self.auto_refresh_enabled = False

        self._setup_ui()
        self._apply_theme()
        self._populate()

    def _setup_ui(self):
        """Setup compact UI."""
        self.setWindowTitle("📋 Variables")
        self.resize(800, 600)  # Compact size
        self.setMinimumSize(600, 400)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # === HEADER (Compact: 40px) ===
        header = QWidget(objectName="header")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(8, 4, 8, 4)
        header_layout.setSpacing(8)

        # Search (icon-first, compact)
        self.search_input = QLineEdit(objectName="search")
        self.search_input.setPlaceholderText("🔍 Search...")
        self.search_input.textChanged.connect(self._on_search)
        header_layout.addWidget(self.search_input, 1)

        # Category Filter (compact dropdown)
        self.category_filter = QComboBox()
        self.category_filter.addItems(["All", "Chart", "Bot", "Project", "Indicators", "Regime"])
        self.category_filter.currentTextChanged.connect(self._on_filter)
        header_layout.addWidget(self.category_filter)

        # Show Filter (compact dropdown)
        self.show_filter = QComboBox()
        self.show_filter.addItems(["Defined", "All", "Undefined"])
        self.show_filter.currentTextChanged.connect(self._on_filter)
        header_layout.addWidget(self.show_filter)

        layout.addWidget(header)

        # === CATEGORY GROUPS (Scrollable) ===
        from PyQt6.QtWidgets import QScrollArea
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        scroll_content = QWidget()
        self.groups_layout = QVBoxLayout(scroll_content)
        self.groups_layout.setContentsMargins(8, 8, 8, 8)
        self.groups_layout.setSpacing(8)
        self.groups_layout.addStretch()

        scroll.setWidget(scroll_content)
        layout.addWidget(scroll, 1)

        # === FOOTER (Compact: 32px) ===
        footer = QWidget(objectName="footer")
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(8, 4, 8, 4)
        footer_layout.setSpacing(8)

        self.count_label = QLabel("0 vars", objectName="count_label")
        footer_layout.addWidget(self.count_label)

        footer_layout.addWidget(QLabel("│"))  # Divider

        copy_all_btn = QPushButton("📋 Copy All")
        copy_all_btn.setToolTip("Copy all variable names")
        copy_all_btn.clicked.connect(self._on_copy_all)
        footer_layout.addWidget(copy_all_btn)

        export_btn = QPushButton("💾 Export")
        export_btn.setToolTip("Export as CSV")
        export_btn.clicked.connect(self._on_export)
        footer_layout.addWidget(export_btn)

        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setToolTip("Reload live values")
        refresh_btn.clicked.connect(self._on_refresh)
        footer_layout.addWidget(refresh_btn)

        footer_layout.addStretch()

        close_btn = QPushButton("Close", objectName="primary")
        close_btn.clicked.connect(self.accept)
        footer_layout.addWidget(close_btn)

        layout.addWidget(footer)

        # Keyboard Shortcut
        QShortcut(QKeySequence("Esc"), self, self.reject)
        QShortcut(QKeySequence("Ctrl+F"), self, self.search_input.setFocus)

    def _apply_theme(self):
        """Apply theme stylesheet."""
        # Use QSS_VARIABLE_REFERENCE from above
        self.setStyleSheet(QSS_VARIABLE_REFERENCE)

    def _populate(self):
        """Populate with all variable groups."""
        # Clear existing groups
        while self.groups_layout.count() > 1:
            item = self.groups_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Build context
        self.context = self.context_builder.build_for_reference(...)

        # Add category groups
        self._add_category_group("📊 Chart Data", "chart.", 8)
        self._add_category_group("🤖 Bot Configuration", "bot.", 25)
        self._add_category_group("🎨 Project Variables", "project.", 12)
        self._add_category_group("📈 Indicators", "indicators.", 8)
        self._add_category_group("🌍 Regime", "regime.", 4)

        # Update count
        self.count_label.setText(f"{len(self.context)} vars")

    def _add_category_group(self, title: str, prefix: str, count: int):
        """Add collapsible category group with compact table."""
        group = QGroupBox(f"{title} ({count})")
        group.setCheckable(True)
        group.setChecked(True)  # Expanded by default

        group_layout = QVBoxLayout(group)
        group_layout.setContentsMargins(4, 8, 4, 4)
        group_layout.setSpacing(0)

        # Compact table
        table = QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["Variable", "Type", "Value", "📋"])
        table.horizontalHeader().setStretchLastSection(False)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        table.setColumnWidth(1, 60)   # Type column
        table.setColumnWidth(2, 120)  # Value column
        table.setColumnWidth(3, 32)   # Copy button column
        table.verticalHeader().setVisible(False)
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        # Filter context by prefix
        filtered = {k: v for k, v in self.context.items() if k.startswith(prefix)}

        table.setRowCount(len(filtered))
        for row, (var_name, var_data) in enumerate(filtered.items()):
            # Truncate long names (with tooltip)
            display_name = var_name if len(var_name) <= 16 else var_name[:13] + "..."

            # Variable name (truncated)
            name_item = QTableWidgetItem(display_name)
            name_item.setToolTip(f"{var_name}\n{var_data.get('description', '')}")
            table.setItem(row, 0, name_item)

            # Type
            type_item = QTableWidgetItem(var_data["type"])
            table.setItem(row, 1, type_item)

            # Value
            value = var_data["value"] if var_data["has_value"] else "N/A"
            value_item = QTableWidgetItem(str(value))
            if not var_data["has_value"]:
                value_item.setForeground(Qt.GlobalColor.gray)
            table.setItem(row, 2, value_item)

            # Copy button (icon-only, compact)
            copy_btn = QPushButton("📋", objectName="copy_btn")
            copy_btn.setToolTip("Copy to clipboard")
            copy_btn.clicked.connect(lambda checked, name=var_name: self._on_copy(name))
            table.setCellWidget(row, 3, copy_btn)

            # Double-click to insert
            table.itemDoubleClicked.connect(
                lambda item, name=var_name: self.variable_inserted.emit(name)
            )

        group_layout.addWidget(table)
        self.groups_layout.insertWidget(self.groups_layout.count() - 1, group)

    def _on_copy(self, variable_name: str):
        """Copy variable name to clipboard."""
        QApplication.clipboard().setText(variable_name)
        # Optional: Show toast notification "Copied!"

    def _on_copy_all(self):
        """Copy all variable names."""
        all_vars = "\n".join(self.context.keys())
        QApplication.clipboard().setText(all_vars)

    def _on_export(self):
        """Export to CSV."""
        # ... CSV export logic

    def _on_refresh(self):
        """Reload live values."""
        self._populate()

    def _on_search(self, text: str):
        """Filter by search text."""
        # ... search logic

    def _on_filter(self):
        """Apply category/show filters."""
        # ... filter logic
```

---

## 📊 Space Savings Summary

| Component | Before | After | Saved |
|-----------|--------|-------|-------|
| Window Width | 900px | 800px | **-100px** |
| Window Height | 700px | 600px | **-100px** |
| Header Height | 60px | 40px | **-20px** |
| Row Height | 32px | 24px | **-8px per row** |
| Footer Height | 48px | 32px | **-16px** |
| Copy Button | 50px | 24px | **-26px per row** |
| **Total Savings** | | | **~15-20% smaller** |

---

## ✅ Benefits

1. **Platzsparend:** 15-20% kleiner, passt besser auf kleinere Bildschirme
2. **Theme-Konsistent:** Nutzt DARK_ORANGE_PALETTE aus Design-System
3. **Chart-Style:** Gleiche Ästhetik wie Chart Window (dunkles Theme, Orange Accents)
4. **Performance:** Kleinere UI = schnelleres Rendering
5. **Fokus:** Weniger visuelle Ablenkung, mehr Inhalt sichtbar

---

**Erstellt:** 2026-01-28
**Version:** 2.0 (Compact & Theme-Consistent)
**Status:** ✅ Ready for Implementation
**Design-System:** DARK_ORANGE_PALETTE
