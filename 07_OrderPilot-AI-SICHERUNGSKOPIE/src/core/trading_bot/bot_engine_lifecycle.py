"""Bot Engine Lifecycle - Start/Stop and Analysis Loop.

Refactored from bot_engine.py.

Contains:
- start: Start bot lifecycle (connect adapter, load position or start analysis)
- stop: Stop bot (cancel tasks, handle open positions)
- _run_analysis_loop: Main analysis loop with interval timing
- _run_analysis_cycle: Single analysis cycle (market data, indicators, regime, signal generation, AI validation, trade execution)
- _check_exit_signal: Check for exit signals when in position
- _get_balance: Get current account balance
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING

from .bot_types import BotState
from .position_monitor import ExitResult, ExitTrigger

if TYPE_CHECKING:
    from .bot_engine import TradingBotEngine

logger = logging.getLogger(__name__)


class BotEngineLifecycle:
    """Helper for bot lifecycle management."""

    def __init__(self, parent: "TradingBotEngine"):
        self.parent = parent

    async def start(self) -> None:
        """Startet den Bot."""
        if self.parent._running:
            self.parent._callbacks._log("Bot is already running")
            return

        self.parent._callbacks._set_state(BotState.STARTING)
        self.parent._running = True

        try:
            # Adapter verbinden
            if not self.parent.adapter.connected:
                await self.parent.adapter.connect()
                self.parent._callbacks._log("Adapter connected")

            # Stats zurücksetzen wenn neuer Tag
            self.parent._statistics._check_daily_reset()

            # Gespeicherte Position laden (falls vorhanden)
            if self.parent._persistence.load_position():
                self.parent._callbacks._log("Weiter mit wiederhergestellter Position")
                # State ist bereits IN_POSITION durch load_position()
            else:
                # Analysis-Loop starten (nur wenn keine Position)
                self.parent._analysis_task = asyncio.create_task(self._run_analysis_loop())
                self.parent._callbacks._set_state(BotState.ANALYZING)

            self.parent._callbacks._log("Bot started successfully")

        except Exception as e:
            self.parent._last_error = str(e)
            self.parent._callbacks._set_state(BotState.ERROR)
            self.parent._callbacks._log(f"Failed to start: {e}")
            if self.parent._on_error:
                self.parent._on_error(str(e))

    async def stop(self, close_position: bool = False) -> None:
        """
        Stoppt den Bot.

        Args:
            close_position: True = Position schließen, False = Position speichern
        """
        if not self.parent._running:
            return

        self.parent._callbacks._set_state(BotState.STOPPING)
        self.parent._running = False

        # Analysis-Task stoppen
        if self.parent._analysis_task:
            self.parent._analysis_task.cancel()
            try:
                await self.parent._analysis_task
            except asyncio.CancelledError:
                pass

        # Offene Position behandeln
        if self.parent.has_position:
            if close_position:
                self.parent._callbacks._log("Position wird geschlossen...")
                exit_result = ExitResult(
                    should_exit=True,
                    trigger=ExitTrigger.BOT_STOPPED,
                    trigger_price=self.parent.position_monitor.position.current_price,
                    reason="Bot stopped",
                )
                await self.parent.trade_handler.close_position(exit_result)
            else:
                # Position speichern für nächsten Start
                self.parent._callbacks._log("Position wird für nächsten Start gespeichert...")
                self.parent._persistence.save_position()

        self.parent._callbacks._set_state(BotState.IDLE)
        self.parent._callbacks._log("Bot stopped")

    async def _run_analysis_loop(self) -> None:
        """Haupt-Analyse-Loop."""
        interval = self.parent.config.analysis_interval_seconds

        while self.parent._running:
            try:
                await self._run_analysis_cycle()
                await asyncio.sleep(interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.parent._callbacks._log(f"Analysis error: {e}")
                logger.exception("Analysis cycle error")
                await asyncio.sleep(interval)

    async def _run_analysis_cycle(self) -> None:
        """Ein Analyse-Zyklus."""
        if not self.parent._running:
            return

        # Keine Analyse wenn Position offen und Monitor aktiv
        if self.parent._state == BotState.IN_POSITION:
            # Nur Exit-Signal prüfen
            await self._check_exit_signal()
            return

        self.parent._callbacks._set_state(BotState.ANALYZING)

        # Marktdaten holen
        df = await self.parent.market_analyzer.fetch_market_data()
        if df is None or df.empty:
            self.parent._callbacks._log("No market data available")
            return

        # Indikatoren berechnen (falls noch nicht vorhanden)
        if "ema_20" not in df.columns:
            df = self.parent.market_analyzer.calculate_indicators(df)

        # Regime erkennen
        regime = self.parent.market_analyzer.detect_regime(df)

        # Signal generieren
        signal = self.parent.signal_generator.generate_signal(
            df=df,
            regime=regime,
            require_regime_alignment=self.parent.config.require_regime_alignment,
        )

        self.parent._last_signal = signal
        self.parent._last_analysis_time = datetime.now(timezone.utc)
        self.parent._stats.signals_generated += 1

        if self.parent._on_signal_generated:
            self.parent._on_signal_generated(signal)

        # Kein valides Signal
        if not signal.is_valid:
            self.parent._callbacks._set_state(BotState.WAITING_SIGNAL)
            self.parent._stats.signals_rejected_confluence += 1
            return

        self.parent._callbacks._log(
            f"Signal: {signal.direction.value} "
            f"(Confluence: {signal.confluence_score}/5)"
        )

        # Immer Indikatoren und Kontext extrahieren (für Logging)
        indicators = self.parent.signal_generator.extract_indicator_snapshot(df)
        market_context = self.parent.market_analyzer.extract_market_context(df, regime)

        # AI Validation - IMMER wenn aktiviert!
        if self.parent.ai_validator.enabled:
            self.parent._callbacks._set_state(BotState.VALIDATING)

            ai_result = await self.parent.ai_validator.validate_signal_async(
                signal=signal,
                market_data=df,
                market_context=market_context,
            )

            if not ai_result.approved:
                self.parent._callbacks._log(f"AI rejected: {ai_result.reason}")
                self.parent._stats.signals_rejected_ai += 1
                self.parent._callbacks._set_state(BotState.WAITING_SIGNAL)
                return

            self.parent._callbacks._log(f"AI approved: {ai_result.confidence:.2%}")

        # Signal approved - Trade ausführen
        await self.parent.trade_handler.execute_trade(signal, indicators, market_context)

    async def _check_exit_signal(self) -> None:
        """Prüft auf Exit-Signal."""
        # Position Monitor checkt automatisch SL/TP
        # Hier könnten zusätzliche Checks rein (z.B. Signal-Reversal)
        pass

    async def _get_balance(self) -> Decimal:
        """Holt aktuelle Balance."""
        try:
            account = await self.parent.adapter.get_account()
            if account and account.equity:
                return account.equity
            return Decimal("10000")  # Fallback
        except Exception as e:
            logger.error(f"Failed to get balance: {e}")
            return Decimal("10000")
