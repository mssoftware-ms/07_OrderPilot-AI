"""UI Widget Setup Helpers for OrderPilot-AI.

Provides common functionality and helpers for Qt widgets to reduce code duplication.
"""

import logging
from typing import Any

from PyQt6.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QTableWidget,
    QHeaderView,
    QWidget,
)

logger = logging.getLogger(__name__)


# ==================== Table Widget Helpers ====================

def create_table_widget(
    columns: list[str],
    stretch_columns: bool = True,
    selection_behavior: QTableWidget.SelectionBehavior = QTableWidget.SelectionBehavior.SelectRows,
    selection_mode: QTableWidget.SelectionMode = QTableWidget.SelectionMode.SingleSelection,
    editable: bool = False,
    alternating_colors: bool = True,
    sortable: bool = False
) -> QTableWidget:
    """Create a configured QTableWidget with common settings.

    Args:
        columns: List of column headers
        stretch_columns: If True, columns stretch to fill width
        selection_behavior: Row or cell selection
        selection_mode: Single, multi, or no selection
        editable: Allow editing cells
        alternating_colors: Use alternating row colors
        sortable: Enable column sorting

    Returns:
        Configured QTableWidget
    """
    table = QTableWidget()
    table.setColumnCount(len(columns))
    table.setHorizontalHeaderLabels(columns)

    # Configure header
    header = table.horizontalHeader()
    if stretch_columns:
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    else:
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)

    # Configure table behavior
    table.setSelectionBehavior(selection_behavior)
    table.setSelectionMode(selection_mode)

    if not editable:
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

    table.setAlternatingRowColors(alternating_colors)

    if sortable:
        table.setSortingEnabled(True)

    return table


def setup_table_row(
    table: QTableWidget,
    row: int,
    data: dict[str, Any],
    column_keys: list[str],
    format_funcs: dict[str, Any] | None = None
) -> None:
    """Set up a table row with data.

    Args:
        table: QTableWidget to update
        row: Row index
        data: Dictionary with data for the row
        column_keys: List of keys matching column order
        format_funcs: Optional dict mapping column keys to format functions
    """
    from PyQt6.QtWidgets import QTableWidgetItem

    format_funcs = format_funcs or {}

    for col, key in enumerate(column_keys):
        value = data.get(key, "--")

        # Apply format function if provided
        if key in format_funcs:
            value = format_funcs[key](value)
        else:
            value = str(value)

        table.setItem(row, col, QTableWidgetItem(value))


# ==================== Layout Helpers ====================

def create_vbox_layout(parent: QWidget | None = None, spacing: int = 5, margins: tuple[int, int, int, int] | None = None) -> QVBoxLayout:
    """Create a QVBoxLayout with common settings.

    Args:
        parent: Parent widget (can be None)
        spacing: Spacing between widgets
        margins: Tuple of (left, top, right, bottom) margins. None for default.

    Returns:
        Configured QVBoxLayout
    """
    layout = QVBoxLayout(parent)
    layout.setSpacing(spacing)

    if margins:
        layout.setContentsMargins(*margins)

    return layout


def create_hbox_layout(parent: QWidget | None = None, spacing: int = 5, margins: tuple[int, int, int, int] | None = None) -> QHBoxLayout:
    """Create a QHBoxLayout with common settings.

    Args:
        parent: Parent widget (can be None)
        spacing: Spacing between widgets
        margins: Tuple of (left, top, right, bottom) margins. None for default.

    Returns:
        Configured QHBoxLayout
    """
    layout = QHBoxLayout(parent)
    layout.setSpacing(spacing)

    if margins:
        layout.setContentsMargins(*margins)

    return layout


def create_grid_layout(parent: QWidget | None = None, spacing: int = 5, margins: tuple[int, int, int, int] | None = None) -> QGridLayout:
    """Create a QGridLayout with common settings.

    Args:
        parent: Parent widget (can be None)
        spacing: Spacing between widgets
        margins: Tuple of (left, top, right, bottom) margins. None for default.

    Returns:
        Configured QGridLayout
    """
    layout = QGridLayout(parent)
    layout.setSpacing(spacing)

    if margins:
        layout.setContentsMargins(*margins)

    return layout


# ==================== Event Bus Helpers ====================

class EventBusWidget(QWidget):
    """Base widget with event bus integration.

    Provides automatic event subscription/unsubscription lifecycle management.
    Subclasses should implement _setup_event_subscriptions() to register handlers.
    """

    def __init__(self, parent: QWidget | None = None):
        """Initialize event bus widget.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self._event_subscriptions: list[tuple[Any, Any]] = []

    def _subscribe_event(self, event_type: Any, handler: Any) -> None:
        """Subscribe to an event and track for cleanup.

        Args:
            event_type: Event type to subscribe to
            handler: Handler function
        """
        from src.common.event_bus import event_bus

        event_bus.subscribe(event_type, handler)
        self._event_subscriptions.append((event_type, handler))

    def _setup_event_subscriptions(self) -> None:
        """Set up event subscriptions.

        Subclasses should override this method to subscribe to events
        using _subscribe_event().
        """
        pass

    def closeEvent(self, event):
        """Clean up event subscriptions on close."""
        from src.common.event_bus import event_bus

        for event_type, handler in self._event_subscriptions:
            try:
                event_bus.unsubscribe(event_type, handler)
            except Exception as e:
                logger.debug(f"Failed to unsubscribe from {event_type}: {e}")

        self._event_subscriptions.clear()
        super().closeEvent(event)


# ==================== Common Widget Template ====================

class BaseTableWidget(EventBusWidget):
    """Base class for table-based widgets with common setup pattern.

    Provides template method pattern for widget initialization:
    1. Create UI layout
    2. Create and configure table
    3. Add table to layout
    4. Set up event handlers

    Subclasses should implement:
    - _get_table_columns() - return list of column headers
    - _configure_table() - optional additional table configuration
    - _setup_event_subscriptions() - subscribe to events
    """

    def __init__(self, parent: QWidget | None = None):
        """Initialize base table widget.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.table: QTableWidget | None = None
        self._init_ui()
        self._setup_event_subscriptions()

    def _init_ui(self) -> None:
        """Initialize UI using template method pattern."""
        # Create main layout
        self.layout = create_vbox_layout(self)

        # Create and configure table
        columns = self._get_table_columns()
        self.table = create_table_widget(
            columns=columns,
            **self._get_table_config()
        )

        # Allow subclasses to configure table further
        self._configure_table()

        # Add table to layout
        self.layout.addWidget(self.table)

        # Allow subclasses to add additional widgets
        self._add_additional_widgets()

    def _get_table_columns(self) -> list[str]:
        """Get table column headers.

        Subclasses must implement this method.

        Returns:
            List of column header labels
        """
        raise NotImplementedError("Subclasses must implement _get_table_columns()")

    def _get_table_config(self) -> dict[str, Any]:
        """Get table configuration parameters.

        Subclasses can override to customize table behavior.

        Returns:
            Dict of parameters for create_table_widget()
        """
        return {
            "stretch_columns": True,
            "selection_behavior": QTableWidget.SelectionBehavior.SelectRows,
            "selection_mode": QTableWidget.SelectionMode.SingleSelection,
            "editable": False,
            "alternating_colors": True,
            "sortable": False
        }

    def _configure_table(self) -> None:
        """Configure table after creation.

        Optional hook for subclasses to apply additional configuration.
        """
        pass

    def _add_additional_widgets(self) -> None:
        """Add additional widgets to layout.

        Optional hook for subclasses to add widgets before/after table.
        """
        pass

    def update_row(self, row: int, data: dict[str, Any]) -> None:
        """Update a table row with data.

        Args:
            row: Row index
            data: Dictionary with column data
        """
        if not self.table:
            return

        column_keys = self._get_column_keys()
        format_funcs = self._get_format_functions()

        setup_table_row(
            self.table,
            row,
            data,
            column_keys,
            format_funcs
        )

    def _get_column_keys(self) -> list[str]:
        """Get keys for mapping data to columns.

        Subclasses should implement this to define how data dict keys
        map to table columns.

        Returns:
            List of keys matching column order
        """
        raise NotImplementedError("Subclasses must implement _get_column_keys()")

    def _get_format_functions(self) -> dict[str, Any]:
        """Get format functions for columns.

        Subclasses can override to provide custom formatting.

        Returns:
            Dict mapping column keys to format functions
        """
        return {}
