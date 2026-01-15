"""Leverage Rules Helpers - Private helper methods.

Refactored from 694 LOC monolith using composition pattern.

Module 2/3 of leverage_rules.py split.

Contains:
- _get_asset_tier(): Determine asset tier
- _get_tier_max_leverage(): Get tier max leverage
- _get_regime_multiplier(): Get regime multiplier
- _get_volatility_multiplier(): Get volatility multiplier
- _calculate_liquidation_prices(): Calculate liquidation prices
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .leverage_rules_state import AssetTier, LeverageRulesConfig

# Default asset tier mappings
DEFAULT_TIER_1 = {"BTC", "BTCUSD", "BTCUSDT", "ETH", "ETHUSD", "ETHUSDT"}
DEFAULT_TIER_2 = {"SOL", "BNB", "XRP", "ADA", "DOGE", "AVAX", "LINK", "DOT"}
DEFAULT_TIER_3 = {"MATIC", "ATOM", "LTC", "UNI", "NEAR", "APT", "OP", "ARB"}


class LeverageRulesHelpers:
    """Helper für LeverageRulesEngine private methods."""

    def __init__(self, parent):
        """
        Args:
            parent: LeverageRulesEngine Instanz
        """
        self.parent = parent

    def get_asset_tier(self, symbol: str) -> "AssetTier":
        """Determine asset tier for symbol."""
        from .leverage_rules_state import AssetTier

        # Check overrides first
        symbol_upper = symbol.upper()
        if symbol_upper in self.parent.config.asset_tier_overrides:
            tier_str = self.parent.config.asset_tier_overrides[symbol_upper]
            try:
                return AssetTier(tier_str)
            except ValueError:
                pass

        # Extract base asset from symbol
        base = symbol_upper.replace("USDT", "").replace("USD", "").replace("PERP", "")

        if base in DEFAULT_TIER_1 or symbol_upper in DEFAULT_TIER_1:
            return AssetTier.TIER_1
        elif base in DEFAULT_TIER_2:
            return AssetTier.TIER_2
        elif base in DEFAULT_TIER_3:
            return AssetTier.TIER_3
        else:
            return AssetTier.TIER_4

    def get_tier_max_leverage(self, tier: "AssetTier") -> int:
        """Get max leverage for tier."""
        from .leverage_rules_state import AssetTier

        tier_map = {
            AssetTier.TIER_1: self.parent.config.max_leverage_tier_1,
            AssetTier.TIER_2: self.parent.config.max_leverage_tier_2,
            AssetTier.TIER_3: self.parent.config.max_leverage_tier_3,
            AssetTier.TIER_4: self.parent.config.max_leverage_tier_4,
        }
        return tier_map.get(tier, self.parent.config.default_leverage)

    def get_regime_multiplier(self, regime_str: str) -> float:
        """Get regime-based leverage multiplier."""
        regime_upper = regime_str.upper()

        if "STRONG_TREND" in regime_upper:
            return self.parent.config.regime_multiplier_strong_trend
        elif "WEAK_TREND" in regime_upper:
            return self.parent.config.regime_multiplier_weak_trend
        elif "CHOP" in regime_upper or "RANGE" in regime_upper:
            return self.parent.config.regime_multiplier_chop
        elif "VOLATIL" in regime_upper or "EXPLOSIVE" in regime_upper:
            return self.parent.config.regime_multiplier_volatile
        else:
            return self.parent.config.regime_multiplier_neutral

    def get_volatility_multiplier(self, atr_percent: float) -> float:
        """Get volatility-based leverage multiplier."""
        if atr_percent <= self.parent.config.atr_low_threshold_pct:
            return self.parent.config.volatility_low_multiplier
        elif atr_percent >= self.parent.config.atr_high_threshold_pct:
            return self.parent.config.volatility_high_multiplier
        else:
            # Linear interpolation between thresholds
            range_pct = self.parent.config.atr_high_threshold_pct - self.parent.config.atr_low_threshold_pct
            position = (atr_percent - self.parent.config.atr_low_threshold_pct) / range_pct
            return self.parent.config.volatility_low_multiplier - (
                position * (self.parent.config.volatility_low_multiplier - self.parent.config.volatility_high_multiplier)
            )

    def calculate_liquidation_prices(
        self, entry_price: float, leverage: int
    ) -> tuple[float, float]:
        """
        Calculate liquidation prices for long and short positions.

        Simplified calculation (actual varies by exchange):
        Long: entry * (1 - 1/leverage)
        Short: entry * (1 + 1/leverage)
        """
        if leverage <= 0:
            return 0.0, float("inf")

        liq_distance = entry_price / leverage
        liq_long = entry_price - liq_distance
        liq_short = entry_price + liq_distance

        return round(liq_long, 2), round(liq_short, 2)
