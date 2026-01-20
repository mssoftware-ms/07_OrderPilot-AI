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

QDRANT_CONTAINER_NAME = "orderpilot-qdrant"  # Separate container for OrderPilot
QDRANT_IMAGE = "qdrant/qdrant:latest"
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6335"))  # Port 6335 for OrderPilot (6333 is RAG)
COLLECTION_NAME = "trading_patterns"


class PatternDbLifecycleMixin:
    """PatternDbLifecycleMixin extracted from PatternDatabaseDialog."""
    def closeEvent(self, event):
        """Handle dialog close."""
        self._status_timer.stop()
        if self._build_worker and self._build_worker.isRunning():
            self._build_worker.cancel()
            self._build_worker.wait(3000)
        super().closeEvent(event)
