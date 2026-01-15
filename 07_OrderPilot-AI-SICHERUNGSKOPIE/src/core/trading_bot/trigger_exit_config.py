"""
Trigger & Exit Config - Configuration Management

Handles trigger/exit configuration:
- TriggerExitConfig dataclass with all settings
- Breakout, Pullback, SFP trigger settings
- SL/TP, Trailing Stop, Time Stop settings
- Load/save functions for persistence

Module 2/5 of trigger_exit_engine.py split (Lines 80-241, 1076-1105)
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIG
# =============================================================================


@dataclass
class TriggerExitConfig:
    """Configuration for Trigger and Exit Engine."""

    # Breakout Trigger Settings
    breakout_min_candle_close_pct: float = 0.25  # Min % close beyond level
    breakout_volume_multiplier: float = 1.2      # Min volume vs SMA20
    breakout_confirmation_candles: int = 1       # Candles to confirm

    # Pullback Trigger Settings
    pullback_max_distance_atr: float = 0.5       # Max ATR distance for pullback
    pullback_min_strength: float = 0.3           # Min level strength
    pullback_patience_candles: int = 5           # Candles to wait for pullback

    # SFP Trigger Settings
    sfp_wick_min_pct: float = 0.3                # Min wick beyond level %
    sfp_body_inside_pct: float = 75.0            # Body % must be inside level
    sfp_quick_reversal_candles: int = 2          # Max candles for quick reversal

    # Exit Settings - SL/TP
    sl_type: str = "atr_based"                   # "atr_based" or "percent_based"
    tp_type: str = "atr_based"
    sl_atr_multiplier: float = 1.5
    tp_atr_multiplier: float = 2.5
    sl_percent: float = 0.5                      # Fallback percent
    tp_percent: float = 1.5
    min_risk_reward: float = 1.5                 # Min R:R ratio

    # Exit Settings - Trailing Stop
    trailing_enabled: bool = True
    trailing_type: str = "atr_based"             # "atr_based" or "percent_based"
    trailing_atr_multiplier: float = 1.0
    trailing_percent: float = 0.3
    trailing_activation_profit_pct: float = 0.5  # Activate after X% profit
    trailing_step_percent: float = 0.1           # Min step size

    # Exit Settings - Time Stop
    time_stop_enabled: bool = True
    max_holding_minutes: int = 480               # 8 hours default

    # Exit Settings - Structure Stop
    structure_stop_enabled: bool = True
    structure_stop_buffer_atr: float = 0.2       # Buffer below/above structure

    # Partial Take Profit
    partial_tp_enabled: bool = False
    partial_tp_1_percent: float = 50.0           # Close 50% at TP1
    partial_tp_1_rr: float = 1.0                 # TP1 at 1R
    move_sl_to_be_after_tp1: bool = True         # Move SL to breakeven

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "breakout": {
                "min_candle_close_pct": self.breakout_min_candle_close_pct,
                "volume_multiplier": self.breakout_volume_multiplier,
                "confirmation_candles": self.breakout_confirmation_candles,
            },
            "pullback": {
                "max_distance_atr": self.pullback_max_distance_atr,
                "min_strength": self.pullback_min_strength,
                "patience_candles": self.pullback_patience_candles,
            },
            "sfp": {
                "wick_min_pct": self.sfp_wick_min_pct,
                "body_inside_pct": self.sfp_body_inside_pct,
                "quick_reversal_candles": self.sfp_quick_reversal_candles,
            },
            "sl_tp": {
                "sl_type": self.sl_type,
                "tp_type": self.tp_type,
                "sl_atr_multiplier": self.sl_atr_multiplier,
                "tp_atr_multiplier": self.tp_atr_multiplier,
                "sl_percent": self.sl_percent,
                "tp_percent": self.tp_percent,
                "min_risk_reward": self.min_risk_reward,
            },
            "trailing": {
                "enabled": self.trailing_enabled,
                "type": self.trailing_type,
                "atr_multiplier": self.trailing_atr_multiplier,
                "percent": self.trailing_percent,
                "activation_profit_pct": self.trailing_activation_profit_pct,
                "step_percent": self.trailing_step_percent,
            },
            "time_stop": {
                "enabled": self.time_stop_enabled,
                "max_holding_minutes": self.max_holding_minutes,
            },
            "structure_stop": {
                "enabled": self.structure_stop_enabled,
                "buffer_atr": self.structure_stop_buffer_atr,
            },
            "partial_tp": {
                "enabled": self.partial_tp_enabled,
                "tp1_percent": self.partial_tp_1_percent,
                "tp1_rr": self.partial_tp_1_rr,
                "move_sl_to_be": self.move_sl_to_be_after_tp1,
            }
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TriggerExitConfig":
        """Create from dictionary."""
        config = cls()

        if "breakout" in data:
            b = data["breakout"]
            config.breakout_min_candle_close_pct = b.get("min_candle_close_pct", config.breakout_min_candle_close_pct)
            config.breakout_volume_multiplier = b.get("volume_multiplier", config.breakout_volume_multiplier)
            config.breakout_confirmation_candles = b.get("confirmation_candles", config.breakout_confirmation_candles)

        if "pullback" in data:
            p = data["pullback"]
            config.pullback_max_distance_atr = p.get("max_distance_atr", config.pullback_max_distance_atr)
            config.pullback_min_strength = p.get("min_strength", config.pullback_min_strength)
            config.pullback_patience_candles = p.get("patience_candles", config.pullback_patience_candles)

        if "sfp" in data:
            s = data["sfp"]
            config.sfp_wick_min_pct = s.get("wick_min_pct", config.sfp_wick_min_pct)
            config.sfp_body_inside_pct = s.get("body_inside_pct", config.sfp_body_inside_pct)
            config.sfp_quick_reversal_candles = s.get("quick_reversal_candles", config.sfp_quick_reversal_candles)

        if "sl_tp" in data:
            st = data["sl_tp"]
            config.sl_type = st.get("sl_type", config.sl_type)
            config.tp_type = st.get("tp_type", config.tp_type)
            config.sl_atr_multiplier = st.get("sl_atr_multiplier", config.sl_atr_multiplier)
            config.tp_atr_multiplier = st.get("tp_atr_multiplier", config.tp_atr_multiplier)
            config.sl_percent = st.get("sl_percent", config.sl_percent)
            config.tp_percent = st.get("tp_percent", config.tp_percent)
            config.min_risk_reward = st.get("min_risk_reward", config.min_risk_reward)

        if "trailing" in data:
            t = data["trailing"]
            config.trailing_enabled = t.get("enabled", config.trailing_enabled)
            config.trailing_type = t.get("type", config.trailing_type)
            config.trailing_atr_multiplier = t.get("atr_multiplier", config.trailing_atr_multiplier)
            config.trailing_percent = t.get("percent", config.trailing_percent)
            config.trailing_activation_profit_pct = t.get("activation_profit_pct", config.trailing_activation_profit_pct)
            config.trailing_step_percent = t.get("step_percent", config.trailing_step_percent)

        if "time_stop" in data:
            ts = data["time_stop"]
            config.time_stop_enabled = ts.get("enabled", config.time_stop_enabled)
            config.max_holding_minutes = ts.get("max_holding_minutes", config.max_holding_minutes)

        if "structure_stop" in data:
            ss = data["structure_stop"]
            config.structure_stop_enabled = ss.get("enabled", config.structure_stop_enabled)
            config.structure_stop_buffer_atr = ss.get("buffer_atr", config.structure_stop_buffer_atr)

        if "partial_tp" in data:
            pt = data["partial_tp"]
            config.partial_tp_enabled = pt.get("enabled", config.partial_tp_enabled)
            config.partial_tp_1_percent = pt.get("tp1_percent", config.partial_tp_1_percent)
            config.partial_tp_1_rr = pt.get("tp1_rr", config.partial_tp_1_rr)
            config.move_sl_to_be_after_tp1 = pt.get("move_sl_to_be", config.move_sl_to_be_after_tp1)

        return config


# =============================================================================
# LOAD/SAVE FUNCTIONS
# =============================================================================


def load_trigger_exit_config(path: Optional[Path] = None) -> TriggerExitConfig:
    """Load config from JSON file."""
    if path is None:
        path = Path("config/trigger_exit_config.json")

    if path.exists():
        try:
            with open(path, "r") as f:
                data = json.load(f)
            return TriggerExitConfig.from_dict(data)
        except Exception as e:
            logger.warning(f"Failed to load trigger/exit config: {e}")

    return TriggerExitConfig()


def save_trigger_exit_config(config: TriggerExitConfig, path: Optional[Path] = None) -> bool:
    """Save config to JSON file."""
    if path is None:
        path = Path("config/trigger_exit_config.json")

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(config.to_dict(), f, indent=2)
        logger.info(f"Trigger/Exit config saved to {path}")
        return True
    except Exception as e:
        logger.error(f"Failed to save trigger/exit config: {e}")
        return False
