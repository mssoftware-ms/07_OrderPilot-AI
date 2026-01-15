"""
Leverage Rules Engine - Dynamic Leverage Management

Phase 3.6: Futures/Leverage Rules Integration.

Berechnet dynamischen Max-Leverage basierend auf:
- Asset-Typ (BTC, ETH, Altcoins)
- Market Regime (STRONG_TREND vs CHOP vs VOLATILE)
- Volatilität (ATR-basiert)
- Account Risk Limits
- Liquidation Buffer

Safety-First Design:
- Konservative Defaults
- Multiple Limit-Checks
- Liquidation Distance Validation
"""

from __future__ import annotations

import json
import logging
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .regime_detector import RegimeResult

logger = logging.getLogger(__name__)


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


# =============================================================================
# LEVERAGE RULES ENGINE
# =============================================================================


class LeverageRulesEngine:
    """
    Dynamic leverage calculation with multiple safety checks.

    Workflow:
    1. Determine asset tier
    2. Get base max leverage for tier
    3. Apply regime modifier
    4. Apply volatility modifier
    5. Validate against liquidation distance
    6. Return conservative result

    Safety features:
    - Multiple limit layers
    - Liquidation distance validation
    - Account risk limits
    - Conservative defaults
    """

    # Default asset tier mappings
    DEFAULT_TIER_1 = {"BTC", "BTCUSD", "BTCUSDT", "ETH", "ETHUSD", "ETHUSDT"}
    DEFAULT_TIER_2 = {"SOL", "BNB", "XRP", "ADA", "DOGE", "AVAX", "LINK", "DOT"}
    DEFAULT_TIER_3 = {"MATIC", "ATOM", "LTC", "UNI", "NEAR", "APT", "OP", "ARB"}

    def __init__(self, config: Optional[LeverageRulesConfig] = None):
        """Initialize Leverage Rules Engine."""
        self.config = config or LeverageRulesConfig()
        logger.info("LeverageRulesEngine initialized")

    def calculate_leverage(
        self,
        symbol: str,
        entry_price: float,
        regime_result: Optional["RegimeResult"] = None,
        atr: Optional[float] = None,
        requested_leverage: Optional[int] = None,
        account_balance: Optional[float] = None,
        current_exposure: Optional[float] = None,
    ) -> LeverageResult:
        """
        Calculate recommended leverage for a trade.

        Args:
            symbol: Trading symbol
            entry_price: Expected entry price
            regime_result: Current market regime
            atr: ATR value for volatility calculation
            requested_leverage: User's requested leverage (optional)
            account_balance: Account balance for risk checks
            current_exposure: Current total exposure

        Returns:
            LeverageResult with recommended leverage and breakdown
        """
        warnings = []

        # 1. Determine asset tier
        asset_tier = self._get_asset_tier(symbol)
        tier_limit = self._get_tier_max_leverage(asset_tier)

        # 2. Apply regime modifier
        regime_str = ""
        regime_multiplier = 1.0
        if regime_result:
            regime_str = regime_result.regime.value if hasattr(regime_result.regime, "value") else str(regime_result.regime)
            regime_multiplier = self._get_regime_multiplier(regime_str)

        regime_adjusted = int(tier_limit * regime_multiplier)

        # 3. Apply volatility modifier
        atr_percent = 0.0
        volatility_multiplier = 1.0
        if atr and entry_price > 0:
            atr_percent = (atr / entry_price) * 100
            volatility_multiplier = self._get_volatility_multiplier(atr_percent)

        volatility_adjusted = int(regime_adjusted * volatility_multiplier)

        # 4. Apply global cap
        final_limit = min(
            volatility_adjusted,
            self.config.max_leverage_global
        )
        final_limit = max(final_limit, self.config.min_leverage)

        # 5. Validate liquidation distance
        liq_long, liq_short = self._calculate_liquidation_prices(entry_price, final_limit)
        liq_distance_pct = (1 / final_limit) * 100 if final_limit > 0 else 100

        if liq_distance_pct < self.config.min_liquidation_distance_pct:
            # Reduce leverage to meet liquidation distance requirement
            safe_leverage = int(100 / self.config.min_liquidation_distance_pct)
            final_limit = min(final_limit, safe_leverage)
            warnings.append(f"Leverage reduced for liquidation safety (min {self.config.min_liquidation_distance_pct}% distance)")

        # 6. Account risk checks
        if account_balance and account_balance > 0:
            # Check position size risk
            max_position = account_balance * (self.config.max_position_risk_pct / 100) * final_limit
            # This is informational - actual position sizing is done elsewhere

            # Check daily exposure
            if current_exposure:
                exposure_pct = (current_exposure / account_balance) * 100
                if exposure_pct >= self.config.max_daily_exposure_pct:
                    return LeverageResult(
                        recommended_leverage=0,
                        max_allowed_leverage=final_limit,
                        action=LeverageAction.BLOCKED,
                        reason=f"Daily exposure limit reached ({exposure_pct:.1f}% / {self.config.max_daily_exposure_pct}%)",
                        tier_limit=tier_limit,
                        regime_adjusted=regime_adjusted,
                        volatility_adjusted=volatility_adjusted,
                        final_limit=final_limit,
                        liquidation_price_long=liq_long,
                        liquidation_price_short=liq_short,
                        liquidation_distance_pct=liq_distance_pct,
                        symbol=symbol,
                        asset_tier=asset_tier.value,
                        regime=regime_str,
                        atr_percent=atr_percent,
                        warnings=["Daily exposure limit reached"],
                    )

        # 7. Compare with requested leverage
        recommended = final_limit
        action = LeverageAction.APPROVED

        if requested_leverage:
            if requested_leverage > final_limit:
                action = LeverageAction.REDUCED
                warnings.append(f"Requested {requested_leverage}x reduced to {final_limit}x")
            else:
                recommended = requested_leverage

        # Build reason string
        reasons = []
        if tier_limit != final_limit:
            reasons.append(f"Tier {asset_tier.value}: {tier_limit}x")
        if regime_adjusted != tier_limit:
            reasons.append(f"Regime ({regime_str}): {regime_adjusted}x")
        if volatility_adjusted != regime_adjusted:
            reasons.append(f"Volatility ({atr_percent:.2f}%): {volatility_adjusted}x")

        reason = " → ".join(reasons) if reasons else f"Default: {final_limit}x"

        return LeverageResult(
            recommended_leverage=recommended,
            max_allowed_leverage=final_limit,
            action=action,
            reason=reason,
            tier_limit=tier_limit,
            regime_adjusted=regime_adjusted,
            volatility_adjusted=volatility_adjusted,
            final_limit=final_limit,
            liquidation_price_long=liq_long,
            liquidation_price_short=liq_short,
            liquidation_distance_pct=liq_distance_pct,
            symbol=symbol,
            asset_tier=asset_tier.value,
            regime=regime_str,
            atr_percent=atr_percent,
            warnings=warnings,
        )

    def validate_leverage(
        self,
        leverage: int,
        symbol: str,
        entry_price: float,
        sl_price: float,
        direction: str,
    ) -> tuple[bool, str, List[str]]:
        """
        Validate that a specific leverage is safe for the trade.

        Args:
            leverage: Leverage to validate
            symbol: Trading symbol
            entry_price: Entry price
            sl_price: Stop loss price
            direction: "LONG" or "SHORT"

        Returns:
            Tuple (is_valid, reason, warnings)
        """
        warnings = []

        # Calculate SL distance
        sl_distance_pct = abs(entry_price - sl_price) / entry_price * 100

        # Calculate liquidation distance
        liq_distance_pct = (1 / leverage) * 100 if leverage > 0 else 100

        # Check if SL would hit before liquidation (with buffer)
        required_buffer = self.config.liquidation_buffer_multiplier
        safe_sl_distance = liq_distance_pct / required_buffer

        if sl_distance_pct >= safe_sl_distance:
            return (
                False,
                f"Stop Loss ({sl_distance_pct:.2f}%) too wide for {leverage}x leverage. "
                f"Max SL at {leverage}x: {safe_sl_distance:.2f}%",
                [f"SL exceeds safe distance ({safe_sl_distance:.2f}%)"],
            )

        # Calculate liquidation prices
        liq_long, liq_short = self._calculate_liquidation_prices(entry_price, leverage)

        # Validate SL is inside liquidation
        if direction == "LONG":
            if sl_price <= liq_long:
                return (
                    False,
                    f"Stop Loss ({sl_price:.2f}) is at or below liquidation ({liq_long:.2f})",
                    ["SL at/below liquidation price"],
                )
        else:
            if sl_price >= liq_short:
                return (
                    False,
                    f"Stop Loss ({sl_price:.2f}) is at or above liquidation ({liq_short:.2f})",
                    ["SL at/above liquidation price"],
                )

        # Check tier limits
        asset_tier = self._get_asset_tier(symbol)
        tier_max = self._get_tier_max_leverage(asset_tier)

        if leverage > tier_max:
            warnings.append(f"Leverage exceeds tier limit ({tier_max}x for {asset_tier.value})")

        if leverage > self.config.max_leverage_global:
            return (
                False,
                f"Leverage {leverage}x exceeds global max ({self.config.max_leverage_global}x)",
                warnings,
            )

        # All checks passed
        return True, "Leverage validated", warnings

    def get_safe_leverage_for_sl(
        self,
        entry_price: float,
        sl_price: float,
        symbol: str,
    ) -> int:
        """
        Calculate safe leverage based on stop loss distance.

        Args:
            entry_price: Entry price
            sl_price: Stop loss price
            symbol: Trading symbol

        Returns:
            Safe leverage value
        """
        sl_distance_pct = abs(entry_price - sl_price) / entry_price * 100

        if sl_distance_pct <= 0:
            return self.config.min_leverage

        # Calculate max leverage where SL is inside liquidation with buffer
        buffer = self.config.liquidation_buffer_multiplier
        max_leverage_for_sl = int(100 / (sl_distance_pct * buffer))

        # Apply tier limits
        asset_tier = self._get_asset_tier(symbol)
        tier_max = self._get_tier_max_leverage(asset_tier)

        # Return minimum of calculated and tier limit
        safe_leverage = min(max_leverage_for_sl, tier_max, self.config.max_leverage_global)
        safe_leverage = max(safe_leverage, self.config.min_leverage)

        return safe_leverage

    # =========================================================================
    # PRIVATE HELPERS
    # =========================================================================

    def _get_asset_tier(self, symbol: str) -> AssetTier:
        """Determine asset tier for symbol."""
        # Check overrides first
        symbol_upper = symbol.upper()
        if symbol_upper in self.config.asset_tier_overrides:
            tier_str = self.config.asset_tier_overrides[symbol_upper]
            try:
                return AssetTier(tier_str)
            except ValueError:
                pass

        # Extract base asset from symbol
        base = symbol_upper.replace("USDT", "").replace("USD", "").replace("PERP", "")

        if base in self.DEFAULT_TIER_1 or symbol_upper in self.DEFAULT_TIER_1:
            return AssetTier.TIER_1
        elif base in self.DEFAULT_TIER_2:
            return AssetTier.TIER_2
        elif base in self.DEFAULT_TIER_3:
            return AssetTier.TIER_3
        else:
            return AssetTier.TIER_4

    def _get_tier_max_leverage(self, tier: AssetTier) -> int:
        """Get max leverage for tier."""
        tier_map = {
            AssetTier.TIER_1: self.config.max_leverage_tier_1,
            AssetTier.TIER_2: self.config.max_leverage_tier_2,
            AssetTier.TIER_3: self.config.max_leverage_tier_3,
            AssetTier.TIER_4: self.config.max_leverage_tier_4,
        }
        return tier_map.get(tier, self.config.default_leverage)

    def _get_regime_multiplier(self, regime_str: str) -> float:
        """Get regime-based leverage multiplier."""
        regime_upper = regime_str.upper()

        if "STRONG_TREND" in regime_upper:
            return self.config.regime_multiplier_strong_trend
        elif "WEAK_TREND" in regime_upper:
            return self.config.regime_multiplier_weak_trend
        elif "CHOP" in regime_upper or "RANGE" in regime_upper:
            return self.config.regime_multiplier_chop
        elif "VOLATIL" in regime_upper or "EXPLOSIVE" in regime_upper:
            return self.config.regime_multiplier_volatile
        else:
            return self.config.regime_multiplier_neutral

    def _get_volatility_multiplier(self, atr_percent: float) -> float:
        """Get volatility-based leverage multiplier."""
        if atr_percent <= self.config.atr_low_threshold_pct:
            return self.config.volatility_low_multiplier
        elif atr_percent >= self.config.atr_high_threshold_pct:
            return self.config.volatility_high_multiplier
        else:
            # Linear interpolation between thresholds
            range_pct = self.config.atr_high_threshold_pct - self.config.atr_low_threshold_pct
            position = (atr_percent - self.config.atr_low_threshold_pct) / range_pct
            return self.config.volatility_low_multiplier - (
                position * (self.config.volatility_low_multiplier - self.config.volatility_high_multiplier)
            )

    def _calculate_liquidation_prices(
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

    def update_config(self, config: LeverageRulesConfig) -> None:
        """Update engine configuration."""
        self.config = config
        logger.info("LeverageRulesEngine config updated")


# =============================================================================
# GLOBAL SINGLETON & FACTORY
# =============================================================================

_global_engine: Optional[LeverageRulesEngine] = None
_engine_lock = threading.Lock()


def get_leverage_rules_engine(config: Optional[LeverageRulesConfig] = None) -> LeverageRulesEngine:
    """Get global LeverageRulesEngine singleton."""
    global _global_engine

    with _engine_lock:
        if _global_engine is None:
            _global_engine = LeverageRulesEngine(config)
            logger.info("Global LeverageRulesEngine created")
        return _global_engine


def calculate_leverage(
    symbol: str,
    entry_price: float,
    regime_result: Optional["RegimeResult"] = None,
    atr: Optional[float] = None,
) -> LeverageResult:
    """Convenience function to calculate leverage."""
    engine = get_leverage_rules_engine()
    return engine.calculate_leverage(symbol, entry_price, regime_result, atr)


def load_leverage_config(path: Optional[Path] = None) -> LeverageRulesConfig:
    """Load config from JSON file."""
    if path is None:
        path = Path("config/leverage_rules_config.json")

    if path.exists():
        try:
            with open(path, "r") as f:
                data = json.load(f)
            return LeverageRulesConfig.from_dict(data)
        except Exception as e:
            logger.warning(f"Failed to load leverage config: {e}")

    return LeverageRulesConfig()


def save_leverage_config(config: LeverageRulesConfig, path: Optional[Path] = None) -> bool:
    """Save config to JSON file."""
    if path is None:
        path = Path("config/leverage_rules_config.json")

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(config.to_dict(), f, indent=2)
        logger.info(f"Leverage config saved to {path}")
        return True
    except Exception as e:
        logger.error(f"Failed to save leverage config: {e}")
        return False
