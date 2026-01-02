"""Chart AI Markings Mixin - Methods for AI-driven chart markings.

Provides methods to add markings from AI analysis:
- Horizontal lines (Stop Loss, Take Profit)
- Price zones (Support, Resistance, Demand, Supply)
- Entry markers (Long, Short)
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from PyQt6.QtCore import pyqtSignal

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class ChartAIMarkingsMixin:
    """Mixin for AI-driven chart markings via JavaScript API."""

    # Signal to execute JavaScript in main thread (thread-safe)
    _execute_js_signal = pyqtSignal(str)

    def __init__(self, *args, **kwargs):
        """Initialize the mixin and connect signals."""
        super().__init__(*args, **kwargs)
        # Connect signal to handler (will be called in main thread)
        self._execute_js_signal.connect(self._execute_js_in_main_thread)

    def _execute_js_in_main_thread(self, js_code: str) -> None:
        """Execute JavaScript in main thread (signal handler).

        Args:
            js_code: JavaScript code to execute
        """
        try:
            web_view = getattr(self, "web_view", None)
            if not web_view or not web_view.page():
                logger.warning("Cannot run JS: web_view or page not available")
                return

            web_view.page().runJavaScript(js_code)
        except Exception as e:
            logger.error(f"Error executing JS: {e}", exc_info=True)

    def _run_js_thread_safe(self, js_code: str) -> None:
        """Run JavaScript in the main Qt thread (thread-safe).

        Args:
            js_code: JavaScript code to execute
        """
        try:
            # Emit signal - will be processed in main thread
            self._execute_js_signal.emit(js_code)
        except Exception as e:
            logger.error(f"Error emitting JS signal: {e}", exc_info=True)

    def add_horizontal_line(self, price: float, color: str, label: str) -> str:
        """Add a horizontal line at specified price.

        Args:
            price: Price level for the line
            color: Line color (hex format, e.g., '#ff0000')
            label: Label text for the line

        Returns:
            ID of the created line
        """
        # Generate unique ID for the line
        line_id = f"ai_{label.lower().replace(' ', '_')}_{int(price)}"

        js_code = f"""
            (function() {{
                try {{
                    if (typeof window.chartAPI !== 'undefined' && window.chartAPI.addHorizontalLine) {{
                        const lineId = window.chartAPI.addHorizontalLine(
                            {price},
                            '{color}',
                            '{label}',
                            'solid',
                            '{line_id}'
                        );
                        console.log('Added horizontal line:', '{label}', 'at', {price}, 'ID:', lineId);
                        return lineId;
                    }} else {{
                        console.error('chartAPI.addHorizontalLine not available');
                        return null;
                    }}
                }} catch (e) {{
                    console.error('Error adding horizontal line:', e);
                    return null;
                }}
            }})();
        """

        # Check if chart is ready
        if not getattr(self, "page_loaded", False):
            logger.warning(f"Chart not ready for adding horizontal line: {label}")
            return line_id

        # Run JavaScript in main thread (thread-safe)
        self._run_js_thread_safe(js_code)
        logger.info(f"✅ Added horizontal line: {label} at {price:.2f} ({color})")

        return line_id

    def add_zone(
        self,
        start_time: int,
        end_time: int,
        top_price: float,
        bottom_price: float,
        fill_color: str,
        border_color: str,
        label: str,
    ) -> str:
        """Add a price zone (rectangle) to the chart.

        Args:
            start_time: Start timestamp (Unix seconds)
            end_time: End timestamp (Unix seconds)
            top_price: Upper price boundary
            bottom_price: Lower price boundary
            fill_color: Fill color (rgba format)
            border_color: Border color (hex format)
            label: Zone label

        Returns:
            ID of the created zone
        """
        try:
            # Generate unique ID for the zone
            zone_id = f"ai_zone_{label.lower().replace(' ', '_')}_{int(bottom_price)}"

            # Check if chart is ready
            if not getattr(self, "page_loaded", False):
                logger.warning(f"Chart not ready for adding zone: {label}")
                return zone_id

            js_code = f"""
                (function() {{
                    try {{
                        if (typeof window.chartAPI === 'undefined') {{
                            console.error('chartAPI not defined');
                            return null;
                        }}

                        // Get priceSeries reference
                        const priceSeries = window.priceSeries;
                        if (!priceSeries) {{
                            console.error('priceSeries not available');
                            return null;
                        }}

                        // Create zone primitive
                        const zone = new ZonePrimitive(
                            '{zone_id}',
                            {start_time},
                            {end_time},
                            {top_price},
                            {bottom_price},
                            '{fill_color}',
                            '{border_color}',
                            '{label}'
                        );

                        // Attach to price series
                        priceSeries.attachPrimitive(zone);

                        // Store in drawings array if available
                        if (typeof window.drawings !== 'undefined') {{
                            window.drawings.push(zone);
                        }}

                        console.log('Added zone:', '{label}', {{
                            id: '{zone_id}',
                            startTime: {start_time},
                            endTime: {end_time},
                            topPrice: {top_price},
                            bottomPrice: {bottom_price}
                        }});

                        return '{zone_id}';
                    }} catch (e) {{
                        console.error('Error adding zone:', e);
                        return null;
                    }}
                }})();
            """

            # Run JavaScript in main thread (thread-safe)
            self._run_js_thread_safe(js_code)
            logger.info(
                f"✅ Added zone: {label} [{bottom_price:.2f}-{top_price:.2f}] "
                f"from {start_time} to {end_time}"
            )

            return zone_id

        except Exception as e:
            logger.error(f"CRITICAL: Exception in add_zone for {label}: {e}", exc_info=True)
            return f"error_{label}"

    def add_support_zone(
        self,
        start_time: int,
        end_time: int,
        top_price: float,
        bottom_price: float,
        label: str = "Support",
    ) -> str:
        """Add a support zone (green).

        Args:
            start_time: Start timestamp (Unix seconds)
            end_time: End timestamp (Unix seconds)
            top_price: Upper price boundary
            bottom_price: Lower price boundary
            label: Zone label

        Returns:
            Zone ID
        """
        return self.add_zone(
            start_time,
            end_time,
            top_price,
            bottom_price,
            fill_color="rgba(38, 166, 154, 0.15)",  # Light teal/green
            border_color="#26a69a",
            label=label,
        )

    def add_resistance_zone(
        self,
        start_time: int,
        end_time: int,
        top_price: float,
        bottom_price: float,
        label: str = "Resistance",
    ) -> str:
        """Add a resistance zone (red).

        Args:
            start_time: Start timestamp (Unix seconds)
            end_time: End timestamp (Unix seconds)
            top_price: Upper price boundary
            bottom_price: Lower price boundary
            label: Zone label

        Returns:
            Zone ID
        """
        return self.add_zone(
            start_time,
            end_time,
            top_price,
            bottom_price,
            fill_color="rgba(239, 83, 80, 0.15)",  # Light red
            border_color="#ef5350",
            label=label,
        )

    def add_demand_zone(
        self,
        start_time: int,
        end_time: int,
        top_price: float,
        bottom_price: float,
        label: str = "Demand",
    ) -> str:
        """Add a demand zone (blue).

        Args:
            start_time: Start timestamp (Unix seconds)
            end_time: End timestamp (Unix seconds)
            top_price: Upper price boundary
            bottom_price: Lower price boundary
            label: Zone label

        Returns:
            Zone ID
        """
        return self.add_zone(
            start_time,
            end_time,
            top_price,
            bottom_price,
            fill_color="rgba(33, 150, 243, 0.15)",  # Light blue
            border_color="#2196f3",
            label=label,
        )

    def add_supply_zone(
        self,
        start_time: int,
        end_time: int,
        top_price: float,
        bottom_price: float,
        label: str = "Supply",
    ) -> str:
        """Add a supply zone (orange).

        Args:
            start_time: Start timestamp (Unix seconds)
            end_time: End timestamp (Unix seconds)
            top_price: Upper price boundary
            bottom_price: Lower price boundary
            label: Zone label

        Returns:
            Zone ID
        """
        return self.add_zone(
            start_time,
            end_time,
            top_price,
            bottom_price,
            fill_color="rgba(255, 152, 0, 0.15)",  # Light orange
            border_color="#ff9800",
            label=label,
        )

    def add_long_entry(self, timestamp: int, price: float, label: str = "Long Entry") -> str:
        """Add a long entry marker (green arrow up).

        Args:
            timestamp: Entry timestamp (Unix seconds)
            price: Entry price
            label: Marker label

        Returns:
            Marker ID
        """
        marker_id = f"ai_long_{int(timestamp)}_{int(price)}"

        js_code = f"""
            (function() {{
                try {{
                    const priceSeries = window.priceSeries;
                    if (!priceSeries) {{
                        console.error('priceSeries not available');
                        return null;
                    }}

                    // Add marker using LightweightCharts markers API
                    const existingMarkers = priceSeries.markers() || [];
                    const newMarker = {{
                        time: {timestamp},
                        position: 'belowBar',
                        color: '#26a69a',
                        shape: 'arrowUp',
                        text: '{label}',
                        id: '{marker_id}'
                    }};

                    priceSeries.setMarkers([...existingMarkers, newMarker]);
                    console.log('Added long entry marker at', {price}, 'time', {timestamp});
                    return '{marker_id}';
                }} catch (e) {{
                    console.error('Error adding long entry marker:', e);
                    return null;
                }}
            }})();
        """

        # Check if chart is ready
        if not getattr(self, "page_loaded", False):
            logger.warning("Chart not ready for adding long entry")
            return marker_id

        # Run JavaScript in main thread (thread-safe)
        self._run_js_thread_safe(js_code)
        logger.info(f"✅ Added long entry marker at {price:.2f}, time {timestamp}")

        return marker_id

    def add_short_entry(self, timestamp: int, price: float, label: str = "Short Entry") -> str:
        """Add a short entry marker (red arrow down).

        Args:
            timestamp: Entry timestamp (Unix seconds)
            price: Entry price
            label: Marker label

        Returns:
            Marker ID
        """
        marker_id = f"ai_short_{int(timestamp)}_{int(price)}"

        js_code = f"""
            (function() {{
                try {{
                    const priceSeries = window.priceSeries;
                    if (!priceSeries) {{
                        console.error('priceSeries not available');
                        return null;
                    }}

                    // Add marker using LightweightCharts markers API
                    const existingMarkers = priceSeries.markers() || [];
                    const newMarker = {{
                        time: {timestamp},
                        position: 'aboveBar',
                        color: '#ef5350',
                        shape: 'arrowDown',
                        text: '{label}',
                        id: '{marker_id}'
                    }};

                    priceSeries.setMarkers([...existingMarkers, newMarker]);
                    console.log('Added short entry marker at', {price}, 'time', {timestamp});
                    return '{marker_id}';
                }} catch (e) {{
                    console.error('Error adding short entry marker:', e);
                    return null;
                }}
            }})();
        """

        # Check if chart is ready
        if not getattr(self, "page_loaded", False):
            logger.warning("Chart not ready for adding short entry")
            return marker_id

        # Run JavaScript in main thread (thread-safe)
        self._run_js_thread_safe(js_code)
        logger.info(f"✅ Added short entry marker at {price:.2f}, time {timestamp}")

        return marker_id
