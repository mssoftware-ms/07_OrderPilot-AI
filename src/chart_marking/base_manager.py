"""Base Manager for Chart Marking Elements.

Provides common CRUD operations, lock management, and state persistence
for all chart element managers (markers, zones, lines).
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Callable, Generic, Optional, TypeVar

logger = logging.getLogger(__name__)

# Generic type variable for managed items
T = TypeVar('T')


class BaseChartElementManager(ABC, Generic[T]):
    """Base class for all chart element managers.

    This class provides common infrastructure for managing chart elements:
    - CRUD operations (create, read, update, delete)
    - Lock management (prevent accidental deletion)
    - State persistence (save/restore)
    - Update callbacks (trigger chart redraw)

    Subclasses only need to implement item-specific business logic.

    Type Parameters:
        T: The item type being managed (EntryMarker, Zone, etc.)

    Example:
        class EntryMarkerManager(BaseChartElementManager[EntryMarker]):
            def _get_item_class(self) -> type[EntryMarker]:
                return EntryMarker

            def _get_item_type_name(self) -> str:
                return "entry marker"
    """

    def __init__(self, on_update: Optional[Callable[[], None]] = None):
        """Initialize the manager.

        Args:
            on_update: Callback to invoke when items change (triggers chart update)
        """
        self._items: dict[str, T] = {}
        self._on_update = on_update
        self._id_counter = 0

    def _generate_id(self, prefix: str = "item") -> str:
        """Generate a unique item ID.

        The ID format is: {prefix}_{timestamp_ms}_{counter}
        This ensures IDs are unique, sortable by creation time, and human-readable.

        Args:
            prefix: ID prefix (e.g., "long", "bos", "support")

        Returns:
            Unique ID string
        """
        self._id_counter += 1
        return f"{prefix}_{int(datetime.now().timestamp() * 1000)}_{self._id_counter}"

    def _trigger_update(self) -> None:
        """Trigger chart update callback if registered."""
        if self._on_update:
            self._on_update()

    # Abstract methods - subclasses must implement

    @abstractmethod
    def _get_item_class(self) -> type[T]:
        """Return the item class for deserialization.

        This is used by restore_state() to reconstruct items from dicts.

        Returns:
            Item class (e.g., EntryMarker, Zone, StopLossLine)
        """
        pass

    @abstractmethod
    def _get_item_type_name(self) -> str:
        """Return item type name for logging.

        Returns:
            Human-readable type name (e.g., "entry marker", "zone", "line")
        """
        pass

    # CRUD Operations

    def remove(self, item_id: str) -> bool:
        """Remove an item by ID.

        Args:
            item_id: ID of item to remove

        Returns:
            True if removed, False if not found
        """
        if item_id in self._items:
            del self._items[item_id]
            logger.debug(f"Removed {self._get_item_type_name()}: {item_id}")
            self._trigger_update()
            return True
        return False

    def clear(self) -> None:
        """Remove all items."""
        count = len(self._items)
        self._items.clear()
        logger.debug(f"Cleared {count} {self._get_item_type_name()}s")
        self._trigger_update()

    # Lock Management

    def set_locked(self, item_id: str, is_locked: bool) -> bool:
        """Set item lock status.

        Locked items cannot be modified or deleted in the UI.

        Args:
            item_id: Item ID
            is_locked: Whether item is locked

        Returns:
            True if updated, False if not found
        """
        item = self._items.get(item_id)
        if not item:
            return False

        item.is_locked = is_locked
        logger.debug(f"{self._get_item_type_name()} {item_id} locked={is_locked}")
        return True

    def toggle_locked(self, item_id: str) -> bool | None:
        """Toggle item lock status.

        Args:
            item_id: Item ID

        Returns:
            New lock state, or None if item not found
        """
        item = self._items.get(item_id)
        if not item:
            return None

        item.is_locked = not item.is_locked
        logger.debug(
            f"{self._get_item_type_name()} {item_id} "
            f"toggled to {'locked' if item.is_locked else 'unlocked'}"
        )
        return item.is_locked

    # Getters

    def get(self, item_id: str) -> Optional[T]:
        """Get an item by ID.

        Args:
            item_id: Item ID

        Returns:
            Item instance, or None if not found
        """
        return self._items.get(item_id)

    def get_all(self) -> list[T]:
        """Get all items.

        Returns:
            List of all items (unordered)
        """
        return list(self._items.values())

    # State Persistence

    def to_state(self) -> list[dict[str, Any]]:
        """Export state for persistence.

        Serializes all items to dictionaries for saving to disk/database.

        Returns:
            List of item dictionaries
        """
        return [item.to_dict() for item in self._items.values()]

    def restore_state(self, state: list[dict[str, Any]]) -> None:
        """Restore state from persistence.

        Deserializes items from dictionaries and rebuilds internal state.
        Invalid items are logged and skipped.

        Args:
            state: List of item dictionaries (from to_state())
        """
        self._items.clear()
        item_class = self._get_item_class()

        for data in state:
            try:
                item = item_class.from_dict(data)
                self._items[item.id] = item
            except Exception as e:
                logger.warning(f"Failed to restore {self._get_item_type_name()}: {e}")

        logger.debug(f"Restored {len(self._items)} {self._get_item_type_name()}s")
        self._trigger_update()

    # Magic Methods

    def __len__(self) -> int:
        """Return number of items."""
        return len(self._items)

    def __contains__(self, item_id: str) -> bool:
        """Check if item exists.

        Args:
            item_id: Item ID to check

        Returns:
            True if item exists
        """
        return item_id in self._items
