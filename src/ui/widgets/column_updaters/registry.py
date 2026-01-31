"""Column updater registry for dispatching updates."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from PyQt6.QtWidgets import QTableWidget
    from .base_updater import BaseColumnUpdater


class ColumnUpdaterRegistry:
    """Registry for column updaters following Strategy Pattern.

    Dispatches column updates to the appropriate updater based on column index.
    """

    def __init__(self) -> None:
        """Initialize empty registry."""
        self._updaters: list[BaseColumnUpdater] = []

    def register(self, updater: BaseColumnUpdater) -> None:
        """Register a column updater.

        Args:
            updater: Column updater instance
        """
        self._updaters.append(updater)

    def update(
        self,
        table: QTableWidget,
        row: int,
        column: int,
        signal: dict,
        context: dict[str, Any],
    ) -> None:
        """Dispatch column update to appropriate updater.

        Args:
            table: QTableWidget instance
            row: Row index
            column: Column index
            signal: Signal dictionary
            context: Additional context
        """
        for updater in self._updaters:
            if updater.can_update(column):
                updater.update(table, row, column, signal, context)
                return

        # No updater found - column should be handled elsewhere
        pass
