"""
Heatmap UI Bridge

Provides communication bridge between Python and JavaScript for heatmap rendering.
Handles data serialization and JavaScript API calls via PyQt6 WebEngine.
"""

import asyncio
import json
import logging
from typing import Optional, List, Dict, Any, Callable

from PyQt6.QtCore import QObject, pyqtSlot, pyqtSignal

from ..aggregation.grid_builder import GridCell


logger = logging.getLogger(__name__)


class HeatmapBridge(QObject):
    """
    Bridge between Python backend and JavaScript heatmap renderer.

    Provides methods to:
    - Initialize heatmap series in Lightweight Charts
    - Send full grid data
    - Send incremental updates
    - Control visibility and styling
    """

    # Signals for async communication
    data_ready = pyqtSignal(str)  # Emits JSON data
    error_occurred = pyqtSignal(str)  # Emits error message

    def __init__(self, web_view):
        """
        Initialize bridge.

        Args:
            web_view: QWebEngineView instance containing the chart
        """
        super().__init__()
        self.web_view = web_view
        self._initialized = False
        self._visible = False

    def is_initialized(self) -> bool:
        """Check if heatmap series is initialized."""
        return self._initialized

    def is_visible(self) -> bool:
        """Check if heatmap is visible."""
        return self._visible

    async def initialize_series(
        self,
        opacity: float = 0.5,
        palette: str = "hot",
    ) -> bool:
        """
        Initialize heatmap series in JavaScript.

        Must be called before sending data.

        Args:
            opacity: Heatmap opacity (0-1)
            palette: Color palette name

        Returns:
            True if successful
        """
        js_code = f"""
        (function() {{
            try {{
                if (typeof window.initializeHeatmap === 'function') {{
                    window.initializeHeatmap({{
                        opacity: {opacity},
                        palette: '{palette}'
                    }});
                    return true;
                }} else {{
                    console.error('initializeHeatmap function not found');
                    return false;
                }}
            }} catch (e) {{
                console.error('Failed to initialize heatmap:', e);
                return false;
            }}
        }})();
        """

        result = await self._run_javascript(js_code)

        if result:
            self._initialized = True
            logger.info("Heatmap series initialized")
        else:
            logger.error("Failed to initialize heatmap series")

        return result

    async def set_heatmap_data(self, cells: List[GridCell]) -> bool:
        """
        Set complete heatmap data (replaces existing data).

        Args:
            cells: List of grid cells

        Returns:
            True if successful
        """
        if not self._initialized:
            logger.error("Heatmap not initialized, call initialize_series() first")
            return False

        # Convert cells to JavaScript format
        data = self._cells_to_js_data(cells)

        js_code = f"""
        (function() {{
            try {{
                if (typeof window.setHeatmapData === 'function') {{
                    const data = {json.dumps(data)};
                    window.setHeatmapData(data);
                    return true;
                }} else {{
                    console.error('setHeatmapData function not found');
                    return false;
                }}
            }} catch (e) {{
                console.error('Failed to set heatmap data:', e);
                return false;
            }}
        }})();
        """

        result = await self._run_javascript(js_code)

        if result:
            logger.debug(f"Set {len(cells)} heatmap cells")
        else:
            logger.error("Failed to set heatmap data")

        return result

    async def append_heatmap_cells(self, cells: List[GridCell]) -> bool:
        """
        Append cells to existing heatmap (incremental update).

        Args:
            cells: List of new/updated cells

        Returns:
            True if successful
        """
        if not self._initialized:
            logger.error("Heatmap not initialized")
            return False

        if not cells:
            return True  # Nothing to append

        # Convert cells to JavaScript format
        data = self._cells_to_js_data(cells)

        js_code = f"""
        (function() {{
            try {{
                if (typeof window.appendHeatmapCells === 'function') {{
                    const data = {json.dumps(data)};
                    window.appendHeatmapCells(data);
                    return true;
                }} else {{
                    console.error('appendHeatmapCells function not found');
                    return false;
                }}
            }} catch (e) {{
                console.error('Failed to append heatmap cells:', e);
                return false;
            }}
        }})();
        """

        result = await self._run_javascript(js_code)

        if result:
            logger.debug(f"Appended {len(cells)} heatmap cells")
        else:
            logger.error("Failed to append heatmap cells")

        return result

    async def set_visible(self, visible: bool) -> bool:
        """
        Show or hide heatmap series.

        Args:
            visible: True to show, False to hide

        Returns:
            True if successful
        """
        js_code = f"""
        (function() {{
            try {{
                if (typeof window.setHeatmapVisible === 'function') {{
                    window.setHeatmapVisible({str(visible).lower()});
                    return true;
                }} else {{
                    console.error('setHeatmapVisible function not found');
                    return false;
                }}
            }} catch (e) {{
                console.error('Failed to set heatmap visibility:', e);
                return false;
            }}
        }})();
        """

        result = await self._run_javascript(js_code)

        if result:
            self._visible = visible
            logger.debug(f"Set heatmap visibility: {visible}")
        else:
            logger.error("Failed to set heatmap visibility")

        return result

    async def update_settings(
        self,
        opacity: Optional[float] = None,
        palette: Optional[str] = None,
    ) -> bool:
        """
        Update heatmap visual settings.

        Args:
            opacity: New opacity (0-1), None to keep current
            palette: New color palette, None to keep current

        Returns:
            True if successful
        """
        settings = {}
        if opacity is not None:
            settings["opacity"] = opacity
        if palette is not None:
            settings["palette"] = palette

        if not settings:
            return True  # Nothing to update

        js_code = f"""
        (function() {{
            try {{
                if (typeof window.updateHeatmapSettings === 'function') {{
                    const settings = {json.dumps(settings)};
                    window.updateHeatmapSettings(settings);
                    return true;
                }} else {{
                    console.error('updateHeatmapSettings function not found');
                    return false;
                }}
            }} catch (e) {{
                console.error('Failed to update heatmap settings:', e);
                return false;
            }}
        }})();
        """

        result = await self._run_javascript(js_code)

        if result:
            logger.debug(f"Updated heatmap settings: {settings}")
        else:
            logger.error("Failed to update heatmap settings")

        return result

    async def clear_heatmap(self) -> bool:
        """
        Clear all heatmap data.

        Returns:
            True if successful
        """
        js_code = """
        (function() {
            try {
                if (typeof window.clearHeatmap === 'function') {
                    window.clearHeatmap();
                    return true;
                } else {
                    console.error('clearHeatmap function not found');
                    return false;
                }
            } catch (e) {
                console.error('Failed to clear heatmap:', e);
                return false;
            }
        })();
        """

        result = await self._run_javascript(js_code)

        if result:
            logger.debug("Cleared heatmap data")
        else:
            logger.error("Failed to clear heatmap")

        return result

    def _cells_to_js_data(self, cells: List[GridCell]) -> List[Dict[str, Any]]:
        """
        Convert GridCell objects to JavaScript-compatible format.

        JavaScript expects array of objects with:
        - time: timestamp in seconds (Lightweight Charts format)
        - price: price level
        - value: intensity (0-1)
        """
        return [
            {
                "time": cell.time_ms / 1000,  # Convert ms to seconds
                "price": cell.price,
                "value": cell.intensity,
            }
            for cell in cells
        ]

    async def _run_javascript(self, code: str) -> Any:
        """
        Execute JavaScript code in web view and wait for result.

        Args:
            code: JavaScript code to execute

        Returns:
            Result from JavaScript execution
        """
        try:
            # Create future for result
            loop = asyncio.get_event_loop()
            future = loop.create_future()

            def callback(result):
                if not future.done():
                    future.set_result(result)

            # Run JavaScript with callback
            self.web_view.page().runJavaScript(code, callback)

            # Wait for result with timeout
            result = await asyncio.wait_for(future, timeout=5.0)
            return result

        except asyncio.TimeoutError:
            logger.error(f"JavaScript execution timeout: {code[:100]}...")
            return None
        except Exception as e:
            logger.error(f"JavaScript execution error: {e}", exc_info=True)
            return None

    @pyqtSlot()
    def on_chart_ready(self):
        """Handle chart ready signal from JavaScript."""
        logger.info("Chart ready, can initialize heatmap")

    @pyqtSlot(str)
    def on_javascript_error(self, error: str):
        """Handle JavaScript error."""
        logger.error(f"JavaScript error: {error}")
        self.error_occurred.emit(error)


# Example usage
if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    import sys

    async def _example():
        app = QApplication(sys.argv)

        # Create web view
        web_view = QWebEngineView()
        web_view.setHtml("<html><body>Test</body></html>")

        # Create bridge
        bridge = HeatmapBridge(web_view)

        # Initialize
        await bridge.initialize_series(opacity=0.5, palette="hot")

        # Test data
        from ..aggregation.grid_builder import GridCell

        cells = [
            GridCell(time_ms=1700000000000, price=50000.0, intensity=0.5, raw_value=100.0),
            GridCell(time_ms=1700000060000, price=50010.0, intensity=0.7, raw_value=150.0),
        ]

        # Set data
        await bridge.set_heatmap_data(cells)

        # Show
        await bridge.set_visible(True)

        web_view.show()
        app.exec()

    asyncio.run(_example())
