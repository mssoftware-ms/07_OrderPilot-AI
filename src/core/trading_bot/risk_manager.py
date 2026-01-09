"""
Risk Manager - SL/TP Berechnung und Position Sizing (REFACTORED)

REFACTORED: Split into focused helper modules using composition pattern.

Verantwortlich für:
- ATR-basierte Stop Loss Berechnung
- ATR-basierte Take Profit Berechnung
- Risiko-basierte Position Sizing
- Daily Loss Tracking
- Max Position Size Limits
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

# Import RiskCalculation from new location
from .risk_calculation import RiskCalculation

# Import helper modules
from .risk_manager_config import RiskManagerConfig
from .risk_manager_daily_tracking import RiskManagerDailyTracking
from .risk_manager_init import RiskManagerInit
from .risk_manager_position_sizing import RiskManagerPositionSizing
from .risk_manager_risk_analysis import RiskManagerRiskAnalysis
from .risk_manager_sl_tp import RiskManagerSLTP
from .risk_manager_trade_validation import RiskManagerTradeValidation
from .risk_manager_trailing import RiskManagerTrailing

if TYPE_CHECKING:
    from .bot_config import BotConfig
    from .strategy_config import StrategyConfig

# Re-export RiskCalculation for backward compatibility
__all__ = ["RiskManager", "RiskCalculation"]


class RiskManager:
    """
    Verwaltet Risiko-Berechnungen und Position Sizing (REFACTORED).

    Verwendet ATR-basierte SL/TP und risiko-basiertes Position Sizing.
    Delegiert spezifische Aufgaben an Helper-Klassen.
    """

    def __init__(
        self,
        config: BotConfig | None = None,
        strategy_config: StrategyConfig | None = None,
    ):
        """
        Args:
            config: Bot-Konfiguration
            strategy_config: Strategie-Konfiguration (für JSON-basierte Parameter)
        """
        # Will be initialized by helper
        self.config = None
        self.strategy_config = None
        self.sl_type = None
        self.tp_type = None
        self.sl_percent = None
        self.tp_percent = None
        self.sl_atr_multiplier = None
        self.tp_atr_multiplier = None
        self.risk_per_trade_percent = None
        self.max_daily_loss_percent = None
        self.max_position_size = None
        self.leverage = None
        self._daily_realized_pnl = None
        self._daily_trades = None
        self._last_reset_date: datetime | None = None

        # Create helpers (composition pattern)
        self._init = RiskManagerInit(self)
        self._sl_tp = RiskManagerSLTP(self)
        self._position_sizing = RiskManagerPositionSizing(self)
        self._risk_analysis = RiskManagerRiskAnalysis(self)
        self._daily_tracking = RiskManagerDailyTracking(self)
        self._trade_validation = RiskManagerTradeValidation(self)
        self._trailing = RiskManagerTrailing(self)
        self._config_updater = RiskManagerConfig(self)

        # Initialize config
        self._init.initialize_config(config, strategy_config)

    def calculate_sl_tp(
        self,
        entry_price: Decimal,
        side: str,
        atr: Decimal | None = None,
    ) -> tuple[Decimal, Decimal]:
        """Berechnet Stop Loss und Take Profit (delegiert)."""
        return self._sl_tp.calculate_sl_tp(entry_price, side, atr)

    def calculate_position_size(
        self,
        balance: Decimal,
        entry_price: Decimal,
        stop_loss: Decimal,
        risk_percent: Decimal | None = None,
    ) -> Decimal:
        """Berechnet Position Size basierend auf Risiko (delegiert)."""
        return self._position_sizing.calculate_position_size(
            balance, entry_price, stop_loss, risk_percent
        )

    def calculate_full_risk(
        self,
        balance: Decimal,
        entry_price: Decimal,
        side: str,
        atr: Decimal,
    ) -> RiskCalculation:
        """Berechnet vollständige Risiko-Analyse (delegiert)."""
        return self._risk_analysis.calculate_full_risk(balance, entry_price, side, atr)

    def check_daily_loss_limit(self, balance: Decimal) -> tuple[bool, str]:
        """Prüft ob Daily Loss Limit erreicht ist (delegiert)."""
        return self._daily_tracking.check_daily_loss_limit(balance)

    def record_trade_result(self, pnl: Decimal) -> None:
        """Zeichnet Trade-Ergebnis auf (delegiert)."""
        self._daily_tracking.record_trade_result(pnl)

    def get_daily_stats(self) -> dict:
        """Gibt tägliche Statistiken zurück (delegiert)."""
        return self._daily_tracking.get_daily_stats()

    def validate_trade(
        self,
        balance: Decimal,
        entry_price: Decimal,
        side: str,
        atr: Decimal,
    ) -> tuple[bool, str, RiskCalculation | None]:
        """Validiert ob Trade durchgeführt werden darf (delegiert)."""
        return self._trade_validation.validate_trade(balance, entry_price, side, atr)

    def adjust_sl_for_trailing(
        self,
        current_price: Decimal,
        current_sl: Decimal,
        entry_price: Decimal,
        side: str,
        atr: Decimal | None = None,
        activation_percent: Decimal | None = None,
    ) -> tuple[Decimal, bool]:
        """Berechnet neuen Trailing Stop (delegiert)."""
        return self._trailing.adjust_sl_for_trailing(
            current_price,
            current_sl,
            entry_price,
            side,
            atr,
            activation_percent,
        )

    def update_config(self, config: BotConfig) -> None:
        """Aktualisiert die Konfiguration zur Laufzeit (delegiert)."""
        self._config_updater.update_config(config)

    def update_strategy_config(self, strategy_config: StrategyConfig) -> None:
        """Aktualisiert die Strategie-Konfiguration zur Laufzeit (delegiert)."""
        self._config_updater.update_strategy_config(strategy_config)
