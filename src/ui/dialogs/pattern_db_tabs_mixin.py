"""Pattern Database Dialog Tabs Mixin.

Contains tab creation methods for PatternDatabaseDialog:
- _create_status_tab: Docker status and DB stats
- _create_build_tab: Symbol selection and build options
- _create_search_tab: Search test interface
"""

from __future__ import annotations

import os
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from src.core.pattern_db.fetcher import CRYPTO_SYMBOLS

DEFAULT_STOCK_SYMBOLS = ["QQQ"]

# Constants (OrderPilot uses Port 6335, RAG uses 6333)
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6335"))
COLLECTION_NAME = "trading_patterns"


class PatternDbTabsMixin:
    """Mixin providing tab creation methods for PatternDatabaseDialog."""

    def _create_status_tab(self) -> QWidget:
        """Create the status tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Docker Status Group
        docker_group = QGroupBox("Docker Qdrant Status")
        docker_layout = QGridLayout(docker_group)

        self.docker_status_label = QLabel("Checking...")
        self.docker_status_label.setFont(QFont("Consolas", 10))
        docker_layout.addWidget(QLabel("Status:"), 0, 0)
        docker_layout.addWidget(self.docker_status_label, 0, 1)

        self.docker_container_label = QLabel("-")
        docker_layout.addWidget(QLabel("Container:"), 1, 0)
        docker_layout.addWidget(self.docker_container_label, 1, 1)

        # Docker control buttons
        docker_btn_layout = QHBoxLayout()
        self.start_docker_btn = QPushButton("Start Qdrant")
        self.start_docker_btn.clicked.connect(self._start_docker)
        docker_btn_layout.addWidget(self.start_docker_btn)

        self.stop_docker_btn = QPushButton("Stop Qdrant")
        self.stop_docker_btn.clicked.connect(self._stop_docker)
        docker_btn_layout.addWidget(self.stop_docker_btn)

        self.restart_docker_btn = QPushButton("Restart")
        self.restart_docker_btn.clicked.connect(self._restart_docker)
        docker_btn_layout.addWidget(self.restart_docker_btn)

        docker_btn_layout.addStretch()
        docker_layout.addLayout(docker_btn_layout, 2, 0, 1, 2)

        layout.addWidget(docker_group)

        # Collection Stats Group
        stats_group = QGroupBox("Pattern Database Statistics")
        stats_layout = QGridLayout(stats_group)

        self.collection_name_label = QLabel("-")
        stats_layout.addWidget(QLabel("Collection:"), 0, 0)
        stats_layout.addWidget(self.collection_name_label, 0, 1)

        self.patterns_count_label = QLabel("-")
        self.patterns_count_label.setFont(QFont("Consolas", 12, QFont.Weight.Bold))
        stats_layout.addWidget(QLabel("Total Patterns:"), 1, 0)
        stats_layout.addWidget(self.patterns_count_label, 1, 1)

        self.collection_status_label = QLabel("-")
        stats_layout.addWidget(QLabel("Collection Status:"), 2, 0)
        stats_layout.addWidget(self.collection_status_label, 2, 1)

        refresh_btn = QPushButton("Refresh Stats")
        refresh_btn.clicked.connect(self._refresh_stats)
        stats_layout.addWidget(refresh_btn, 3, 0, 1, 2)

        layout.addWidget(stats_group)

        # Info/Help
        info_group = QGroupBox("Information")
        info_layout = QVBoxLayout(info_group)
        info_text = QLabel(
            "The Pattern Database stores historical trading patterns as vectors.\n"
            "Similar patterns are matched using cosine similarity to validate trading signals.\n\n"
            f"Uses existing Qdrant Docker instance (RAG-System)\n"
            f"Collection: {COLLECTION_NAME}\n"
            f"Qdrant Port: {QDRANT_PORT}"
        )
        info_text.setWordWrap(True)
        info_layout.addWidget(info_text)
        layout.addWidget(info_group)

        layout.addStretch()
        return widget

    def _create_build_tab(self) -> QWidget:
        """Create the build database tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        layout.addWidget(self._build_asset_group())
        layout.addWidget(self._build_settings_group())
        layout.addWidget(self._build_progress_group())

        return widget

    def _build_asset_group(self) -> QGroupBox:
        asset_group = QGroupBox("Asset Selection")
        asset_layout = QVBoxLayout(asset_group)
        asset_layout.addLayout(self._build_asset_type_layout())
        asset_layout.addLayout(self._build_symbol_lists_layout())
        return asset_group

    def _build_asset_type_layout(self) -> QHBoxLayout:
        type_layout = QHBoxLayout()
        self.stock_radio = QCheckBox("Stocks / ETFs")
        self.stock_radio.setChecked(True)
        type_layout.addWidget(self.stock_radio)

        self.crypto_radio = QCheckBox("Crypto (BTC, ETH)")
        self.crypto_radio.setChecked(True)
        type_layout.addWidget(self.crypto_radio)
        type_layout.addStretch()
        return type_layout

    def _build_symbol_lists_layout(self) -> QHBoxLayout:
        lists_layout = QHBoxLayout()
        stock_box = self._build_stock_list_box()
        crypto_box = self._build_crypto_list_box()
        lists_layout.addLayout(stock_box)
        lists_layout.addLayout(crypto_box)
        return lists_layout

    def _build_stock_list_box(self) -> QVBoxLayout:
        stock_box = QVBoxLayout()
        stock_box.addWidget(QLabel("Stock Symbols:"))
        self.stock_list = QListWidget()
        self.stock_list.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        for symbol in DEFAULT_STOCK_SYMBOLS:
            item = QListWidgetItem(symbol)
            item.setSelected(True)
            self.stock_list.addItem(item)
        stock_box.addWidget(self.stock_list)

        stock_box.addLayout(self._build_stock_buttons_layout())
        stock_box.addLayout(self._build_custom_stock_layout())
        return stock_box

    def _build_stock_buttons_layout(self) -> QHBoxLayout:
        stock_btns = QHBoxLayout()
        select_all_stocks = QPushButton("All")
        select_all_stocks.clicked.connect(lambda: self._select_all(self.stock_list, True))
        stock_btns.addWidget(select_all_stocks)
        select_none_stocks = QPushButton("None")
        select_none_stocks.clicked.connect(lambda: self._select_all(self.stock_list, False))
        stock_btns.addWidget(select_none_stocks)
        remove_selected_stocks = QPushButton("Remove Selected")
        remove_selected_stocks.clicked.connect(self._remove_selected_stocks)
        stock_btns.addWidget(remove_selected_stocks)
        clear_stocks = QPushButton("Clear List")
        clear_stocks.clicked.connect(self._clear_stock_list)
        stock_btns.addWidget(clear_stocks)
        return stock_btns

    def _build_custom_stock_layout(self) -> QHBoxLayout:
        add_stock_layout = QHBoxLayout()
        self.custom_stock_input = QLineEdit()
        self.custom_stock_input.setPlaceholderText(
            "Add stock/index (e.g., AAPL, SPY, QQQ, ^NDX)"
        )
        add_stock_layout.addWidget(self.custom_stock_input)
        add_stock_btn = QPushButton("+")
        add_stock_btn.setMaximumWidth(30)
        add_stock_btn.clicked.connect(self._add_custom_stock)
        add_stock_layout.addWidget(add_stock_btn)
        return add_stock_layout

    def _build_crypto_list_box(self) -> QVBoxLayout:
        crypto_box = QVBoxLayout()
        crypto_box.addWidget(QLabel("Crypto Symbols:"))
        self.crypto_list = QListWidget()
        self.crypto_list.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        for symbol in CRYPTO_SYMBOLS:
            item = QListWidgetItem(symbol)
            item.setSelected(True)
            self.crypto_list.addItem(item)
        for symbol in ["SOL/USD", "DOGE/USD", "AVAX/USD", "LINK/USD"]:
            item = QListWidgetItem(symbol)
            item.setSelected(False)
            self.crypto_list.addItem(item)
        crypto_box.addWidget(self.crypto_list)

        crypto_box.addLayout(self._build_custom_crypto_layout())
        crypto_box.addLayout(self._build_crypto_buttons_layout())
        return crypto_box

    def _build_custom_crypto_layout(self) -> QHBoxLayout:
        add_crypto_layout = QHBoxLayout()
        self.custom_crypto_input = QLineEdit()
        self.custom_crypto_input.setPlaceholderText("Add custom (e.g., ADA/USD)")
        add_crypto_layout.addWidget(self.custom_crypto_input)
        add_crypto_btn = QPushButton("+")
        add_crypto_btn.setMaximumWidth(30)
        add_crypto_btn.clicked.connect(self._add_custom_crypto)
        add_crypto_layout.addWidget(add_crypto_btn)
        return add_crypto_layout

    def _build_crypto_buttons_layout(self) -> QHBoxLayout:
        crypto_btns = QHBoxLayout()
        select_all_crypto = QPushButton("All")
        select_all_crypto.clicked.connect(lambda: self._select_all(self.crypto_list, True))
        crypto_btns.addWidget(select_all_crypto)
        select_none_crypto = QPushButton("None")
        select_none_crypto.clicked.connect(lambda: self._select_all(self.crypto_list, False))
        crypto_btns.addWidget(select_none_crypto)
        remove_selected_crypto = QPushButton("Remove Selected")
        remove_selected_crypto.clicked.connect(self._remove_selected_crypto)
        crypto_btns.addWidget(remove_selected_crypto)
        clear_crypto = QPushButton("Clear List")
        clear_crypto.clicked.connect(self._clear_crypto_list)
        crypto_btns.addWidget(clear_crypto)
        return crypto_btns

    def _build_settings_group(self) -> QGroupBox:
        settings_group = QGroupBox("Timeframes & Settings")
        settings_layout = QGridLayout(settings_group)
        settings_layout.addWidget(QLabel("Timeframes:"), 0, 0)
        settings_layout.addLayout(self._build_timeframe_layout(), 0, 1)
        settings_layout.addWidget(QLabel("Days of History:"), 1, 0)
        self.days_spin = QSpinBox()
        self.days_spin.setRange(30, 1825)
        self.days_spin.setValue(365)
        self.days_spin.setSuffix(" days")
        settings_layout.addWidget(self.days_spin, 1, 1)

        settings_layout.addWidget(QLabel("Pattern Window:"), 2, 0)
        self.window_spin = QSpinBox()
        self.window_spin.setRange(10, 100)
        self.window_spin.setValue(20)
        self.window_spin.setSuffix(" bars")
        settings_layout.addWidget(self.window_spin, 2, 1)

        settings_layout.addWidget(QLabel("Step Size:"), 3, 0)
        self.step_spin = QSpinBox()
        self.step_spin.setRange(1, 20)
        self.step_spin.setValue(5)
        self.step_spin.setSuffix(" bars")
        self.step_spin.setToolTip("Higher = fewer patterns, faster build")
        settings_layout.addWidget(self.step_spin, 3, 1)
        return settings_group

    def _build_timeframe_layout(self) -> QHBoxLayout:
        tf_layout = QHBoxLayout()
        self.tf_1min = QCheckBox("1Min")
        self.tf_1min.setChecked(True)
        tf_layout.addWidget(self.tf_1min)
        self.tf_5min = QCheckBox("5Min")
        self.tf_5min.setChecked(True)
        tf_layout.addWidget(self.tf_5min)
        self.tf_15min = QCheckBox("15Min")
        self.tf_15min.setChecked(True)
        tf_layout.addWidget(self.tf_15min)
        self.tf_30min = QCheckBox("30Min")
        tf_layout.addWidget(self.tf_30min)
        self.tf_1hour = QCheckBox("1Hour")
        tf_layout.addWidget(self.tf_1hour)
        tf_layout.addStretch()
        return tf_layout

    def _build_progress_group(self) -> QGroupBox:
        progress_group = QGroupBox("Build Progress")
        progress_layout = QVBoxLayout(progress_group)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_bar)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        self.log_text.setFont(QFont("Consolas", 9))
        progress_layout.addWidget(self.log_text)

        progress_layout.addLayout(self._build_controls_layout())
        return progress_group

    def _build_controls_layout(self) -> QHBoxLayout:
        btn_layout = QHBoxLayout()
        self.build_btn = QPushButton("Build Database")
        self.build_btn.clicked.connect(self._start_build)
        btn_layout.addWidget(self.build_btn)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(self._cancel_build)
        btn_layout.addWidget(self.cancel_btn)

        self.clear_db_btn = QPushButton("Clear Database")
        self.clear_db_btn.clicked.connect(self._clear_database)
        btn_layout.addWidget(self.clear_db_btn)

        btn_layout.addStretch()
        return btn_layout

    def _create_search_tab(self) -> QWidget:
        """Create the search test tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        info_label = QLabel(
            "Test pattern search functionality.\n"
            "This simulates how the trading bot will query similar patterns."
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        # Search parameters
        search_group = QGroupBox("Search Parameters")
        search_layout = QGridLayout(search_group)

        search_layout.addWidget(QLabel("Symbol:"), 0, 0)
        self.search_symbol = QComboBox()
        self.search_symbol.setEditable(True)
        self.search_symbol.addItems(["AAPL", "MSFT", "NVDA", "BTC/USD", "ETH/USD"])
        search_layout.addWidget(self.search_symbol, 0, 1)

        search_layout.addWidget(QLabel("Timeframe:"), 1, 0)
        self.search_timeframe = QComboBox()
        self.search_timeframe.addItems(["1Min", "5Min", "15Min"])
        search_layout.addWidget(self.search_timeframe, 1, 1)

        search_layout.addWidget(QLabel("Trend Filter:"), 2, 0)
        self.search_trend = QComboBox()
        self.search_trend.addItems(["Any", "up", "down", "sideways"])
        search_layout.addWidget(self.search_trend, 2, 1)

        search_layout.addWidget(QLabel("Min Similarity:"), 3, 0)
        self.search_threshold = QSpinBox()
        self.search_threshold.setRange(50, 99)
        self.search_threshold.setValue(75)
        self.search_threshold.setSuffix("%")
        search_layout.addWidget(self.search_threshold, 3, 1)

        layout.addWidget(search_group)

        # Search button
        search_btn = QPushButton("Search Similar Patterns (Last 20 Bars)")
        search_btn.clicked.connect(self._run_search_test)
        layout.addWidget(search_btn)

        # Results
        results_group = QGroupBox("Search Results")
        results_layout = QVBoxLayout(results_group)

        self.search_results = QTextEdit()
        self.search_results.setReadOnly(True)
        self.search_results.setFont(QFont("Consolas", 9))
        results_layout.addWidget(self.search_results)

        layout.addWidget(results_group)

        return widget
