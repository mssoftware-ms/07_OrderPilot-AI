"""
BotTabLogsMixin - Logging and journal methods

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


class BotTabLogsMixin:
    """Logging and journal methods"""

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

    def _save_settings(self, config: BotConfig) -> None:
        """Speichert Bot-Einstellungen in JSON-Datei."""
        try:
            # Stelle sicher dass Verzeichnis existiert
            BOT_SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)

            # Config zu Dictionary konvertieren
            settings = config.to_dict()

            with open(BOT_SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)

            logger.info(f"Bot-Einstellungen gespeichert: {BOT_SETTINGS_FILE}")
        except Exception as e:
            logger.error(f"Fehler beim Speichern der Einstellungen: {e}")

    def _load_settings(self) -> BotConfig:
        """Lädt Bot-Einstellungen aus JSON-Datei."""
        try:
            if BOT_SETTINGS_FILE.exists():
                with open(BOT_SETTINGS_FILE, 'r', encoding='utf-8') as f:
                    settings = json.load(f)

                logger.info(f"Bot-Einstellungen geladen: {BOT_SETTINGS_FILE}")
                return BotConfig.from_dict(settings)
        except Exception as e:
            logger.warning(f"Fehler beim Laden der Einstellungen: {e}")

        # Fallback: Default-Konfiguration
        return BotConfig(symbol="BTCUSDT")

    # === Callbacks (Thread-sicher via Signals) ===

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
    def _log(self, message: str) -> None:
        """Fügt Log-Nachricht hinzu."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self._append_log(f"[{timestamp}] {message}")

    def _append_log(self, message: str) -> None:
        """Fügt Text zum Log hinzu (Thread-sicher)."""
        self.log_text.append(message)
        # Auto-scroll
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.log_text.setTextCursor(cursor)

    # === Public API ===

    def set_history_manager(self, manager: "HistoryManager") -> None:
        """Setzt den History Manager und verbindet ihn mit dem Adapter.

        Die Engine-Pipeline erhält Marktdaten über den Adapter, der diese
        vom HistoryManager bezieht. Wird für MarketContextBuilder benötigt.
        """
        self._history_manager = manager

        # Connect to adapter for market data access
        if manager and hasattr(self._adapter, 'set_history_manager'):
            self._adapter.set_history_manager(manager)
            logger.info("BotTab.set_history_manager: Connected HistoryManager to PaperAdapter")
            self._log("✅ HistoryManager verbunden - Marktdaten verfügbar")