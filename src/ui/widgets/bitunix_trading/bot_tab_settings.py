"""Bot Tab Settings Dialog - Settings Dialog für Bot Trading Tab.

Refactored from 850 LOC bot_tab_main.py (further split).

Module 1/3 of bot_tab_main.py second-level split.

Contains:
- BotSettingsDialog: Tab-basierter Settings Dialog
  - Basic Settings (Risk, SL/TP, Signal, AI, Performance)
  - Engine Settings Tabs (Entry Score, Trigger/Exit, Leverage, LLM, Levels)
  - Apply/Save All funktionalität
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import TYPE_CHECKING

from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    from src.core.trading_bot import BotConfig

# Phase 5 - Engine Settings Widgets
try:
    from src.ui.widgets.settings import (
        EntryScoreSettingsWidget,
        LevelSettingsWidget,
        LeverageSettingsWidget,
        LLMValidationSettingsWidget,
        TriggerExitSettingsWidget,
    )

    HAS_ENGINE_SETTINGS = True
except ImportError:
    HAS_ENGINE_SETTINGS = False

logger = logging.getLogger(__name__)


class BotSettingsDialog(QDialog):
    """Tab-basierter Dialog für Bot-Einstellungen.

    Tabs:
    - Basic: Grundeinstellungen (Risk, SL/TP, Signal, AI)
    - Entry Score: Gewichte und Quality Thresholds
    - Trigger/Exit: SL/TP-Modi, Trailing
    - Leverage: Tiers, Regime-Anpassung, Safety
    - LLM Validation: Thresholds, Modifiers
    - Levels: Level-Detection Settings
    """

    def __init__(self, config: "BotConfig", parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("⚙ Trading Bot Settings")
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)

        self._config = config
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Erstellt das Tab-basierte Dialog-Layout."""
        layout = QVBoxLayout(self)

        # Tab Widget für verschiedene Settings-Bereiche
        tabs = QTabWidget()

        # Tab 1: Basic Settings (bisherige Inhalte)
        basic_tab = QWidget()
        basic_layout = QVBoxLayout(basic_tab)
        self._create_basic_settings(basic_layout)
        tabs.addTab(basic_tab, "⚙ Basic")

        # Tab 2-6: Engine Settings (nur wenn verfügbar)
        if HAS_ENGINE_SETTINGS:
            self._entry_score_widget = EntryScoreSettingsWidget()
            tabs.addTab(self._entry_score_widget, "📊 Entry Score")

            self._trigger_exit_widget = TriggerExitSettingsWidget()
            tabs.addTab(self._trigger_exit_widget, "🎯 Trigger/Exit")

            self._leverage_widget = LeverageSettingsWidget()
            tabs.addTab(self._leverage_widget, "⚡ Leverage")

            self._llm_widget = LLMValidationSettingsWidget()
            tabs.addTab(self._llm_widget, "🤖 LLM Validation")

            self._levels_widget = LevelSettingsWidget()
            tabs.addTab(self._levels_widget, "📈 Levels")

        layout.addWidget(tabs)

        # Buttons
        button_layout = QHBoxLayout()

        if HAS_ENGINE_SETTINGS:
            apply_all_btn = QPushButton("Alle übernehmen")
            apply_all_btn.clicked.connect(self._apply_all_engine_settings)
            button_layout.addWidget(apply_all_btn)

            save_all_btn = QPushButton("Alle speichern")
            save_all_btn.clicked.connect(self._save_all_engine_settings)
            button_layout.addWidget(save_all_btn)

        button_layout.addStretch()

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        button_layout.addWidget(buttons)

        layout.addLayout(button_layout)

    def _create_basic_settings(self, layout: QVBoxLayout) -> None:
        """Erstellt die Basic Settings (bisheriger Dialog-Inhalt)."""

        # Risk Management - KEINE Begrenzungen, User entscheidet
        risk_group = QGroupBox("Risk Management")
        risk_layout = QFormLayout(risk_group)

        self.risk_spin = QDoubleSpinBox()
        self.risk_spin.setRange(0.1, 100.0)  # Bis 100% möglich
        self.risk_spin.setSingleStep(0.5)
        self.risk_spin.setValue(float(self._config.risk_per_trade_percent))
        self.risk_spin.setSuffix(" %")
        risk_layout.addRow("Risiko pro Trade:", self.risk_spin)

        self.daily_loss_spin = QDoubleSpinBox()
        self.daily_loss_spin.setRange(0.1, 100.0)  # Bis 100% möglich
        self.daily_loss_spin.setSingleStep(1.0)
        self.daily_loss_spin.setValue(float(self._config.max_daily_loss_percent))
        self.daily_loss_spin.setSuffix(" %")
        risk_layout.addRow("Max. Tagesverlust:", self.daily_loss_spin)

        layout.addWidget(risk_group)

        # SL/TP - Erweiterte Ranges
        sltp_group = QGroupBox("SL/TP (ATR Multiplikator)")
        sltp_layout = QFormLayout(sltp_group)

        self.sl_spin = QDoubleSpinBox()
        self.sl_spin.setRange(0.1, 100.0)  # Flexibel
        self.sl_spin.setSingleStep(0.1)
        self.sl_spin.setValue(float(self._config.sl_atr_multiplier))
        self.sl_spin.setSuffix(" x ATR")
        sltp_layout.addRow("Stop Loss:", self.sl_spin)

        self.tp_spin = QDoubleSpinBox()
        self.tp_spin.setRange(0.1, 100.0)  # Flexibel
        self.tp_spin.setSingleStep(0.1)
        self.tp_spin.setValue(float(self._config.tp_atr_multiplier))
        self.tp_spin.setSuffix(" x ATR")
        sltp_layout.addRow("Take Profit:", self.tp_spin)

        self.trailing_check = QCheckBox("Trailing Stop aktivieren")
        self.trailing_check.setChecked(self._config.trailing_stop_enabled)
        sltp_layout.addRow(self.trailing_check)

        self.trailing_spin = QDoubleSpinBox()
        self.trailing_spin.setRange(0.1, 100.0)  # Flexibel
        self.trailing_spin.setSingleStep(0.1)
        self.trailing_spin.setValue(float(self._config.trailing_stop_atr_multiplier))
        self.trailing_spin.setSuffix(" x ATR")
        sltp_layout.addRow("Trailing Abstand:", self.trailing_spin)

        layout.addWidget(sltp_group)

        # Signal - Erweiterte Ranges
        signal_group = QGroupBox("Signal-Einstellungen")
        signal_layout = QFormLayout(signal_group)

        self.confluence_spin = QSpinBox()
        self.confluence_spin.setRange(1, 10)  # Flexibel
        self.confluence_spin.setValue(self._config.min_confluence_score)
        signal_layout.addRow("Min. Confluence:", self.confluence_spin)

        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(1, 3600)  # 1 Sek bis 1 Stunde
        self.interval_spin.setValue(self._config.analysis_interval_seconds)
        self.interval_spin.setSuffix(" Sek")
        signal_layout.addRow("Analyse-Intervall:", self.interval_spin)

        layout.addWidget(signal_group)

        # AI - Erweiterte Ranges
        ai_group = QGroupBox("AI Validation")
        ai_layout = QFormLayout(ai_group)

        self.ai_check = QCheckBox("AI Validation aktivieren")
        self.ai_check.setChecked(self._config.ai.enabled)
        ai_layout.addRow(self.ai_check)

        self.ai_threshold_spin = QSpinBox()
        self.ai_threshold_spin.setRange(0, 100)  # 0-100%
        self.ai_threshold_spin.setValue(self._config.ai.confidence_threshold)
        self.ai_threshold_spin.setSuffix(" %")
        ai_layout.addRow("Min. Confidence:", self.ai_threshold_spin)

        self.ai_provider_combo = QComboBox()
        self.ai_provider_combo.addItems(["openai", "anthropic", "gemini"])
        self.ai_provider_combo.setCurrentText(self._config.ai.provider)
        ai_layout.addRow("Provider:", self.ai_provider_combo)

        layout.addWidget(ai_group)

        # Performance Settings (Punkt 4: Pipeline Timeframe)
        perf_group = QGroupBox("⚡ Performance")
        perf_layout = QFormLayout(perf_group)

        self.pipeline_timeframe_combo = QComboBox()
        self.pipeline_timeframe_combo.addItems(["1m", "5m", "15m", "30m", "1h"])
        # Default auf "1m" wenn parent nicht existiert
        if self.parent() and hasattr(self.parent(), '_pipeline_timeframe'):
            current_tf = self.parent()._pipeline_timeframe
            idx = self.pipeline_timeframe_combo.findText(current_tf)
            if idx >= 0:
                self.pipeline_timeframe_combo.setCurrentIndex(idx)
        else:
            self.pipeline_timeframe_combo.setCurrentText("1m")

        perf_layout.addRow("Pipeline Timeframe:", self.pipeline_timeframe_combo)

        info_label = QLabel(
            "Pipeline läuft nur bei neuen Bars dieser Zeiteinheit.\n"
            "Kürzere Timeframes = mehr Updates, höhere CPU-Last.\n"
            "Längere Timeframes = weniger Updates, weniger CPU-Last."
        )
        info_label.setStyleSheet("color: #888; font-size: 10px;")
        info_label.setWordWrap(True)
        perf_layout.addRow(info_label)

        layout.addWidget(perf_group)

    def _apply_all_engine_settings(self) -> None:
        """Wendet alle Engine-Settings an ohne zu speichern.

        Settings werden in Config-Files gespeichert UND laufende Engines aktualisiert.
        """
        # Apply Basic Performance Settings (Pipeline Timeframe)
        if self.parent() and hasattr(self.parent(), '_pipeline_timeframe'):
            new_timeframe = self.pipeline_timeframe_combo.currentText()
            self.parent()._pipeline_timeframe = new_timeframe
            logger.info(f"Pipeline timeframe updated to: {new_timeframe}")

        # Apply Engine Settings
        if HAS_ENGINE_SETTINGS:
            self._entry_score_widget.apply_settings()
            self._trigger_exit_widget.apply_settings()
            self._leverage_widget.apply_settings()
            self._llm_widget.apply_settings()
            self._levels_widget.apply_settings()

            # Update laufende Engines im Parent (BotTab)
            if self.parent() and hasattr(self.parent(), 'update_engine_configs'):
                self.parent().update_engine_configs()
                QMessageBox.information(
                    self, "Settings Applied", "All settings (Basic + Engines) have been applied and engines updated."
                )
            else:
                QMessageBox.information(
                    self, "Settings Applied", "All settings have been applied.\n(Engines will be updated on next bot start)"
                )
        else:
            QMessageBox.information(self, "Settings Applied", "Performance settings have been applied.")

    def _save_all_engine_settings(self) -> None:
        """Speichert alle Engine-Settings.

        Settings werden in Config-Files gespeichert UND laufende Engines aktualisiert.
        """
        # Apply Basic Performance Settings (Pipeline Timeframe) - Runtime only
        if self.parent() and hasattr(self.parent(), '_pipeline_timeframe'):
            new_timeframe = self.pipeline_timeframe_combo.currentText()
            self.parent()._pipeline_timeframe = new_timeframe
            logger.info(f"Pipeline timeframe saved to: {new_timeframe}")

        # Save Engine Settings to Config Files
        if HAS_ENGINE_SETTINGS:
            self._entry_score_widget.save_settings()
            self._trigger_exit_widget.save_settings()
            self._leverage_widget.save_settings()
            self._llm_widget.save_settings()
            self._levels_widget.save_settings()

            # Update laufende Engines im Parent (BotTab)
            if self.parent() and hasattr(self.parent(), 'update_engine_configs'):
                self.parent().update_engine_configs()
                QMessageBox.information(
                    self, "Settings Saved", "All settings (Basic + Engines) have been saved and engines updated."
                )
            else:
                QMessageBox.information(
                    self, "Settings Saved", "All settings have been saved.\n(Engines will be updated on next bot start)"
                )
        else:
            QMessageBox.information(self, "Settings Saved", "Performance settings have been saved.")

    def get_config(self) -> "BotConfig":
        """Gibt die aktualisierten Einstellungen zurück."""
        from src.core.trading_bot import AIConfig, BotConfig

        return BotConfig(
            symbol=self._config.symbol,
            # paper_mode ist eine Property, nicht setzen
            risk_per_trade_percent=Decimal(str(self.risk_spin.value())),
            max_daily_loss_percent=Decimal(str(self.daily_loss_spin.value())),
            sl_atr_multiplier=Decimal(str(self.sl_spin.value())),
            tp_atr_multiplier=Decimal(str(self.tp_spin.value())),
            trailing_stop_enabled=self.trailing_check.isChecked(),
            trailing_stop_atr_multiplier=Decimal(str(self.trailing_spin.value())),
            min_confluence_score=self.confluence_spin.value(),
            analysis_interval_seconds=self.interval_spin.value(),
            ai=AIConfig(
                enabled=self.ai_check.isChecked(),
                confidence_threshold=self.ai_threshold_spin.value(),
                provider=self.ai_provider_combo.currentText(),
            ),
        )
