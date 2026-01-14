"""
Heatmap Service

Orchestrates the complete heatmap lifecycle: ingestion, storage, aggregation, and rendering.
Runs in background and coordinates all components.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Callable

from .heatmap_settings import HeatmapSettings
from .ingestion.binance_forceorder_ws import BinanceForceOrderClient, LiquidationEvent
from .ingestion.exchange_info import ExchangeInfoFetcher
from .storage.sqlite_store import LiquidationStore, QueryWindow
from .aggregation.grid_builder import GridBuilder, GridConfig
from .aggregation.normalization import NormalizationType
from .ui.bridge import HeatmapBridge


logger = logging.getLogger(__name__)


class HeatmapService:
    """
    Main service orchestrating the heatmap feature.

    Lifecycle:
    1. Start: Initialize all components, start WebSocket ingestion
    2. Enable: Load historical data and start rendering
    3. Update: Process live events and update grid
    4. Disable: Hide rendering but keep ingestion running
    5. Stop: Shutdown all components gracefully
    """

    def __init__(
        self,
        settings: HeatmapSettings,
        bridge: Optional[HeatmapBridge] = None,
        on_event: Optional[Callable[[LiquidationEvent], None]] = None,
    ):
        """
        Initialize heatmap service.

        Args:
            settings: Configuration settings
            bridge: UI bridge for rendering (optional if running headless)
            on_event: Callback for each liquidation event
        """
        self.settings = settings
        self.bridge = bridge
        self.on_event = on_event

        # Components
        self.ws_client: Optional[BinanceForceOrderClient] = None
        self.store: Optional[LiquidationStore] = None
        self.exchange_info: Optional[ExchangeInfoFetcher] = None
        self.grid_builder: Optional[GridBuilder] = None

        # State
        self._running = False
        self._rendering = False
        self._update_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None

        # Current grid state
        self._current_config: Optional[GridConfig] = None
        self._pending_events = asyncio.Queue()

    async def start(self) -> None:
        """
        Start the service (ingestion begins, rendering depends on settings.enabled).

        This starts the background ingestion immediately, even if heatmap is disabled.
        """
        if self._running:
            logger.warning("Service already running")
            return

        logger.info("Starting heatmap service...")

        # Initialize storage
        self.store = LiquidationStore(
            db_path=self.settings.db_path,
            batch_size=self.settings.batch_size,
            flush_interval=self.settings.flush_interval_ms / 1000,
            retention_days=self.settings.retention_days,
        )
        self.store.connect()
        await self.store.start()

        # Initialize exchange info fetcher
        self.exchange_info = ExchangeInfoFetcher()

        # Initialize grid builder
        self.grid_builder = GridBuilder(self.store)

        # Initialize WebSocket client
        self.ws_client = BinanceForceOrderClient(
            symbol=self.settings.symbol.lower(),
            on_event=self._on_liquidation_event,
        )
        await self.ws_client.start()

        # Start background tasks
        self._update_task = asyncio.create_task(self._update_loop())
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())

        self._running = True

        # If enabled, start rendering
        if self.settings.enabled:
            await self.enable()

        logger.info("Heatmap service started")

    async def stop(self) -> None:
        """Stop the service gracefully."""
        if not self._running:
            return

        logger.info("Stopping heatmap service...")

        self._running = False

        # Stop rendering
        if self._rendering:
            await self.disable()

        # Cancel background tasks
        if self._update_task:
            self._update_task.cancel()
            try:
                await self._update_task
            except asyncio.CancelledError:
                pass

        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        # Stop WebSocket
        if self.ws_client:
            await self.ws_client.stop()

        # Stop storage
        if self.store:
            await self.store.stop()
            self.store.disconnect()

        # Close exchange info fetcher
        if self.exchange_info and self.exchange_info._session:
            await self.exchange_info._session.close()

        logger.info("Heatmap service stopped")

    async def enable(self) -> None:
        """
        Enable heatmap rendering.

        Loads historical data and starts UI updates.
        """
        if not self._running:
            logger.error("Service not running, call start() first")
            return

        if self._rendering:
            logger.warning("Rendering already enabled")
            return

        logger.info("Enabling heatmap rendering...")

        if not self.bridge:
            logger.warning("No bridge configured, running in headless mode")
            self._rendering = True
            return

        # Initialize heatmap series in JavaScript
        await self.bridge.initialize_series(
            opacity=self.settings.opacity,
            palette=self.settings.palette.value,
        )

        # Load and render historical data
        await self._load_and_render_history()

        # Show heatmap
        await self.bridge.set_visible(True)

        self._rendering = True
        self.settings.enabled = True

        logger.info("Heatmap rendering enabled")

    async def disable(self) -> None:
        """
        Disable heatmap rendering.

        Hides UI but keeps background ingestion running.
        """
        if not self._rendering:
            return

        logger.info("Disabling heatmap rendering...")

        if self.bridge:
            await self.bridge.set_visible(False)
            await self.bridge.clear_heatmap()

        self._rendering = False
        self.settings.enabled = False

        logger.info("Heatmap rendering disabled")

    async def update_settings(self, new_settings: HeatmapSettings) -> None:
        """
        Update settings and apply changes.

        Args:
            new_settings: New settings to apply
        """
        old_enabled = self.settings.enabled
        old_window = self.settings.window
        old_opacity = self.settings.opacity
        old_palette = self.settings.palette

        self.settings = new_settings

        # Handle enable/disable
        if new_settings.enabled and not old_enabled:
            await self.enable()
        elif not new_settings.enabled and old_enabled:
            await self.disable()

        # Handle window change (reload data)
        if new_settings.window != old_window and self._rendering:
            await self._load_and_render_history()

        # Handle visual settings change
        if self._rendering and self.bridge:
            if new_settings.opacity != old_opacity or new_settings.palette != old_palette:
                await self.bridge.update_settings(
                    opacity=new_settings.opacity,
                    palette=new_settings.palette.value,
                )

        logger.info("Settings updated")

    def is_running(self) -> bool:
        """Check if service is running."""
        return self._running

    def is_rendering(self) -> bool:
        """Check if heatmap is rendering."""
        return self._rendering

    def get_stats(self) -> dict:
        """Get service statistics."""
        stats = {
            "running": self._running,
            "rendering": self._rendering,
            "ws_connected": self.ws_client.is_running() if self.ws_client else False,
        }

        if self.store:
            stats.update(self.store.get_stats())

        return stats

    async def _on_liquidation_event(self, event: LiquidationEvent) -> None:
        """Handle incoming liquidation event from WebSocket."""
        # Store in database
        await self.store.add_event(event)

        # Queue for grid update if rendering
        if self._rendering:
            await self._pending_events.put(event)

        # Call user callback if provided
        if self.on_event:
            if asyncio.iscoroutinefunction(self.on_event):
                await self.on_event(event)
            else:
                self.on_event(event)

    async def _load_and_render_history(self) -> None:
        """Load historical data and render initial grid."""
        if not self.bridge or not self.grid_builder:
            return

        # Get window parameters
        window = QueryWindow.from_duration(
            timedelta(hours=self.settings.window.to_hours()),
            symbol=self.settings.symbol,
        )

        # Get price range from database
        price_min, price_max = self.store.get_price_range(window)

        if price_min == 0 and price_max == 0:
            logger.warning("No historical data in window")
            return

        # Get tick size
        tick_size = await self.exchange_info.get_tick_size(self.settings.symbol)

        # Calculate grid config (assuming chart dimensions - should be passed from UI)
        # For now, use default window size
        window_width = 1060
        window_height = 550

        rows, cols = self.settings.get_grid_resolution(window_width, window_height)

        self._current_config = GridConfig(
            price_min=price_min,
            price_max=price_max,
            time_start_ms=window.start_ms,
            time_end_ms=window.end_ms,
            rows=rows,
            cols=cols,
            tick_size=tick_size,
        )

        # Build grid
        grid, cells = self.grid_builder.build_grid(
            config=self._current_config,
            window=window,
            normalization=NormalizationType(self.settings.normalization.value),
            weight_by="notional",
        )

        # Send to UI
        await self.bridge.set_heatmap_data(cells)

        logger.info(f"Loaded {len(cells)} historical cells")

    async def _update_loop(self) -> None:
        """Background task to process pending events and update grid."""
        while self._running:
            try:
                # Wait for events or timeout
                try:
                    events = []
                    # Batch events for rate limiting
                    timeout = self.settings.update_rate_limit_ms / 1000
                    deadline = asyncio.get_event_loop().time() + timeout

                    while asyncio.get_event_loop().time() < deadline:
                        remaining = deadline - asyncio.get_event_loop().time()
                        if remaining <= 0:
                            break

                        event = await asyncio.wait_for(
                            self._pending_events.get(),
                            timeout=remaining
                        )
                        events.append(event)

                except asyncio.TimeoutError:
                    pass

                if events and self._rendering and self.bridge and self._current_config:
                    # TODO: Update grid and send delta to UI
                    # For now, just log
                    logger.debug(f"Processing {len(events)} live events")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in update loop: {e}", exc_info=True)
                await asyncio.sleep(1)

    async def _cleanup_loop(self) -> None:
        """Background task to cleanup old data periodically."""
        while self._running:
            try:
                # Run cleanup every 6 hours
                await asyncio.sleep(6 * 3600)

                if self.store:
                    deleted = self.store.cleanup_old_events()
                    if deleted > 0:
                        logger.info(f"Cleanup deleted {deleted} old events")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}", exc_info=True)


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    async def _example():
        settings = HeatmapSettings(enabled=True, window="2h")
        service = HeatmapService(settings)

        await service.start()

        # Run for 1 hour
        await asyncio.sleep(3600)

        await service.stop()

    asyncio.run(_example())
