"""Evaluation Dialog for viewing and editing chart evaluation entries.

Displays support/resistance levels, targets, etc. extracted from AI analysis.
Allows editing values, colors, and exporting to chart.
"""

from __future__ import annotations

import logging
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QCheckBox, QMessageBox, QColorDialog,
    QHeaderView, QStyledItemDelegate, QStyle
)
from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtGui import QColor

from .evaluation_models import EvaluationEntry
from .evaluation_parser import EvaluationParser
from .evaluation_color_manager import ColorManager

logger = logging.getLogger(__name__)


class ColorCellDelegate(QStyledItemDelegate):
    """Custom delegate for color column to prevent selection highlight."""

    def paint(self, painter, option, index):
        """Paint cell without selection highlight."""
        opt = option
        opt.state &= ~QStyle.StateFlag.State_Selected
        super().paint(painter, opt, index)


class EvaluationDialog(QDialog):
    """Dialog for viewing and editing chart evaluation entries.

    Displays support/resistance levels, targets, etc. extracted from AI analysis.
    Allows editing values, colors, and exporting to chart.
    """

    def __init__(self, parent, entries: list[EvaluationEntry] | None = None):
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
        if hasattr(self.parent_window, 'width') and hasattr(self.parent_window, 'height'):
            self.resize(int(self.parent_window.width() * 1.5), int(self.parent_window.height() * 0.5))
        else:
            self.resize(800, 400)

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
                "Erlaubt sind nur Zahlen oder Zahl-Zahl."
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
            if not EvaluationParser.validate_value(value):
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
        chart = getattr(self.parent_window, "chart_widget", None)
        if not chart and hasattr(self.parent_window, 'service'):
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
