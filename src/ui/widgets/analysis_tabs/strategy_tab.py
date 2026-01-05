"""Tab 1: Strategy Selection & Gating."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
    QPushButton, QFrame, QMessageBox
)
from PyQt6.QtCore import Qt
from src.core.analysis.context import AnalysisContext
from src.core.analysis.config_store import AnalysisConfigStore

class StrategyTab(QWidget):
    """UI for selecting strategy and checking regime compatibility."""

    def __init__(self, context: AnalysisContext):
        super().__init__()
        self.context = context
        self.context.regime_changed.connect(self._on_regime_changed)
        self._setup_ui()
        
        # Init defaults
        self._load_strategies()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # 1. Regime Display (Header)
        regime_frame = QFrame()
        regime_frame.setStyleSheet("""
            QFrame {
                background-color: #2a2a2a;
                border-radius: 5px;
                border: 1px solid #444;
            }
        """)
        regime_layout = QHBoxLayout(regime_frame)
        
        self.regime_label = QLabel("Markt-Regime: UNKNOWN")
        self.regime_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #aaa;")
        regime_layout.addWidget(self.regime_label)
        layout.addWidget(regime_frame)

        # 2. Strategy Selection
        strat_layout = QHBoxLayout()
        strat_layout.addWidget(QLabel("Strategie wählen:"))
        
        self.strategy_combo = QComboBox()
        self.strategy_combo.currentIndexChanged.connect(self._on_strategy_selected)
        strat_layout.addWidget(self.strategy_combo, 1)
        layout.addLayout(strat_layout)

        # 3. Gating Status (Traffic Light)
        self.gating_label = QLabel("⚠️ Bitte Regime analysieren (Tab 0)")
        self.gating_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.gating_label.setStyleSheet("""
            background-color: #333;
            color: #ddd;
            padding: 10px;
            border-radius: 4px;
            font-weight: bold;
        """)
        layout.addWidget(self.gating_label)

        # 4. Description
        self.desc_label = QLabel()
        self.desc_label.setWordWrap(True)
        self.desc_label.setStyleSheet("color: #888; font-style: italic;")
        layout.addWidget(self.desc_label)

        layout.addStretch()

        # 5. Auto-Config Button
        self.auto_config_btn = QPushButton("⚙️ Auto-Konfiguration anwenden")
        self.auto_config_btn.setToolTip("Lädt Standard-Timeframes und Indikatoren für diese Strategie")
        self.auto_config_btn.clicked.connect(self._on_auto_config)
        self.auto_config_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                font-weight: bold;
                padding: 10px;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #1976D2; }
        """)
        layout.addWidget(self.auto_config_btn)

    def _load_strategies(self):
        strategies = AnalysisConfigStore.get_default_strategies()
        for strat in strategies:
            self.strategy_combo.addItem(strat.name, strat)
        
        # Select first by default
        if strategies:
            self._on_strategy_selected(0)

    def _on_strategy_selected(self, index):
        strat = self.strategy_combo.itemData(index)
        if not strat:
            return
            
        self.context.set_strategy(strat.name)
        self.desc_label.setText(strat.description)
        self._update_gating()

    def _on_regime_changed(self, regime: str):
        self.regime_label.setText(f"Markt-Regime: {regime}")
        # Color coding for regime
        color = "#aaa"
        if "TREND" in regime: color = "#4CAF50" # Green
        elif "RANGE" in regime: color = "#FFC107" # Amber
        elif "HIGH_VOL" in regime: color = "#F44336" # Red
        
        self.regime_label.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {color};")
        self._update_gating()

    def _update_gating(self):
        regime = self.context.get_regime()
        strat = self.context.get_selected_strategy()
        
        if not strat or regime == "UNKNOWN":
            self.gating_label.setText("⚠️ Warte auf Analyse aus Tab 0...")
            self.gating_label.setStyleSheet("background-color: #333; color: #ddd; padding: 10px; border-radius: 4px;")
            return

        allowed = strat.allowed_regimes
        # Simple permissive check (substring match)
        # e.g. regime="TREND_BULL", allowed=["TREND_BULL", ...]
        
        is_compatible = regime in allowed
        
        if is_compatible:
            self.gating_label.setText(f"✅ Strategie '{strat.name}' ist für '{regime}' geeignet.")
            self.gating_label.setStyleSheet("background-color: #1b5e20; color: #fff; padding: 10px; border-radius: 4px; font-weight: bold;")
        else:
            self.gating_label.setText(f"⛔ Strategie '{strat.name}' wird bei '{regime}' NICHT empfohlen!")
            self.gating_label.setStyleSheet("background-color: #b71c1c; color: #fff; padding: 10px; border-radius: 4px; font-weight: bold;")

    def _on_auto_config(self):
        self.context.apply_auto_config()
        QMessageBox.information(self, "Konfiguration", "Standard-Timeframes und Indikatoren wurden geladen.")
