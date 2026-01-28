"""
Variable Reference Dialog - Compact, Theme-Consistent Read-Only Variable Browser.

This dialog provides a quick reference for all available variables in CEL expressions.
Shows variables from Chart, Bot, Project, Indicators, and Regime sources with
live values, copy functionality, and search/filter capabilities.

Design:
    - 800x600px compact layout (15-20% smaller than original)
    - DARK_ORANGE_PALETTE theme-consistent
    - 24px row height (vs 32px standard)
    - Icon-only buttons for space saving
    - Collapsible category groups
    - Search and filter functionality

Author: OrderPilot-AI Development Team
Created: 2026-01-28
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Optional

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QBrush, QClipboard, QColor, QFont
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    from src.core.trading_bot.bot_config import BotConfig
    from src.ui.widgets.chart_window import ChartWindow

from src.core.variables import CELContextBuilder

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
ROW_HEIGHT = 24  # vs 32px standard
HEADER_HEIGHT = 40  # vs 60px
FOOTER_HEIGHT = 32  # vs 48px


# === QSS Stylesheet ===

QSS_VARIABLE_REFERENCE = f"""
/* Variable Reference Dialog - Compact Theme */

QDialog {{
    background-color: {BACKGROUND_MAIN};
    color: {TEXT_PRIMARY};
    font-family: {FONT_FAMILY};
    font-size: {FONT_SIZE_MD}px;
}}

/* ===== HEADER ===== */
QWidget#header {{
    background-color: {BACKGROUND_SURFACE};
    border-bottom: 1px solid {BORDER_MAIN};
    padding: {SPACING_SM}px;
    min-height: {HEADER_HEIGHT}px;
    max-height: {HEADER_HEIGHT}px;
}}

/* Title */
QLabel#title {{
    color: {TEXT_PRIMARY};
    font-size: {FONT_SIZE_MD}px;
    font-weight: 600;
    padding: 0px;
    margin: 0px;
}}

/* Search Input (compact) */
QLineEdit#search {{
    background-color: {BACKGROUND_INPUT};
    border: 1px solid {BORDER_MAIN};
    border-radius: {RADIUS_SM}px;
    padding: {SPACING_SM}px {SPACING_MD}px;
    font-size: {FONT_SIZE_SM}px;
    color: {TEXT_PRIMARY};
    min-height: 28px;
    max-height: 28px;
}}

QLineEdit#search:focus {{
    border-color: {BORDER_FOCUS};
}}

/* Filter ComboBoxes (compact) */
QComboBox {{
    background-color: {BACKGROUND_INPUT};
    border: 1px solid {BORDER_MAIN};
    border-radius: {RADIUS_SM}px;
    padding: {SPACING_SM}px {SPACING_MD}px;
    font-size: {FONT_SIZE_SM}px;
    color: {TEXT_PRIMARY};
    min-height: 28px;
    max-height: 28px;
    min-width: 100px;
}}

QComboBox:focus {{
    border-color: {BORDER_FOCUS};
}}

QComboBox::drop-down {{
    border: none;
    width: 20px;
}}

QComboBox::down-arrow {{
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 6px solid {TEXT_SECONDARY};
    margin-right: {SPACING_SM}px;
}}

QComboBox QAbstractItemView {{
    background-color: {BACKGROUND_INPUT};
    border: 1px solid {BORDER_MAIN};
    selection-background-color: {SELECTION_BG};
    color: {TEXT_PRIMARY};
    outline: none;
}}

/* ===== TABLE ===== */
QTableWidget {{
    background-color: {BACKGROUND_MAIN};
    alternate-background-color: {BACKGROUND_INPUT};
    gridline-color: {BORDER_MAIN};
    border: none;
    font-size: {FONT_SIZE_XS}px;
    selection-background-color: {SELECTION_BG};
    selection-color: {TEXT_PRIMARY};
    outline: none;
}}

QTableWidget::item {{
    padding: {SPACING_SM}px;
    height: {ROW_HEIGHT}px;
    border: none;
}}

QTableWidget::item:selected {{
    background-color: {SELECTION_BG};
    color: {TEXT_PRIMARY};
}}

/* Table Header */
QHeaderView::section {{
    background-color: {BACKGROUND_SURFACE};
    color: {TEXT_SECONDARY};
    padding: {SPACING_SM}px {SPACING_MD}px;
    border: none;
    border-bottom: 1px solid {BORDER_MAIN};
    font-size: {FONT_SIZE_SM}px;
    font-weight: 600;
    height: 28px;
}}

QHeaderView::section:hover {{
    background-color: {BUTTON_BG};
}}

/* ===== CATEGORY GROUPS ===== */
QGroupBox {{
    background-color: transparent;
    border: 1px solid {BORDER_MAIN};
    border-radius: {RADIUS_SM}px;
    margin-top: {SPACING_MD}px;
    padding-top: {SPACING_LG}px;
    font-size: {FONT_SIZE_SM}px;
    color: {TEXT_PRIMARY};
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0px {SPACING_MD}px;
    background-color: {BACKGROUND_MAIN};
    color: {TEXT_PRIMARY};
    font-weight: 600;
}}

/* ===== BUTTONS ===== */
QPushButton {{
    background-color: {BUTTON_BG};
    border: 1px solid {BORDER_MAIN};
    border-radius: {RADIUS_SM}px;
    padding: {SPACING_SM}px {SPACING_MD}px;
    font-size: {FONT_SIZE_SM}px;
    color: {TEXT_PRIMARY};
    min-height: 28px;
}}

QPushButton:hover {{
    border-color: {BUTTON_HOVER_BORDER};
    background-color: {BACKGROUND_INPUT};
}}

QPushButton:pressed {{
    background-color: {BACKGROUND_MAIN};
}}

QPushButton:disabled {{
    color: {TEXT_SECONDARY};
    border-color: {BORDER_MAIN};
}}

/* Primary Button (Close) */
QPushButton#primary {{
    background-color: {PRIMARY};
    color: {TEXT_INVERSE};
    border-color: {PRIMARY};
    font-weight: 600;
}}

QPushButton#primary:hover {{
    background-color: {PRIMARY_HOVER};
    border-color: {PRIMARY_HOVER};
}}

/* Icon Button (compact) */
QPushButton.icon-btn {{
    min-width: 28px;
    max-width: 28px;
    min-height: 28px;
    max-height: 28px;
    padding: {SPACING_XS}px;
}}

/* ===== FOOTER ===== */
QWidget#footer {{
    background-color: {BACKGROUND_SURFACE};
    border-top: 1px solid {BORDER_MAIN};
    padding: {SPACING_SM}px {SPACING_MD}px;
    min-height: {FOOTER_HEIGHT}px;
    max-height: {FOOTER_HEIGHT}px;
}}

/* Status Label */
QLabel#status {{
    color: {TEXT_SECONDARY};
    font-size: {FONT_SIZE_SM}px;
}}
"""


class VariableReferenceDialog(QDialog):
    """
    Variable Reference Dialog - Read-only browser for all CEL variables.

    Shows variables from 5 categories:
    - Chart: OHLCV data and chart metrics
    - Bot: Bot configuration parameters
    - Project: User-defined project variables
    - Indicators: Technical indicator values
    - Regime: Regime detection values

    Features:
    - Search and filter functionality
    - Copy to clipboard (individual or all)
    - Live value updates (optional)
    - Compact, space-efficient design
    - Theme-consistent styling

    Args:
        chart_window: ChartWindow instance for chart data (optional)
        bot_config: BotConfig instance for bot configuration (optional)
        project_vars_path: Path to .cel_variables.json (optional)
        indicators: Dictionary of indicator values (optional)
        regime: Dictionary of regime values (optional)
        parent: Parent widget

    Examples:
        >>> dialog = VariableReferenceDialog(
        ...     chart_window=chart_window,
        ...     bot_config=bot_config,
        ...     project_vars_path="project/.cel_variables.json"
        ... )
        >>> dialog.exec()
    """

    # Signals
    variable_copied = pyqtSignal(str, str)  # variable_name, value

    def __init__(
        self,
        chart_window: Optional[ChartWindow] = None,
        bot_config: Optional[BotConfig] = None,
        project_vars_path: Optional[str | Path] = None,
        indicators: Optional[Dict[str, Any]] = None,
        regime: Optional[Dict[str, Any]] = None,
        enable_live_updates: bool = False,
        update_interval_ms: int = 1000,
        parent: Optional[QWidget] = None,
    ):
        """Initialize variable reference dialog."""
        super().__init__(parent)

        # Store data sources
        self.chart_window = chart_window
        self.bot_config = bot_config
        self.project_vars_path = project_vars_path
        self.indicators = indicators or {}
        self.regime = regime or {}

        # Context builder
        self.context_builder = CELContextBuilder()

        # Current variables data
        self.variables: Dict[str, Dict[str, Any]] = {}
        self.filtered_variables: Dict[str, Dict[str, Any]] = {}

        # Live updates
        self.enable_live_updates = enable_live_updates
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self._refresh_values)
        if enable_live_updates:
            self.update_timer.start(update_interval_ms)

        # Setup UI
        self._setup_ui()
        self._apply_stylesheet()
        self._load_variables()
        self._populate_table()

        logger.info("VariableReferenceDialog initialized")

    def _setup_ui(self):
        """Setup dialog UI."""
        # Dialog properties
        self.setWindowTitle("📋 Variable Reference")
        self.setModal(False)  # Non-modal
        self.resize(800, 600)
        self.setMinimumSize(600, 400)

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header
        header = self._create_header()
        main_layout.addWidget(header)

        # Table
        self.table = self._create_table()
        main_layout.addWidget(self.table, 1)  # Stretch

        # Footer
        footer = self._create_footer()
        main_layout.addWidget(footer)

    def _create_header(self) -> QWidget:
        """Create compact header with search and filters."""
        header = QWidget()
        header.setObjectName("header")

        layout = QHBoxLayout(header)
        layout.setContentsMargins(SPACING_MD, SPACING_SM, SPACING_MD, SPACING_SM)
        layout.setSpacing(SPACING_MD)

        # Title
        title = QLabel("📋 Variables")
        title.setObjectName("title")
        layout.addWidget(title)

        layout.addStretch()

        # Search input
        self.search_input = QLineEdit()
        self.search_input.setObjectName("search")
        self.search_input.setPlaceholderText("🔍 Search variables...")
        self.search_input.setFixedWidth(200)
        self.search_input.textChanged.connect(self._on_search_changed)
        layout.addWidget(self.search_input)

        # Category filter
        self.category_filter = QComboBox()
        self.category_filter.addItems([
            "All Categories",
            "Chart",
            "Bot",
            "Project",
            "Indicators",
            "Regime"
        ])
        self.category_filter.currentTextChanged.connect(self._on_filter_changed)
        layout.addWidget(self.category_filter)

        # Status filter
        self.status_filter = QComboBox()
        self.status_filter.addItems([
            "All Values",
            "Defined",
            "Undefined"
        ])
        self.status_filter.currentTextChanged.connect(self._on_filter_changed)
        layout.addWidget(self.status_filter)

        # Close button (compact)
        close_btn = QPushButton("×")
        close_btn.setObjectName("close-btn")
        close_btn.setFixedSize(28, 28)
        close_btn.setToolTip("Close")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)

        return header

    def _create_table(self) -> QTableWidget:
        """Create compact table widget."""
        table = QTableWidget()
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels([
            "Variable",
            "Label",
            "Category",
            "Type",
            "Value",
            ""  # Copy button column
        ])

        # Column widths
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # Variable
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Label
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Category
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Type
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)  # Value
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)  # Copy btn
        table.setColumnWidth(5, 40)  # Copy button column

        # Row height
        table.verticalHeader().setDefaultSectionSize(ROW_HEIGHT)
        table.verticalHeader().setVisible(False)

        # Alternating colors
        table.setAlternatingRowColors(True)

        # Selection
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)

        # No edit
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        # Font
        font = QFont(FONT_FAMILY, FONT_SIZE_XS)
        table.setFont(font)

        return table

    def _create_footer(self) -> QWidget:
        """Create compact footer with actions."""
        footer = QWidget()
        footer.setObjectName("footer")

        layout = QHBoxLayout(footer)
        layout.setContentsMargins(SPACING_MD, SPACING_SM, SPACING_MD, SPACING_SM)
        layout.setSpacing(SPACING_MD)

        # Status label
        self.status_label = QLabel("0 variables")
        self.status_label.setObjectName("status")
        layout.addWidget(self.status_label)

        layout.addStretch()

        # Copy All button
        copy_all_btn = QPushButton("📋 Copy All")
        copy_all_btn.setToolTip("Copy all variables to clipboard")
        copy_all_btn.clicked.connect(self._copy_all)
        layout.addWidget(copy_all_btn)

        # Export button
        export_btn = QPushButton("💾 Export")
        export_btn.setToolTip("Export variables to JSON")
        export_btn.clicked.connect(self._export_variables)
        layout.addWidget(export_btn)

        # Refresh button
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setToolTip("Refresh variable values")
        refresh_btn.clicked.connect(self._refresh_values)
        layout.addWidget(refresh_btn)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.setObjectName("primary")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)

        return footer

    def _apply_stylesheet(self):
        """Apply QSS stylesheet."""
        self.setStyleSheet(QSS_VARIABLE_REFERENCE)

    def _load_variables(self):
        """Load variables from all sources."""
        try:
            self.variables = self.context_builder.get_available_variables(
                chart_window=self.chart_window,
                bot_config=self.bot_config,
                project_vars_path=self.project_vars_path,
            )

            # Add indicators
            for name, value in self.indicators.items():
                var_name = f"indicators.{name}"
                self.variables[var_name] = {
                    "description": f"Indicator: {name}",
                    "type": type(value).__name__,
                    "unit": None,
                    "category": "Indicators",
                    "value": value,
                }

            # Add regime
            for name, value in self.regime.items():
                var_name = f"regime.{name}"
                self.variables[var_name] = {
                    "description": f"Regime: {name}",
                    "type": type(value).__name__,
                    "unit": None,
                    "category": "Regime",
                    "value": value,
                }

            self.filtered_variables = self.variables.copy()

            logger.info(f"Loaded {len(self.variables)} variables")

        except Exception as e:
            logger.error(f"Error loading variables: {e}", exc_info=True)
            self.variables = {}
            self.filtered_variables = {}

    def _populate_table(self):
        """Populate table with filtered variables."""
        self.table.setRowCount(0)

        row = 0
        for var_name, var_info in sorted(self.filtered_variables.items()):
            self.table.insertRow(row)

            # Variable name
            name_item = QTableWidgetItem(var_name)
            name_item.setToolTip(
                f"{var_name}\n"
                f"Type: {var_info.get('type', 'unknown')}\n"
                f"Description: {var_info.get('description', 'N/A')}"
            )
            self.table.setItem(row, 0, name_item)

            # Label (UI description)
            label_text = var_info.get("label") or var_info.get("description", "N/A")
            label_item = QTableWidgetItem(label_text)
            self.table.setItem(row, 1, label_item)

            # Category
            category = var_info.get("category", "Unknown")
            category_item = QTableWidgetItem(category)
            self.table.setItem(row, 2, category_item)

            # Type
            var_type = var_info.get("type", "unknown")
            type_item = QTableWidgetItem(var_type)
            self.table.setItem(row, 3, type_item)

            # Value
            value = var_info.get("value")
            unit = var_info.get("unit")

            # Format value for display
            if value is None:
                value_text = "—"  # Em dash for undefined
                value_item = QTableWidgetItem(value_text)
                value_item.setForeground(QBrush(QColor(TEXT_SECONDARY)))  # Dimmed
            elif isinstance(value, bool):
                value_text = "✓" if value else "✗"
                value_item = QTableWidgetItem(value_text)
            elif isinstance(value, float):
                # Format floats with appropriate precision
                if unit == "%":
                    value_text = f"{value:.2f}{unit}"
                else:
                    value_text = f"{value:.6f}" if abs(value) < 0.01 else f"{value:.2f}"
                    if unit:
                        value_text += unit
                value_item = QTableWidgetItem(value_text)
            elif isinstance(value, int):
                value_text = str(value)
                if unit:
                    value_text += unit
                value_item = QTableWidgetItem(value_text)
            else:
                value_text = str(value)
                if unit and not str(value).endswith(unit):
                    value_text += unit
                value_item = QTableWidgetItem(value_text)

            value_item.setToolTip(f"Value: {value_text}\nType: {var_info.get('type', 'unknown')}")
            self.table.setItem(row, 4, value_item)

            # Copy button
            copy_btn = QPushButton("📋")
            copy_btn.setProperty("class", "icon-btn")
            copy_btn.setToolTip(f"Copy {var_name}")
            copy_btn.clicked.connect(
                lambda checked, name=var_name, val=value_text: self._copy_variable(name, val)
            )
            self.table.setCellWidget(row, 5, copy_btn)

            row += 1

        # Update status
        self._update_status()

    def _on_search_changed(self, text: str):
        """Handle search text change."""
        self._apply_filters()

    def _on_filter_changed(self):
        """Handle filter change."""
        self._apply_filters()

    def _apply_filters(self):
        """Apply search and filters to variables."""
        search_text = self.search_input.text().lower()
        category_filter = self.category_filter.currentText()
        status_filter = self.status_filter.currentText()

        # Filter variables
        self.filtered_variables = {}
        for var_name, var_info in self.variables.items():
            # Search filter
            if search_text and search_text not in var_name.lower():
                if search_text not in var_info.get("description", "").lower():
                    continue

            # Category filter
            if category_filter != "All Categories":
                if var_info.get("category") != category_filter:
                    continue

            # Status filter
            if status_filter == "Defined":
                if var_info.get("value") is None:
                    continue
            elif status_filter == "Undefined":
                if var_info.get("value") is not None:
                    continue

            self.filtered_variables[var_name] = var_info

        # Repopulate table
        self._populate_table()

    def _copy_variable(self, var_name: str, value: str):
        """Copy single variable to clipboard."""
        clipboard = QApplication.clipboard()
        clipboard.setText(var_name)

        self.variable_copied.emit(var_name, value)
        logger.info(f"Copied variable: {var_name}")

        # Visual feedback
        self.status_label.setText(f"✓ Copied: {var_name}")
        QTimer.singleShot(2000, self._update_status)

    def _copy_all(self):
        """Copy all variables to clipboard."""
        lines = []
        for var_name, var_info in sorted(self.filtered_variables.items()):
            value = var_info.get("value")
            if value is not None:
                lines.append(f"{var_name} = {value}")

        text = "\n".join(lines)
        clipboard = QApplication.clipboard()
        clipboard.setText(text)

        logger.info(f"Copied {len(lines)} variables")
        self.status_label.setText(f"✓ Copied {len(lines)} variables")
        QTimer.singleShot(2000, self._update_status)

    def _export_variables(self):
        """Export variables to JSON file."""
        # TODO: Implement JSON export
        logger.info("Export variables (not yet implemented)")
        self.status_label.setText("⚠️ Export not yet implemented")
        QTimer.singleShot(2000, self._update_status)

    def _refresh_values(self):
        """Refresh variable values from sources."""
        self._load_variables()
        self._apply_filters()
        logger.debug("Refreshed variable values")

    def _update_status(self):
        """Update status label."""
        total = len(self.variables)
        filtered = len(self.filtered_variables)

        if filtered == total:
            self.status_label.setText(f"{total} variables")
        else:
            self.status_label.setText(f"{filtered}/{total} variables")

    def set_sources(
        self,
        chart_window: Optional[ChartWindow] = None,
        bot_config: Optional[BotConfig] = None,
        project_vars_path: Optional[str | Path] = None,
        indicators: Optional[Dict[str, Any]] = None,
        regime: Optional[Dict[str, Any]] = None,
    ):
        """Update data sources and reload."""
        if chart_window is not None:
            self.chart_window = chart_window
        if bot_config is not None:
            self.bot_config = bot_config
        if project_vars_path is not None:
            self.project_vars_path = project_vars_path
        if indicators is not None:
            self.indicators = indicators
        if regime is not None:
            self.regime = regime

        self._refresh_values()

    def closeEvent(self, event):
        """Handle close event."""
        # Stop live updates
        if self.update_timer.isActive():
            self.update_timer.stop()

        super().closeEvent(event)
        logger.info("VariableReferenceDialog closed")
