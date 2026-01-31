"""Column updaters for table display.

This package provides specialized column updaters following the Strategy Pattern
to handle different types of table column updates (status, P&L, fees, etc.).
"""

from __future__ import annotations

from .base_updater import BaseColumnUpdater
from .registry import ColumnUpdaterRegistry
from .price_updater import CurrentPriceUpdater
from .pnl_updater import PnLPercentUpdater, PnLCurrencyUpdater
from .fees_updater import FeesPercentUpdater, FeesCurrencyUpdater
from .position_updater import InvestUpdater, QuantityUpdater, LiquidationUpdater

__all__ = [
    "BaseColumnUpdater",
    "ColumnUpdaterRegistry",
    "CurrentPriceUpdater",
    "PnLPercentUpdater",
    "PnLCurrencyUpdater",
    "FeesPercentUpdater",
    "FeesCurrencyUpdater",
    "InvestUpdater",
    "QuantityUpdater",
    "LiquidationUpdater",
]
