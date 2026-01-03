"""Chart Markings Manager Dialog.

Provides comprehensive management interface for all chart markings:
- Zones (Support/Resistance/Demand/Supply)
- Entry Markers (Long/Short)
- Structure Breaks (BoS/CHoCH/MSB)
- Lines (Stop-Loss/Take-Profit/Entry)

Features:
- View all markings in categorized table
- Lock/Unlock individual markings
- Edit/Delete markings (if unlocked)
- Filter by type and lock status
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

if TYPE_CHECKING:
    from src.ui.widgets.embedded_tradingview_chart import EmbeddedTradingViewChart

logger = logging.getLogger(__name__)


class ChartMarkingsManagerDialog(QDialog):
    """Dialog for managing all chart markings."""

    def __init__(self, chart_widget: "EmbeddedTradingViewChart", parent=None):
        super().__init__(parent)
        self.chart = chart_widget
        self.setWindowTitle("Chart Markings Manager")
        self.setModal(False)
        self.resize(900, 600)

        self._setup_ui()
        self._load_markings()

    def _setup_ui(self):
        """Setup dialog UI."""
        layout = QVBoxLayout(self)

        # Filters row
        filters = QHBoxLayout()
        filters.addWidget(QLabel("Type:"))
        self.type_filter = QComboBox()
        self.type_filter.addItems([
            "All Types", "Zones", "Entry Markers", "Structure Breaks", "Lines"
        ])
        self.type_filter.currentTextChanged.connect(self._filter_markings)
        filters.addWidget(self.type_filter)

        self.locked_only_cb = QCheckBox("Locked Only")
        self.locked_only_cb.stateChanged.connect(self._filter_markings)
        filters.addWidget(self.locked_only_cb)

        filters.addStretch()
        layout.addLayout(filters)

        # Table: Type | Name | Price/Range | Active | Lock
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels([
            "Type", "Name", "Price/Range", "Active", "Lock"
        ])
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.cellDoubleClicked.connect(self._on_cell_double_click)
        layout.addWidget(self.table)

        # Buttons
        btn_row = QHBoxLayout()

        self.lock_btn = QPushButton("🔒 Lock Selected")
        self.lock_btn.clicked.connect(lambda: self._toggle_lock(True))
        btn_row.addWidget(self.lock_btn)

        self.unlock_btn = QPushButton("🔓 Unlock Selected")
        self.unlock_btn.clicked.connect(lambda: self._toggle_lock(False))
        btn_row.addWidget(self.unlock_btn)

        btn_row.addSpacing(20)

        self.edit_btn = QPushButton("✏️ Edit")
        self.edit_btn.clicked.connect(self._edit_selected)
        btn_row.addWidget(self.edit_btn)

        self.delete_btn = QPushButton("🗑️ Delete")
        self.delete_btn.clicked.connect(self._delete_selected)
        btn_row.addWidget(self.delete_btn)

        btn_row.addStretch()

        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self._load_markings)
        btn_row.addWidget(refresh_btn)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)

        layout.addLayout(btn_row)

    def _load_markings(self):
        """Load all markings from chart into table."""
        self.table.setRowCount(0)
        self._all_markings = []  # Store for filtering

        # Debug logging
        logger.info(f"Loading markings from chart: {self.chart.__class__.__name__}")
        logger.info(f"Has _zones: {hasattr(self.chart, '_zones')}")
        logger.info(f"Has _entry_markers: {hasattr(self.chart, '_entry_markers')}")
        logger.info(f"Has _structure_markers: {hasattr(self.chart, '_structure_markers')}")
        logger.info(f"Has _sl_lines: {hasattr(self.chart, '_sl_lines')}")

        # Load zones
        if hasattr(self.chart, '_zones'):
            zones = self.chart._zones.get_all()
            logger.info(f"Found {len(zones)} zones")
            for zone in zones:
                self._add_marking_row("Zone", zone)

        # Load entry markers
        if hasattr(self.chart, '_entry_markers'):
            markers = self.chart._entry_markers.get_all()
            logger.info(f"Found {len(markers)} entry markers")
            for marker in markers:
                self._add_marking_row("Entry", marker)

        # Load structure breaks
        if hasattr(self.chart, '_structure_markers'):
            markers = self.chart._structure_markers.get_all()
            logger.info(f"Found {len(markers)} structure markers")
            for marker in markers:
                self._add_marking_row("Structure", marker)

        # Load lines
        if hasattr(self.chart, '_sl_lines'):
            lines = self.chart._sl_lines.get_all()
            logger.info(f"Found {len(lines)} lines")
            for line in lines:
                self._add_marking_row("Line", line)

        logger.info(f"Total markings loaded: {len(self._all_markings)}")

        # Show debug info if no markings found
        if len(self._all_markings) == 0:
            debug_info = []
            debug_info.append(f"Chart class: {self.chart.__class__.__name__}")
            debug_info.append(f"\nAttribute checks:")
            debug_info.append(f"  _zones: {hasattr(self.chart, '_zones')}")
            debug_info.append(f"  _entry_markers: {hasattr(self.chart, '_entry_markers')}")
            debug_info.append(f"  _structure_markers: {hasattr(self.chart, '_structure_markers')}")
            debug_info.append(f"  _sl_lines: {hasattr(self.chart, '_sl_lines')}")

            if hasattr(self.chart, '_zones'):
                debug_info.append(f"\nZones manager exists, count: {len(self.chart._zones.get_all())}")
            if hasattr(self.chart, '_entry_markers'):
                debug_info.append(f"Entry markers manager exists, count: {len(self.chart._entry_markers.get_all())}")

            QMessageBox.information(
                self,
                "Debug: No Markings Found",
                "\n".join(debug_info)
            )

        self._filter_markings()

    def _add_marking_row(self, category: str, marking: Any):
        """Add a marking to the table.

        Args:
            category: Marking category (Zone, Entry, Structure, Line)
            marking: Marking object
        """
        row = self.table.rowCount()
        self.table.insertRow(row)

        # Store marking reference
        marking_data = {"category": category, "marking": marking}
        self._all_markings.append(marking_data)

        # Type column
        type_item = QTableWidgetItem(self._get_type_display(category, marking))
        type_item.setData(Qt.ItemDataRole.UserRole, marking_data)
        self.table.setItem(row, 0, type_item)

        # Name column
        name = getattr(marking, 'label', None) or getattr(marking, 'text', '') or marking.id
        self.table.setItem(row, 1, QTableWidgetItem(name))

        # Price/Range column
        price_str = self._get_price_display(marking)
        self.table.setItem(row, 2, QTableWidgetItem(price_str))

        # Active column
        is_active = getattr(marking, 'is_active', True)
        active_item = QTableWidgetItem("✓" if is_active else "✗")
        active_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setItem(row, 3, active_item)

        # Lock column (clickable icon)
        is_locked = getattr(marking, 'is_locked', False)
        lock_item = QTableWidgetItem("🔒" if is_locked else "🔓")
        lock_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        lock_item.setToolTip("Click to toggle lock state")
        if is_locked:
            lock_item.setBackground(QColor("#ffebee"))  # Light red tint
        self.table.setItem(row, 4, lock_item)

    def _get_type_display(self, category: str, marking: Any) -> str:
        """Get display string for marking type.

        Args:
            category: Marking category
            marking: Marking object

        Returns:
            Type display string
        """
        if category == "Zone":
            return f"Zone: {marking.zone_type.value.title()}"
        elif category == "Entry":
            return f"Entry: {marking.direction.value.title()}"
        elif category == "Structure":
            return f"Structure: {marking.break_type.value}"
        elif category == "Line":
            label = getattr(marking, 'label', 'Line')
            return f"Line: {label}"
        return category

    def _get_price_display(self, marking: Any) -> str:
        """Get price/range display string.

        Args:
            marking: Marking object

        Returns:
            Price display string
        """
        if hasattr(marking, 'top_price') and hasattr(marking, 'bottom_price'):
            return f"{marking.bottom_price:.2f} - {marking.top_price:.2f}"
        elif hasattr(marking, 'price'):
            return f"{marking.price:.2f}"
        return "N/A"

    def _filter_markings(self):
        """Apply filters to visible rows."""
        type_filter = self.type_filter.currentText()
        locked_only = self.locked_only_cb.isChecked()

        for row in range(self.table.rowCount()):
            type_item = self.table.item(row, 0)
            marking_data = type_item.data(Qt.ItemDataRole.UserRole)
            marking = marking_data["marking"]

            # Type filter
            show = True
            if type_filter != "All Types":
                category = marking_data["category"]
                if type_filter == "Zones" and category != "Zone":
                    show = False
                elif type_filter == "Entry Markers" and category != "Entry":
                    show = False
                elif type_filter == "Structure Breaks" and category != "Structure":
                    show = False
                elif type_filter == "Lines" and category != "Line":
                    show = False

            # Lock filter
            if show and locked_only:
                is_locked = getattr(marking, 'is_locked', False)
                if not is_locked:
                    show = False

            self.table.setRowHidden(row, not show)

    def _on_cell_double_click(self, row: int, col: int):
        """Handle double-click on cell.

        Args:
            row: Row index
            col: Column index
        """
        if col == 4:  # Lock column
            self._toggle_lock_at_row(row)
        else:  # Any other column - edit
            self._edit_selected()

    def _toggle_lock(self, lock_state: bool):
        """Lock or unlock selected marking.

        Args:
            lock_state: True to lock, False to unlock
        """
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "No Selection", "Please select a marking first.")
            return

        type_item = self.table.item(row, 0)
        marking_data = type_item.data(Qt.ItemDataRole.UserRole)
        category = marking_data["category"]
        marking = marking_data["marking"]

        # Update lock state
        marking.is_locked = lock_state

        # Update via manager
        self._update_manager_lock_state(category, marking.id, lock_state)

        # Refresh display
        lock_item = self.table.item(row, 4)
        lock_item.setText("🔒" if lock_state else "🔓")
        if lock_state:
            lock_item.setBackground(QColor("#ffebee"))
        else:
            lock_item.setBackground(QColor("transparent"))

        logger.info(f"{category} '{marking.id}' {'locked' if lock_state else 'unlocked'}")

    def _toggle_lock_at_row(self, row: int):
        """Toggle lock at specific row.

        Args:
            row: Row index
        """
        type_item = self.table.item(row, 0)
        marking_data = type_item.data(Qt.ItemDataRole.UserRole)
        marking = marking_data["marking"]

        current_state = getattr(marking, 'is_locked', False)
        self.table.setCurrentCell(row, 0)
        self._toggle_lock(not current_state)

    def _update_manager_lock_state(self, category: str, marking_id: str, is_locked: bool):
        """Update lock state in appropriate manager.

        Args:
            category: Marking category
            marking_id: Marking ID
            is_locked: Lock state
        """
        if category == "Zone" and hasattr(self.chart, '_zones'):
            self.chart._zones.set_locked(marking_id, is_locked)
        elif category == "Entry" and hasattr(self.chart, '_entry_markers'):
            self.chart._entry_markers.set_locked(marking_id, is_locked)
        elif category == "Structure" and hasattr(self.chart, '_structure_markers'):
            self.chart._structure_markers.set_locked(marking_id, is_locked)
        elif category == "Line" and hasattr(self.chart, '_sl_lines'):
            self.chart._sl_lines.set_locked(marking_id, is_locked)

    def _edit_selected(self):
        """Edit selected marking."""
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "No Selection", "Please select a marking first.")
            return

        type_item = self.table.item(row, 0)
        marking_data = type_item.data(Qt.ItemDataRole.UserRole)
        marking = marking_data["marking"]

        if marking.is_locked:
            QMessageBox.warning(
                self, "Marking Locked",
                "This marking is locked. Unlock it first to edit."
            )
            return

        # Call appropriate edit method based on category
        category = marking_data["category"]
        if category == "Zone" and hasattr(self.chart, '_edit_zone'):
            self.chart._edit_zone(marking)
            self._load_markings()  # Refresh after edit

    def _delete_selected(self):
        """Delete selected marking."""
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "No Selection", "Please select a marking first.")
            return

        type_item = self.table.item(row, 0)
        marking_data = type_item.data(Qt.ItemDataRole.UserRole)
        marking = marking_data["marking"]
        category = marking_data["category"]

        # Confirm deletion
        marking_name = getattr(marking, 'label', None) or getattr(marking, 'text', '') or marking.id
        reply = QMessageBox.question(
            self, "Delete Marking",
            f"Are you sure you want to delete '{marking_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        # Call appropriate delete method based on category
        if category == "Zone" and hasattr(self.chart, '_zones'):
            self.chart._zones.remove(marking.id)
        elif category == "Entry" and hasattr(self.chart, '_entry_markers'):
            self.chart._entry_markers.remove(marking.id)
        elif category == "Structure" and hasattr(self.chart, '_structure_markers'):
            self.chart._structure_markers.remove(marking.id)
        elif category == "Line" and hasattr(self.chart, '_sl_lines'):
            self.chart._sl_lines.remove(marking.id)

        self._load_markings()  # Refresh after delete
        logger.info(f"{category} '{marking_name}' deleted from manager dialog")
