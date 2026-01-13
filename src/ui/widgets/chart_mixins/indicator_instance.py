"""Indicator Instance - Instance management.

Refactored from 676 LOC monolith using composition pattern.

Module 2/7 of indicator_mixin.py split.

Contains:
- add_indicator_instance(): Create new indicator instance
- remove_indicator_instance(): Remove instance
- add_indicator_instance_to_chart(): Calculate + render instance
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .indicator_utils import IndicatorInstance

from src.core.indicators.engine import IndicatorConfig

logger = logging.getLogger(__name__)


class IndicatorInstanceManager:
    """Helper für IndicatorMixin instance management."""

    def __init__(self, parent):
        """
        Args:
            parent: IndicatorMixin Instanz
        """
        self.parent = parent

    def add_indicator_instance(self, ind_id: str, params: dict, color: str) -> None:
        """Create a new indicator instance (may be multiple per type)."""
        from .indicator_utils import IndicatorInstance, get_indicator_configs

        overlay_configs, oscillator_configs = get_indicator_configs()

        is_overlay = ind_id in overlay_configs
        is_oscillator = ind_id in oscillator_configs
        if not (is_overlay or is_oscillator):
            logger.warning("Indicator %s not implemented", ind_id)
            return

        if is_overlay:
            ind_type, default_params, base_display, _, _ = overlay_configs[ind_id]
        else:
            ind_type, default_params, base_display, min_val, max_val = oscillator_configs[ind_id]

        # merge params over defaults
        merged_params = dict(default_params or {})
        merged_params.update(params or {})

        self.parent._indicator_counter += 1
        instance_id = f"{ind_id}_{self.parent._indicator_counter}"
        display_name = f"{base_display} #{self.parent._indicator_counter}"

        inst = IndicatorInstance(
            instance_id=instance_id,
            ind_id=ind_id,
            ind_type=ind_type,
            params=merged_params,
            display_name=display_name,
            is_overlay=is_overlay,
            color=color,
            min_val=None if is_overlay else min_val,
            max_val=None if is_overlay else max_val,
        )

        self.parent.active_indicators[instance_id] = inst
        # If data not yet loaded or chart not ready, queue instance
        if self.parent.data is None or not (self.parent.page_loaded and self.parent.chart_initialized):
            self.parent._pending_indicator_instances.append(inst)
            logger.info("Queued indicator %s until chart is ready", display_name)
        else:
            self.add_indicator_instance_to_chart(inst)

        self.parent._update_indicators_button_badge()
        if hasattr(self.parent, "_refresh_active_indicator_menu"):
            self.parent._refresh_active_indicator_menu()

    def remove_indicator_instance(self, instance_id: str) -> None:
        """Remove indicator instance from chart and active dict."""
        inst = self.parent.active_indicators.get(instance_id)
        if not inst:
            return

        try:
            self.parent._chart_ops.remove_indicator_from_chart(
                inst.instance_id,
                inst.display_name,
                inst.is_overlay,
            )
        finally:
            self.parent.active_indicators.pop(instance_id, None)
            self.parent._update_indicators_button_badge()
            if hasattr(self.parent, "_refresh_active_indicator_menu"):
                self.parent._refresh_active_indicator_menu()

    def add_indicator_instance_to_chart(self, inst: "IndicatorInstance") -> None:
        """Calculate + render a specific instance.

        Args:
            inst: IndicatorInstance to add
        """
        try:
            if self.parent.data is None:
                logger.warning("No data yet, cannot add indicator %s", inst.display_name)
                return

            # Issue #55: Ensure chart is fully ready before adding indicator
            if not (self.parent.page_loaded and self.parent.chart_initialized):
                logger.warning("Chart not ready yet, cannot add indicator %s", inst.display_name)
                # Re-queue the indicator
                if inst not in self.parent._pending_indicator_instances:
                    self.parent._pending_indicator_instances.append(inst)
                return

            logger.info(f"Adding indicator to chart: {inst.display_name} (overlay={inst.is_overlay})")

            config = IndicatorConfig(indicator_type=inst.ind_type, params=inst.params)
            result = self.parent.indicator_engine.calculate(self.parent.data, config)
            ind_data = self.parent._conversion.convert_indicator_result(inst.ind_id, result)

            logger.debug(f"Indicator data calculated: {len(ind_data)} points")

            if inst.is_overlay:
                self.parent._chart_ops.create_overlay_indicator(inst.display_name, inst.color)
                logger.info(f"Created overlay indicator: {inst.display_name}")
            else:
                self.parent._chart_ops.create_oscillator_panel(
                    inst.instance_id, inst.display_name, inst.color, inst.min_val, inst.max_val
                )
                logger.info(f"Created oscillator panel: {inst.instance_id}")

            if inst.is_overlay:
                self.parent._chart_ops.update_overlay_data(inst.display_name, ind_data)
                logger.info(f"Updated overlay data: {inst.display_name}")
            else:
                self.parent._chart_ops.update_oscillator_data(inst.instance_id, ind_data)
                logger.info(f"Updated oscillator data: {inst.instance_id}")

        except Exception as ind_error:
            logger.error("Error creating indicator %s: %s", inst.ind_id, ind_error, exc_info=True)
