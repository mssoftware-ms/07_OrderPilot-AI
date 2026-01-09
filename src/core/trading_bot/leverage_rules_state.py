"""Leverage Rules State - Enums, Config, Result dataclasses.

Refactored from 694 LOC monolith using composition pattern.

Module 1/3 of leverage_rules.py split.

Contains:
- AssetTier: Asset risk tier enum
- LeverageAction: Action taken enum
- LeverageRulesConfig: Configuration dataclass
- LeverageResult: Result dataclass
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


# =============================================================================
# ENUMS
# =============================================================================


class AssetTier(str, Enum):
    """Asset risk tier based on liquidity and volatility."""
    TIER_1 = "tier_1"    # BTC, ETH - highest liquidity
    TIER_2 = "tier_2"    # Major altcoins (SOL, BNB, XRP)
    TIER_3 = "tier_3"    # Mid-cap altcoins
    TIER_4 = "tier_4"    # Small-cap, high volatility


class LeverageAction(str, Enum):
    """Action taken by leverage calculation."""
    APPROVED = "approved"
    REDUCED = "reduced"
    BLOCKED = "blocked"


# =============================================================================
# CONFIG
# =============================================================================


@dataclass
class LeverageRulesConfig:
    """Configuration for Leverage Rules Engine."""

    # Global limits
    max_leverage_global: int = 20          # Absolute maximum
    default_leverage: int = 5              # Default if no specific rules apply
    min_leverage: int = 1                  # Minimum leverage

    # Per-tier max leverage (conservative defaults)
    max_leverage_tier_1: int = 20          # BTC/ETH
    max_leverage_tier_2: int = 15          # Major alts
    max_leverage_tier_3: int = 10          # Mid-cap
    max_leverage_tier_4: int = 5           # Small-cap

    # Regime-based modifiers (multipliers on max)
    regime_multiplier_strong_trend: float = 1.0     # Full leverage in trend
    regime_multiplier_weak_trend: float = 0.8       # 80% in weak trend
    regime_multiplier_neutral: float = 0.6          # 60% in neutral
    regime_multiplier_chop: float = 0.4             # 40% in chop
    regime_multiplier_volatile: float = 0.3         # 30% in explosive volatility

    # Volatility adjustments
    atr_low_threshold_pct: float = 1.0      # < 1% ATR = low vol
    atr_high_threshold_pct: float = 3.0     # > 3% ATR = high vol
    volatility_low_multiplier: float = 1.2   # Increase leverage in low vol
    volatility_high_multiplier: float = 0.5  # Decrease in high vol

    # Liquidation safety
    min_liquidation_distance_pct: float = 5.0   # Min % distance to liquidation
    liquidation_buffer_multiplier: float = 1.5   # Extra buffer

    # Account risk limits
    max_position_risk_pct: float = 2.0       # Max % of account at risk per trade
    max_daily_exposure_pct: float = 20.0     # Max total exposure per day
    max_concurrent_positions: int = 3         # Max positions open

    # Asset mappings (symbol -> tier)
    asset_tier_overrides: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "global": {
                "max_leverage": self.max_leverage_global,
                "default_leverage": self.default_leverage,
                "min_leverage": self.min_leverage,
            },
            "tiers": {
                "tier_1": self.max_leverage_tier_1,
                "tier_2": self.max_leverage_tier_2,
                "tier_3": self.max_leverage_tier_3,
                "tier_4": self.max_leverage_tier_4,
            },
            "regime_multipliers": {
                "strong_trend": self.regime_multiplier_strong_trend,
                "weak_trend": self.regime_multiplier_weak_trend,
                "neutral": self.regime_multiplier_neutral,
                "chop": self.regime_multiplier_chop,
                "volatile": self.regime_multiplier_volatile,
            },
            "volatility": {
                "atr_low_threshold_pct": self.atr_low_threshold_pct,
                "atr_high_threshold_pct": self.atr_high_threshold_pct,
                "low_multiplier": self.volatility_low_multiplier,
                "high_multiplier": self.volatility_high_multiplier,
            },
            "liquidation": {
                "min_distance_pct": self.min_liquidation_distance_pct,
                "buffer_multiplier": self.liquidation_buffer_multiplier,
            },
            "account_limits": {
                "max_position_risk_pct": self.max_position_risk_pct,
                "max_daily_exposure_pct": self.max_daily_exposure_pct,
                "max_concurrent_positions": self.max_concurrent_positions,
            },
            "asset_tier_overrides": self.asset_tier_overrides,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LeverageRulesConfig":
        """Create from dictionary."""
        config = cls()

        if "global" in data:
            g = data["global"]
            config.max_leverage_global = g.get("max_leverage", config.max_leverage_global)
            config.default_leverage = g.get("default_leverage", config.default_leverage)
            config.min_leverage = g.get("min_leverage", config.min_leverage)

        if "tiers" in data:
            t = data["tiers"]
            config.max_leverage_tier_1 = t.get("tier_1", config.max_leverage_tier_1)
            config.max_leverage_tier_2 = t.get("tier_2", config.max_leverage_tier_2)
            config.max_leverage_tier_3 = t.get("tier_3", config.max_leverage_tier_3)
            config.max_leverage_tier_4 = t.get("tier_4", config.max_leverage_tier_4)

        if "regime_multipliers" in data:
            r = data["regime_multipliers"]
            config.regime_multiplier_strong_trend = r.get("strong_trend", config.regime_multiplier_strong_trend)
            config.regime_multiplier_weak_trend = r.get("weak_trend", config.regime_multiplier_weak_trend)
            config.regime_multiplier_neutral = r.get("neutral", config.regime_multiplier_neutral)
            config.regime_multiplier_chop = r.get("chop", config.regime_multiplier_chop)
            config.regime_multiplier_volatile = r.get("volatile", config.regime_multiplier_volatile)

        if "volatility" in data:
            v = data["volatility"]
            config.atr_low_threshold_pct = v.get("atr_low_threshold_pct", config.atr_low_threshold_pct)
            config.atr_high_threshold_pct = v.get("atr_high_threshold_pct", config.atr_high_threshold_pct)
            config.volatility_low_multiplier = v.get("low_multiplier", config.volatility_low_multiplier)
            config.volatility_high_multiplier = v.get("high_multiplier", config.volatility_high_multiplier)

        if "liquidation" in data:
            l = data["liquidation"]
            config.min_liquidation_distance_pct = l.get("min_distance_pct", config.min_liquidation_distance_pct)
            config.liquidation_buffer_multiplier = l.get("buffer_multiplier", config.liquidation_buffer_multiplier)

        if "account_limits" in data:
            a = data["account_limits"]
            config.max_position_risk_pct = a.get("max_position_risk_pct", config.max_position_risk_pct)
            config.max_daily_exposure_pct = a.get("max_daily_exposure_pct", config.max_daily_exposure_pct)
            config.max_concurrent_positions = a.get("max_concurrent_positions", config.max_concurrent_positions)

        if "asset_tier_overrides" in data:
            config.asset_tier_overrides = data["asset_tier_overrides"]

        return config


# =============================================================================
# RESULT DATACLASS
# =============================================================================


@dataclass
class LeverageResult:
    """Result of leverage calculation."""

    # Calculated leverage
    recommended_leverage: int
    max_allowed_leverage: int

    # Action taken
    action: LeverageAction
    reason: str

    # Breakdown of limits applied
    tier_limit: int
    regime_adjusted: int
    volatility_adjusted: int
    final_limit: int

    # Risk metrics
    liquidation_price_long: Optional[float] = None
    liquidation_price_short: Optional[float] = None
    liquidation_distance_pct: float = 0.0

    # Context
    symbol: str = ""
    asset_tier: str = ""
    regime: str = ""
    atr_percent: float = 0.0

    # Warnings
    warnings: List[str] = field(default_factory=list)

    @property
    def is_safe(self) -> bool:
        """Check if leverage is within safe limits."""
        return self.action != LeverageAction.BLOCKED and len(self.warnings) == 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "recommended_leverage": self.recommended_leverage,
            "max_allowed_leverage": self.max_allowed_leverage,
            "action": self.action.value,
            "reason": self.reason,
            "breakdown": {
                "tier_limit": self.tier_limit,
                "regime_adjusted": self.regime_adjusted,
                "volatility_adjusted": self.volatility_adjusted,
                "final_limit": self.final_limit,
            },
            "risk": {
                "liquidation_price_long": self.liquidation_price_long,
                "liquidation_price_short": self.liquidation_price_short,
                "liquidation_distance_pct": round(self.liquidation_distance_pct, 2),
            },
            "context": {
                "symbol": self.symbol,
                "asset_tier": self.asset_tier,
                "regime": self.regime,
                "atr_percent": round(self.atr_percent, 3),
            },
            "warnings": self.warnings,
            "is_safe": self.is_safe,
        }
