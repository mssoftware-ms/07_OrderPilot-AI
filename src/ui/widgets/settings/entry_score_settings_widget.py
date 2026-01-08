"""
Entry Score Settings Widget - Konfiguration für EntryScoreEngine.

Erlaubt die Anpassung von:
- Komponenten-Gewichten (Trend, RSI, MACD, ADX, Volatility, Volume)
- Quality Thresholds (EXCELLENT, GOOD, MODERATE, WEAK)
- Gate-Einstellungen (Regime-Gates)
- Minimum Entry Score

Phase 5.1 der Bot-Integration.
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
    QProgressBar,
    QMessageBox,
)

logger = logging.getLogger(__name__)

# Default config file path
DEFAULT_CONFIG_PATH = Path("config/entry_score_config.json")


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
        self._setup_ui()
        self._load_settings()
        self._connect_signals()

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
        weights_group = self._create_weights_group()
        main_layout.addWidget(weights_group)

        # Quality Thresholds Group
        thresholds_group = self._create_thresholds_group()
        main_layout.addWidget(thresholds_group)

        # Gate Settings Group
        gates_group = self._create_gates_group()
        main_layout.addWidget(gates_group)

        # Entry Requirements Group
        entry_group = self._create_entry_group()
        main_layout.addWidget(entry_group)

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

    def _create_weights_group(self) -> QGroupBox:
        """Create component weights settings group."""
        group = QGroupBox("Komponenten-Gewichte (Summe = 1.0)")
        layout = QFormLayout(group)

        # Weight sum indicator
        self._weight_sum_label = QLabel("Summe: 1.00")
        self._weight_sum_bar = QProgressBar()
        self._weight_sum_bar.setRange(0, 100)
        self._weight_sum_bar.setValue(100)
        self._weight_sum_bar.setTextVisible(False)
        self._weight_sum_bar.setFixedHeight(8)

        sum_layout = QHBoxLayout()
        sum_layout.addWidget(self._weight_sum_label)
        sum_layout.addWidget(self._weight_sum_bar, 1)
        layout.addRow(sum_layout)

        # Trend Alignment Weight
        self._weight_trend = QDoubleSpinBox()
        self._weight_trend.setRange(0.0, 1.0)
        self._weight_trend.setValue(0.25)
        self._weight_trend.setSingleStep(0.05)
        self._weight_trend.setDecimals(2)
        self._weight_trend.setToolTip(
            "Gewicht für Trend-Alignment (EMA-Stack, Preis über/unter EMAs)."
        )
        layout.addRow("Trend Alignment:", self._weight_trend)

        # RSI Weight
        self._weight_rsi = QDoubleSpinBox()
        self._weight_rsi.setRange(0.0, 1.0)
        self._weight_rsi.setValue(0.15)
        self._weight_rsi.setSingleStep(0.05)
        self._weight_rsi.setDecimals(2)
        self._weight_rsi.setToolTip(
            "Gewicht für RSI (Oversold/Overbought + Neutral Zone)."
        )
        layout.addRow("RSI:", self._weight_rsi)

        # MACD Weight
        self._weight_macd = QDoubleSpinBox()
        self._weight_macd.setRange(0.0, 1.0)
        self._weight_macd.setValue(0.20)
        self._weight_macd.setSingleStep(0.05)
        self._weight_macd.setDecimals(2)
        self._weight_macd.setToolTip(
            "Gewicht für MACD (Crossover, Histogram-Richtung)."
        )
        layout.addRow("MACD:", self._weight_macd)

        # ADX Weight
        self._weight_adx = QDoubleSpinBox()
        self._weight_adx.setRange(0.0, 1.0)
        self._weight_adx.setValue(0.15)
        self._weight_adx.setSingleStep(0.05)
        self._weight_adx.setDecimals(2)
        self._weight_adx.setToolTip(
            "Gewicht für ADX (Trend-Stärke, DI+/DI- Alignment)."
        )
        layout.addRow("ADX:", self._weight_adx)

        # Volatility Weight
        self._weight_volatility = QDoubleSpinBox()
        self._weight_volatility.setRange(0.0, 1.0)
        self._weight_volatility.setValue(0.10)
        self._weight_volatility.setSingleStep(0.05)
        self._weight_volatility.setDecimals(2)
        self._weight_volatility.setToolTip(
            "Gewicht für Volatilität (ATR-basiert, nicht zu hoch/niedrig)."
        )
        layout.addRow("Volatility:", self._weight_volatility)

        # Volume Weight
        self._weight_volume = QDoubleSpinBox()
        self._weight_volume.setRange(0.0, 1.0)
        self._weight_volume.setValue(0.15)
        self._weight_volume.setSingleStep(0.05)
        self._weight_volume.setDecimals(2)
        self._weight_volume.setToolTip(
            "Gewicht für Volumen (Ratio zu Average, Volumentrend)."
        )
        layout.addRow("Volume:", self._weight_volume)

        return group

    def _create_thresholds_group(self) -> QGroupBox:
        """Create quality threshold settings group."""
        group = QGroupBox("Quality Thresholds")
        layout = QFormLayout(group)

        # Info
        info = QLabel("Score-Schwellenwerte für Quality-Klassifizierung:")
        info.setStyleSheet("color: #888; font-size: 11px;")
        layout.addRow(info)

        # Excellent Threshold
        self._threshold_excellent = QDoubleSpinBox()
        self._threshold_excellent.setRange(0.5, 1.0)
        self._threshold_excellent.setValue(0.80)
        self._threshold_excellent.setSingleStep(0.05)
        self._threshold_excellent.setDecimals(2)
        self._threshold_excellent.setToolTip("Score >= diesem Wert = EXCELLENT Quality")
        layout.addRow("EXCELLENT >=", self._threshold_excellent)

        # Good Threshold
        self._threshold_good = QDoubleSpinBox()
        self._threshold_good.setRange(0.4, 0.9)
        self._threshold_good.setValue(0.65)
        self._threshold_good.setSingleStep(0.05)
        self._threshold_good.setDecimals(2)
        self._threshold_good.setToolTip("Score >= diesem Wert = GOOD Quality")
        layout.addRow("GOOD >=", self._threshold_good)

        # Moderate Threshold
        self._threshold_moderate = QDoubleSpinBox()
        self._threshold_moderate.setRange(0.3, 0.8)
        self._threshold_moderate.setValue(0.50)
        self._threshold_moderate.setSingleStep(0.05)
        self._threshold_moderate.setDecimals(2)
        self._threshold_moderate.setToolTip("Score >= diesem Wert = MODERATE Quality")
        layout.addRow("MODERATE >=", self._threshold_moderate)

        # Weak Threshold
        self._threshold_weak = QDoubleSpinBox()
        self._threshold_weak.setRange(0.1, 0.6)
        self._threshold_weak.setValue(0.35)
        self._threshold_weak.setSingleStep(0.05)
        self._threshold_weak.setDecimals(2)
        self._threshold_weak.setToolTip("Score >= diesem Wert = WEAK Quality")
        layout.addRow("WEAK >=", self._threshold_weak)

        return group

    def _create_gates_group(self) -> QGroupBox:
        """Create regime gate settings group."""
        group = QGroupBox("Regime Gates")
        layout = QFormLayout(group)

        # Info
        info = QLabel("Gates können Entries blockieren oder Score modifizieren:")
        info.setStyleSheet("color: #888; font-size: 11px;")
        layout.addRow(info)

        # Block in CHOP
        self._block_in_chop = QCheckBox("Block bei CHOP/RANGE Regime")
        self._block_in_chop.setChecked(True)
        self._block_in_chop.setToolTip(
            "Blockiert Market-Entries wenn Markt in Seitwärtsbewegung ist."
        )
        layout.addRow(self._block_in_chop)

        # Block against trend
        self._block_against_trend = QCheckBox("Block gegen Strong Trend")
        self._block_against_trend.setChecked(True)
        self._block_against_trend.setToolTip(
            "Blockiert Long-Entries bei STRONG_TREND_BEAR und umgekehrt."
        )
        layout.addRow(self._block_against_trend)

        # Allow SFP counter-trend
        self._allow_sfp_counter = QCheckBox("SFP Counter-Trend erlauben")
        self._allow_sfp_counter.setChecked(True)
        self._allow_sfp_counter.setToolTip(
            "Erlaubt Swing Failure Pattern auch gegen den Trend."
        )
        layout.addRow(self._allow_sfp_counter)

        # Boost modifier
        self._boost_modifier = QDoubleSpinBox()
        self._boost_modifier.setRange(0.0, 0.5)
        self._boost_modifier.setValue(0.10)
        self._boost_modifier.setSingleStep(0.05)
        self._boost_modifier.setDecimals(2)
        self._boost_modifier.setPrefix("+")
        self._boost_modifier.setToolTip(
            "Score-Bonus bei aligned Strong Trend."
        )
        layout.addRow("Boost bei aligned Trend:", self._boost_modifier)

        # Chop penalty
        self._chop_penalty = QDoubleSpinBox()
        self._chop_penalty.setRange(0.0, 0.5)
        self._chop_penalty.setValue(0.15)
        self._chop_penalty.setSingleStep(0.05)
        self._chop_penalty.setDecimals(2)
        self._chop_penalty.setPrefix("-")
        self._chop_penalty.setToolTip(
            "Score-Reduktion bei CHOP Regime (wenn nicht blockiert)."
        )
        layout.addRow("Penalty bei CHOP:", self._chop_penalty)

        # Volatile penalty
        self._volatile_penalty = QDoubleSpinBox()
        self._volatile_penalty.setRange(0.0, 0.5)
        self._volatile_penalty.setValue(0.10)
        self._volatile_penalty.setSingleStep(0.05)
        self._volatile_penalty.setDecimals(2)
        self._volatile_penalty.setPrefix("-")
        self._volatile_penalty.setToolTip(
            "Score-Reduktion bei VOLATILITY_EXPLOSIVE Regime."
        )
        layout.addRow("Penalty bei Volatile:", self._volatile_penalty)

        return group

    def _create_entry_group(self) -> QGroupBox:
        """Create entry requirements group."""
        group = QGroupBox("Entry Requirements")
        layout = QFormLayout(group)

        # Min score for entry
        self._min_score_entry = QDoubleSpinBox()
        self._min_score_entry.setRange(0.1, 0.9)
        self._min_score_entry.setValue(0.50)
        self._min_score_entry.setSingleStep(0.05)
        self._min_score_entry.setDecimals(2)
        self._min_score_entry.setToolTip(
            "Minimum Entry Score für einen Trade.\n"
            "Unter diesem Wert: NO_SIGNAL."
        )
        layout.addRow("Min. Score für Entry:", self._min_score_entry)

        return group

    def _connect_signals(self) -> None:
        """Connect change signals."""
        # Weight spinboxes
        weight_spinboxes = [
            self._weight_trend,
            self._weight_rsi,
            self._weight_macd,
            self._weight_adx,
            self._weight_volatility,
            self._weight_volume,
        ]

        for spinbox in weight_spinboxes:
            spinbox.valueChanged.connect(self._on_weight_changed)
            spinbox.valueChanged.connect(self._emit_settings_changed)

        # Other spinboxes
        other_spinboxes = [
            self._threshold_excellent,
            self._threshold_good,
            self._threshold_moderate,
            self._threshold_weak,
            self._boost_modifier,
            self._chop_penalty,
            self._volatile_penalty,
            self._min_score_entry,
        ]

        for spinbox in other_spinboxes:
            spinbox.valueChanged.connect(self._emit_settings_changed)

        # Checkboxes
        checkboxes = [
            self._block_in_chop,
            self._block_against_trend,
            self._allow_sfp_counter,
        ]

        for checkbox in checkboxes:
            checkbox.stateChanged.connect(self._emit_settings_changed)

    def _on_weight_changed(self) -> None:
        """Update weight sum display."""
        total = (
            self._weight_trend.value()
            + self._weight_rsi.value()
            + self._weight_macd.value()
            + self._weight_adx.value()
            + self._weight_volatility.value()
            + self._weight_volume.value()
        )

        self._weight_sum_label.setText(f"Summe: {total:.2f}")
        self._weight_sum_bar.setValue(int(total * 100))

        # Color indicator
        if abs(total - 1.0) < 0.01:
            self._weight_sum_bar.setStyleSheet(
                "QProgressBar::chunk { background-color: #4CAF50; }"
            )
        else:
            self._weight_sum_bar.setStyleSheet(
                "QProgressBar::chunk { background-color: #f44336; }"
            )

    def _emit_settings_changed(self) -> None:
        """Emit settings changed signal."""
        self.settings_changed.emit(self.get_settings())

    def get_settings(self) -> dict:
        """Get current settings as dict."""
        return {
            "weights": {
                "trend_alignment": self._weight_trend.value(),
                "rsi": self._weight_rsi.value(),
                "macd": self._weight_macd.value(),
                "adx": self._weight_adx.value(),
                "volatility": self._weight_volatility.value(),
                "volume": self._weight_volume.value(),
            },
            "thresholds": {
                "excellent": self._threshold_excellent.value(),
                "good": self._threshold_good.value(),
                "moderate": self._threshold_moderate.value(),
                "weak": self._threshold_weak.value(),
            },
            "gates": {
                "block_in_chop": self._block_in_chop.isChecked(),
                "block_against_strong_trend": self._block_against_trend.isChecked(),
                "allow_counter_trend_sfp": self._allow_sfp_counter.isChecked(),
                "trend_boost": self._boost_modifier.value(),
                "chop_penalty": self._chop_penalty.value(),
                "volatile_penalty": self._volatile_penalty.value(),
            },
            "min_score_for_entry": self._min_score_entry.value(),
        }

    def set_settings(self, settings: dict) -> None:
        """Set settings from dict."""
        if "weights" in settings:
            w = settings["weights"]
            self._weight_trend.setValue(w.get("trend_alignment", 0.25))
            self._weight_rsi.setValue(w.get("rsi", 0.15))
            self._weight_macd.setValue(w.get("macd", 0.20))
            self._weight_adx.setValue(w.get("adx", 0.15))
            self._weight_volatility.setValue(w.get("volatility", 0.10))
            self._weight_volume.setValue(w.get("volume", 0.15))

        if "thresholds" in settings:
            t = settings["thresholds"]
            self._threshold_excellent.setValue(t.get("excellent", 0.80))
            self._threshold_good.setValue(t.get("good", 0.65))
            self._threshold_moderate.setValue(t.get("moderate", 0.50))
            self._threshold_weak.setValue(t.get("weak", 0.35))

        if "gates" in settings:
            g = settings["gates"]
            self._block_in_chop.setChecked(g.get("block_in_chop", True))
            self._block_against_trend.setChecked(g.get("block_against_strong_trend", True))
            self._allow_sfp_counter.setChecked(g.get("allow_counter_trend_sfp", True))
            self._boost_modifier.setValue(g.get("trend_boost", 0.10))
            self._chop_penalty.setValue(g.get("chop_penalty", 0.15))
            self._volatile_penalty.setValue(g.get("volatile_penalty", 0.10))

        self._min_score_entry.setValue(settings.get("min_score_for_entry", 0.50))

        self._on_weight_changed()

    def _load_settings(self) -> None:
        """Load settings from config file."""
        try:
            if DEFAULT_CONFIG_PATH.exists():
                with open(DEFAULT_CONFIG_PATH, "r") as f:
                    settings = json.load(f)
                self.set_settings(settings)
                logger.info("Entry score settings loaded from config")
            else:
                self._on_weight_changed()  # Initialize display
        except Exception as e:
            logger.warning(f"Failed to load entry score settings: {e}")
            self._on_weight_changed()

    def _apply_settings(self) -> None:
        """Apply settings to engine."""
        settings = self.get_settings()

        # Validate weights sum
        total = sum(settings["weights"].values())
        if abs(total - 1.0) > 0.01:
            QMessageBox.warning(
                self,
                "Ungültige Gewichte",
                f"Die Gewichte müssen sich zu 1.0 summieren.\n"
                f"Aktuelle Summe: {total:.2f}",
            )
            return

        try:
            from src.core.trading_bot import get_entry_score_engine, EntryScoreConfig

            engine = get_entry_score_engine()
            config = EntryScoreConfig(
                trend_weight=settings["weights"]["trend_alignment"],
                rsi_weight=settings["weights"]["rsi"],
                macd_weight=settings["weights"]["macd"],
                adx_weight=settings["weights"]["adx"],
                volatility_weight=settings["weights"]["volatility"],
                volume_weight=settings["weights"]["volume"],
                excellent_threshold=settings["thresholds"]["excellent"],
                good_threshold=settings["thresholds"]["good"],
                moderate_threshold=settings["thresholds"]["moderate"],
                weak_threshold=settings["thresholds"]["weak"],
                block_in_chop=settings["gates"]["block_in_chop"],
                block_against_strong_trend=settings["gates"]["block_against_strong_trend"],
                allow_counter_trend_sfp=settings["gates"]["allow_counter_trend_sfp"],
                trend_boost=settings["gates"]["trend_boost"],
                chop_penalty=settings["gates"]["chop_penalty"],
                volatile_penalty=settings["gates"]["volatile_penalty"],
                min_score_for_entry=settings["min_score_for_entry"],
            )
            engine.update_config(config)
            logger.info("Entry score settings applied")

            QMessageBox.information(
                self, "Erfolg", "Einstellungen wurden übernommen."
            )
        except Exception as e:
            logger.error(f"Failed to apply entry score settings: {e}")
            QMessageBox.critical(
                self, "Fehler", f"Einstellungen konnten nicht übernommen werden:\n{e}"
            )

    def _save_settings(self) -> None:
        """Save settings to config file."""
        settings = self.get_settings()

        # Validate weights sum
        total = sum(settings["weights"].values())
        if abs(total - 1.0) > 0.01:
            QMessageBox.warning(
                self,
                "Ungültige Gewichte",
                f"Die Gewichte müssen sich zu 1.0 summieren.\n"
                f"Aktuelle Summe: {total:.2f}",
            )
            return

        try:
            DEFAULT_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(DEFAULT_CONFIG_PATH, "w") as f:
                json.dump(settings, f, indent=2)

            self._apply_settings()
            self.settings_saved.emit()
            logger.info(f"Entry score settings saved to {DEFAULT_CONFIG_PATH}")
        except Exception as e:
            logger.error(f"Failed to save entry score settings: {e}")
            QMessageBox.critical(
                self, "Fehler", f"Einstellungen konnten nicht gespeichert werden:\n{e}"
            )

    def _reset_to_defaults(self) -> None:
        """Reset to default settings."""
        self.set_settings({
            "weights": {
                "trend_alignment": 0.25,
                "rsi": 0.15,
                "macd": 0.20,
                "adx": 0.15,
                "volatility": 0.10,
                "volume": 0.15,
            },
            "thresholds": {
                "excellent": 0.80,
                "good": 0.65,
                "moderate": 0.50,
                "weak": 0.35,
            },
            "gates": {
                "block_in_chop": True,
                "block_against_strong_trend": True,
                "allow_counter_trend_sfp": True,
                "trend_boost": 0.10,
                "chop_penalty": 0.15,
                "volatile_penalty": 0.10,
            },
            "min_score_for_entry": 0.50,
        })
        self._emit_settings_changed()
        logger.info("Entry score settings reset to defaults")
