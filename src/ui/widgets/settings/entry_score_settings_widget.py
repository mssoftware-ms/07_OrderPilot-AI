"""
Entry Score Settings Widget - Konfiguration für EntryScoreEngine.

REFACTORED: Split into focused helper modules using composition pattern.

Erlaubt die Anpassung von:
- Komponenten-Gewichten (Trend, RSI, MACD, ADX, Volatility, Volume)
- Quality Thresholds (EXCELLENT, GOOD, MODERATE, WEAK)
- Gate-Einstellungen (Regime-Gates)
- Minimum Entry Score

Phase 5.1 der Bot-Integration.
"""

from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
)

from .entry_score_ui_weights import EntryScoreUIWeights
from .entry_score_ui_thresholds import EntryScoreUIThresholds
from .entry_score_ui_gates import EntryScoreUIGates
from .entry_score_ui_entry import EntryScoreUIEntry
from .entry_score_signals import EntryScoreSignals
from .entry_score_validation import EntryScoreValidation
from .entry_score_persistence import EntryScorePersistence


class EntryScoreSettingsWidget(QWidget):
    """
    Widget für EntryScoreEngine-Einstellungen.

    Ermöglicht die Konfiguration aller EntryScoreEngine-Parameter:
    - Komponenten-Gewichte (müssen sich zu 1.0 summieren)
    - Quality Thresholds
    - Gate-Einstellungen

    Signals:
        settings_changed: Emitted when settings are changed
        settings_saved: Emitted when settings are saved

    Usage:
        widget = EntryScoreSettingsWidget()
        widget.settings_changed.connect(on_settings_changed)
        layout.addWidget(widget)
    """

    settings_changed = pyqtSignal(dict)
    settings_saved = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)

        # Create helpers (composition pattern)
        self._ui_weights = EntryScoreUIWeights(self)
        self._ui_thresholds = EntryScoreUIThresholds(self)
        self._ui_gates = EntryScoreUIGates(self)
        self._ui_entry = EntryScoreUIEntry(self)
        self._signals = EntryScoreSignals(self)
        self._validation = EntryScoreValidation(self)
        self._persistence = EntryScorePersistence(self)

        self._setup_ui()
        self._persistence.load_settings()
        self._signals.connect_signals()

    def _setup_ui(self) -> None:
        """Setup the UI components."""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(16)

        # Title
        title = QLabel("<h3>Entry Score Einstellungen</h3>")
        main_layout.addWidget(title)

        # Description
        desc = QLabel(
            "Konfiguriere die Berechnung des Entry-Scores (0.0-1.0).\n"
            "Der Score bestimmt die Qualität eines Einstiegssignals."
        )
        desc.setStyleSheet("color: #888;")
        desc.setWordWrap(True)
        main_layout.addWidget(desc)

        # Component Weights Group
        weights_group = self._ui_weights.create_weights_group()
        main_layout.addWidget(weights_group)

        # Quality Thresholds Group
        thresholds_group = self._ui_thresholds.create_thresholds_group()
        main_layout.addWidget(thresholds_group)

        # Gate Settings Group
        gates_group = self._ui_gates.create_gates_group()
        main_layout.addWidget(gates_group)

        # Entry Requirements Group
        entry_group = self._ui_entry.create_entry_group()
        main_layout.addWidget(entry_group)

        # Spacer
        main_layout.addStretch()

        # Action Buttons
        button_layout = QHBoxLayout()

        self._reset_btn = QPushButton("Zurücksetzen")
        self._reset_btn.clicked.connect(self._persistence.reset_to_defaults)
        button_layout.addWidget(self._reset_btn)

        button_layout.addStretch()

        self._apply_btn = QPushButton("Übernehmen")
        self._apply_btn.setStyleSheet(
            "background-color: #4CAF50; color: white; font-weight: bold; padding: 8px 16px;"
        )
        self._apply_btn.clicked.connect(self._persistence.apply_settings)
        button_layout.addWidget(self._apply_btn)

        self._save_btn = QPushButton("Speichern")
        self._save_btn.setStyleSheet(
            "background-color: #2196F3; color: white; font-weight: bold; padding: 8px 16px;"
        )
        self._save_btn.clicked.connect(self._persistence.save_settings)
        button_layout.addWidget(self._save_btn)

        main_layout.addLayout(button_layout)

    def get_settings(self) -> dict:
        """Get current settings as dict."""
        return self._persistence.get_settings()

    def set_settings(self, settings: dict) -> None:
        """Set settings from dict."""
        return self._persistence.set_settings(settings)
