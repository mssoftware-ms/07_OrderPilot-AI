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


class PatternDbLogMixin:
    """PatternDbLogMixin extracted from PatternDatabaseDialog."""
    def _log(self, message: str):
        """Add message to log."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        # Scroll to bottom
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )
    def _clear_database(self):
        """Clear the entire database."""
        result = QMessageBox.warning(
            self,
            "Clear Database",
            "This will delete ALL patterns from the database.\n\nAre you sure?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if result != QMessageBox.StandardButton.Yes:
            return

        try:
            async def clear():
                from src.core.pattern_db.qdrant_client import TradingPatternDB
                db = TradingPatternDB()
                return await db.delete_collection()

            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            success = loop.run_until_complete(clear())

            if success:
                self._log("Database cleared successfully")
                self._refresh_stats()
            else:
                self._log("Failed to clear database")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to clear database:\n{e}")
