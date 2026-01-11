"""Trading Journal Widget - Refactored Main Orchestrator.

Refactored from 663 LOC monolith using composition pattern.

Module 5/5 of trading_journal_widget.py split.

Contains:
- TradingJournalWidget: Main orchestrator with tabs and export functionality
"""

from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QPushButton,
    QFileDialog,
    QMessageBox,
)

from .trading_journal_signals_tab import SignalsTab
from .trading_journal_trades_tab import TradesTab
from .trading_journal_llm_tab import LLMOutputsTab
from .trading_journal_errors_tab import ErrorsTab


class TradingJournalWidget(QWidget):
    """Main Widget für Trading-Journal mit Tabs für Signals, Trades, LLM-Outputs, Errors."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Erstellt die UI mit Tabs."""
        layout = QVBoxLayout(self)

        # Tab-Widget
        self._tabs = QTabWidget()

        # Tabs erstellen (Composition Pattern)
        self._signals_tab = SignalsTab()
        self._trades_tab = TradesTab()
        self._llm_tab = LLMOutputsTab()
        self._errors_tab = ErrorsTab()

        self._tabs.addTab(self._signals_tab, "Signale")
        self._tabs.addTab(self._trades_tab, "Trades")
        self._tabs.addTab(self._llm_tab, "LLM Validierung")
        self._tabs.addTab(self._errors_tab, "Fehler")

        layout.addWidget(self._tabs)

        # Export-Buttons
        export_layout = QHBoxLayout()
        btn_export_json = QPushButton("Export (JSON)")
        btn_export_json.clicked.connect(lambda: self._export("json"))
        export_layout.addWidget(btn_export_json)

        btn_export_csv = QPushButton("Export (CSV)")
        btn_export_csv.clicked.connect(lambda: self._export("csv"))
        export_layout.addWidget(btn_export_csv)

        export_layout.addStretch()
        layout.addLayout(export_layout)

    def add_signal(self, signal_data: dict) -> None:
        """Fügt ein Signal zur Historie hinzu."""
        self._signals_tab.add_signal(signal_data)

    def add_llm_output(self, output_data: dict) -> None:
        """Fügt eine LLM-Ausgabe hinzu."""
        self._llm_tab.add_output(output_data)

    def add_error(self, error_data: dict) -> None:
        """Fügt einen Fehler hinzu."""
        self._errors_tab.add_error(error_data)

    # ==================== Bot Log Delegation Methods ====================

    def append_bot_log(self, log_type: str, message: str) -> None:
        """Fügt einen Bot-Log-Eintrag hinzu.

        Args:
            log_type: Log-Typ (z.B. "INFO", "SIGNAL", "TRADE", "ERROR")
            message: Log-Nachricht
        """
        self._signals_tab.append_log(log_type, message)

    def set_bot_running(self, is_running: bool) -> None:
        """Setzt den Bot-Running-Status.

        Args:
            is_running: True wenn Bot läuft
        """
        self._signals_tab.set_bot_running(is_running)

    def set_bot_current_task(self, task: str) -> None:
        """Setzt die aktuelle Bot-Aufgabe.

        Args:
            task: Beschreibung der aktuellen Aufgabe
        """
        self._signals_tab.set_current_task(task)

    def clear_bot_log(self) -> None:
        """Löscht alle Bot-Log-Einträge."""
        self._signals_tab.clear_log()

    def get_bot_log_entries(self) -> list[str]:
        """Gibt alle Bot-Log-Einträge zurück."""
        return self._signals_tab.get_log_entries()

    def is_bot_running(self) -> bool:
        """Gibt zurück ob der Bot läuft."""
        return self._signals_tab.is_bot_running()

    def _export(self, format_type: str) -> None:
        """Exportiert Journal-Daten als JSON oder CSV.

        Args:
            format_type: "json" oder "csv"
        """
        # Sammle Daten
        data = {
            "exported_at": datetime.now().isoformat(),
            "signals": self._signals_tab.get_signals(),
            "llm_outputs": self._llm_tab.get_outputs(),
            "errors": self._errors_tab.get_errors(),
        }

        # Datei-Dialog
        if format_type == "json":
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Export Journal (JSON)",
                f"trading_journal_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                "JSON Files (*.json)"
            )
        else:  # csv
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Export Journal (CSV)",
                f"trading_journal_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "CSV Files (*.csv)"
            )

        if not file_path:
            return

        try:
            if format_type == "json":
                self._export_json(file_path, data)
            else:
                self._export_csv(file_path, data)

            QMessageBox.information(
                self,
                "Export erfolgreich",
                f"Journal wurde exportiert nach:\n{file_path}"
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Export fehlgeschlagen",
                f"Fehler beim Exportieren:\n{e}"
            )

    def _export_json(self, file_path: str, data: dict) -> None:
        """Exportiert Daten als JSON."""
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _export_csv(self, file_path: str, data: dict) -> None:
        """Exportiert Daten als CSV (Signale + Errors kombiniert)."""
        with open(file_path, "w", encoding="utf-8", newline="") as f:
            # Schreibe Signale
            if data["signals"]:
                writer = csv.DictWriter(f, fieldnames=data["signals"][0].keys())
                writer.writeheader()
                writer.writerows(data["signals"])
                f.write("\n")

            # Schreibe LLM Outputs
            if data["llm_outputs"]:
                f.write("# LLM Validierungen\n")
                writer = csv.DictWriter(f, fieldnames=data["llm_outputs"][0].keys())
                writer.writeheader()
                writer.writerows(data["llm_outputs"])
                f.write("\n")

            # Schreibe Fehler
            if data["errors"]:
                f.write("# Fehler\n")
                writer = csv.DictWriter(f, fieldnames=data["errors"][0].keys())
                writer.writeheader()
                writer.writerows(data["errors"])


__all__ = ["TradingJournalWidget"]
