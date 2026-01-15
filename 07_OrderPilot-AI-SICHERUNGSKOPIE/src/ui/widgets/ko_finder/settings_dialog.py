"""
Einstellungs-Dialog für KO-Finder.

Enthält:
- Score-Gewichtungen (Spread, Hebel, KO-Safety, EV)
- Trading-Plan Parameter (SL, TP, Gap-Puffer)
- Anzahl abzurufender Derivate
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from PyQt6.QtCore import QSettings, Qt
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class KOSettingsDialog(QDialog):
    """
    Einstellungs-Dialog für KO-Finder Score-Parameter.
    """

    # Settings Keys
    SETTINGS_PREFIX = "ko_finder/scoring"

    def __init__(self, parent=None) -> None:
        """Initialisiere Dialog."""
        super().__init__(parent)
        self.setWindowTitle("KO-Finder Einstellungen")
        self.setMinimumWidth(400)
        self._init_ui()
        self._load_settings()

    def _init_ui(self) -> None:
        """Erstelle UI-Elemente."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        layout.addWidget(self._build_trading_group())
        layout.addWidget(self._build_weights_group())
        layout.addWidget(self._build_fetch_group())
        layout.addWidget(self._build_button_box())

    def _build_trading_group(self) -> QGroupBox:
        trading_group = QGroupBox("Trading-Plan")
        trading_layout = QFormLayout(trading_group)

        self.sl_spin = QDoubleSpinBox()
        self.sl_spin.setRange(0.1, 10.0)
        self.sl_spin.setValue(1.0)
        self.sl_spin.setSingleStep(0.1)
        self.sl_spin.setDecimals(1)
        self.sl_spin.setSuffix(" %")
        self.sl_spin.setToolTip("Stop-Loss Schwelle in % vom Underlying")
        trading_layout.addRow("Stop-Loss:", self.sl_spin)

        self.tp_spin = QDoubleSpinBox()
        self.tp_spin.setRange(0.1, 20.0)
        self.tp_spin.setValue(2.0)
        self.tp_spin.setSingleStep(0.1)
        self.tp_spin.setDecimals(1)
        self.tp_spin.setSuffix(" %")
        self.tp_spin.setToolTip("Take-Profit Ziel in % vom Underlying")
        trading_layout.addRow("Take-Profit:", self.tp_spin)

        self.gap_spin = QDoubleSpinBox()
        self.gap_spin.setRange(0.1, 5.0)
        self.gap_spin.setValue(0.5)
        self.gap_spin.setSingleStep(0.1)
        self.gap_spin.setDecimals(1)
        self.gap_spin.setSuffix(" %")
        self.gap_spin.setToolTip(
            "Puffer zwischen Stop-Loss und KO-Level\n"
            "(Schutz vor Overnight-Gaps)"
        )
        trading_layout.addRow("Gap-Puffer:", self.gap_spin)
        return trading_group

    def _build_weights_group(self) -> QGroupBox:
        weights_group = QGroupBox("Score-Gewichtungen")
        weights_layout = QFormLayout(weights_group)

        info_label = QLabel("Gewichtungen müssen in Summe 100% ergeben.")
        info_label.setStyleSheet("color: gray; font-size: 10px;")
        weights_layout.addRow(info_label)

        self.w_spread_spin = QSpinBox()
        self.w_spread_spin.setRange(0, 100)
        self.w_spread_spin.setValue(45)
        self.w_spread_spin.setSuffix(" %")
        self.w_spread_spin.setToolTip(
            "Gewichtung der Spread-Effizienz\n"
            "Niedriger Spread = höherer Score"
        )
        self.w_spread_spin.valueChanged.connect(self._on_weight_changed)
        weights_layout.addRow("Spread-Effizienz:", self.w_spread_spin)

        self.w_lev_spin = QSpinBox()
        self.w_lev_spin.setRange(0, 100)
        self.w_lev_spin.setValue(30)
        self.w_lev_spin.setSuffix(" %")
        self.w_lev_spin.setToolTip(
            "Gewichtung des Hebels\n"
            "Logarithmisch saturiert (max ~10x)"
        )
        self.w_lev_spin.valueChanged.connect(self._on_weight_changed)
        weights_layout.addRow("Hebel:", self.w_lev_spin)

        self.w_ko_spin = QSpinBox()
        self.w_ko_spin.setRange(0, 100)
        self.w_ko_spin.setValue(20)
        self.w_ko_spin.setSuffix(" %")
        self.w_ko_spin.setToolTip(
            "Gewichtung der KO-Sicherheit\n"
            "Mehr Puffer zwischen SL und KO = höherer Score"
        )
        self.w_ko_spin.valueChanged.connect(self._on_weight_changed)
        weights_layout.addRow("KO-Sicherheit:", self.w_ko_spin)

        self.w_ev_spin = QSpinBox()
        self.w_ev_spin.setRange(0, 100)
        self.w_ev_spin.setValue(5)
        self.w_ev_spin.setSuffix(" %")
        self.w_ev_spin.setToolTip(
            "Gewichtung des Expected Value\n"
            "Berücksichtigt Spread-Kosten bei SL/TP"
        )
        self.w_ev_spin.valueChanged.connect(self._on_weight_changed)
        weights_layout.addRow("Expected Value:", self.w_ev_spin)

        self.sum_label = QLabel("Summe: 100%")
        self.sum_label.setStyleSheet("font-weight: bold;")
        weights_layout.addRow(self.sum_label)
        return weights_group

    def _build_fetch_group(self) -> QGroupBox:
        fetch_group = QGroupBox("Abruf-Einstellungen")
        fetch_layout = QFormLayout(fetch_group)

        self.top_n_spin = QSpinBox()
        self.top_n_spin.setRange(5, 100)
        self.top_n_spin.setValue(10)
        self.top_n_spin.setToolTip(
            "Anzahl der besten Produkte je Richtung (Long/Short)"
        )
        fetch_layout.addRow("Anzahl Derivate (je Richtung):", self.top_n_spin)
        return fetch_group

    def _build_button_box(self) -> QDialogButtonBox:
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
            | QDialogButtonBox.StandardButton.RestoreDefaults
        )
        button_box.accepted.connect(self._on_save)
        button_box.rejected.connect(self.reject)

        restore_btn = button_box.button(QDialogButtonBox.StandardButton.RestoreDefaults)
        if restore_btn:
            restore_btn.clicked.connect(self._on_restore_defaults)
        return button_box

    def _on_weight_changed(self) -> None:
        """Handler für Gewichtungs-Änderungen."""
        total = (
            self.w_spread_spin.value()
            + self.w_lev_spin.value()
            + self.w_ko_spin.value()
            + self.w_ev_spin.value()
        )

        self.sum_label.setText(f"Summe: {total}%")

        if total == 100:
            self.sum_label.setStyleSheet("font-weight: bold; color: green;")
        else:
            self.sum_label.setStyleSheet("font-weight: bold; color: red;")

    def _load_settings(self) -> None:
        """Lade Einstellungen aus QSettings."""
        settings = QSettings()

        # Trading-Plan
        self.sl_spin.setValue(
            float(settings.value(f"{self.SETTINGS_PREFIX}/dsl", 1.0))
        )
        self.tp_spin.setValue(
            float(settings.value(f"{self.SETTINGS_PREFIX}/dtp", 2.0))
        )
        self.gap_spin.setValue(
            float(settings.value(f"{self.SETTINGS_PREFIX}/dgap", 0.5))
        )

        # Gewichtungen (in % gespeichert)
        self.w_spread_spin.setValue(
            int(settings.value(f"{self.SETTINGS_PREFIX}/w_spread", 45))
        )
        self.w_lev_spin.setValue(
            int(settings.value(f"{self.SETTINGS_PREFIX}/w_lev", 30))
        )
        self.w_ko_spin.setValue(
            int(settings.value(f"{self.SETTINGS_PREFIX}/w_ko", 20))
        )
        self.w_ev_spin.setValue(
            int(settings.value(f"{self.SETTINGS_PREFIX}/w_ev", 5))
        )

        # Abruf
        self.top_n_spin.setValue(
            int(settings.value(f"{self.SETTINGS_PREFIX}/top_n", 10))
        )

        # Summe aktualisieren
        self._on_weight_changed()

    def _on_save(self) -> None:
        """Speichere Einstellungen."""
        # Gewichtungs-Summe prüfen
        total = (
            self.w_spread_spin.value()
            + self.w_lev_spin.value()
            + self.w_ko_spin.value()
            + self.w_ev_spin.value()
        )

        if total != 100:
            from PyQt6.QtWidgets import QMessageBox

            QMessageBox.warning(
                self,
                "Ungültige Gewichtungen",
                f"Die Summe der Gewichtungen muss 100% ergeben.\n"
                f"Aktuelle Summe: {total}%",
            )
            return

        settings = QSettings()

        # Trading-Plan
        settings.setValue(f"{self.SETTINGS_PREFIX}/dsl", self.sl_spin.value())
        settings.setValue(f"{self.SETTINGS_PREFIX}/dtp", self.tp_spin.value())
        settings.setValue(f"{self.SETTINGS_PREFIX}/dgap", self.gap_spin.value())

        # Gewichtungen
        settings.setValue(f"{self.SETTINGS_PREFIX}/w_spread", self.w_spread_spin.value())
        settings.setValue(f"{self.SETTINGS_PREFIX}/w_lev", self.w_lev_spin.value())
        settings.setValue(f"{self.SETTINGS_PREFIX}/w_ko", self.w_ko_spin.value())
        settings.setValue(f"{self.SETTINGS_PREFIX}/w_ev", self.w_ev_spin.value())

        # Abruf
        settings.setValue(f"{self.SETTINGS_PREFIX}/top_n", self.top_n_spin.value())

        logger.info("KO-Finder settings saved")
        self.accept()

    def _on_restore_defaults(self) -> None:
        """Stelle Standardwerte wieder her."""
        # Trading-Plan
        self.sl_spin.setValue(1.0)
        self.tp_spin.setValue(2.0)
        self.gap_spin.setValue(0.5)

        # Gewichtungen
        self.w_spread_spin.setValue(45)
        self.w_lev_spin.setValue(30)
        self.w_ko_spin.setValue(20)
        self.w_ev_spin.setValue(5)

        # Abruf
        self.top_n_spin.setValue(10)

    @staticmethod
    def get_scoring_params():
        """
        Hole ScoringParams aus QSettings.

        Returns:
            ScoringParams mit aktuellen Einstellungen
        """
        from src.derivatives.ko_finder.engine.ranking import ScoringParams

        settings = QSettings()
        prefix = KOSettingsDialog.SETTINGS_PREFIX

        return ScoringParams(
            dsl=float(settings.value(f"{prefix}/dsl", 1.0)) / 100,  # % -> Dezimal
            dtp=float(settings.value(f"{prefix}/dtp", 2.0)) / 100,
            dgap=float(settings.value(f"{prefix}/dgap", 0.5)) / 100,
            w_spread=int(settings.value(f"{prefix}/w_spread", 45)) / 100,  # % -> Dezimal
            w_lev=int(settings.value(f"{prefix}/w_lev", 30)) / 100,
            w_ko=int(settings.value(f"{prefix}/w_ko", 20)) / 100,
            w_ev=int(settings.value(f"{prefix}/w_ev", 5)) / 100,
        )

    @staticmethod
    def get_top_n() -> int:
        """Hole Top-N Einstellung aus QSettings."""
        settings = QSettings()
        return int(settings.value(f"{KOSettingsDialog.SETTINGS_PREFIX}/top_n", 10))
