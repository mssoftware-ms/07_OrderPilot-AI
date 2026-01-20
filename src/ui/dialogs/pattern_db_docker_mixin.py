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


class PatternDbDockerMixin:
    """PatternDbDockerMixin extracted from PatternDatabaseDialog."""
    def _update_docker_status(self):
        """Update Docker status display."""
        try:
            # Check if container exists and is running
            result = subprocess.run(
                ["docker", "ps", "-a", "--filter", f"name={QDRANT_CONTAINER_NAME}", "--format", "{{.Status}}"],
                capture_output=True,
                text=True,
                timeout=5,
            )

            status = result.stdout.strip()
            if not status:
                self.docker_status_label.setText("Not Created")
                self.docker_status_label.setStyleSheet("color: gray;")
                self.docker_container_label.setText(f"{QDRANT_CONTAINER_NAME} (not found)")
                self.start_docker_btn.setEnabled(True)
                self.stop_docker_btn.setEnabled(False)
            elif "Up" in status:
                self.docker_status_label.setText(f"Running ({status})")
                self.docker_status_label.setStyleSheet("color: green; font-weight: bold;")
                self.docker_container_label.setText(QDRANT_CONTAINER_NAME)
                self.start_docker_btn.setEnabled(False)
                self.stop_docker_btn.setEnabled(True)
            else:
                self.docker_status_label.setText(f"Stopped ({status})")
                self.docker_status_label.setStyleSheet("color: orange;")
                self.docker_container_label.setText(QDRANT_CONTAINER_NAME)
                self.start_docker_btn.setEnabled(True)
                self.stop_docker_btn.setEnabled(False)

        except subprocess.TimeoutExpired:
            self.docker_status_label.setText("Docker not responding")
            self.docker_status_label.setStyleSheet("color: red;")
        except FileNotFoundError:
            self.docker_status_label.setText("Docker not installed")
            self.docker_status_label.setStyleSheet("color: red;")
        except Exception as e:
            self.docker_status_label.setText(f"Error: {e}")
            self.docker_status_label.setStyleSheet("color: red;")
    def _start_docker(self):
        """Start the existing Qdrant Docker container (from RAG-System)."""
        try:
            # Start the existing container
            subprocess.run(["docker", "start", QDRANT_CONTAINER_NAME], check=True)
            self._log(f"Started Qdrant container: {QDRANT_CONTAINER_NAME}")
            self._log(f"Collection for patterns: {COLLECTION_NAME}")
            self._update_docker_status()

        except subprocess.CalledProcessError as e:
            QMessageBox.critical(
                self,
                "Docker Error",
                f"Failed to start Docker container '{QDRANT_CONTAINER_NAME}'.\n\n"
                f"Make sure the RAG-System Docker stack is set up.\n\n"
                f"Error: {e}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
    def _stop_docker(self):
        """Stop the Qdrant Docker container."""
        try:
            subprocess.run(["docker", "stop", QDRANT_CONTAINER_NAME], check=True)
            self._log("Stopped Qdrant container")
            self._update_docker_status()
        except subprocess.CalledProcessError as e:
            QMessageBox.critical(self, "Docker Error", f"Failed to stop Docker:\n{e}")
    def _restart_docker(self):
        """Restart the Qdrant Docker container."""
        try:
            subprocess.run(["docker", "restart", QDRANT_CONTAINER_NAME], check=True)
            self._log("Restarted Qdrant container")
            self._update_docker_status()
        except subprocess.CalledProcessError as e:
            QMessageBox.critical(self, "Docker Error", f"Failed to restart Docker:\n{e}")
