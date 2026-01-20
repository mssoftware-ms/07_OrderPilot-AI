from __future__ import annotations

import asyncio
import json
import logging
import os
import subprocess
from datetime import datetime
from typing import Optional

from PyQt6.QtCore import Qt, QTimer, QSettings
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QPushButton,
    QTabWidget,
    QMessageBox,
    QListWidget,
    QListWidgetItem,
)

from .pattern_db_tabs_mixin import PatternDbTabsMixin
from .pattern_db_worker import DatabaseBuildWorker

logger = logging.getLogger(__name__)

QDRANT_CONTAINER_NAME = "orderpilot-qdrant"
QDRANT_IMAGE = "qdrant/qdrant:latest"
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6335"))
COLLECTION_NAME = "trading_patterns"


class PatternDbUIMixin:
    """PatternDbUIMixin extracted from PatternDatabaseDialog."""
    def _setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)

        # Create tab widget
        tabs = QTabWidget()
        layout.addWidget(tabs)

        # Tab 1: Status & Docker
        status_tab = self._create_status_tab()
        tabs.addTab(status_tab, "Status")

        # Tab 2: Build Database
        build_tab = self._create_build_tab()
        tabs.addTab(build_tab, "Build Database")

        # Tab 3: Search Test
        search_tab = self._create_search_tab()
        tabs.addTab(search_tab, "Search Test")

        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)
    def _select_all(self, list_widget: QListWidget, select: bool):
        """Select or deselect all items in a list."""
        for i in range(list_widget.count()):
            list_widget.item(i).setSelected(select)
    def _add_custom_crypto(self):
        """Add a custom crypto symbol."""
        symbol = self.custom_crypto_input.text().strip().upper()
        if symbol and "/" in symbol:
            # Check if already exists
            for i in range(self.crypto_list.count()):
                if self.crypto_list.item(i).text() == symbol:
                    return
            from PyQt6.QtWidgets import QListWidgetItem
            item = QListWidgetItem(symbol)
            item.setSelected(True)
            self.crypto_list.addItem(item)
            self.custom_crypto_input.clear()
    def _add_custom_stock(self):
        """Add a custom stock or index symbol."""
        symbol = self.custom_stock_input.text().strip().upper()
        if not symbol:
            return
        for i in range(self.stock_list.count()):
            if self.stock_list.item(i).text() == symbol:
                return
        from PyQt6.QtWidgets import QListWidgetItem
        item = QListWidgetItem(symbol)
        item.setSelected(True)
        self.stock_list.addItem(item)
        self.custom_stock_input.clear()
    def _remove_selected_stocks(self):
        """Remove selected stock symbols from list."""
        for item in self.stock_list.selectedItems():
            row = self.stock_list.row(item)
            self.stock_list.takeItem(row)
    def _clear_stock_list(self):
        """Clear all stock symbols."""
        self.stock_list.clear()
    def _remove_selected_crypto(self):
        """Remove selected crypto symbols from list."""
        for item in self.crypto_list.selectedItems():
            row = self.crypto_list.row(item)
            self.crypto_list.takeItem(row)
    def _clear_crypto_list(self):
        """Clear all crypto symbols."""
        self.crypto_list.clear()
    def _load_initial_state(self):
        """Load initial state on dialog open."""
        self._update_docker_status()
        self._refresh_stats()
        self._load_ui_settings()
