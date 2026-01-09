"""Level Zones Mixin for Chart Widgets (Refactored).

Refactored from 722 LOC monolith using composition pattern.

Main Mixin (Module 5/5).

Delegates to 4 specialized helper modules:
- LevelZonesToolbar: Toolbar and menu building
- LevelZonesRendering: Level detection and zone rendering
- LevelZonesInteractions: Click detection and context menu
- level_zones_colors: Color definitions (imported)

Provides:
- LevelZonesMixin: Main mixin class with delegation
- Re-exports helper classes for backward compatibility
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, List, Optional

from src.ui.widgets.chart_mixins.level_zones_toolbar import LevelZonesToolbar
from src.ui.widgets.chart_mixins.level_zones_rendering import LevelZonesRendering
from src.ui.widgets.chart_mixins.level_zones_interactions import LevelZonesInteractions
from src.ui.widgets.chart_mixins.level_zones_colors import LEVEL_ZONE_COLORS

if TYPE_CHECKING:
    import pandas as pd
    from src.core.trading_bot.level_engine import Level, LevelsResult

logger = logging.getLogger(__name__)


class LevelZonesMixin:
    """
    Mixin für Level-Zonen-Rendering in Chart-Widgets.

    Fügt folgende Funktionalität hinzu:
    - Konvertiert LevelEngine-Levels zu Chart-Zonen
    - Toggle für Level-Anzeige
    - Farblegende
    - Auto-Update bei Datenänderung

    Usage:
        class MyChartWidget(LevelZonesMixin, QWidget):
            def __init__(self):
                super().__init__()
                self._setup_level_zones()
    """

    _level_zones_visible: bool = True
    _level_zones_ids: List[str] = []
    _levels_result: Optional["LevelsResult"] = None

    def _setup_level_zones(self) -> None:
        """
        Setup level zones functionality.

        Should be called after toolbar and zones system are initialized.
        """
        self._level_zones_ids = []
        self._level_zones_visible = True
        self._levels_result = None

        # Instantiate helper modules (composition pattern)
        self._toolbar = LevelZonesToolbar(parent=self)
        self._rendering = LevelZonesRendering(parent=self)
        self._interactions = LevelZonesInteractions(parent=self)

        logger.debug("Level zones mixin initialized")

    def _add_levels_toggle_to_toolbar(self, toolbar) -> None:
        """
        Add levels toggle button to toolbar.

        Delegates to LevelZonesToolbar.add_levels_toggle_to_toolbar().

        Args:
            toolbar: QToolBar to add button to
        """
        self._toolbar.add_levels_toggle_to_toolbar(toolbar)

    def detect_and_render_levels(
        self,
        df: "pd.DataFrame",
        symbol: str = "UNKNOWN",
        timeframe: str = "5m",
        current_price: Optional[float] = None,
    ) -> None:
        """
        Detect levels from DataFrame and render as zones.

        Delegates to LevelZonesRendering.detect_and_render_levels().

        Args:
            df: DataFrame with OHLCV data
            symbol: Trading symbol
            timeframe: Timeframe
            current_price: Current price for classification
        """
        self._rendering.detect_and_render_levels(df, symbol, timeframe, current_price)

    def set_levels_result(self, result: "LevelsResult") -> None:
        """
        Set levels result directly.

        Delegates to LevelZonesRendering.set_levels_result().

        Args:
            result: LevelsResult from LevelEngine
        """
        self._rendering.set_levels_result(result)

    def get_levels_for_chatbot(self) -> str:
        """
        Get levels in tag format for chatbot.

        Returns:
            String with level tags like "[#Support Zone; 91038-91120]"
        """
        if self._levels_result is None:
            return ""
        return self._levels_result.to_tag_format()

    def get_nearest_support(self, price: Optional[float] = None) -> Optional["Level"]:
        """Get nearest support level."""
        if self._levels_result is None:
            return None
        return self._levels_result.get_nearest_support(price)

    def get_nearest_resistance(self, price: Optional[float] = None) -> Optional["Level"]:
        """Get nearest resistance level."""
        if self._levels_result is None:
            return None
        return self._levels_result.get_nearest_resistance(price)

    def _on_zone_clicked(self, zone_id: str, price: float, top: float, bottom: float, label: str) -> None:
        """Handle zone click event.

        Delegates to LevelZonesInteractions.on_zone_clicked().

        Args:
            zone_id: Clicked zone ID
            price: Price at click
            top: Zone top price
            bottom: Zone bottom price
            label: Zone label
        """
        if hasattr(self, '_interactions') and self._interactions is not None:
            self._interactions.on_zone_clicked(zone_id, price, top, bottom, label)


# Re-export für backward compatibility
__all__ = [
    "LevelZonesMixin",
    "LevelZonesToolbar",
    "LevelZonesRendering",
    "LevelZonesInteractions",
    "LEVEL_ZONE_COLORS",
]
