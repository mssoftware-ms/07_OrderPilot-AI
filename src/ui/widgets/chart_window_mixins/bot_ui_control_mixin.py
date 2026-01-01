from __future__ import annotations

import logging
from pathlib import Path

from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import QCheckBox, QComboBox, QDoubleSpinBox, QFormLayout, QGroupBox, QHBoxLayout, QLabel, QPushButton, QSpinBox, QVBoxLayout, QWidget

logger = logging.getLogger(__name__)

class BotUIControlMixin:
    """BotUIControlMixin extracted from BotUIPanelsMixin."""
    def _create_bot_control_tab(self) -> QWidget:
        """Create bot control tab with start/stop and settings."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # ==================== CONTROL GROUP (full width at top) ====================
        control_group = QGroupBox("Bot Control")
        control_layout = QHBoxLayout()
        control_layout.setContentsMargins(8, 8, 8, 8)

        # Status indicator
        self.bot_status_label = QLabel("Status: STOPPED")
        self.bot_status_label.setStyleSheet(
            "font-weight: bold; color: #9e9e9e; font-size: 14px;"
        )
        control_layout.addWidget(self.bot_status_label)
        control_layout.addStretch()

        # Start/Stop buttons inline
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
        layout.addWidget(control_group)

        # ==================== SETTINGS GROUP ====================
        settings_group = QGroupBox("Bot Settings")
        settings_layout = QFormLayout()

        # Symbol (read from chart)
        self.bot_symbol_label = QLabel("-")
        self.bot_symbol_label.setStyleSheet("font-weight: bold; font-size: 13px;")
        settings_layout.addRow("Symbol:", self.bot_symbol_label)

        # KI Mode
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

        # Trailing Mode
        self.trailing_mode_combo = QComboBox()
        self.trailing_mode_combo.addItems(["PCT", "ATR", "SWING"])
        self.trailing_mode_combo.setCurrentIndex(0)
        self.trailing_mode_combo.setToolTip(
            "Trailing Stop Mode:\n"
            "- PCT: Fester Prozent-Abstand vom aktuellen Kurs\n"
            "- ATR: Volatilitaets-basiert (ATR-Multiple), Regime-angepasst\n"
            "- SWING: Bollinger Bands als Support/Resistance"
        )
        self.trailing_mode_combo.currentTextChanged.connect(self._on_trailing_mode_changed)
        settings_layout.addRow("Trailing Mode:", self.trailing_mode_combo)

        # Initial Stop Loss %
        self.initial_sl_spin = QDoubleSpinBox()
        self.initial_sl_spin.setRange(0.1, 10.0)
        self.initial_sl_spin.setValue(2.0)
        self.initial_sl_spin.setSuffix(" %")
        self.initial_sl_spin.setDecimals(2)
        self.initial_sl_spin.setToolTip(
            "Initial Stop-Loss in Prozent vom Entry-Preis.\n"
            "Dies ist der EINZIGE fixe Parameter - alle anderen Exits sind dynamisch.\n"
            "Empfohlen: 1.5-3% fuer Aktien, 2-5% fuer Crypto."
        )
        settings_layout.addRow("Initial SL %:", self.initial_sl_spin)

        # Account capital for bot
        self.bot_capital_spin = QDoubleSpinBox()
        self.bot_capital_spin.setRange(100, 10000000)
        self.bot_capital_spin.setValue(10000)
        self.bot_capital_spin.setPrefix("EUR")
        self.bot_capital_spin.setDecimals(0)
        self.bot_capital_spin.setToolTip(
            "Verfuegbares Kapital fuer den Bot.\n"
            "Basis fuer Positionsgroessen-Berechnung und P&L%."
        )
        settings_layout.addRow("Kapital:", self.bot_capital_spin)

        # Risk per trade %
        self.risk_per_trade_spin = QDoubleSpinBox()
        self.risk_per_trade_spin.setRange(0.1, 100.0)
        self.risk_per_trade_spin.setValue(10.0)
        self.risk_per_trade_spin.setSuffix(" %")
        self.risk_per_trade_spin.setDecimals(2)
        self.risk_per_trade_spin.setToolTip(
            "Prozent des Kapitals, das pro Trade investiert wird.\n"
            "Beispiel: 10.000EUR Kapital x 10% = 1.000EUR pro Trade.\n"
            "P&L% wird auf diesen Betrag berechnet."
        )
        settings_layout.addRow("Risk/Trade %:", self.risk_per_trade_spin)

        # Max daily trades
        self.max_trades_spin = QSpinBox()
        self.max_trades_spin.setRange(1, 50)
        self.max_trades_spin.setValue(10)
        settings_layout.addRow("Max Trades/Day:", self.max_trades_spin)

        # Max daily loss %
        self.max_daily_loss_spin = QDoubleSpinBox()
        self.max_daily_loss_spin.setRange(0.5, 10.0)
        self.max_daily_loss_spin.setValue(3.0)
        self.max_daily_loss_spin.setSuffix(" %")
        self.max_daily_loss_spin.setDecimals(2)
        settings_layout.addRow("Max Daily Loss %:", self.max_daily_loss_spin)

        # Disable restrictions checkbox (for paper trading)
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

        # Disable MACD exit checkbox
        self.disable_macd_exit_cb = QCheckBox("MACD-Exit deaktivieren")
        self.disable_macd_exit_cb.setChecked(False)
        self.disable_macd_exit_cb.setToolTip(
            "Deaktiviert den automatischen Verkauf bei MACD-Kreuzungen.\n"
            "Position wird nur durch Stop-Loss geschlossen.\n"
            "MACD-Signale werden trotzdem im Chart angezeigt."
        )
        settings_layout.addRow("MACD-Exit:", self.disable_macd_exit_cb)

        # Disable RSI Extreme exit checkbox
        self.disable_rsi_exit_cb = QCheckBox("RSI-Extrem-Exit deaktivieren")
        self.disable_rsi_exit_cb.setChecked(False)
        self.disable_rsi_exit_cb.setToolTip(
            "Deaktiviert den automatischen Verkauf bei RSI-Extremwerten.\n"
            "Position wird nur durch Stop-Loss geschlossen.\n"
            "RSI-Extrem-Signale werden trotzdem im Chart angezeigt."
        )
        settings_layout.addRow("RSI-Exit:", self.disable_rsi_exit_cb)

        # Derivathandel checkbox
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

        settings_group.setLayout(settings_layout)

        # ==================== TRAILING STOP SETTINGS ====================
        trailing_group = QGroupBox("Trailing Stop Settings")
        trailing_layout = QFormLayout()

        # Regime-Adaptive checkbox
        self.regime_adaptive_cb = QCheckBox("Regime-Adaptiv")
        self.regime_adaptive_cb.setChecked(True)
        self.regime_adaptive_cb.setToolTip(
            "Passt ATR-Multiplier automatisch an Marktregime an:\n"
            "- Trending (ADX > 25): Engerer Stop (mehr Gewinn mitnehmen)\n"
            "- Ranging (ADX < 20): Weiterer Stop (weniger Whipsaws)"
        )
        self.regime_adaptive_cb.stateChanged.connect(self._on_regime_adaptive_changed)
        trailing_layout.addRow("Adaptive:", self.regime_adaptive_cb)

        # Trailing Activation Threshold
        self.trailing_activation_spin = QDoubleSpinBox()
        self.trailing_activation_spin.setRange(0.0, 100.0)
        self.trailing_activation_spin.setValue(0.0)
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

        # TRA% (New field requested)
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

        # Trailing Stop Distance (PCT mode)
        self.trailing_distance_spin = QDoubleSpinBox()
        self.trailing_distance_spin.setRange(0.1, 10.0)
        self.trailing_distance_spin.setValue(1.5)
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

        # ATR Multiplier (fixed, when not adaptive)
        self.atr_multiplier_spin = QDoubleSpinBox()
        self.atr_multiplier_spin.setRange(0.5, 8.0)
        self.atr_multiplier_spin.setValue(2.5)
        self.atr_multiplier_spin.setSingleStep(0.1)
        self.atr_multiplier_spin.setDecimals(2)
        self.atr_multiplier_spin.setToolTip(
            "Fester ATR-Multiplier (wenn Regime-Adaptiv AUS).\n"
            "Stop = Highest High - (ATR x Multiplier)\n"
            "Hoeher = weiterer Stop, weniger Whipsaws"
        )
        trailing_layout.addRow("ATR Multiplier:", self.atr_multiplier_spin)

        # ATR Trending (for adaptive mode)
        self.atr_trending_spin = QDoubleSpinBox()
        self.atr_trending_spin.setRange(0.5, 5.0)
        self.atr_trending_spin.setValue(2.0)
        self.atr_trending_spin.setSingleStep(0.1)
        self.atr_trending_spin.setDecimals(2)
        self.atr_trending_spin.setToolTip(
            "ATR-Multiplier fuer TRENDING Maerkte (ADX > 25).\n"
            "Niedriger = engerer Stop = mehr Gewinn mitnehmen\n"
            "Empfohlen: 1.5-2.5x"
        )
        trailing_layout.addRow("ATR Trending:", self.atr_trending_spin)

        # ATR Ranging (for adaptive mode)
        self.atr_ranging_spin = QDoubleSpinBox()
        self.atr_ranging_spin.setRange(1.0, 8.0)
        self.atr_ranging_spin.setValue(3.5)
        self.atr_ranging_spin.setSingleStep(0.1)
        self.atr_ranging_spin.setDecimals(2)
        self.atr_ranging_spin.setToolTip(
            "ATR-Multiplier fuer RANGING/CHOPPY Maerkte (ADX < 20).\n"
            "Hoeher = weiterer Stop = weniger Whipsaws\n"
            "Empfohlen: 3.0-4.0x"
        )
        trailing_layout.addRow("ATR Ranging:", self.atr_ranging_spin)

        # Volatility Bonus
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

        # Min Step %
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

        # ==================== SIDE-BY-SIDE LAYOUT FOR SETTINGS ====================
        settings_row = QHBoxLayout()
        settings_row.setSpacing(10)
        settings_row.addWidget(settings_group)
        settings_row.addWidget(trailing_group)
        layout.addLayout(settings_row)

        # ==================== PATTERN VALIDATION (own group, full width) ====================
        pattern_group = QGroupBox("Pattern Validation")
        pattern_layout = QFormLayout(pattern_group)

        self.min_score_spin = QSpinBox()
        self.min_score_spin.setRange(0, 100)
        self.min_score_spin.setValue(60)  # 0-100 integer
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
        self.use_pattern_cb.setToolTip("Validiert Signale mit der Pattern-Datenbank (Qdrant) vor Entry")
        pattern_layout.addRow("Pattern:", self.use_pattern_cb)

        self.pattern_similarity_spin = QDoubleSpinBox()
        self.pattern_similarity_spin.setRange(0.1, 1.0)
        self.pattern_similarity_spin.setSingleStep(0.05)
        self.pattern_similarity_spin.setValue(0.70)
        self.pattern_similarity_spin.setDecimals(2)
        self.pattern_similarity_spin.setToolTip("Mindest-Similarity (0-1) damit ein Treffer berücksichtigt wird")
        pattern_layout.addRow("Min Similarity:", self.pattern_similarity_spin)

        self.pattern_matches_spin = QSpinBox()
        self.pattern_matches_spin.setRange(1, 200)
        self.pattern_matches_spin.setValue(5)
        self.pattern_matches_spin.setToolTip("Mindestens benötigte Treffer (ähnliche Muster)")
        pattern_layout.addRow("Min Matches:", self.pattern_matches_spin)

        self.pattern_winrate_spin = QSpinBox()
        self.pattern_winrate_spin.setRange(0, 100)
        self.pattern_winrate_spin.setValue(55)
        self.pattern_winrate_spin.setToolTip("Minimale historische Win-Rate der Treffer (0-100)")
        pattern_layout.addRow("Min Win-Rate:", self.pattern_winrate_spin)

        layout.addWidget(pattern_group)

        # Update visibility based on trailing mode and regime_adaptive
        self._on_trailing_mode_changed()
        self._on_regime_adaptive_changed()

        # ==================== BOTTOM ROW: DISPLAY + HELP ====================
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(10)

        # Display options (compact)
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
        bottom_row.addWidget(display_group)

        # Help button
        help_btn = QPushButton("Trading-Bot Hilfe")
        help_btn.setStyleSheet("padding: 8px; font-size: 12px;")
        help_btn.setToolTip("Oeffnet die ausfuehrliche Dokumentation zum Trading-Bot")
        help_btn.clicked.connect(self._on_open_help_clicked)
        bottom_row.addWidget(help_btn)

        bottom_row.addStretch()
        layout.addLayout(bottom_row)

        layout.addStretch()
        return widget
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
