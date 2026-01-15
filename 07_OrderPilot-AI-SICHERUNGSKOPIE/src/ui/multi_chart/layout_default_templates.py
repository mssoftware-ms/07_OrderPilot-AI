"""Layout Default Templates - Builder Functions for Standard Layouts.

Refactored from layout_manager.py.

Contains:
- create_default_layouts: Create all default layouts if none exist
- _build_mtf_layout: Multi-Timeframe Analysis (3 windows, BTC/USD)
- _build_crypto_layout: Crypto Trading (BTC + ETH parallel)
- _build_scalping_layout: Stock Scalping (1-minute chart)
- _build_dual_monitor_layout: Dual Monitor Setup (3 windows across 2 monitors)
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from .layout_config_models import ChartLayoutConfig, ChartWindowConfig

if TYPE_CHECKING:
    from .layout_manager import ChartLayoutManager

logger = logging.getLogger(__name__)


class LayoutDefaultTemplates:
    """Helper for creating default layout templates."""

    def __init__(self, parent: "ChartLayoutManager"):
        self.parent = parent

    def create_default_layouts(self) -> None:
        """Create default layout templates if none exist."""
        if list(self.parent._layouts_dir.glob("*.json")):
            return  # Layouts already exist

        self.parent._persistence.save_layout(self._build_mtf_layout())
        self.parent._persistence.save_layout(self._build_crypto_layout())
        self.parent._persistence.save_layout(self._build_scalping_layout())
        self.parent._persistence.save_layout(self._build_dual_monitor_layout())

        logger.info("Created default chart layouts")

    def _build_mtf_layout(self) -> ChartLayoutConfig:
        """Build Multi-Timeframe Analysis layout (3 windows)."""
        return ChartLayoutConfig(
            name="Multi-Timeframe-Analyse",
            description="Übergeordneter Trend mit 3 Zeitebenen für Pre-Trade Analyse",
            windows=[
                ChartWindowConfig(
                    symbol="BTC/USD",
                    timeframe="1D",
                    period="3M",
                    monitor=0,
                    x=0, y=0,
                    width=800, height=500,
                    indicators=["SMA", "RSI"],
                ),
                ChartWindowConfig(
                    symbol="BTC/USD",
                    timeframe="1H",
                    period="2W",
                    monitor=0,
                    x=800, y=0,
                    width=800, height=500,
                    indicators=["EMA", "MACD"],
                ),
                ChartWindowConfig(
                    symbol="BTC/USD",
                    timeframe="5T",
                    period="2D",
                    monitor=0,
                    x=0, y=500,
                    width=1600, height=500,
                    indicators=["BB", "RSI"],
                    auto_stream=True,
                ),
            ],
            sync_crosshair=True,
        )

    def _build_crypto_layout(self) -> ChartLayoutConfig:
        """Build Crypto Trading layout (BTC + ETH parallel)."""
        return ChartLayoutConfig(
            name="Crypto-Trading",
            description="BTC und ETH parallel mit Live-Stream",
            windows=[
                ChartWindowConfig(
                    symbol="BTC/USD",
                    timeframe="1T",
                    period="1D",
                    monitor=0,
                    x=0, y=0,
                    width=960, height=800,
                    auto_stream=True,
                ),
                ChartWindowConfig(
                    symbol="ETH/USD",
                    timeframe="1T",
                    period="1D",
                    monitor=0,
                    x=960, y=0,
                    width=960, height=800,
                    auto_stream=True,
                ),
            ],
        )

    def _build_scalping_layout(self) -> ChartLayoutConfig:
        """Build Stock Scalping layout (1-minute chart)."""
        return ChartLayoutConfig(
            name="Aktien-Scalping",
            description="Schnelles Trading mit 1-Minuten Chart",
            windows=[
                ChartWindowConfig(
                    symbol="SPY",
                    timeframe="1T",
                    period="1D",
                    monitor=0,
                    x=0, y=0,
                    width=1200, height=900,
                    indicators=["EMA", "RSI", "MACD"],
                    auto_stream=True,
                ),
            ],
        )

    def _build_dual_monitor_layout(self) -> ChartLayoutConfig:
        """Build Dual Monitor Setup layout (3 windows across 2 monitors)."""
        return ChartLayoutConfig(
            name="Dual-Monitor-Setup",
            description="Charts auf 2 Monitoren verteilt",
            windows=[
                ChartWindowConfig(
                    symbol="BTC/USD",
                    timeframe="1H",
                    period="1M",
                    monitor=0,
                    x=0, y=0,
                    width=1920, height=1080,
                    indicators=["SMA", "BB"],
                ),
                ChartWindowConfig(
                    symbol="BTC/USD",
                    timeframe="5T",
                    period="5D",
                    monitor=1,
                    x=0, y=0,
                    width=1920, height=540,
                    auto_stream=True,
                ),
                ChartWindowConfig(
                    symbol="ETH/USD",
                    timeframe="5T",
                    period="5D",
                    monitor=1,
                    x=0, y=540,
                    width=1920, height=540,
                    auto_stream=True,
                ),
            ],
            sync_crosshair=True,
        )
