"""
Filter-Panel für KO-Finder.

Enthält Controls für:
- Min. Hebel
- Max. Spread
- Emittenten-Auswahl
- Top-N
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    from src.derivatives.ko_finder.config import KOFilterConfig
    from src.derivatives.ko_finder.constants import Issuer

logger = logging.getLogger(__name__)


class KOFilterPanel(QWidget):
    """
    Filter-Panel mit Controls für KO-Suche.

    Signals:
        filter_changed: Emittiert wenn Filter geändert werden
        refresh_requested: Emittiert bei Klick auf Aktualisieren
    """

    filter_changed = pyqtSignal()
    refresh_requested = pyqtSignal()

    def __init__(self, parent=None) -> None:
        """Initialisiere Panel."""
        super().__init__(parent)
        self._issuer_checkboxes: dict[str, QCheckBox] = {}
        self._init_ui()
        self._load_scoring_settings()

    def _init_ui(self) -> None:
        """Erstelle UI-Elemente."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)

        # Filter Group
        filter_group = QGroupBox("Filter")
        filter_layout = QFormLayout(filter_group)

        # Min Hebel
        self.min_leverage_spin = QDoubleSpinBox()
        self.min_leverage_spin.setRange(1.0, 100.0)
        self.min_leverage_spin.setValue(5.0)
        self.min_leverage_spin.setSingleStep(0.5)
        self.min_leverage_spin.setDecimals(1)
        self.min_leverage_spin.valueChanged.connect(self._on_filter_changed)
        filter_layout.addRow("Min. Hebel:", self.min_leverage_spin)

        # Max Spread
        self.max_spread_spin = QDoubleSpinBox()
        self.max_spread_spin.setRange(0.1, 10.0)
        self.max_spread_spin.setValue(2.0)
        self.max_spread_spin.setSingleStep(0.1)
        self.max_spread_spin.setDecimals(1)
        self.max_spread_spin.setSuffix(" %")
        self.max_spread_spin.valueChanged.connect(self._on_filter_changed)
        filter_layout.addRow("Max. Spread:", self.max_spread_spin)

        # Min KO-Abstand
        self.min_distance_spin = QDoubleSpinBox()
        self.min_distance_spin.setRange(0.1, 20.0)
        self.min_distance_spin.setValue(0.5)
        self.min_distance_spin.setSingleStep(0.1)
        self.min_distance_spin.setDecimals(1)
        self.min_distance_spin.setSuffix(" %")
        self.min_distance_spin.valueChanged.connect(self._on_filter_changed)
        filter_layout.addRow("Min. KO-Abstand:", self.min_distance_spin)

        # Top-N
        self.top_n_spin = QSpinBox()
        self.top_n_spin.setRange(1, 50)
        self.top_n_spin.setValue(10)
        self.top_n_spin.valueChanged.connect(self._on_filter_changed)
        filter_layout.addRow("Top-N je Richtung:", self.top_n_spin)

        layout.addWidget(filter_group)

        # Emittenten Group
        issuer_group = QGroupBox("Emittenten")
        issuer_layout = QVBoxLayout(issuer_group)

        # Import hier um zirkuläre Imports zu vermeiden
        from src.derivatives.ko_finder.constants import Issuer

        for issuer in Issuer:
            cb = QCheckBox(issuer.display_name)
            cb.setChecked(True)
            cb.stateChanged.connect(self._on_filter_changed)
            self._issuer_checkboxes[issuer.name] = cb
            issuer_layout.addWidget(cb)

        layout.addWidget(issuer_group)

        # Buttons
        button_layout = QHBoxLayout()

        self.refresh_btn = QPushButton("Aktualisieren")
        self.refresh_btn.clicked.connect(self._on_refresh_clicked)
        button_layout.addWidget(self.refresh_btn)

        self.reset_btn = QPushButton("Reset")
        self.reset_btn.clicked.connect(self._on_reset_clicked)
        button_layout.addWidget(self.reset_btn)

        layout.addLayout(button_layout)

        # Settings Button (Zahnrad)
        settings_layout = QHBoxLayout()
        self.settings_btn = QPushButton("Scoring-Einstellungen...")
        self.settings_btn.setToolTip("Score-Gewichtungen und Trading-Plan konfigurieren")
        self.settings_btn.clicked.connect(self._on_settings_clicked)
        settings_layout.addWidget(self.settings_btn)

        layout.addLayout(settings_layout)

        # Stretch am Ende
        layout.addStretch()

    def get_config(self) -> KOFilterConfig:
        """
        Erstelle KOFilterConfig aus aktuellen UI-Werten.

        Returns:
            Aktuelle Filter-Konfiguration
        """
        from src.derivatives.ko_finder.config import KOFilterConfig
        from src.derivatives.ko_finder.constants import Issuer

        # Ausgewählte Emittenten
        selected_issuers = []
        for issuer in Issuer:
            cb = self._issuer_checkboxes.get(issuer.name)
            if cb and cb.isChecked():
                selected_issuers.append(issuer)

        return KOFilterConfig(
            min_leverage=self.min_leverage_spin.value(),
            max_spread_pct=self.max_spread_spin.value(),
            min_ko_distance_pct=self.min_distance_spin.value(),
            top_n=self.top_n_spin.value(),
            issuers=selected_issuers or list(Issuer),  # Alle wenn keiner
        )

    def set_config(self, config: KOFilterConfig) -> None:
        """
        Setze UI-Werte aus Konfiguration.

        Args:
            config: Filter-Konfiguration
        """
        # Signals blockieren während Update
        self.blockSignals(True)

        self.min_leverage_spin.setValue(config.min_leverage)
        self.max_spread_spin.setValue(config.max_spread_pct)
        self.min_distance_spin.setValue(config.min_ko_distance_pct)
        self.top_n_spin.setValue(config.top_n)

        # Emittenten
        from src.derivatives.ko_finder.constants import Issuer

        issuer_values = [i.value for i in config.issuers]
        for issuer in Issuer:
            cb = self._issuer_checkboxes.get(issuer.name)
            if cb:
                cb.setChecked(issuer.value in issuer_values)

        self.blockSignals(False)

    def set_loading(self, loading: bool) -> None:
        """
        Setze Ladezustand.

        Args:
            loading: True wenn am Laden
        """
        self.refresh_btn.setEnabled(not loading)
        self.refresh_btn.setText("Laden..." if loading else "Aktualisieren")

    def _on_filter_changed(self) -> None:
        """Handler für Filter-Änderungen."""
        self.filter_changed.emit()

    def _on_refresh_clicked(self) -> None:
        """Handler für Refresh-Button."""
        self.refresh_requested.emit()

    def _on_reset_clicked(self) -> None:
        """Handler für Reset-Button."""
        from src.derivatives.ko_finder.config import KOFilterConfig

        self.set_config(KOFilterConfig())
        self.filter_changed.emit()

    def _on_settings_clicked(self) -> None:
        """Handler für Settings-Button."""
        from .settings_dialog import KOSettingsDialog

        dialog = KOSettingsDialog(self)
        if dialog.exec():
            # Settings wurden gespeichert - Top-N aktualisieren
            self.top_n_spin.setValue(KOSettingsDialog.get_top_n())
            logger.info("KO-Finder scoring settings updated")

    def _load_scoring_settings(self) -> None:
        """Lade Scoring-Einstellungen (Top-N) aus QSettings."""
        try:
            from .settings_dialog import KOSettingsDialog
            top_n = KOSettingsDialog.get_top_n()
            self.top_n_spin.setValue(top_n)
        except Exception as e:
            logger.debug("Could not load scoring settings: %s", e)
