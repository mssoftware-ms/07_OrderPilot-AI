"""
Backtest Execution Phases.

This module contains the phase-based execution logic for backtesting,
extracted from BacktestEngine.run() to reduce complexity.
"""

from .setup_phase import SetupPhase
from .simulation_phase import SimulationPhase
from .teardown_phase import TeardownPhase

__all__ = ['SetupPhase', 'SimulationPhase', 'TeardownPhase']
