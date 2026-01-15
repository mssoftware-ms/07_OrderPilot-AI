"""
Position Monitor - Echtzeit-Überwachung von offenen Positionen

Verantwortlich für:
- SL/TP Überwachung (client-seitig, da Bitunix keine nativen SL/TP unterstützt)
- Trailing Stop Management
- Exit-Signale bei Preis-Triggern
- Position Status Updates

WICHTIG: Da Bitunix keine nativen Stop-Orders unterstützt, überwacht dieser
Monitor den Preis in Echtzeit und löst Market-Orders zum Schließen aus.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING, Callable, Awaitable

if TYPE_CHECKING:
    from PyQt6.QtCore import QTimer

    from src.core.broker.broker_types import Position
    from .risk_manager import RiskManager
    from .trade_logger import TradeLogEntry

logger = logging.getLogger(__name__)


class ExitTrigger(str, Enum):
    """Grund für Position-Exit."""

    STOP_LOSS = "STOP_LOSS"
    TAKE_PROFIT = "TAKE_PROFIT"
    TRAILING_STOP = "TRAILING_STOP"
    SIGNAL_EXIT = "SIGNAL_EXIT"
    MANUAL = "MANUAL"
    SESSION_END = "SESSION_END"
    DAILY_LOSS_LIMIT = "DAILY_LOSS_LIMIT"
    BOT_STOPPED = "BOT_STOPPED"


@dataclass
class MonitoredPosition:
    """Position mit Überwachungs-Details."""

    symbol: str
    side: str  # "BUY" (Long) oder "SELL" (Short)
    entry_price: Decimal
    quantity: Decimal
    entry_time: datetime

    # Stop Levels
    stop_loss: Decimal
    take_profit: Decimal
    initial_stop_loss: Decimal  # Original SL (vor Trailing)

    # Trailing Stop State
    trailing_enabled: bool = True
    trailing_activated: bool = False
    trailing_atr: Decimal | None = None

    # Current State
    current_price: Decimal | None = None
    unrealized_pnl: Decimal = field(default_factory=lambda: Decimal("0"))
    unrealized_pnl_percent: float = 0.0
    highest_price: Decimal | None = None  # Für Long Trailing
    lowest_price: Decimal | None = None  # Für Short Trailing

    # Trade Log Reference
    trade_log: "TradeLogEntry | None" = None

    def update_price(self, price: Decimal) -> None:
        """Aktualisiert Preis und berechnet PnL."""
        self.current_price = price

        # Update High/Low für Trailing
        if self.highest_price is None or price > self.highest_price:
            self.highest_price = price
        if self.lowest_price is None or price < self.lowest_price:
            self.lowest_price = price

        # PnL berechnen
        if self.side == "BUY":
            self.unrealized_pnl = (price - self.entry_price) * self.quantity
        else:
            self.unrealized_pnl = (self.entry_price - price) * self.quantity

        if self.entry_price > 0:
            entry_value = self.entry_price * self.quantity
            self.unrealized_pnl_percent = float(self.unrealized_pnl / entry_value * 100)

    def to_dict(self) -> dict:
        """Serialisiert Position zu Dictionary für Persistenz."""
        return {
            "symbol": self.symbol,
            "side": self.side,
            "entry_price": str(self.entry_price),
            "quantity": str(self.quantity),
            "entry_time": self.entry_time.isoformat(),
            "stop_loss": str(self.stop_loss),
            "take_profit": str(self.take_profit),
            "initial_stop_loss": str(self.initial_stop_loss),
            "trailing_enabled": self.trailing_enabled,
            "trailing_activated": self.trailing_activated,
            "trailing_atr": str(self.trailing_atr) if self.trailing_atr else None,
            "current_price": str(self.current_price) if self.current_price else None,
            "highest_price": str(self.highest_price) if self.highest_price else None,
            "lowest_price": str(self.lowest_price) if self.lowest_price else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MonitoredPosition":
        """Deserialisiert Position aus Dictionary."""
        return cls(
            symbol=data["symbol"],
            side=data["side"],
            entry_price=Decimal(data["entry_price"]),
            quantity=Decimal(data["quantity"]),
            entry_time=datetime.fromisoformat(data["entry_time"]),
            stop_loss=Decimal(data["stop_loss"]),
            take_profit=Decimal(data["take_profit"]),
            initial_stop_loss=Decimal(data["initial_stop_loss"]),
            trailing_enabled=data.get("trailing_enabled", True),
            trailing_activated=data.get("trailing_activated", False),
            trailing_atr=Decimal(data["trailing_atr"]) if data.get("trailing_atr") else None,
            current_price=Decimal(data["current_price"]) if data.get("current_price") else None,
            highest_price=Decimal(data["highest_price"]) if data.get("highest_price") else None,
            lowest_price=Decimal(data["lowest_price"]) if data.get("lowest_price") else None,
        )


@dataclass
class ExitResult:
    """Ergebnis einer Exit-Prüfung."""

    should_exit: bool
    trigger: ExitTrigger | None = None
    trigger_price: Decimal | None = None
    reason: str = ""


class PositionMonitor:
    """
    Überwacht offene Positionen und triggert Exits.

    Features:
    - Echtzeit SL/TP Überwachung
    - ATR-basierter Trailing Stop
    - Callbacks für Exit-Events
    """

    def __init__(
        self,
        risk_manager: "RiskManager | None" = None,
        check_interval_ms: int = 1000,
    ):
        """
        Args:
            risk_manager: RiskManager für Trailing Stop Berechnung
            check_interval_ms: Prüfintervall in Millisekunden
        """
        self.risk_manager = risk_manager
        self.check_interval_ms = check_interval_ms

        # Aktive Position (nur eine gleichzeitig)
        self._position: MonitoredPosition | None = None

        # Callbacks
        self._on_exit_triggered: Callable[
            [MonitoredPosition, ExitResult], Awaitable[None]
        ] | None = None
        self._on_trailing_updated: Callable[
            [MonitoredPosition, Decimal, Decimal], Awaitable[None]
        ] | None = None
        self._on_price_updated: Callable[
            [MonitoredPosition], Awaitable[None]
        ] | None = None

        # Timer (wird von außen gesetzt, z.B. QTimer)
        self._timer: "QTimer | None" = None
        self._running = False

        logger.info(
            f"PositionMonitor initialized. Check interval: {check_interval_ms}ms"
        )

    @property
    def has_position(self) -> bool:
        """Gibt True zurück wenn eine Position überwacht wird."""
        return self._position is not None

    @property
    def position(self) -> MonitoredPosition | None:
        """Gibt aktuelle überwachte Position zurück."""
        return self._position

    def set_position(
        self,
        symbol: str,
        side: str,
        entry_price: Decimal,
        quantity: Decimal,
        stop_loss: Decimal,
        take_profit: Decimal,
        trailing_atr: Decimal | None = None,
        trade_log: "TradeLogEntry | None" = None,
    ) -> MonitoredPosition:
        """
        Setzt neue zu überwachende Position.

        Args:
            symbol: Trading Symbol
            side: "BUY" oder "SELL"
            entry_price: Entry-Preis
            quantity: Position Size
            stop_loss: Stop Loss Preis
            take_profit: Take Profit Preis
            trailing_atr: ATR für Trailing Stop (None = kein Trailing)
            trade_log: Referenz zum Trade Log

        Returns:
            Erstellte MonitoredPosition
        """
        if self._position is not None:
            logger.warning(
                f"Overwriting existing position {self._position.symbol} "
                f"with new position {symbol}"
            )

        self._position = MonitoredPosition(
            symbol=symbol,
            side=side.upper(),
            entry_price=entry_price,
            quantity=quantity,
            entry_time=datetime.now(timezone.utc),
            stop_loss=stop_loss,
            take_profit=take_profit,
            initial_stop_loss=stop_loss,
            trailing_enabled=trailing_atr is not None,
            trailing_atr=trailing_atr,
            current_price=entry_price,
            highest_price=entry_price,
            lowest_price=entry_price,
            trade_log=trade_log,
        )

        logger.info(
            f"Position monitoring started: {symbol} {side} @ {entry_price}, "
            f"SL: {stop_loss}, TP: {take_profit}, "
            f"Trailing: {'Yes' if trailing_atr else 'No'}"
        )

        return self._position

    def clear_position(self) -> None:
        """Löscht überwachte Position."""
        if self._position:
            logger.info(f"Position monitoring stopped: {self._position.symbol}")
        self._position = None

    def restore_position(self, position_data: dict) -> MonitoredPosition | None:
        """
        Stellt Position aus gespeicherten Daten wieder her.

        Args:
            position_data: Dictionary mit Position-Daten (von to_dict())

        Returns:
            Wiederhergestellte Position oder None bei Fehler
        """
        try:
            self._position = MonitoredPosition.from_dict(position_data)
            logger.info(
                f"Position restored: {self._position.symbol} {self._position.side} "
                f"@ {self._position.entry_price}, SL: {self._position.stop_loss}, "
                f"TP: {self._position.take_profit}"
            )
            return self._position
        except Exception as e:
            logger.error(f"Failed to restore position: {e}")
            return None

    async def on_price_update(self, price: Decimal) -> ExitResult | None:
        """
        Wird bei jedem Preis-Update aufgerufen.

        Args:
            price: Aktueller Marktpreis

        Returns:
            ExitResult wenn Exit getriggert wurde, sonst None
        """
        if not self._position:
            return None

        # Update Position
        self._position.update_price(price)

        # Callback für Preis-Update
        if self._on_price_updated:
            await self._on_price_updated(self._position)

        # Prüfe Exit-Bedingungen
        exit_result = self._check_exit_conditions(price)

        if exit_result.should_exit:
            logger.info(
                f"Exit triggered: {exit_result.trigger.value} "
                f"@ {exit_result.trigger_price} - {exit_result.reason}"
            )

            if self._on_exit_triggered:
                await self._on_exit_triggered(self._position, exit_result)

            return exit_result

        # Prüfe Trailing Stop Update
        if self._position.trailing_enabled and self._position.trailing_atr:
            await self._update_trailing_stop(price)

        return None

    def _check_exit_conditions(self, price: Decimal) -> ExitResult:
        """Prüft alle Exit-Bedingungen."""
        pos = self._position
        if not pos:
            return ExitResult(should_exit=False)

        # Stop Loss Check
        if pos.side == "BUY":
            if price <= pos.stop_loss:
                return ExitResult(
                    should_exit=True,
                    trigger=ExitTrigger.TRAILING_STOP
                    if pos.trailing_activated
                    else ExitTrigger.STOP_LOSS,
                    trigger_price=price,
                    reason=f"Price {price} hit SL {pos.stop_loss}",
                )
        else:  # SHORT
            if price >= pos.stop_loss:
                return ExitResult(
                    should_exit=True,
                    trigger=ExitTrigger.TRAILING_STOP
                    if pos.trailing_activated
                    else ExitTrigger.STOP_LOSS,
                    trigger_price=price,
                    reason=f"Price {price} hit SL {pos.stop_loss}",
                )

        # Take Profit Check
        if pos.side == "BUY":
            if price >= pos.take_profit:
                return ExitResult(
                    should_exit=True,
                    trigger=ExitTrigger.TAKE_PROFIT,
                    trigger_price=price,
                    reason=f"Price {price} hit TP {pos.take_profit}",
                )
        else:  # SHORT
            if price <= pos.take_profit:
                return ExitResult(
                    should_exit=True,
                    trigger=ExitTrigger.TAKE_PROFIT,
                    trigger_price=price,
                    reason=f"Price {price} hit TP {pos.take_profit}",
                )

        return ExitResult(should_exit=False)

    async def _update_trailing_stop(self, price: Decimal) -> None:
        """Aktualisiert Trailing Stop wenn nötig."""
        pos = self._position
        if not pos or not pos.trailing_atr or not self.risk_manager:
            return

        # Prüfe ob Trailing aktiviert werden soll
        new_sl, was_updated = self.risk_manager.adjust_sl_for_trailing(
            current_price=price,
            current_sl=pos.stop_loss,
            entry_price=pos.entry_price,
            side=pos.side,
            atr=pos.trailing_atr,
        )

        if was_updated:
            old_sl = pos.stop_loss
            pos.stop_loss = new_sl
            pos.trailing_activated = True

            logger.info(
                f"Trailing stop updated: {old_sl} -> {new_sl} (Price: {price})"
            )

            # Trade Log aktualisieren
            if pos.trade_log:
                pos.trade_log.record_trailing_stop_update(
                    old_sl=float(old_sl),
                    new_sl=float(new_sl),
                    trigger_price=float(price),
                )

            # Callback
            if self._on_trailing_updated:
                await self._on_trailing_updated(pos, old_sl, new_sl)

    def trigger_manual_exit(self, reason: str = "Manual exit") -> ExitResult:
        """
        Triggert manuellen Exit.

        Returns:
            ExitResult für manuellen Exit
        """
        if not self._position:
            return ExitResult(should_exit=False, reason="No position to exit")

        return ExitResult(
            should_exit=True,
            trigger=ExitTrigger.MANUAL,
            trigger_price=self._position.current_price,
            reason=reason,
        )

    def trigger_session_end_exit(self) -> ExitResult:
        """
        Triggert Session-Ende Exit.

        Returns:
            ExitResult für Session-Ende
        """
        if not self._position:
            return ExitResult(should_exit=False, reason="No position to exit")

        return ExitResult(
            should_exit=True,
            trigger=ExitTrigger.SESSION_END,
            trigger_price=self._position.current_price,
            reason="Session ended - closing position",
        )

    def trigger_signal_exit(self, signal_reason: str) -> ExitResult:
        """
        Triggert Exit durch Signal-Umkehr.

        Returns:
            ExitResult für Signal-Exit
        """
        if not self._position:
            return ExitResult(should_exit=False, reason="No position to exit")

        return ExitResult(
            should_exit=True,
            trigger=ExitTrigger.SIGNAL_EXIT,
            trigger_price=self._position.current_price,
            reason=signal_reason,
        )

    # === Callbacks ===

    def set_exit_callback(
        self,
        callback: Callable[[MonitoredPosition, ExitResult], Awaitable[None]],
    ) -> None:
        """Setzt Callback für Exit-Events."""
        self._on_exit_triggered = callback

    def set_trailing_callback(
        self,
        callback: Callable[[MonitoredPosition, Decimal, Decimal], Awaitable[None]],
    ) -> None:
        """Setzt Callback für Trailing-Stop Updates."""
        self._on_trailing_updated = callback

    def set_price_callback(
        self,
        callback: Callable[[MonitoredPosition], Awaitable[None]],
    ) -> None:
        """Setzt Callback für Preis-Updates."""
        self._on_price_updated = callback

    # === Status ===

    def get_position_status(self) -> dict | None:
        """Gibt aktuellen Position-Status zurück."""
        if not self._position:
            return None

        pos = self._position
        return {
            "symbol": pos.symbol,
            "side": pos.side,
            "entry_price": str(pos.entry_price),
            "current_price": str(pos.current_price) if pos.current_price else None,
            "quantity": str(pos.quantity),
            "stop_loss": str(pos.stop_loss),
            "take_profit": str(pos.take_profit),
            "initial_stop_loss": str(pos.initial_stop_loss),
            "trailing_enabled": pos.trailing_enabled,
            "trailing_activated": pos.trailing_activated,
            "unrealized_pnl": str(pos.unrealized_pnl),
            "unrealized_pnl_percent": pos.unrealized_pnl_percent,
            "entry_time": pos.entry_time.isoformat(),
            "duration_seconds": (
                datetime.now(timezone.utc) - pos.entry_time
            ).total_seconds(),
        }

    def get_sl_tp_distance(self) -> tuple[Decimal, Decimal] | None:
        """Gibt aktuelle Distanz zu SL und TP zurück."""
        if not self._position or not self._position.current_price:
            return None

        pos = self._position
        price = pos.current_price

        if pos.side == "BUY":
            sl_distance = price - pos.stop_loss
            tp_distance = pos.take_profit - price
        else:
            sl_distance = pos.stop_loss - price
            tp_distance = price - pos.take_profit

        return sl_distance, tp_distance


class PositionMonitorService:
    """
    Service-Wrapper für PositionMonitor mit asyncio-Support.

    Kann als Background-Task laufen.
    """

    def __init__(
        self,
        monitor: PositionMonitor,
        price_provider: Callable[[], Awaitable[Decimal | None]],
    ):
        """
        Args:
            monitor: PositionMonitor Instanz
            price_provider: Async Funktion die aktuellen Preis liefert
        """
        self.monitor = monitor
        self.price_provider = price_provider
        self._running = False
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        """Startet den Monitor-Service."""
        if self._running:
            return

        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info("PositionMonitorService started")

    async def stop(self) -> None:
        """Stoppt den Monitor-Service."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("PositionMonitorService stopped")

    async def _run_loop(self) -> None:
        """Haupt-Loop für Preis-Checks."""
        interval_sec = self.monitor.check_interval_ms / 1000

        while self._running:
            try:
                if self.monitor.has_position:
                    price = await self.price_provider()
                    if price is not None:
                        await self.monitor.on_price_update(price)

                await asyncio.sleep(interval_sec)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in position monitor loop: {e}")
                await asyncio.sleep(interval_sec)
