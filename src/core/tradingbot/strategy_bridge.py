"""Strategy Bridge - Connects Simulator and Catalog systems.

This module bridges the gap between:
- Strategy Simulator (src/core/simulator): For backtesting/optimization
- Strategy Catalog (src/core/tradingbot): For live trading Daily Strategy selection

It provides:
1. Mapping between simulator strategy names and catalog strategy names
2. Parameter synchronization from simulator to catalog
3. Loading optimized params for active trading strategies
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


# STRATEGY NAME MAPPINGS
# Maps Simulator strategy names to their corresponding Catalog strategies
# One simulator strategy may map to multiple catalog variants
SIMULATOR_TO_CATALOG_MAP: dict[str, list[str]] = {
    "breakout": ["breakout_volatility", "breakout_momentum"],
    "momentum": ["momentum_macd"],
    "mean_reversion": ["mean_reversion_bb", "mean_reversion_rsi"],
    "trend_following": ["trend_following_conservative", "trend_following_aggressive"],
    "scalping": ["scalping_range"],
    "bollinger_squeeze": ["breakout_volatility"],  # Similar concept
    "trend_pullback": ["trend_following_conservative"],
    "opening_range": ["breakout_momentum"],
    "regime_hybrid": ["trend_following_conservative", "mean_reversion_bb"],
    "sideways_range": ["sideways_range_bounce"],
}

# Reverse mapping: Catalog strategy to Simulator strategy
CATALOG_TO_SIMULATOR_MAP: dict[str, str] = {
    "breakout_volatility": "breakout",
    "breakout_momentum": "breakout",
    "momentum_macd": "momentum",
    "mean_reversion_bb": "mean_reversion",
    "mean_reversion_rsi": "mean_reversion",
    "trend_following_conservative": "trend_following",
    "trend_following_aggressive": "trend_following",
    "scalping_range": "scalping",
    "sideways_range_bounce": "sideways_range",
}


# PARAMETER MAPPING
# Maps simulator parameter names to catalog entry_rule indicator thresholds
# Format: simulator_param -> (indicator_name, threshold_field)
PARAM_TO_ENTRY_RULE_MAP: dict[str, dict[str, Any]] = {
    # RSI parameters
    "rsi_period": {"indicator_pattern": "rsi", "affects": "calculation"},
    "rsi_lower": {"indicator_pattern": "rsi", "affects": "threshold", "condition": "below"},
    "rsi_upper": {"indicator_pattern": "rsi", "affects": "threshold", "condition": "above"},
    "rsi_oversold": {"indicator_pattern": "rsi", "affects": "threshold"},
    "rsi_overbought": {"indicator_pattern": "rsi", "affects": "threshold"},

    # ADX parameters
    "adx_period": {"indicator_pattern": "adx", "affects": "calculation"},
    "adx_threshold": {"indicator_pattern": "adx", "affects": "threshold"},

    # Bollinger Bands parameters
    "bb_period": {"indicator_pattern": "bb", "affects": "calculation"},
    "bb_std": {"indicator_pattern": "bb", "affects": "calculation"},

    # Volume parameters
    "volume_ratio": {"indicator_pattern": "volume", "affects": "threshold"},

    # MACD parameters
    "macd_fast": {"indicator_pattern": "macd", "affects": "calculation"},
    "macd_slow": {"indicator_pattern": "macd", "affects": "calculation"},
    "macd_signal": {"indicator_pattern": "macd", "affects": "calculation"},
}


@dataclass
class BridgedParameters:
    """Container for bridged parameters between systems."""
    simulator_strategy: str
    catalog_strategy: str
    simulator_params: dict[str, Any]
    entry_rule_updates: dict[str, dict[str, Any]]
    exit_rule_updates: dict[str, dict[str, Any]]
    indicator_config: dict[str, Any]


class StrategyBridge:
    """Bridge between Strategy Simulator and Strategy Catalog."""

    # Default path for bridged parameters
    BRIDGE_CONFIG_PATH = Path("config/strategy_bridge")

    def __init__(self):
        """Initialize the strategy bridge."""
        self._ensure_config_dir()

    def _ensure_config_dir(self) -> None:
        """Ensure config directory exists."""
        self.BRIDGE_CONFIG_PATH.mkdir(parents=True, exist_ok=True)

    # =========================================================================
    # MAPPING METHODS
    # =========================================================================

    def get_catalog_strategies(self, simulator_strategy: str) -> list[str]:
        """Get catalog strategies that correspond to a simulator strategy.

        Args:
            simulator_strategy: Simulator strategy name (e.g., "mean_reversion")

        Returns:
            List of catalog strategy names
        """
        return SIMULATOR_TO_CATALOG_MAP.get(simulator_strategy.lower(), [])

    def get_simulator_strategy(self, catalog_strategy: str) -> str | None:
        """Get simulator strategy that corresponds to a catalog strategy.

        Args:
            catalog_strategy: Catalog strategy name (e.g., "mean_reversion_bb")

        Returns:
            Simulator strategy name or None
        """
        return CATALOG_TO_SIMULATOR_MAP.get(catalog_strategy)

    def get_primary_catalog_strategy(self, simulator_strategy: str) -> str | None:
        """Get the primary (first) catalog strategy for a simulator strategy.

        Args:
            simulator_strategy: Simulator strategy name

        Returns:
            Primary catalog strategy name or None
        """
        catalog_strategies = self.get_catalog_strategies(simulator_strategy)
        return catalog_strategies[0] if catalog_strategies else None

    # =========================================================================
    # PARAMETER BRIDGING
    # =========================================================================

    def bridge_parameters(
        self,
        simulator_strategy: str,
        simulator_params: dict[str, Any],
        target_catalog_strategy: str | None = None,
    ) -> BridgedParameters:
        """Bridge simulator parameters to catalog format.

        Converts simulator optimization parameters to entry_rule updates
        and indicator configuration for the catalog strategy.

        Args:
            simulator_strategy: Simulator/Catalog strategy name (supports both)
            simulator_params: Parameters from simulator optimization
            target_catalog_strategy: Specific catalog strategy (optional)

        Returns:
            BridgedParameters with converted values
        """
        # Handle direct catalog strategy names
        if target_catalog_strategy is None:
            if self.is_catalog_strategy(simulator_strategy):
                # Simulator is using catalog name directly
                target_catalog_strategy = simulator_strategy
            else:
                # Legacy: simulator family name - get primary catalog strategy
                target_catalog_strategy = self.get_primary_catalog_strategy(simulator_strategy)

        if not target_catalog_strategy:
            raise ValueError(f"No catalog strategy found for: {simulator_strategy}")

        # Prepare updates
        entry_rule_updates = {}
        exit_rule_updates = {}
        indicator_config = {}

        for param_name, param_value in simulator_params.items():
            mapping = PARAM_TO_ENTRY_RULE_MAP.get(param_name)

            if mapping:
                indicator_pattern = mapping.get("indicator_pattern", "")
                affects = mapping.get("affects", "")

                if affects == "threshold":
                    # Update entry rule threshold
                    entry_rule_updates[indicator_pattern] = {
                        "threshold": param_value,
                        "condition": mapping.get("condition"),
                    }
                elif affects == "calculation":
                    # Update indicator calculation parameters
                    if indicator_pattern not in indicator_config:
                        indicator_config[indicator_pattern] = {}
                    indicator_config[indicator_pattern][param_name] = param_value
            else:
                # Store as generic indicator config
                indicator_config[param_name] = param_value

        return BridgedParameters(
            simulator_strategy=simulator_strategy,
            catalog_strategy=target_catalog_strategy,
            simulator_params=simulator_params,
            entry_rule_updates=entry_rule_updates,
            exit_rule_updates=exit_rule_updates,
            indicator_config=indicator_config,
        )

    # =========================================================================
    # PERSISTENCE
    # =========================================================================

    def save_bridged_params(
        self,
        simulator_strategy: str,
        simulator_params: dict[str, Any],
        catalog_strategy: str | None = None,
        symbol: str | None = None,
    ) -> Path:
        """Save bridged parameters for production use.

        Args:
            simulator_strategy: Simulator strategy name
            simulator_params: Optimized parameters
            catalog_strategy: Target catalog strategy (optional)
            symbol: Symbol these params were optimized for (optional)

        Returns:
            Path to saved config file
        """
        from datetime import datetime

        bridged = self.bridge_parameters(
            simulator_strategy, simulator_params, catalog_strategy
        )

        config = {
            "simulator_strategy": bridged.simulator_strategy,
            "catalog_strategy": bridged.catalog_strategy,
            "simulator_params": bridged.simulator_params,
            "entry_rule_updates": bridged.entry_rule_updates,
            "exit_rule_updates": bridged.exit_rule_updates,
            "indicator_config": bridged.indicator_config,
            "metadata": {
                "symbol": symbol,
                "saved_at": datetime.now().isoformat(),
                "version": "1.0",
            },
        }

        filename = f"{bridged.catalog_strategy}_bridged.json"
        filepath = self.BRIDGE_CONFIG_PATH / filename

        with open(filepath, "w") as f:
            json.dump(config, f, indent=2)

        logger.info(f"Saved bridged params: {filepath}")
        return filepath

    def load_bridged_params(self, catalog_strategy: str) -> dict[str, Any] | None:
        """Load bridged parameters for a catalog strategy.

        Args:
            catalog_strategy: Catalog strategy name

        Returns:
            Bridged config dict or None if not found
        """
        filename = f"{catalog_strategy}_bridged.json"
        filepath = self.BRIDGE_CONFIG_PATH / filename

        if not filepath.exists():
            logger.debug(f"No bridged params found: {filepath}")
            return None

        with open(filepath) as f:
            return json.load(f)

    def get_indicator_config_for_strategy(
        self, catalog_strategy: str
    ) -> dict[str, Any]:
        """Get indicator configuration for a catalog strategy.

        If bridged params exist, returns optimized config.
        Otherwise returns default config.

        Args:
            catalog_strategy: Catalog strategy name

        Returns:
            Indicator configuration dict
        """
        bridged = self.load_bridged_params(catalog_strategy)

        if bridged:
            return bridged.get("indicator_config", {})

        # Return defaults based on strategy type
        return self._get_default_indicator_config(catalog_strategy)

    def _get_default_indicator_config(self, catalog_strategy: str) -> dict[str, Any]:
        """Get default indicator config for a catalog strategy."""
        defaults = {
            "rsi_period": 14,
            "adx_period": 14,
            "bb_period": 20,
            "bb_std": 2.0,
            "macd_fast": 12,
            "macd_slow": 26,
            "macd_signal": 9,
            "atr_period": 14,
            "sma_fast": 20,
            "sma_slow": 50,
        }

        # Strategy-specific overrides
        if "scalping" in catalog_strategy:
            defaults.update({
                "rsi_period": 7,
                "bb_period": 10,
                "atr_period": 7,
            })
        elif "aggressive" in catalog_strategy:
            defaults.update({
                "adx_threshold": 30,
            })

        return defaults

    # =========================================================================
    # APPLY TO ACTIVE STRATEGY
    # =========================================================================

    def is_catalog_strategy(self, strategy_name: str) -> bool:
        """Check if strategy_name is a catalog strategy name.

        Args:
            strategy_name: Strategy name to check

        Returns:
            True if it's a valid catalog strategy name
        """
        # Catalog strategies have underscores with variant suffixes
        return strategy_name in CATALOG_TO_SIMULATOR_MAP

    def apply_to_active_strategy(
        self,
        bot_controller,
        simulator_strategy: str,
        simulator_params: dict[str, Any],
    ) -> bool:
        """Apply simulator parameters to the active trading strategy.

        Args:
            bot_controller: The active bot controller instance
            simulator_strategy: Simulator/Catalog strategy name (now supports both)
            simulator_params: Optimized parameters

        Returns:
            True if successfully applied
        """
        try:
            # Get active strategy from bot
            active_strategy_name = None

            if hasattr(bot_controller, 'get_strategy_selection'):
                selection = bot_controller.get_strategy_selection()
                if selection and selection.selected_strategy:
                    active_strategy_name = selection.selected_strategy

            if not active_strategy_name:
                if hasattr(bot_controller, 'active_strategy') and bot_controller.active_strategy:
                    active_strategy_name = bot_controller.active_strategy.name

            if not active_strategy_name:
                logger.warning("No active strategy to apply parameters to")
                return False

            # Check compatibility - now supports catalog strategy names directly
            if self.is_catalog_strategy(simulator_strategy):
                # Direct catalog name comparison
                if simulator_strategy != active_strategy_name:
                    logger.warning(
                        f"Strategy mismatch: Active={active_strategy_name}, "
                        f"Optimized={simulator_strategy}"
                    )
                target_catalog = simulator_strategy
            else:
                # Legacy: simulator family name - map to catalog
                expected_simulator = self.get_simulator_strategy(active_strategy_name)
                if expected_simulator != simulator_strategy.lower():
                    logger.warning(
                        f"Strategy family mismatch: Active={active_strategy_name} "
                        f"(expects {expected_simulator}), Got={simulator_strategy}"
                    )
                target_catalog = active_strategy_name

            # Bridge and save parameters
            self.save_bridged_params(
                simulator_strategy=simulator_strategy,
                simulator_params=simulator_params,
                catalog_strategy=target_catalog,
                symbol=getattr(bot_controller, 'symbol', None),
            )

            # Update indicator config in bot if possible
            if hasattr(bot_controller, 'update_indicator_config'):
                bridged = self.bridge_parameters(
                    simulator_strategy, simulator_params, target_catalog
                )
                bot_controller.update_indicator_config(bridged.indicator_config)
                logger.info(f"Applied indicator config to bot: {bridged.indicator_config}")

            logger.info(
                f"Applied {simulator_strategy} params to active strategy: {active_strategy_name}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to apply params to active strategy: {e}")
            return False


# MODULE-LEVEL CONVENIENCE FUNCTIONS
_bridge_instance: StrategyBridge | None = None


def get_strategy_bridge() -> StrategyBridge:
    """Get singleton StrategyBridge instance."""
    global _bridge_instance
    if _bridge_instance is None:
        _bridge_instance = StrategyBridge()
    return _bridge_instance


def get_catalog_strategies_for_simulator(simulator_strategy: str) -> list[str]:
    """Get catalog strategies for a simulator strategy."""
    return get_strategy_bridge().get_catalog_strategies(simulator_strategy)


def get_simulator_strategy_for_catalog(catalog_strategy: str) -> str | None:
    """Get simulator strategy for a catalog strategy."""
    return get_strategy_bridge().get_simulator_strategy(catalog_strategy)


def apply_simulator_params_to_bot(
    bot_controller,
    simulator_strategy: str,
    simulator_params: dict[str, Any],
) -> bool:
    """Apply simulator parameters to active bot strategy."""
    return get_strategy_bridge().apply_to_active_strategy(
        bot_controller, simulator_strategy, simulator_params
    )
