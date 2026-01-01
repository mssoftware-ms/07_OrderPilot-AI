"""Zone Edit Dialog for editing chart zone properties.

Allows users to modify zone boundaries, type, and label.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QDoubleSpinBox,
    QComboBox,
    QPushButton,
    QMessageBox,
)

if TYPE_CHECKING:
    from src.chart_marking.models import Zone

logger = logging.getLogger(__name__)


class ZoneEditDialog(QDialog):
    """Dialog for editing a chart zone."""

    def __init__(self, zone: "Zone", parent=None):
        """Initialize the zone edit dialog.

        Args:
            zone: Zone object to edit
            parent: Parent widget
        """
        super().__init__(parent)
        self.zone = zone
        self._original_values = {
            "top_price": zone.top_price,
            "bottom_price": zone.bottom_price,
            "label": zone.label,
            "zone_type": zone.zone_type.value,
        }

        self.setWindowTitle(f"Edit Zone: {zone.label or zone.id}")
        self.setMinimumWidth(350)

        self._setup_ui()
        self._load_values()

    def _setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)

        # Header
        header = QLabel(f"Zone ID: {self.zone.id}")
        header.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(header)

        # Form layout
        form = QFormLayout()

        # Zone type
        self.type_combo = QComboBox()
        self.type_combo.addItems(["support", "resistance", "demand", "supply"])
        form.addRow("Type:", self.type_combo)

        # Label
        self.label_edit = QLineEdit()
        self.label_edit.setPlaceholderText("Zone label...")
        form.addRow("Label:", self.label_edit)

        # Top price
        self.top_price_spin = QDoubleSpinBox()
        self.top_price_spin.setDecimals(6)
        self.top_price_spin.setRange(0.000001, 99999999.999999)
        self.top_price_spin.setSingleStep(0.01)
        form.addRow("Top Price:", self.top_price_spin)

        # Bottom price
        self.bottom_price_spin = QDoubleSpinBox()
        self.bottom_price_spin.setDecimals(6)
        self.bottom_price_spin.setRange(0.000001, 99999999.999999)
        self.bottom_price_spin.setSingleStep(0.01)
        form.addRow("Bottom Price:", self.bottom_price_spin)

        # Zone info
        info_text = self._format_time_info()
        info_label = QLabel(info_text)
        info_label.setStyleSheet("color: #888; font-size: 10px; margin-top: 10px;")
        info_label.setWordWrap(True)
        form.addRow("Time Range:", info_label)

        layout.addLayout(form)

        # Zone height indicator
        self.height_label = QLabel()
        self.height_label.setStyleSheet("color: #888; font-size: 10px;")
        layout.addWidget(self.height_label)
        self._update_height_label()

        # Connect spinbox changes to update height label
        self.top_price_spin.valueChanged.connect(self._update_height_label)
        self.bottom_price_spin.valueChanged.connect(self._update_height_label)

        layout.addStretch()

        # Buttons
        btn_layout = QHBoxLayout()

        self.delete_btn = QPushButton("Delete Zone")
        self.delete_btn.setStyleSheet("color: #ff6666;")
        self.delete_btn.clicked.connect(self._on_delete)
        btn_layout.addWidget(self.delete_btn)

        btn_layout.addStretch()

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)

        self.save_btn = QPushButton("Save")
        self.save_btn.setDefault(True)
        self.save_btn.clicked.connect(self._on_save)
        btn_layout.addWidget(self.save_btn)

        layout.addLayout(btn_layout)

    def _format_time_info(self) -> str:
        """Format the time range info."""
        try:
            start = datetime.fromtimestamp(self.zone.start_time)
            end = datetime.fromtimestamp(self.zone.end_time)
            return f"{start.strftime('%Y-%m-%d %H:%M')} - {end.strftime('%Y-%m-%d %H:%M')}"
        except (OSError, ValueError):
            return f"{self.zone.start_time} - {self.zone.end_time}"

    def _load_values(self):
        """Load current zone values into the form."""
        # Type
        zone_type = self.zone.zone_type.value
        index = self.type_combo.findText(zone_type)
        if index >= 0:
            self.type_combo.setCurrentIndex(index)

        # Label
        self.label_edit.setText(self.zone.label or "")

        # Prices
        self.top_price_spin.setValue(self.zone.top_price)
        self.bottom_price_spin.setValue(self.zone.bottom_price)

    def _update_height_label(self):
        """Update the zone height indicator."""
        top = self.top_price_spin.value()
        bottom = self.bottom_price_spin.value()
        if top > 0 and bottom > 0:
            height = abs(top - bottom)
            mid = (top + bottom) / 2
            pct = (height / mid) * 100 if mid > 0 else 0
            self.height_label.setText(f"Zone Height: {height:.6f} ({pct:.3f}%)")

    def _on_save(self):
        """Save changes and close dialog."""
        # Validate
        top = self.top_price_spin.value()
        bottom = self.bottom_price_spin.value()

        if top <= bottom:
            QMessageBox.warning(
                self, "Invalid Prices",
                "Top price must be greater than bottom price."
            )
            return

        # Accept dialog - caller will apply changes
        self.accept()

    def _on_delete(self):
        """Confirm and delete the zone."""
        reply = QMessageBox.question(
            self, "Delete Zone",
            f"Are you sure you want to delete zone '{self.zone.label or self.zone.id}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.done(2)  # Use return code 2 to indicate deletion

    def get_values(self) -> dict:
        """Get the edited values.

        Returns:
            Dictionary with edited zone properties
        """
        return {
            "zone_type": self.type_combo.currentText(),
            "label": self.label_edit.text(),
            "top_price": self.top_price_spin.value(),
            "bottom_price": self.bottom_price_spin.value(),
        }

    def has_changes(self) -> bool:
        """Check if any values were changed."""
        current = self.get_values()
        return (
            current["top_price"] != self._original_values["top_price"] or
            current["bottom_price"] != self._original_values["bottom_price"] or
            current["label"] != self._original_values["label"] or
            current["zone_type"] != self._original_values["zone_type"]
        )
