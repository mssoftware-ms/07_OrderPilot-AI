"""Backtesting Module for OrderPilot-AI.

Provides comprehensive backtesting capabilities using Backtrader framework,
integrated with comprehensive backtest models for visualization and analysis.
"""

from .backtrader_integration import (
    BacktestConfig,
    BacktestEngine,
    BacktestResultLegacy,
    BACKTRADER_AVAILABLE,
)

# Import new comprehensive BacktestResult from models
from src.core.models.backtest_models import (
    BacktestMetrics,
    BacktestResult,
    Bar,
    EquityPoint,
    Trade,
    TradeSide,
)

__all__ = [
    # Configuration
    'BacktestConfig',

    # Engine
    'BacktestEngine',
    'BACKTRADER_AVAILABLE',

    # New comprehensive models (preferred)
    'BacktestResult',
    'BacktestMetrics',
    'Bar',
    'Trade',
    'TradeSide',
    'EquityPoint',

    # Legacy model (deprecated)
    'BacktestResultLegacy',
]
