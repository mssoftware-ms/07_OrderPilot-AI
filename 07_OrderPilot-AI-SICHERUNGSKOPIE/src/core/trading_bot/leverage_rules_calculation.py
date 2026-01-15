"""Leverage Rules Calculation - Main calculation methods.

Refactored from 694 LOC monolith using composition pattern.

Module 3/3 of leverage_rules.py split.

Contains:
- calculate_leverage(): Calculate recommended leverage
- validate_leverage(): Validate leverage safety
- get_safe_leverage_for_sl(): Calculate safe leverage for SL
"""

from __future__ import annotations

from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .regime_detector import RegimeResult
    from .leverage_rules_state import LeverageResult


class LeverageRulesCalculation:
    """Helper für LeverageRulesEngine calculation methods."""

    def __init__(self, parent):
        """
        Args:
            parent: LeverageRulesEngine Instanz
        """
        self.parent = parent

    def calculate_leverage(
        self,
        symbol: str,
        entry_price: float,
        regime_result: Optional["RegimeResult"] = None,
        atr: Optional[float] = None,
        requested_leverage: Optional[int] = None,
        account_balance: Optional[float] = None,
        current_exposure: Optional[float] = None,
    ) -> "LeverageResult":
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
        from .leverage_rules_state import LeverageAction, LeverageResult

        warnings = []

        # 1. Determine asset tier
        asset_tier = self.parent._helpers.get_asset_tier(symbol)
        tier_limit = self.parent._helpers.get_tier_max_leverage(asset_tier)

        # 2. Apply regime modifier
        regime_str = ""
        regime_multiplier = 1.0
        if regime_result:
            regime_str = regime_result.regime.value if hasattr(regime_result.regime, "value") else str(regime_result.regime)
            regime_multiplier = self.parent._helpers.get_regime_multiplier(regime_str)

        regime_adjusted = int(tier_limit * regime_multiplier)

        # 3. Apply volatility modifier
        atr_percent = 0.0
        volatility_multiplier = 1.0
        if atr and entry_price > 0:
            atr_percent = (atr / entry_price) * 100
            volatility_multiplier = self.parent._helpers.get_volatility_multiplier(atr_percent)

        volatility_adjusted = int(regime_adjusted * volatility_multiplier)

        # 4. Apply global cap
        final_limit = min(
            volatility_adjusted,
            self.parent.config.max_leverage_global
        )
        final_limit = max(final_limit, self.parent.config.min_leverage)

        # 5. Validate liquidation distance
        liq_long, liq_short = self.parent._helpers.calculate_liquidation_prices(entry_price, final_limit)
        liq_distance_pct = (1 / final_limit) * 100 if final_limit > 0 else 100

        if liq_distance_pct < self.parent.config.min_liquidation_distance_pct:
            # Reduce leverage to meet liquidation distance requirement
            safe_leverage = int(100 / self.parent.config.min_liquidation_distance_pct)
            final_limit = min(final_limit, safe_leverage)
            warnings.append(f"Leverage reduced for liquidation safety (min {self.parent.config.min_liquidation_distance_pct}% distance)")

        # 6. Account risk checks
        if account_balance and account_balance > 0:
            # Check position size risk
            max_position = account_balance * (self.parent.config.max_position_risk_pct / 100) * final_limit
            # This is informational - actual position sizing is done elsewhere

            # Check daily exposure
            if current_exposure:
                exposure_pct = (current_exposure / account_balance) * 100
                if exposure_pct >= self.parent.config.max_daily_exposure_pct:
                    return LeverageResult(
                        recommended_leverage=0,
                        max_allowed_leverage=final_limit,
                        action=LeverageAction.BLOCKED,
                        reason=f"Daily exposure limit reached ({exposure_pct:.1f}% / {self.parent.config.max_daily_exposure_pct}%)",
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
        required_buffer = self.parent.config.liquidation_buffer_multiplier
        safe_sl_distance = liq_distance_pct / required_buffer

        if sl_distance_pct >= safe_sl_distance:
            return (
                False,
                f"Stop Loss ({sl_distance_pct:.2f}%) too wide for {leverage}x leverage. "
                f"Max SL at {leverage}x: {safe_sl_distance:.2f}%",
                [f"SL exceeds safe distance ({safe_sl_distance:.2f}%)"],
            )

        # Calculate liquidation prices
        liq_long, liq_short = self.parent._helpers.calculate_liquidation_prices(entry_price, leverage)

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
        asset_tier = self.parent._helpers.get_asset_tier(symbol)
        tier_max = self.parent._helpers.get_tier_max_leverage(asset_tier)

        if leverage > tier_max:
            warnings.append(f"Leverage exceeds tier limit ({tier_max}x for {asset_tier.value})")

        if leverage > self.parent.config.max_leverage_global:
            return (
                False,
                f"Leverage {leverage}x exceeds global max ({self.parent.config.max_leverage_global}x)",
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
            return self.parent.config.min_leverage

        # Calculate max leverage where SL is inside liquidation with buffer
        buffer = self.parent.config.liquidation_buffer_multiplier
        max_leverage_for_sl = int(100 / (sl_distance_pct * buffer))

        # Apply tier limits
        asset_tier = self.parent._helpers.get_asset_tier(symbol)
        tier_max = self.parent._helpers.get_tier_max_leverage(asset_tier)

        # Return minimum of calculated and tier limit
        safe_leverage = min(max_leverage_for_sl, tier_max, self.parent.config.max_leverage_global)
        safe_leverage = max(safe_leverage, self.parent.config.min_leverage)

        return safe_leverage
