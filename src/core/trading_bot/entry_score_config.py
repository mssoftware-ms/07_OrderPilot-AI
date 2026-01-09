"""
Entry Score Config - Configuration Management

Handles entry score configuration:
- EntryScoreConfig dataclass with validation
- Component weight management
- Threshold settings
- Indicator parameters
- Regime modifiers
- Gate settings
- Load/save functions for persistence

Module 2/4 of entry_score_engine.py split (Lines 70-212, 1152-1198)
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================


@dataclass
class EntryScoreConfig:
    """Configuration for Entry Score calculation."""

    # Component Weights (must sum to 1.0)
    weight_trend_alignment: float = 0.25    # EMA Stack
    weight_momentum_rsi: float = 0.15       # RSI positioning
    weight_momentum_macd: float = 0.15      # MACD crossover/histogram
    weight_trend_strength: float = 0.20     # ADX
    weight_volatility: float = 0.10         # BB/ATR
    weight_volume: float = 0.15             # Volume confirmation

    # Thresholds for quality tiers
    threshold_excellent: float = 0.80
    threshold_good: float = 0.65
    threshold_moderate: float = 0.50
    threshold_weak: float = 0.35

    # Minimum score for valid signal
    min_score_for_entry: float = 0.50

    # Indicator Parameters
    ema_short: int = 20
    ema_medium: int = 50
    ema_long: int = 200
    rsi_period: int = 14
    rsi_overbought: int = 70
    rsi_oversold: int = 30
    adx_strong_trend: float = 25.0
    adx_weak_trend: float = 15.0
    atr_period: int = 14

    # Regime-based modifiers
    regime_boost_strong_trend: float = 0.10    # Boost in strong trend
    regime_penalty_chop: float = -0.15         # Penalty in chop/range
    regime_penalty_volatile: float = -0.10     # Penalty in explosive volatility

    # Gate settings
    block_in_chop_range: bool = True
    block_against_strong_trend: bool = True
    allow_counter_trend_sfp: bool = True  # Allow SFP (Swing Failure Pattern) setups

    def validate(self) -> bool:
        """Validate config - weights must sum to ~1.0."""
        total = (
            self.weight_trend_alignment +
            self.weight_momentum_rsi +
            self.weight_momentum_macd +
            self.weight_trend_strength +
            self.weight_volatility +
            self.weight_volume
        )
        if not (0.99 <= total <= 1.01):
            logger.warning(f"Entry score weights sum to {total:.2f}, should be 1.0")
            return False
        return True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "weights": {
                "trend_alignment": self.weight_trend_alignment,
                "momentum_rsi": self.weight_momentum_rsi,
                "momentum_macd": self.weight_momentum_macd,
                "trend_strength": self.weight_trend_strength,
                "volatility": self.weight_volatility,
                "volume": self.weight_volume,
            },
            "thresholds": {
                "excellent": self.threshold_excellent,
                "good": self.threshold_good,
                "moderate": self.threshold_moderate,
                "weak": self.threshold_weak,
                "min_for_entry": self.min_score_for_entry,
            },
            "indicators": {
                "ema_short": self.ema_short,
                "ema_medium": self.ema_medium,
                "ema_long": self.ema_long,
                "rsi_period": self.rsi_period,
                "rsi_overbought": self.rsi_overbought,
                "rsi_oversold": self.rsi_oversold,
                "adx_strong_trend": self.adx_strong_trend,
                "adx_weak_trend": self.adx_weak_trend,
            },
            "regime_modifiers": {
                "boost_strong_trend": self.regime_boost_strong_trend,
                "penalty_chop": self.regime_penalty_chop,
                "penalty_volatile": self.regime_penalty_volatile,
            },
            "gates": {
                "block_in_chop_range": self.block_in_chop_range,
                "block_against_strong_trend": self.block_against_strong_trend,
                "allow_counter_trend_sfp": self.allow_counter_trend_sfp,
            }
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EntryScoreConfig":
        """Create from dictionary."""
        config = cls()

        if "weights" in data:
            w = data["weights"]
            config.weight_trend_alignment = w.get("trend_alignment", config.weight_trend_alignment)
            config.weight_momentum_rsi = w.get("momentum_rsi", config.weight_momentum_rsi)
            config.weight_momentum_macd = w.get("momentum_macd", config.weight_momentum_macd)
            config.weight_trend_strength = w.get("trend_strength", config.weight_trend_strength)
            config.weight_volatility = w.get("volatility", config.weight_volatility)
            config.weight_volume = w.get("volume", config.weight_volume)

        if "thresholds" in data:
            t = data["thresholds"]
            config.threshold_excellent = t.get("excellent", config.threshold_excellent)
            config.threshold_good = t.get("good", config.threshold_good)
            config.threshold_moderate = t.get("moderate", config.threshold_moderate)
            config.threshold_weak = t.get("weak", config.threshold_weak)
            config.min_score_for_entry = t.get("min_for_entry", config.min_score_for_entry)

        if "indicators" in data:
            i = data["indicators"]
            config.ema_short = i.get("ema_short", config.ema_short)
            config.ema_medium = i.get("ema_medium", config.ema_medium)
            config.ema_long = i.get("ema_long", config.ema_long)
            config.rsi_period = i.get("rsi_period", config.rsi_period)
            config.rsi_overbought = i.get("rsi_overbought", config.rsi_overbought)
            config.rsi_oversold = i.get("rsi_oversold", config.rsi_oversold)
            config.adx_strong_trend = i.get("adx_strong_trend", config.adx_strong_trend)
            config.adx_weak_trend = i.get("adx_weak_trend", config.adx_weak_trend)

        if "regime_modifiers" in data:
            r = data["regime_modifiers"]
            config.regime_boost_strong_trend = r.get("boost_strong_trend", config.regime_boost_strong_trend)
            config.regime_penalty_chop = r.get("penalty_chop", config.regime_penalty_chop)
            config.regime_penalty_volatile = r.get("penalty_volatile", config.regime_penalty_volatile)

        if "gates" in data:
            g = data["gates"]
            config.block_in_chop_range = g.get("block_in_chop_range", config.block_in_chop_range)
            config.block_against_strong_trend = g.get("block_against_strong_trend", config.block_against_strong_trend)
            config.allow_counter_trend_sfp = g.get("allow_counter_trend_sfp", config.allow_counter_trend_sfp)

        return config


# =============================================================================
# LOAD/SAVE FUNCTIONS
# =============================================================================


def load_entry_score_config(path: Optional[Path] = None) -> EntryScoreConfig:
    """
    Load entry score config from JSON file.

    Args:
        path: Config file path (default: config/entry_score_config.json)

    Returns:
        Loaded or default config
    """
    if path is None:
        path = Path("config/entry_score_config.json")

    if path.exists():
        try:
            with open(path, "r") as f:
                data = json.load(f)
            return EntryScoreConfig.from_dict(data)
        except Exception as e:
            logger.warning(f"Failed to load entry score config: {e}")

    return EntryScoreConfig()


def save_entry_score_config(config: EntryScoreConfig, path: Optional[Path] = None) -> bool:
    """
    Save entry score config to JSON file.

    Args:
        config: Config to save
        path: Target path (default: config/entry_score_config.json)

    Returns:
        True if saved successfully
    """
    if path is None:
        path = Path("config/entry_score_config.json")

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(config.to_dict(), f, indent=2)
        logger.info(f"Entry score config saved to {path}")
        return True
    except Exception as e:
        logger.error(f"Failed to save entry score config: {e}")
        return False
