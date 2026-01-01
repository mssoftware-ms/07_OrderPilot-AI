"""Indicators Widget.

Provides UI for managing and configuring technical indicators.
"""

import logging

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
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

logger = logging.getLogger(__name__)


class IndicatorsWidget(QWidget):
    """Widget for managing technical indicators."""

    def __init__(self):
        """Initialize indicators widget."""
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        """Setup the UI components."""
        layout = QVBoxLayout(self)

        layout.addWidget(self._build_available_group())
        layout.addWidget(self._build_settings_group())
        layout.addWidget(self._build_info_group())

        layout.addStretch()

        logger.info("IndicatorsWidget initialized")

    def _build_available_group(self) -> QGroupBox:
        available_group = QGroupBox("Available Indicators")
        available_layout = QVBoxLayout()

        self.indicators_list = QTableWidget()
        self.indicators_list.setColumnCount(4)
        self.indicators_list.setHorizontalHeaderLabels(
            ["Indicator", "Type", "Parameters", "Enabled"]
        )
        self.indicators_list.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )

        self._populate_indicators_table()
        available_layout.addWidget(self.indicators_list)
        available_layout.addLayout(self._build_indicator_controls())
        available_group.setLayout(available_layout)
        return available_group

    def _populate_indicators_table(self) -> None:
        indicators = [
            ("SMA", "Trend", "period=20", True),
            ("EMA", "Trend", "period=20", False),
            ("RSI", "Momentum", "period=14", True),
            ("MACD", "Trend", "fast=12,slow=26,signal=9", True),
            ("BB", "Volatility", "period=20,std=2", False),
            ("ATR", "Volatility", "period=14", False),
            ("STOCH", "Momentum", "k=14,d=3", False),
            ("ADX", "Trend", "period=14", False),
            ("CCI", "Momentum", "period=20", False),
            ("MFI", "Momentum", "period=14", False),
        ]

        self.indicators_list.setRowCount(len(indicators))
        for i, (name, ind_type, params, enabled) in enumerate(indicators):
            self.indicators_list.setItem(i, 0, QTableWidgetItem(name))
            self.indicators_list.setItem(i, 1, QTableWidgetItem(ind_type))
            self.indicators_list.setItem(i, 2, QTableWidgetItem(params))

            check_item = QTableWidgetItem()
            check_item.setFlags(
                Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled
            )
            check_item.setCheckState(
                Qt.CheckState.Checked if enabled else Qt.CheckState.Unchecked
            )
            self.indicators_list.setItem(i, 3, check_item)

    def _build_indicator_controls(self) -> QHBoxLayout:
        add_indicator_layout = QHBoxLayout()

        self.indicator_type_combo = QComboBox()
        self.indicator_type_combo.addItems(
            ["SMA", "EMA", "RSI", "MACD", "BB", "ATR", "STOCH", "ADX", "CCI", "MFI"]
        )
        add_indicator_layout.addWidget(self.indicator_type_combo)

        self.indicator_params_edit = QLineEdit()
        self.indicator_params_edit.setPlaceholderText("Parameters (e.g., period=20)")
        add_indicator_layout.addWidget(self.indicator_params_edit)

        self.add_indicator_button = QPushButton("Add Indicator")
        self.add_indicator_button.clicked.connect(self._add_indicator)
        add_indicator_layout.addWidget(self.add_indicator_button)

        self.remove_indicator_button = QPushButton("Remove Selected")
        self.remove_indicator_button.clicked.connect(self._remove_indicator)
        add_indicator_layout.addWidget(self.remove_indicator_button)

        return add_indicator_layout

    def _build_settings_group(self) -> QGroupBox:
        settings_group = QGroupBox("Indicator Settings")
        settings_layout = QVBoxLayout()

        self.use_talib_check = QCheckBox("Use TA-Lib (if available)")
        self.use_talib_check.setChecked(True)
        self.use_talib_check.setToolTip(
            "Use TA-Lib library for faster indicator calculations when available"
        )
        settings_layout.addWidget(self.use_talib_check)

        self.cache_indicators_check = QCheckBox("Cache Indicator Results")
        self.cache_indicators_check.setChecked(True)
        self.cache_indicators_check.setToolTip(
            "Cache calculated indicator values to improve performance"
        )
        settings_layout.addWidget(self.cache_indicators_check)

        settings_group.setLayout(settings_layout)
        return settings_group

    def _build_info_group(self) -> QGroupBox:
        info_group = QGroupBox("Information")
        info_layout = QVBoxLayout()

        info_text = QLabel(
            "Technical indicators help analyze price movements and identify trading opportunities.\n\n"
            "• Trend indicators: SMA, EMA, MACD, ADX\n"
            "• Momentum indicators: RSI, STOCH, CCI, MFI\n"
            "• Volatility indicators: BB (Bollinger Bands), ATR\n\n"
            "Enable indicators in the chart view to visualize them alongside price data."
        )
        info_text.setWordWrap(True)
        info_layout.addWidget(info_text)

        info_group.setLayout(info_layout)
        return info_group

    def _add_indicator(self):
        """Add a new indicator."""
        ind_type = self.indicator_type_combo.currentText()
        params = self.indicator_params_edit.text()

        row = self.indicators_list.rowCount()
        self.indicators_list.insertRow(row)

        self.indicators_list.setItem(row, 0, QTableWidgetItem(ind_type))
        self.indicators_list.setItem(row, 1, QTableWidgetItem("Custom"))
        self.indicators_list.setItem(row, 2, QTableWidgetItem(params))

        check_item = QTableWidgetItem()
        check_item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
        check_item.setCheckState(Qt.CheckState.Checked)
        self.indicators_list.setItem(row, 3, check_item)

        self.indicator_params_edit.clear()

        logger.info(f"Added indicator: {ind_type} with params: {params}")

    def _remove_indicator(self):
        """Remove selected indicator."""
        current_row = self.indicators_list.currentRow()
        if current_row >= 0:
            indicator_name = self.indicators_list.item(current_row, 0).text()
            self.indicators_list.removeRow(current_row)
            logger.info(f"Removed indicator: {indicator_name}")
