from __future__ import annotations

import asyncio
import json
import logging
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

QDRANT_CONTAINER_NAME = "09_rag-system-ai_cl-qdrant-1"
QDRANT_IMAGE = "qdrant/qdrant"
QDRANT_PORT = 6333
COLLECTION_NAME = "trading_patterns"


class PatternDbSettingsMixin:
    """PatternDbSettingsMixin extracted from PatternDatabaseDialog."""
    def _load_ui_settings(self) -> None:
        """Load saved UI settings for the Pattern DB dialog."""
        try:
            stock_symbols_json = self._settings.value("pattern_db/stock_symbols")
            crypto_symbols_json = self._settings.value("pattern_db/crypto_symbols")
            stock_selected_json = self._settings.value("pattern_db/stock_selected")
            crypto_selected_json = self._settings.value("pattern_db/crypto_selected")

            if stock_symbols_json:
                symbols = json.loads(stock_symbols_json)
                self.stock_list.clear()
                for s in symbols:
                    item = QListWidgetItem(s)
                    self.stock_list.addItem(item)

            if crypto_symbols_json:
                symbols = json.loads(crypto_symbols_json)
                self.crypto_list.clear()
                for s in symbols:
                    item = QListWidgetItem(s)
                    self.crypto_list.addItem(item)

            if stock_selected_json:
                selected = set(json.loads(stock_selected_json))
                for i in range(self.stock_list.count()):
                    item = self.stock_list.item(i)
                    item.setSelected(item.text() in selected)

            if crypto_selected_json:
                selected = set(json.loads(crypto_selected_json))
                for i in range(self.crypto_list.count()):
                    item = self.crypto_list.item(i)
                    item.setSelected(item.text() in selected)

            self.stock_radio.setChecked(
                self._settings.value("pattern_db/stock_enabled", True, type=bool)
            )
            self.crypto_radio.setChecked(
                self._settings.value("pattern_db/crypto_enabled", True, type=bool)
            )

            # Timeframes
            self.tf_1min.setChecked(self._settings.value("pattern_db/tf_1min", True, type=bool))
            self.tf_5min.setChecked(self._settings.value("pattern_db/tf_5min", True, type=bool))
            self.tf_15min.setChecked(self._settings.value("pattern_db/tf_15min", True, type=bool))
            self.tf_30min.setChecked(self._settings.value("pattern_db/tf_30min", False, type=bool))
            self.tf_1hour.setChecked(self._settings.value("pattern_db/tf_1hour", False, type=bool))

            # Numeric inputs
            days = self._settings.value("pattern_db/days_back", None)
            if days is not None:
                self.days_spin.setValue(int(days))
            window = self._settings.value("pattern_db/window_size", None)
            if window is not None:
                self.window_spin.setValue(int(window))
            step = self._settings.value("pattern_db/step_size", None)
            if step is not None:
                self.step_spin.setValue(int(step))

            # Search tab settings
            search_symbol = self._settings.value("pattern_db/search_symbol")
            if search_symbol:
                idx = self.search_symbol.findText(search_symbol)
                if idx >= 0:
                    self.search_symbol.setCurrentIndex(idx)
                else:
                    self.search_symbol.addItem(search_symbol)
                    self.search_symbol.setCurrentText(search_symbol)

            search_timeframe = self._settings.value("pattern_db/search_timeframe")
            if search_timeframe:
                idx = self.search_timeframe.findText(search_timeframe)
                if idx >= 0:
                    self.search_timeframe.setCurrentIndex(idx)

            threshold = self._settings.value("pattern_db/search_threshold", None)
            if threshold is not None:
                self.search_threshold.setValue(float(threshold))

        except Exception as e:
            logger.error(f"Failed to load Pattern DB settings: {e}")
    def _save_ui_settings(self) -> None:
        """Persist UI settings for the Pattern DB dialog."""
        try:
            stock_symbols = [self.stock_list.item(i).text() for i in range(self.stock_list.count())]
            crypto_symbols = [self.crypto_list.item(i).text() for i in range(self.crypto_list.count())]
            stock_selected = [item.text() for item in self.stock_list.selectedItems()]
            crypto_selected = [item.text() for item in self.crypto_list.selectedItems()]

            self._settings.setValue("pattern_db/stock_symbols", json.dumps(stock_symbols))
            self._settings.setValue("pattern_db/crypto_symbols", json.dumps(crypto_symbols))
            self._settings.setValue("pattern_db/stock_selected", json.dumps(stock_selected))
            self._settings.setValue("pattern_db/crypto_selected", json.dumps(crypto_selected))

            self._settings.setValue("pattern_db/stock_enabled", self.stock_radio.isChecked())
            self._settings.setValue("pattern_db/crypto_enabled", self.crypto_radio.isChecked())

            # Timeframes
            self._settings.setValue("pattern_db/tf_1min", self.tf_1min.isChecked())
            self._settings.setValue("pattern_db/tf_5min", self.tf_5min.isChecked())
            self._settings.setValue("pattern_db/tf_15min", self.tf_15min.isChecked())
            self._settings.setValue("pattern_db/tf_30min", self.tf_30min.isChecked())
            self._settings.setValue("pattern_db/tf_1hour", self.tf_1hour.isChecked())

            # Numeric inputs
            self._settings.setValue("pattern_db/days_back", self.days_spin.value())
            self._settings.setValue("pattern_db/window_size", self.window_spin.value())
            self._settings.setValue("pattern_db/step_size", self.step_spin.value())

            # Search tab
            self._settings.setValue("pattern_db/search_symbol", self.search_symbol.currentText())
            self._settings.setValue("pattern_db/search_timeframe", self.search_timeframe.currentText())
            self._settings.setValue("pattern_db/search_threshold", self.search_threshold.value())

        except Exception as e:
            logger.error(f"Failed to save Pattern DB settings: {e}")
    def closeEvent(self, event):
        """Persist settings on close."""
        self._save_ui_settings()
        super().closeEvent(event)
