"""
Risk Manager Initialization - Config Setup.

Refactored from risk_manager.py.

Contains:
- Initialization logic for RiskManager
- Config parsing (strategy_config/config/hardcoded defaults)
"""

from __future__ import annotations

import logging
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .bot_config import BotConfig
    from .risk_manager import RiskManager
    from .strategy_config import StrategyConfig

logger = logging.getLogger(__name__)


class RiskManagerInit:
    """Helper for RiskManager initialization."""

    def __init__(self, parent: RiskManager):
        self.parent = parent

    def initialize_config(
        self,
        config: BotConfig | None,
        strategy_config: StrategyConfig | None,
    ) -> None:
        """Initialize config from either strategy_config, config, or hardcoded defaults."""
        self.parent.config = config
        self.parent.strategy_config = strategy_config

        if strategy_config:
            self._init_from_strategy_config(strategy_config)
        elif config:
            self._init_from_bot_config(config)
        else:
            self._init_hardcoded_defaults()

        # Daily Loss Tracking
        self.parent._daily_realized_pnl = Decimal("0")
        self.parent._daily_trades = 0
        self.parent._last_reset_date = None

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
            f"RiskManager initialized. "
            f"SL: {sl_desc}, TP: {tp_desc}, "
            f"Risk/Trade: {self.parent.risk_per_trade_percent}%"
        )

    def _init_from_strategy_config(self, strategy_config: StrategyConfig) -> None:
        """Initialize from StrategyConfig (JSON-based)."""
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

    def _init_from_bot_config(self, config: BotConfig) -> None:
        """Initialize from BotConfig."""
        self.parent.sl_type = "atr_based"
        self.parent.tp_type = "atr_based"
        self.parent.sl_percent = Decimal("0.5")
        self.parent.tp_percent = Decimal("1.0")
        self.parent.sl_atr_multiplier = config.sl_atr_multiplier
        self.parent.tp_atr_multiplier = config.tp_atr_multiplier
        self.parent.risk_per_trade_percent = config.risk_per_trade_percent
        self.parent.max_daily_loss_percent = config.max_daily_loss_percent
        self.parent.max_position_size = config.max_position_size_btc
        self.parent.leverage = config.leverage

    def _init_hardcoded_defaults(self) -> None:
        """Initialize with hardcoded defaults."""
        self.parent.sl_type = "percent_based"
        self.parent.tp_type = "percent_based"
        self.parent.sl_percent = Decimal("0.5")
        self.parent.tp_percent = Decimal("1.0")
        self.parent.sl_atr_multiplier = Decimal("1.5")
        self.parent.tp_atr_multiplier = Decimal("2.0")
        self.parent.risk_per_trade_percent = Decimal("1.0")
        self.parent.max_daily_loss_percent = Decimal("3.0")
        self.parent.max_position_size = Decimal("0.1")
        self.parent.leverage = 10
