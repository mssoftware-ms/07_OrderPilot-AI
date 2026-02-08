"""Signals Table Mirror - Compact synchronized table for dock panels.

Provides a read-only mirror of the main signals table with reduced columns.
Automatically synchronizes with the master table via model signals.

Columns (11):
    Time, Status, P&L%, P&L USDT, Type, Strategy, Side, SL%, TR%, TRA%, Hebel

Usage:
    master_table = self.signals_table  # 25 columns
    mirror = SignalsTableMirror(master_table)
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional

from PyQt6.QtCore import Qt, QModelIndex, QTimer
from PyQt6.QtGui import QColor, QBrush
from PyQt6.QtWidgets import (
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QAbstractItemView,
    QWidget,
    QVBoxLayout,
    QLabel,
)

# Import design system for theme-consistent colors
from src.ui.design_system import THEMES, ColorPalette, theme_service

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class SignalsTableMirror(QTableWidget):
    """Compact mirror of the main signals table.

    Displays a subset of columns from the master table:
    - Time (0) - first column
    - Status (10)
    - P&L% (12)
    - P&L USDT (13)
    - Type (1)
    - Strategy (2)
    - Side (3)
    - SL% (6)
    - TR% (7)
    - TRA% (8)
    - Hebel (20)

    Features:
    - Automatic synchronization with master table
    - Read-only display
    - Compact column widths
    - Color-coded P&L values
    """

    # Column definitions: (display_name, master_column_index, width)
    # Master columns: 0=Time, 1=Type, 2=Strategy, 3=Side, 6=SL%, 7=TR%, 8=TRA%,
    #                 10=Status, 12=P&L%, 13=P&L USDT, 20=Hebel
    COLUMNS = [
        ("Time", 0, 70),
        ("Status", 10, 55),
        ("P&L%", 12, 55),
        ("P&L", 13, 65),
        ("Type", 1, 45),
        ("Strategy", 2, 85),
        ("Side", 3, 40),
        ("SL%", 6, 45),
        ("TR%", 7, 45),
        ("TRA%", 8, 45),
        ("Hebel", 20, 40),
    ]

    def __init__(self, master_table: Optional[QTableWidget] = None, parent: QWidget = None):
        """Initialize the signals table mirror.

        Args:
            master_table: The master signals table to mirror (can be set later)
            parent: Parent widget
        """
        super().__init__(parent)
        self._master_table = master_table
        self._sync_in_progress = False
        self._pending_full_sync = False
        self._dirty_rows: set[int] = set()

        # Throttle timer - coalesce rapid updates into single sync
        self._sync_timer = QTimer(self)
        self._sync_timer.setSingleShot(True)
        self._sync_timer.setInterval(50)  # 50ms debounce
        self._sync_timer.timeout.connect(self._process_pending_sync)

        # Get theme palette for consistent styling
        self._palette = self._get_theme_palette()

        self._setup_ui()

        # Subscribe to theme changes
        theme_service.subscribe(self._on_theme_changed)

        if master_table:
            self.set_master_table(master_table)

    def _get_theme_palette(self) -> ColorPalette:
        """Get the current theme palette from app settings or default."""
        try:
            from PyQt6.QtCore import QSettings
            settings = QSettings("OrderPilot", "TradingApp")
            theme_name = settings.value("theme/name", "Dark Orange")
            key = theme_name.lower().replace(" ", "_")
            return THEMES.get(key, THEMES["dark_orange"])
        except Exception:
            return THEMES["dark_orange"]

    def _setup_ui(self) -> None:
        """Setup table UI with columns and styling."""
        # Configure columns
        self.setColumnCount(len(self.COLUMNS))
        self.setHorizontalHeaderLabels([col[0] for col in self.COLUMNS])

        # Set column widths (user can resize)
        header = self.horizontalHeader()
        for i, (_, _, width) in enumerate(self.COLUMNS):
            self.setColumnWidth(i, width)
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.Interactive)

        # Last column can stretch but is also resizable
        header.setStretchLastSection(False)

        # Vertical header (row numbers) - hide for compactness
        self.verticalHeader().setVisible(False)
        self.verticalHeader().setDefaultSectionSize(22)

        # Selection behavior
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)

        # Read-only
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        # Styling using theme palette
        p = self._palette
        self.setStyleSheet(f"""
            QTableWidget {{
                background-color: {p.background_input};
                color: {p.text_primary};
                border: 1px solid {p.border_main};
                border-radius: 4px;
                gridline-color: {p.background_surface};
                font-size: 11px;
            }}
            QTableWidget::item {{
                padding: 2px 4px;
            }}
            QTableWidget::item:selected {{
                background-color: {p.selection_bg};
            }}
            QHeaderView::section {{
                background-color: {p.background_surface};
                color: {p.text_secondary};
                padding: 4px;
                border: none;
                border-right: 1px solid {p.border_main};
                font-size: 10px;
                font-weight: bold;
            }}
        """)

        # Minimum height
        self.setMinimumHeight(100)

    def set_master_table(self, master_table: QTableWidget) -> None:
        """Set or update the master table to mirror.

        Args:
            master_table: The master signals table (25 columns)
        """
        # Disconnect from old master
        if self._master_table:
            self._disconnect_master()

        self._master_table = master_table

        # Connect to new master
        if master_table:
            self._connect_master()
            self._full_sync()

    def _connect_master(self) -> None:
        """Connect to master table signals for synchronization."""
        if not self._master_table:
            return

        model = self._master_table.model()
        if model:
            model.dataChanged.connect(self._on_master_data_changed)
            model.rowsInserted.connect(self._on_master_rows_inserted)
            model.rowsRemoved.connect(self._on_master_rows_removed)
            model.modelReset.connect(self._on_master_reset)

        logger.debug("SignalsTableMirror connected to master table")

    def _disconnect_master(self) -> None:
        """Disconnect from master table signals."""
        if not self._master_table:
            return

        model = self._master_table.model()
        if model:
            try:
                model.dataChanged.disconnect(self._on_master_data_changed)
                model.rowsInserted.disconnect(self._on_master_rows_inserted)
                model.rowsRemoved.disconnect(self._on_master_rows_removed)
                model.modelReset.disconnect(self._on_master_reset)
            except (TypeError, RuntimeError):
                pass  # Already disconnected

    def _full_sync(self) -> None:
        """Perform full synchronization with master table."""
        if not self._master_table or self._sync_in_progress:
            return

        self._sync_in_progress = True
        try:
            # Clear existing rows
            self.setRowCount(0)

            # Copy all rows from master
            master_row_count = self._master_table.rowCount()
            self.setRowCount(master_row_count)

            for row in range(master_row_count):
                self._sync_row(row)

            logger.debug(f"SignalsTableMirror full sync: {master_row_count} rows")

        finally:
            self._sync_in_progress = False

    def _sync_row(self, row: int) -> None:
        """Synchronize a single row from master to mirror.

        Args:
            row: Row index to synchronize
        """
        if not self._master_table or row >= self._master_table.rowCount():
            return

        for mirror_col, (col_name, master_col, _) in enumerate(self.COLUMNS):
            master_item = self._master_table.item(row, master_col)

            if master_item:
                # Create mirror item
                cell_text = master_item.text()
                mirror_item = QTableWidgetItem(cell_text)

                # Copy styling
                mirror_item.setTextAlignment(master_item.textAlignment())

                # Copy foreground color (important for P&L)
                if master_item.foreground().color().isValid():
                    mirror_item.setForeground(master_item.foreground())

                # Copy background if set
                if master_item.background().color().isValid():
                    mirror_item.setBackground(master_item.background())

                # Set tooltip: Strategy column shows cell content, others copy from master
                if col_name == "Strategy" and cell_text:
                    mirror_item.setToolTip(cell_text)
                elif master_item.toolTip():
                    mirror_item.setToolTip(master_item.toolTip())

                self.setItem(row, mirror_col, mirror_item)
            else:
                # Empty item
                self.setItem(row, mirror_col, QTableWidgetItem(""))

    # ─────────────────────────────────────────────────────────────────────
    # Master Table Signal Handlers (Throttled)
    # ─────────────────────────────────────────────────────────────────────

    def _schedule_sync(self, rows: Optional[set[int]] = None, full: bool = False) -> None:
        """Schedule a throttled sync operation.

        Args:
            rows: Specific rows to sync (None = use existing dirty rows)
            full: If True, schedule a full sync instead
        """
        if full:
            self._pending_full_sync = True
            self._dirty_rows.clear()
        elif rows:
            if not self._pending_full_sync:
                self._dirty_rows.update(rows)

        # Start/restart debounce timer
        if not self._sync_timer.isActive():
            self._sync_timer.start()

    def _process_pending_sync(self) -> None:
        """Process pending sync operations (called by debounce timer)."""
        if self._sync_in_progress:
            # Reschedule if sync is already in progress
            self._sync_timer.start()
            return

        if self._pending_full_sync:
            self._pending_full_sync = False
            self._dirty_rows.clear()
            self._full_sync()
        elif self._dirty_rows:
            rows_to_sync = self._dirty_rows.copy()
            self._dirty_rows.clear()
            self._sync_specific_rows(rows_to_sync)

    def _sync_specific_rows(self, rows: set[int]) -> None:
        """Sync only specific rows (efficient partial update)."""
        if not self._master_table or self._sync_in_progress:
            return

        self._sync_in_progress = True
        try:
            master_row_count = self._master_table.rowCount()
            for row in rows:
                if 0 <= row < master_row_count and row < self.rowCount():
                    self._sync_row(row)
        finally:
            self._sync_in_progress = False

    def _on_master_data_changed(
        self,
        top_left: QModelIndex,
        bottom_right: QModelIndex,
        roles: list = None
    ) -> None:
        """Handle data changes in master table (throttled)."""
        if self._sync_in_progress:
            return

        # Check if any of our columns changed
        master_cols_we_care_about = {col[1] for col in self.COLUMNS}
        dirty = set()

        for row in range(top_left.row(), bottom_right.row() + 1):
            for col in range(top_left.column(), bottom_right.column() + 1):
                if col in master_cols_we_care_about:
                    dirty.add(row)
                    break  # Row marked dirty, move to next row

        if dirty:
            self._schedule_sync(rows=dirty)

    def _on_master_rows_inserted(
        self,
        parent: QModelIndex,
        first: int,
        last: int
    ) -> None:
        """Handle rows inserted in master table (schedule full sync)."""
        if self._sync_in_progress:
            return
        # Row inserts shift indices - need full sync
        self._schedule_sync(full=True)

    def _on_master_rows_removed(
        self,
        parent: QModelIndex,
        first: int,
        last: int
    ) -> None:
        """Handle rows removed from master table (schedule full sync)."""
        if self._sync_in_progress:
            return
        # Row removals shift indices - need full sync
        self._schedule_sync(full=True)

    def _on_master_reset(self) -> None:
        """Handle master table model reset."""
        self._schedule_sync(full=True)

    # ─────────────────────────────────────────────────────────────────────
    # Public API
    # ─────────────────────────────────────────────────────────────────────

    def refresh(self) -> None:
        """Force a full refresh from master table."""
        self._full_sync()

    def get_selected_master_row(self) -> Optional[int]:
        """Get the master table row index for the currently selected row.

        Returns:
            Master table row index, or None if no selection
        """
        selected = self.selectedItems()
        if selected:
            return selected[0].row()
        return None

    def _on_theme_changed(self, new_palette: ColorPalette) -> None:
        """Handle theme change - re-apply styling.

        Args:
            new_palette: The new ColorPalette to apply.
        """
        self._palette = new_palette
        self._setup_ui()  # Re-apply table styling with new palette
        logger.debug(f"SignalsTableMirror theme updated to: {new_palette.name}")

    def __del__(self):
        """Destructor - unsubscribe from theme service."""
        try:
            theme_service.unsubscribe(self._on_theme_changed)
        except Exception:
            pass  # May fail during shutdown


class SignalsTableMirrorWidget(QWidget):
    """Container widget for SignalsTableMirror with header."""

    def __init__(
        self,
        master_table: Optional[QTableWidget] = None,
        title: str = "Recent Signals",
        parent: QWidget = None
    ):
        """Initialize container widget.

        Args:
            master_table: Master signals table to mirror
            title: Header title
            parent: Parent widget
        """
        super().__init__(parent)

        # Get theme palette
        palette = self._get_theme_palette()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Header using theme colors
        header = QLabel(title)
        header.setStyleSheet(f"""
            color: {palette.text_secondary};
            font-size: 11px;
            font-weight: bold;
            padding: 2px 4px;
        """)
        layout.addWidget(header)

        # Table
        self.table = SignalsTableMirror(master_table, self)
        layout.addWidget(self.table)

    def _get_theme_palette(self) -> ColorPalette:
        """Get the current theme palette from app settings or default."""
        try:
            from PyQt6.QtCore import QSettings
            settings = QSettings("OrderPilot", "TradingApp")
            theme_name = settings.value("theme/name", "Dark Orange")
            key = theme_name.lower().replace(" ", "_")
            return THEMES.get(key, THEMES["dark_orange"])
        except Exception:
            return THEMES["dark_orange"]

    def set_master_table(self, master_table: QTableWidget) -> None:
        """Set the master table to mirror."""
        self.table.set_master_table(master_table)
