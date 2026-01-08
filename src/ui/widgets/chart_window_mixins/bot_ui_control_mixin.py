from __future__ import annotations

import logging
from pathlib import Path

from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import QCheckBox, QComboBox, QDoubleSpinBox, QFormLayout, QGroupBox, QHBoxLayout, QLabel, QPushButton, QSlider, QSpinBox, QVBoxLayout, QWidget, QMessageBox, QFileDialog
from PyQt6.QtCore import Qt
import json
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

class BotUIControlMixin:
    """BotUIControlMixin extracted from BotUIPanelsMixin."""
    def _create_bot_control_tab(self) -> QWidget:
        """Create bot control tab with start/stop and settings."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        layout.addWidget(self._build_control_group())
        settings_row = QHBoxLayout()
        settings_row.setSpacing(10)
        settings_row.addWidget(self._build_settings_group())
        settings_row.addWidget(self._build_trailing_group())
        layout.addLayout(settings_row)

        layout.addWidget(self._build_pattern_group())

        self._on_trailing_mode_changed()
        self._on_regime_adaptive_changed()

        layout.addLayout(self._build_bottom_row())
        layout.addStretch()
        return widget

    def _build_control_group(self) -> QGroupBox:
        control_group = QGroupBox("Bot Control")
        control_layout = QHBoxLayout()
        control_layout.setContentsMargins(8, 8, 8, 8)

        self.bot_status_label = QLabel("Status: STOPPED")
        self.bot_status_label.setStyleSheet(
            "font-weight: bold; color: #9e9e9e; font-size: 14px;"
        )
        control_layout.addWidget(self.bot_status_label)
        control_layout.addStretch()

        self.bot_start_btn = QPushButton("Start Bot")
        self.bot_start_btn.setStyleSheet(
            "background-color: #26a69a; color: white; font-weight: bold; "
            "padding: 8px 16px;"
        )
        self.bot_start_btn.clicked.connect(self._on_bot_start_clicked)
        control_layout.addWidget(self.bot_start_btn)

        self.bot_stop_btn = QPushButton("Stop Bot")
        self.bot_stop_btn.setStyleSheet(
            "background-color: #ef5350; color: white; font-weight: bold; "
            "padding: 8px 16px;"
        )
        self.bot_stop_btn.setEnabled(False)
        self.bot_stop_btn.clicked.connect(self._on_bot_stop_clicked)
        control_layout.addWidget(self.bot_stop_btn)

        self.bot_pause_btn = QPushButton("Pause")
        self.bot_pause_btn.setStyleSheet("padding: 8px;")
        self.bot_pause_btn.setEnabled(False)
        self.bot_pause_btn.clicked.connect(self._on_bot_pause_clicked)
        control_layout.addWidget(self.bot_pause_btn)

        control_group.setLayout(control_layout)
        return control_group

    def _build_settings_group(self) -> QGroupBox:
        settings_group = QGroupBox("Bot Settings")
        settings_layout = QFormLayout()

        self.bot_symbol_label = QLabel("-")
        self.bot_symbol_label.setStyleSheet("font-weight: bold; font-size: 13px;")
        settings_layout.addRow("Symbol:", self.bot_symbol_label)

        self.ki_mode_combo = QComboBox()
        self.ki_mode_combo.addItems(["NO_KI", "LOW_KI", "FULL_KI"])
        self.ki_mode_combo.setCurrentIndex(0)
        self.ki_mode_combo.currentTextChanged.connect(self._on_ki_mode_changed)
        self.ki_mode_combo.setToolTip(
            "KI Mode:\n"
            "- NO_KI: Rein regelbasiert, kein LLM-Call\n"
            "- LOW_KI: Daily Strategy Selection (1 Call/Tag)\n"
            "- FULL_KI: Daily + Intraday Events (RegimeFlip, Exit, Signal)"
        )
        settings_layout.addRow("KI Mode:", self.ki_mode_combo)

        # === TRADE DIRECTION / BIAS ===
        self.trade_direction_combo = QComboBox()
        self.trade_direction_combo.addItems(["AUTO", "BOTH", "LONG_ONLY", "SHORT_ONLY"])
        self.trade_direction_combo.setCurrentIndex(0)  # Default: AUTO (durch Backtesting ermittelt)
        self.trade_direction_combo.setToolTip(
            "Trade Direction Bias:\n"
            "- AUTO: Wird durch Backtesting automatisch ermittelt (empfohlen)\n"
            "- BOTH: Long UND Short Trades erlaubt\n"
            "- LONG_ONLY: Nur Long-Positionen (Aufwärtstrend)\n"
            "- SHORT_ONLY: Nur Short-Positionen (Abwärtstrend)\n\n"
            "AUTO analysiert historische Daten und wählt die profitabelste Richtung."
        )
        self.trade_direction_combo.setStyleSheet(
            "QComboBox { font-weight: bold; }"
        )
        self.trade_direction_combo.currentTextChanged.connect(self._on_trade_direction_changed)
        settings_layout.addRow("Trade Richtung:", self.trade_direction_combo)

        self.trailing_mode_combo = QComboBox()
        self.trailing_mode_combo.addItems(["PCT", "ATR", "SWING"])
        self.trailing_mode_combo.setCurrentIndex(1)  # ATR für Micro-Account
        self.trailing_mode_combo.setToolTip(
            "Trailing Stop Mode:\n"
            "- PCT: Fester Prozent-Abstand vom aktuellen Kurs\n"
            "- ATR: Volatilitaets-basiert (ATR-Multiple), Regime-angepasst\n"
            "- SWING: Bollinger Bands als Support/Resistance"
        )
        self.trailing_mode_combo.currentTextChanged.connect(self._on_trailing_mode_changed)
        settings_layout.addRow("Trailing Mode:", self.trailing_mode_combo)

        self.initial_sl_spin = QDoubleSpinBox()
        self.initial_sl_spin.setRange(0.1, 10.0)
        self.initial_sl_spin.setValue(1.5)  # Eng für Micro-Account
        self.initial_sl_spin.setSuffix(" %")
        self.initial_sl_spin.setDecimals(2)
        self.initial_sl_spin.setToolTip(
            "Initial Stop-Loss in Prozent vom Entry-Preis.\n"
            "Dies ist der EINZIGE fixe Parameter - alle anderen Exits sind dynamisch.\n"
            "Empfohlen: 1.5-3% fuer Aktien, 2-5% fuer Crypto."
        )
        settings_layout.addRow("Initial SL %:", self.initial_sl_spin)

        self.bot_capital_spin = QDoubleSpinBox()
        self.bot_capital_spin.setRange(10, 10000000)
        self.bot_capital_spin.setValue(100)  # Default für Micro-Account
        self.bot_capital_spin.setPrefix("€ ")
        self.bot_capital_spin.setDecimals(0)
        self.bot_capital_spin.setToolTip(
            "Verfuegbares Kapital fuer den Bot.\n"
            "Basis fuer Positionsgroessen-Berechnung und P&L%.\n"
            "Bei kleinem Kapital (<500€) ist Hebel oft nötig!"
        )
        settings_layout.addRow("Kapital:", self.bot_capital_spin)

        self.risk_per_trade_spin = QDoubleSpinBox()
        self.risk_per_trade_spin.setRange(0.1, 100.0)
        self.risk_per_trade_spin.setValue(50.0)  # Micro-Account: höherer Risk%
        self.risk_per_trade_spin.setSuffix(" %")
        self.risk_per_trade_spin.setDecimals(2)
        self.risk_per_trade_spin.setToolTip(
            "Prozent des Kapitals, das pro Trade investiert wird.\n"
            "Beispiel: 100EUR Kapital x 50% = 50EUR pro Trade.\n"
            "Bei Micro-Account empfohlen: 30-50% mit engem SL."
        )
        settings_layout.addRow("Risk/Trade %:", self.risk_per_trade_spin)

        self.max_trades_spin = QSpinBox()
        self.max_trades_spin.setRange(1, 50)
        self.max_trades_spin.setValue(10)
        settings_layout.addRow("Max Trades/Day:", self.max_trades_spin)

        self.max_daily_loss_spin = QDoubleSpinBox()
        self.max_daily_loss_spin.setRange(0.5, 10.0)
        self.max_daily_loss_spin.setValue(3.0)
        self.max_daily_loss_spin.setSuffix(" %")
        self.max_daily_loss_spin.setDecimals(2)
        settings_layout.addRow("Max Daily Loss %:", self.max_daily_loss_spin)

        self.disable_restrictions_cb = QCheckBox("Restriktionen deaktivieren")
        self.disable_restrictions_cb.setChecked(True)
        self.disable_restrictions_cb.setToolTip(
            "Deaktiviert Max Trades/Day und Max Daily Loss Limits.\n"
            "Empfohlen fuer Paper Trading und Strategie-Tests.\n"
            "Im Live-Modus sollten Restriktionen AKTIVIERT sein!"
        )
        self.disable_restrictions_cb.setStyleSheet(
            "color: #ff9800; font-weight: bold;"
        )
        settings_layout.addRow("Paper Mode:", self.disable_restrictions_cb)

        self.disable_macd_exit_cb = QCheckBox("MACD-Exit deaktivieren")
        self.disable_macd_exit_cb.setChecked(False)
        self.disable_macd_exit_cb.setToolTip(
            "Deaktiviert den automatischen Verkauf bei MACD-Kreuzungen.\n"
            "Position wird nur durch Stop-Loss geschlossen.\n"
            "MACD-Signale werden trotzdem im Chart angezeigt."
        )
        settings_layout.addRow("MACD-Exit:", self.disable_macd_exit_cb)

        self.disable_rsi_exit_cb = QCheckBox("RSI-Extrem-Exit deaktivieren")
        self.disable_rsi_exit_cb.setChecked(False)
        self.disable_rsi_exit_cb.setToolTip(
            "Deaktiviert den automatischen Verkauf bei RSI-Extremwerten.\n"
            "Position wird nur durch Stop-Loss geschlossen.\n"
            "RSI-Extrem-Signale werden trotzdem im Chart angezeigt."
        )
        settings_layout.addRow("RSI-Exit:", self.disable_rsi_exit_cb)

        self.enable_derivathandel_cb = QCheckBox("Derivathandel aktivieren")
        self.enable_derivathandel_cb.setChecked(False)
        self.enable_derivathandel_cb.setToolTip(
            "Bei aktiviert: Automatische KO-Produkt-Suche bei Signal-Bestaetigung.\n"
            "Das beste Derivat wird basierend auf Score ausgewaehlt.\n"
            "ACHTUNG: KO-Produkte haben hoeheres Risiko (Hebel, Totalverlust)!"
        )
        self.enable_derivathandel_cb.setStyleSheet(
            "color: #ff5722; font-weight: bold;"
        )
        self.enable_derivathandel_cb.stateChanged.connect(self._on_derivathandel_changed)
        settings_layout.addRow("Derivathandel:", self.enable_derivathandel_cb)

        # === LEVERAGE OVERRIDE SECTION ===
        leverage_separator = QLabel("─── Leverage Override ───")
        leverage_separator.setStyleSheet("color: #FF9800; font-weight: bold; margin-top: 10px;")
        settings_layout.addRow(leverage_separator)

        self.leverage_override_cb = QCheckBox("Manueller Hebel aktivieren")
        self.leverage_override_cb.setChecked(True)  # Default ON für Micro-Account
        self.leverage_override_cb.setToolTip(
            "Aktiviert manuelle Hebel-Überschreibung.\n"
            "Überschreibt die automatische Leverage-Berechnung.\n"
            "WICHTIG für Micro-Accounts (<500€)!"
        )
        self.leverage_override_cb.setStyleSheet("color: #FF9800; font-weight: bold;")
        self.leverage_override_cb.stateChanged.connect(self._on_leverage_override_changed)
        settings_layout.addRow("Override:", self.leverage_override_cb)

        # Leverage Slider mit Wert-Anzeige
        leverage_widget = QWidget()
        leverage_layout = QHBoxLayout(leverage_widget)
        leverage_layout.setContentsMargins(0, 0, 0, 0)
        leverage_layout.setSpacing(8)

        self.leverage_slider = QSlider(Qt.Orientation.Horizontal)
        self.leverage_slider.setRange(1, 100)
        self.leverage_slider.setValue(20)  # Default 20x für Micro-Account
        self.leverage_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.leverage_slider.setTickInterval(10)
        self.leverage_slider.setToolTip(
            "Manueller Hebel (1x - 100x).\n"
            "Empfohlen für 100€ Kapital: 15-25x\n"
            "ACHTUNG: Hoher Hebel = hohes Risiko!"
        )
        self.leverage_slider.valueChanged.connect(self._on_leverage_slider_changed)
        leverage_layout.addWidget(self.leverage_slider, stretch=3)

        self.leverage_value_label = QLabel("20x")
        self.leverage_value_label.setStyleSheet(
            "font-weight: bold; font-size: 14px; color: #FF9800; min-width: 50px;"
        )
        leverage_layout.addWidget(self.leverage_value_label)

        settings_layout.addRow("Hebel:", leverage_widget)

        # Quick-Select Buttons für Leverage
        quick_lev_widget = QWidget()
        quick_lev_layout = QHBoxLayout(quick_lev_widget)
        quick_lev_layout.setContentsMargins(0, 0, 0, 0)
        quick_lev_layout.setSpacing(4)

        for lev in [5, 10, 20, 50, 75, 100]:
            btn = QPushButton(f"{lev}x")
            btn.setFixedWidth(40)
            btn.setStyleSheet("padding: 3px; font-size: 10px;")
            btn.clicked.connect(lambda checked, l=lev: self._set_leverage(l))
            quick_lev_layout.addWidget(btn)

        settings_layout.addRow("Schnellwahl:", quick_lev_widget)

        # === SAVE/LOAD DEFAULTS SECTION ===
        defaults_separator = QLabel("─── Einstellungen ───")
        defaults_separator.setStyleSheet("color: #4CAF50; font-weight: bold; margin-top: 10px;")
        settings_layout.addRow(defaults_separator)

        defaults_widget = QWidget()
        defaults_layout = QHBoxLayout(defaults_widget)
        defaults_layout.setContentsMargins(0, 0, 0, 0)
        defaults_layout.setSpacing(8)

        self.save_defaults_btn = QPushButton("💾 Speichern")
        self.save_defaults_btn.setStyleSheet(
            "background-color: #4CAF50; color: white; padding: 4px 8px; font-size: 10px;"
        )
        self.save_defaults_btn.setToolTip("Aktuelle Einstellungen als Standard speichern")
        self.save_defaults_btn.clicked.connect(self._on_save_defaults_clicked)
        defaults_layout.addWidget(self.save_defaults_btn)

        self.load_defaults_btn = QPushButton("📂 Laden")
        self.load_defaults_btn.setStyleSheet(
            "background-color: #2196F3; color: white; padding: 4px 8px; font-size: 10px;"
        )
        self.load_defaults_btn.setToolTip("Gespeicherte Standard-Einstellungen laden")
        self.load_defaults_btn.clicked.connect(self._on_load_defaults_clicked)
        defaults_layout.addWidget(self.load_defaults_btn)

        self.reset_defaults_btn = QPushButton("🔄 Reset")
        self.reset_defaults_btn.setStyleSheet(
            "background-color: #607D8B; color: white; padding: 4px 8px; font-size: 10px;"
        )
        self.reset_defaults_btn.setToolTip("Auf Factory-Defaults zurücksetzen")
        self.reset_defaults_btn.clicked.connect(self._on_reset_defaults_clicked)
        defaults_layout.addWidget(self.reset_defaults_btn)

        settings_layout.addRow("Defaults:", defaults_widget)

        settings_group.setLayout(settings_layout)
        return settings_group

    def _build_trailing_group(self) -> QGroupBox:
        trailing_group = QGroupBox("Trailing Stop Settings")
        trailing_layout = QFormLayout()

        self.regime_adaptive_cb = QCheckBox("Regime-Adaptiv")
        self.regime_adaptive_cb.setChecked(True)
        self.regime_adaptive_cb.setToolTip(
            "Passt ATR-Multiplier automatisch an Marktregime an:\n"
            "- Trending (ADX > 25): Engerer Stop (mehr Gewinn mitnehmen)\n"
            "- Ranging (ADX < 20): Weiterer Stop (weniger Whipsaws)"
        )
        self.regime_adaptive_cb.stateChanged.connect(self._on_regime_adaptive_changed)
        trailing_layout.addRow("Adaptive:", self.regime_adaptive_cb)

        self.trailing_activation_spin = QDoubleSpinBox()
        self.trailing_activation_spin.setRange(0.0, 100.0)
        self.trailing_activation_spin.setValue(5.0)  # Micro-Account: frühe Aktivierung
        self.trailing_activation_spin.setSingleStep(1.0)
        self.trailing_activation_spin.setDecimals(1)
        self.trailing_activation_spin.setSuffix(" %")
        self.trailing_activation_spin.setToolTip(
            "Ab welchem GEWINN (Return on Risk) der Trailing Stop aktiviert wird.\n\n"
            "Beispiel bei 100EUR Risiko:\n"
            "- 0% = sofort wenn im Gewinn\n"
            "- 10% = Trailing erst ab 10EUR Gewinn aktiv\n"
            "- 50% = Trailing erst ab 50EUR Gewinn aktiv\n\n"
            "Bis zur Aktivierung gilt nur der Initial Stop Loss (rot)."
        )
        trailing_layout.addRow("Aktivierung ab:", self.trailing_activation_spin)

        self.tra_percent_spin = QDoubleSpinBox()
        self.tra_percent_spin.setRange(0.0, 10.0)
        self.tra_percent_spin.setValue(0.5)
        self.tra_percent_spin.setSingleStep(0.1)
        self.tra_percent_spin.setDecimals(2)
        self.tra_percent_spin.setSuffix(" %")
        self.tra_percent_spin.setToolTip(
            "Trailing Activation Percent.\n"
            "Wird in die Signals-Tabelle übernommen und steuert,\n"
            "wann der Trailing Stop aktiv wird."
        )
        trailing_layout.addRow("TRA%:", self.tra_percent_spin)

        self.trailing_distance_spin = QDoubleSpinBox()
        self.trailing_distance_spin.setRange(0.1, 10.0)
        self.trailing_distance_spin.setValue(1.0)  # Micro-Account: eng
        self.trailing_distance_spin.setSingleStep(0.1)
        self.trailing_distance_spin.setDecimals(2)
        self.trailing_distance_spin.setSuffix(" %")
        self.trailing_distance_spin.setToolTip(
            "Abstand des Trailing Stops zum AKTUELLEN Kurs in %.\n\n"
            "Beispiel LONG:\n"
            "- Kurs bei 102EUR, Abstand 1.5% -> Stop bei 100.47EUR\n"
            "- Kurs steigt auf 105EUR -> Stop steigt auf 103.43EUR\n\n"
            "Stop bewegt sich NUR in guenstige Richtung!"
        )
        trailing_layout.addRow("Abstand (PCT):", self.trailing_distance_spin)

        self.atr_multiplier_spin = QDoubleSpinBox()
        self.atr_multiplier_spin.setRange(0.5, 8.0)
        self.atr_multiplier_spin.setValue(1.5)  # Micro-Account: eng
        self.atr_multiplier_spin.setSingleStep(0.1)
        self.atr_multiplier_spin.setDecimals(2)
        self.atr_multiplier_spin.setToolTip(
            "Fester ATR-Multiplier (wenn Regime-Adaptiv AUS).\n"
            "Stop = Highest High - (ATR x Multiplier)\n"
            "Hoeher = weiterer Stop, weniger Whipsaws"
        )
        trailing_layout.addRow("ATR Multiplier:", self.atr_multiplier_spin)

        self.atr_trending_spin = QDoubleSpinBox()
        self.atr_trending_spin.setRange(0.5, 5.0)
        self.atr_trending_spin.setValue(1.2)  # Micro-Account: sehr eng bei Trend
        self.atr_trending_spin.setSingleStep(0.1)
        self.atr_trending_spin.setDecimals(2)
        self.atr_trending_spin.setToolTip(
            "ATR-Multiplier fuer TRENDING Maerkte (ADX > 25).\n"
            "Niedriger = engerer Stop = mehr Gewinn mitnehmen\n"
            "Empfohlen: 1.5-2.5x"
        )
        trailing_layout.addRow("ATR Trending:", self.atr_trending_spin)

        self.atr_ranging_spin = QDoubleSpinBox()
        self.atr_ranging_spin.setRange(1.0, 8.0)
        self.atr_ranging_spin.setValue(2.0)  # Micro-Account: moderater bei Range
        self.atr_ranging_spin.setSingleStep(0.1)
        self.atr_ranging_spin.setDecimals(2)
        self.atr_ranging_spin.setToolTip(
            "ATR-Multiplier fuer RANGING/CHOPPY Maerkte (ADX < 20).\n"
            "Hoeher = weiterer Stop = weniger Whipsaws\n"
            "Empfohlen: 3.0-4.0x"
        )
        trailing_layout.addRow("ATR Ranging:", self.atr_ranging_spin)

        self.volatility_bonus_spin = QDoubleSpinBox()
        self.volatility_bonus_spin.setRange(0.0, 2.0)
        self.volatility_bonus_spin.setValue(0.5)
        self.volatility_bonus_spin.setSingleStep(0.1)
        self.volatility_bonus_spin.setDecimals(2)
        self.volatility_bonus_spin.setToolTip(
            "Extra ATR-Multiplier bei hoher Volatilitaet.\n"
            "Wird hinzuaddiert wenn ATR > 2% des Preises.\n"
            "Empfohlen: 0.3-0.5x"
        )
        trailing_layout.addRow("Vol. Bonus:", self.volatility_bonus_spin)

        self.min_step_spin = QDoubleSpinBox()
        self.min_step_spin.setRange(0.05, 2.0)
        self.min_step_spin.setValue(0.3)
        self.min_step_spin.setSingleStep(0.05)
        self.min_step_spin.setSuffix(" %")
        self.min_step_spin.setDecimals(2)
        self.min_step_spin.setToolTip(
            "Mindest-Bewegung fuer Stop-Update.\n"
            "Verhindert zu haeufige kleine Anpassungen.\n"
            "Empfohlen: 0.2-0.5% fuer Crypto"
        )
        trailing_layout.addRow("Min Step:", self.min_step_spin)

        trailing_group.setLayout(trailing_layout)
        return trailing_group

    def _build_pattern_group(self) -> QGroupBox:
        pattern_group = QGroupBox("Pattern Validation")
        pattern_layout = QFormLayout(pattern_group)

        self.min_score_spin = QSpinBox()
        self.min_score_spin.setRange(0, 100)
        self.min_score_spin.setValue(55)  # Micro-Account: niedrigere Schwelle
        self.min_score_spin.setSingleStep(1)
        self.min_score_spin.setToolTip(
            "Minimaler Score (Ganzzahl 0-100) für Trade-Einstieg.\n"
            "0 = immer erlaubt, 100 = nur perfekte Signale.\n"
            "Empfohlen: 55-65.\n"
            "Wird intern auf 0-1 skaliert (z.B. 60 -> 0.60)."
        )
        pattern_layout.addRow("Min Score:", self.min_score_spin)

        self.use_pattern_cb = QCheckBox("Pattern-Check aktivieren")
        self.use_pattern_cb.setChecked(False)
        self.use_pattern_cb.setToolTip(
            "Validiert Signale mit der Pattern-Datenbank (Qdrant) vor Entry"
        )
        pattern_layout.addRow("Pattern:", self.use_pattern_cb)

        self.pattern_similarity_spin = QDoubleSpinBox()
        self.pattern_similarity_spin.setRange(0.1, 1.0)
        self.pattern_similarity_spin.setSingleStep(0.05)
        self.pattern_similarity_spin.setValue(0.70)
        self.pattern_similarity_spin.setDecimals(2)
        self.pattern_similarity_spin.setToolTip(
            "Mindest-Similarity (0-1) damit ein Treffer berücksichtigt wird"
        )
        pattern_layout.addRow("Min Similarity:", self.pattern_similarity_spin)

        self.pattern_matches_spin = QSpinBox()
        self.pattern_matches_spin.setRange(1, 200)
        self.pattern_matches_spin.setValue(5)
        self.pattern_matches_spin.setToolTip("Mindestens benötigte Treffer (ähnliche Muster)")
        pattern_layout.addRow("Min Matches:", self.pattern_matches_spin)

        self.pattern_winrate_spin = QSpinBox()
        self.pattern_winrate_spin.setRange(0, 100)
        self.pattern_winrate_spin.setValue(55)
        self.pattern_winrate_spin.setToolTip(
            "Minimale historische Win-Rate der Treffer (0-100)"
        )
        pattern_layout.addRow("Min Win-Rate:", self.pattern_winrate_spin)
        return pattern_group

    def _build_bottom_row(self) -> QHBoxLayout:
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(10)
        bottom_row.addWidget(self._build_display_group())
        bottom_row.addWidget(self._build_help_button())
        bottom_row.addStretch()
        return bottom_row

    def _build_display_group(self) -> QGroupBox:
        display_group = QGroupBox("Chart Display")
        display_layout = QHBoxLayout()
        display_layout.setContentsMargins(8, 8, 8, 8)

        self.show_entry_markers_cb = QCheckBox("Entry Markers")
        self.show_entry_markers_cb.setChecked(True)
        self.show_entry_markers_cb.stateChanged.connect(self._on_display_option_changed)
        display_layout.addWidget(self.show_entry_markers_cb)

        self.show_stop_lines_cb = QCheckBox("Stop Lines")
        self.show_stop_lines_cb.setChecked(True)
        self.show_stop_lines_cb.stateChanged.connect(self._on_display_option_changed)
        display_layout.addWidget(self.show_stop_lines_cb)

        self.show_debug_hud_cb = QCheckBox("Debug HUD")
        self.show_debug_hud_cb.setChecked(False)
        self.show_debug_hud_cb.stateChanged.connect(self._on_debug_hud_changed)
        display_layout.addWidget(self.show_debug_hud_cb)

        display_group.setLayout(display_layout)
        return display_group

    def _build_help_button(self) -> QPushButton:
        help_btn = QPushButton("Trading-Bot Hilfe")
        help_btn.setStyleSheet("padding: 8px; font-size: 12px;")
        help_btn.setToolTip("Oeffnet die ausfuehrliche Dokumentation zum Trading-Bot")
        help_btn.clicked.connect(self._on_open_help_clicked)
        return help_btn
    def _on_open_help_clicked(self) -> None:
        """Open the trading bot help documentation."""
        try:
            current_file = Path(__file__).resolve()
            project_root = current_file.parent.parent.parent.parent.parent
            help_file = project_root / "Help" / "tradingbot-hilfe.html"

            if help_file.exists():
                url = QUrl.fromLocalFile(str(help_file))
                QDesktopServices.openUrl(url)
                logger.info(f"Opened help file: {help_file}")
            else:
                logger.warning(f"Help file not found: {help_file}")
        except Exception as e:
            logger.error(f"Failed to open help: {e}")

    # =========================================================================
    # LEVERAGE OVERRIDE HANDLERS
    # =========================================================================

    def _on_leverage_override_changed(self, state: int) -> None:
        """Handler für Leverage Override Checkbox."""
        enabled = state == Qt.CheckState.Checked.value
        self.leverage_slider.setEnabled(enabled)

        if enabled:
            self.leverage_value_label.setStyleSheet(
                "font-weight: bold; font-size: 14px; color: #FF9800; min-width: 50px;"
            )
            logger.info(f"Leverage Override aktiviert: {self.leverage_slider.value()}x")
        else:
            self.leverage_value_label.setStyleSheet(
                "font-weight: bold; font-size: 14px; color: #888; min-width: 50px;"
            )
            logger.info("Leverage Override deaktiviert - automatischer Hebel aktiv")

    def _on_leverage_slider_changed(self, value: int) -> None:
        """Handler für Leverage Slider Wertänderung."""
        self.leverage_value_label.setText(f"{value}x")

        # Farbcodierung nach Risiko
        if value <= 10:
            color = "#4CAF50"  # Grün - niedrig
        elif value <= 25:
            color = "#FF9800"  # Orange - mittel
        elif value <= 50:
            color = "#FF5722"  # Dunkel-Orange - hoch
        else:
            color = "#F44336"  # Rot - sehr hoch

        self.leverage_value_label.setStyleSheet(
            f"font-weight: bold; font-size: 14px; color: {color}; min-width: 50px;"
        )

        logger.debug(f"Leverage geändert auf {value}x")

    def _set_leverage(self, value: int) -> None:
        """Setzt den Leverage-Slider auf einen bestimmten Wert."""
        self.leverage_slider.setValue(value)

    def get_leverage_override(self) -> tuple[bool, int]:
        """
        Gibt den aktuellen Leverage Override Status zurück.

        Returns:
            Tuple (override_enabled, leverage_value)
        """
        if hasattr(self, 'leverage_override_cb') and hasattr(self, 'leverage_slider'):
            return (
                self.leverage_override_cb.isChecked(),
                self.leverage_slider.value()
            )
        return (False, 1)

    # =========================================================================
    # SAVE/LOAD DEFAULTS HANDLERS
    # =========================================================================

    def _get_bot_settings(self) -> dict:
        """Sammelt alle Bot-Einstellungen in einem Dict."""
        settings = {
            'meta': {
                'saved_at': datetime.now().isoformat(),
                'version': '1.0',
                'type': 'bot_control_settings',
            },
            'settings': {}
        }

        # Alle SpinBox/DoubleSpinBox/ComboBox/CheckBox Werte sammeln
        widget_map = {
            # Bot Settings
            'ki_mode': ('ki_mode_combo', 'combo'),
            'trade_direction': ('trade_direction_combo', 'combo'),
            'trailing_mode': ('trailing_mode_combo', 'combo'),
            'initial_sl': ('initial_sl_spin', 'double'),
            'capital': ('bot_capital_spin', 'double'),
            'risk_per_trade': ('risk_per_trade_spin', 'double'),
            'max_trades': ('max_trades_spin', 'int'),
            'max_daily_loss': ('max_daily_loss_spin', 'double'),
            'disable_restrictions': ('disable_restrictions_cb', 'check'),
            'disable_macd_exit': ('disable_macd_exit_cb', 'check'),
            'disable_rsi_exit': ('disable_rsi_exit_cb', 'check'),
            'enable_derivathandel': ('enable_derivathandel_cb', 'check'),
            # Leverage Override
            'leverage_override_enabled': ('leverage_override_cb', 'check'),
            'leverage_value': ('leverage_slider', 'slider'),
            # Trailing Settings
            'regime_adaptive': ('regime_adaptive_cb', 'check'),
            'trailing_activation': ('trailing_activation_spin', 'double'),
            'tra_percent': ('tra_percent_spin', 'double'),
            'trailing_distance': ('trailing_distance_spin', 'double'),
            'atr_multiplier': ('atr_multiplier_spin', 'double'),
            'atr_trending': ('atr_trending_spin', 'double'),
            'atr_ranging': ('atr_ranging_spin', 'double'),
            'volatility_bonus': ('volatility_bonus_spin', 'double'),
            'min_step': ('min_step_spin', 'double'),
            # Pattern Validation
            'min_score': ('min_score_spin', 'int'),
            'use_pattern': ('use_pattern_cb', 'check'),
            'pattern_similarity': ('pattern_similarity_spin', 'double'),
            'pattern_matches': ('pattern_matches_spin', 'int'),
            'pattern_winrate': ('pattern_winrate_spin', 'int'),
            # Display
            'show_entry_markers': ('show_entry_markers_cb', 'check'),
            'show_stop_lines': ('show_stop_lines_cb', 'check'),
            'show_debug_hud': ('show_debug_hud_cb', 'check'),
        }

        for key, (widget_name, widget_type) in widget_map.items():
            if hasattr(self, widget_name):
                widget = getattr(self, widget_name)
                try:
                    if widget_type == 'combo':
                        settings['settings'][key] = widget.currentText()
                    elif widget_type == 'check':
                        settings['settings'][key] = widget.isChecked()
                    elif widget_type == 'int':
                        settings['settings'][key] = widget.value()
                    elif widget_type == 'double':
                        settings['settings'][key] = widget.value()
                    elif widget_type == 'slider':
                        settings['settings'][key] = widget.value()
                except Exception as e:
                    logger.warning(f"Could not read {widget_name}: {e}")

        return settings

    def _apply_bot_settings(self, settings: dict) -> None:
        """Wendet gespeicherte Bot-Einstellungen an."""
        data = settings.get('settings', {})

        widget_map = {
            'ki_mode': ('ki_mode_combo', 'combo'),
            'trade_direction': ('trade_direction_combo', 'combo'),
            'trailing_mode': ('trailing_mode_combo', 'combo'),
            'initial_sl': ('initial_sl_spin', 'double'),
            'capital': ('bot_capital_spin', 'double'),
            'risk_per_trade': ('risk_per_trade_spin', 'double'),
            'max_trades': ('max_trades_spin', 'int'),
            'max_daily_loss': ('max_daily_loss_spin', 'double'),
            'disable_restrictions': ('disable_restrictions_cb', 'check'),
            'disable_macd_exit': ('disable_macd_exit_cb', 'check'),
            'disable_rsi_exit': ('disable_rsi_exit_cb', 'check'),
            'enable_derivathandel': ('enable_derivathandel_cb', 'check'),
            'leverage_override_enabled': ('leverage_override_cb', 'check'),
            'leverage_value': ('leverage_slider', 'slider'),
            'regime_adaptive': ('regime_adaptive_cb', 'check'),
            'trailing_activation': ('trailing_activation_spin', 'double'),
            'tra_percent': ('tra_percent_spin', 'double'),
            'trailing_distance': ('trailing_distance_spin', 'double'),
            'atr_multiplier': ('atr_multiplier_spin', 'double'),
            'atr_trending': ('atr_trending_spin', 'double'),
            'atr_ranging': ('atr_ranging_spin', 'double'),
            'volatility_bonus': ('volatility_bonus_spin', 'double'),
            'min_step': ('min_step_spin', 'double'),
            'min_score': ('min_score_spin', 'int'),
            'use_pattern': ('use_pattern_cb', 'check'),
            'pattern_similarity': ('pattern_similarity_spin', 'double'),
            'pattern_matches': ('pattern_matches_spin', 'int'),
            'pattern_winrate': ('pattern_winrate_spin', 'int'),
            'show_entry_markers': ('show_entry_markers_cb', 'check'),
            'show_stop_lines': ('show_stop_lines_cb', 'check'),
            'show_debug_hud': ('show_debug_hud_cb', 'check'),
        }

        for key, (widget_name, widget_type) in widget_map.items():
            if key in data and hasattr(self, widget_name):
                widget = getattr(self, widget_name)
                value = data[key]
                try:
                    if widget_type == 'combo':
                        idx = widget.findText(value)
                        if idx >= 0:
                            widget.setCurrentIndex(idx)
                    elif widget_type == 'check':
                        widget.setChecked(bool(value))
                    elif widget_type in ('int', 'double', 'slider'):
                        widget.setValue(value)
                except Exception as e:
                    logger.warning(f"Could not apply {widget_name}: {e}")

    def _on_save_defaults_clicked(self) -> None:
        """Speichert aktuelle Einstellungen als Standard."""
        try:
            settings = self._get_bot_settings()

            # Default-Speicherort
            config_dir = Path("config/bot_configs")
            config_dir.mkdir(parents=True, exist_ok=True)

            default_file = config_dir / "bot_defaults.json"

            with open(default_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)

            logger.info(f"Bot-Einstellungen gespeichert: {default_file}")
            QMessageBox.information(
                self, "Gespeichert",
                f"Einstellungen wurden als Standard gespeichert.\n\n"
                f"Datei: {default_file}\n"
                f"Parameter: {len(settings['settings'])}"
            )

        except Exception as e:
            logger.exception("Failed to save defaults")
            QMessageBox.critical(self, "Fehler", f"Speichern fehlgeschlagen:\n{e}")

    def _on_load_defaults_clicked(self) -> None:
        """Lädt gespeicherte Standard-Einstellungen."""
        try:
            default_file = Path("config/bot_configs/bot_defaults.json")

            if not default_file.exists():
                QMessageBox.warning(
                    self, "Keine Defaults",
                    "Keine gespeicherten Standard-Einstellungen gefunden.\n\n"
                    "Bitte zuerst 'Speichern' klicken."
                )
                return

            with open(default_file, 'r', encoding='utf-8') as f:
                settings = json.load(f)

            self._apply_bot_settings(settings)

            meta = settings.get('meta', {})
            saved_at = meta.get('saved_at', 'Unbekannt')

            logger.info(f"Bot-Einstellungen geladen: {default_file}")
            QMessageBox.information(
                self, "Geladen",
                f"Standard-Einstellungen wurden geladen.\n\n"
                f"Gespeichert: {saved_at[:19] if len(saved_at) > 19 else saved_at}\n"
                f"Parameter: {len(settings.get('settings', {}))}"
            )

        except Exception as e:
            logger.exception("Failed to load defaults")
            QMessageBox.critical(self, "Fehler", f"Laden fehlgeschlagen:\n{e}")

    def _on_reset_defaults_clicked(self) -> None:
        """Setzt alle Einstellungen auf Factory-Defaults zurück."""
        reply = QMessageBox.question(
            self, "Reset bestätigen",
            "Alle Einstellungen auf Factory-Defaults zurücksetzen?\n\n"
            "Dies setzt die Einstellungen auf optimierte Micro-Account Werte:\n"
            "- Kapital: 100€\n"
            "- Hebel: 20x\n"
            "- Risk/Trade: 50%\n"
            "- Initial SL: 2%\n"
            "- Trailing: ATR-basiert",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        # Factory Defaults für Micro-Account
        factory_defaults = {
            'meta': {'type': 'factory_defaults'},
            'settings': {
                # Bot Settings
                'ki_mode': 'NO_KI',
                'trade_direction': 'AUTO',  # Wird durch Backtesting ermittelt
                'trailing_mode': 'ATR',
                'initial_sl': 2.0,
                'capital': 100,
                'risk_per_trade': 50.0,
                'max_trades': 10,
                'max_daily_loss': 5.0,
                'disable_restrictions': True,
                'disable_macd_exit': True,
                'disable_rsi_exit': True,
                'enable_derivathandel': False,
                # Leverage Override
                'leverage_override_enabled': True,
                'leverage_value': 20,
                # Trailing Settings (optimiert für enge Stops)
                'regime_adaptive': True,
                'trailing_activation': 5.0,  # Trailing ab 5% Gewinn
                'tra_percent': 0.3,
                'trailing_distance': 1.0,  # Eng!
                'atr_multiplier': 1.5,  # Eng!
                'atr_trending': 1.2,  # Sehr eng bei Trend
                'atr_ranging': 2.0,
                'volatility_bonus': 0.3,
                'min_step': 0.2,
                # Pattern Validation
                'min_score': 55,
                'use_pattern': False,
                'pattern_similarity': 0.70,
                'pattern_matches': 5,
                'pattern_winrate': 55,
                # Display
                'show_entry_markers': True,
                'show_stop_lines': True,
                'show_debug_hud': False,
            }
        }

        self._apply_bot_settings(factory_defaults)
        logger.info("Factory-Defaults angewendet")

        QMessageBox.information(
            self, "Reset",
            "Einstellungen wurden auf Micro-Account Factory-Defaults zurückgesetzt."
        )

    # =========================================================================
    # TRADE DIRECTION HANDLER
    # =========================================================================

    def _on_trade_direction_changed(self, direction: str) -> None:
        """Handler für Trade Direction Änderung."""
        # Farbcodierung nach Richtung
        colors = {
            "AUTO": "#9E9E9E",      # Grau - automatisch
            "BOTH": "#2196F3",      # Blau - beide Richtungen
            "LONG_ONLY": "#4CAF50", # Grün - nur Long
            "SHORT_ONLY": "#F44336" # Rot - nur Short
        }
        color = colors.get(direction, "#9E9E9E")
        self.trade_direction_combo.setStyleSheet(
            f"QComboBox {{ font-weight: bold; color: {color}; }}"
        )

        if direction == "AUTO":
            logger.info("Trade Direction: AUTO - wird durch Backtesting ermittelt")
        else:
            logger.info(f"Trade Direction manuell gesetzt: {direction}")

    def get_trade_direction(self) -> str:
        """
        Gibt die aktuelle Trade Direction zurück.

        Returns:
            'AUTO', 'BOTH', 'LONG_ONLY' oder 'SHORT_ONLY'
        """
        if hasattr(self, 'trade_direction_combo'):
            return self.trade_direction_combo.currentText()
        return "BOTH"

    def set_trade_direction_from_backtest(self, direction: str) -> None:
        """
        Setzt die Trade Direction basierend auf Backtesting-Ergebnis.

        Args:
            direction: 'BOTH', 'LONG_ONLY' oder 'SHORT_ONLY'
        """
        if hasattr(self, 'trade_direction_combo'):
            idx = self.trade_direction_combo.findText(direction)
            if idx >= 0:
                self.trade_direction_combo.setCurrentIndex(idx)
                logger.info(f"Trade Direction durch Backtesting gesetzt: {direction}")
