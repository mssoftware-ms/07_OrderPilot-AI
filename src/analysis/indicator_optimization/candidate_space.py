"""Candidate Space for Indicator Optimization.

Defines the search space for indicator parameters and families.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any

from src.analysis.entry_signals.entry_signal_engine import OptimParams


@dataclass
class ParameterRange:
    """Defines a range or set of choices for a parameter."""

    name: str
    choices: list[Any] = field(default_factory=list)
    min_val: float | None = None
    max_val: float | None = None
    step: float | None = None

    def sample(self) -> Any:
        """Sample a value from this range."""
        if self.choices:
            return random.choice(self.choices)
        if self.min_val is not None and self.max_val is not None:
            if isinstance(self.min_val, int) and isinstance(self.max_val, int):
                return random.randint(self.min_val, self.max_val)
            return random.uniform(self.min_val, self.max_val)
        return None


class CandidateSpace:
    """Defines the search space for optimization."""

    def __init__(self) -> None:
        """Initialize the candidate space with default ranges."""
        self.ranges: dict[str, ParameterRange] = {
            # Core indicators
            "ema_fast": ParameterRange("ema_fast", choices=[10, 14, 20, 30]),
            "ema_slow": ParameterRange("ema_slow", choices=[40, 50, 80]),
            "atr_period": ParameterRange("atr_period", choices=[10, 14, 20]),
            "rsi_period": ParameterRange("rsi_period", choices=[10, 14, 18]),
            "bb_period": ParameterRange("bb_period", choices=[14, 20, 30]),
            "bb_std": ParameterRange("bb_std", choices=[1.8, 2.0, 2.2]),
            "adx_period": ParameterRange("adx_period", choices=[10, 14, 20]),
            
            # Regime thresholds
            "adx_trend": ParameterRange("adx_trend", choices=[16.0, 18.0, 20.0, 22.0]),
            "squeeze_bb_width": ParameterRange("squeeze_bb_width", choices=[0.010, 0.012, 0.014, 0.016]),
            "high_vol_atr_pct": ParameterRange("high_vol_atr_pct", choices=[0.010, 0.012, 0.014, 0.016]),
            
            # Entry thresholds
            "pullback_atr": ParameterRange("pullback_atr", choices=[0.5, 0.7, 0.9, 1.1]),
            "pullback_rsi": ParameterRange("pullback_rsi", choices=[40.0, 45.0, 50.0]),
            "wick_reject": ParameterRange("wick_reject", choices=[0.5, 0.55, 0.6]),
            "bb_entry": ParameterRange("bb_entry", choices=[0.10, 0.15, 0.20]),
            "rsi_oversold": ParameterRange("rsi_oversold", choices=[30.0, 35.0, 40.0]),
            "rsi_overbought": ParameterRange("rsi_overbought", choices=[60.0, 65.0, 70.0]),
            
            # Breakout
            "vol_spike_factor": ParameterRange("vol_spike_factor", choices=[1.1, 1.2, 1.4]),
            "breakout_atr": ParameterRange("breakout_atr", choices=[0.1, 0.2, 0.3]),
            
            # Filters
            "min_confidence": ParameterRange("min_confidence", choices=[0.56, 0.58, 0.60, 0.62]),
            "cooldown_bars": ParameterRange("cooldown_bars", choices=[6, 10, 14]),
            "cluster_window_bars": ParameterRange("cluster_window_bars", choices=[4, 6, 8]),
            
            # Evaluation
            "eval_horizon_bars": ParameterRange("eval_horizon_bars", choices=[30, 40, 60]),
            "eval_tp_atr": ParameterRange("eval_tp_atr", choices=[0.8, 1.0, 1.2]),
            "eval_sl_atr": ParameterRange("eval_sl_atr", choices=[0.6, 0.8, 1.0]),
        }

    def sample_params(self, base_params: OptimParams) -> OptimParams:
        """Sample a new set of parameters based on the defined ranges.
        
        Args:
            base_params: The base parameters object to copy and update.
            
        Returns:
            A new OptimParams instance with sampled values.
        """
        # Create a copy of base params
        new_params = OptimParams(**vars(base_params))
        
        # Update with sampled values
        for name, param_range in self.ranges.items():
            val = param_range.sample()
            if val is not None and hasattr(new_params, name):
                setattr(new_params, name, val)
                
        return new_params
