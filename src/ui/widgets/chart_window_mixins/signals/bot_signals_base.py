"""Bot Signals Base Mixin - Shared infrastructure for signal handling.

This module provides the base infrastructure used by all signal mixins:
- Price update coordination
- Bot status management
- Log management (bot log + KI messages)
- Export functionality
- Settings integration
- Utilities (column visibility, dialogs)
"""

from __future__ import annotations

import logging
from datetime import datetime

from PyQt6.QtWidgets import QMessageBox, QFileDialog

logger = logging.getLogger(__name__)


class BotSignalsBaseMixin:
    """Base mixin providing shared infrastructure for signal handling.

    This mixin is inherited by all other signal mixins and provides:
    - Price update methods (_update_current_price_in_position)
    - Bot status updates (_set_bot_run_status_label, _update_signals_tab_bot_button)
    - Log management (bot log + KI messages)
    - Export functionality (_on_export_signals_clicked)
    - Settings integration (_open_main_settings_dialog)
    - Utility methods (column visibility)
    """

    # ==========================================
    # Price Update Methods
    # ==========================================

    def _update_current_price_in_position(self, price: float):
        """Update current price in Current Position widget.

        Args:
            price: Current market price

        Issue #2: Fixed label name from 'current_price_value_label' to 'position_current_label'.
        """
        if hasattr(self, 'position_current_label'):
            try:
                self.position_current_label.setText(f"{price:.2f}")
            except Exception as e:
                logger.debug(f"Failed to update current price in position widget: {e}")

    # ==========================================
    # Bot Status Management
    # ==========================================

    def _set_bot_run_status_label(self, running: bool) -> None:
        """Update bot run status label.

        Args:
            running: True if bot is running (green), False if stopped (gray)
        """
        if not hasattr(self, 'bot_run_status_label'):
            return
        color = "#26a69a" if running else "#9e9e9e"
        state = "RUNNING" if running else "STOPPED"
        self.bot_run_status_label.setText(f"Status: {state}")
        self.bot_run_status_label.setStyleSheet(f"font-weight: bold; color: {color};")

    def _update_signals_tab_bot_button(self, running: bool) -> None:
        """Update the Start Bot button appearance in Trading tab.

        Args:
            running: True if bot is running (green), False if stopped (red)
        """
        if not hasattr(self, 'signals_tab_start_bot_btn'):
            return

        if running:
            self.signals_tab_start_bot_btn.setText("⏹ Stop Bot")
            self.signals_tab_start_bot_btn.setStyleSheet(
                "font-size: 10px; padding: 2px 12px; background-color: #26a69a; color: white; font-weight: bold;"
            )
        else:
            self.signals_tab_start_bot_btn.setText("▶ Start Bot")
            self.signals_tab_start_bot_btn.setStyleSheet(
                "font-size: 10px; padding: 2px 12px; background-color: #ef5350; color: white; font-weight: bold;"
            )

    def _on_signals_tab_bot_toggle_clicked(self) -> None:
        """Handle Start Bot button click in Trading (Signals) tab.

        Toggles bot on/off and updates button appearance.
        Same functionality as Start/Stop buttons in Bot tab.
        """
        # Check if bot is running by looking at bot_controller
        is_running = (
            hasattr(self, '_bot_controller')
            and self._bot_controller is not None
            and getattr(self._bot_controller, '_running', False)
        )

        if is_running:
            # Stop the bot
            logger.info("Signals Tab: Stopping bot")
            self._on_bot_stop_clicked()
        else:
            # Start the bot
            logger.info("Signals Tab: Starting bot")
            self._on_bot_start_clicked()

    # ==========================================
    # Trading Bot Log Management (Issue #23)
    # ==========================================

    def _append_bot_log(self, log_type: str, message: str, timestamp: str | None = None) -> None:
        """Append a log line to the Trading Bot Log UI.

        Args:
            log_type: Log level (info, warning, error, etc.)
            message: Log message content
            timestamp: Optional timestamp (defaults to now)
        """
        if not hasattr(self, 'bot_log_text') or self.bot_log_text is None:
            return
        ts = timestamp or datetime.now().strftime("%H:%M:%S")
        entry = f"[{ts}] [{log_type.upper()}] {message}"
        self.bot_log_text.appendPlainText(entry)
        # Mirror into KI raw log as well so nothing is lost
        self._append_ki_message(entry, ts)

    def _clear_bot_log(self) -> None:
        """Clear all bot log entries."""
        if hasattr(self, 'bot_log_text'):
            self.bot_log_text.clear()

    def _save_bot_log(self) -> None:
        """Save bot log to file (TXT or MD)."""
        if not hasattr(self, 'bot_log_text'):
            return
        content = self.bot_log_text.toPlainText()
        if not content.strip():
            QMessageBox.information(self, "Keine Logs", "Es sind keine Log-Einträge vorhanden.")
            return
        default_name = f"trading_bot_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Log speichern",
            default_name,
            "Text Files (*.txt);;Markdown (*.md);;All Files (*)",
        )
        if not file_path:
            return
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            QMessageBox.information(self, "Gespeichert", f"Log gespeichert: {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Log konnte nicht gespeichert werden: {e}")

    # ==========================================
    # KI Messages Management (Issue #2)
    # ==========================================

    def _append_ki_message(self, message: str, timestamp: str | None = None) -> None:
        """Append a message to the KI messages log.

        Args:
            message: Message content
            timestamp: Optional timestamp (defaults to now)
        """
        if not hasattr(self, "ki_messages_text") or self.ki_messages_text is None:
            return
        ts = timestamp or datetime.now().strftime("%H:%M:%S")
        entry = f"[{ts}] {message}"
        self.ki_messages_text.appendPlainText(entry)

    def _clear_ki_messages(self) -> None:
        """Clear all KI messages."""
        if hasattr(self, "ki_messages_text"):
            self.ki_messages_text.clear()

    def _save_ki_messages(self) -> None:
        """Save KI messages to file (TXT or MD)."""
        if not hasattr(self, "ki_messages_text"):
            return
        content = self.ki_messages_text.toPlainText()
        if not content.strip():
            QMessageBox.information(self, "Keine Nachrichten", "Es sind keine KI-Nachrichten vorhanden.")
            return
        default_name = f"ki_messages_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "KI-Nachrichten speichern",
            default_name,
            "Text Files (*.txt);;Markdown (*.md);;All Files (*)",
        )
        if not file_path:
            return
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            QMessageBox.information(self, "Gespeichert", f"KI-Nachrichten gespeichert: {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"KI-Nachrichten konnten nicht gespeichert werden: {e}")

    def _open_prompt_management(self) -> None:
        """Open prompt management dialog for KI configuration."""
        try:
            from src.ui.dialogs.prompt_management_dialog import PromptManagementDialog
            dialog = PromptManagementDialog(self)
            dialog.exec()
        except Exception:
            QMessageBox.information(
                self,
                "Prompt Management",
                "Prompt-Management-Dialog ist in dieser Version noch nicht verfügbar.",
            )

    # ==========================================
    # Export Functionality
    # ==========================================

    def _on_export_signals_clicked(self) -> None:
        """Export current signals table / history to XLSX or CSV.

        Exports the _signal_history list to Excel or CSV format using pandas.
        """
        try:
            import pandas as pd  # type: ignore
        except Exception as e:
            QMessageBox.critical(self, "Export fehlgeschlagen", f"pandas nicht verfügbar: {e}")
            return

        if not hasattr(self, "_signal_history") or not self._signal_history:
            QMessageBox.information(self, "Keine Daten", "Keine Einträge zum Export vorhanden.")
            return

        default_name = f"trading_signals_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Trading-Tabelle exportieren",
            default_name,
            "Excel Files (*.xlsx);;CSV (*.csv);;All Files (*)",
        )
        if not file_path:
            return

        try:
            df = pd.DataFrame(self._signal_history)
            if file_path.lower().endswith(".csv"):
                df.to_csv(file_path, index=False)
            else:
                # Excel export requires openpyxl/xlsxwriter; pandas will raise if missing
                df.to_excel(file_path, index=False)
            QMessageBox.information(self, "Exportiert", f"Datei gespeichert:\n{file_path}")
        except Exception as e:
            logger.error(f"Export failed: {e}", exc_info=True)
            QMessageBox.critical(self, "Export fehlgeschlagen", str(e))

    # ==========================================
    # Utility Methods
    # ==========================================

    def _update_leverage_column_visibility(self) -> None:
        """Update leverage column visibility.

        Issue #3: Hebel column (20) is now always visible.
        Previously this would hide the column if no signals had leverage > 1.
        Now the column stays visible per Issue #3 requirements.
        """
        if not hasattr(self, 'signals_table'):
            return

        # Issue #3: Hebel column is always visible now
        self.signals_table.setColumnHidden(20, False)

    def _open_main_settings_dialog(self) -> None:
        """Open the main Settings dialog.

        Tries to find the settings dialog method in parent widgets:
        1. Check chart_widget.open_main_settings_dialog()
        2. Walk up parent tree looking for show_settings_dialog()
        """
        if hasattr(self, 'chart_widget') and hasattr(self.chart_widget, 'open_main_settings_dialog'):
            self.chart_widget.open_main_settings_dialog()
            return
        widget = self
        while widget is not None:
            if hasattr(widget, "show_settings_dialog"):
                widget.show_settings_dialog()
                return
            widget = widget.parent()
        logger.warning("Settings dialog not available from Trading tab")
