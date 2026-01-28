"""
Variable Manager Dialog - CRUD Interface for Project Variables.

This dialog provides a complete interface for creating, editing, and deleting
project variables stored in .cel_variables.json files. Includes real-time
Pydantic validation, category organization, tag management, and import/export.

Design:
    - 900x700px main layout with split view
    - DARK_ORANGE_PALETTE theme-consistent
    - 24px row height in table
    - Real-time validation with error feedback
    - Import/Export JSON functionality

Author: OrderPilot-AI Development Team
Created: 2026-01-28
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from src.core.variables import VariableStorage, VariableType
from src.core.variables.variable_models import ProjectVariable, ProjectVariables

logger = logging.getLogger(__name__)

# === Design System Constants (DARK_ORANGE_PALETTE) ===

# Backgrounds
BACKGROUND_MAIN = "#0F1115"
BACKGROUND_SURFACE = "#1A1D23"
BACKGROUND_INPUT = "#23262E"

# Borders
BORDER_MAIN = "#32363E"
BORDER_FOCUS = "#F29F05"

# Text
TEXT_PRIMARY = "#EAECEF"
TEXT_SECONDARY = "#848E9C"
TEXT_INVERSE = "#0F1115"

# Accent
PRIMARY = "#F29F05"
PRIMARY_HOVER = "#FFAD1F"
SUCCESS = "#0ECB81"
ERROR = "#F6465D"
INFO = "#5D6878"

# Components
SELECTION_BG = "rgba(242, 159, 5, 0.2)"
BUTTON_BG = "#2A2D33"
BUTTON_HOVER_BORDER = "#F29F05"

# Typography
FONT_FAMILY = "'Aptos', 'Segoe UI', sans-serif"
FONT_SIZE_XS = 11
FONT_SIZE_SM = 12
FONT_SIZE_MD = 14

# Spacing
SPACING_XS = 2
SPACING_SM = 4
SPACING_MD = 8
SPACING_LG = 16
RADIUS_SM = 4

# Compact Dimensions
ROW_HEIGHT = 24
HEADER_HEIGHT = 40
FOOTER_HEIGHT = 32


# === QSS Stylesheet ===

DIALOG_STYLESHEET = f"""
/* QDialog */
QDialog {{
    background-color: {BACKGROUND_MAIN};
    color: {TEXT_PRIMARY};
    font-family: {FONT_FAMILY};
    font-size: {FONT_SIZE_SM}px;
}}

/* QLabel */
QLabel {{
    color: {TEXT_PRIMARY};
    font-size: {FONT_SIZE_SM}px;
    padding: {SPACING_SM}px;
}}

QLabel#header {{
    font-size: {FONT_SIZE_MD}px;
    font-weight: bold;
    color: {PRIMARY};
    padding: {SPACING_MD}px;
}}

QLabel#error {{
    color: {ERROR};
    font-size: {FONT_SIZE_XS}px;
    padding: {SPACING_XS}px {SPACING_SM}px;
}}

/* QLineEdit */
QLineEdit {{
    background-color: {BACKGROUND_INPUT};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER_MAIN};
    border-radius: {RADIUS_SM}px;
    padding: {SPACING_SM}px {SPACING_MD}px;
    font-size: {FONT_SIZE_SM}px;
}}

QLineEdit:focus {{
    border-color: {BORDER_FOCUS};
}}

QLineEdit:disabled {{
    background-color: {BACKGROUND_SURFACE};
    color: {TEXT_SECONDARY};
}}

/* QTextEdit */
QTextEdit {{
    background-color: {BACKGROUND_INPUT};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER_MAIN};
    border-radius: {RADIUS_SM}px;
    padding: {SPACING_SM}px;
    font-size: {FONT_SIZE_SM}px;
}}

QTextEdit:focus {{
    border-color: {BORDER_FOCUS};
}}

/* QComboBox */
QComboBox {{
    background-color: {BACKGROUND_INPUT};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER_MAIN};
    border-radius: {RADIUS_SM}px;
    padding: {SPACING_SM}px {SPACING_MD}px;
    font-size: {FONT_SIZE_SM}px;
}}

QComboBox:focus {{
    border-color: {BORDER_FOCUS};
}}

QComboBox::drop-down {{
    border: none;
    padding-right: {SPACING_SM}px;
}}

QComboBox::down-arrow {{
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid {TEXT_SECONDARY};
}}

QComboBox QAbstractItemView {{
    background-color: {BACKGROUND_SURFACE};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER_MAIN};
    selection-background-color: {SELECTION_BG};
    selection-color: {TEXT_PRIMARY};
}}

/* QCheckBox */
QCheckBox {{
    color: {TEXT_PRIMARY};
    spacing: {SPACING_MD}px;
    font-size: {FONT_SIZE_SM}px;
}}

QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border: 1px solid {BORDER_MAIN};
    border-radius: 3px;
    background-color: {BACKGROUND_INPUT};
}}

QCheckBox::indicator:checked {{
    background-color: {PRIMARY};
    border-color: {PRIMARY};
}}

/* QPushButton */
QPushButton {{
    background-color: {BUTTON_BG};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER_MAIN};
    border-radius: {RADIUS_SM}px;
    padding: {SPACING_SM}px {SPACING_LG}px;
    font-size: {FONT_SIZE_SM}px;
    min-height: {ROW_HEIGHT}px;
}}

QPushButton:hover {{
    border-color: {BUTTON_HOVER_BORDER};
    background-color: rgba(242, 159, 5, 0.1);
}}

QPushButton:pressed {{
    background-color: rgba(242, 159, 5, 0.2);
}}

QPushButton:disabled {{
    color: {TEXT_SECONDARY};
    border-color: {BORDER_MAIN};
    background-color: {BACKGROUND_SURFACE};
}}

QPushButton#primary {{
    background-color: {PRIMARY};
    color: {TEXT_INVERSE};
    border-color: {PRIMARY};
    font-weight: bold;
}}

QPushButton#primary:hover {{
    background-color: {PRIMARY_HOVER};
    border-color: {PRIMARY_HOVER};
}}

QPushButton#danger {{
    background-color: {ERROR};
    color: {TEXT_PRIMARY};
    border-color: {ERROR};
}}

QPushButton#danger:hover {{
    background-color: #FF5566;
    border-color: #FF5566;
}}

/* QTableWidget */
QTableWidget {{
    background-color: {BACKGROUND_SURFACE};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER_MAIN};
    border-radius: {RADIUS_SM}px;
    gridline-color: {BORDER_MAIN};
    font-size: {FONT_SIZE_SM}px;
}}

QTableWidget::item {{
    padding: {SPACING_SM}px;
    border: none;
}}

QTableWidget::item:selected {{
    background-color: {SELECTION_BG};
    color: {TEXT_PRIMARY};
}}

QTableWidget::item:hover {{
    background-color: rgba(242, 159, 5, 0.1);
}}

QHeaderView::section {{
    background-color: {BACKGROUND_INPUT};
    color: {TEXT_SECONDARY};
    border: none;
    border-bottom: 1px solid {BORDER_MAIN};
    border-right: 1px solid {BORDER_MAIN};
    padding: {SPACING_SM}px {SPACING_MD}px;
    font-size: {FONT_SIZE_XS}px;
    font-weight: bold;
    text-transform: uppercase;
    height: {HEADER_HEIGHT}px;
}}

QHeaderView::section:last {{
    border-right: none;
}}

/* QListWidget */
QListWidget {{
    background-color: {BACKGROUND_SURFACE};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER_MAIN};
    border-radius: {RADIUS_SM}px;
    font-size: {FONT_SIZE_SM}px;
}}

QListWidget::item {{
    padding: {SPACING_SM}px {SPACING_MD}px;
    border: none;
}}

QListWidget::item:selected {{
    background-color: {SELECTION_BG};
    color: {TEXT_PRIMARY};
}}

QListWidget::item:hover {{
    background-color: rgba(242, 159, 5, 0.1);
}}

/* QGroupBox */
QGroupBox {{
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER_MAIN};
    border-radius: {RADIUS_SM}px;
    margin-top: 12px;
    font-weight: bold;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 {SPACING_SM}px;
    color: {PRIMARY};
}}

/* QSplitter */
QSplitter::handle {{
    background-color: {BORDER_MAIN};
    width: 2px;
}}

QSplitter::handle:hover {{
    background-color: {PRIMARY};
}}
"""


class VariableManagerDialog(QDialog):
    """
    Variable Manager Dialog for CRUD operations on project variables.

    Provides a complete interface for managing .cel_variables.json files:
    - Create/Edit/Delete variables
    - Real-time Pydantic validation
    - Category organization
    - Tag management
    - Import/Export JSON

    Signals:
        variables_changed: Emitted when variables are modified
    """

    variables_changed = pyqtSignal()

    def __init__(
        self,
        project_vars_path: Optional[str | Path] = None,
        parent: Optional[QWidget] = None,
    ):
        """
        Initialize Variable Manager Dialog.

        Args:
            project_vars_path: Path to .cel_variables.json file (optional)
            parent: Parent widget (optional)
        """
        super().__init__(parent)

        self.project_vars_path = Path(project_vars_path) if project_vars_path else None
        self.storage = VariableStorage()
        self.variables: Optional[ProjectVariables] = None
        self.current_var_name: Optional[str] = None
        self.unsaved_changes = False

        self._setup_ui()
        self._apply_stylesheet()
        self._load_variables()

        logger.info("Variable Manager Dialog initialized")

    def _setup_ui(self):
        """Setup the user interface."""
        self.setWindowTitle("📝 Variable Manager")
        self.setMinimumSize(900, 700)
        self.resize(900, 700)

        # Main layout
        layout = QVBoxLayout(self)
        layout.setSpacing(SPACING_MD)
        layout.setContentsMargins(SPACING_LG, SPACING_LG, SPACING_LG, SPACING_LG)

        # Header
        header = self._create_header()
        layout.addWidget(header)

        # Main content (splitter)
        splitter = self._create_main_content()
        layout.addWidget(splitter, stretch=1)

        # Footer
        footer = self._create_footer()
        layout.addLayout(footer)

    def _create_header(self) -> QWidget:
        """Create header with file info and actions."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # Title
        title = QLabel("📝 Variable Manager")
        title.setObjectName("header")
        layout.addWidget(title)

        # File path
        self.file_label = QLabel("No file loaded")
        self.file_label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: {FONT_SIZE_XS}px;")
        layout.addWidget(self.file_label, stretch=1)

        # File actions
        btn_new = QPushButton("🆕 New")
        btn_new.setToolTip("Create new variables file")
        btn_new.clicked.connect(self._new_file)
        layout.addWidget(btn_new)

        btn_open = QPushButton("📂 Open")
        btn_open.setToolTip("Open existing variables file")
        btn_open.clicked.connect(self._open_file)
        layout.addWidget(btn_open)

        btn_save = QPushButton("💾 Save")
        btn_save.setToolTip("Save current file")
        btn_save.clicked.connect(self._save_file)
        btn_save.setObjectName("primary")
        layout.addWidget(btn_save)
        self.btn_save = btn_save

        return widget

    def _create_main_content(self) -> QSplitter:
        """Create main content area with variable list and editor."""
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: Variable list
        left_panel = self._create_variable_list()
        splitter.addWidget(left_panel)

        # Right: Variable editor
        right_panel = self._create_variable_editor()
        splitter.addWidget(right_panel)

        splitter.setSizes([350, 550])
        return splitter

    def _create_variable_list(self) -> QWidget:
        """Create variable list panel."""
        widget = QGroupBox("Variables")
        layout = QVBoxLayout(widget)

        # Search
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search variables...")
        self.search_input.textChanged.connect(self._filter_variables)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)

        # Category filter
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Category:"))
        self.category_filter = QComboBox()
        self.category_filter.currentTextChanged.connect(self._filter_variables)
        filter_layout.addWidget(self.category_filter, stretch=1)
        layout.addLayout(filter_layout)

        # Variable table
        self.var_table = QTableWidget()
        self.var_table.setColumnCount(3)
        self.var_table.setHorizontalHeaderLabels(["Name", "Type", "Category"])
        self.var_table.horizontalHeader().setStretchLastSection(True)
        self.var_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.var_table.verticalHeader().setVisible(False)
        self.var_table.verticalHeader().setDefaultSectionSize(ROW_HEIGHT)
        self.var_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.var_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.var_table.itemSelectionChanged.connect(self._on_variable_selected)
        layout.addWidget(self.var_table, stretch=1)

        # Actions
        actions = QHBoxLayout()
        btn_add = QPushButton("➕ Add")
        btn_add.clicked.connect(self._add_variable)
        actions.addWidget(btn_add)

        btn_delete = QPushButton("🗑️ Delete")
        btn_delete.setObjectName("danger")
        btn_delete.clicked.connect(self._delete_variable)
        btn_delete.setEnabled(False)
        actions.addWidget(btn_delete)
        self.btn_delete = btn_delete

        layout.addLayout(actions)

        return widget

    def _create_variable_editor(self) -> QWidget:
        """Create variable editor panel."""
        widget = QGroupBox("Variable Editor")
        layout = QVBoxLayout(widget)

        # Form
        form = QFormLayout()
        form.setSpacing(SPACING_MD)
        form.setContentsMargins(SPACING_MD, SPACING_MD, SPACING_MD, SPACING_MD)

        # Name
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g., entry_min_price")
        self.name_input.textChanged.connect(self._on_form_changed)
        form.addRow("Name:", self.name_input)

        self.name_error = QLabel()
        self.name_error.setObjectName("error")
        self.name_error.setVisible(False)
        form.addRow("", self.name_error)

        # Type
        self.type_combo = QComboBox()
        self.type_combo.addItems([t.value for t in VariableType])
        self.type_combo.currentTextChanged.connect(self._on_type_changed)
        form.addRow("Type:", self.type_combo)

        # Value
        self.value_input = QLineEdit()
        self.value_input.setPlaceholderText("e.g., 90000.0")
        self.value_input.textChanged.connect(self._on_form_changed)
        form.addRow("Value:", self.value_input)

        self.value_error = QLabel()
        self.value_error.setObjectName("error")
        self.value_error.setVisible(False)
        form.addRow("", self.value_error)

        # Description
        self.desc_input = QTextEdit()
        self.desc_input.setPlaceholderText("Description of the variable...")
        self.desc_input.setMaximumHeight(80)
        self.desc_input.textChanged.connect(self._on_form_changed)
        form.addRow("Description:", self.desc_input)

        # Category
        self.category_input = QLineEdit()
        self.category_input.setPlaceholderText("e.g., Entry Rules")
        self.category_input.textChanged.connect(self._on_form_changed)
        form.addRow("Category:", self.category_input)

        # Unit
        self.unit_input = QLineEdit()
        self.unit_input.setPlaceholderText("e.g., USD, %, pips")
        self.unit_input.textChanged.connect(self._on_form_changed)
        form.addRow("Unit:", self.unit_input)

        # Tags
        self.tags_input = QLineEdit()
        self.tags_input.setPlaceholderText("Comma-separated tags: price, entry, threshold")
        self.tags_input.textChanged.connect(self._on_form_changed)
        form.addRow("Tags:", self.tags_input)

        # Readonly
        self.readonly_checkbox = QCheckBox("Read-only (cannot be modified at runtime)")
        self.readonly_checkbox.stateChanged.connect(self._on_form_changed)
        form.addRow("", self.readonly_checkbox)

        layout.addLayout(form)

        # Editor actions
        actions = QHBoxLayout()
        actions.addStretch()

        btn_clear = QPushButton("🔄 Clear")
        btn_clear.clicked.connect(self._clear_form)
        actions.addWidget(btn_clear)

        btn_apply = QPushButton("✅ Apply")
        btn_apply.setObjectName("primary")
        btn_apply.clicked.connect(self._apply_changes)
        btn_apply.setEnabled(False)
        actions.addWidget(btn_apply)
        self.btn_apply = btn_apply

        layout.addLayout(actions)
        layout.addStretch()

        # Initially disable form
        self._set_form_enabled(False)

        return widget

    def _create_footer(self) -> QHBoxLayout:
        """Create footer with global actions."""
        layout = QHBoxLayout()

        # Import/Export
        btn_import = QPushButton("📥 Import JSON")
        btn_import.setToolTip("Import variables from JSON file")
        btn_import.clicked.connect(self._import_json)
        layout.addWidget(btn_import)

        btn_export = QPushButton("📤 Export JSON")
        btn_export.setToolTip("Export variables to JSON file")
        btn_export.clicked.connect(self._export_json)
        layout.addWidget(btn_export)

        layout.addStretch()

        # Variable count
        self.count_label = QLabel("0 variables")
        self.count_label.setStyleSheet(f"color: {TEXT_SECONDARY};")
        layout.addWidget(self.count_label)

        # Close
        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self._on_close)
        layout.addWidget(btn_close)

        return layout

    def _apply_stylesheet(self):
        """Apply QSS stylesheet to dialog."""
        self.setStyleSheet(DIALOG_STYLESHEET)

    def _load_variables(self):
        """Load variables from file."""
        if not self.project_vars_path or not self.project_vars_path.exists():
            self.variables = ProjectVariables()
            self._update_file_label()
            self._refresh_variable_list()
            return

        try:
            self.variables = self.storage.load(self.project_vars_path, create_if_missing=True)
            self._update_file_label()
            self._refresh_variable_list()
            self.unsaved_changes = False
            logger.info(f"Loaded {len(self.variables.variables)} variables from {self.project_vars_path}")
        except Exception as e:
            logger.error(f"Failed to load variables: {e}")
            QMessageBox.critical(
                self,
                "Load Error",
                f"Failed to load variables:\n{str(e)}"
            )
            self.variables = ProjectVariables()

    def _refresh_variable_list(self):
        """Refresh the variable table."""
        if not self.variables:
            return

        # Save current selection
        selected_name = self.current_var_name

        # Clear table
        self.var_table.setRowCount(0)

        # Get unique categories
        categories = {"All"}
        for var_name, var in self.variables.variables.items():
            categories.add(var.category)

        # Update category filter
        current_category = self.category_filter.currentText()
        self.category_filter.clear()
        self.category_filter.addItems(sorted(categories))
        if current_category in categories:
            self.category_filter.setCurrentText(current_category)

        # Populate table
        search_text = self.search_input.text().lower()
        category_filter = self.category_filter.currentText()

        for var_name, var in sorted(self.variables.variables.items()):
            # Apply filters
            if search_text and search_text not in var_name.lower() and search_text not in var.description.lower():
                continue
            if category_filter != "All" and var.category != category_filter:
                continue

            row = self.var_table.rowCount()
            self.var_table.insertRow(row)

            # Name
            name_item = QTableWidgetItem(var_name)
            name_item.setData(Qt.ItemDataRole.UserRole, var_name)
            self.var_table.setItem(row, 0, name_item)

            # Type
            type_item = QTableWidgetItem(var.type.value)
            self.var_table.setItem(row, 1, type_item)

            # Category
            category_item = QTableWidgetItem(var.category)
            self.var_table.setItem(row, 2, category_item)

            # Restore selection
            if var_name == selected_name:
                self.var_table.selectRow(row)

        # Update count
        total = len(self.variables.variables)
        visible = self.var_table.rowCount()
        if visible == total:
            self.count_label.setText(f"{total} variable{'s' if total != 1 else ''}")
        else:
            self.count_label.setText(f"{visible} of {total} variable{'s' if total != 1 else ''}")

    def _filter_variables(self):
        """Apply search and category filters."""
        self._refresh_variable_list()

    def _on_variable_selected(self):
        """Handle variable selection in table."""
        selected_items = self.var_table.selectedItems()
        if not selected_items:
            self.current_var_name = None
            self._clear_form()
            self._set_form_enabled(False)
            self.btn_delete.setEnabled(False)
            return

        # Get variable name
        row = selected_items[0].row()
        name_item = self.var_table.item(row, 0)
        var_name = name_item.data(Qt.ItemDataRole.UserRole)

        if var_name == self.current_var_name:
            return

        self.current_var_name = var_name
        self._load_variable_to_form(var_name)
        self._set_form_enabled(True)
        self.btn_delete.setEnabled(True)

    def _load_variable_to_form(self, var_name: str):
        """Load variable data into form."""
        if not self.variables or var_name not in self.variables.variables:
            return

        var = self.variables.variables[var_name]

        # Block signals during load
        self.name_input.blockSignals(True)
        self.type_combo.blockSignals(True)
        self.value_input.blockSignals(True)
        self.desc_input.blockSignals(True)
        self.category_input.blockSignals(True)
        self.unit_input.blockSignals(True)
        self.tags_input.blockSignals(True)
        self.readonly_checkbox.blockSignals(True)

        # Set values
        self.name_input.setText(var_name)
        self.type_combo.setCurrentText(var.type.value)
        self.value_input.setText(str(var.value))
        self.desc_input.setPlainText(var.description)
        self.category_input.setText(var.category)
        self.unit_input.setText(var.unit or "")
        self.tags_input.setText(", ".join(var.tags))
        self.readonly_checkbox.setChecked(var.readonly)

        # Restore signals
        self.name_input.blockSignals(False)
        self.type_combo.blockSignals(False)
        self.value_input.blockSignals(False)
        self.desc_input.blockSignals(False)
        self.category_input.blockSignals(False)
        self.unit_input.blockSignals(False)
        self.tags_input.blockSignals(False)
        self.readonly_checkbox.blockSignals(False)

        # Clear errors
        self._clear_errors()
        self.btn_apply.setEnabled(False)

    def _clear_form(self):
        """Clear all form fields."""
        self.name_input.clear()
        self.type_combo.setCurrentIndex(0)
        self.value_input.clear()
        self.desc_input.clear()
        self.category_input.clear()
        self.unit_input.clear()
        self.tags_input.clear()
        self.readonly_checkbox.setChecked(False)
        self._clear_errors()
        self.btn_apply.setEnabled(False)

    def _set_form_enabled(self, enabled: bool):
        """Enable or disable form fields."""
        self.name_input.setEnabled(enabled)
        self.type_combo.setEnabled(enabled)
        self.value_input.setEnabled(enabled)
        self.desc_input.setEnabled(enabled)
        self.category_input.setEnabled(enabled)
        self.unit_input.setEnabled(enabled)
        self.tags_input.setEnabled(enabled)
        self.readonly_checkbox.setEnabled(enabled)

    def _on_type_changed(self):
        """Handle type change."""
        var_type = self.type_combo.currentText()

        # Update value placeholder
        placeholders = {
            "float": "e.g., 90000.0",
            "int": "e.g., 10",
            "string": "e.g., bullish",
            "bool": "true or false",
            "list": "e.g., [1, 2, 3]"
        }
        self.value_input.setPlaceholderText(placeholders.get(var_type, "Value"))

        self._on_form_changed()

    def _on_form_changed(self):
        """Handle form field changes."""
        self.btn_apply.setEnabled(True)
        self._validate_form()

    def _validate_form(self) -> bool:
        """
        Validate form data in real-time.

        Returns:
            True if form is valid, False otherwise
        """
        valid = True
        self._clear_errors()

        # Validate name
        name = self.name_input.text().strip()
        if not name:
            self.name_error.setText("⚠️ Name is required")
            self.name_error.setVisible(True)
            valid = False
        elif not name.replace("_", "").isalnum():
            self.name_error.setText("⚠️ Name must be alphanumeric with underscores")
            self.name_error.setVisible(True)
            valid = False
        elif self.current_var_name != name and self.variables and name in self.variables.variables:
            self.name_error.setText("⚠️ Variable name already exists")
            self.name_error.setVisible(True)
            valid = False

        # Validate value based on type
        value_str = self.value_input.text().strip()
        var_type = self.type_combo.currentText()

        if not value_str:
            self.value_error.setText("⚠️ Value is required")
            self.value_error.setVisible(True)
            valid = False
        else:
            try:
                # Try to parse value
                if var_type == "float":
                    float(value_str)
                elif var_type == "int":
                    int(value_str)
                elif var_type == "bool":
                    if value_str.lower() not in ("true", "false"):
                        raise ValueError("Must be 'true' or 'false'")
                elif var_type == "list":
                    json.loads(value_str)
                # string type always valid
            except (ValueError, json.JSONDecodeError) as e:
                self.value_error.setText(f"⚠️ Invalid {var_type}: {str(e)}")
                self.value_error.setVisible(True)
                valid = False

        # Validate description
        desc = self.desc_input.toPlainText().strip()
        if not desc:
            valid = False

        return valid

    def _clear_errors(self):
        """Clear all error labels."""
        self.name_error.setVisible(False)
        self.value_error.setVisible(False)

    def _add_variable(self):
        """Add new variable."""
        self.current_var_name = None
        self._clear_form()
        self._set_form_enabled(True)
        self.btn_delete.setEnabled(False)
        self.name_input.setFocus()

    def _delete_variable(self):
        """Delete selected variable."""
        if not self.current_var_name or not self.variables:
            return

        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete variable '{self.current_var_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            self.variables.delete_variable(self.current_var_name)
            self.unsaved_changes = True
            self._refresh_variable_list()
            self._clear_form()
            self._set_form_enabled(False)
            self.btn_delete.setEnabled(False)
            self.variables_changed.emit()
            logger.info(f"Deleted variable: {self.current_var_name}")
        except Exception as e:
            logger.error(f"Failed to delete variable: {e}")
            QMessageBox.critical(self, "Delete Error", f"Failed to delete variable:\n{str(e)}")

    def _apply_changes(self):
        """Apply changes from form."""
        if not self._validate_form():
            QMessageBox.warning(self, "Validation Error", "Please fix the errors before applying changes.")
            return

        try:
            # Get form data
            name = self.name_input.text().strip()
            var_type = VariableType(self.type_combo.currentText())
            value_str = self.value_input.text().strip()
            desc = self.desc_input.toPlainText().strip()
            category = self.category_input.text().strip()
            unit = self.unit_input.text().strip() or None
            tags = [t.strip() for t in self.tags_input.text().split(",") if t.strip()]
            readonly = self.readonly_checkbox.isChecked()

            # Parse value
            value: Any
            if var_type == VariableType.FLOAT:
                value = float(value_str)
            elif var_type == VariableType.INT:
                value = int(value_str)
            elif var_type == VariableType.BOOL:
                value = value_str.lower() == "true"
            elif var_type == VariableType.LIST:
                value = json.loads(value_str)
            else:  # string
                value = value_str

            # Create variable
            var = ProjectVariable(
                type=var_type,
                value=value,
                description=desc,
                category=category,
                unit=unit,
                tags=tags,
                readonly=readonly
            )

            # Add or update
            if not self.variables:
                self.variables = ProjectVariables()

            if self.current_var_name and self.current_var_name != name:
                # Rename: delete old, add new
                self.variables.delete_variable(self.current_var_name)
                self.variables.add_variable(name, var)
                logger.info(f"Renamed variable: {self.current_var_name} -> {name}")
            elif self.current_var_name:
                # Update existing
                self.variables.update_variable(name, var)
                logger.info(f"Updated variable: {name}")
            else:
                # Add new
                self.variables.add_variable(name, var)
                logger.info(f"Added variable: {name}")

            self.current_var_name = name
            self.unsaved_changes = True
            self._refresh_variable_list()
            self.btn_apply.setEnabled(False)
            self.variables_changed.emit()

        except Exception as e:
            logger.error(f"Failed to apply changes: {e}")
            QMessageBox.critical(self, "Apply Error", f"Failed to apply changes:\n{str(e)}")

    def _new_file(self):
        """Create new variables file."""
        if self.unsaved_changes:
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have unsaved changes. Create new file anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "New Variables File",
            str(Path.cwd() / ".cel_variables.json"),
            "JSON Files (*.json)"
        )

        if not file_path:
            return

        self.project_vars_path = Path(file_path)
        self.variables = ProjectVariables()
        self.unsaved_changes = False
        self._update_file_label()
        self._refresh_variable_list()
        self._clear_form()
        self._set_form_enabled(False)
        logger.info(f"Created new file: {self.project_vars_path}")

    def _open_file(self):
        """Open existing variables file."""
        if self.unsaved_changes:
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have unsaved changes. Open file anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Variables File",
            str(Path.cwd()),
            "JSON Files (*.json)"
        )

        if not file_path:
            return

        self.project_vars_path = Path(file_path)
        self._load_variables()
        self._clear_form()
        self._set_form_enabled(False)

    def _save_file(self):
        """Save variables to file."""
        if not self.project_vars_path:
            # Save As
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save Variables File",
                str(Path.cwd() / ".cel_variables.json"),
                "JSON Files (*.json)"
            )
            if not file_path:
                return
            self.project_vars_path = Path(file_path)

        if not self.variables:
            return

        try:
            self.storage.save(self.project_vars_path, self.variables)
            self.unsaved_changes = False
            self._update_file_label()
            logger.info(f"Saved {len(self.variables.variables)} variables to {self.project_vars_path}")
            QMessageBox.information(
                self,
                "Saved",
                f"Saved {len(self.variables.variables)} variables to:\n{self.project_vars_path}"
            )
        except Exception as e:
            logger.error(f"Failed to save variables: {e}")
            QMessageBox.critical(self, "Save Error", f"Failed to save variables:\n{str(e)}")

    def _import_json(self):
        """Import variables from JSON file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Variables",
            str(Path.cwd()),
            "JSON Files (*.json)"
        )

        if not file_path:
            return

        try:
            imported = self.storage.load(Path(file_path))

            # Merge or replace?
            if self.variables and self.variables.variables:
                reply = QMessageBox.question(
                    self,
                    "Import Mode",
                    f"Import {len(imported.variables)} variables.\n\nMerge with existing ({len(self.variables.variables)} variables) or replace?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel,
                    QMessageBox.StandardButton.Yes
                )

                if reply == QMessageBox.StandardButton.Cancel:
                    return
                elif reply == QMessageBox.StandardButton.Yes:
                    # Merge
                    for name, var in imported.variables.items():
                        self.variables.add_variable(name, var)
                else:
                    # Replace
                    self.variables = imported
            else:
                self.variables = imported

            self.unsaved_changes = True
            self._refresh_variable_list()
            self.variables_changed.emit()
            logger.info(f"Imported {len(imported.variables)} variables from {file_path}")
            QMessageBox.information(
                self,
                "Import Successful",
                f"Imported {len(imported.variables)} variables from:\n{file_path}"
            )
        except Exception as e:
            logger.error(f"Failed to import variables: {e}")
            QMessageBox.critical(self, "Import Error", f"Failed to import variables:\n{str(e)}")

    def _export_json(self):
        """Export variables to JSON file."""
        if not self.variables or not self.variables.variables:
            QMessageBox.warning(self, "No Variables", "No variables to export.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Variables",
            str(Path.cwd() / "exported_variables.json"),
            "JSON Files (*.json)"
        )

        if not file_path:
            return

        try:
            self.storage.save(Path(file_path), self.variables)
            logger.info(f"Exported {len(self.variables.variables)} variables to {file_path}")
            QMessageBox.information(
                self,
                "Export Successful",
                f"Exported {len(self.variables.variables)} variables to:\n{file_path}"
            )
        except Exception as e:
            logger.error(f"Failed to export variables: {e}")
            QMessageBox.critical(self, "Export Error", f"Failed to export variables:\n{str(e)}")

    def _update_file_label(self):
        """Update file path label."""
        if self.project_vars_path:
            self.file_label.setText(f"📁 {self.project_vars_path.name}")
        else:
            self.file_label.setText("No file loaded")

    def _on_close(self):
        """Handle close button."""
        if self.unsaved_changes:
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have unsaved changes. Close anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        self.accept()

    def closeEvent(self, event):
        """Handle dialog close event."""
        if self.unsaved_changes:
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have unsaved changes. Close anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                event.ignore()
                return

        event.accept()
