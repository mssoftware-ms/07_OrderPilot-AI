"""Crosshair Synchronization for Multi-Chart setups.

This module handles synchronizing crosshairs across multiple chart windows,
allowing users to see the same time position across different timeframes.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Callable, Optional
from weakref import WeakValueDictionary

if TYPE_CHECKING:
    from PyQt6.QtCore import QObject

logger = logging.getLogger(__name__)


class CrosshairSyncManager:
    """Manages crosshair synchronization across multiple charts.

    When the user moves the crosshair in one chart, all other registered
    charts will update their crosshairs to the same timestamp.

    Attributes:
        enabled: Whether sync is currently active
        windows: Registered chart windows
    """

    def __init__(self, enabled: bool = True) -> None:
        """Initialize the sync manager.

        Args:
            enabled: Whether sync is enabled by default
        """
        self._enabled = enabled
        self._windows: WeakValueDictionary[str, Any] = WeakValueDictionary()
        self._callbacks: dict[str, Callable[[int, float], None]] = {}
        self._syncing = False  # Prevent recursion

    @property
    def enabled(self) -> bool:
        """Check if sync is enabled."""
        return self._enabled

    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable crosshair sync.

        Args:
            enabled: New enabled state
        """
        self._enabled = enabled
        logger.debug("Crosshair sync %s", "enabled" if enabled else "disabled")

    def register_window(
        self,
        window_id: str,
        window: "QObject",
        on_crosshair_update: Optional[Callable[[int, float], None]] = None,
    ) -> None:
        """Register a chart window for crosshair sync.

        Args:
            window_id: Unique identifier for this window
            window: The chart window object
            on_crosshair_update: Callback to update crosshair position
                                 Args: (timestamp, price)
        """
        self._windows[window_id] = window
        if on_crosshair_update:
            self._callbacks[window_id] = on_crosshair_update
        logger.debug("Registered window for crosshair sync: %s", window_id)

    def unregister_window(self, window_id: str) -> None:
        """Unregister a window from crosshair sync.

        Args:
            window_id: Window to unregister
        """
        self._windows.pop(window_id, None)
        self._callbacks.pop(window_id, None)
        logger.debug("Unregistered window from crosshair sync: %s", window_id)

    def on_crosshair_move(
        self,
        source_window_id: str,
        timestamp: int,
        price: float,
    ) -> None:
        """Handle crosshair movement from a source window.

        Propagates the position to all other registered windows.

        Args:
            source_window_id: Window where the crosshair moved
            timestamp: Unix timestamp of crosshair position
            price: Price level of crosshair
        """
        if not self._enabled or self._syncing:
            return

        self._syncing = True
        try:
            for window_id, callback in self._callbacks.items():
                if window_id != source_window_id:
                    try:
                        callback(timestamp, price)
                    except Exception as e:
                        logger.warning(
                            "Failed to sync crosshair to %s: %s",
                            window_id, e
                        )
        finally:
            self._syncing = False

    def broadcast_position(self, timestamp: int, price: float) -> None:
        """Broadcast a crosshair position to all windows.

        Use this when you want to sync all charts to a specific position.

        Args:
            timestamp: Unix timestamp
            price: Price level
        """
        if not self._enabled:
            return

        self._syncing = True
        try:
            for window_id, callback in self._callbacks.items():
                try:
                    callback(timestamp, price)
                except Exception as e:
                    logger.warning(
                        "Failed to broadcast crosshair to %s: %s",
                        window_id, e
                    )
        finally:
            self._syncing = False

    def get_registered_count(self) -> int:
        """Get the number of registered windows.

        Returns:
            Number of windows registered for sync
        """
        return len(self._windows)

    def clear(self) -> None:
        """Clear all registered windows."""
        self._windows.clear()
        self._callbacks.clear()
        logger.debug("Cleared all crosshair sync registrations")


# JavaScript injection for crosshair sync
# This code hooks into the chart's crosshair events
CROSSHAIR_SYNC_JS = """
// Crosshair sync setup
(function() {
    if (!window.chart || !window.chartAPI) {
        console.warn('Chart not ready for crosshair sync');
        return;
    }

    // Subscribe to crosshair move events
    window.chart.subscribeCrosshairMove(param => {
        if (!param || !param.time || !param.point) return;

        // Get price from the main series
        const seriesData = param.seriesData;
        if (!seriesData) return;

        let price = null;
        for (const [series, data] of seriesData) {
            if (data && typeof data.close !== 'undefined') {
                price = data.close;
                break;
            } else if (data && typeof data.value !== 'undefined') {
                price = data.value;
                break;
            }
        }

        if (price === null) return;

        // Notify Python bridge
        if (window.pyBridge && window.pyBridge.onCrosshairMove) {
            window.pyBridge.onCrosshairMove(param.time, price);
        }
    });

    // API to set crosshair position from Python
    window.chartAPI.setCrosshairPosition = function(timestamp, price) {
        if (!window.chart) return false;
        try {
            // Use the chart's setCrosshairPosition method (LWC v5)
            window.chart.setCrosshairPosition(
                price,
                timestamp,
                window.mainSeries
            );
            return true;
        } catch (e) {
            console.warn('setCrosshairPosition failed:', e);
            return false;
        }
    };

    console.log('Crosshair sync initialized');
})();
"""


def get_crosshair_sync_javascript() -> str:
    """Get the JavaScript code for crosshair sync.

    Returns:
        JavaScript code as string
    """
    return CROSSHAIR_SYNC_JS
