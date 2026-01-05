"""Tab 2: Timeframe Configuration."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, 
    QHeaderView, QPushButton, QHBoxLayout
)
from src.core.analysis.context import AnalysisContext
from src.core.analysis.models import TimeframeConfig

class TimeframesTab(QWidget):
    """UI for configuring analysis timeframes."""

    def __init__(self, context: AnalysisContext):
        super().__init__()
        self.context = context
        self.context.timeframes_changed.connect(self._update_table)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Rolle", "Timeframe", "Lookback (Bars)", "Quelle"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        # Placeholder functionality for manual edits
        self.reset_btn = QPushButton("Zurücksetzen")
        self.reset_btn.clicked.connect(self._request_reload)
        btn_layout.addWidget(self.reset_btn)
        layout.addLayout(btn_layout)

    def _update_table(self, timeframes: list[TimeframeConfig]):
        self.table.setRowCount(0)
        for tf in timeframes:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(tf.role))
            self.table.setItem(row, 1, QTableWidgetItem(tf.tf))
            self.table.setItem(row, 2, QTableWidgetItem(str(tf.lookback)))
            self.table.setItem(row, 3, QTableWidgetItem(tf.provider))

    def _request_reload(self):
        """Reloads from current strategy default."""
        self.context.apply_auto_config()
