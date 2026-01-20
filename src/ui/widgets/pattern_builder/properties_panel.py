"""Properties Panel for Pattern Builder - Edit candle OHLC values and properties.

QWidget with form layout for editing selected candle properties.
Bidirectional updates: Canvas selection → Panel update, Panel changes → Canvas update.
"""

from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QFormLayout, QDoubleSpinBox, QComboBox,
    QSpinBox, QPushButton, QLabel, QGroupBox, QVBoxLayout
)
from PyQt6.QtCore import Qt, pyqtSignal

from .candle_item import CandleItem
from ui.windows.cel_editor.theme import TEXT_PRIMARY, ACCENT_TEAL


class PropertiesPanel(QWidget):
    """Properties panel for editing candle OHLC values and type.

    Features:
    - OHLC input fields (QDoubleSpinBox, 0-100 range)
    - Candle type selector (QComboBox with 8 types)
    - Index input (QSpinBox, negative values allowed)
    - Apply Changes button
    - Bidirectional updates with canvas

    Signals:
    - values_changed(candle: CandleItem, properties: dict): Emitted when user applies changes

    Usage:
        panel = PropertiesPanel()
        panel.values_changed.connect(canvas.update_candle_properties)
        canvas.selectionChanged.connect(panel.on_canvas_selection_changed)
    """

    # Signal emitted when user applies changes
    values_changed = pyqtSignal(CandleItem, dict)  # candle, new_properties

    # Available candle types (matching CandleToolbar)
    CANDLE_TYPES = [
        ("bullish", "Bullish"),
        ("bearish", "Bearish"),
        ("doji", "Doji"),
        ("hammer", "Hammer"),
        ("shooting_star", "Shooting Star"),
        ("spinning_top", "Spinning Top"),
        ("marubozu_long", "Marubozu Long"),
        ("marubozu_short", "Marubozu Short")
    ]

    def __init__(self, parent=None):
        """Initialize properties panel.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)

        # Current candle being edited
        self.current_candle: Optional[CandleItem] = None

        # Setup UI
        self._create_ui()

        # Initially disabled (no candle selected)
        self._set_enabled(False)

    def _create_ui(self):
        """Create UI components."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(12)

        # Title
        title = QLabel("Candle Properties")
        title.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 14px; font-weight: bold;")
        main_layout.addWidget(title)

        # OHLC Group
        ohlc_group = QGroupBox("OHLC Values (0-100)")
        ohlc_group.setStyleSheet(f"QGroupBox {{ color: {TEXT_PRIMARY}; }}")
        ohlc_layout = QFormLayout(ohlc_group)

        # Open
        self.open_spin = QDoubleSpinBox()
        self.open_spin.setRange(0.0, 100.0)
        self.open_spin.setDecimals(1)
        self.open_spin.setSingleStep(0.5)
        self.open_spin.setSuffix(" %")
        ohlc_layout.addRow("Open:", self.open_spin)

        # High
        self.high_spin = QDoubleSpinBox()
        self.high_spin.setRange(0.0, 100.0)
        self.high_spin.setDecimals(1)
        self.high_spin.setSingleStep(0.5)
        self.high_spin.setSuffix(" %")
        ohlc_layout.addRow("High:", self.high_spin)

        # Low
        self.low_spin = QDoubleSpinBox()
        self.low_spin.setRange(0.0, 100.0)
        self.low_spin.setDecimals(1)
        self.low_spin.setSingleStep(0.5)
        self.low_spin.setSuffix(" %")
        ohlc_layout.addRow("Low:", self.low_spin)

        # Close
        self.close_spin = QDoubleSpinBox()
        self.close_spin.setRange(0.0, 100.0)
        self.close_spin.setDecimals(1)
        self.close_spin.setSingleStep(0.5)
        self.close_spin.setSuffix(" %")
        ohlc_layout.addRow("Close:", self.close_spin)

        main_layout.addWidget(ohlc_group)

        # Candle Type Group
        type_group = QGroupBox("Candle Type")
        type_group.setStyleSheet(f"QGroupBox {{ color: {TEXT_PRIMARY}; }}")
        type_layout = QFormLayout(type_group)

        self.type_combo = QComboBox()
        for type_id, type_name in self.CANDLE_TYPES:
            self.type_combo.addItem(type_name, type_id)
        type_layout.addRow("Type:", self.type_combo)

        main_layout.addWidget(type_group)

        # Index Group
        index_group = QGroupBox("Candle Index")
        index_group.setStyleSheet(f"QGroupBox {{ color: {TEXT_PRIMARY}; }}")
        index_layout = QFormLayout(index_group)

        self.index_spin = QSpinBox()
        self.index_spin.setRange(-999, 0)  # Allow negative indices
        self.index_spin.setValue(0)
        self.index_spin.setPrefix("Index ")
        self.index_spin.setToolTip("Candle position: 0=current, -1=previous, -2=two back, etc.")
        index_layout.addRow("Index:", self.index_spin)

        main_layout.addWidget(index_group)

        # Apply Button
        self.apply_btn = QPushButton("✓ Apply Changes")
        self.apply_btn.setObjectName("primary")  # Primary button style
        self.apply_btn.setToolTip("Apply changes to selected candle")
        self.apply_btn.clicked.connect(self._on_apply_clicked)
        main_layout.addWidget(self.apply_btn)

        # Validation Info
        self.validation_label = QLabel("")
        self.validation_label.setStyleSheet("color: #ef5350; font-size: 11px;")  # Red for errors
        self.validation_label.setWordWrap(True)
        main_layout.addWidget(self.validation_label)

        # Stretch to push everything to top
        main_layout.addStretch()

    def _set_enabled(self, enabled: bool):
        """Enable or disable all input fields.

        Args:
            enabled: True to enable, False to disable
        """
        self.open_spin.setEnabled(enabled)
        self.high_spin.setEnabled(enabled)
        self.low_spin.setEnabled(enabled)
        self.close_spin.setEnabled(enabled)
        self.type_combo.setEnabled(enabled)
        self.index_spin.setEnabled(enabled)
        self.apply_btn.setEnabled(enabled)

    def on_canvas_selection_changed(self, selected_candles: list):
        """Handle canvas selection change.

        Args:
            selected_candles: List of selected CandleItem objects
        """
        if not selected_candles:
            # No selection - disable panel
            self.current_candle = None
            self._set_enabled(False)
            self.validation_label.setText("No candle selected")
            return

        if len(selected_candles) > 1:
            # Multiple selection - disable panel
            self.current_candle = None
            self._set_enabled(False)
            self.validation_label.setText(f"{len(selected_candles)} candles selected (select only one)")
            return

        # Single candle selected - update panel
        candle = selected_candles[0]
        self.current_candle = candle

        # Update input fields (without triggering valueChanged signals)
        self._update_fields_from_candle(candle)

        # Enable panel
        self._set_enabled(True)
        self.validation_label.setText("")

    def _update_fields_from_candle(self, candle: CandleItem):
        """Update input fields from candle properties.

        Args:
            candle: Candle to read properties from
        """
        # Block signals to avoid triggering valueChanged
        self.open_spin.blockSignals(True)
        self.high_spin.blockSignals(True)
        self.low_spin.blockSignals(True)
        self.close_spin.blockSignals(True)
        self.type_combo.blockSignals(True)
        self.index_spin.blockSignals(True)

        # Update OHLC values
        self.open_spin.setValue(candle.ohlc["open"])
        self.high_spin.setValue(candle.ohlc["high"])
        self.low_spin.setValue(candle.ohlc["low"])
        self.close_spin.setValue(candle.ohlc["close"])

        # Update candle type
        type_index = self.type_combo.findData(candle.candle_type)
        if type_index >= 0:
            self.type_combo.setCurrentIndex(type_index)

        # Update index
        self.index_spin.setValue(candle.index)

        # Unblock signals
        self.open_spin.blockSignals(False)
        self.high_spin.blockSignals(False)
        self.low_spin.blockSignals(False)
        self.close_spin.blockSignals(False)
        self.type_combo.blockSignals(False)
        self.index_spin.blockSignals(False)

    def _validate_ohlc(self) -> tuple[bool, str]:
        """Validate OHLC values.

        Returns:
            (is_valid, error_message)
        """
        open_val = self.open_spin.value()
        high_val = self.high_spin.value()
        low_val = self.low_spin.value()
        close_val = self.close_spin.value()

        # High must be >= all others
        if high_val < max(open_val, low_val, close_val):
            return False, "High must be >= Open, Low, and Close"

        # Low must be <= all others
        if low_val > min(open_val, high_val, close_val):
            return False, "Low must be <= Open, High, and Close"

        # Low <= Open, Close <= High
        if open_val < low_val or open_val > high_val:
            return False, "Open must be between Low and High"

        if close_val < low_val or close_val > high_val:
            return False, "Close must be between Low and High"

        return True, ""

    def _on_apply_clicked(self):
        """Handle apply button click."""
        if not self.current_candle:
            return

        # Validate OHLC
        is_valid, error_msg = self._validate_ohlc()
        if not is_valid:
            self.validation_label.setText(f"⚠ {error_msg}")
            return

        # Clear validation error
        self.validation_label.setText("")

        # Collect new properties
        new_properties = {
            "ohlc": {
                "open": self.open_spin.value(),
                "high": self.high_spin.value(),
                "low": self.low_spin.value(),
                "close": self.close_spin.value()
            },
            "candle_type": self.type_combo.currentData(),
            "index": self.index_spin.value()
        }

        # Emit signal
        self.values_changed.emit(self.current_candle, new_properties)

    def get_current_candle(self) -> Optional[CandleItem]:
        """Get currently selected candle.

        Returns:
            CandleItem or None
        """
        return self.current_candle
