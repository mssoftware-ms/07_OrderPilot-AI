"""Heatmap Mixin for Chart Widget Integration.

Integrates the Binance Liquidation Heatmap feature into the chart widget.
Handles initialization, lifecycle management, and coordination with the
background HeatmapService.
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Optional

from PyQt6.QtCore import QSettings, pyqtSignal, QTimer

if TYPE_CHECKING:
    from Heatmap import HeatmapService, HeatmapSettings
    from Heatmap.ui.bridge import HeatmapBridge

logger = logging.getLogger(__name__)


class HeatmapMixin:
    """Mixin for Heatmap integration into chart widget.

    This mixin provides:
    - Heatmap service lifecycle management
    - Settings synchronization
    - JavaScript bridge integration
    - Resize event handling for grid rebuilds

    Requirements:
    - Parent must have QWebEngineView as self.web_view
    - Parent must have access to QSettings
    """

    # Signal emitted when heatmap is enabled/disabled
    heatmap_toggled = pyqtSignal(bool)

    def __init__(self, *args, **kwargs):
        """Initialize heatmap mixin."""
        super().__init__(*args, **kwargs)

        self.heatmap_service: Optional[HeatmapService] = None
        self.heatmap_bridge: Optional[HeatmapBridge] = None
        self._heatmap_initialized = False
        self._heatmap_resize_timer: Optional[QTimer] = None

        # Load settings
        self._load_heatmap_settings()

    def _load_heatmap_settings(self) -> None:
        """Load heatmap settings from QSettings."""
        try:
            from Heatmap.heatmap_settings import (
                HeatmapSettings,
                WindowDuration,
                ColorPalette,
                NormalizationMode,
                DecayMode,
                ResolutionMode
            )

            settings = QSettings("OrderPilot", "TradingApp")

            # Map decay_minutes to DecayMode
            decay_minutes = settings.value("heatmap/decay_minutes", 0, type=int)
            decay = DecayMode.OFF
            if decay_minutes >= 360:  # 6h
                decay = DecayMode.SIX_HOURS
            elif decay_minutes >= 60:
                decay = DecayMode.SIXTY_MIN
            elif decay_minutes >= 20:
                decay = DecayMode.TWENTY_MIN

            # Map auto_resolution to ResolutionMode
            auto_res = settings.value("heatmap/auto_resolution", True, type=bool)
            resolution_mode = ResolutionMode.AUTO if auto_res else ResolutionMode.MANUAL

            # Map window string to Enum (safely)
            window_str = settings.value("heatmap/window", "2h", type=str)
            try:
                window = WindowDuration(window_str)
            except ValueError:
                window = WindowDuration.TWO_HOURS

            # Map palette string to Enum
            palette_str = settings.value("heatmap/palette", "hot", type=str)
            try:
                palette = ColorPalette(palette_str)
            except ValueError:
                palette = ColorPalette.HOT

            # Map normalization string to Enum
            norm_str = settings.value("heatmap/normalization", "sqrt", type=str)
            try:
                normalization = NormalizationMode(norm_str)
            except ValueError:
                normalization = NormalizationMode.SQRT

            self._heatmap_settings = HeatmapSettings(
                enabled=settings.value("heatmap/enabled", False, type=bool),
                window=window,
                opacity=settings.value("heatmap/opacity", 0.5, type=float),
                palette=palette,
                normalization=normalization,
                decay=decay,
                resolution_mode=resolution_mode,
                manual_rows=settings.value("heatmap/rows", 280, type=int),
                manual_cols=settings.value("heatmap/cols", 1200, type=int),
            )

            logger.info(f"Loaded heatmap settings: enabled={self._heatmap_settings.enabled}, "
                       f"window={self._heatmap_settings.window}")
        except Exception as e:
            logger.error(f"Failed to load heatmap settings: {e}", exc_info=True)
            # Create default settings
            from Heatmap import HeatmapSettings
            self._heatmap_settings = HeatmapSettings()

    def _save_heatmap_settings(self) -> None:
        """Save heatmap settings to QSettings."""
        if not hasattr(self, '_heatmap_settings'):
            return

        try:
            from Heatmap.heatmap_settings import ResolutionMode, DecayMode

            settings = QSettings("OrderPilot", "TradingApp")
            settings.setValue("heatmap/enabled", self._heatmap_settings.enabled)
            settings.setValue("heatmap/window", self._heatmap_settings.window.value)
            settings.setValue("heatmap/opacity", self._heatmap_settings.opacity)
            settings.setValue("heatmap/palette", self._heatmap_settings.palette.value)
            settings.setValue("heatmap/normalization", self._heatmap_settings.normalization.value)

            # Convert decay back to minutes (approx)
            decay_val = 0
            if self._heatmap_settings.decay == DecayMode.SIX_HOURS:
                decay_val = 360
            elif self._heatmap_settings.decay == DecayMode.SIXTY_MIN:
                decay_val = 60
            elif self._heatmap_settings.decay == DecayMode.TWENTY_MIN:
                decay_val = 20
            settings.setValue("heatmap/decay_minutes", decay_val)

            settings.setValue("heatmap/auto_resolution", self._heatmap_settings.resolution_mode == ResolutionMode.AUTO)
            settings.setValue("heatmap/rows", self._heatmap_settings.manual_rows)
            settings.setValue("heatmap/cols", self._heatmap_settings.manual_cols)
            settings.sync()

            logger.debug("Saved heatmap settings to QSettings")
        except Exception as e:
            logger.error(f"Failed to save heatmap settings: {e}", exc_info=True)

    def init_heatmap(self) -> None:
        """Initialize heatmap service and bridge.

        Should be called after web_view is fully loaded.
        """
        if self._heatmap_initialized:
            logger.warning("Heatmap already initialized")
            return

        try:
            from Heatmap import HeatmapService
            from Heatmap.ui.bridge import HeatmapBridge

            # Verify web_view exists
            if not hasattr(self, 'web_view'):
                logger.error("Chart widget must have web_view attribute for heatmap")
                return

            # Create bridge
            self.heatmap_bridge = HeatmapBridge(self.web_view)
            logger.info("Heatmap bridge created")

            # Create service
            self.heatmap_service = HeatmapService(
                settings=self._heatmap_settings,
                bridge=self.heatmap_bridge
            )

            # Start background service (ingestion always runs)
            asyncio.create_task(self._start_heatmap_service())

            self._heatmap_initialized = True
            logger.info("Heatmap initialization complete")

        except Exception as e:
            logger.error(f"Failed to initialize heatmap: {e}", exc_info=True)

    async def _start_heatmap_service(self) -> None:
        """Start heatmap service (async)."""
        try:
            if self.heatmap_service:
                await self.heatmap_service.start()
                logger.info("Heatmap service started")

                # If enabled in settings, activate rendering
                if self._heatmap_settings.enabled:
                    await self.enable_heatmap()
        except Exception as e:
            logger.error(f"Failed to start heatmap service: {e}", exc_info=True)

    async def enable_heatmap(self) -> None:
        """Enable heatmap rendering.

        Loads historical data and starts live updates.
        """
        if not self._heatmap_initialized or not self.heatmap_service:
            logger.warning("Heatmap not initialized, cannot enable")
            return

        try:
            # Get current chart window (high/low)
            window_data = await self._get_chart_window()

            # Enable service
            await self.heatmap_service.enable(
                high=window_data.get('high'),
                low=window_data.get('low')
            )

            self._heatmap_settings.enabled = True
            self._save_heatmap_settings()
            self.heatmap_toggled.emit(True)

            logger.info("Heatmap enabled")

        except Exception as e:
            logger.error(f"Failed to enable heatmap: {e}", exc_info=True)

    async def disable_heatmap(self) -> None:
        """Disable heatmap rendering.

        Background ingestion continues.
        """
        if not self._heatmap_initialized or not self.heatmap_service:
            logger.warning("Heatmap not initialized, cannot disable")
            return

        try:
            await self.heatmap_service.disable()

            self._heatmap_settings.enabled = False
            self._save_heatmap_settings()
            self.heatmap_toggled.emit(False)

            logger.info("Heatmap disabled")

        except Exception as e:
            logger.error(f"Failed to disable heatmap: {e}", exc_info=True)

    async def update_heatmap_settings(self, new_settings: HeatmapSettings) -> None:
        """Update heatmap settings and refresh display.

        Args:
            new_settings: New HeatmapSettings instance
        """
        if not self._heatmap_initialized or not self.heatmap_service:
            logger.warning("Heatmap not initialized, cannot update settings")
            return

        try:
            old_enabled = self._heatmap_settings.enabled
            self._heatmap_settings = new_settings
            self._save_heatmap_settings()

            # Update service
            await self.heatmap_service.update_settings(new_settings)

            # Handle enable/disable state change
            if new_settings.enabled != old_enabled:
                if new_settings.enabled:
                    await self.enable_heatmap()
                else:
                    await self.disable_heatmap()

            logger.info(f"Heatmap settings updated: {new_settings}")

        except Exception as e:
            logger.error(f"Failed to update heatmap settings: {e}", exc_info=True)

    async def _get_chart_window(self) -> dict:
        """Get current chart window (high/low prices).

        Returns:
            dict: {'high': float, 'low': float}
        """
        # This is a placeholder - actual implementation depends on your chart
        # You may need to call JavaScript to get visible price range
        # Example: result = await self.web_view.page().runJavaScript("getVisiblePriceRange()")

        try:
            if hasattr(self, 'web_view') and self.web_view:
                # Try to get visible range from chart
                # This assumes you have a JavaScript function getVisiblePriceRange()
                result = {}
                # TODO: Implement actual JavaScript call
                # For now, return empty dict (service will use full data range)
                return result
        except Exception as e:
            logger.error(f"Failed to get chart window: {e}", exc_info=True)

        return {}

    def resizeEvent(self, event):
        """Handle resize events for heatmap grid rebuild.

        Debounced to avoid excessive rebuilds during drag resize.
        """
        # Call parent resize handler
        if hasattr(super(), 'resizeEvent'):
            super().resizeEvent(event)

        # Debounce heatmap rebuild
        if self._heatmap_initialized and self._heatmap_settings.enabled:
            if not self._heatmap_resize_timer:
                self._heatmap_resize_timer = QTimer()
                self._heatmap_resize_timer.setSingleShot(True)
                self._heatmap_resize_timer.timeout.connect(self._on_heatmap_resize_complete)

            # Restart timer (300ms debounce)
            self._heatmap_resize_timer.start(300)

    def _on_heatmap_resize_complete(self) -> None:
        """Called after resize debounce completes."""
        asyncio.create_task(self._rebuild_heatmap_grid())

    async def _rebuild_heatmap_grid(self) -> None:
        """Rebuild heatmap grid after resize."""
        if not self._heatmap_initialized or not self.heatmap_service:
            return

        try:
            # Get new window dimensions
            window_data = await self._get_chart_window()

            # Rebuild grid with new dimensions
            await self.heatmap_service.rebuild_grid(
                high=window_data.get('high'),
                low=window_data.get('low'),
                width=self.width(),
                height=self.height()
            )

            logger.debug("Heatmap grid rebuilt after resize")

        except Exception as e:
            logger.error(f"Failed to rebuild heatmap grid: {e}", exc_info=True)

    def cleanup_heatmap(self) -> None:
        """Cleanup heatmap resources.

        Should be called on widget destruction.
        """
        if self.heatmap_service:
            try:
                asyncio.create_task(self.heatmap_service.stop())
                logger.info("Heatmap service stopped")
            except Exception as e:
                logger.error(f"Error stopping heatmap service: {e}", exc_info=True)

        self._heatmap_initialized = False
        self.heatmap_service = None
        self.heatmap_bridge = None

    def get_heatmap_stats(self) -> Optional[dict]:
        """Get heatmap statistics.

        Returns:
            dict: Statistics or None if not initialized
        """
        if self.heatmap_service:
            return self.heatmap_service.get_stats()
        return None
