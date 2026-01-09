"""Indicator Update - Update orchestration.

Refactored from 676 LOC monolith using composition pattern.

Module 5/7 of indicator_mixin.py split.

Contains:
- update_indicators(): Main update method
- should_skip_full_update(): Skip check
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class IndicatorUpdate:
    """Helper für IndicatorMixin update orchestration."""

    def __init__(self, parent):
        """
        Args:
            parent: IndicatorMixin Instanz
        """
        self.parent = parent

    def update_indicators(self):
        """Update technical indicators on chart."""
        logger.info("🔧 _update_indicators called")

        if self.parent.data is None:
            logger.warning("❌ Cannot update indicators: chart data not loaded yet")
            return

        if self.should_skip_full_update():
            return

        logger.info("✓ Chart ready, processing indicators...")

        try:
            self.parent._updating_indicators = True

            # First apply any pending instances queued before data was ready
            if hasattr(self.parent, "_pending_indicator_instances") and self.parent._pending_indicator_instances:
                pending = list(self.parent._pending_indicator_instances)
                self.parent._pending_indicator_instances.clear()
                for inst in pending:
                    self.parent._instance_mgr.add_indicator_instance_to_chart(inst)

            # Update all active indicators
            for inst in list(self.parent.active_indicators.values()):
                self.parent._instance_mgr.add_indicator_instance_to_chart(inst)

            self.parent._update_indicators_button_badge()

        except Exception as e:
            logger.error(f"Error updating indicators: {e}", exc_info=True)
        finally:
            self.parent._updating_indicators = False

    def should_skip_full_update(self) -> bool:
        """Check if indicator update should be skipped.

        Returns:
            True if update should be skipped
        """
        if not (self.parent.page_loaded and self.parent.chart_initialized):
            logger.warning(
                "❌ Cannot update indicators: chart not fully initialized yet (page_loaded=%s, chart_initialized=%s)",
                self.parent.page_loaded,
                self.parent.chart_initialized,
            )
            self.parent._pending_indicator_update = True
            return True

        if self.parent._updating_indicators:
            logger.warning("⏸️ Indicator update already in progress, skipping...")
            return True

        return False
