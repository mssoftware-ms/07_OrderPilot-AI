"""Bot UI Control Widgets - Widget Builder Module.

Creates all PyQt6 widgets for bot control panel using composition pattern.
Extracted from BotUIControlMixin for Single Responsibility.

Module 1/4 of bot_ui_control_mixin.py split.
"""

from __future__ import annotations

import logging
from pathlib import Path

from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

logger = logging.getLogger(__name__)


class BotUIControlWidgets:
    """Widget builder for bot control UI elements.

    Creates all UI groups and widgets with proper styling and tooltips.
    """

    def __init__(self, parent):
        """Initialize widget builder.

        Args:
            parent: Parent widget (typically BotUIControlMixin)
        """
        self.parent = parent

    def build_control_group(self) -> QGroupBox:
        """Create bot control group with Start/Stop/Pause buttons."""
        control_group = QGroupBox("Bot Control")
        control_layout = QHBoxLayout()
        control_layout.setContentsMargins(8, 8, 8, 8)

        self.parent.bot_status_label = QLabel("Status: STOPPED")
        self.parent.bot_status_label.setStyleSheet(
            "font-weight: bold; color: #9e9e9e; font-size: 14px;"
        )
        control_layout.addWidget(self.parent.bot_status_label)
        control_layout.addStretch()

        self.parent.bot_start_btn = QPushButton("Start Bot")
        self.parent.bot_start_btn.setStyleSheet(
            "background-color: #26a69a; color: white; font-weight: bold; "
            "padding: 8px 16px;"
        )
        self.parent.bot_start_btn.clicked.connect(self.parent._on_bot_start_clicked)
        control_layout.addWidget(self.parent.bot_start_btn)

        self.parent.bot_stop_btn = QPushButton("Stop Bot")
        self.parent.bot_stop_btn.setStyleSheet(
            "background-color: #ef5350; color: white; font-weight: bold; "
            "padding: 8px 16px;"
        )
        self.parent.bot_stop_btn.setEnabled(False)
        self.parent.bot_stop_btn.clicked.connect(self.parent._on_bot_stop_clicked)
        control_layout.addWidget(self.parent.bot_stop_btn)

        self.parent.bot_pause_btn = QPushButton("Pause")
        self.parent.bot_pause_btn.setStyleSheet("padding: 8px;")
        self.parent.bot_pause_btn.setEnabled(False)
        self.parent.bot_pause_btn.clicked.connect(self.parent._on_bot_pause_clicked)
        control_layout.addWidget(self.parent.bot_pause_btn)

        control_group.setLayout(control_layout)
        return control_group

    def build_settings_group(self) -> QGroupBox:
        """Create bot settings group with all configuration options."""
        settings_group = QGroupBox("Bot Settings")
        settings_layout = QFormLayout()

        # Symbol Label
        self.parent.bot_symbol_label = QLabel("-")
        self.parent.bot_symbol_label.setStyleSheet("font-weight: bold; font-size: 13px;")
        settings_layout.addRow("Symbol:", self.parent.bot_symbol_label)

        # KI Mode
        self.parent.ki_mode_combo = QComboBox()
        self.parent.ki_mode_combo.addItems(["NO_KI", "LOW_KI", "FULL_KI"])
        self.parent.ki_mode_combo.setCurrentIndex(0)
        self.parent.ki_mode_combo.currentTextChanged.connect(self.parent._on_ki_mode_changed)
        self.parent.ki_mode_combo.setToolTip(
            "KI Mode:\n"
            "- NO_KI: Rein regelbasiert, kein LLM-Call\n"
            "- LOW_KI: Daily Strategy Selection (1 Call/Tag)\n"
            "- FULL_KI: Daily + Intraday Events (RegimeFlip, Exit, Signal)"
        )
        settings_layout.addRow("KI Mode:", self.parent.ki_mode_combo)

        # Trade Direction / Bias
        self.parent.trade_direction_combo = QComboBox()
        self.parent.trade_direction_combo.addItems(["AUTO", "BOTH", "LONG_ONLY", "SHORT_ONLY"])
        self.parent.trade_direction_combo.setCurrentIndex(0)
        self.parent.trade_direction_combo.setToolTip(
            "Trade Direction Bias:\n"
            "- AUTO: Wird durch Backtesting automatisch ermittelt (empfohlen)\n"
            "- BOTH: Long UND Short Trades erlaubt\n"
            "- LONG_ONLY: Nur Long-Positionen (Aufwärtstrend)\n"
            "- SHORT_ONLY: Nur Short-Positionen (Abwärtstrend)\n\n"
            "AUTO analysiert historische Daten und wählt die profitabelste Richtung."
        )
        self.parent.trade_direction_combo.setStyleSheet("QComboBox { font-weight: bold; }")
        self.parent.trade_direction_combo.currentTextChanged.connect(
            self.parent._on_trade_direction_changed
        )
        settings_layout.addRow("Trade Richtung:", self.parent.trade_direction_combo)

        # Trailing Mode
        self.parent.trailing_mode_combo = QComboBox()
        self.parent.trailing_mode_combo.addItems(["PCT", "ATR", "SWING"])
        self.parent.trailing_mode_combo.setCurrentIndex(1)
        self.parent.trailing_mode_combo.setToolTip(
            "Trailing Stop Mode:\n"
            "- PCT: Fester Prozent-Abstand vom aktuellen Kurs\n"
            "- ATR: Volatilitaets-basiert (ATR-Multiple), Regime-angepasst\n"
            "- SWING: Bollinger Bands als Support/Resistance"
        )
        self.parent.trailing_mode_combo.currentTextChanged.connect(
            self.parent._on_trailing_mode_changed
        )
        settings_layout.addRow("Trailing Mode:", self.parent.trailing_mode_combo)

        # Initial Stop Loss
        self.parent.initial_sl_spin = QDoubleSpinBox()
        self.parent.initial_sl_spin.setRange(0.1, 10.0)
        self.parent.initial_sl_spin.setValue(1.5)
        self.parent.initial_sl_spin.setSuffix(" %")
        self.parent.initial_sl_spin.setDecimals(2)
        self.parent.initial_sl_spin.setToolTip(
            "Initial Stop-Loss in Prozent vom Entry-Preis.\n"
            "Dies ist der EINZIGE fixe Parameter - alle anderen Exits sind dynamisch.\n"
            "Empfohlen: 1.5-3% fuer Aktien, 2-5% fuer Crypto."
        )
        settings_layout.addRow("Initial SL %:", self.parent.initial_sl_spin)

        # Capital
        self.parent.bot_capital_spin = QDoubleSpinBox()
        self.parent.bot_capital_spin.setRange(10, 10000000)
        self.parent.bot_capital_spin.setValue(100)
        self.parent.bot_capital_spin.setPrefix("€ ")
        self.parent.bot_capital_spin.setDecimals(0)
        self.parent.bot_capital_spin.setToolTip(
            "Verfuegbares Kapital fuer den Bot.\n"
            "Basis fuer Positionsgroessen-Berechnung und P&L%.\n"
            "Bei kleinem Kapital (<500€) ist Hebel oft nötig!"
        )
        settings_layout.addRow("Kapital:", self.parent.bot_capital_spin)

        # Risk per Trade
        self.parent.risk_per_trade_spin = QDoubleSpinBox()
        self.parent.risk_per_trade_spin.setRange(0.1, 100.0)
        self.parent.risk_per_trade_spin.setValue(50.0)
        self.parent.risk_per_trade_spin.setSuffix(" %")
        self.parent.risk_per_trade_spin.setDecimals(2)
        self.parent.risk_per_trade_spin.setToolTip(
            "Prozent des Kapitals, das pro Trade investiert wird.\n"
            "Beispiel: 100EUR Kapital x 50% = 50EUR pro Trade.\n"
            "Bei Micro-Account empfohlen: 30-50% mit engem SL."
        )
        settings_layout.addRow("Risk/Trade %:", self.parent.risk_per_trade_spin)

        # Max Trades per Day
        self.parent.max_trades_spin = QSpinBox()
        self.parent.max_trades_spin.setRange(1, 50)
        self.parent.max_trades_spin.setValue(10)
        settings_layout.addRow("Max Trades/Day:", self.parent.max_trades_spin)

        # Max Daily Loss
        self.parent.max_daily_loss_spin = QDoubleSpinBox()
        self.parent.max_daily_loss_spin.setRange(0.5, 10.0)
        self.parent.max_daily_loss_spin.setValue(3.0)
        self.parent.max_daily_loss_spin.setSuffix(" %")
        self.parent.max_daily_loss_spin.setDecimals(2)
        settings_layout.addRow("Max Daily Loss %:", self.parent.max_daily_loss_spin)

        # NOTE: Paper Mode, MACD Exit, RSI Exit, Derivathandel und Leverage Override
        # wurden in eine separate GroupBox "Quick Toggles & Leverage" verschoben (Issue #43)
        # Siehe build_quick_toggles_group()

        # === SAVE/LOAD DEFAULTS SECTION ===
        defaults_separator = QLabel("─── Einstellungen ───")
        defaults_separator.setStyleSheet("color: #4CAF50; font-weight: bold; margin-top: 10px;")
        settings_layout.addRow(defaults_separator)

        defaults_widget = QWidget()
        defaults_layout = QHBoxLayout(defaults_widget)
        defaults_layout.setContentsMargins(0, 0, 0, 0)
        defaults_layout.setSpacing(8)

        self.parent.save_defaults_btn = QPushButton("💾 Speichern")
        self.parent.save_defaults_btn.setStyleSheet(
            "background-color: #4CAF50; color: white; padding: 4px 8px; font-size: 10px;"
        )
        self.parent.save_defaults_btn.setToolTip("Aktuelle Einstellungen als Standard speichern")
        self.parent.save_defaults_btn.clicked.connect(self.parent._on_save_defaults_clicked)
        defaults_layout.addWidget(self.parent.save_defaults_btn)

        self.parent.load_defaults_btn = QPushButton("📂 Laden")
        self.parent.load_defaults_btn.setStyleSheet(
            "background-color: #2196F3; color: white; padding: 4px 8px; font-size: 10px;"
        )
        self.parent.load_defaults_btn.setToolTip("Gespeicherte Standard-Einstellungen laden")
        self.parent.load_defaults_btn.clicked.connect(self.parent._on_load_defaults_clicked)
        defaults_layout.addWidget(self.parent.load_defaults_btn)

        self.parent.reset_defaults_btn = QPushButton("🔄 Reset")
        self.parent.reset_defaults_btn.setStyleSheet(
            "background-color: #607D8B; color: white; padding: 4px 8px; font-size: 10px;"
        )
        self.parent.reset_defaults_btn.setToolTip("Auf Factory-Defaults zurücksetzen")
        self.parent.reset_defaults_btn.clicked.connect(self.parent._on_reset_defaults_clicked)
        defaults_layout.addWidget(self.parent.reset_defaults_btn)

        settings_layout.addRow("Defaults:", defaults_widget)

        settings_group.setLayout(settings_layout)
        return settings_group

    def build_quick_toggles_group(self) -> QGroupBox:
        """Create combined Quick Toggles & Leverage Override group (Issue #43).

        Combines Paper Mode, MACD Exit, RSI Exit, Derivathandel and Leverage Override
        in a compact two-column layout.
        """
        group = QGroupBox("⚡ Quick Toggles & Leverage")
        main_layout = QHBoxLayout(group)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(12)

        # === LEFT COLUMN: Toggles ===
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(4)

        # Paper Mode
        self.parent.disable_restrictions_cb = QCheckBox("Paper Mode")
        self.parent.disable_restrictions_cb.setChecked(True)
        self.parent.disable_restrictions_cb.setToolTip(
            "Deaktiviert Max Trades/Day und Max Daily Loss Limits.\n"
            "Empfohlen fuer Paper Trading und Strategie-Tests.\n"
            "Im Live-Modus sollten Restriktionen AKTIVIERT sein!"
        )
        self.parent.disable_restrictions_cb.setStyleSheet("color: #ff9800; font-weight: bold;")
        left_layout.addWidget(self.parent.disable_restrictions_cb)

        # MACD Exit
        self.parent.disable_macd_exit_cb = QCheckBox("MACD-Exit deaktiv.")
        self.parent.disable_macd_exit_cb.setChecked(False)
        self.parent.disable_macd_exit_cb.setToolTip(
            "Deaktiviert den automatischen Verkauf bei MACD-Kreuzungen.\n"
            "Position wird nur durch Stop-Loss geschlossen."
        )
        left_layout.addWidget(self.parent.disable_macd_exit_cb)

        # RSI Exit
        self.parent.disable_rsi_exit_cb = QCheckBox("RSI-Exit deaktiv.")
        self.parent.disable_rsi_exit_cb.setChecked(False)
        self.parent.disable_rsi_exit_cb.setToolTip(
            "Deaktiviert den automatischen Verkauf bei RSI-Extremwerten.\n"
            "Position wird nur durch Stop-Loss geschlossen."
        )
        left_layout.addWidget(self.parent.disable_rsi_exit_cb)

        # Derivathandel
        self.parent.enable_derivathandel_cb = QCheckBox("Derivathandel")
        self.parent.enable_derivathandel_cb.setChecked(False)
        self.parent.enable_derivathandel_cb.setToolTip(
            "Bei aktiviert: Automatische KO-Produkt-Suche bei Signal-Bestaetigung.\n"
            "ACHTUNG: KO-Produkte haben hoeheres Risiko!"
        )
        self.parent.enable_derivathandel_cb.setStyleSheet("color: #ff5722; font-weight: bold;")
        self.parent.enable_derivathandel_cb.stateChanged.connect(
            self.parent._on_derivathandel_changed
        )
        left_layout.addWidget(self.parent.enable_derivathandel_cb)

        left_layout.addStretch()
        main_layout.addWidget(left_widget)

        # === VERTICAL SEPARATOR ===
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setStyleSheet("color: #444;")
        main_layout.addWidget(separator)

        # === RIGHT COLUMN: Leverage Override ===
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(4)

        # Leverage Override Checkbox
        self.parent.leverage_override_cb = QCheckBox("Manueller Hebel")
        self.parent.leverage_override_cb.setChecked(True)
        self.parent.leverage_override_cb.setToolTip(
            "Aktiviert manuelle Hebel-Überschreibung.\n"
            "WICHTIG für Micro-Accounts (<500€)!"
        )
        self.parent.leverage_override_cb.setStyleSheet("color: #FF9800; font-weight: bold;")
        self.parent.leverage_override_cb.stateChanged.connect(
            self.parent._on_leverage_override_changed
        )
        right_layout.addWidget(self.parent.leverage_override_cb)

        # Leverage Slider mit Wert-Anzeige
        slider_widget = QWidget()
        slider_layout = QHBoxLayout(slider_widget)
        slider_layout.setContentsMargins(0, 0, 0, 0)
        slider_layout.setSpacing(4)

        self.parent.leverage_slider = QSlider(Qt.Orientation.Horizontal)
        self.parent.leverage_slider.setRange(1, 100)
        self.parent.leverage_slider.setValue(20)
        self.parent.leverage_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.parent.leverage_slider.setTickInterval(20)
        self.parent.leverage_slider.setToolTip(
            "Manueller Hebel (1x - 100x).\n"
            "Empfohlen für 100€ Kapital: 15-25x"
        )
        self.parent.leverage_slider.valueChanged.connect(self.parent._on_leverage_slider_changed)
        slider_layout.addWidget(self.parent.leverage_slider, stretch=2)

        self.parent.leverage_value_label = QLabel("20x")
        self.parent.leverage_value_label.setStyleSheet(
            "font-weight: bold; font-size: 13px; color: #FF9800; min-width: 40px;"
        )
        slider_layout.addWidget(self.parent.leverage_value_label)
        right_layout.addWidget(slider_widget)

        # Quick-Select Buttons für Leverage
        quick_widget = QWidget()
        quick_layout = QHBoxLayout(quick_widget)
        quick_layout.setContentsMargins(0, 0, 0, 0)
        quick_layout.setSpacing(2)

        for lev in [5, 10, 20, 50, 75, 100]:
            btn = QPushButton(f"{lev}x")
            btn.setFixedWidth(32)
            btn.setStyleSheet("padding: 2px; font-size: 9px;")
            btn.clicked.connect(lambda checked, l=lev: self.parent._set_leverage(l))
            quick_layout.addWidget(btn)

        right_layout.addWidget(quick_widget)
        right_layout.addStretch()
        main_layout.addWidget(right_widget)

        return group

    def build_trailing_group(self) -> QGroupBox:
        """Create trailing stop settings group."""
        trailing_group = QGroupBox("Trailing Stop Settings")
        trailing_layout = QFormLayout()

        # Regime-Adaptive
        self.parent.regime_adaptive_cb = QCheckBox("Regime-Adaptiv")
        self.parent.regime_adaptive_cb.setChecked(True)
        self.parent.regime_adaptive_cb.setToolTip(
            "Passt ATR-Multiplier automatisch an Marktregime an:\n"
            "- Trending (ADX > 25): Engerer Stop (mehr Gewinn mitnehmen)\n"
            "- Ranging (ADX < 20): Weiterer Stop (weniger Whipsaws)"
        )
        self.parent.regime_adaptive_cb.stateChanged.connect(self.parent._on_regime_adaptive_changed)
        trailing_layout.addRow("Adaptive:", self.parent.regime_adaptive_cb)

        # Trailing Activation
        self.parent.trailing_activation_spin = QDoubleSpinBox()
        self.parent.trailing_activation_spin.setRange(0.0, 100.0)
        self.parent.trailing_activation_spin.setValue(5.0)
        self.parent.trailing_activation_spin.setSingleStep(1.0)
        self.parent.trailing_activation_spin.setDecimals(1)
        self.parent.trailing_activation_spin.setSuffix(" %")
        self.parent.trailing_activation_spin.setToolTip(
            "Ab welchem GEWINN (Return on Risk) der Trailing Stop aktiviert wird.\n\n"
            "Beispiel bei 100EUR Risiko:\n"
            "- 0% = sofort wenn im Gewinn\n"
            "- 10% = Trailing erst ab 10EUR Gewinn aktiv\n"
            "- 50% = Trailing erst ab 50EUR Gewinn aktiv\n\n"
            "Bis zur Aktivierung gilt nur der Initial Stop Loss (rot)."
        )
        trailing_layout.addRow("Aktivierung ab:", self.parent.trailing_activation_spin)

        # TRA Percent
        self.parent.tra_percent_spin = QDoubleSpinBox()
        self.parent.tra_percent_spin.setRange(0.0, 10.0)
        self.parent.tra_percent_spin.setValue(0.5)
        self.parent.tra_percent_spin.setSingleStep(0.1)
        self.parent.tra_percent_spin.setDecimals(2)
        self.parent.tra_percent_spin.setSuffix(" %")
        self.parent.tra_percent_spin.setToolTip(
            "Trailing Activation Percent.\n"
            "Wird in die Signals-Tabelle übernommen und steuert,\n"
            "wann der Trailing Stop aktiv wird."
        )
        trailing_layout.addRow("TRA%:", self.parent.tra_percent_spin)

        # Trailing Distance
        self.parent.trailing_distance_spin = QDoubleSpinBox()
        self.parent.trailing_distance_spin.setRange(0.1, 10.0)
        self.parent.trailing_distance_spin.setValue(1.0)
        self.parent.trailing_distance_spin.setSingleStep(0.1)
        self.parent.trailing_distance_spin.setDecimals(2)
        self.parent.trailing_distance_spin.setSuffix(" %")
        self.parent.trailing_distance_spin.setToolTip(
            "Abstand des Trailing Stops zum AKTUELLEN Kurs in %.\n\n"
            "Beispiel LONG:\n"
            "- Kurs bei 102EUR, Abstand 1.5% -> Stop bei 100.47EUR\n"
            "- Kurs steigt auf 105EUR -> Stop steigt auf 103.43EUR\n\n"
            "Stop bewegt sich NUR in guenstige Richtung!"
        )
        trailing_layout.addRow("Abstand (PCT):", self.parent.trailing_distance_spin)

        # ATR Multiplier
        self.parent.atr_multiplier_spin = QDoubleSpinBox()
        self.parent.atr_multiplier_spin.setRange(0.5, 8.0)
        self.parent.atr_multiplier_spin.setValue(1.5)
        self.parent.atr_multiplier_spin.setSingleStep(0.1)
        self.parent.atr_multiplier_spin.setDecimals(2)
        self.parent.atr_multiplier_spin.setToolTip(
            "Fester ATR-Multiplier (wenn Regime-Adaptiv AUS).\n"
            "Stop = Highest High - (ATR x Multiplier)\n"
            "Hoeher = weiterer Stop, weniger Whipsaws"
        )
        trailing_layout.addRow("ATR Multiplier:", self.parent.atr_multiplier_spin)

        # ATR Trending
        self.parent.atr_trending_spin = QDoubleSpinBox()
        self.parent.atr_trending_spin.setRange(0.5, 5.0)
        self.parent.atr_trending_spin.setValue(1.2)
        self.parent.atr_trending_spin.setSingleStep(0.1)
        self.parent.atr_trending_spin.setDecimals(2)
        self.parent.atr_trending_spin.setToolTip(
            "ATR-Multiplier fuer TRENDING Maerkte (ADX > 25).\n"
            "Niedriger = engerer Stop = mehr Gewinn mitnehmen\n"
            "Empfohlen: 1.5-2.5x"
        )
        trailing_layout.addRow("ATR Trending:", self.parent.atr_trending_spin)

        # ATR Ranging
        self.parent.atr_ranging_spin = QDoubleSpinBox()
        self.parent.atr_ranging_spin.setRange(1.0, 8.0)
        self.parent.atr_ranging_spin.setValue(2.0)
        self.parent.atr_ranging_spin.setSingleStep(0.1)
        self.parent.atr_ranging_spin.setDecimals(2)
        self.parent.atr_ranging_spin.setToolTip(
            "ATR-Multiplier fuer RANGING/CHOPPY Maerkte (ADX < 20).\n"
            "Hoeher = weiterer Stop = weniger Whipsaws\n"
            "Empfohlen: 3.0-4.0x"
        )
        trailing_layout.addRow("ATR Ranging:", self.parent.atr_ranging_spin)

        # Volatility Bonus
        self.parent.volatility_bonus_spin = QDoubleSpinBox()
        self.parent.volatility_bonus_spin.setRange(0.0, 2.0)
        self.parent.volatility_bonus_spin.setValue(0.5)
        self.parent.volatility_bonus_spin.setSingleStep(0.1)
        self.parent.volatility_bonus_spin.setDecimals(2)
        self.parent.volatility_bonus_spin.setToolTip(
            "Extra ATR-Multiplier bei hoher Volatilitaet.\n"
            "Wird hinzuaddiert wenn ATR > 2% des Preises.\n"
            "Empfohlen: 0.3-0.5x"
        )
        trailing_layout.addRow("Vol. Bonus:", self.parent.volatility_bonus_spin)

        # Min Step
        self.parent.min_step_spin = QDoubleSpinBox()
        self.parent.min_step_spin.setRange(0.05, 2.0)
        self.parent.min_step_spin.setValue(0.3)
        self.parent.min_step_spin.setSingleStep(0.05)
        self.parent.min_step_spin.setSuffix(" %")
        self.parent.min_step_spin.setDecimals(2)
        self.parent.min_step_spin.setToolTip(
            "Mindest-Bewegung fuer Stop-Update.\n"
            "Verhindert zu haeufige kleine Anpassungen.\n"
            "Empfohlen: 0.2-0.5% fuer Crypto"
        )
        trailing_layout.addRow("Min Step:", self.parent.min_step_spin)

        trailing_group.setLayout(trailing_layout)
        return trailing_group

    def build_pattern_group(self) -> QGroupBox:
        """Create pattern validation settings group."""
        pattern_group = QGroupBox("Pattern Validation")
        pattern_layout = QFormLayout(pattern_group)

        # Min Score
        self.parent.min_score_spin = QSpinBox()
        self.parent.min_score_spin.setRange(0, 100)
        self.parent.min_score_spin.setValue(55)
        self.parent.min_score_spin.setSingleStep(1)
        self.parent.min_score_spin.setToolTip(
            "Minimaler Score (Ganzzahl 0-100) für Trade-Einstieg.\n"
            "0 = immer erlaubt, 100 = nur perfekte Signale.\n"
            "Empfohlen: 55-65.\n"
            "Wird intern auf 0-1 skaliert (z.B. 60 -> 0.60)."
        )
        pattern_layout.addRow("Min Score:", self.parent.min_score_spin)

        # Use Pattern
        self.parent.use_pattern_cb = QCheckBox("Pattern-Check aktivieren")
        self.parent.use_pattern_cb.setChecked(False)
        self.parent.use_pattern_cb.setToolTip(
            "Validiert Signale mit der Pattern-Datenbank (Qdrant) vor Entry"
        )
        pattern_layout.addRow("Pattern:", self.parent.use_pattern_cb)

        # Pattern Similarity
        self.parent.pattern_similarity_spin = QDoubleSpinBox()
        self.parent.pattern_similarity_spin.setRange(0.1, 1.0)
        self.parent.pattern_similarity_spin.setSingleStep(0.05)
        self.parent.pattern_similarity_spin.setValue(0.70)
        self.parent.pattern_similarity_spin.setDecimals(2)
        self.parent.pattern_similarity_spin.setToolTip(
            "Mindest-Similarity (0-1) damit ein Treffer berücksichtigt wird"
        )
        pattern_layout.addRow("Min Similarity:", self.parent.pattern_similarity_spin)

        # Pattern Matches
        self.parent.pattern_matches_spin = QSpinBox()
        self.parent.pattern_matches_spin.setRange(1, 200)
        self.parent.pattern_matches_spin.setValue(5)
        self.parent.pattern_matches_spin.setToolTip("Mindestens benötigte Treffer (ähnliche Muster)")
        pattern_layout.addRow("Min Matches:", self.parent.pattern_matches_spin)

        # Pattern Win-Rate
        self.parent.pattern_winrate_spin = QSpinBox()
        self.parent.pattern_winrate_spin.setRange(0, 100)
        self.parent.pattern_winrate_spin.setValue(55)
        self.parent.pattern_winrate_spin.setToolTip(
            "Minimale historische Win-Rate der Treffer (0-100)"
        )
        pattern_layout.addRow("Min Win-Rate:", self.parent.pattern_winrate_spin)

        return pattern_group

    def build_display_group(self) -> QGroupBox:
        """Create chart display options group."""
        display_group = QGroupBox("Chart Display")
        display_layout = QHBoxLayout()
        display_layout.setContentsMargins(8, 8, 8, 8)

        self.parent.show_entry_markers_cb = QCheckBox("Entry Markers")
        self.parent.show_entry_markers_cb.setChecked(True)
        self.parent.show_entry_markers_cb.stateChanged.connect(
            self.parent._on_display_option_changed
        )
        display_layout.addWidget(self.parent.show_entry_markers_cb)

        self.parent.show_stop_lines_cb = QCheckBox("Stop Lines")
        self.parent.show_stop_lines_cb.setChecked(True)
        self.parent.show_stop_lines_cb.stateChanged.connect(
            self.parent._on_display_option_changed
        )
        display_layout.addWidget(self.parent.show_stop_lines_cb)

        self.parent.show_debug_hud_cb = QCheckBox("Debug HUD")
        self.parent.show_debug_hud_cb.setChecked(False)
        self.parent.show_debug_hud_cb.stateChanged.connect(self.parent._on_debug_hud_changed)
        display_layout.addWidget(self.parent.show_debug_hud_cb)

        display_group.setLayout(display_layout)
        return display_group

    def build_help_button(self) -> QPushButton:
        """Create help button."""
        help_btn = QPushButton("Trading-Bot Hilfe")
        help_btn.setStyleSheet("padding: 8px; font-size: 12px;")
        help_btn.setToolTip("Oeffnet die ausfuehrliche Dokumentation zum Trading-Bot")
        help_btn.clicked.connect(self.parent._on_open_help_clicked)
        return help_btn
