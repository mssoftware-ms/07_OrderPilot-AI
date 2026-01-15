"""Markings Manager - Manages bidirectional chart markings for AI chat.

Extracts markings from chart, sends to AI, receives updates, applies to chart.
"""

from __future__ import annotations

import logging
from datetime import timezone
from typing import TYPE_CHECKING
from uuid import uuid4

from .chart_markings import ChartMarking, ChartMarkingsState, CompactAnalysisResponse, MarkingType

if TYPE_CHECKING:
    from src.ui.widgets.embedded_tradingview_chart import EmbeddedTradingViewChart

logger = logging.getLogger(__name__)


class MarkingsManager:
    """Manages chart markings for AI analysis."""

    def __init__(self, chart_widget: "EmbeddedTradingViewChart"):
        """Initialize markings manager.

        Args:
            chart_widget: Chart widget to manage markings for
        """
        self.chart = chart_widget
        self._markings_state = ChartMarkingsState()

        # Dispatch map: MarkingType -> handler method
        self._marking_handlers = {
            MarkingType.STOP_LOSS: self._apply_stop_loss,
            MarkingType.TAKE_PROFIT: self._apply_take_profit,
            MarkingType.ENTRY_LONG: self._apply_entry_long,
            MarkingType.ENTRY_SHORT: self._apply_entry_short,
            MarkingType.SUPPORT_ZONE: self._apply_support_zone,
            MarkingType.RESISTANCE_ZONE: self._apply_resistance_zone,
            MarkingType.DEMAND_ZONE: self._apply_demand_zone,
            MarkingType.SUPPLY_ZONE: self._apply_supply_zone,
        }

    def get_current_markings(self) -> ChartMarkingsState:
        """Get current state of all chart markings.

        Returns:
            Current markings state
        """
        # TODO: Extract markings from chart widget
        # For now, return stored state
        self._markings_state.symbol = getattr(self.chart, "current_symbol", "")
        self._markings_state.timeframe = getattr(self.chart, "current_timeframe", "")
        return self._markings_state

    def apply_ai_response(self, response: CompactAnalysisResponse) -> None:
        """Apply AI response updates to chart markings.

        Args:
            response: Parsed AI response with marking updates
        """
        logger.info(f"Applying {len(response.markings_updated)} marking updates to chart")

        for var_str in response.markings_updated:
            marking = ChartMarking.from_variable_string(var_str, str(uuid4()))
            if marking:
                self._apply_marking_to_chart(marking)
                self._markings_state.update_or_add(marking)
            else:
                logger.warning(f"Failed to parse marking: {var_str}")

        for marking_id in response.markings_removed:
            self._remove_marking_from_chart(marking_id)
            self._markings_state.remove_marking(marking_id)

        logger.info("Chart markings updated successfully")

    def _apply_marking_to_chart(self, marking: ChartMarking) -> None:
        """Apply a single marking to the chart using dispatch pattern.

        Args:
            marking: Marking to apply
        """
        try:
            handler = self._marking_handlers.get(marking.type)
            if handler:
                handler(marking)
            else:
                logger.warning(f"Unsupported marking type: {marking.type}")
        except Exception as e:
            logger.error(f"Failed to apply marking {marking.type}: {e}", exc_info=True)

    # Handler methods for each marking type (reduce complexity)
    def _apply_stop_loss(self, marking: ChartMarking) -> None:
        """Apply stop loss marking."""
        if marking.price:
            logger.info(f"Adding Stop Loss at {marking.price:.2f}")
            self._add_horizontal_line(marking.price, "#f44336", marking.label or "Stop Loss")

    def _apply_take_profit(self, marking: ChartMarking) -> None:
        """Apply take profit marking."""
        if marking.price:
            logger.info(f"Adding Take Profit at {marking.price:.2f}")
            self._add_horizontal_line(marking.price, "#4caf50", marking.label or "Take Profit")

    def _apply_entry_long(self, marking: ChartMarking) -> None:
        """Apply long entry marking."""
        if marking.price:
            logger.info(f"Adding Long Entry at {marking.price:.2f}")
            timestamp = self._get_current_timestamp()
            if hasattr(self.chart, 'add_long_entry'):
                self.chart.add_long_entry(timestamp, marking.price, marking.label or "Long Entry")
            else:
                logger.warning("Chart does not have add_long_entry method")

    def _apply_entry_short(self, marking: ChartMarking) -> None:
        """Apply short entry marking."""
        if marking.price:
            logger.info(f"Adding Short Entry at {marking.price:.2f}")
            timestamp = self._get_current_timestamp()
            if hasattr(self.chart, 'add_short_entry'):
                self.chart.add_short_entry(timestamp, marking.price, marking.label or "Short Entry")
            else:
                logger.warning("Chart does not have add_short_entry method")

    def _apply_support_zone(self, marking: ChartMarking) -> None:
        """Apply support zone marking."""
        if marking.price_top and marking.price_bottom:
            logger.info(f"Adding Support Zone {marking.price_bottom:.2f}-{marking.price_top:.2f}")
            self._add_zone(marking, "support")

    def _apply_resistance_zone(self, marking: ChartMarking) -> None:
        """Apply resistance zone marking."""
        if marking.price_top and marking.price_bottom:
            logger.info(f"Adding Resistance Zone {marking.price_bottom:.2f}-{marking.price_top:.2f}")
            self._add_zone(marking, "resistance")

    def _apply_demand_zone(self, marking: ChartMarking) -> None:
        """Apply demand zone marking."""
        if marking.price_top and marking.price_bottom:
            logger.info(f"Adding Demand Zone {marking.price_bottom:.2f}-{marking.price_top:.2f}")
            self._add_zone(marking, "demand")

    def _apply_supply_zone(self, marking: ChartMarking) -> None:
        """Apply supply zone marking."""
        if marking.price_top and marking.price_bottom:
            logger.info(f"Adding Supply Zone {marking.price_bottom:.2f}-{marking.price_top:.2f}")
            self._add_zone(marking, "supply")

    def _add_horizontal_line(self, price: float, color: str, label: str) -> None:
        """Add horizontal line to chart.

        Args:
            price: Price level
            color: Line color
            label: Line label
        """
        if hasattr(self.chart, 'add_horizontal_line'):
            self.chart.add_horizontal_line(price, color, label)
        else:
            logger.warning("Chart does not have add_horizontal_line method")

    def _add_zone(self, marking: ChartMarking, zone_type: str) -> None:
        """Add price zone to chart.

        Args:
            marking: Marking with zone data
            zone_type: Type of zone ('support', 'resistance', 'demand', 'supply')
        """
        # Get time range for the zone
        start_time, end_time = self._get_zone_time_range()

        # Map zone type to chart methods
        method_map = {
            "support": "add_support_zone",
            "resistance": "add_resistance_zone",
            "demand": "add_demand_zone",
            "supply": "add_supply_zone",
        }

        method_name = method_map.get(zone_type)
        if method_name and hasattr(self.chart, method_name):
            method = getattr(self.chart, method_name)
            method(
                start_time,
                end_time,
                marking.price_top,
                marking.price_bottom,
                marking.label or zone_type.title()
            )
        else:
            logger.warning(f"Chart does not have {method_name} method")

    def _get_zone_time_range(self) -> tuple[int, int]:
        """Get time range for zones spanning into the extended canvas area.

        Returns:
            Tuple of (start_time, end_time) as unix timestamps
        """
        # Try to get from chart data
        try:
            if hasattr(self.chart, 'data') and self.chart.data is not None:
                df = self.chart.data
                if len(df) > 0:
                    # DataFrame index is the timestamp
                    last_timestamp = df.index[-1]

                    # Use last 50 candles for zone width
                    num_candles = min(50, len(df))
                    start_timestamp = df.index[-num_candles]

                    # Convert to Unix timestamps (UTC)
                    # Handle both timezone-aware and naive datetimes
                    if start_timestamp.tzinfo is None:
                        start_timestamp = start_timestamp.replace(tzinfo=timezone.utc)
                    if last_timestamp.tzinfo is None:
                        last_timestamp = last_timestamp.replace(tzinfo=timezone.utc)

                    start_time = int(start_timestamp.timestamp())

                    # ✅ EXTENDED CANVAS: Extend zone into the future (rightOffset area)
                    # Calculate time per bar based on chart timeframe
                    if len(df) >= 2:
                        time_diff = (df.index[-1] - df.index[-2]).total_seconds()
                    else:
                        time_diff = 300  # Default: 5 minutes

                    # Extend zone 30 bars into the future (into rightOffset=50 area)
                    future_extension_bars = 30
                    end_time = int(last_timestamp.timestamp()) + int(time_diff * future_extension_bars)

                    logger.debug(f"Zone time range: {start_time} to {end_time} ({num_candles} candles + {future_extension_bars} future bars)")
                    return start_time, end_time
        except Exception as e:
            logger.warning(f"Could not get time range from chart data: {e}", exc_info=True)

        # Fallback: use last known price time or current time
        logger.warning("Using fallback time range - zones may not appear correctly")
        import time
        end_time = int(time.time())
        start_time = end_time - (3600 * 2)  # 2 hours
        return start_time, end_time

    def _get_current_timestamp(self) -> int:
        """Get current timestamp for markers.

        Returns:
            Unix timestamp
        """
        try:
            if hasattr(self.chart, 'data') and self.chart.data is not None:
                df = self.chart.data
                if len(df) > 0:
                    # DataFrame index is the timestamp
                    last_timestamp = df.index[-1]

                    # Convert to Unix timestamp (UTC)
                    # Handle both timezone-aware and naive datetimes
                    if last_timestamp.tzinfo is None:
                        last_timestamp = last_timestamp.replace(tzinfo=timezone.utc)
                    return int(last_timestamp.timestamp())
        except Exception as e:
            logger.warning(f"Could not get timestamp from chart data: {e}", exc_info=True)

        import time
        return int(time.time())

    def _remove_marking_from_chart(self, marking_id: str) -> None:
        """Remove marking from chart.

        Args:
            marking_id: ID of marking to remove
        """
        # TODO: Implement removal logic
        # Charts typically don't have IDs for all elements, so this is tricky
        # For now, just log
        logger.info(f"Marking removal requested: {marking_id} (not implemented yet)")

    def add_manual_marking(
        self,
        marking_type: MarkingType,
        price: float | None = None,
        price_top: float | None = None,
        price_bottom: float | None = None,
        label: str = "",
        reasoning: str = "",
    ) -> ChartMarking:
        """Manually add a marking (for user-created markings).

        Args:
            marking_type: Type of marking
            price: Single price point (for entry, stop, etc.)
            price_top: Top of zone
            price_bottom: Bottom of zone
            label: Optional label
            reasoning: Optional reasoning

        Returns:
            Created marking
        """
        marking = ChartMarking(
            id=str(uuid4()),
            type=marking_type,
            price=price,
            price_top=price_top,
            price_bottom=price_bottom,
            label=label,
            reasoning=reasoning,
        )

        self._apply_marking_to_chart(marking)
        self._markings_state.update_or_add(marking)

        return marking
