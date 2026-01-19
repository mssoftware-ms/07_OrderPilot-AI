"""Indicator Mixin for EmbeddedTradingViewChart.

Contains indicator calculation, conversion, and update methods.

REFACTORED: Split into 7 helper modules using composition pattern:
- indicator_utils.py: Utilities, IndicatorInstance dataclass, configs
- indicator_instance.py: Instance management (add/remove/render)
- indicator_conversion.py: Data conversion (MACD, multi-series, single-series)
- indicator_chart_ops.py: Chart operations (create/update/remove)
- indicator_update.py: Update orchestration
- indicator_realtime.py: Real-time updates
- indicator_mixin.py: Orchestrator + UI
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PyQt6.QtGui import QAction

from .indicator_instance import IndicatorInstanceManager
from .indicator_conversion import IndicatorConversion
from .indicator_chart_ops import IndicatorChartOps
from .indicator_update import IndicatorUpdate
from .indicator_realtime import IndicatorRealtime

logger = logging.getLogger(__name__)


class IndicatorMixin:
    """Mixin providing indicator functionality for EmbeddedTradingViewChart."""

    def _ensure_indicator_helpers(self) -> None:
        """Lazy initialization of indicator helpers (composition pattern)."""
        if getattr(self, '_updater', None) is None:
            self._instance_mgr = IndicatorInstanceManager(parent=self)
            self._conversion = IndicatorConversion(parent=self)
            self._chart_ops = IndicatorChartOps(parent=self)
            self._updater = IndicatorUpdate(parent=self)
            self._realtime = IndicatorRealtime(parent=self)
            logger.debug("IndicatorMixin helpers initialized")

    def _setup_indicators(self) -> None:
        """Initialize indicator helpers (composition pattern).

        Note: Also called via _ensure_indicator_helpers() for lazy init.
        """
        self._ensure_indicator_helpers()

    # =============================================================================
    # PUBLIC API - DELEGATES TO HELPERS
    # =============================================================================

    def _add_indicator_instance(self, ind_id: str, params: dict, color: str) -> None:
        """Delegate to instance manager."""
        self._ensure_indicator_helpers()
        self._instance_mgr.add_indicator_instance(ind_id, params, color)

    def _remove_indicator_instance(self, instance_id: str) -> None:
        """Delegate to instance manager."""
        self._ensure_indicator_helpers()
        self._instance_mgr.remove_indicator_instance(instance_id)

    def _update_indicators(self):
        """Delegate to updater."""
        self._ensure_indicator_helpers()
        self._updater.update_indicators()

    def _update_indicators_realtime(self, candle: dict):
        """Delegate to realtime helper."""
        self._ensure_indicator_helpers()
        self._realtime.update_indicators_realtime(candle)

    def _cleanup_all_chart_indicators(self):
        """Remove ALL chart indicators/panels (JavaScript cleanup).

        This is a nuclear option to clear all duplicate chart objects
        that may have accumulated due to bugs.
        """
        if not hasattr(self, 'active_indicators'):
            return

        try:
            # Remove all visual chart elements for each active indicator
            for instance_id, inst in list(self.active_indicators.items()):
                try:
                    display_name = inst.get('display_name', instance_id)
                    is_overlay = inst.get('is_overlay', True)
                    self._chart_ops.remove_indicator_from_chart(instance_id, display_name, is_overlay)
                except Exception as e:
                    logger.warning(f"Could not remove chart element for {instance_id}: {e}")

            logger.info("Cleaned up all chart indicators (visual removal)")

        except Exception as e:
            logger.error(f"Error during chart indicator cleanup: {e}", exc_info=True)

    def _refresh_all_indicators(self):
        """Refresh all active indicators with updated chart data.

        This removes chart-visual elements first, then re-creates them,
        but keeps the same instance IDs in active_indicators dict.
        """
        if not hasattr(self, 'active_indicators') or not self.active_indicators:
            return

        try:
            # Store active indicators data BEFORE visual removal
            indicators_data = []
            for instance_id, inst in list(self.active_indicators.items()):
                indicators_data.append({
                    'instance_id': instance_id,
                    'inst': inst,
                    'display_name': inst.get('display_name', instance_id),
                    'is_overlay': inst.get('is_overlay', True)
                })

            # STEP 1: Remove visual chart elements (JavaScript objects)
            # BUT keep active_indicators dict intact
            for data in indicators_data:
                try:
                    self._chart_ops.remove_indicator_from_chart(
                        data['instance_id'],
                        data['display_name'],
                        data['is_overlay']
                    )
                except Exception as e:
                    logger.warning(f"Could not remove chart element for {data['instance_id']}: {e}")

            # STEP 2: Re-create visual chart elements with SAME instance IDs
            # This calls add_indicator_instance_to_chart() which creates NEW chart objects
            # but uses the EXISTING instance data from active_indicators
            self._update_indicators()

            active_count = len(self.active_indicators)
            logger.info(f"Refreshed {active_count} indicators with updated chart data")

        except Exception as e:
            logger.error(f"Error refreshing indicators: {e}", exc_info=True)

    # =============================================================================
    # UI - BUTTON BADGE & TOGGLE HANDLER
    # =============================================================================

    def _update_indicators_button_badge(self):
        """Update indicators button to show count of active indicators."""
        active_count = len(getattr(self, "active_indicators", {}))

        if active_count > 0:
            self.indicators_button.setText(f"📊 Indikatoren ({active_count})")
            self.indicators_button.setStyleSheet("""
                QPushButton {
                    background-color: #FF6B00;
                    color: white;
                    font-weight: bold;
                    border: 2px solid #FF8C00;
                    border-radius: 3px;
                    padding: 5px 10px;
                }
                QPushButton:hover {
                    background-color: #FF8C00;
                }
                QPushButton::menu-indicator {
                    subcontrol-origin: padding;
                    subcontrol-position: right center;
                }
            """)
        else:
            self.indicators_button.setText("📊 Indikatoren")
            self.indicators_button.setStyleSheet("""
                QPushButton {
                    background-color: #2a2a2a;
                    color: #aaa;
                    border: 1px solid #555;
                    border-radius: 3px;
                    padding: 5px 10px;
                }
                QPushButton:hover {
                    background-color: #3a3a3a;
                    color: #fff;
                }
                QPushButton::menu-indicator {
                    subcontrol-origin: padding;
                    subcontrol-position: right center;
                }
            """)

    def _on_indicator_toggled(self, action: "QAction"):
        """Handle indicator toggle from dropdown menu.

        Args:
            action: The QAction that was toggled
        """
        indicator_data = action.data()
        indicator_id = indicator_data["id"]
        is_checked = action.isChecked()

        logger.info(f"🔄 Indicator {indicator_id} {'enabled' if is_checked else 'disabled'} (currently active: {list(self.active_indicators.keys())})")

        # Update indicators display
        self._update_indicators()

        # Update button style to show how many indicators are active
        self._update_indicators_button_badge()

        logger.info(f"✓ Toggle complete. Active indicators: {list(self.active_indicators.keys())}")
