"""Bot Tab Control Pipeline - Main Engine Pipeline Execution.

Refactored from 1,160 LOC monolith using composition pattern.

Module 2/6 of bot_tab_control.py split.

Contains:
- process_market_data_through_engines(): Main pipeline execution
- _check_and_run_pipeline(): Performance-optimized pipeline trigger
- _has_new_bar(): Bar change detection
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.trading_bot import MarketContext

# Import für JSON Entry Integration
from src.core.trading_bot.entry_score_engine import EntryScoreResult
from src.core.trading_bot.entry_score_types import ScoreDirection, ScoreQuality
from src.core.tradingbot.models import TradeSide

logger = logging.getLogger(__name__)


class BotTabControlPipeline:
    """Helper für Main Engine Pipeline Execution."""

    def __init__(self, parent):
        """
        Args:
            parent: BotTabControl Instanz
        """
        self.parent = parent

    async def process_market_data_through_engines(self, symbol: str, timeframe: str = "1m") -> None:
        """Holt Marktdaten und schickt sie durch die Engine-Pipeline.

        Pipeline:
        1. DataFrame von HistoryManager holen
        2. MarketContext bauen (via MarketContextBuilder)
        3. EntryScore berechnen
        4. LLM Validation (Quick→Deep)
        5. Trigger prüfen
        6. Leverage berechnen
        7. Ergebnisse speichern für Status Panel

        Args:
            symbol: Trading-Symbol (z.B. "BTCUSDT")
            timeframe: Timeframe (z.B. "1m", "5m")
        """
        if not self.parent.parent._context_builder or not self.parent.parent._history_manager:
            logger.warning(
                f"Pipeline skipped - context_builder={self.parent.parent._context_builder is not None}, "
                f"history_manager={self.parent.parent._history_manager is not None}"
            )
            return

        try:
            # 1. DataFrame holen (letzten 200 Kerzen für Indikatoren)
            df = await self.parent.parent._history_manager.get_historical_data(
                symbol=symbol,
                timeframe=timeframe,
                limit=200,
            )

            if df is None or df.empty:
                logger.warning(f"No data available for {symbol} {timeframe}")
                return

            # 2. MarketContext bauen
            context = self.parent.parent._context_builder.build(df, symbol=symbol, timeframe=timeframe)
            self.parent.parent._last_market_context = context
            logger.debug(f"MarketContext built: {context.context_id}")

            # 3. EntryScore berechnen
            if self.parent.parent._entry_score_engine:
                # PRÜFE: Ist JSON Entry Scorer aktiv?
                if self.parent._control._json_entry_scorer:
                    # === JSON ENTRY FLOW (NEU) ===
                    logger.debug("Using JSON Entry Scorer (CEL-based)")
                    entry_result = self._evaluate_json_entry(context, symbol, timeframe)
                    self.parent.parent._last_entry_score = entry_result
                    logger.debug(
                        f"JSON Entry Score: {entry_result.final_score:.3f} "
                        f"({entry_result.direction.value}, {entry_result.quality.value})"
                    )
                else:
                    # === STANDARD ENTRY FLOW ===
                    logger.debug("Using standard EntryScoreEngine")
                    entry_result = self.parent.parent._entry_score_engine.calculate(context)
                    self.parent.parent._last_entry_score = entry_result
                    logger.debug(f"Entry Score: {entry_result.final_score:.3f} ({entry_result.quality.value})")

            # 4. LLM Validation (Quick→Deep)
            if self.parent.parent._llm_validation and self.parent.parent._last_entry_score:
                llm_result = await self.parent.parent._llm_validation.validate(
                    context=context,
                    entry_score=self.parent.parent._last_entry_score.final_score,
                    direction="long" if self.parent.parent._last_entry_score.direction.value == "long" else "short",
                )
                self.parent.parent._last_llm_result = llm_result
                logger.debug(f"LLM Validation: {llm_result.action.value} (tier={llm_result.tier.value})")

            # 5. Trigger prüfen
            if self.parent.parent._trigger_exit_engine and self.parent.parent._last_entry_score:
                trigger_result = self.parent.parent._trigger_exit_engine.check_trigger(
                    context=context,
                    direction=(
                        "long"
                        if self.parent.parent._last_entry_score.direction.value == "long"
                        else "short"
                    ),
                )
                self.parent.parent._last_trigger_result = trigger_result
                logger.debug(
                    f"Trigger: {trigger_result.status.value} (type={trigger_result.trigger_type.value if trigger_result.trigger_type else 'None'})"
                )

            # 6. Leverage berechnen
            if self.parent.parent._leverage_engine:
                leverage_result = self.parent.parent._leverage_engine.calculate(
                    symbol=symbol,
                    regime=context.regime.regime_type,
                )
                self.parent.parent._last_leverage_result = leverage_result
                logger.debug(f"Leverage: {leverage_result.final_leverage:.1f}x (action={leverage_result.action.value})")

            # 7. Trade-Ausführung (falls Trigger aktiv und keine offene Position)
            await self.parent._trade_helper._execute_trade_if_triggered(symbol=symbol, context=context)

            # 8. Position Monitoring (falls offene Position)
            await self.parent._trade_helper._monitor_open_position(context=context)

            # 9. Status Panel aktualisieren (falls sichtbar)
            if self.parent.parent._status_panel and self.parent.parent.status_panel_btn.isChecked():
                self.parent._ui_helper._update_status_panel()

            # 10. Journal Log (mit MarketContext ID)
            self.parent._ui_helper._log_engine_results_to_journal()

        except Exception as e:
            logger.exception(f"Failed to process market data through engines: {e}")
            self.parent._log(f"❌ Engine-Pipeline Fehler: {e}")

    async def _check_and_run_pipeline(self, symbol: str, timeframe: str) -> None:
        """Prüft ob neuer Bar existiert und startet Pipeline nur dann (Performance).

        Args:
            symbol: Trading-Symbol (z.B. "BTCUSDT")
            timeframe: Zeiteinheit (z.B. "1m", "5m", "15m")
        """
        try:
            # Check if new bar exists
            has_new_bar = await self._has_new_bar(symbol, timeframe)

            if has_new_bar:
                # Neuer Bar → Full Pipeline ausführen
                logger.debug(f"New bar detected at {symbol} {timeframe} - running pipeline")
                await self.process_market_data_through_engines(
                    symbol=symbol,
                    timeframe=timeframe,
                )
            else:
                # Kein neuer Bar → nur lightweight P&L Update
                if self.parent.parent._current_position and self.parent.parent._last_market_context:
                    # Get latest tick price for P&L update
                    if self.parent.parent._history_manager:
                        df = await self.parent.parent._history_manager.get_historical_data(
                            symbol=symbol,
                            timeframe="1s",  # Latest tick
                            limit=1,
                        )
                        if df is not None and not df.empty and "close" in df.columns:
                            current_price = float(df["close"].iloc[-1])
                            self.parent._ui_helper._update_sltp_bar(current_price)
        except Exception as e:
            logger.exception(f"Failed to check and run pipeline: {e}")

    async def _has_new_bar(self, symbol: str, timeframe: str) -> bool:
        """Prüft ob ein neuer Bar vorhanden ist (Performance-Optimierung).

        Args:
            symbol: Trading-Symbol
            timeframe: Zeiteinheit

        Returns:
            True wenn neuer Bar existiert, False sonst
        """
        try:
            if not self.parent.parent._history_manager:
                return False

            # Get latest 2 bars
            df = await self.parent.parent._history_manager.get_historical_data(
                symbol=symbol,
                timeframe=timeframe,
                limit=2,
            )

            if df is None or df.empty or "time" not in df.columns:
                return False

            # Get latest bar timestamp
            latest_timestamp = int(df["time"].iloc[-1])

            # Compare with last processed timestamp
            if latest_timestamp != self.parent.parent._last_bar_timestamp:
                self.parent.parent._last_bar_timestamp = latest_timestamp
                logger.debug(f"New bar timestamp: {latest_timestamp} (previous: {self.parent.parent._last_bar_timestamp})")
                return True

            return False
        except Exception as e:
            logger.exception(f"Failed to check for new bar: {e}")
            return False  # Skip pipeline on error

    def _evaluate_json_entry(
        self,
        context: "MarketContext",
        symbol: str,
        timeframe: str,
    ) -> EntryScoreResult:
        """Evaluiert JSON Entry via CEL Expression (NEU).

        Verwendet JsonEntryScorer statt EntryScoreEngine für JSON-basierte Entry-Logik.
        Unterstützt trigger_regime_analysis() und last_closed_regime() über chart_window.

        Args:
            context: MarketContext mit features und regime
            symbol: Trading Symbol
            timeframe: Timeframe

        Returns:
            EntryScoreResult kompatibel mit Pipeline
        """
        json_scorer = self.parent._control._json_entry_scorer

        # Get chart_window reference for CEL regime functions
        # This allows trigger_regime_analysis() and last_closed_regime() to work
        chart_window = self._get_active_chart_window(symbol)

        # Get prev_regime from BotController for new_regime_detected()
        # prev_regime is the regime BEFORE the current candle-close
        prev_regime = None
        if hasattr(self.parent._control, '_prev_regime_name'):
            prev_regime = self.parent._control._prev_regime_name
        elif context.regime:
            # Fallback: use current regime state (less accurate for detection)
            prev_regime = context.regime.regime_state.regime.value

        logger.debug(f"JSON Entry: chart_window={type(chart_window).__name__ if chart_window else 'None'}, prev_regime={prev_regime}")

        # 1. Evaluiere Long Entry
        should_enter_long, score_long, reasons_long = json_scorer.should_enter_long(
            features=context.features,
            regime=context.regime.regime_state,
            chart_window=chart_window,  # Pass chart_window for CEL functions
            prev_regime=prev_regime,
        )

        # 2. Evaluiere Short Entry
        should_enter_short, score_short, reasons_short = json_scorer.should_enter_short(
            features=context.features,
            regime=context.regime.regime_state,
            chart_window=chart_window,  # Pass chart_window for CEL functions
            prev_regime=prev_regime,
        )

        # 3. Bestimme Direction basierend auf Signals
        if should_enter_long and should_enter_short:
            # Beide Signale → Wähle das mit höherem Score
            if score_long >= score_short:
                direction = ScoreDirection.LONG
                final_score = score_long
                reason_codes = reasons_long
            else:
                direction = ScoreDirection.SHORT
                final_score = score_short
                reason_codes = reasons_short
        elif should_enter_long:
            # Nur Long Signal
            direction = ScoreDirection.LONG
            final_score = score_long
            reason_codes = reasons_long
        elif should_enter_short:
            # Nur Short Signal
            direction = ScoreDirection.SHORT
            final_score = score_short
            reason_codes = reasons_short
        else:
            # Kein Signal
            direction = ScoreDirection.NEUTRAL
            final_score = 0.0
            reason_codes = ["NO_ENTRY_SIGNAL"]

        # 4. Bestimme Quality basierend auf Score
        if final_score >= 0.80:
            quality = ScoreQuality.EXCELLENT
        elif final_score >= 0.65:
            quality = ScoreQuality.GOOD
        elif final_score >= 0.50:
            quality = ScoreQuality.FAIR
        else:
            quality = ScoreQuality.POOR

        # 5. Erstelle EntryScoreResult (kompatibel mit Pipeline)
        entry_result = EntryScoreResult(
            raw_score=final_score,
            final_score=final_score,
            direction=direction,
            quality=quality,
            components=[],  # Keine Component-Breakdown bei JSON Entry
            gate_result=None,  # Keine Gates bei JSON Entry
            symbol=symbol,
            timeframe=timeframe,
            current_price=context.current_price,
            regime=context.regime.regime_state.regime.value,
        )

        # 6. Log Reason Codes (für Debugging)
        if reason_codes:
            logger.debug(f"JSON Entry Reasons: {', '.join(reason_codes)}")

        return entry_result

    def _get_active_chart_window(self, symbol: str):
        """Find active ChartWindow for the given symbol.

        Traverses the Qt widget hierarchy to find a ChartWindow that:
        1. Has the RegimeDisplayMixin (via chart_widget)
        2. Matches the trading symbol

        Args:
            symbol: Trading symbol to match (e.g. "BTCUSDT")

        Returns:
            ChartWindow/Widget instance or None if not found
        """
        try:
            from PyQt6.QtWidgets import QApplication

            # 1. Try parent traversal (fastest if embedded)
            current = self.parent.parent
            while current:
                if type(current).__name__ == "ChartWindow":
                    # Check symbol match
                    chart_symbol = getattr(current, "symbol", "") or getattr(current, "current_symbol", "")
                    if chart_symbol and symbol.upper() in str(chart_symbol).upper():
                        if hasattr(current, "chart_widget"):
                            return current.chart_widget
                    break
                # Qt parent traversal
                current = current.parent() if hasattr(current, "parent") else None

            # 2. Search all top-level windows
            for window in QApplication.topLevelWidgets():
                if type(window).__name__ == "ChartWindow":
                    # Check symbol
                    chart_symbol = getattr(window, "symbol", "") or getattr(window, "current_symbol", "")
                    if chart_symbol and symbol.upper() in str(chart_symbol).upper():
                         if hasattr(window, "chart_widget"):
                             return window.chart_widget

                # Also check direct chart widgets (if detached)
                if hasattr(window, "current_symbol"):
                     # Check if it is the chart widget itself
                     curr_sym = getattr(window, "current_symbol", "")
                     if curr_sym and symbol.upper() in str(curr_sym).upper():
                         if hasattr(window, "_last_regime_name"):
                             return window

            logger.debug(f"No ChartWindow found for {symbol}")
            return None

        except Exception as e:
            logger.warning(f"Failed to find ChartWindow: {e}")
            return None
