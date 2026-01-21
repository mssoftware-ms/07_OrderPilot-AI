"""Backtest Tab UI - Toolbar Builder Module.

Creates the compact button toolbar with status display, progress bar,
and all action buttons (Start, Stop, Load Config, Templates, etc.).

Module 1/4 of backtest_tab_ui.py split.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from PyQt6.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QProgressBar,
    QFrame,
)

if TYPE_CHECKING:
    from PyQt6.QtWidgets import QWidget

logger = logging.getLogger(__name__)


class BacktestTabUIToolbar:
    """Toolbar builder for backtest tab.

    Creates compact button rows with status display, progress bar,
    and all action buttons.
    """

    def __init__(self, parent: QWidget):
        """
        Args:
            parent: BacktestTab Widget
        """
        self.parent = parent

    def create_compact_button_row(self) -> QVBoxLayout:
        """Erstellt kompakte Button-Zeilen (2 Reihen für bessere Sichtbarkeit)."""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(2)

        # === ZEILE 1: Status + Hauptaktionen ===
        row1 = QHBoxLayout()
        row1.setSpacing(6)

        # Status Icon + Label
        self.parent.status_icon = QLabel("🧪")
        row1.addWidget(self.parent.status_icon)

        self.parent.status_label = QLabel("IDLE")
        row1.addWidget(self.parent.status_label)

        # Progress Bar
        self.parent.progress_bar = QProgressBar()
        self.parent.progress_bar.setRange(0, 100)
        self.parent.progress_bar.setValue(0)
        self.parent.progress_bar.setFixedWidth(100)
        self.parent.progress_bar.setFixedHeight(20)
        self.parent.progress_bar.setTextVisible(True)
        # Theme handles styling
        row1.addWidget(self.parent.progress_bar)

        row1.addSpacing(8)

        # === START BUTTON (grün, prominent) ===
        self.parent.start_btn = QPushButton("▶ Start Backtest")
        self.parent.start_btn.setMinimumWidth(110)
        self.parent.start_btn.setProperty("class", "success")
        self.parent.start_btn.clicked.connect(self.parent._on_start_clicked)
        row1.addWidget(self.parent.start_btn)

        # Stop Button
        self.parent.stop_btn = QPushButton("⏹ Stop")
        self.parent.stop_btn.setMinimumWidth(60)
        self.parent.stop_btn.setProperty("class", "danger")
        self.parent.stop_btn.setEnabled(False)
        self.parent.stop_btn.clicked.connect(self.parent._on_stop_clicked)
        row1.addWidget(self.parent.stop_btn)

        row1.addStretch()

        # Status Detail
        self.parent.status_detail = QLabel("Bereit")
        row1.addWidget(self.parent.status_detail)

        main_layout.addLayout(row1)

        # === ZEILE 2: Config + Tools ===
        row2 = QHBoxLayout()
        row2.setSpacing(6)

        # Load Engine Configs Button (GRÖSSER)
        self.parent.load_config_btn = QPushButton("📥 Engine Configs laden")
        self.parent.load_config_btn.setMinimumWidth(140)
        self.parent.load_config_btn.setProperty("class", "primary")
        self.parent.load_config_btn.setToolTip("Lädt alle Engine-Konfigurationen in die Config-Tabelle")
        row2.addWidget(self.parent.load_config_btn)

        # Auto-Generate Button
        self.parent.auto_gen_btn = QPushButton("🤖 Auto-Generate")
        self.parent.auto_gen_btn.setMinimumWidth(110)
        self.parent.auto_gen_btn.setProperty("class", "info")
        self.parent.auto_gen_btn.setToolTip("Generiert automatisch Test-Varianten")
        row2.addWidget(self.parent.auto_gen_btn)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        row2.addWidget(sep)

        # Template Buttons
        self.parent.save_template_btn = QPushButton("💾 Save")
        self.parent.save_template_btn.setMinimumWidth(60)
        self.parent.save_template_btn.setToolTip("Template speichern")
        self.parent.save_template_btn.setProperty("class", "success small-button")
        row2.addWidget(self.parent.save_template_btn)

        self.parent.load_template_btn = QPushButton("📂 Load")
        self.parent.load_template_btn.setMinimumWidth(60)
        self.parent.load_template_btn.setToolTip("Template laden")
        self.parent.load_template_btn.setProperty("class", "warning small-button")
        row2.addWidget(self.parent.load_template_btn)

        self.parent.derive_variant_btn = QPushButton("📝 Variant")
        self.parent.derive_variant_btn.setMinimumWidth(65)
        self.parent.derive_variant_btn.setToolTip("Variante ableiten")
        self.parent.derive_variant_btn.setProperty("class", "info small-button")
        row2.addWidget(self.parent.derive_variant_btn)

        row2.addStretch()

        main_layout.addLayout(row2)

        return main_layout
