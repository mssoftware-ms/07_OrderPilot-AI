"""
Risk Manager - SL/TP Berechnung und Position Sizing

Verantwortlich für:
- ATR-basierte Stop Loss Berechnung
- ATR-basierte Take Profit Berechnung
- Risiko-basierte Position Sizing
- Daily Loss Tracking
- Max Position Size Limits
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .bot_config import BotConfig
    from .strategy_config import StrategyConfig

logger = logging.getLogger(__name__)


@dataclass
class RiskCalculation:
    """Ergebnis einer Risiko-Berechnung."""

    # Entry
    entry_price: Decimal
    side: str  # "BUY" oder "SELL"

    # SL/TP
    stop_loss: Decimal
    take_profit: Decimal
    sl_distance: Decimal
    tp_distance: Decimal
    sl_percent: float
    tp_percent: float

    # Position Size
    quantity: Decimal
    position_value_usd: Decimal
    risk_amount_usd: Decimal
    risk_percent: float

    # ATR Info
    atr_value: Decimal
    atr_percent: float

    # Risk:Reward
    risk_reward_ratio: float

    def to_dict(self) -> dict:
        """Konvertiert zu Dictionary."""
        return {
            "entry_price": str(self.entry_price),
            "side": self.side,
            "stop_loss": str(self.stop_loss),
            "take_profit": str(self.take_profit),
            "sl_distance": str(self.sl_distance),
            "tp_distance": str(self.tp_distance),
            "sl_percent": self.sl_percent,
            "tp_percent": self.tp_percent,
            "quantity": str(self.quantity),
            "position_value_usd": str(self.position_value_usd),
            "risk_amount_usd": str(self.risk_amount_usd),
            "risk_percent": self.risk_percent,
            "atr_value": str(self.atr_value),
            "atr_percent": self.atr_percent,
            "risk_reward_ratio": self.risk_reward_ratio,
        }


class RiskManager:
    """
    Verwaltet Risiko-Berechnungen und Position Sizing.

    Verwendet ATR-basierte SL/TP und risiko-basiertes Position Sizing.
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
        self.config = config
        self.strategy_config = strategy_config

        # Defaults aus Config oder Hardcoded
        if strategy_config:
            # Percent-basierte oder ATR-basierte SL/TP
            self.sl_type = strategy_config.sl_type
            self.tp_type = strategy_config.tp_type
            self.sl_percent = Decimal(str(strategy_config.sl_percent))
            self.tp_percent = Decimal(str(strategy_config.tp_percent))
            self.sl_atr_multiplier = Decimal(str(strategy_config.sl_atr_multiplier))
            self.tp_atr_multiplier = Decimal(str(strategy_config.tp_atr_multiplier))
            risk_cfg = strategy_config.risk_config
            self.risk_per_trade_percent = Decimal(
                str(risk_cfg.max_position_risk_percent)
            )
            self.max_daily_loss_percent = Decimal(str(risk_cfg.max_daily_loss_percent))
            self.max_position_size = Decimal(str(risk_cfg.max_position_size_btc))
            self.leverage = risk_cfg.leverage
        elif config:
            self.sl_type = "atr_based"
            self.tp_type = "atr_based"
            self.sl_percent = Decimal("0.5")
            self.tp_percent = Decimal("1.0")
            self.sl_atr_multiplier = config.sl_atr_multiplier
            self.tp_atr_multiplier = config.tp_atr_multiplier
            self.risk_per_trade_percent = config.risk_per_trade_percent
            self.max_daily_loss_percent = config.max_daily_loss_percent
            self.max_position_size = config.max_position_size_btc
            self.leverage = config.leverage
        else:
            # Hardcoded Defaults
            self.sl_type = "percent_based"
            self.tp_type = "percent_based"
            self.sl_percent = Decimal("0.5")
            self.tp_percent = Decimal("1.0")
            self.sl_atr_multiplier = Decimal("1.5")
            self.tp_atr_multiplier = Decimal("2.0")
            self.risk_per_trade_percent = Decimal("1.0")
            self.max_daily_loss_percent = Decimal("3.0")
            self.max_position_size = Decimal("0.1")
            self.leverage = 10

        # Daily Loss Tracking
        self._daily_realized_pnl = Decimal("0")
        self._daily_trades = 0
        self._last_reset_date: datetime | None = None

        sl_desc = f"{self.sl_percent}%" if self.sl_type == "percent_based" else f"{self.sl_atr_multiplier}x ATR"
        tp_desc = f"{self.tp_percent}%" if self.tp_type == "percent_based" else f"{self.tp_atr_multiplier}x ATR"
        logger.info(
            f"RiskManager initialized. "
            f"SL: {sl_desc}, TP: {tp_desc}, "
            f"Risk/Trade: {self.risk_per_trade_percent}%"
        )

    def calculate_sl_tp(
        self,
        entry_price: Decimal,
        side: str,
        atr: Decimal | None = None,
    ) -> tuple[Decimal, Decimal]:
        """
        Berechnet Stop Loss und Take Profit.

        Unterstützt zwei Modi:
        - 'percent_based': Feste Prozent vom Entry (bevorzugt für Risikokontrolle)
        - 'atr_based': ATR-Multiplikator (dynamisch je nach Volatilität)

        Args:
            entry_price: Erwarteter Entry-Preis
            side: "BUY" (Long) oder "SELL" (Short)
            atr: Average True Range Wert (optional bei percent_based)

        Returns:
            Tuple (stop_loss, take_profit)
        """
        # Stop Loss Distanz berechnen
        if self.sl_type == "percent_based":
            sl_distance = entry_price * (self.sl_percent / Decimal("100"))
        else:
            if atr is None:
                logger.warning("ATR required for atr_based SL, using 1% fallback")
                sl_distance = entry_price * Decimal("0.01")
            else:
                sl_distance = atr * self.sl_atr_multiplier

        # Take Profit Distanz berechnen
        if self.tp_type == "percent_based":
            tp_distance = entry_price * (self.tp_percent / Decimal("100"))
        else:
            if atr is None:
                logger.warning("ATR required for atr_based TP, using 2% fallback")
                tp_distance = entry_price * Decimal("0.02")
            else:
                tp_distance = atr * self.tp_atr_multiplier

        if side.upper() == "BUY":
            stop_loss = entry_price - sl_distance
            take_profit = entry_price + tp_distance
        else:  # SELL (Short)
            stop_loss = entry_price + sl_distance
            take_profit = entry_price - tp_distance

        # Runden auf 2 Dezimalstellen (USD)
        stop_loss = stop_loss.quantize(Decimal("0.01"))
        take_profit = take_profit.quantize(Decimal("0.01"))

        sl_pct = (sl_distance / entry_price * Decimal("100")).quantize(Decimal("0.01"))
        tp_pct = (tp_distance / entry_price * Decimal("100")).quantize(Decimal("0.01"))

        logger.info(
            f"SL/TP calculated: Entry={entry_price}, Side={side}, "
            f"SL={stop_loss} ({sl_pct}%), TP={take_profit} ({tp_pct}%)"
        )

        return stop_loss, take_profit

    def calculate_position_size(
        self,
        balance: Decimal,
        entry_price: Decimal,
        stop_loss: Decimal,
        risk_percent: Decimal | None = None,
    ) -> Decimal:
        """
        Berechnet Position Size basierend auf Risiko.

        Args:
            balance: Verfügbares Kapital (USDT)
            entry_price: Entry-Preis
            stop_loss: Stop Loss Preis
            risk_percent: Risiko % (default: aus Config)

        Returns:
            Position Size in BTC (gerundet auf 3 Dezimalstellen)
        """
        if risk_percent is None:
            risk_percent = self.risk_per_trade_percent

        # Risiko-Betrag berechnen
        risk_amount = balance * (risk_percent / Decimal("100"))

        # SL-Distanz berechnen
        sl_distance = abs(entry_price - stop_loss)

        if sl_distance <= 0:
            logger.warning("SL distance is zero or negative, using minimum position")
            return Decimal("0.001")

        # Position Size = Risk Amount / SL Distance
        # Bei Leverage: Position kann größer sein
        quantity = risk_amount / sl_distance

        # Max Position Size Limit
        if quantity > self.max_position_size:
            logger.info(
                f"Position size {quantity} exceeds max {self.max_position_size}, capping"
            )
            quantity = self.max_position_size

        # Minimum Position Size
        min_position = Decimal("0.001")  # 0.001 BTC minimum
        if quantity < min_position:
            logger.info(f"Position size {quantity} below minimum, using {min_position}")
            quantity = min_position

        # Runden auf 3 Dezimalstellen
        quantity = quantity.quantize(Decimal("0.001"))

        logger.debug(
            f"Position size calculated: Balance={balance}, Risk={risk_percent}%, "
            f"SL Distance={sl_distance}, Quantity={quantity}"
        )

        return quantity

    def calculate_full_risk(
        self,
        balance: Decimal,
        entry_price: Decimal,
        side: str,
        atr: Decimal,
    ) -> RiskCalculation:
        """
        Berechnet vollständige Risiko-Analyse.

        Args:
            balance: Verfügbares Kapital (USDT)
            entry_price: Entry-Preis
            side: "BUY" oder "SELL"
            atr: ATR Wert

        Returns:
            RiskCalculation mit allen Details
        """
        # SL/TP berechnen
        stop_loss, take_profit = self.calculate_sl_tp(entry_price, side, atr)

        # Position Size berechnen
        quantity = self.calculate_position_size(balance, entry_price, stop_loss)

        # Distanzen
        sl_distance = abs(entry_price - stop_loss)
        tp_distance = abs(take_profit - entry_price)

        # Prozente
        sl_percent = float(sl_distance / entry_price * 100)
        tp_percent = float(tp_distance / entry_price * 100)
        atr_percent = float(atr / entry_price * 100)

        # Position Value und Risk Amount
        position_value = quantity * entry_price
        risk_amount = quantity * sl_distance

        # Risk:Reward Ratio
        if sl_distance > 0:
            risk_reward = float(tp_distance / sl_distance)
        else:
            risk_reward = 0.0

        # Risk Percent (actual)
        if balance > 0:
            actual_risk_percent = float(risk_amount / balance * 100)
        else:
            actual_risk_percent = 0.0

        return RiskCalculation(
            entry_price=entry_price,
            side=side.upper(),
            stop_loss=stop_loss,
            take_profit=take_profit,
            sl_distance=sl_distance,
            tp_distance=tp_distance,
            sl_percent=round(sl_percent, 2),
            tp_percent=round(tp_percent, 2),
            quantity=quantity,
            position_value_usd=position_value.quantize(Decimal("0.01")),
            risk_amount_usd=risk_amount.quantize(Decimal("0.01")),
            risk_percent=round(actual_risk_percent, 2),
            atr_value=atr,
            atr_percent=round(atr_percent, 2),
            risk_reward_ratio=round(risk_reward, 2),
        )

    def check_daily_loss_limit(self, balance: Decimal) -> tuple[bool, str]:
        """
        Prüft ob Daily Loss Limit erreicht ist.

        Args:
            balance: Aktueller Kontostand

        Returns:
            Tuple (can_trade, reason)
        """
        self._check_daily_reset()

        # 100% = effektiv deaktiviert (für Paper Trading)
        if self.max_daily_loss_percent >= Decimal("100"):
            return True, f"Daily loss limit disabled (100%). PnL: {self._daily_realized_pnl} USDT"

        max_loss = balance * (self.max_daily_loss_percent / Decimal("100"))

        if self._daily_realized_pnl < 0 and abs(self._daily_realized_pnl) >= max_loss:
            logger.warning(
                f"Daily loss limit reached: {self._daily_realized_pnl} USDT "
                f"(limit: {self.max_daily_loss_percent}% = -{max_loss} USDT)"
            )
            return False, (
                f"Daily loss limit reached: {self._daily_realized_pnl} USDT "
                f"(max: -{max_loss} USDT)"
            )

        return True, f"Daily PnL: {self._daily_realized_pnl} USDT (limit: {self.max_daily_loss_percent}%)"

    def record_trade_result(self, pnl: Decimal) -> None:
        """
        Zeichnet Trade-Ergebnis auf.

        Args:
            pnl: Realisierter PnL des Trades
        """
        self._check_daily_reset()
        self._daily_realized_pnl += pnl
        self._daily_trades += 1

        logger.info(
            f"Trade recorded. PnL: {pnl} USDT, "
            f"Daily total: {self._daily_realized_pnl} USDT, "
            f"Trades today: {self._daily_trades}"
        )

    def _check_daily_reset(self) -> None:
        """Prüft ob neuer Tag begonnen hat und setzt Daily Stats zurück."""
        now = datetime.now(timezone.utc)
        today = now.date()

        if self._last_reset_date is None or self._last_reset_date != today:
            logger.info(f"Daily stats reset. Previous: {self._last_reset_date}")
            self._daily_realized_pnl = Decimal("0")
            self._daily_trades = 0
            self._last_reset_date = today

    def get_daily_stats(self) -> dict:
        """Gibt tägliche Statistiken zurück."""
        self._check_daily_reset()
        return {
            "date": str(self._last_reset_date),
            "realized_pnl": str(self._daily_realized_pnl),
            "trades": self._daily_trades,
            "max_loss_percent": str(self.max_daily_loss_percent),
        }

    def validate_trade(
        self,
        balance: Decimal,
        entry_price: Decimal,
        side: str,
        atr: Decimal,
    ) -> tuple[bool, str, RiskCalculation | None]:
        """
        Validiert ob Trade durchgeführt werden darf.

        Args:
            balance: Verfügbares Kapital
            entry_price: Entry-Preis
            side: "BUY" oder "SELL"
            atr: ATR Wert

        Returns:
            Tuple (is_valid, reason, risk_calculation)
        """
        # Daily Loss Check
        can_trade, reason = self.check_daily_loss_limit(balance)
        if not can_trade:
            return False, reason, None

        # Berechne Risiko
        risk_calc = self.calculate_full_risk(balance, entry_price, side, atr)

        # Validiere Position Size
        if risk_calc.quantity <= 0:
            return False, "Position size would be zero", risk_calc

        # Validiere Position Value
        if risk_calc.position_value_usd > balance * Decimal(str(self.leverage)):
            return (
                False,
                f"Position value {risk_calc.position_value_usd} exceeds "
                f"available margin (Balance: {balance}, Leverage: {self.leverage}x)",
                risk_calc,
            )

        # Validiere Risk Amount
        max_risk = balance * (self.risk_per_trade_percent / Decimal("100")) * Decimal(
            "1.1"
        )  # 10% Toleranz
        if risk_calc.risk_amount_usd > max_risk:
            return (
                False,
                f"Risk amount {risk_calc.risk_amount_usd} exceeds "
                f"max allowed {max_risk}",
                risk_calc,
            )

        return True, "Trade validated", risk_calc

    def adjust_sl_for_trailing(
        self,
        current_price: Decimal,
        current_sl: Decimal,
        entry_price: Decimal,
        side: str,
        atr: Decimal | None = None,
        activation_percent: Decimal | None = None,
    ) -> tuple[Decimal, bool]:
        """
        Berechnet neuen Trailing Stop.

        Unterstützt zwei Modi:
        - 'percent_based': Feste Prozent vom aktuellen Preis
        - 'atr_based': ATR-Multiplikator

        Args:
            current_price: Aktueller Marktpreis
            current_sl: Aktueller Stop Loss
            entry_price: Entry-Preis
            side: "BUY" oder "SELL"
            atr: ATR Wert für Trailing Distance (optional bei percent_based)
            activation_percent: Min. Profit % für Aktivierung

        Returns:
            Tuple (new_sl, was_updated)
        """
        # Aktivierungsschwelle
        if activation_percent is None:
            if self.strategy_config:
                activation_percent = Decimal(
                    str(self.strategy_config.trailing_stop_activation_percent)
                )
            elif self.config:
                activation_percent = self.config.trailing_stop_activation_percent
            else:
                activation_percent = Decimal("0.5")

        # Trailing Distance berechnen
        trailing_type = "atr_based"
        if self.strategy_config:
            trailing_type = self.strategy_config.trailing_stop_type

        if trailing_type == "percent_based":
            # Prozent-basierter Trailing Stop
            if self.strategy_config:
                trail_percent = Decimal(str(self.strategy_config.trailing_stop_percent))
            else:
                trail_percent = Decimal("0.3")
            trailing_distance = current_price * (trail_percent / Decimal("100"))
        else:
            # ATR-basierter Trailing Stop
            if atr is None:
                logger.warning("ATR required for atr_based trailing, using 0.3% fallback")
                trailing_distance = current_price * Decimal("0.003")
            else:
                if self.strategy_config:
                    trailing_multiplier = Decimal(
                        str(self.strategy_config.trailing_stop_atr_multiplier)
                    )
                elif self.config:
                    trailing_multiplier = self.config.trailing_stop_atr_multiplier
                else:
                    trailing_multiplier = Decimal("1.0")
                trailing_distance = atr * trailing_multiplier

        if side.upper() == "BUY":
            # Long: Prüfe ob Preis gestiegen ist
            profit_percent = (current_price - entry_price) / entry_price * 100

            if profit_percent < activation_percent:
                return current_sl, False

            # Neuer SL = Preis - Trailing Distance
            new_sl = current_price - trailing_distance
            new_sl = new_sl.quantize(Decimal("0.01"))

            # SL darf nur steigen, nie fallen
            if new_sl > current_sl:
                return new_sl, True

        else:  # SELL (Short)
            # Short: Prüfe ob Preis gefallen ist
            profit_percent = (entry_price - current_price) / entry_price * 100

            if profit_percent < activation_percent:
                return current_sl, False

            # Neuer SL = Preis + Trailing Distance
            new_sl = current_price + trailing_distance
            new_sl = new_sl.quantize(Decimal("0.01"))

            # SL darf nur sinken, nie steigen
            if new_sl < current_sl:
                return new_sl, True

        return current_sl, False

    def update_config(self, config: "BotConfig") -> None:
        """
        Aktualisiert die Konfiguration zur Laufzeit.

        Args:
            config: Neue Bot-Konfiguration
        """
        self.config = config
        self.sl_atr_multiplier = config.sl_atr_multiplier
        self.tp_atr_multiplier = config.tp_atr_multiplier
        self.risk_per_trade_percent = config.risk_per_trade_percent
        self.max_daily_loss_percent = config.max_daily_loss_percent
        self.max_position_size = config.max_position_size_btc
        self.leverage = config.leverage

        logger.info(
            f"RiskManager config updated: "
            f"SL={self.sl_atr_multiplier}x ATR, TP={self.tp_atr_multiplier}x ATR, "
            f"Risk/Trade={self.risk_per_trade_percent}%"
        )

    def update_strategy_config(self, strategy_config: "StrategyConfig") -> None:
        """
        Aktualisiert die Strategie-Konfiguration zur Laufzeit.

        Args:
            strategy_config: Neue Strategie-Konfiguration (aus JSON)
        """
        self.strategy_config = strategy_config
        self.sl_type = strategy_config.sl_type
        self.tp_type = strategy_config.tp_type
        self.sl_percent = Decimal(str(strategy_config.sl_percent))
        self.tp_percent = Decimal(str(strategy_config.tp_percent))
        self.sl_atr_multiplier = Decimal(str(strategy_config.sl_atr_multiplier))
        self.tp_atr_multiplier = Decimal(str(strategy_config.tp_atr_multiplier))

        risk_cfg = strategy_config.risk_config
        self.risk_per_trade_percent = Decimal(str(risk_cfg.max_position_risk_percent))
        self.max_daily_loss_percent = Decimal(str(risk_cfg.max_daily_loss_percent))
        self.max_position_size = Decimal(str(risk_cfg.max_position_size_btc))
        self.leverage = risk_cfg.leverage

        sl_desc = f"{self.sl_percent}%" if self.sl_type == "percent_based" else f"{self.sl_atr_multiplier}x ATR"
        tp_desc = f"{self.tp_percent}%" if self.tp_type == "percent_based" else f"{self.tp_atr_multiplier}x ATR"
        logger.info(
            f"RiskManager strategy config updated: SL: {sl_desc}, TP: {tp_desc}, "
            f"Risk/Trade={self.risk_per_trade_percent}%"
        )
