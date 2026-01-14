"""Settings Tabs - Heatmap Configuration.

Contains the Heatmap settings tab for configuring the
Binance Liquidation Heatmap feature.
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)


class SettingsTabsHeatmap:
    """Helper for Heatmap Settings Tab."""

    def __init__(self, parent):
        """Initialize helper.

        Args:
            parent: SettingsDialog instance
        """
        self.parent = parent

    def create_heatmap_tab(self) -> QWidget:
        """Create heatmap settings tab.

        Returns:
            QWidget: Heatmap configuration tab
        """
        tab = QWidget()
        main_layout = QVBoxLayout(tab)

        # Enable/Disable Section
        enable_group = QGroupBox("Heatmap Status")
        enable_layout = QVBoxLayout()

        self.parent.heatmap_enabled_check = QCheckBox("Enable Liquidation Heatmap")
        self.parent.heatmap_enabled_check.setToolTip(
            "Enable/disable heatmap rendering. Background data collection always runs."
        )
        enable_layout.addWidget(self.parent.heatmap_enabled_check)

        info_label = QLabel(
            "ℹ️ Displays BTCUSDT liquidation data from Binance as a background heatmap.\n"
            "Data collection runs continuously in the background."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #999; font-size: 11px;")
        enable_layout.addWidget(info_label)

        enable_group.setLayout(enable_layout)
        main_layout.addWidget(enable_group)

        # Data Window Section
        window_group = QGroupBox("Time Window")
        window_layout = QFormLayout()

        self.parent.heatmap_window_combo = QComboBox()
        self.parent.heatmap_window_combo.addItems(["2h", "8h", "2d"])
        self.parent.heatmap_window_combo.setToolTip(
            "Historical time window to display (2 hours, 8 hours, or 2 days)"
        )
        window_layout.addRow("Data Window:", self.parent.heatmap_window_combo)

        window_group.setLayout(window_layout)
        main_layout.addWidget(window_group)

        # Appearance Section
        appearance_group = QGroupBox("Appearance")
        appearance_layout = QFormLayout()

        # Opacity
        opacity_container = QWidget()
        opacity_hlayout = QHBoxLayout(opacity_container)
        opacity_hlayout.setContentsMargins(0, 0, 0, 0)

        self.parent.heatmap_opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.parent.heatmap_opacity_slider.setRange(0, 100)
        self.parent.heatmap_opacity_slider.setValue(50)
        self.parent.heatmap_opacity_slider.setToolTip("Heatmap transparency (0 = invisible, 100 = opaque)")

        self.parent.heatmap_opacity_label = QLabel("50%")
        self.parent.heatmap_opacity_label.setMinimumWidth(40)
        self.parent.heatmap_opacity_slider.valueChanged.connect(
            lambda v: self.parent.heatmap_opacity_label.setText(f"{v}%")
        )

        opacity_hlayout.addWidget(self.parent.heatmap_opacity_slider)
        opacity_hlayout.addWidget(self.parent.heatmap_opacity_label)

        appearance_layout.addRow("Opacity:", opacity_container)

        # Color Palette
        self.parent.heatmap_palette_combo = QComboBox()
        self.parent.heatmap_palette_combo.addItems(["hot", "cool", "viridis", "plasma"])
        self.parent.heatmap_palette_combo.setToolTip("Color scheme for liquidation intensity")
        appearance_layout.addRow("Color Palette:", self.parent.heatmap_palette_combo)

        # Preview button
        preview_btn = QPushButton("Preview Palette")
        preview_btn.clicked.connect(self._show_palette_preview)
        appearance_layout.addRow("", preview_btn)

        appearance_group.setLayout(appearance_layout)
        main_layout.addWidget(appearance_group)

        # Processing Section
        processing_group = QGroupBox("Data Processing")
        processing_layout = QFormLayout()

        # Normalization
        self.parent.heatmap_norm_combo = QComboBox()
        self.parent.heatmap_norm_combo.addItems(["linear", "sqrt", "log", "log10"])
        self.parent.heatmap_norm_combo.setToolTip(
            "Intensity scaling:\n"
            "• linear: Raw values\n"
            "• sqrt: Square root (recommended)\n"
            "• log: Natural logarithm\n"
            "• log10: Base-10 logarithm"
        )
        processing_layout.addRow("Normalization:", self.parent.heatmap_norm_combo)

        # Decay
        self.parent.heatmap_decay_combo = QComboBox()
        self.parent.heatmap_decay_combo.addItems(["Off", "20 minutes", "60 minutes", "6 hours"])
        self.parent.heatmap_decay_combo.setToolTip(
            "Time decay for older liquidations (fades out over time)"
        )
        processing_layout.addRow("Time Decay:", self.parent.heatmap_decay_combo)

        processing_group.setLayout(processing_layout)
        main_layout.addWidget(processing_group)

        # Resolution Section
        resolution_group = QGroupBox("Grid Resolution")
        resolution_layout = QVBoxLayout()

        self.parent.heatmap_auto_res_check = QCheckBox("Auto Resolution (Recommended)")
        self.parent.heatmap_auto_res_check.setChecked(True)
        self.parent.heatmap_auto_res_check.setToolTip(
            "Automatically calculate optimal grid resolution based on window size"
        )
        self.parent.heatmap_auto_res_check.toggled.connect(self._toggle_manual_resolution)
        resolution_layout.addWidget(self.parent.heatmap_auto_res_check)

        # Manual resolution controls
        manual_widget = QWidget()
        manual_layout = QFormLayout(manual_widget)

        self.parent.heatmap_rows_spin = QSpinBox()
        self.parent.heatmap_rows_spin.setRange(50, 1000)
        self.parent.heatmap_rows_spin.setValue(280)
        self.parent.heatmap_rows_spin.setToolTip("Number of price bins (rows)")
        manual_layout.addRow("Rows (Price Bins):", self.parent.heatmap_rows_spin)

        self.parent.heatmap_cols_spin = QSpinBox()
        self.parent.heatmap_cols_spin.setRange(100, 5000)
        self.parent.heatmap_cols_spin.setValue(1200)
        self.parent.heatmap_cols_spin.setToolTip("Number of time bins (columns)")
        manual_layout.addRow("Cols (Time Bins):", self.parent.heatmap_cols_spin)

        self.parent.heatmap_manual_res_widget = manual_widget
        resolution_layout.addWidget(manual_widget)

        # Initially disable manual controls
        manual_widget.setEnabled(False)

        resolution_group.setLayout(resolution_layout)
        main_layout.addWidget(resolution_group)

        # Statistics Section
        stats_group = QGroupBox("Statistics")
        stats_layout = QVBoxLayout()

        self.parent.heatmap_stats_label = QLabel("No data available")
        self.parent.heatmap_stats_label.setWordWrap(True)
        self.parent.heatmap_stats_label.setStyleSheet("font-family: monospace; font-size: 10px;")
        stats_layout.addWidget(self.parent.heatmap_stats_label)

        refresh_stats_btn = QPushButton("Refresh Statistics")
        refresh_stats_btn.clicked.connect(self._refresh_heatmap_stats)
        stats_layout.addWidget(refresh_stats_btn)

        stats_group.setLayout(stats_layout)
        main_layout.addWidget(stats_group)

        # Spacer
        main_layout.addStretch()

        return tab

    def _toggle_manual_resolution(self, checked: bool) -> None:
        """Toggle manual resolution controls.

        Args:
            checked: True if auto resolution is enabled
        """
        if hasattr(self.parent, 'heatmap_manual_res_widget'):
            self.parent.heatmap_manual_res_widget.setEnabled(not checked)

    def _show_palette_preview(self) -> None:
        """Show preview of selected color palette."""
        from PyQt6.QtWidgets import QMessageBox

        palette = self.parent.heatmap_palette_combo.currentText()

        palette_info = {
            "hot": "🔥 Hot: Black → Red → Orange → Yellow (high intensity = bright)",
            "cool": "❄️ Cool: Blue → Cyan → Green (high intensity = warm)",
            "viridis": "🌈 Viridis: Purple → Green → Yellow (perceptually uniform)",
            "plasma": "🔮 Plasma: Dark blue → Purple → Orange → Yellow",
        }

        info = palette_info.get(palette, "Unknown palette")

        QMessageBox.information(
            self.parent,
            f"Palette: {palette.capitalize()}",
            info
        )

    def _refresh_heatmap_stats(self) -> None:
        """Refresh heatmap statistics display."""
        try:
            # Try to get stats from main window's chart widget
            if hasattr(self.parent, 'parent') and self.parent.parent():
                main_window = self.parent.parent()
                if hasattr(main_window, 'chart_widget'):
                    stats = main_window.chart_widget.get_heatmap_stats()
                    if stats:
                        self._update_stats_display(stats)
                        return

            # No stats available
            self.parent.heatmap_stats_label.setText(
                "⚠️ Heatmap not initialized or no data available"
            )

        except Exception as e:
            self.parent.heatmap_stats_label.setText(f"❌ Error: {e}")

    def _update_stats_display(self, stats: dict) -> None:
        """Update statistics label with formatted data.

        Args:
            stats: Statistics dictionary from HeatmapService
        """
        try:
            lines = []
            lines.append(f"📊 Heatmap Statistics")
            lines.append(f"─" * 40)

            if 'total_events' in stats:
                lines.append(f"Total Events: {stats['total_events']:,}")

            if 'db_size_mb' in stats:
                lines.append(f"Database Size: {stats['db_size_mb']:.2f} MB")

            if 'oldest_event' in stats:
                lines.append(f"Oldest Event: {stats['oldest_event']}")

            if 'newest_event' in stats:
                lines.append(f"Newest Event: {stats['newest_event']}")

            if 'grid_cells' in stats:
                lines.append(f"Grid Cells: {stats['grid_cells']:,}")

            if 'active_cells' in stats:
                lines.append(f"Active Cells: {stats['active_cells']:,}")

            if 'ws_connected' in stats:
                status = "✅ Connected" if stats['ws_connected'] else "❌ Disconnected"
                lines.append(f"WebSocket: {status}")

            self.parent.heatmap_stats_label.setText("\n".join(lines))

        except Exception as e:
            self.parent.heatmap_stats_label.setText(f"❌ Error formatting stats: {e}")

    def load_heatmap_settings(self) -> None:
        """Load heatmap settings from QSettings."""
        settings = self.parent.settings

        # Load and apply settings
        enabled = settings.value("heatmap/enabled", False, type=bool)
        self.parent.heatmap_enabled_check.setChecked(enabled)

        window = settings.value("heatmap/window", "2h", type=str)
        idx = self.parent.heatmap_window_combo.findText(window)
        if idx >= 0:
            self.parent.heatmap_window_combo.setCurrentIndex(idx)

        opacity = settings.value("heatmap/opacity", 0.5, type=float)
        self.parent.heatmap_opacity_slider.setValue(int(opacity * 100))

        palette = settings.value("heatmap/palette", "hot", type=str)
        idx = self.parent.heatmap_palette_combo.findText(palette)
        if idx >= 0:
            self.parent.heatmap_palette_combo.setCurrentIndex(idx)

        norm = settings.value("heatmap/normalization", "sqrt", type=str)
        idx = self.parent.heatmap_norm_combo.findText(norm)
        if idx >= 0:
            self.parent.heatmap_norm_combo.setCurrentIndex(idx)

        decay_minutes = settings.value("heatmap/decay_minutes", 0, type=int)
        decay_map = {0: "Off", 20: "20 minutes", 60: "60 minutes", 360: "6 hours"}
        decay_text = decay_map.get(decay_minutes, "Off")
        idx = self.parent.heatmap_decay_combo.findText(decay_text)
        if idx >= 0:
            self.parent.heatmap_decay_combo.setCurrentIndex(idx)

        auto_res = settings.value("heatmap/auto_resolution", True, type=bool)
        self.parent.heatmap_auto_res_check.setChecked(auto_res)

        rows = settings.value("heatmap/rows", 280, type=int)
        self.parent.heatmap_rows_spin.setValue(rows)

        cols = settings.value("heatmap/cols", 1200, type=int)
        self.parent.heatmap_cols_spin.setValue(cols)

    def save_heatmap_settings(self) -> None:
        """Save heatmap settings to QSettings."""
        settings = self.parent.settings

        # Save all settings
        settings.setValue("heatmap/enabled", self.parent.heatmap_enabled_check.isChecked())
        settings.setValue("heatmap/window", self.parent.heatmap_window_combo.currentText())

        opacity = self.parent.heatmap_opacity_slider.value() / 100.0
        settings.setValue("heatmap/opacity", opacity)

        settings.setValue("heatmap/palette", self.parent.heatmap_palette_combo.currentText())
        settings.setValue("heatmap/normalization", self.parent.heatmap_norm_combo.currentText())

        # Map decay text back to minutes
        decay_text = self.parent.heatmap_decay_combo.currentText()
        decay_map = {"Off": 0, "20 minutes": 20, "60 minutes": 60, "6 hours": 360}
        decay_minutes = decay_map.get(decay_text, 0)
        settings.setValue("heatmap/decay_minutes", decay_minutes)

        settings.setValue("heatmap/auto_resolution", self.parent.heatmap_auto_res_check.isChecked())
        settings.setValue("heatmap/rows", self.parent.heatmap_rows_spin.value())
        settings.setValue("heatmap/cols", self.parent.heatmap_cols_spin.value())

        settings.sync()
