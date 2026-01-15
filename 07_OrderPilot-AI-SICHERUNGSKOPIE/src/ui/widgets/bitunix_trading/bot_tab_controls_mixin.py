"""
BotTabControlsMixin - Bot control methods (settings, toggle, apply)

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


class BotTabControlsMixin:
    """Bot control methods (settings, toggle, apply)"""

    def _handle_settings_click(self) -> None:
        """Handler für Settings-Button mit Debug-Output."""
        print("=" * 50)
        print("DEBUG: Settings button was clicked!")
        print("=" * 50)
        # Visuelle Bestätigung dass Button geklickt wurde
        self.settings_btn.setText("...")
        self.settings_btn.repaint()  # Force immediate repaint
        try:
            self._on_settings_clicked()
        finally:
            self.settings_btn.setText("⚙")

    @pyqtSlot()
    def _on_settings_clicked(self) -> None:
        """Öffnet Settings Dialog."""
        print("DEBUG: _on_settings_clicked() called")
        logger.info("Settings button clicked!")
        self._log("⚙ Öffne Einstellungen...")
        try:
            print("DEBUG: Getting config...")
            config = self._get_current_config()
            print(f"DEBUG: Config loaded: {config.symbol}")
            logger.info(f"Config loaded: {config.symbol}")

            print("DEBUG: Creating dialog...")
            dialog = BotSettingsDialog(config, self)
            print("DEBUG: Dialog created, calling exec()...")

            result = dialog.exec()
            print(f"DEBUG: Dialog result: {result}")
            logger.info(f"Dialog result: {result}")

            if result == QDialog.DialogCode.Accepted:
                new_config = dialog.get_config()
                self._apply_config(new_config)
                self._log("⚙ Einstellungen aktualisiert")
            else:
                self._log("⚙ Einstellungen abgebrochen")
        except Exception as e:
            print(f"DEBUG ERROR: {e}")
            import traceback
            traceback.print_exc()
            logger.exception("Settings dialog error")
            self._log(f"❌ Settings Fehler: {e}")
            QMessageBox.critical(self, "Fehler", f"Settings konnten nicht geöffnet werden:\n{e}")
    def _toggle_status_panel(self) -> None:
        """Togglet die Sichtbarkeit des Status Panels."""
        if self._status_panel:
            visible = self.status_panel_btn.isChecked()
            self._status_panel.setVisible(visible)
            if visible:
                self._log("📊 Status Panel eingeblendet")
                self._update_status_panel()
            else:
                self._log("📊 Status Panel ausgeblendet")

    def _on_status_panel_refresh(self) -> None:
        """Callback wenn Status Panel Refresh angefordert wird."""
        self._update_status_panel()
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