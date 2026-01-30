"""
Backtest Type Definitions.

Common types used across backtest modules.
"""

from dataclasses import dataclass
import pandas as pd


@dataclass
class Trade:
    """Trade record for backtest results."""
    entry_time: pd.Timestamp
    entry_price: float
    side: str  # 'long' or 'short'
    size: float
    exit_time: pd.Timestamp = None
    exit_price: float = None
    pnl: float = 0.0
    pnl_pct: float = 0.0
    exit_reason: str = ""
