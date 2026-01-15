"""Layout Manager Dialog for managing saved chart layouts.

Allows users to view, apply, rename, and delete saved layouts.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

if TYPE_CHECKING:
    from src.chart_marking.multi_chart.layout_manager import LayoutManager

logger = logging.getLogger(__name__)


class LayoutManagerDialog(QDialog):
    """Dialog for managing saved chart layouts."""

    def __init__(self, layout_manager: "LayoutManager", parent=None):
        """Initialize the layout manager dialog.

        Args:
            layout_manager: LayoutManager instance
            parent: Parent widget
        """
        super().__init__(parent)
        self.layout_manager = layout_manager

        self.setWindowTitle("Layout Manager")
        self.setMinimumSize(400, 300)

        self._setup_ui()
        self._populate_layouts()

    def _setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)

        # Header
        header = QLabel("Saved Chart Layouts")
        header.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(header)

        # Layout list
        self.layout_list = QListWidget()
        self.layout_list.setAlternatingRowColors(True)
        self.layout_list.itemDoubleClicked.connect(self._on_apply)
        layout.addWidget(self.layout_list)

        # Info label
        self.info_label = QLabel("Double-click to apply a layout")
        self.info_label.setStyleSheet("color: #888; font-style: italic;")
        layout.addWidget(self.info_label)

        # Buttons
        btn_layout = QHBoxLayout()

        self.apply_btn = QPushButton("Apply")
        self.apply_btn.setToolTip("Apply selected layout")
        self.apply_btn.clicked.connect(self._on_apply)
        btn_layout.addWidget(self.apply_btn)

        self.rename_btn = QPushButton("Rename...")
        self.rename_btn.setToolTip("Rename selected layout")
        self.rename_btn.clicked.connect(self._on_rename)
        btn_layout.addWidget(self.rename_btn)

        self.delete_btn = QPushButton("Delete")
        self.delete_btn.setToolTip("Delete selected layout")
        self.delete_btn.clicked.connect(self._on_delete)
        btn_layout.addWidget(self.delete_btn)

        btn_layout.addStretch()

        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.close_btn)

        layout.addLayout(btn_layout)

    def _populate_layouts(self):
        """Populate the layout list."""
        self.layout_list.clear()

        layouts = self.layout_manager.list_layouts()

        for layout_info in layouts:
            layout_id = layout_info.get("id", "")
            name = layout_info.get("name", layout_id)
            chart_count = layout_info.get("chart_count", 0)
            is_default = layout_id.startswith("default_")

            # Create item with details
            item_text = f"{name}"
            if chart_count > 0:
                item_text += f" ({chart_count} charts)"
            if is_default:
                item_text += " [Preset]"

            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, layout_id)

            # Style presets differently
            if is_default:
                item.setForeground(Qt.GlobalColor.darkCyan)

            self.layout_list.addItem(item)

        # Update info
        count = len(layouts)
        self.info_label.setText(
            f"{count} layout(s) available. Double-click to apply."
        )

    def _get_selected_layout_id(self) -> str | None:
        """Get the ID of the selected layout."""
        item = self.layout_list.currentItem()
        if item:
            return item.data(Qt.ItemDataRole.UserRole)
        return None

    def _on_apply(self):
        """Apply the selected layout."""
        layout_id = self._get_selected_layout_id()
        if not layout_id:
            QMessageBox.warning(self, "No Selection", "Please select a layout.")
            return

        layout = self.layout_manager.load_layout(layout_id)
        if layout:
            # Emit signal or callback to apply layout
            # For now, just close with success
            self.accept()
            logger.info("Layout '%s' selected for application", layout_id)
        else:
            QMessageBox.warning(
                self, "Error",
                f"Could not load layout '{layout_id}'."
            )

    def _on_rename(self):
        """Rename the selected layout."""
        layout_id = self._get_selected_layout_id()
        if not layout_id:
            QMessageBox.warning(self, "No Selection", "Please select a layout.")
            return

        if layout_id.startswith("default_"):
            QMessageBox.information(
                self, "Cannot Rename",
                "Preset layouts cannot be renamed."
            )
            return

        layout = self.layout_manager.load_layout(layout_id)
        if not layout:
            return

        current_name = layout.name
        new_name, ok = QInputDialog.getText(
            self, "Rename Layout",
            "Enter new name:",
            text=current_name
        )

        if ok and new_name and new_name != current_name:
            # Update the layout name
            layout.name = new_name
            self.layout_manager.save_layout(layout)
            self._populate_layouts()
            logger.info("Layout renamed from '%s' to '%s'", current_name, new_name)

    def _on_delete(self):
        """Delete the selected layout."""
        layout_id = self._get_selected_layout_id()
        if not layout_id:
            QMessageBox.warning(self, "No Selection", "Please select a layout.")
            return

        if layout_id.startswith("default_"):
            QMessageBox.information(
                self, "Cannot Delete",
                "Preset layouts cannot be deleted."
            )
            return

        reply = QMessageBox.question(
            self, "Delete Layout",
            f"Are you sure you want to delete this layout?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            success = self.layout_manager.delete_layout(layout_id)
            if success:
                self._populate_layouts()
                logger.info("Layout '%s' deleted", layout_id)
            else:
                QMessageBox.warning(
                    self, "Error",
                    f"Could not delete layout '{layout_id}'."
                )
