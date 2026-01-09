"""Backtest Runner Loop - Main Execution Loop.

Refactored from 832 LOC monolith using composition pattern.

Module 2/5 of backtest_runner.py split.

Contains:
- Main execution loop (run method)
- Candle processing (_process_candle)
- State initialization and daily resets
- Risk checks
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from .backtest_runner_state import BacktestState

if TYPE_CHECKING:
    from .config import BacktestResult, CandleSnapshot

logger = logging.getLogger(__name__)


class BacktestRunnerLoop:
    """Helper für Main Execution Loop."""

    def __init__(self, parent):
        """
        Args:
            parent: BacktestRunner Instanz
        """
        self.parent = parent

    async def run(self) -> "BacktestResult":
        """Führt den Backtest durch."""
        try:
            # 1. Initialisierung
            self._emit_progress(0, "Initialisiere...")
            self._init_state()

            # 2. Daten laden (via ReplayProvider)
            self._emit_progress(10, "Lade Daten...")
            bar_count = await self.parent.replay_provider.load_data(
                symbol=self.parent.config.symbol,
                start=self.parent.config.start_date,
                end=self.parent.config.end_date,
                timeframe=self.parent.config.base_timeframe,
            )

            if bar_count == 0:
                logger.warning("Keine Daten geladen - Backtest abgebrochen")
                return self.parent._metrics_helper._calculate_result()

            logger.info(f"✅ {bar_count} Bars geladen")

            # 3. Haupt-Loop
            self._emit_progress(20, f"Verarbeite {bar_count} Bars...")

            iterator = self.parent.replay_provider.replay_iter()
            processed = 0

            async for candle, history in iterator:
                if self.parent._stop_requested:
                    logger.info("🛑 Backtest gestoppt durch User")
                    break

                await self._process_candle(candle, history)

                processed += 1
                if processed % 100 == 0:
                    progress = 20 + int((processed / bar_count) * 70)
                    self._emit_progress(progress, f"{processed}/{bar_count} Bars")

            # 4. Alle Positionen schließen (EOD)
            self._emit_progress(95, "Schließe offene Positionen...")
            await self.parent._positions_helper._close_all_positions("End of Backtest")

            # 5. Result berechnen
            self._emit_progress(98, "Berechne Metriken...")
            result = self.parent._metrics_helper._calculate_result()

            self._emit_progress(100, "✅ Backtest abgeschlossen")
            logger.info(
                f"✅ Backtest abgeschlossen: {result.metrics.total_trades} Trades, "
                f"{result.metrics.total_return_pct:.1f}% Return"
            )

            return result

        except Exception as e:
            logger.exception(f"Backtest-Fehler: {e}")
            raise

    def _init_state(self) -> None:
        """Initialisiert den Backtest-Zustand."""
        self.parent.state = BacktestState(
            equity=self.parent.config.initial_capital,
            cash=self.parent.config.initial_capital,
        )
        logger.info(f"Backtest-State initialisiert: ${self.parent.config.initial_capital:,.2f}")

    async def _process_candle(self, candle: "CandleSnapshot", history_1m: list["CandleSnapshot"]) -> None:
        """Verarbeitet eine einzelne Candle."""
        # Daily Reset Check
        self._check_daily_reset(candle.datetime)

        # MTF Daten holen
        mtf_data = self.parent.mtf_resampler.get_current_timeframes(candle.bar_index)

        # Positions managen (SL/TP Check)
        await self.parent._positions_helper._manage_positions(candle, history_1m, mtf_data)

        # Signal generieren (falls keine Position offen)
        if not self.parent.state.open_positions:
            # Risk Checks
            if not self._risk_check_passed():
                return

            signal = await self.parent._signals_helper._generate_signal(candle, history_1m, mtf_data)

            if signal:
                await self.parent._signals_helper._execute_signal(signal, candle)

        # Equity Curve updaten
        self.parent._positions_helper._update_equity_curve(candle.datetime, candle.close)

    def _check_daily_reset(self, time: datetime) -> None:
        """Prüft ob neuer Tag und resettet daily_pnl/trade_count."""
        current_date = time.date()

        if self.parent.state.last_reset_date is None:
            self.parent.state.last_reset_date = current_date
            return

        if current_date > self.parent.state.last_reset_date:
            logger.debug(f"Daily Reset: {current_date} | PnL: {self.parent.state.daily_pnl:+.2f}")
            self.parent.state.daily_pnl = 0.0
            self.parent.state.trade_count_today = 0
            self.parent.state.last_reset_date = current_date

    def _risk_check_passed(self) -> bool:
        """Prüft Risk-Limits (Daily Loss, Max Trades, Cooldown)."""
        # Max Daily Loss Check
        if self.parent.state.daily_pnl < -self.parent.config.risk.max_daily_loss:
            return False

        # Max Trades per Day
        if self.parent.state.trade_count_today >= self.parent.config.risk.max_trades_per_day:
            return False

        # Loss Streak Cooldown
        if self.parent.state.loss_streak >= self.parent.config.risk.max_loss_streak:
            if self.parent.state.cooldown_until is None:
                # Setze Cooldown (1 Tag)
                if self.parent.replay_provider.data is not None and not self.parent.replay_provider.data.empty:
                    last_row = self.parent.replay_provider.data.iloc[-1]
                    current_time = datetime.fromtimestamp(last_row["timestamp"] / 1000, tz=timezone.utc)
                    from datetime import timedelta

                    self.parent.state.cooldown_until = current_time + timedelta(days=1)
                    logger.warning(f"⚠️ Loss Streak Cooldown aktiviert bis {self.parent.state.cooldown_until}")

            # Cooldown aktiv?
            if self.parent.state.cooldown_until:
                if self.parent.replay_provider.data is not None and not self.parent.replay_provider.data.empty:
                    last_row = self.parent.replay_provider.data.iloc[-1]
                    current_time = datetime.fromtimestamp(last_row["timestamp"] / 1000, tz=timezone.utc)
                    if current_time < self.parent.state.cooldown_until:
                        return False

        return True

    def _emit_progress(self, progress: int, message: str) -> None:
        """Sendet Progress-Update via Callback."""
        if self.parent.progress_callback:
            self.parent.progress_callback(progress, message)
