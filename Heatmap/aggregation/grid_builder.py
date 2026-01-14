"""
Heatmap Grid Builder

Converts liquidation events into a 2D grid suitable for heatmap rendering.
Handles automatic resolution calculation and incremental updates.
"""

import logging
import math
from dataclasses import dataclass
from typing import List, Tuple, Optional

import numpy as np

from ..storage.sqlite_store import QueryWindow, LiquidationStore
from .normalization import normalize_intensity, NormalizationType


logger = logging.getLogger(__name__)


@dataclass
class GridConfig:
    """Configuration for heatmap grid generation."""

    price_min: float  # Minimum price (low of window)
    price_max: float  # Maximum price (high of window)
    time_start_ms: int  # Start timestamp
    time_end_ms: int  # End timestamp
    rows: int  # Number of price bins
    cols: int  # Number of time bins
    tick_size: float = 0.01  # Minimum price increment

    @property
    def price_bin_size(self) -> float:
        """Calculate price bin size, rounded to tick_size."""
        if self.rows <= 0:
            return 0.0

        price_range = self.price_max - self.price_min
        raw_bin = price_range / self.rows

        # Round up to nearest tick_size multiple
        if self.tick_size > 0:
            return math.ceil(raw_bin / self.tick_size) * self.tick_size
        return raw_bin

    @property
    def time_bin_size_ms(self) -> int:
        """Calculate time bin size in milliseconds."""
        if self.cols <= 0:
            return 0

        time_range = self.time_end_ms - self.time_start_ms
        return math.ceil(time_range / self.cols)

    @classmethod
    def auto_from_window(
        cls,
        window: QueryWindow,
        price_min: float,
        price_max: float,
        window_width: int,
        window_height: int,
        tick_size: float = 0.01,
        target_px_per_bin: float = 2.3,
    ) -> "GridConfig":
        """
        Auto-calculate grid resolution based on window size.

        Args:
            window: Time window
            price_min: Minimum price
            price_max: Maximum price
            window_width: Chart window width in pixels
            window_height: Chart window height in pixels
            tick_size: Minimum price increment
            target_px_per_bin: Target pixels per grid cell

        Returns:
            GridConfig with auto-calculated rows/cols
        """
        # Calculate target rows and cols
        rows = max(1, min(round(window_height / target_px_per_bin), 380))
        cols = max(1, min(round(window_width / (target_px_per_bin / 2)), 1700))

        return cls(
            price_min=price_min,
            price_max=price_max,
            time_start_ms=window.start_ms,
            time_end_ms=window.end_ms,
            rows=rows,
            cols=cols,
            tick_size=tick_size,
        )


@dataclass
class GridCell:
    """Single cell in heatmap grid."""

    time_ms: int  # Cell time (bin center)
    price: float  # Cell price (bin center)
    intensity: float  # Normalized intensity [0, 1]
    raw_value: float  # Raw aggregated value before normalization


class GridBuilder:
    """
    Builds heatmap grid from liquidation events.

    Aggregates events into 2D grid cells and applies normalization.
    """

    def __init__(self, store: LiquidationStore):
        """
        Initialize grid builder.

        Args:
            store: Liquidation event store
        """
        self.store = store

    def build_grid(
        self,
        config: GridConfig,
        window: QueryWindow,
        normalization: NormalizationType = NormalizationType.SQRT,
        weight_by: str = "notional",  # "notional", "qty", or "count"
    ) -> Tuple[np.ndarray, List[GridCell]]:
        """
        Build heatmap grid from stored events.

        Args:
            config: Grid configuration
            window: Query window
            normalization: Intensity normalization type
            weight_by: How to aggregate events ("notional", "qty", "count")

        Returns:
            Tuple of (raw_grid, cells):
                - raw_grid: 2D numpy array (rows × cols) with normalized values
                - cells: List of non-zero GridCell objects for rendering
        """
        # Query events from database
        events = self.store.query_events(window)

        if not events:
            logger.debug("No events found in window")
            return np.zeros((config.rows, config.cols)), []

        # Initialize grid
        grid = np.zeros((config.rows, config.cols), dtype=float)

        # Map events to grid cells
        for event_data in events:
            ts_ms, symbol, side, price, qty, notional = event_data

            # Calculate grid indices
            row_idx = self._price_to_row(price, config)
            col_idx = self._time_to_col(ts_ms, config)

            if row_idx < 0 or row_idx >= config.rows:
                continue
            if col_idx < 0 or col_idx >= config.cols:
                continue

            # Aggregate value based on weight_by
            if weight_by == "notional":
                value = notional
            elif weight_by == "qty":
                value = qty
            else:  # count
                value = 1.0

            grid[row_idx, col_idx] += value

        # Normalize intensity
        normalized_grid = normalize_intensity(grid, normalization)

        # Convert to cell list (only non-zero cells)
        cells = self._grid_to_cells(normalized_grid, grid, config)

        logger.debug(f"Built grid: {config.rows}×{config.cols}, {len(cells)} non-zero cells")

        return normalized_grid, cells

    def add_event_to_grid(
        self,
        grid: np.ndarray,
        event_data: Tuple,
        config: GridConfig,
        weight_by: str = "notional",
    ) -> Optional[Tuple[int, int]]:
        """
        Add single event to existing grid (for live updates).

        Args:
            grid: Existing grid array (modified in-place)
            event_data: Event tuple (ts_ms, symbol, side, price, qty, notional)
            config: Grid configuration
            weight_by: Aggregation method

        Returns:
            (row, col) indices if event added, None if out of bounds
        """
        ts_ms, symbol, side, price, qty, notional = event_data

        row_idx = self._price_to_row(price, config)
        col_idx = self._time_to_col(ts_ms, config)

        if row_idx < 0 or row_idx >= config.rows:
            return None
        if col_idx < 0 or col_idx >= config.cols:
            return None

        # Aggregate value
        if weight_by == "notional":
            value = notional
        elif weight_by == "qty":
            value = qty
        else:
            value = 1.0

        grid[row_idx, col_idx] += value

        return (row_idx, col_idx)

    def _price_to_row(self, price: float, config: GridConfig) -> int:
        """Map price to grid row index (0 = bottom = min price)."""
        if config.price_max <= config.price_min:
            return 0

        # Normalize price to [0, 1]
        normalized = (price - config.price_min) / (config.price_max - config.price_min)

        # Map to row (flip so row 0 is bottom)
        row = int(normalized * config.rows)

        return max(0, min(row, config.rows - 1))

    def _time_to_col(self, ts_ms: int, config: GridConfig) -> int:
        """Map timestamp to grid column index (0 = left = start time)."""
        if config.time_end_ms <= config.time_start_ms:
            return 0

        # Normalize time to [0, 1]
        normalized = (ts_ms - config.time_start_ms) / (config.time_end_ms - config.time_start_ms)

        # Map to column
        col = int(normalized * config.cols)

        return max(0, min(col, config.cols - 1))

    def _row_to_price(self, row: int, config: GridConfig) -> float:
        """Map grid row to price (center of bin)."""
        normalized = (row + 0.5) / config.rows
        return config.price_min + normalized * (config.price_max - config.price_min)

    def _col_to_time(self, col: int, config: GridConfig) -> int:
        """Map grid column to timestamp (center of bin)."""
        normalized = (col + 0.5) / config.cols
        time_range = config.time_end_ms - config.time_start_ms
        return config.time_start_ms + int(normalized * time_range)

    def _grid_to_cells(
        self,
        normalized_grid: np.ndarray,
        raw_grid: np.ndarray,
        config: GridConfig,
        min_intensity: float = 0.01,
    ) -> List[GridCell]:
        """
        Convert grid array to list of GridCell objects.

        Only includes cells with intensity >= min_intensity.
        """
        cells = []

        for row in range(config.rows):
            for col in range(config.cols):
                intensity = normalized_grid[row, col]
                raw_value = raw_grid[row, col]

                if intensity >= min_intensity:
                    cells.append(
                        GridCell(
                            time_ms=self._col_to_time(col, config),
                            price=self._row_to_price(row, config),
                            intensity=intensity,
                            raw_value=raw_value,
                        )
                    )

        return cells


# Example usage
if __name__ == "__main__":
    import asyncio
    from datetime import timedelta
    from ..storage.sqlite_store import LiquidationStore, QueryWindow
    from ..ingestion.binance_forceorder_ws import LiquidationEvent

    async def _example():
        # Create test database
        store = LiquidationStore(db_path="test_grid.db")
        store.connect()
        await store.start()

        # Add test events
        import time
        current_ms = int(time.time() * 1000)

        for i in range(100):
            event = LiquidationEvent(
                ts_ms=current_ms - i * 60000,  # 1 minute intervals
                symbol="BTCUSDT",
                side="SELL" if i % 2 else "BUY",
                price=50000 + (i % 50) * 10,
                qty=0.1,
                notional=5000,
                source="BINANCE_USDM",
                raw_json="{}",
            )
            await store.add_event(event)

        await asyncio.sleep(2)  # Wait for flush

        # Build grid
        window = QueryWindow.from_hours(2, symbol="BTCUSDT")
        config = GridConfig.auto_from_window(
            window=window,
            price_min=49500,
            price_max=50500,
            window_width=1060,
            window_height=550,
            tick_size=0.1,
        )

        builder = GridBuilder(store)
        grid, cells = builder.build_grid(config, window)

        print(f"Grid shape: {grid.shape}")
        print(f"Non-zero cells: {len(cells)}")
        print(f"Sample cells: {cells[:5]}")

        await store.stop()
        store.disconnect()

    logging.basicConfig(level=logging.INFO)
    asyncio.run(_example())
