"""
BotTabMonitoringMixin - Position monitoring and display methods

This mixin is part of the split BotTab implementation.
Contains methods extracted from bot_tab.py for better modularity.
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import TYPE_CHECKING

import qasync
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QColor, QTextCursor
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QGroupBox,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QFrame,
    QProgressBar,
    QSplitter,
    QHeaderView,
    QMessageBox,
)

if TYPE_CHECKING:
    from src.core.broker.bitunix_paper_adapter import BitunixPaperAdapter
    from src.core.market_data.history_provider import HistoryManager

from src.core.trading_bot import (
    BotState,
    BotConfig,
    BotStatistics,
    SignalDirection,
    TradeSignal,
    MonitoredPosition,
    ExitResult,
    TradeLogEntry,
    MarketContext,
    RegimeType,
)

try:
    from src.ui.widgets.trading_status_panel import TradingStatusPanel
    HAS_STATUS_PANEL = True
except ImportError:
    HAS_STATUS_PANEL = False

try:
    from src.ui.widgets.trading_journal_widget import TradingJournalWidget
    HAS_JOURNAL = True
except ImportError:
    HAS_JOURNAL = False

logger = logging.getLogger(__name__)

BOT_SETTINGS_FILE = Path("config/bot_settings.json")


class BotTabMonitoringMixin:
    """Position monitoring and display methods"""

    def _on_status_panel_refresh(self) -> None:
        """Callback wenn Status Panel Refresh angefordert wird."""
        self._update_status_panel()

    def _update_status_panel(self) -> None:
        """Aktualisiert das Status Panel mit aktuellen Engine-Ergebnissen.

        Nutzt die Ergebnisse aus der neuen Engine-Pipeline:
        - self._last_regime_result (von RegimeDetectorService)
        - self._last_entry_score (von EntryScoreEngine)
        - self._last_llm_result (von LLMValidationService)
        - self._last_trigger_result (von TriggerExitEngine)
        - self._last_leverage_result (von LeverageRulesEngine)
        """
        if not self._status_panel:
            return

        try:
            # Regime Result
            regime_result = None
            if self._last_market_context and self._last_market_context.regime:
                regime_result = self._last_market_context.regime

            # Entry Score Result
            score_result = self._last_entry_score

            # LLM Validation Result
            llm_result = self._last_llm_result

            # Trigger Result
            trigger_result = self._last_trigger_result

            # Leverage Result
            leverage_result = self._last_leverage_result

            # Update all at once
            self._status_panel.update_all(
                regime_result=regime_result,
                score_result=score_result,
                llm_result=llm_result,
                trigger_result=trigger_result,
                leverage_result=leverage_result,
            )

            logger.debug("Status Panel updated with new engine results")

        except Exception as e:
            logger.warning(f"Failed to update status panel: {e}")

    # === Phase 5.4: Journal Methods ===

    def _toggle_journal(self) -> None:
        """Togglet die Sichtbarkeit des Trading Journals."""
        if self._journal_widget:
            visible = self.journal_btn.isChecked()
            self._journal_widget.setVisible(visible)
            if visible:
                self._log("📔 Trading Journal eingeblendet")
                self._journal_widget.refresh_trades()
            else:
                self._log("📔 Trading Journal ausgeblendet")

    # NOTE: WhatsApp Methods wurden in das ChartWindow Trading Bot Panel verschoben
    # (siehe panels_mixin.py und whatsapp_widget.py)

    def _log_signal_to_journal(self, signal: TradeSignal) -> None:
        """Loggt ein Signal ins Journal."""
        if not self._journal_widget:
            return

        # Symbol aus Config laden (neue Pipeline)
        config = self._get_current_config()
        signal_data = {
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "symbol": config.symbol if config else "-",
            "direction": signal.direction.value if hasattr(signal.direction, 'value') else str(signal.direction),
            "score": getattr(signal, 'entry_score', 0) or len(signal.conditions_met) / 5,
            "quality": getattr(signal, 'quality', 'MODERATE'),
            "gate_status": getattr(signal, 'gate_status', 'PASSED'),
            "trigger": signal.regime or "-",
        }
        self._journal_widget.add_signal(signal_data)

    def _log_llm_to_journal(self, llm_result: dict) -> None:
        """Loggt ein LLM-Ergebnis ins Journal."""
        if not self._journal_widget:
            return

        # Symbol aus Config laden (neue Pipeline)
        config = self._get_current_config()
        llm_data = {
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "symbol": config.symbol if config else "-",
            **llm_result,
        }
        self._journal_widget.add_llm_output(llm_data)

    def _log_error_to_journal(self, error_msg: str, context: str = "") -> None:
        """Loggt einen Fehler ins Journal."""
        if not self._journal_widget:
            return

        error_data = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "type": "ERROR",
            "message": error_msg,
            "context": context,
        }
        self._journal_widget.add_error(error_data)

    # === Bot Engine ===

    # OLD: _initialize_bot_engine() REMOVED - using new engine pipeline
    # def _initialize_bot_engine(): DELETED

    def _initialize_new_engines(self) -> None:
        """Initialisiert die neuen Engines (Phase 1-4).

        Diese Methode erstellt alle neuen Trading-Engines:
        - MarketContextBuilder: Baut MarketContext aus DataFrame
        - RegimeDetectorService: Erkennt Markt-Regime
        - LevelEngine: Erkennt Support/Resistance Levels
        - EntryScoreEngine: Berechnet normalisierten Entry-Score
        - LLMValidationService: AI-Validierung (Quick→Deep)
        - TriggerExitEngine: Entry-Trigger + Exit-Management
        - LeverageRulesEngine: Dynamisches Leverage-Regelwerk
        """
        try:
            # 1. MarketContextBuilder - Single Source of Truth
            builder_config = MarketContextBuilderConfig(
                enable_caching=True,
                enable_preflight=True,
                require_regime=True,
                require_levels=True,
            )
            self._context_builder = MarketContextBuilder(config=builder_config)
            logger.info("✅ MarketContextBuilder initialized")

            # 2. RegimeDetectorService
            regime_config = RegimeConfig(
                trend_lookback=50,
                volatility_lookback=20,
                threshold_strong_trend=0.7,
                threshold_weak_trend=0.4,
                threshold_chop=0.3,
            )
            self._regime_detector = RegimeDetectorService(config=regime_config)
            logger.info("✅ RegimeDetectorService initialized")

            # 3. LevelEngine
            level_config = LevelEngineConfig(
                swing_lookback=20,
                min_touches=2,
                price_tolerance_pct=0.5,
                enable_daily_levels=True,
                enable_weekly_levels=True,
            )
            self._level_engine = LevelEngine(config=level_config)
            logger.info("✅ LevelEngine initialized")

            # 4. EntryScoreEngine
            entry_config = EntryScoreConfig(
                # Weights
                weight_trend=0.25,
                weight_rsi=0.15,
                weight_macd=0.15,
                weight_adx=0.15,
                weight_volatility=0.15,
                weight_volume=0.15,
                # Quality thresholds
                score_excellent=0.8,
                score_good=0.6,
                score_acceptable=0.4,
            )
            self._entry_score_engine = EntryScoreEngine(config=entry_config)
            logger.info("✅ EntryScoreEngine initialized")

            # 5. LLMValidationService
            llm_config = LLMValidationConfig(
                quick_threshold_score=0.7,
                deep_threshold_score=0.5,
                veto_modifier=-0.3,
                boost_modifier=0.2,
                enable_quick=True,
                enable_deep=True,
            )
            self._llm_validation = LLMValidationService(config=llm_config)
            logger.info("✅ LLMValidationService initialized")

            # 6. TriggerExitEngine
            trigger_config = TriggerExitConfig(
                # Entry triggers
                enable_breakout=True,
                enable_pullback=True,
                enable_sfp=True,
                # Exit settings
                use_atr_stops=True,
                atr_sl_multiplier=2.0,
                atr_tp_multiplier=3.0,
                enable_trailing=True,
            )
            self._trigger_exit_engine = TriggerExitEngine(config=trigger_config)
            logger.info("✅ TriggerExitEngine initialized")

            # 7. LeverageRulesEngine
            leverage_config = LeverageRulesConfig(
                # Asset tiers
                tier_blue_chip_max=5.0,
                tier_mid_cap_max=3.0,
                tier_small_cap_max=2.0,
                # Regime modifiers
                strong_trend_modifier=1.0,
                weak_trend_modifier=0.7,
                chop_range_modifier=0.5,
                volatility_explosive_modifier=0.3,
            )
            self._leverage_engine = LeverageRulesEngine(config=leverage_config)
            logger.info("✅ LeverageRulesEngine initialized")

            self._log("✅ Alle neuen Engines initialisiert (Phase 1-4)")

        except Exception as e:
            logger.exception("Failed to initialize new engines")
            self._log(f"❌ Fehler bei Engine-Initialisierung: {e}")
            raise

    def update_engine_configs(self) -> None:
        """Aktualisiert die Konfiguration aller laufenden Engines.

        Lädt Config-Files und wendet sie auf die laufenden Engine-Instanzen an.
        WICHTIG: Sofort wirksam, kein Bot-Neustart nötig (Punkt 2).
        """
        if not self._context_builder:
            logger.warning("Engines not initialized yet - skipping config update")
            return

        try:
            from src.core.trading_bot import (
                load_entry_score_config,
                load_trigger_exit_config,
                load_leverage_config,
                load_llm_validation_config,
            )

            # 1. Entry Score Config laden und anwenden
            if self._entry_score_engine:
                entry_config = load_entry_score_config()
                self._entry_score_engine.config = entry_config
                logger.info(f"✅ EntryScoreEngine config updated: weights={entry_config.weight_trend}/{entry_config.weight_rsi}/{entry_config.weight_macd}")

            # 2. Trigger/Exit Config laden und anwenden
            if self._trigger_exit_engine:
                trigger_config = load_trigger_exit_config()
                self._trigger_exit_engine.config = trigger_config
                logger.info(f"✅ TriggerExitEngine config updated: breakout={trigger_config.enable_breakout}, pullback={trigger_config.enable_pullback}")

            # 3. Leverage Config laden und anwenden
            if self._leverage_engine:
                leverage_config = load_leverage_config()
                self._leverage_engine.config = leverage_config
                logger.info(f"✅ LeverageRulesEngine config updated: blue_chip_max={leverage_config.tier_blue_chip_max}x")

            # 4. LLM Validation Config laden und anwenden
            if self._llm_validation:
                llm_config = load_llm_validation_config()
                self._llm_validation.config = llm_config
                logger.info(f"✅ LLMValidationService config updated: quick_threshold={llm_config.quick_threshold_score}")

            # Note: RegimeDetector und LevelEngine haben keine Config-Files
            # (nutzen Builder-Config bzw. fest codierte Werte)

            self._log("⚙️ Engine-Konfigurationen aktualisiert (sofort wirksam)")
            logger.info("All engine configs reloaded and applied to running instances")

        except Exception as e:
            logger.exception(f"Failed to update engine configs: {e}")
            self._log(f"❌ Fehler beim Aktualisieren der Engine-Configs: {e}")
    def _update_sltp_bar(self, current_price: float) -> None:
        """Aktualisiert den visuellen SL/TP Balken im Signals-Tab.

        Der Balken zeigt die Position zwischen SL (0%) und TP (100%):
        - Rot (links) = Stop Loss
        - Orange (mitte) = aktueller Preis
        - Grün (rechts) = Take Profit

        Args:
            current_price: Aktueller Marktpreis
        """
        if not self._current_position:
            return

        try:
            sl_price = self._position_stop_loss
            tp_price = self._position_take_profit
            entry_price = self._position_entry_price
            side = self._position_side

            # Berechne Position zwischen SL und TP (0-100%)
            if side == "long":
                # Long: SL < Entry < Current < TP
                price_range = tp_price - sl_price
                current_offset = current_price - sl_price
            else:
                # Short: TP < Current < Entry < SL
                price_range = sl_price - tp_price
                current_offset = sl_price - current_price

            # Position in % (0 = SL, 100 = TP)
            if price_range > 0:
                position_pct = (current_offset / price_range) * 100
                position_pct = max(0, min(100, position_pct))  # Clamp 0-100
            else:
                position_pct = 50  # Fallback

            # Update Bar
            self.sltp_bar.setValue(int(position_pct))

            # Update Labels
            self.sltp_sl_label.setText(f"SL: {sl_price:.2f}")
            self.sltp_current_label.setText(f"{current_price:.2f}")
            self.sltp_tp_label.setText(f"TP: {tp_price:.2f}")

            # Berechne P&L
            quantity = self._position_quantity
            if side == "long":
                pnl = (current_price - entry_price) * quantity
            else:
                pnl = (entry_price - current_price) * quantity

            pnl_pct = (pnl / (entry_price * quantity)) * 100

            # Update P&L Label mit Farbe
            pnl_color = "#26a69a" if pnl >= 0 else "#ef5350"
            pnl_sign = "+" if pnl >= 0 else ""
            self.sltp_pnl_label.setText(f"P&L: {pnl_sign}${pnl:.2f} ({pnl_sign}{pnl_pct:.2f}%)")
            self.sltp_pnl_label.setStyleSheet(f"color: {pnl_color}; font-weight: bold; font-size: 12px; margin-top: 5px;")

        except Exception as e:
            logger.exception(f"Failed to update SL/TP bar: {e}")

    def _reset_sltp_bar(self) -> None:
        """Setzt den SL/TP Visual Bar auf Default-Werte zurück (keine aktive Position)."""
        try:
            # Reset Labels
            self.sltp_sl_label.setText("SL: —")
            self.sltp_current_label.setText("—")
            self.sltp_tp_label.setText("TP: —")
            self.sltp_pnl_label.setText("P&L: —")
            self.sltp_pnl_label.setStyleSheet("color: #888; font-size: 11px; margin-top: 5px;")

            # Reset Bar
            self.sltp_bar.setValue(50)  # Mitte

            logger.debug("SL/TP bar reset to default state (no position)")
        except Exception as e:
            logger.exception(f"Failed to reset SL/TP bar: {e}")

    def _log_engine_results_to_journal(self) -> None:
        """Loggt Engine-Ergebnisse ins Trading Journal mit MarketContext ID."""
        if not self._journal_widget or not self._last_market_context:
            return

        try:
            # Entry Score
            if self._last_entry_score:
                entry_data = {
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "context_id": self._last_market_context.context_id,
                    "score": self._last_entry_score.final_score,
                    "quality": self._last_entry_score.quality.value,
                    "direction": self._last_entry_score.direction.value,
                    "components": {
                        comp.name: comp.value
                        for comp in self._last_entry_score.components
                    },
                }
                self._journal_widget.add_entry_score(entry_data)

            # LLM Result
            if self._last_llm_result:
                llm_data = {
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "context_id": self._last_market_context.context_id,
                    "action": self._last_llm_result.action.value,
                    "tier": self._last_llm_result.tier.value,
                    "reasoning": self._last_llm_result.reasoning[:200] if self._last_llm_result.reasoning else "",
                }
                self._journal_widget.add_llm_output(llm_data)

        except Exception as e:
            logger.exception(f"Failed to log engine results to journal: {e}")

    def _get_current_config(self) -> BotConfig:
        """Gibt aktuelle Bot-Konfiguration zurück (lädt aus Datei wenn vorhanden)."""
        return self._load_settings()

    def _apply_config(self, config: BotConfig) -> None:
        """Wendet neue Konfiguration an und speichert sie."""
        self._save_settings(config)
        # Neue Pipeline: Engine-Configs sofort aktualisieren
        self.update_engine_configs()
    def _on_state_changed(self, state: BotState) -> None:
        """Callback wenn sich der Bot-State ändert."""
        self.status_changed.emit(state.value)

    def _on_signal_updated(self, signal: TradeSignal) -> None:
        """Callback wenn ein neues Signal generiert wurde."""
        self.signal_updated.emit(signal)
        # Phase 5.4: Log to journal
        self._log_signal_to_journal(signal)

    def _on_position_opened(self, position: MonitoredPosition) -> None:
        """Callback wenn eine Position geöffnet wurde."""
        self.position_updated.emit(position)

    def _on_position_closed(self, trade_log: TradeLogEntry) -> None:
        """Callback wenn eine Position geschlossen wurde."""
        # Position ist jetzt None (geschlossen)
        self.position_updated.emit(None)
        # Statistiken werden über _update_stats_display() aktualisiert
        # (alte _bot_engine.statistics entfernt - neue Pipeline hat eigene Stats)

    def _on_bot_error(self, error: str) -> None:
        """Callback für Bot-Fehler."""
        self._log(f"❌ Fehler: {error}")
        # Phase 5.4: Log to journal
        self._log_error_to_journal(error, context="Bot Engine")

    def _on_bot_log(self, message: str) -> None:
        """Callback für Bot-Log-Nachrichten."""
        self.log_message.emit(message)

    # === UI Updates ===

    def _update_status_display(self, state: str) -> None:
        """Aktualisiert Status-Anzeige."""
        state_config = {
            "IDLE": ("🤖", "#888", "Bot ist gestoppt"),
            "STARTING": ("🔄", "#FFC107", "Bot startet..."),
            "ANALYZING": ("🔍", "#2196F3", "Analysiere Markt..."),
            "WAITING_SIGNAL": ("⏳", "#9C27B0", "Warte auf Signal..."),
            "VALIDATING": ("🧠", "#FF9800", "Validiere Signal mit AI..."),
            "OPENING_POSITION": ("📈", "#4CAF50", "Öffne Position..."),
            "IN_POSITION": ("💰", "#4CAF50", "Position aktiv"),
            "CLOSING_POSITION": ("📉", "#f44336", "Schließe Position..."),
            "STOPPING": ("⏸", "#FFC107", "Bot stoppt..."),
            "ERROR": ("❌", "#f44336", "Fehler aufgetreten"),
        }

        icon, color, detail = state_config.get(state, ("❓", "#888", state))

        self.status_icon.setText(icon)
        self.status_label.setText(state)
        self.status_label.setStyleSheet(f"""
            font-size: 16px;
            font-weight: bold;
            color: {color};
        """)
        self.status_detail.setText(detail)

    def _update_signal_display(self, signal: TradeSignal | None) -> None:
        """Aktualisiert Signal-Anzeige."""
        if signal is None:
            self.signal_direction.setText("—")
            self.signal_direction.setStyleSheet("""
                font-size: 18px; font-weight: bold;
                padding: 5px 15px; border-radius: 4px;
                background-color: #333;
            """)
            self.signal_confluence.setText("—")
            self.signal_regime.setText("Regime: —")
            self.signal_conditions.setText("—")
            self.signal_timestamp.setText("Letztes Update: —")
            return

        # Direction
        if signal.direction == SignalDirection.LONG:
            self.signal_direction.setText("📈 LONG")
            self.signal_direction.setStyleSheet("""
                font-size: 18px; font-weight: bold;
                padding: 5px 15px; border-radius: 4px;
                background-color: #1B5E20; color: #4CAF50;
            """)
        elif signal.direction == SignalDirection.SHORT:
            self.signal_direction.setText("📉 SHORT")
            self.signal_direction.setStyleSheet("""
                font-size: 18px; font-weight: bold;
                padding: 5px 15px; border-radius: 4px;
                background-color: #B71C1C; color: #f44336;
            """)
        else:
            self.signal_direction.setText("— NEUTRAL")
            self.signal_direction.setStyleSheet("""
                font-size: 18px; font-weight: bold;
                padding: 5px 15px; border-radius: 4px;
                background-color: #333;
            """)

        # Confluence
        total = len(signal.conditions_met) + len(signal.conditions_failed)
        met = len(signal.conditions_met)
        self.signal_confluence.setText(f"{met}/{total}")

        # Regime
        self.signal_regime.setText(f"Regime: {signal.regime or '—'}")

        # Conditions
        conditions = ", ".join([c.name for c in signal.conditions_met])
        self.signal_conditions.setText(conditions if conditions else "—")

        # Timestamp
        self.signal_timestamp.setText(f"Update: {datetime.now().strftime('%H:%M:%S')}")

    def _update_position_display(self, position: MonitoredPosition | None) -> None:
        """Aktualisiert Position-Anzeige."""
        if position is None:
            self.pos_side.setText("—")
            self.pos_side.setStyleSheet("font-weight: bold;")
            self.pos_entry.setText("—")
            self.pos_current.setText("—")
            self.pos_sl.setText("—")
            self.pos_tp.setText("—")
            self.pos_pnl.setText("—")
            self.sl_tp_progress.setValue(50)
            self.close_position_btn.setEnabled(False)
            return

        # Side
        if position.side == "BUY":
            self.pos_side.setText("🟢 LONG")
            self.pos_side.setStyleSheet("font-weight: bold; color: #4CAF50;")
        else:
            self.pos_side.setText("🔴 SHORT")
            self.pos_side.setStyleSheet("font-weight: bold; color: #f44336;")

        # Prices
        self.pos_entry.setText(f"${position.entry_price:,.2f}")
        if position.current_price:
            self.pos_current.setText(f"${position.current_price:,.2f}")

        self.pos_sl.setText(f"${position.stop_loss:,.2f}")
        self.pos_tp.setText(f"${position.take_profit:,.2f}")

        # PnL
        pnl = position.unrealized_pnl
        pnl_pct = position.unrealized_pnl_percent
        if pnl >= 0:
            self.pos_pnl.setText(f"+${pnl:,.2f} (+{pnl_pct:.2f}%)")
            self.pos_pnl.setStyleSheet("font-weight: bold; color: #4CAF50;")
        else:
            self.pos_pnl.setText(f"-${abs(pnl):,.2f} ({pnl_pct:.2f}%)")
            self.pos_pnl.setStyleSheet("font-weight: bold; color: #f44336;")

        # Progress Bar (Position zwischen SL und TP)
        if position.current_price and position.stop_loss and position.take_profit:
            price = float(position.current_price)
            sl = float(position.stop_loss)
            tp = float(position.take_profit)

            if position.side == "BUY":
                total_range = tp - sl
                if total_range > 0:
                    progress = int((price - sl) / total_range * 100)
                    progress = max(0, min(100, progress))
                    self.sl_tp_progress.setValue(progress)
            else:  # SHORT
                total_range = sl - tp
                if total_range > 0:
                    progress = int((sl - price) / total_range * 100)
                    progress = max(0, min(100, progress))
                    self.sl_tp_progress.setValue(progress)

        self.close_position_btn.setEnabled(True)

    def _update_stats_display(self, stats: BotStatistics) -> None:
        """Aktualisiert Statistik-Anzeige."""
        self.stats_trades.setText(str(stats.trades_total))

        # Win Rate
        wr = stats.win_rate
        self.stats_winrate.setText(f"{wr:.1f}%")
        if wr >= 50:
            self.stats_winrate.setStyleSheet("font-size: 18px; font-weight: bold; color: #4CAF50;")
        else:
            self.stats_winrate.setStyleSheet("font-size: 18px; font-weight: bold; color: #f44336;")

        # PnL
        pnl = stats.total_pnl
        if pnl >= 0:
            self.stats_pnl.setText(f"+${pnl:,.2f}")
            self.stats_pnl.setStyleSheet("font-size: 18px; font-weight: bold; color: #4CAF50;")
        else:
            self.stats_pnl.setText(f"-${abs(pnl):,.2f}")
            self.stats_pnl.setStyleSheet("font-size: 18px; font-weight: bold; color: #f44336;")

        # Drawdown
        dd = stats.max_drawdown
        self.stats_drawdown.setText(f"-${abs(dd):,.2f}")

    def _periodic_update(self) -> None:
        """Periodisches UI Update (Punkt 4: Performance-Tuning).

        Läuft die Engine-Pipeline NUR wenn ein neuer Bar verfügbar ist.
        Bei gleichen Bars: nur lightweight SL/TP Bar Update.
        """
        if self._context_builder:
            # Get current symbol from bot config
            config = self._get_current_config()

            # Performance: Prüfe ob neuer Bar existiert
            asyncio.create_task(
                self._check_and_run_pipeline(
                    symbol=config.symbol,
                    timeframe=self._pipeline_timeframe,
                )
            )

        # Phase 5: Status Panel auch aktualisieren wenn sichtbar
        if self._status_panel and self._status_panel.isVisible():
            self._update_status_panel()
    def set_chart_data(
        self,
        data: "pd.DataFrame",
        symbol: str,
        timeframe: str,
    ) -> None:
        """
        Übergibt Chart-Daten an den Bot Engine.

        NOTE: Die neue Engine-Pipeline holt Daten über den HistoryManager.
        Diese Methode bleibt für Kompatibilität, triggert aber ggf. ein
        Pipeline-Update wenn Engines initialisiert sind.

        Args:
            data: DataFrame mit OHLCV-Daten
            symbol: Symbol (z.B. 'BTCUSDT')
            timeframe: Timeframe (z.B. '5m', '1H')
        """
        # Neue Pipeline: Daten werden über _process_market_data_through_engines() verarbeitet
        # Diese Methode bleibt für Chart-Signale, triggert optionales Update
        if self._context_builder and data is not None and not data.empty:
            logger.debug(f"BotTab: Chart data received ({symbol} {timeframe}), pipeline uses HistoryManager")

    def clear_chart_data(self) -> None:
        """Löscht Chart-Daten im Engine (z.B. bei Symbol-Wechsel)."""
        # Neue Pipeline: Cached Context invalidieren
        self._last_market_context = None
        self._last_entry_score = None
        self._last_llm_result = None
        self._last_trigger_result = None
        self._last_leverage_result = None
        logger.debug("BotTab: Chart data cleared, cache invalidated")

    def on_tick_price_updated(self, price: float) -> None:
        """
        Empfängt Live-Tick-Preise vom Chart-Streaming.

        Aktualisiert die Position und refresht die UI (neue Pipeline).

        Args:
            price: Aktueller Marktpreis vom Streaming
        """
        # Neue Pipeline: Position direkt in self._current_position
        if not self._current_position:
            return

        # SL/TP Bar aktualisieren
        self._update_sltp_bar(price)

        # Position P&L aktualisieren
        entry = self._position_entry_price
        side = self._position_side
        qty = self._position_quantity

        if entry > 0 and qty > 0:
            if side == "long":
                pnl = (price - entry) * qty
                pnl_pct = ((price - entry) / entry) * 100
            else:  # short
                pnl = (entry - price) * qty
                pnl_pct = ((entry - price) / entry) * 100

            # P&L Label aktualisieren
            color = "#4CAF50" if pnl >= 0 else "#f44336"
            sign = "+" if pnl >= 0 else ""
            self.sltp_pnl_label.setText(f"P&L: {sign}${pnl:.2f} ({sign}{pnl_pct:.2f}%)")
            self.sltp_pnl_label.setStyleSheet(f"color: {color}; font-size: 11px; margin-top: 5px;")

    def cleanup(self) -> None:
        """Cleanup bei Widget-Zerstörung (App schließt)."""
        self.update_timer.stop()
        # Neue Pipeline: Position direkt speichern
        if self._current_position:
            self._save_position_to_file()
            logger.info("BotTab cleanup: Position saved for next start")
        # Bot-State zurücksetzen
        self._bot_running = False
        logger.debug("BotTab cleanup completed")

    def _save_position_to_file(self) -> bool:
        """Speichert aktive Position in Datei (für Wiederherstellung beim Neustart)."""
        import json
        from pathlib import Path

        position_file = Path("config/trading_bot/active_position.json")
        try:
            position_file.parent.mkdir(parents=True, exist_ok=True)

            if self._current_position:
                # entry_time zu ISO-String konvertieren
                pos_data = self._current_position.copy()
                if "entry_time" in pos_data and hasattr(pos_data["entry_time"], "isoformat"):
                    pos_data["entry_time"] = pos_data["entry_time"].isoformat()

                data = {
                    "position": pos_data,
                    "saved_at": datetime.now(timezone.utc).isoformat(),
                }
                position_file.write_text(json.dumps(data, indent=2))
                logger.info(f"Position saved: {pos_data.get('symbol')} {pos_data.get('side')}")
                return True
            else:
                # Keine Position - Datei löschen falls vorhanden
                if position_file.exists():
                    position_file.unlink()
                    logger.debug("No position to save, removed old file")
                return True

        except Exception as e:
            logger.error(f"Failed to save position: {e}")
            return False

    def _restore_saved_position(self) -> None:
        """Issue #20: Stellt gespeicherte Position beim Start wieder her."""
        import json
        from pathlib import Path
        from datetime import datetime

        position_file = Path("config/trading_bot/active_position.json")

        try:
            if not position_file.exists():
                logger.debug("BotTab: No saved position file found")
                return

            data = json.loads(position_file.read_text())
            position_data = data.get("position")

            if not position_data:
                logger.debug("BotTab: Saved position file is empty")
                return

            # Position wiederherstellen
            self._current_position = position_data

            # entry_time von ISO-String zurück konvertieren
            if "entry_time" in self._current_position:
                entry_time_str = self._current_position["entry_time"]
                if isinstance(entry_time_str, str):
                    self._current_position["entry_time"] = datetime.fromisoformat(entry_time_str)

            # UI-Variablen setzen
            self._position_entry_price = position_data.get("entry_price", 0)
            self._position_side = position_data.get("side", "long")
            self._position_quantity = position_data.get("quantity", 0)
            self._position_stop_loss = position_data.get("stop_loss")
            self._position_take_profit = position_data.get("take_profit")

            self._log("📂 Gespeicherte Position wiederhergestellt")
            logger.info(
                f"BotTab: Restored saved position: {position_data.get('symbol')} "
                f"{position_data.get('side')} @ {position_data.get('entry_price')}"
            )

            # UI aktualisieren
            self._update_display()

            # SL/TP Bar anzeigen
            if self._position_entry_price:
                self.sltp_container.setVisible(True)
                self._update_sltp_bar(self._position_entry_price)

            # Position-Datei nach erfolgreichem Laden löschen (wird beim nächsten Save neu erstellt)
            position_file.unlink()
            logger.debug("BotTab: Removed position file after successful restore")

        except Exception as e:
            logger.warning(f"BotTab: Failed to restore saved position: {e}")
            self._log(f"⚠️ Position konnte nicht wiederhergestellt werden: {e}")