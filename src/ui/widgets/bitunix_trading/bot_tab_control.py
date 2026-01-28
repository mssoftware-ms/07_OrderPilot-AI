"""Bot Tab Control - Main Orchestrator for Bot Trading Control.

Refactored from 1,160 LOC monolith using composition pattern.

Module 6/6 (Main Orchestrator).

Thin orchestration layer that ties all modules together:
- BotTabControlEngineInit: Engine initialization and config management
- BotTabControlPipeline: Main pipeline execution
- BotTabControlTrade: Trade execution and position monitoring
- BotTabControlUI: UI updates and visual elements
- BotTabControlPersistence: Settings and position persistence
- BotTabControl (this): Thin Orchestrator

Public API:
- on_start_clicked(): Start bot
- on_stop_clicked(): Stop bot
- on_close_position_clicked(): Manual close
- toggle_status_panel(), toggle_journal(): UI toggles
- periodic_update(): Main update loop
- cleanup(): Cleanup on close
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import TYPE_CHECKING

import qasync
from pathlib import Path
from PyQt6.QtCore import pyqtSlot
from PyQt6.QtGui import QTextCursor
from PyQt6.QtWidgets import QMessageBox, QFileDialog

if TYPE_CHECKING:
    from PyQt6.QtWidgets import QWidget

# Import helper modules
from .bot_tab_control_engine_init import BotTabControlEngineInit
from .bot_tab_control_pipeline import BotTabControlPipeline
from .bot_tab_control_trade import BotTabControlTrade
from .bot_tab_control_ui import BotTabControlUI
from .bot_tab_control_persistence import BotTabControlPersistence

# JSON Entry System (NEU)
from src.core.tradingbot.json_entry_loader import JsonEntryConfig
from src.core.tradingbot.json_entry_scorer import JsonEntryScorer

logger = logging.getLogger(__name__)


class BotTabControl:
    """Verwaltet Bot Control und Engine-Pipeline.

    Architektur (Composition Pattern):
    - BotTabControlEngineInit: Engine initialization
    - BotTabControlPipeline: Pipeline execution
    - BotTabControlTrade: Trade execution/monitoring
    - BotTabControlUI: UI updates
    - BotTabControlPersistence: Settings/position persistence
    - BotTabControl (this): Thin Orchestrator
    """

    def __init__(self, parent_widget: "QWidget"):
        """Initialisiert BotTabControl.

        Args:
            parent_widget: Das BotTab Widget
        """
        self.parent = parent_widget

        # Helper modules (composition pattern)
        self._engine_init_helper = BotTabControlEngineInit(parent=self)
        self._pipeline_helper = BotTabControlPipeline(parent=self)
        self._trade_helper = BotTabControlTrade(parent=self)
        self._ui_helper = BotTabControlUI(parent=self)
        self._persistence_helper = BotTabControlPersistence(parent=self)

        # JSON Entry System (NEU)
        self._json_entry_config: JsonEntryConfig | None = None
        self._json_entry_scorer: JsonEntryScorer | None = None

    # === Bot Control ===

    @qasync.asyncSlot()
    async def on_start_clicked(self) -> None:
        """Startet den Bot (neue Engine-Pipeline)."""
        try:
            self._log("🚀 Starte Trading Bot (neue Engine-Pipeline)...")
            logger.info("Bot start clicked - initializing pipeline...")

            # KRITISCH: Prüfe ob HistoryManager verfügbar ist
            if not self.parent._history_manager:
                error_msg = (
                    "❌ HistoryManager nicht verfügbar!\n\n"
                    "Die Pipeline benötigt einen HistoryManager für Marktdaten.\n"
                    "Bitte öffne zuerst einen Chart mit einem Symbol."
                )
                self._log(error_msg)
                logger.error("Bot start failed: HistoryManager is None")
                QMessageBox.warning(
                    self.parent,
                    "HistoryManager fehlt",
                    error_msg,
                )
                return

            # Neue Engines initialisieren (Phase 1-4)
            if not self.parent._context_builder:
                self._log("🔧 Initialisiere Trading Engines...")
                self._engine_init_helper._initialize_new_engines()
                self._log("✅ Engines initialisiert")

            # UI aktualisieren
            self.parent.start_btn.setEnabled(False)
            self.parent.stop_btn.setEnabled(True)
            self.parent.update_timer.start()

            self._log("✅ Bot gestartet! Pipeline läuft jede Sekunde.")
            logger.info("Bot started successfully - pipeline running every second")

        except Exception as e:
            self._log(f"❌ Fehler beim Starten: {e}")
            logger.exception("Bot start failed")
            QMessageBox.critical(self.parent, "Fehler", f"Bot konnte nicht gestartet werden:\n{e}")

    @qasync.asyncSlot()
    async def on_start_json_clicked(self) -> None:
        """Startet Bot mit JSON-basierter Entry-Logik (NEUE METHODE).

        Flow:
        1. File Picker für Regime JSON
        2. Optional: File Picker für Indicator JSON
        3. Lade JsonEntryConfig (kombiniert beide JSON)
        4. Validiere Config und zeige Warnings
        5. Initialisiere Standard-Engines (wie bei normalem Start)
        6. Erstelle JsonEntryScorer (ersetzt EntryScoreEngine)
        7. UI aktualisieren
        8. Start update timer

        Wichtig: SL/TP/Trailing Stop werden aus UI-Feldern verwendet!
        """
        try:
            self._log("🚀 Starte Trading Bot (JSON Entry)...")
            logger.info("JSON Entry bot start clicked")

            # KRITISCH: Prüfe ob HistoryManager verfügbar ist
            if not self.parent._history_manager:
                error_msg = (
                    "❌ HistoryManager nicht verfügbar!\n\n"
                    "Die Pipeline benötigt einen HistoryManager für Marktdaten.\n"
                    "Bitte öffne zuerst einen Chart mit einem Symbol."
                )
                self._log(error_msg)
                logger.error("JSON Entry bot start failed: HistoryManager is None")
                QMessageBox.warning(
                    self.parent,
                    "HistoryManager fehlt",
                    error_msg,
                )
                return

            # 1. File Picker für Regime JSON
            regime_json, _ = QFileDialog.getOpenFileName(
                self.parent,
                "Regime JSON auswählen",
                "03_JSON/Entry_Analyzer/Regime/",
                "JSON Files (*.json)",
            )
            if not regime_json:
                self._log("❌ Abgebrochen - keine Regime JSON ausgewählt")
                return

            # 2. File Picker für Indicator JSON (optional)
            indicator_json = None
            reply = QMessageBox.question(
                self.parent,
                "Indicator JSON",
                "Möchten Sie auch eine separate Indicator JSON laden?\n\n"
                "Wenn Ja: Indicator JSON hat Vorrang bei Indicator-Definitionen\n"
                "Wenn Nein: Nur Indicators aus Regime JSON werden verwendet",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                indicator_json, _ = QFileDialog.getOpenFileName(
                    self.parent,
                    "Indicator JSON auswählen",
                    "03_JSON/Entry_Analyzer/Indicators/",
                    "JSON Files (*.json)",
                )

            # 3. Lade JSON Entry Config
            self._log("📂 Lade JSON-Dateien...")
            self._json_entry_config = JsonEntryConfig.from_files(
                regime_json_path=regime_json,
                indicator_json_path=indicator_json if indicator_json else None,
            )
            self._log(f"✅ Regime JSON: {Path(regime_json).name}")
            if indicator_json:
                self._log(f"✅ Indicator JSON: {Path(indicator_json).name}")

            # Zeige Entry Expression (gekürzt)
            expr_preview = self._json_entry_config.entry_expression
            if len(expr_preview) > 80:
                expr_preview = expr_preview[:77] + "..."
            self._log(f"📝 Entry Expression: {expr_preview}")

            # 4. Validiere Config
            warnings = self._json_entry_config.validate()
            if warnings:
                self._log("⚠️ Validierungs-Warnungen:")
                for warning in warnings:
                    self._log(f"   - {warning}")

            # 5. Initialisiere Standard-Engines (wie bei normalem Start)
            if not self.parent._context_builder:
                self._log("🔧 Initialisiere Trading Engines...")
                self._engine_init_helper._initialize_new_engines()
                self._log("✅ Engines initialisiert")

            # 6. Erstelle JSON Entry Scorer (ersetzt EntryScoreEngine)
            from src.core.tradingbot.cel_engine import get_cel_engine

            cel_engine = get_cel_engine()
            self._json_entry_scorer = JsonEntryScorer(
                json_config=self._json_entry_config,
                cel_engine=cel_engine,
            )
            self._log("✅ JSON Entry Scorer bereit")
            self._log(f"   Compiled Expression: {self._json_entry_scorer._compiled_expr is not None}")

            # 7. UI aktualisieren
            self.parent.start_btn.setEnabled(False)
            self.parent.start_btn_json.setEnabled(False)
            self.parent.stop_btn.setEnabled(True)

            # 8. Start update timer
            self.parent.update_timer.start()

            self._log("✅ Bot gestartet! JSON Entry Pipeline läuft.")
            self._log(
                f"   SL: {self.parent.initial_sl_spin.value()}% | "
                f"TP: {self.parent.initial_tp_spin.value()}% | "
                f"Trailing: {'Ja' if self.parent.trailing_enabled_check.isChecked() else 'Nein'}"
            )
            logger.info(
                f"JSON Entry Bot started successfully - "
                f"expression_length={len(self._json_entry_config.entry_expression)}"
            )

        except FileNotFoundError as e:
            self._log(f"❌ Datei nicht gefunden: {e}")
            logger.exception("JSON file not found")
            QMessageBox.critical(self.parent, "Datei nicht gefunden", str(e))
        except Exception as e:
            self._log(f"❌ Fehler beim Starten: {e}")
            logger.exception("JSON Entry Bot start failed")
            QMessageBox.critical(self.parent, "Fehler", f"Bot konnte nicht gestartet werden:\n{e}")

    @qasync.asyncSlot()
    async def on_stop_clicked(self) -> None:
        """Stoppt den Bot (neue Engine-Pipeline)."""
        try:
            self._log("⏹ Stoppe Trading Bot...")

            # Timer stoppen (Pipeline stoppt automatisch)
            self.parent.update_timer.stop()

            # Cleanup JSON Entry Scorer (falls aktiv)
            if self._json_entry_scorer:
                self._json_entry_scorer = None
                self._json_entry_config = None
                self._log("   JSON Entry Scorer deaktiviert")
                logger.info("JSON Entry Scorer cleaned up")

            # UI aktualisieren
            self.parent.start_btn.setEnabled(True)
            self.parent.start_btn_json.setEnabled(True)  # NEU: Auch JSON Button wieder aktivieren
            self.parent.stop_btn.setEnabled(False)

            self._log("✅ Bot gestoppt! Pipeline wurde angehalten.")

        except Exception as e:
            self._log(f"❌ Fehler beim Stoppen: {e}")
            logger.exception("Bot stop failed")

    @qasync.asyncSlot()
    async def on_close_position_clicked(self) -> None:
        """Schließt die aktuelle Position manuell (neue Pipeline)."""
        if not self.parent._current_position:
            QMessageBox.warning(self.parent, "Keine Position", "Es ist keine Position geöffnet.")
            return

        confirm = QMessageBox.question(
            self.parent,
            "Position schließen",
            "Position wirklich manuell schließen?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if confirm == QMessageBox.StandardButton.Yes:
            try:
                self._log("🔄 Schließe Position manuell...")
                # Hole aktuellen Preis aus letztem MarketContext
                current_price = (
                    self.parent._last_market_context.current_price
                    if self.parent._last_market_context
                    else self.parent._position_entry_price
                )
                context_id = (
                    self.parent._last_market_context.context_id if self.parent._last_market_context else "manual_close"
                )

                await self._trade_helper._close_position(
                    exit_price=current_price,
                    exit_reason="Manual Close (User)",
                    context_id=context_id,
                )
                self._log("✅ Position geschlossen!")
            except Exception as e:
                self._log(f"❌ Fehler: {e}")
                logger.exception("Manual position close failed")

    # === UI Toggles (delegate to ui_helper) ===

    def toggle_status_panel(self) -> None:
        """Togglet die Sichtbarkeit des Status Panels."""
        self._ui_helper.toggle_status_panel()

    def on_status_panel_refresh(self) -> None:
        """Callback wenn Status Panel Refresh angefordert wird."""
        self._ui_helper.on_status_panel_refresh()

    def toggle_journal(self) -> None:
        """Togglet die Sichtbarkeit des Trading Journals."""
        self._ui_helper.toggle_journal()

    # === Engine Management (delegate to engine_init_helper) ===

    def update_engine_configs(self) -> None:
        """Aktualisiert die Konfiguration aller laufenden Engines."""
        self._engine_init_helper.update_engine_configs()

    # === Settings Management (delegate to persistence_helper) ===

    def _get_current_config(self):
        """Gibt aktuelle Bot-Konfiguration zurück (delegiert zu persistence_helper)."""
        return self._persistence_helper._get_current_config()

    def apply_config(self, config) -> None:
        """Wendet neue Konfiguration an."""
        self._persistence_helper.apply_config(config)

    # === Periodic Updates ===

    def periodic_update(self) -> None:
        """Periodisches UI Update (Performance-Tuning).

        Läuft die Engine-Pipeline NUR wenn ein neuer Bar verfügbar ist.
        """
        if self.parent._context_builder:
            # Get current symbol from bot config
            config = self._persistence_helper._get_current_config()

            # Performance: Prüfe ob neuer Bar existiert
            asyncio.create_task(
                self._pipeline_helper._check_and_run_pipeline(
                    symbol=config.symbol,
                    timeframe=self.parent._pipeline_timeframe,
                )
            )

        # Phase 5: Status Panel auch aktualisieren wenn sichtbar
        if self.parent._status_panel and self.parent._status_panel.isVisible():
            self._ui_helper._update_status_panel()

    # === Cleanup & Position Restore (delegate to persistence_helper) ===

    def cleanup(self) -> None:
        """Cleanup bei Widget-Zerstörung (App schließt)."""
        self._persistence_helper.cleanup()

    def restore_saved_position(self) -> None:
        """Stellt gespeicherte Position beim Start wieder her."""
        self._persistence_helper.restore_saved_position()

    # === Helper Methods ===

    def _log(self, message: str) -> None:
        """Fügt Log-Nachricht hinzu."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self._append_log(f"[{timestamp}] {message}")

    def _append_log(self, message: str) -> None:
        """Fügt Text zum Log hinzu (Thread-sicher)."""
        self.parent.log_text.append(message)
        # Auto-scroll
        cursor = self.parent.log_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.parent.log_text.setTextCursor(cursor)


# Re-export für backward compatibility
__all__ = ["BotTabControl"]
