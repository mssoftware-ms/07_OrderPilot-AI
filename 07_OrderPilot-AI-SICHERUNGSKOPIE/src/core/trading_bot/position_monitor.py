"""
Position Monitor - Echtzeit-Überwachung von offenen Positionen (REFACTORED)

REFACTORED: Split into focused helper modules using composition pattern.

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
from decimal import Decimal
from typing import TYPE_CHECKING, Awaitable, Callable

# Import types and helpers
from .position_monitor_exit_checks import PositionMonitorExitChecks
from .position_monitor_management import PositionMonitorManagement
from .position_monitor_price import PositionMonitorPrice
from .position_monitor_status import PositionMonitorStatus
from .position_monitor_trailing import PositionMonitorTrailing
from .position_monitor_types import ExitResult, ExitTrigger, MonitoredPosition

if TYPE_CHECKING:
    from PyQt6.QtCore import QTimer

    from .risk_manager import RiskManager
    from .trade_logger import TradeLogEntry

# Re-export types for backward compatibility
__all__ = ["PositionMonitor", "PositionMonitorService", "MonitoredPosition", "ExitResult", "ExitTrigger"]

logger = logging.getLogger(__name__)


class PositionMonitor:
    """
    Überwacht offene Positionen und triggert Exits (REFACTORED).

    Features:
    - Echtzeit SL/TP Überwachung
    - ATR-basierter Trailing Stop
    - Callbacks für Exit-Events

    Delegiert spezifische Aufgaben an Helper-Klassen.
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
        self._on_exit_triggered: (
            Callable[[MonitoredPosition, ExitResult], Awaitable[None]] | None
        ) = None
        self._on_trailing_updated: (
            Callable[[MonitoredPosition, Decimal, Decimal], Awaitable[None]] | None
        ) = None
        self._on_price_updated: (
            Callable[[MonitoredPosition], Awaitable[None]] | None
        ) = None

        # Timer (wird von außen gesetzt, z.B. QTimer)
        self._timer: "QTimer | None" = None
        self._running = False

        # Create helpers (composition pattern)
        self._management = PositionMonitorManagement(self)
        self._exit_checks = PositionMonitorExitChecks(self)
        self._trailing = PositionMonitorTrailing(self)
        self._price = PositionMonitorPrice(self)
        self._status = PositionMonitorStatus(self)

        logger.info(f"PositionMonitor initialized. Check interval: {check_interval_ms}ms")

    @property
    def has_position(self) -> bool:
        """Gibt True zurück wenn eine Position überwacht wird."""
        return self._position is not None

    @property
    def position(self) -> MonitoredPosition | None:
        """Gibt aktuelle überwachte Position zurück."""
        return self._position

    # === Position Management (Delegiert) ===

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
        """Setzt neue zu überwachende Position (delegiert)."""
        return self._management.set_position(
            symbol, side, entry_price, quantity, stop_loss, take_profit, trailing_atr, trade_log
        )

    def clear_position(self) -> None:
        """Löscht überwachte Position (delegiert)."""
        return self._management.clear_position()

    def restore_position(self, position_data: dict) -> MonitoredPosition | None:
        """Stellt Position aus gespeicherten Daten wieder her (delegiert)."""
        return self._management.restore_position(position_data)

    # === Price Updates (Delegiert) ===

    async def on_price_update(self, price: Decimal) -> ExitResult | None:
        """Wird bei jedem Preis-Update aufgerufen (delegiert)."""
        return await self._price.on_price_update(price)

    # === Exit Triggers (Delegiert) ===

    def trigger_manual_exit(self, reason: str = "Manual exit") -> ExitResult:
        """Triggert manuellen Exit (delegiert)."""
        return self._exit_checks.trigger_manual_exit(reason)

    def trigger_session_end_exit(self) -> ExitResult:
        """Triggert Session-Ende Exit (delegiert)."""
        return self._exit_checks.trigger_session_end_exit()

    def trigger_signal_exit(self, signal_reason: str) -> ExitResult:
        """Triggert Exit durch Signal-Umkehr (delegiert)."""
        return self._exit_checks.trigger_signal_exit(signal_reason)

    # === Callbacks (Delegiert) ===

    def set_exit_callback(
        self,
        callback: Callable[[MonitoredPosition, ExitResult], Awaitable[None]],
    ) -> None:
        """Setzt Callback für Exit-Events (delegiert)."""
        return self._status.set_exit_callback(callback)

    def set_trailing_callback(
        self,
        callback: Callable[[MonitoredPosition, Decimal, Decimal], Awaitable[None]],
    ) -> None:
        """Setzt Callback für Trailing-Stop Updates (delegiert)."""
        return self._status.set_trailing_callback(callback)

    def set_price_callback(
        self,
        callback: Callable[[MonitoredPosition], Awaitable[None]],
    ) -> None:
        """Setzt Callback für Preis-Updates (delegiert)."""
        return self._status.set_price_callback(callback)

    # === Status (Delegiert) ===

    def get_position_status(self) -> dict | None:
        """Gibt aktuellen Position-Status zurück (delegiert)."""
        return self._status.get_position_status()

    def get_sl_tp_distance(self) -> tuple[Decimal, Decimal] | None:
        """Gibt aktuelle Distanz zu SL und TP zurück (delegiert)."""
        return self._status.get_sl_tp_distance()


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
