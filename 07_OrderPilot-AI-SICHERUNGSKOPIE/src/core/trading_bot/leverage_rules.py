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

REFACTORED: Split into 3 helper modules using composition pattern:
- leverage_rules_state.py: Enums, Config, Result dataclasses
- leverage_rules_helpers.py: Private helper methods
- leverage_rules_calculation.py: Main calculation methods
"""

from __future__ import annotations

import json
import logging
import threading
from pathlib import Path
from typing import List, Optional, TYPE_CHECKING

from .leverage_rules_state import (
    AssetTier,
    LeverageAction,
    LeverageRulesConfig,
    LeverageResult,
)
from .leverage_rules_helpers import LeverageRulesHelpers
from .leverage_rules_calculation import LeverageRulesCalculation

if TYPE_CHECKING:
    from .regime_detector import RegimeResult

logger = logging.getLogger(__name__)


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

    def __init__(self, config: Optional[LeverageRulesConfig] = None):
        """Initialize Leverage Rules Engine."""
        self.config = config or LeverageRulesConfig()

        # Instantiate helper modules (composition pattern)
        self._helpers = LeverageRulesHelpers(parent=self)
        self._calculation = LeverageRulesCalculation(parent=self)

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

        Delegates to LeverageRulesCalculation.calculate_leverage().
        """
        return self._calculation.calculate_leverage(
            symbol, entry_price, regime_result, atr,
            requested_leverage, account_balance, current_exposure
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

        Delegates to LeverageRulesCalculation.validate_leverage().
        """
        return self._calculation.validate_leverage(
            leverage, symbol, entry_price, sl_price, direction
        )

    def get_safe_leverage_for_sl(
        self,
        entry_price: float,
        sl_price: float,
        symbol: str,
    ) -> int:
        """
        Calculate safe leverage based on stop loss distance.

        Delegates to LeverageRulesCalculation.get_safe_leverage_for_sl().
        """
        return self._calculation.get_safe_leverage_for_sl(entry_price, sl_price, symbol)

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


# Re-export for backward compatibility
__all__ = [
    "AssetTier",
    "LeverageAction",
    "LeverageRulesConfig",
    "LeverageResult",
    "LeverageRulesEngine",
    "get_leverage_rules_engine",
    "calculate_leverage",
    "load_leverage_config",
    "save_leverage_config",
]
