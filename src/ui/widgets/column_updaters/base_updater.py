"""Base class for column updaters."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from PyQt6.QtWidgets import QTableWidget


class BaseColumnUpdater(ABC):
    """Base class for table column updaters.

    Each updater handles a specific type of column (status, P&L, fees, etc.)
    following the Strategy Pattern for clean separation of concerns.
    """

    @abstractmethod
    def can_update(self, column_index: int) -> bool:
        """Check if this updater handles the given column index.

        Args:
            column_index: Table column index

        Returns:
            True if this updater handles this column
        """
        pass

    @abstractmethod
    def update(
        self,
        table: QTableWidget,
        row: int,
        column: int,
        signal: dict,
        context: dict[str, Any],
    ) -> None:
        """Update column value with formatting.

        Args:
            table: QTableWidget instance
            row: Row index
            column: Column index
            signal: Signal dictionary with data
            context: Additional context (current_price, leverage, fees, etc.)
        """
        pass
