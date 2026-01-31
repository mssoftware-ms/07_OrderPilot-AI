"""Toolbar Row 1 Actions Mixin - Action Methods and Toolbar Operations.

This module handles action methods and toolbar operations for toolbar row 1.
Part of toolbar_mixin_row1.py refactoring (827 LOC → 3 focused mixins).

Responsibilities:
- Zoom operations (zoom all, zoom back)
- Chart loading and refresh operations
- Indicator add/remove/reset operations
- Custom parameter dialogs
- Active indicator menu refresh
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from PyQt6.QtGui import QAction

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class ToolbarRow1ActionsMixin:
    """Row 1 toolbar actions - action methods and toolbar operations."""

    def on_zoom_all(self):
        """Zoom chart to show all data with sane pane heights."""
        try:
            if hasattr(self.parent, "zoom_to_fit_all"):
                self.parent.zoom_to_fit_all()
            else:
                logger.warning("zoom_to_fit_all not available on chart widget")
        except Exception as e:
            logger.error("Zoom-All failed: %s", e, exc_info=True)

    def on_zoom_back(self):
        """Restore previous view (visible range + pane heights)."""
        try:
            if hasattr(self.parent, "zoom_back_to_previous_view"):
                restored = self.parent.zoom_back_to_previous_view()
                if not restored:
                    logger.info("No previous view state to restore")
            else:
                logger.warning("zoom_back_to_previous_view not available on chart widget")
        except Exception as e:
            logger.error("Zoom-Back failed: %s", e, exc_info=True)

    def on_load_chart(self) -> None:
        """Handle load chart button - reload current symbol."""
        try:
            if hasattr(self.parent, 'current_symbol') and self.parent.current_symbol:
                symbol = self.parent.current_symbol
                provider = getattr(self.parent, 'current_data_provider', None)
                logger.info(f"Reloading chart for {symbol}")
                # Use qasync to run async method
                import qasync
                import asyncio
                if hasattr(self.parent, 'load_symbol'):
                    asyncio.ensure_future(self.parent.load_symbol(symbol, provider))
            else:
                logger.warning("No current symbol to load")
        except Exception as e:
            logger.error(f"Load chart failed: {e}", exc_info=True)

    def on_refresh(self) -> None:
        """Handle refresh button - same as load chart."""
        self.on_load_chart()

    def on_indicator_add(self, ind_id: str, params: dict, color: str) -> None:
        """Add indicator instance to chart."""
        if hasattr(self.parent, "chart_widget") and hasattr(self.parent.chart_widget, "_add_indicator_instance"):
            self.parent.chart_widget._add_indicator_instance(ind_id, params, color)
            self.refresh_active_indicator_menu()

    def on_indicator_remove(self, instance_id: str) -> None:
        """Remove indicator instance from chart."""
        if hasattr(self.parent, "chart_widget") and hasattr(self.parent.chart_widget, "_remove_indicator_instance"):
            self.parent.chart_widget._remove_indicator_instance(instance_id)
            self.refresh_active_indicator_menu()

    def on_reset_indicators(self) -> None:
        """Completely clear all indicators from the chart."""
        if hasattr(self.parent, "chart_widget"):
            chart = self.parent.chart_widget
            if hasattr(chart, "_cleanup_all_chart_indicators"):
                chart._cleanup_all_chart_indicators()

            # Explicitly clear active_indicators and counter
            if hasattr(chart, "active_indicators"):
                chart.active_indicators.clear()
            if hasattr(chart, "_indicator_counter"):
                chart._indicator_counter = 0

            self.refresh_active_indicator_menu()
            if hasattr(chart, "_update_indicators_button_badge"):
                chart._update_indicators_button_badge()

            logger.info("Nuclear reset: All indicators cleared from chart")

    def refresh_active_indicator_menu(self) -> None:
        """Show active indicators as remove-actions directly in main menu."""
        if not hasattr(self.parent, "indicators_menu"):
            return
        # remove old actions
        if getattr(self.parent, "_remove_actions", None):
            for act in self.parent._remove_actions:
                self.parent.indicators_menu.removeAction(act)
        if getattr(self.parent, "_remove_section_separator", None):
            self.parent.indicators_menu.removeAction(self.parent._remove_section_separator)
        self.parent._remove_actions = []
        self.parent._remove_section_separator = None

        if not hasattr(self.parent, "chart_widget") or not getattr(self.parent.chart_widget, "active_indicators", None):
            return

        if self.parent.chart_widget.active_indicators:
            self.parent._remove_section_separator = self.parent.indicators_menu.addSeparator()
            for instance_id, inst in self.parent.chart_widget.active_indicators.items():
                label = f"Remove: {inst.display_name}"
                act = QAction(label, self.parent)
                act.triggered.connect(lambda _=False, iid=instance_id: self.on_indicator_remove(iid))
                self.parent.indicators_menu.addAction(act)
                self.parent._remove_actions.append(act)

    def prompt_custom_period(self, ind_id: str, color: str) -> None:
        """Show custom period dialog for indicator."""
        from PyQt6.QtWidgets import QInputDialog
        period, ok = QInputDialog.getInt(self.parent, "Periode wählen", f"{ind_id} Periode:", value=14, min=1, max=500)
        if ok:
            self.on_indicator_add(ind_id, {"period": period}, color)

    def prompt_generic_params(self, ind_id: str, color: str) -> None:
        """Show generic parameter dialog for indicator."""
        from PyQt6.QtWidgets import QInputDialog
        text, ok = QInputDialog.getText(self.parent, "Parameter", f"{ind_id} Parameter (key=value,comma-separated):", text="period=20")
        if not ok:
            return
        params = {}
        try:
            for part in text.split(","):
                k, v = part.split("=")
                params[k.strip()] = float(v) if "." in v else int(v)
            self.on_indicator_add(ind_id, params, color)
        except Exception:
            logger.error("Parameter-Parsing fehlgeschlagen: %s", text)
