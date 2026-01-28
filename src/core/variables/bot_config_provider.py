"""
Bot Configuration Provider for CEL Expressions.

This module provides access to bot configuration parameters for use in
CEL expressions through the bot.* namespace.

Available Variables:
    bot.symbol                     - Trading symbol
    bot.leverage                   - Leverage (10x)
    bot.paper_mode                 - Is paper trading? (always True)
    bot.risk_per_trade_pct         - Risk per trade (%)
    bot.max_daily_loss_pct         - Max daily loss (%)
    bot.max_position_size_btc      - Max position size (BTC)
    bot.sl_atr_multiplier          - Stop Loss ATR multiplier
    bot.tp_atr_multiplier          - Take Profit ATR multiplier
    bot.trailing_stop_enabled      - Trailing stop enabled?
    bot.trailing_stop_atr_mult     - Trailing stop ATR multiplier
    bot.trailing_stop_activation   - Trailing stop activation (%)
    bot.min_confluence_score       - Minimum confluence score
    bot.require_regime_alignment   - Require regime alignment?
    bot.session.enabled            - Session management enabled?
    bot.session.start_utc          - Session start time (UTC)
    bot.session.end_utc            - Session end time (UTC)
    bot.ai.enabled                 - AI validation enabled?
    bot.ai.confidence_threshold    - AI confidence threshold (0-100)
    bot.ai.min_confluence_for_ai   - Min confluence to trigger AI

Author: OrderPilot-AI Development Team
Created: 2026-01-28
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Dict

if TYPE_CHECKING:
    from src.core.trading_bot.bot_config import BotConfig

logger = logging.getLogger(__name__)


class BotConfigProvider:
    """
    Provides bot configuration for CEL expressions via bot.* namespace.

    This provider extracts bot configuration parameters from BotConfig
    and makes them available for CEL expressions.

    Examples:
        >>> provider = BotConfigProvider()
        >>> context = provider.get_context(bot_config)
        >>> print(context['bot.leverage'])
        10

    Attributes:
        namespace: Namespace prefix for variables (default: 'bot')
    """

    def __init__(self, namespace: str = "bot"):
        """
        Initialize bot config provider.

        Args:
            namespace: Namespace prefix for variables (default: 'bot')
        """
        self.namespace = namespace

    def get_context(self, bot_config: BotConfig) -> Dict[str, Any]:
        """
        Extract bot configuration and return CEL context.

        Args:
            bot_config: BotConfig instance

        Returns:
            Dictionary with bot.* variables

        Examples:
            >>> context = provider.get_context(bot_config)
            >>> print(context.keys())
            dict_keys(['bot.symbol', 'bot.leverage', 'bot.paper_mode', ...])
        """
        context = {}

        try:
            # === TRADING ===
            context[f"{self.namespace}.symbol"] = bot_config.symbol
            context[f"{self.namespace}.leverage"] = bot_config.leverage
            context[f"{self.namespace}.paper_mode"] = bot_config.paper_mode

            # === RISK MANAGEMENT ===
            context[f"{self.namespace}.risk_per_trade_pct"] = float(
                bot_config.risk_per_trade_percent
            )
            context[f"{self.namespace}.max_daily_loss_pct"] = float(
                bot_config.max_daily_loss_percent
            )
            context[f"{self.namespace}.max_position_size_btc"] = float(
                bot_config.max_position_size_btc
            )

            # === SL/TP ===
            context[f"{self.namespace}.sl_atr_multiplier"] = float(
                bot_config.sl_atr_multiplier
            )
            context[f"{self.namespace}.tp_atr_multiplier"] = float(
                bot_config.tp_atr_multiplier
            )

            # === TRAILING STOP ===
            context[f"{self.namespace}.trailing_stop_enabled"] = (
                bot_config.trailing_stop_enabled
            )
            context[f"{self.namespace}.trailing_stop_atr_mult"] = float(
                bot_config.trailing_stop_atr_multiplier
            )
            context[f"{self.namespace}.trailing_stop_activation_pct"] = float(
                bot_config.trailing_stop_activation_percent
            )

            # === SIGNAL GENERATION ===
            context[f"{self.namespace}.min_confluence_score"] = (
                bot_config.min_confluence_score
            )
            context[f"{self.namespace}.require_regime_alignment"] = (
                bot_config.require_regime_alignment
            )

            # === TIMING ===
            context[f"{self.namespace}.analysis_interval_sec"] = (
                bot_config.analysis_interval_seconds
            )
            context[f"{self.namespace}.position_check_interval_ms"] = (
                bot_config.position_check_interval_ms
            )
            context[f"{self.namespace}.macro_update_interval_min"] = (
                bot_config.macro_update_interval_minutes
            )
            context[f"{self.namespace}.trend_update_interval_min"] = (
                bot_config.trend_update_interval_minutes
            )

            # === SESSION CONFIG ===
            context[f"{self.namespace}.session.enabled"] = (
                bot_config.session.enabled
            )
            context[f"{self.namespace}.session.start_utc"] = (
                bot_config.session.start_utc
            )
            context[f"{self.namespace}.session.end_utc"] = (
                bot_config.session.end_utc
            )
            context[f"{self.namespace}.session.close_at_end"] = (
                bot_config.session.close_at_end
            )

            # === AI CONFIG ===
            context[f"{self.namespace}.ai.enabled"] = bot_config.ai.enabled
            context[f"{self.namespace}.ai.confidence_threshold"] = (
                bot_config.ai.confidence_threshold
            )
            context[f"{self.namespace}.ai.min_confluence_for_ai"] = (
                bot_config.ai.min_confluence_for_ai
            )
            context[f"{self.namespace}.ai.fallback_to_technical"] = (
                bot_config.ai.fallback_to_technical
            )

            logger.debug(
                f"BotConfigProvider extracted {len(context)} variables "
                f"for {bot_config.symbol}"
            )

            return context

        except Exception as e:
            logger.error(f"Error extracting bot config: {e}", exc_info=True)
            return self._get_empty_context()

    def _get_empty_context(self) -> Dict[str, Any]:
        """
        Return empty/placeholder context when bot config is unavailable.

        Returns:
            Dictionary with None/default values
        """
        return {
            f"{self.namespace}.symbol": None,
            f"{self.namespace}.leverage": None,
            f"{self.namespace}.paper_mode": True,  # Always True
            f"{self.namespace}.risk_per_trade_pct": None,
            f"{self.namespace}.max_daily_loss_pct": None,
            f"{self.namespace}.max_position_size_btc": None,
            f"{self.namespace}.sl_atr_multiplier": None,
            f"{self.namespace}.tp_atr_multiplier": None,
            f"{self.namespace}.trailing_stop_enabled": None,
            f"{self.namespace}.trailing_stop_atr_mult": None,
            f"{self.namespace}.trailing_stop_activation_pct": None,
            f"{self.namespace}.min_confluence_score": None,
            f"{self.namespace}.require_regime_alignment": None,
            f"{self.namespace}.analysis_interval_sec": None,
            f"{self.namespace}.position_check_interval_ms": None,
            f"{self.namespace}.macro_update_interval_min": None,
            f"{self.namespace}.trend_update_interval_min": None,
            f"{self.namespace}.session.enabled": None,
            f"{self.namespace}.session.start_utc": None,
            f"{self.namespace}.session.end_utc": None,
            f"{self.namespace}.session.close_at_end": None,
            f"{self.namespace}.ai.enabled": None,
            f"{self.namespace}.ai.confidence_threshold": None,
            f"{self.namespace}.ai.min_confluence_for_ai": None,
            f"{self.namespace}.ai.fallback_to_technical": None,
        }

    def get_variable_names(self) -> list[str]:
        """
        Get list of all available variable names.

        Returns:
            List of fully qualified variable names

        Examples:
            >>> provider = BotConfigProvider()
            >>> print(provider.get_variable_names())
            ['bot.symbol', 'bot.leverage', ...]
        """
        empty = self._get_empty_context()
        return sorted(empty.keys())

    def get_variable_info(self) -> Dict[str, Dict[str, str]]:
        """
        Get metadata for all variables.

        Returns:
            Dictionary of variable_name -> {description, type, unit}

        Examples:
            >>> provider = BotConfigProvider()
            >>> info = provider.get_variable_info()
            >>> print(info['bot.leverage'])
            {'description': 'Trading leverage', 'type': 'int', 'unit': 'x'}
        """
        return {
            f"{self.namespace}.symbol": {
                "description": "Trading symbol",
                "type": "string",
                "unit": None,
            },
            f"{self.namespace}.leverage": {
                "description": "Trading leverage",
                "type": "int",
                "unit": "x",
            },
            f"{self.namespace}.paper_mode": {
                "description": "Is paper trading? (always True)",
                "type": "bool",
                "unit": None,
            },
            f"{self.namespace}.risk_per_trade_pct": {
                "description": "Risk per trade",
                "type": "float",
                "unit": "%",
            },
            f"{self.namespace}.max_daily_loss_pct": {
                "description": "Maximum daily loss",
                "type": "float",
                "unit": "%",
            },
            f"{self.namespace}.max_position_size_btc": {
                "description": "Maximum position size",
                "type": "float",
                "unit": "BTC",
            },
            f"{self.namespace}.sl_atr_multiplier": {
                "description": "Stop Loss ATR multiplier",
                "type": "float",
                "unit": None,
            },
            f"{self.namespace}.tp_atr_multiplier": {
                "description": "Take Profit ATR multiplier",
                "type": "float",
                "unit": None,
            },
            f"{self.namespace}.trailing_stop_enabled": {
                "description": "Is trailing stop enabled?",
                "type": "bool",
                "unit": None,
            },
            f"{self.namespace}.trailing_stop_atr_mult": {
                "description": "Trailing stop ATR multiplier",
                "type": "float",
                "unit": None,
            },
            f"{self.namespace}.trailing_stop_activation_pct": {
                "description": "Trailing stop activation threshold",
                "type": "float",
                "unit": "%",
            },
            f"{self.namespace}.min_confluence_score": {
                "description": "Minimum confluence score for signals",
                "type": "int",
                "unit": None,
            },
            f"{self.namespace}.require_regime_alignment": {
                "description": "Require regime alignment for signals?",
                "type": "bool",
                "unit": None,
            },
            f"{self.namespace}.analysis_interval_sec": {
                "description": "Analysis interval",
                "type": "int",
                "unit": "seconds",
            },
            f"{self.namespace}.position_check_interval_ms": {
                "description": "Position check interval",
                "type": "int",
                "unit": "milliseconds",
            },
            f"{self.namespace}.session.enabled": {
                "description": "Is session management enabled?",
                "type": "bool",
                "unit": None,
            },
            f"{self.namespace}.session.start_utc": {
                "description": "Session start time (UTC)",
                "type": "string",
                "unit": None,
            },
            f"{self.namespace}.session.end_utc": {
                "description": "Session end time (UTC)",
                "type": "string",
                "unit": None,
            },
            f"{self.namespace}.ai.enabled": {
                "description": "Is AI validation enabled?",
                "type": "bool",
                "unit": None,
            },
            f"{self.namespace}.ai.confidence_threshold": {
                "description": "AI confidence threshold",
                "type": "int",
                "unit": None,
            },
            f"{self.namespace}.ai.min_confluence_for_ai": {
                "description": "Minimum confluence to trigger AI call",
                "type": "int",
                "unit": None,
            },
        }
