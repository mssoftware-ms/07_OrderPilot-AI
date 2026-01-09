"""
Risk Manager Config - Config Update Methods.

Refactored from risk_manager.py.

Contains:
- update_config: Updates BotConfig at runtime
- update_strategy_config: Updates StrategyConfig at runtime
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .bot_config import BotConfig
    from .risk_manager import RiskManager
    from .strategy_config import StrategyConfig

logger = logging.getLogger(__name__)


class RiskManagerConfig:
    """Helper for config updates."""

    def __init__(self, parent: RiskManager):
        self.parent = parent

    def update_config(self, config: BotConfig) -> None:
        """
        Aktualisiert die Konfiguration zur Laufzeit.

        Args:
            config: Neue Bot-Konfiguration
        """
        self.parent.config = config
        self.parent.sl_atr_multiplier = config.sl_atr_multiplier
        self.parent.tp_atr_multiplier = config.tp_atr_multiplier
        self.parent.risk_per_trade_percent = config.risk_per_trade_percent
        self.parent.max_daily_loss_percent = config.max_daily_loss_percent
        self.parent.max_position_size = config.max_position_size_btc
        self.parent.leverage = config.leverage

        logger.info(
            f"RiskManager config updated: "
            f"SL={self.parent.sl_atr_multiplier}x ATR, TP={self.parent.tp_atr_multiplier}x ATR, "
            f"Risk/Trade={self.parent.risk_per_trade_percent}%"
        )

    def update_strategy_config(self, strategy_config: StrategyConfig) -> None:
        """
        Aktualisiert die Strategie-Konfiguration zur Laufzeit.

        Args:
            strategy_config: Neue Strategie-Konfiguration (aus JSON)
        """
        self.parent.strategy_config = strategy_config
        self.parent.sl_type = strategy_config.sl_type
        self.parent.tp_type = strategy_config.tp_type
        self.parent.sl_percent = Decimal(str(strategy_config.sl_percent))
        self.parent.tp_percent = Decimal(str(strategy_config.tp_percent))
        self.parent.sl_atr_multiplier = Decimal(str(strategy_config.sl_atr_multiplier))
        self.parent.tp_atr_multiplier = Decimal(str(strategy_config.tp_atr_multiplier))

        risk_cfg = strategy_config.risk_config
        self.parent.risk_per_trade_percent = Decimal(
            str(risk_cfg.max_position_risk_percent)
        )
        self.parent.max_daily_loss_percent = Decimal(str(risk_cfg.max_daily_loss_percent))
        self.parent.max_position_size = Decimal(str(risk_cfg.max_position_size_btc))
        self.parent.leverage = risk_cfg.leverage

        sl_desc = (
            f"{self.parent.sl_percent}%"
            if self.parent.sl_type == "percent_based"
            else f"{self.parent.sl_atr_multiplier}x ATR"
        )
        tp_desc = (
            f"{self.parent.tp_percent}%"
            if self.parent.tp_type == "percent_based"
            else f"{self.parent.tp_atr_multiplier}x ATR"
        )
        logger.info(
            f"RiskManager strategy config updated: SL: {sl_desc}, TP: {tp_desc}, "
            f"Risk/Trade={self.parent.risk_per_trade_percent}%"
        )
