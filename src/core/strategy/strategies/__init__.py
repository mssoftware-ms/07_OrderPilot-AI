"""Trading Strategies for OrderPilot-AI.

This package contains various trading strategy implementations.
All strategies inherit from BaseStrategy and can be registered
with the StrategyEngine.
"""

from .trend_following import TrendFollowingStrategy
from .mean_reversion import MeanReversionStrategy
from .momentum import MomentumStrategy
from .breakout import BreakoutStrategy
from .scalping import ScalpingStrategy

__all__ = [
    "TrendFollowingStrategy",
    "MeanReversionStrategy",
    "MomentumStrategy",
    "BreakoutStrategy",
    "ScalpingStrategy",
]
