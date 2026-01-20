"""Tab 2: Pattern Integration Widget - Pattern-to-Strategy Mapping UI."""

from __future__ import annotations

from typing import Optional, Dict, List
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QGroupBox, QLabel, QTextEdit, QPushButton, QHeaderView, QMessageBox,
    QComboBox
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QColor
import logging

from src.strategies.strategy_models import (
    PATTERN_STRATEGIES,
    PatternStrategyMapping,
    StrategyType,
    PatternCategory
)
from src.strategies.pattern_strategy_mapper import (
    PatternStrategyMapper,
    TradeSetup
)

logger = logging.getLogger(__name__)


class PatternIntegrationWidget(QWidget):
    """Tab 2: Pattern-to-Strategy Integration with success rates."""

    strategy_selected = pyqtSignal(str, dict)  # (pattern_type, strategy_mapping)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.mapper = PatternStrategyMapper()
        self.selected_pattern_type: Optional[str] = None
        self._setup_ui()
        self._populate_pattern_table()

    def _setup_ui(self):
        """Setup UI with pattern-strategy mapping table - Dark/Orange theme."""
        layout = QVBoxLayout(self)

        # Dark/Orange Theme
        self.setStyleSheet("""
            QWidget {
                background-color: #2d2d2d;
                color: #e0e0e0;
            }
            QGroupBox {
                border: 1px solid #ff6f00;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                color: #e0e0e0;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 5px;
                color: #ffa726;
            }
            QComboBox {
                background-color: #1e1e1e;
                color: #e0e0e0;
                border: 1px solid #404040;
                border-radius: 3px;
                padding: 5px;
            }
            QComboBox:hover {
                border: 1px solid #ff6f00;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #e0e0e0;
            }
            QTableWidget {
                background-color: #1e1e1e;
                alternate-background-color: #252525;
                color: #e0e0e0;
                gridline-color: #404040;
                border: 1px solid #404040;
            }
            QTableWidget::item:selected {
                background-color: #ff6f00;
                color: white;
            }
            QTableWidget::item:hover {
                background-color: #353535;
            }
            QHeaderView::section {
                background-color: #2d2d2d;
                color: #ffa726;
                padding: 5px;
                border: 1px solid #404040;
                font-weight: bold;
            }
            QTextEdit {
                background-color: #1e1e1e;
                color: #e0e0e0;
                border: 1px solid #404040;
                border-radius: 3px;
            }
        """)

        # Header - Dark/Teal Theme
        header = QLabel("🎯 Pattern-Strategy Integration")
        header.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px; color: #ffa726;")
        layout.addWidget(header)

        # Filter by category
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filter by Category:"))
        self.category_filter = QComboBox()
        self.category_filter.addItems([
            "All",
            "REVERSAL",
            "CONTINUATION",
            "SMART_MONEY",
            "BREAKOUT",
            "HARMONIC"
        ])
        self.category_filter.currentTextChanged.connect(self._on_category_changed)
        filter_layout.addWidget(self.category_filter)
        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # Pattern-Strategy Mapping Table
        table_group = QGroupBox("Pattern-Strategy Mappings (Phase 1)")
        table_layout = QVBoxLayout(table_group)

        self.pattern_table = QTableWidget()
        self.pattern_table.setColumnCount(6)
        self.pattern_table.setHorizontalHeaderLabels([
            "Pattern Name",
            "Category",
            "Success Rate",
            "Strategy Type",
            "Avg Profit",
            "Phase"
        ])
        self.pattern_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.pattern_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.pattern_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.pattern_table.setAlternatingRowColors(True)
        self.pattern_table.itemSelectionChanged.connect(self._on_pattern_selected)

        table_layout.addWidget(self.pattern_table)
        layout.addWidget(table_group)

        # Strategy Details
        details_group = QGroupBox("Strategy Details")
        details_layout = QVBoxLayout(details_group)

        self.strategy_details = QTextEdit()
        self.strategy_details.setReadOnly(True)
        self.strategy_details.setMaximumHeight(200)
        details_layout.addWidget(self.strategy_details)

        layout.addWidget(details_group)

        # Trade Setup Preview
        setup_group = QGroupBox("Trade Setup Preview")
        setup_layout = QVBoxLayout(setup_group)

        self.trade_setup_display = QTextEdit()
        self.trade_setup_display.setReadOnly(True)
        self.trade_setup_display.setMaximumHeight(150)
        setup_layout.addWidget(self.trade_setup_display)

        layout.addWidget(setup_group)

        # Action buttons - Dark/Teal Theme (Trading Bot style)
        action_layout = QHBoxLayout()

        self.apply_btn = QPushButton("✓ Apply Strategy")
        self.apply_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 15px;
                background-color: #26a69a;
                color: white;
                border: none;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2bbbad;
            }
            QPushButton:pressed {
                background-color: #00897b;
            }
            QPushButton:disabled {
                background-color: #404040;
                color: #606060;
            }
        """)
        self.apply_btn.setEnabled(False)
        self.apply_btn.clicked.connect(self._on_apply_strategy)
        action_layout.addWidget(self.apply_btn)

        self.export_btn = QPushButton("💾 Export to CEL")
        self.export_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 15px;
                background-color: #2196f3;
                color: white;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #42a5f5;
            }
            QPushButton:pressed {
                background-color: #1976d2;
            }
            QPushButton:disabled {
                background-color: #404040;
                color: #606060;
            }
        """)
        self.export_btn.setEnabled(False)
        self.export_btn.clicked.connect(self._on_export_cel)
        action_layout.addWidget(self.export_btn)

        action_layout.addStretch()
        layout.addLayout(action_layout)

    def _populate_pattern_table(self, category_filter: str = "All"):
        """Populate table with pattern-strategy mappings."""
        self.pattern_table.setRowCount(0)

        # Filter by implementation phase
        phase_1_patterns = {
            k: v for k, v in PATTERN_STRATEGIES.items()
            if v.implementation_phase == 1
        }

        for pattern_type, mapping in phase_1_patterns.items():
            # Apply category filter
            if category_filter != "All" and mapping.category.name != category_filter:
                continue

            row = self.pattern_table.rowCount()
            self.pattern_table.insertRow(row)

            # Pattern Name
            name_item = QTableWidgetItem(mapping.pattern_name)
            name_item.setData(Qt.ItemDataRole.UserRole, pattern_type)  # Store pattern_type
            self.pattern_table.setItem(row, 0, name_item)

            # Category
            category_item = QTableWidgetItem(mapping.category.name)
            category_color = self._get_category_color(mapping.category)
            category_item.setForeground(category_color)
            self.pattern_table.setItem(row, 1, category_item)

            # Success Rate (dark theme compatible colors)
            success_item = QTableWidgetItem(f"{mapping.strategy.success_rate:.1f}%")
            if mapping.strategy.success_rate >= 90:
                success_item.setForeground(QColor("#66bb6a"))  # Light green
            elif mapping.strategy.success_rate >= 85:
                success_item.setForeground(QColor("#9ccc65"))  # Light lime
            else:
                success_item.setForeground(QColor("#ffa726"))  # Orange
            self.pattern_table.setItem(row, 2, success_item)

            # Strategy Type
            self.pattern_table.setItem(row, 3, QTableWidgetItem(mapping.strategy.strategy_type.value))

            # Avg Profit
            self.pattern_table.setItem(row, 4, QTableWidgetItem(mapping.strategy.avg_profit))

            # Phase
            self.pattern_table.setItem(row, 5, QTableWidgetItem(f"Phase {mapping.implementation_phase}"))

        logger.info(f"Populated pattern table with {self.pattern_table.rowCount()} patterns")

    def _get_category_color(self, category: PatternCategory):
        """Get color for pattern category (dark theme compatible)."""
        colors = {
            PatternCategory.REVERSAL: QColor("#5c9eff"),  # Light blue
            PatternCategory.CONTINUATION: QColor("#26a69a"),  # Teal
            PatternCategory.SMART_MONEY: QColor("#4fc3f7"),  # Cyan
            PatternCategory.BREAKOUT: QColor("#ba68c8"),  # Purple
            PatternCategory.HARMONIC: QColor("#ffd54f")  # Yellow
        }
        return colors.get(category, QColor("#e0e0e0"))

    def _on_category_changed(self, category: str):
        """Handle category filter change."""
        self._populate_pattern_table(category)

    def _on_pattern_selected(self):
        """Handle pattern selection - show strategy details."""
        selected_rows = self.pattern_table.selectionModel().selectedRows()
        if not selected_rows:
            self.strategy_details.clear()
            self.trade_setup_display.clear()
            self.apply_btn.setEnabled(False)
            self.export_btn.setEnabled(False)
            return

        row = selected_rows[0].row()
        pattern_type = self.pattern_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        self.selected_pattern_type = pattern_type

        mapping = PATTERN_STRATEGIES[pattern_type]

        # Display strategy details
        details = self._format_strategy_details(mapping)
        self.strategy_details.setHtml(details)

        # Generate trade setup preview
        setup_preview = self._generate_trade_setup_preview(mapping)
        self.trade_setup_display.setHtml(setup_preview)

        # Enable action buttons
        self.apply_btn.setEnabled(True)
        self.export_btn.setEnabled(True)

        # Store selected strategy for bot integration (Enhancement 4)
        self._selected_pattern_type = pattern_type
        self._selected_strategy = mapping.dict()

        # Emit signal
        self.strategy_selected.emit(pattern_type, mapping.dict())

        logger.info(f"Selected pattern: {mapping.pattern_name}")

    def _format_strategy_details(self, mapping: PatternStrategyMapping) -> str:
        """Format strategy details as HTML (dark theme compatible)."""
        strategy = mapping.strategy

        html = f"""
        <h3 style="color: #ffa726;">{mapping.pattern_name}</h3>
        <p><b>Category:</b> {mapping.category.name}</p>
        <p><b>Success Rate:</b> <span style="color: #66bb6a; font-weight: bold;">{strategy.success_rate:.1f}%</span></p>
        <p><b>Strategy:</b> {strategy.strategy_type.value}</p>
        <p><b>Average Profit:</b> {strategy.avg_profit}</p>
        <p><b>Risk-Reward:</b> {strategy.risk_reward_ratio}</p>

        <h4 style="color: #ffa726;">Best Practices:</h4>
        <ul>
        """

        for practice in strategy.best_practices:
            html += f"<li>{practice}</li>"

        html += f"""
        </ul>

        <h4 style="color: #ffa726;">Entry/Exit Rules:</h4>
        <p><b>Stop Loss:</b> {strategy.stop_loss_placement}</p>
        <p><b>Target:</b> {strategy.target_calculation}</p>
        """

        if strategy.volume_confirmation:
            html += "<p style='color: #66bb6a;'>✓ <b>Volume Confirmation Required</b></p>"

        if strategy.rsi_condition:
            html += f"<p style='color: #5c9eff;'>📊 <b>RSI Condition:</b> {strategy.rsi_condition}</p>"

        if strategy.macd_confirmation:
            html += "<p style='color: #5c9eff;'>📈 <b>MACD Confirmation Required</b></p>"

        return html

    def _generate_trade_setup_preview(self, mapping: PatternStrategyMapping) -> str:
        """Generate trade setup preview (simplified)."""
        html = f"""
        <h4>Trade Setup Template</h4>
        <p><i>Example for {mapping.pattern_name} pattern detected at current price:</i></p>
        <table border="1" cellpadding="5" style="border-collapse: collapse;">
        <tr>
            <td><b>Entry Price</b></td>
            <td>Breakout confirmation level</td>
        </tr>
        <tr>
            <td><b>Stop Loss</b></td>
            <td>{mapping.strategy.stop_loss_placement}</td>
        </tr>
        <tr>
            <td><b>Target Price</b></td>
            <td>{mapping.strategy.target_calculation}</td>
        </tr>
        <tr>
            <td><b>Risk-Reward</b></td>
            <td>{mapping.strategy.risk_reward_ratio}</td>
        </tr>
        <tr>
            <td><b>Expected Success</b></td>
            <td>{mapping.strategy.success_rate:.1f}%</td>
        </tr>
        </table>

        <p><i>Actual entry/stop/target levels require pattern geometry analysis.</i></p>
        """
        return html

    def _on_apply_strategy(self):
        """Apply selected strategy (integrate with bot/analyzer)."""
        if not self.selected_pattern_type:
            return

        mapping = PATTERN_STRATEGIES[self.selected_pattern_type]

        QMessageBox.information(
            self,
            "Apply Strategy",
            f"Applying {mapping.pattern_name} strategy...\n\n"
            f"Integration with Trading Bot coming in Phase 6."
        )

    def _on_export_cel(self):
        """Export strategy to CEL-compatible format."""
        if not self.selected_pattern_type:
            return

        mapping = PATTERN_STRATEGIES[self.selected_pattern_type]

        # TODO: Generate CEL rules from strategy
        QMessageBox.information(
            self,
            "Export to CEL",
            f"Exporting {mapping.pattern_name} to CEL format...\n\n"
            f"CEL export functionality coming in Phase 4."
        )

    def update_patterns(self, patterns: List):
        """Update widget with detected patterns (called from Tab 1)."""
        # TODO: Implement pattern highlighting in table
        logger.info(f"Received {len(patterns)} detected patterns from Tab 1")
