"""
LLM Validation Settings Widget - Konfiguration für LLMValidationService.

Erlaubt die Anpassung von:
- Enable/Disable LLM Validation
- Quick/Deep Routing Thresholds
- Score Modifiers (Boost/Caution/Veto)
- Prompt Settings
- Timeout & Fallback

Phase 5.4 der Bot-Integration.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QGroupBox,
    QLabel,
    QSpinBox,
    QDoubleSpinBox,
    QCheckBox,
    QPushButton,
    QSlider,
    QMessageBox,
)

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_PATH = Path("config/llm_validation_config.json")


class LLMValidationSettingsWidget(QWidget):
    """
    Widget für LLMValidationService-Einstellungen.

    Ermöglicht die Konfiguration aller LLM-Validierungs-Parameter.

    Signals:
        settings_changed: Emitted when settings are changed
        settings_saved: Emitted when settings are saved
    """

    settings_changed = pyqtSignal(dict)
    settings_saved = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._setup_ui()
        self._load_settings()
        self._connect_signals()

    def _setup_ui(self) -> None:
        """Setup the UI components."""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(12)

        # Title
        title = QLabel("<h3>LLM Validation Einstellungen</h3>")
        main_layout.addWidget(title)

        # Info
        info = QLabel(
            "LLM Validation agiert NUR als Veto/Boost - führt keine Trades aus!\n"
            "Bei deaktivierter Validation werden nur technische Signale verwendet."
        )
        info.setStyleSheet("color: #888;")
        info.setWordWrap(True)
        main_layout.addWidget(info)

        # Enable Group
        enable_group = self._create_enable_group()
        main_layout.addWidget(enable_group)

        # Routing Thresholds Group
        routing_group = self._create_routing_group()
        main_layout.addWidget(routing_group)

        # Score Modifiers Group
        modifiers_group = self._create_modifiers_group()
        main_layout.addWidget(modifiers_group)

        # Prompt Settings Group
        prompt_group = self._create_prompt_group()
        main_layout.addWidget(prompt_group)

        # Spacer
        main_layout.addStretch()

        # Action Buttons
        button_layout = QHBoxLayout()

        self._reset_btn = QPushButton("Zurücksetzen")
        self._reset_btn.clicked.connect(self._reset_to_defaults)
        button_layout.addWidget(self._reset_btn)

        button_layout.addStretch()

        self._apply_btn = QPushButton("Übernehmen")
        self._apply_btn.setStyleSheet(
            "background-color: #4CAF50; color: white; font-weight: bold; padding: 8px 16px;"
        )
        self._apply_btn.clicked.connect(self._apply_settings)
        button_layout.addWidget(self._apply_btn)

        self._save_btn = QPushButton("Speichern")
        self._save_btn.setStyleSheet(
            "background-color: #2196F3; color: white; font-weight: bold; padding: 8px 16px;"
        )
        self._save_btn.clicked.connect(self._save_settings)
        button_layout.addWidget(self._save_btn)

        main_layout.addLayout(button_layout)

    def _create_enable_group(self) -> QGroupBox:
        """Create enable/disable settings."""
        group = QGroupBox("LLM Validation Status")
        layout = QFormLayout(group)

        # Enable
        self._enabled = QCheckBox("LLM Validation aktivieren")
        self._enabled.setChecked(True)
        self._enabled.setToolTip(
            "Wenn deaktiviert, werden nur technische Signale verwendet."
        )
        layout.addRow(self._enabled)

        # Fallback
        self._fallback_to_technical = QCheckBox("Fallback zu Technical bei Fehler")
        self._fallback_to_technical.setChecked(True)
        self._fallback_to_technical.setToolTip(
            "Bei LLM-Fehler automatisch auf technische Analyse zurückfallen."
        )
        layout.addRow(self._fallback_to_technical)

        # Timeout
        self._timeout = QSpinBox()
        self._timeout.setRange(5, 120)
        self._timeout.setValue(30)
        self._timeout.setSuffix(" Sekunden")
        self._timeout.setToolTip("Timeout für LLM-Anfragen")
        layout.addRow("Timeout:", self._timeout)

        return group

    def _create_routing_group(self) -> QGroupBox:
        """Create Quick→Deep routing thresholds."""
        group = QGroupBox("Quick → Deep Routing Thresholds")
        layout = QVBoxLayout(group)

        # Visual explanation
        explanation = QLabel(
            "Quick Analyse:\n"
            "  • Confidence >= Approve → APPROVE/BOOST\n"
            "  • Approve > Confidence >= Deep → Deep Analyse\n"
            "  • Confidence < Deep → VETO"
        )
        explanation.setStyleSheet("color: #888; font-size: 10px; font-family: monospace;")
        layout.addWidget(explanation)

        form = QFormLayout()

        # Quick Approve Threshold
        self._quick_approve = QSpinBox()
        self._quick_approve.setRange(50, 100)
        self._quick_approve.setValue(75)
        self._quick_approve.setSuffix("%")
        self._quick_approve.setToolTip("Confidence für direktes Approval ohne Deep")
        form.addRow("Quick Approve >=", self._quick_approve)

        # Quick Deep Threshold
        self._quick_deep = QSpinBox()
        self._quick_deep.setRange(30, 80)
        self._quick_deep.setValue(50)
        self._quick_deep.setSuffix("%")
        self._quick_deep.setToolTip("Confidence Untergrenze für Deep Analyse")
        form.addRow("Quick → Deep >=", self._quick_deep)

        # Visual divider
        form.addRow(QLabel("— Deep Analyse Thresholds —"))

        # Deep Approve Threshold
        self._deep_approve = QSpinBox()
        self._deep_approve.setRange(40, 100)
        self._deep_approve.setValue(70)
        self._deep_approve.setSuffix("%")
        self._deep_approve.setToolTip("Confidence für Approval nach Deep Analyse")
        form.addRow("Deep Approve >=", self._deep_approve)

        # Deep Veto Threshold
        self._deep_veto = QSpinBox()
        self._deep_veto.setRange(20, 60)
        self._deep_veto.setValue(40)
        self._deep_veto.setSuffix("%")
        self._deep_veto.setToolTip("Confidence unter diesem Wert → VETO")
        form.addRow("Deep Veto <", self._deep_veto)

        layout.addLayout(form)

        return group

    def _create_modifiers_group(self) -> QGroupBox:
        """Create score modifier settings."""
        group = QGroupBox("Score Modifiers")
        layout = QFormLayout(group)

        info = QLabel("Modifikatoren auf Entry Score basierend auf LLM Action:")
        info.setStyleSheet("color: #888; font-size: 10px;")
        layout.addRow(info)

        # Boost Modifier
        self._boost_modifier = QDoubleSpinBox()
        self._boost_modifier.setRange(0.0, 0.5)
        self._boost_modifier.setValue(0.15)
        self._boost_modifier.setSingleStep(0.05)
        self._boost_modifier.setDecimals(2)
        self._boost_modifier.setPrefix("+")
        self._boost_modifier.setToolTip("Score-Bonus bei BOOST Action (+15% = +0.15)")
        layout.addRow("BOOST Modifier:", self._boost_modifier)

        # Caution Modifier
        self._caution_modifier = QDoubleSpinBox()
        self._caution_modifier.setRange(-0.5, 0.0)
        self._caution_modifier.setValue(-0.10)
        self._caution_modifier.setSingleStep(0.05)
        self._caution_modifier.setDecimals(2)
        self._caution_modifier.setToolTip("Score-Reduktion bei CAUTION Action (-10% = -0.10)")
        layout.addRow("CAUTION Modifier:", self._caution_modifier)

        # Veto Info
        veto_info = QLabel("VETO: Blockiert Entry komplett (Score → 0)")
        veto_info.setStyleSheet("color: #f44336; font-size: 10px;")
        layout.addRow(veto_info)

        return group

    def _create_prompt_group(self) -> QGroupBox:
        """Create prompt settings."""
        group = QGroupBox("Prompt Einstellungen")
        layout = QFormLayout(group)

        # Include Levels
        self._include_levels = QCheckBox("Support/Resistance Levels einbeziehen")
        self._include_levels.setChecked(True)
        self._include_levels.setToolTip("Detected Levels im Prompt inkludieren")
        layout.addRow(self._include_levels)

        # Include Indicators
        self._include_indicators = QCheckBox("Technische Indikatoren einbeziehen")
        self._include_indicators.setChecked(True)
        self._include_indicators.setToolTip("RSI, MACD, ADX etc. im Prompt inkludieren")
        layout.addRow(self._include_indicators)

        # Max Candles
        self._max_candles = QSpinBox()
        self._max_candles.setRange(0, 50)
        self._max_candles.setValue(10)
        self._max_candles.setToolTip("Anzahl der letzten Candles im Prompt (0 = keine)")
        layout.addRow("Max. Candles:", self._max_candles)

        # Max Tokens
        self._max_tokens = QSpinBox()
        self._max_tokens.setRange(500, 5000)
        self._max_tokens.setValue(2000)
        self._max_tokens.setSingleStep(100)
        self._max_tokens.setToolTip("Maximale Prompt-Länge in Tokens (approx)")
        layout.addRow("Max. Prompt Tokens:", self._max_tokens)

        return group

    def _connect_signals(self) -> None:
        """Connect change signals."""
        spinboxes = [
            self._timeout,
            self._quick_approve, self._quick_deep,
            self._deep_approve, self._deep_veto,
            self._boost_modifier, self._caution_modifier,
            self._max_candles, self._max_tokens,
        ]

        for spinbox in spinboxes:
            spinbox.valueChanged.connect(self._emit_settings_changed)

        checkboxes = [
            self._enabled, self._fallback_to_technical,
            self._include_levels, self._include_indicators,
        ]

        for checkbox in checkboxes:
            checkbox.stateChanged.connect(self._emit_settings_changed)

    def _emit_settings_changed(self) -> None:
        """Emit settings changed signal."""
        self.settings_changed.emit(self.get_settings())

    def get_settings(self) -> dict:
        """Get current settings as dict."""
        return {
            "enabled": self._enabled.isChecked(),
            "fallback_to_technical": self._fallback_to_technical.isChecked(),
            "timeout_seconds": self._timeout.value(),
            "thresholds": {
                "quick_approve": self._quick_approve.value(),
                "quick_deep": self._quick_deep.value(),
                "deep_approve": self._deep_approve.value(),
                "deep_veto": self._deep_veto.value(),
            },
            "modifiers": {
                "boost": self._boost_modifier.value(),
                "caution": self._caution_modifier.value(),
                "veto": -1.0,  # Always -1.0 for veto
            },
            "prompt": {
                "include_levels": self._include_levels.isChecked(),
                "include_indicators": self._include_indicators.isChecked(),
                "include_candles": self._max_candles.value(),
                "max_tokens": self._max_tokens.value(),
            },
        }

    def set_settings(self, settings: dict) -> None:
        """Set settings from dict."""
        self._enabled.setChecked(settings.get("enabled", True))
        self._fallback_to_technical.setChecked(settings.get("fallback_to_technical", True))
        self._timeout.setValue(settings.get("timeout_seconds", 30))

        if "thresholds" in settings:
            t = settings["thresholds"]
            self._quick_approve.setValue(t.get("quick_approve", 75))
            self._quick_deep.setValue(t.get("quick_deep", 50))
            self._deep_approve.setValue(t.get("deep_approve", 70))
            self._deep_veto.setValue(t.get("deep_veto", 40))

        if "modifiers" in settings:
            m = settings["modifiers"]
            self._boost_modifier.setValue(m.get("boost", 0.15))
            self._caution_modifier.setValue(m.get("caution", -0.10))

        if "prompt" in settings:
            p = settings["prompt"]
            self._include_levels.setChecked(p.get("include_levels", True))
            self._include_indicators.setChecked(p.get("include_indicators", True))
            self._max_candles.setValue(p.get("include_candles", 10))
            self._max_tokens.setValue(p.get("max_tokens", 2000))

    def _load_settings(self) -> None:
        """Load settings from config file."""
        try:
            if DEFAULT_CONFIG_PATH.exists():
                with open(DEFAULT_CONFIG_PATH, "r") as f:
                    settings = json.load(f)
                self.set_settings(settings)
                logger.info("LLM validation settings loaded from config")
        except Exception as e:
            logger.warning(f"Failed to load LLM validation settings: {e}")

    def _apply_settings(self) -> None:
        """Apply settings to service."""
        settings = self.get_settings()

        # Validate thresholds
        if self._quick_approve.value() <= self._quick_deep.value():
            QMessageBox.warning(
                self,
                "Ungültige Thresholds",
                "Quick Approve muss größer als Quick→Deep sein.",
            )
            return

        if self._deep_approve.value() <= self._deep_veto.value():
            QMessageBox.warning(
                self,
                "Ungültige Thresholds",
                "Deep Approve muss größer als Deep Veto sein.",
            )
            return

        try:
            from src.core.trading_bot import get_llm_validation_service, LLMValidationConfig

            service = get_llm_validation_service()
            config = LLMValidationConfig(
                enabled=settings["enabled"],
                fallback_to_technical=settings["fallback_to_technical"],
                timeout_seconds=settings["timeout_seconds"],
                quick_approve_threshold=settings["thresholds"]["quick_approve"],
                quick_deep_threshold=settings["thresholds"]["quick_deep"],
                deep_approve_threshold=settings["thresholds"]["deep_approve"],
                deep_veto_threshold=settings["thresholds"]["deep_veto"],
                boost_score_modifier=settings["modifiers"]["boost"],
                caution_score_modifier=settings["modifiers"]["caution"],
                include_levels=settings["prompt"]["include_levels"],
                include_indicators=settings["prompt"]["include_indicators"],
                include_candles=settings["prompt"]["include_candles"],
                max_prompt_tokens=settings["prompt"]["max_tokens"],
            )
            service.update_config(config)
            logger.info("LLM validation settings applied")

            QMessageBox.information(
                self, "Erfolg", "Einstellungen wurden übernommen."
            )
        except Exception as e:
            logger.error(f"Failed to apply LLM validation settings: {e}")
            QMessageBox.critical(
                self, "Fehler", f"Einstellungen konnten nicht übernommen werden:\n{e}"
            )

    def _save_settings(self) -> None:
        """Save settings to config file."""
        settings = self.get_settings()

        try:
            DEFAULT_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(DEFAULT_CONFIG_PATH, "w") as f:
                json.dump(settings, f, indent=2)

            self._apply_settings()
            self.settings_saved.emit()
            logger.info(f"LLM validation settings saved to {DEFAULT_CONFIG_PATH}")
        except Exception as e:
            logger.error(f"Failed to save LLM validation settings: {e}")
            QMessageBox.critical(
                self, "Fehler", f"Einstellungen konnten nicht gespeichert werden:\n{e}"
            )

    def _reset_to_defaults(self) -> None:
        """Reset to default settings."""
        defaults = {
            "enabled": True,
            "fallback_to_technical": True,
            "timeout_seconds": 30,
            "thresholds": {
                "quick_approve": 75,
                "quick_deep": 50,
                "deep_approve": 70,
                "deep_veto": 40,
            },
            "modifiers": {
                "boost": 0.15,
                "caution": -0.10,
            },
            "prompt": {
                "include_levels": True,
                "include_indicators": True,
                "include_candles": 10,
                "max_tokens": 2000,
            },
        }
        self.set_settings(defaults)
        self._emit_settings_changed()
        logger.info("LLM validation settings reset to defaults")
