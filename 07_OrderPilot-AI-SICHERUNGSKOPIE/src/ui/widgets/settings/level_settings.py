"""Level Detection Settings Widget."""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QFormLayout,
    QSpinBox,
    QDoubleSpinBox,
    QGroupBox,
    QCheckBox,
)

from src.core.trading_bot import LevelEngineConfig
import json
from pathlib import Path


class LevelSettingsWidget(QWidget):
    """Settings widget for Level Engine."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.config_file = Path("config/level_engine_config.json")
        self._setup_ui()
        self.load_settings()

    def _setup_ui(self) -> None:
        """Setup UI components."""
        layout = QVBoxLayout(self)

        # Swing Detection
        swing_group = QGroupBox("Swing Detection")
        swing_layout = QFormLayout(swing_group)

        self.swing_lookback = QSpinBox()
        self.swing_lookback.setRange(3, 50)
        self.swing_lookback.setValue(10)
        self.swing_lookback.setToolTip("Bars links/rechts für Swing High/Low")
        swing_layout.addRow("Lookback Bars:", self.swing_lookback)

        self.min_swing_touches = QSpinBox()
        self.min_swing_touches.setRange(1, 10)
        self.min_swing_touches.setValue(2)
        self.min_swing_touches.setToolTip("Min. Touches für valides Level")
        swing_layout.addRow("Min Touches:", self.min_swing_touches)

        layout.addWidget(swing_group)

        # Zone Width
        zone_group = QGroupBox("Zone Width")
        zone_layout = QFormLayout(zone_group)

        self.zone_width_atr = QDoubleSpinBox()
        self.zone_width_atr.setRange(0.1, 2.0)
        self.zone_width_atr.setSingleStep(0.1)
        self.zone_width_atr.setValue(0.3)
        self.zone_width_atr.setToolTip("Zone-Breite als Vielfaches von ATR")
        zone_layout.addRow("ATR Multiplier:", self.zone_width_atr)

        layout.addWidget(zone_group)

        # Clustering
        cluster_group = QGroupBox("Level Clustering")
        cluster_layout = QFormLayout(cluster_group)

        self.cluster_threshold = QDoubleSpinBox()
        self.cluster_threshold.setRange(0.1, 2.0)
        self.cluster_threshold.setSingleStep(0.1)
        self.cluster_threshold.setValue(0.5)
        self.cluster_threshold.setSuffix(" %")
        self.cluster_threshold.setToolTip("Preise innerhalb X% werden geclustert")
        cluster_layout.addRow("Threshold:", self.cluster_threshold)

        self.min_cluster_size = QSpinBox()
        self.min_cluster_size.setRange(2, 10)
        self.min_cluster_size.setValue(3)
        self.min_cluster_size.setToolTip("Minimum Punkte für einen Cluster")
        cluster_layout.addRow("Min Cluster Size:", self.min_cluster_size)

        layout.addWidget(cluster_group)

        # Pivot Points
        pivot_group = QGroupBox("Additional Levels")
        pivot_layout = QFormLayout(pivot_group)

        self.include_pivots = QCheckBox("Include Pivot Points")
        self.include_pivots.setChecked(True)
        pivot_layout.addRow(self.include_pivots)

        self.include_daily = QCheckBox("Include Daily High/Low")
        self.include_daily.setChecked(True)
        pivot_layout.addRow(self.include_daily)

        self.include_weekly = QCheckBox("Include Weekly High/Low")
        self.include_weekly.setChecked(True)
        pivot_layout.addRow(self.include_weekly)

        layout.addWidget(pivot_group)
        layout.addStretch()

    def load_settings(self) -> None:
        """Load settings from config file."""
        # Use defaults from LevelEngineConfig
        config = LevelEngineConfig()

        # Try to load from JSON file
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                config.swing_lookback = data.get("swing_lookback", config.swing_lookback)
                config.min_swing_touches = data.get("min_swing_touches", config.min_swing_touches)
                config.zone_width_atr_mult = data.get("zone_width_atr_mult", config.zone_width_atr_mult)
                config.cluster_threshold_pct = data.get("cluster_threshold_pct", config.cluster_threshold_pct)
                config.min_cluster_size = data.get("min_cluster_size", config.min_cluster_size)
                config.include_pivots = data.get("include_pivots", config.include_pivots)
                config.include_daily_hl = data.get("include_daily_hl", config.include_daily_hl)
                config.include_weekly_hl = data.get("include_weekly_hl", config.include_weekly_hl)
            except Exception:
                pass

        # Set UI values
        self.swing_lookback.setValue(config.swing_lookback)
        self.min_swing_touches.setValue(config.min_swing_touches)
        self.zone_width_atr.setValue(config.zone_width_atr_mult)
        self.cluster_threshold.setValue(config.cluster_threshold_pct)
        self.min_cluster_size.setValue(config.min_cluster_size)
        self.include_pivots.setChecked(config.include_pivots)
        self.include_daily.setChecked(config.include_daily_hl)
        self.include_weekly.setChecked(config.include_weekly_hl)

    def apply_settings(self) -> None:
        """Apply settings."""
        data = {
            "swing_lookback": self.swing_lookback.value(),
            "min_swing_touches": self.min_swing_touches.value(),
            "zone_width_atr_mult": self.zone_width_atr.value(),
            "cluster_threshold_pct": self.cluster_threshold.value(),
            "min_cluster_size": self.min_cluster_size.value(),
            "include_pivots": self.include_pivots.isChecked(),
            "include_daily_hl": self.include_daily.isChecked(),
            "include_weekly_hl": self.include_weekly.isChecked(),
        }

        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w') as f:
            json.dump(data, f, indent=2)

    def save_settings(self) -> None:
        """Save settings to config file."""
        self.apply_settings()
