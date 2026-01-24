"""Compounding component (engine + UI panel)."""

from .calculator import DayResult, MonthKpis, Params, SolveStatus, simulate, solve_daily_profit_pct_for_target

__all__ = [
    "Params",
    "DayResult",
    "MonthKpis",
    "SolveStatus",
    "simulate",
    "solve_daily_profit_pct_for_target",
]
