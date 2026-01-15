"""
Leverage Settings Widget - Konfiguration für LeverageRulesEngine.

Erlaubt die Anpassung von:
- Asset-Tier Max-Leverage
- Regime-basierte Multiplikatoren
- Liquidation Safety Settings
- Account Risk Limits

Phase 5.3 der Bot-Integration.
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
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
)

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_PATH = Path("config/leverage_rules_config.json")


class LeverageSettingsWidget(QWidget):
    """
    Widget für LeverageRulesEngine-Einstellungen.

    Ermöglicht die Konfiguration aller Leverage-Parameter.

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
        title = QLabel("<h3>Leverage Einstellungen</h3>")
        main_layout.addWidget(title)

        # Warning
        warning = QLabel(
            "⚠️ Höherer Leverage = Höheres Risiko!\n"
            "Diese Einstellungen gelten nur für Paper-Trading."
        )
        warning.setStyleSheet("color: #FF9800; background-color: #FFF3E0; padding: 8px; border-radius: 4px;")
        warning.setWordWrap(True)
        main_layout.addWidget(warning)

        # Asset Tiers Group
        tiers_group = self._create_tiers_group()
        main_layout.addWidget(tiers_group)

        # Regime Modifiers Group
        regime_group = self._create_regime_group()
        main_layout.addWidget(regime_group)

        # Safety Settings Group
        safety_group = self._create_safety_group()
        main_layout.addWidget(safety_group)

        # Account Limits Group
        account_group = self._create_account_group()
        main_layout.addWidget(account_group)

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

    def _create_tiers_group(self) -> QGroupBox:
        """Create asset tier leverage settings."""
        group = QGroupBox("Asset-Tier Max-Leverage")
        layout = QFormLayout(group)

        # Info
        info = QLabel(
            "TIER_1: BTC, ETH | TIER_2: SOL, XRP, etc. | TIER_3: Andere bekannte | TIER_4: Kleine Altcoins"
        )
        info.setStyleSheet("color: #888; font-size: 10px;")
        info.setWordWrap(True)
        layout.addRow(info)

        # Tier 1 (BTC, ETH)
        self._tier1_leverage = QSpinBox()
        self._tier1_leverage.setRange(1, 50)
        self._tier1_leverage.setValue(25)  # Micro-Account: höher für BTC/ETH
        self._tier1_leverage.setSuffix("x")
        self._tier1_leverage.setToolTip("Max Leverage für BTC, ETH")
        layout.addRow("TIER 1 (BTC/ETH):", self._tier1_leverage)

        # Tier 2
        self._tier2_leverage = QSpinBox()
        self._tier2_leverage.setRange(1, 40)
        self._tier2_leverage.setValue(20)  # Micro-Account: höher
        self._tier2_leverage.setSuffix("x")
        self._tier2_leverage.setToolTip("Max Leverage für SOL, XRP, ADA, etc.")
        layout.addRow("TIER 2 (Large Cap):", self._tier2_leverage)

        # Tier 3
        self._tier3_leverage = QSpinBox()
        self._tier3_leverage.setRange(1, 30)
        self._tier3_leverage.setValue(10)
        self._tier3_leverage.setSuffix("x")
        self._tier3_leverage.setToolTip("Max Leverage für andere bekannte Coins")
        layout.addRow("TIER 3 (Mid Cap):", self._tier3_leverage)

        # Tier 4
        self._tier4_leverage = QSpinBox()
        self._tier4_leverage.setRange(1, 20)
        self._tier4_leverage.setValue(5)
        self._tier4_leverage.setSuffix("x")
        self._tier4_leverage.setToolTip("Max Leverage für kleine/unbekannte Coins")
        layout.addRow("TIER 4 (Small Cap):", self._tier4_leverage)

        return group

    def _create_regime_group(self) -> QGroupBox:
        """Create regime-based leverage modifiers."""
        group = QGroupBox("Regime-basierte Anpassung")
        layout = QFormLayout(group)

        # Info
        info = QLabel("Multiplikator auf Max-Leverage basierend auf Markt-Regime:")
        info.setStyleSheet("color: #888; font-size: 10px;")
        layout.addRow(info)

        # Strong Trend
        self._regime_strong_trend = QSpinBox()
        self._regime_strong_trend.setRange(50, 100)
        self._regime_strong_trend.setValue(100)
        self._regime_strong_trend.setSuffix("%")
        self._regime_strong_trend.setToolTip("Leverage bei Strong Trend (aligned)")
        layout.addRow("Strong Trend (aligned):", self._regime_strong_trend)

        # Weak Trend
        self._regime_weak_trend = QSpinBox()
        self._regime_weak_trend.setRange(30, 100)
        self._regime_weak_trend.setValue(75)
        self._regime_weak_trend.setSuffix("%")
        self._regime_weak_trend.setToolTip("Leverage bei Weak Trend")
        layout.addRow("Weak Trend:", self._regime_weak_trend)

        # Neutral
        self._regime_neutral = QSpinBox()
        self._regime_neutral.setRange(30, 100)
        self._regime_neutral.setValue(60)
        self._regime_neutral.setSuffix("%")
        self._regime_neutral.setToolTip("Leverage bei Neutral Regime")
        layout.addRow("Neutral:", self._regime_neutral)

        # Chop/Range
        self._regime_chop = QSpinBox()
        self._regime_chop.setRange(20, 80)
        self._regime_chop.setValue(40)
        self._regime_chop.setSuffix("%")
        self._regime_chop.setToolTip("Leverage bei Chop/Range Markt")
        layout.addRow("Chop/Range:", self._regime_chop)

        # Volatile
        self._regime_volatile = QSpinBox()
        self._regime_volatile.setRange(10, 60)
        self._regime_volatile.setValue(30)
        self._regime_volatile.setSuffix("%")
        self._regime_volatile.setToolTip("Leverage bei hoher Volatilität")
        layout.addRow("Volatile:", self._regime_volatile)

        return group

    def _create_safety_group(self) -> QGroupBox:
        """Create liquidation safety settings."""
        group = QGroupBox("Liquidation Safety")
        layout = QFormLayout(group)

        # Min liquidation distance
        self._min_liq_distance = QDoubleSpinBox()
        self._min_liq_distance.setRange(1.0, 20.0)
        self._min_liq_distance.setValue(5.0)
        self._min_liq_distance.setSingleStep(0.5)
        self._min_liq_distance.setDecimals(1)
        self._min_liq_distance.setSuffix("%")
        self._min_liq_distance.setToolTip(
            "Minimaler Abstand zwischen Entry und Liquidation.\n"
            "Verhindert Trades mit zu engem Liquidationspreis."
        )
        layout.addRow("Min. Liquidation Abstand:", self._min_liq_distance)

        # SL before liquidation
        self._sl_before_liq = QCheckBox("SL muss vor Liquidation liegen")
        self._sl_before_liq.setChecked(True)
        self._sl_before_liq.setToolTip(
            "Stellt sicher, dass Stop Loss ausgelöst wird bevor\n"
            "die Liquidation erreicht wird."
        )
        layout.addRow(self._sl_before_liq)

        # Auto-reduce leverage
        self._auto_reduce = QCheckBox("Automatisch Leverage reduzieren")
        self._auto_reduce.setChecked(True)
        self._auto_reduce.setToolTip(
            "Reduziert Leverage automatisch wenn SL\n"
            "zu nah an Liquidation liegt."
        )
        layout.addRow(self._auto_reduce)

        return group

    def _create_account_group(self) -> QGroupBox:
        """Create account risk limits."""
        group = QGroupBox("Account Risk Limits")
        layout = QFormLayout(group)

        # Max position risk %
        self._max_position_risk = QDoubleSpinBox()
        self._max_position_risk.setRange(0.5, 10.0)
        self._max_position_risk.setValue(3.0)  # Micro-Account: höheres Risiko ok
        self._max_position_risk.setSingleStep(0.5)
        self._max_position_risk.setDecimals(1)
        self._max_position_risk.setSuffix("% Account")
        self._max_position_risk.setToolTip("Max Risiko pro Position (% des Accounts)")
        layout.addRow("Max. Position Risk:", self._max_position_risk)

        # Max daily exposure
        self._max_daily_exposure = QDoubleSpinBox()
        self._max_daily_exposure.setRange(5.0, 100.0)
        self._max_daily_exposure.setValue(50.0)  # Micro-Account: höhere Exposure ok
        self._max_daily_exposure.setSingleStep(5.0)
        self._max_daily_exposure.setDecimals(0)
        self._max_daily_exposure.setSuffix("% Account")
        self._max_daily_exposure.setToolTip("Max kumulative Exposure pro Tag")
        layout.addRow("Max. Daily Exposure:", self._max_daily_exposure)

        # Max concurrent positions
        self._max_positions = QSpinBox()
        self._max_positions.setRange(1, 10)
        self._max_positions.setValue(1)  # Micro-Account: nur eine Position
        self._max_positions.setToolTip("Maximale gleichzeitige Positionen")
        layout.addRow("Max. Positionen:", self._max_positions)

        return group

    def _connect_signals(self) -> None:
        """Connect change signals."""
        spinboxes = [
            self._tier1_leverage, self._tier2_leverage,
            self._tier3_leverage, self._tier4_leverage,
            self._regime_strong_trend, self._regime_weak_trend,
            self._regime_neutral, self._regime_chop, self._regime_volatile,
            self._min_liq_distance,
            self._max_position_risk, self._max_daily_exposure, self._max_positions,
        ]

        for spinbox in spinboxes:
            spinbox.valueChanged.connect(self._emit_settings_changed)

        checkboxes = [
            self._sl_before_liq, self._auto_reduce,
        ]

        for checkbox in checkboxes:
            checkbox.stateChanged.connect(self._emit_settings_changed)

    def _emit_settings_changed(self) -> None:
        """Emit settings changed signal."""
        self.settings_changed.emit(self.get_settings())

    def get_settings(self) -> dict:
        """Get current settings as dict."""
        return {
            "tier_limits": {
                "tier_1": self._tier1_leverage.value(),
                "tier_2": self._tier2_leverage.value(),
                "tier_3": self._tier3_leverage.value(),
                "tier_4": self._tier4_leverage.value(),
            },
            "regime_multipliers": {
                "strong_trend": self._regime_strong_trend.value() / 100.0,
                "weak_trend": self._regime_weak_trend.value() / 100.0,
                "neutral": self._regime_neutral.value() / 100.0,
                "chop": self._regime_chop.value() / 100.0,
                "volatile": self._regime_volatile.value() / 100.0,
            },
            "safety": {
                "min_liquidation_distance_pct": self._min_liq_distance.value(),
                "sl_before_liquidation": self._sl_before_liq.isChecked(),
                "auto_reduce_leverage": self._auto_reduce.isChecked(),
            },
            "account_limits": {
                "max_position_risk_pct": self._max_position_risk.value(),
                "max_daily_exposure_pct": self._max_daily_exposure.value(),
                "max_concurrent_positions": self._max_positions.value(),
            },
        }

    def set_settings(self, settings: dict) -> None:
        """Set settings from dict."""
        if "tier_limits" in settings:
            t = settings["tier_limits"]
            self._tier1_leverage.setValue(t.get("tier_1", 20))
            self._tier2_leverage.setValue(t.get("tier_2", 15))
            self._tier3_leverage.setValue(t.get("tier_3", 10))
            self._tier4_leverage.setValue(t.get("tier_4", 5))

        if "regime_multipliers" in settings:
            r = settings["regime_multipliers"]
            self._regime_strong_trend.setValue(int(r.get("strong_trend", 1.0) * 100))
            self._regime_weak_trend.setValue(int(r.get("weak_trend", 0.75) * 100))
            self._regime_neutral.setValue(int(r.get("neutral", 0.60) * 100))
            self._regime_chop.setValue(int(r.get("chop", 0.40) * 100))
            self._regime_volatile.setValue(int(r.get("volatile", 0.30) * 100))

        if "safety" in settings:
            s = settings["safety"]
            self._min_liq_distance.setValue(s.get("min_liquidation_distance_pct", 5.0))
            self._sl_before_liq.setChecked(s.get("sl_before_liquidation", True))
            self._auto_reduce.setChecked(s.get("auto_reduce_leverage", True))

        if "account_limits" in settings:
            a = settings["account_limits"]
            self._max_position_risk.setValue(a.get("max_position_risk_pct", 2.0))
            self._max_daily_exposure.setValue(a.get("max_daily_exposure_pct", 20.0))
            self._max_positions.setValue(a.get("max_concurrent_positions", 3))

    def _load_settings(self) -> None:
        """Load settings from config file."""
        try:
            if DEFAULT_CONFIG_PATH.exists():
                with open(DEFAULT_CONFIG_PATH, "r") as f:
                    settings = json.load(f)
                self.set_settings(settings)
                logger.info("Leverage settings loaded from config")
        except Exception as e:
            logger.warning(f"Failed to load leverage settings: {e}")

    def _apply_settings(self) -> None:
        """Apply settings to engine."""
        settings = self.get_settings()

        try:
            from src.core.trading_bot import get_leverage_rules_engine

            engine = get_leverage_rules_engine()
            engine.update_config_from_dict(settings)
            logger.info("Leverage settings applied")

            QMessageBox.information(
                self, "Erfolg", "Einstellungen wurden übernommen."
            )
        except Exception as e:
            logger.error(f"Failed to apply leverage settings: {e}")
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
            logger.info(f"Leverage settings saved to {DEFAULT_CONFIG_PATH}")
        except Exception as e:
            logger.error(f"Failed to save leverage settings: {e}")
            QMessageBox.critical(
                self, "Fehler", f"Einstellungen konnten nicht gespeichert werden:\n{e}"
            )

    def _reset_to_defaults(self) -> None:
        """Reset to default settings (Micro-Account optimiert)."""
        defaults = {
            "tier_limits": {"tier_1": 25, "tier_2": 20, "tier_3": 10, "tier_4": 5},  # Micro: höher für BTC/ETH
            "regime_multipliers": {
                "strong_trend": 1.0, "weak_trend": 0.75, "neutral": 0.60,
                "chop": 0.40, "volatile": 0.30,
            },
            "safety": {
                "min_liquidation_distance_pct": 5.0,
                "sl_before_liquidation": True,
                "auto_reduce_leverage": True,
            },
            "account_limits": {
                "max_position_risk_pct": 3.0,  # Micro: höheres Risiko ok
                "max_daily_exposure_pct": 50.0,  # Micro: höhere Exposure ok
                "max_concurrent_positions": 1,  # Micro: nur eine Position
            },
        }
        self.set_settings(defaults)
        self._emit_settings_changed()
        logger.info("Leverage settings reset to defaults")
