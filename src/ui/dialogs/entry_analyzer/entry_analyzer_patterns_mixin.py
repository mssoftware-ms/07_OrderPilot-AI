"""Entry Analyzer - Pattern Detection Tab.

Uses pattern detectors (pivot-based + smart money) on current candles.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, List, Dict

import pandas as pd
from PyQt6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QComboBox,
)

from src.analysis.patterns.pivot_engine import detect_pivots_percent, Pivot
from src.analysis.patterns.reversal_patterns import HeadAndShouldersDetector, DoubleTopBottomDetector
from src.analysis.patterns.continuation_patterns import TriangleDetector, FlagDetector
from src.analysis.patterns.smart_money import detect_order_blocks, detect_fvg

logger = logging.getLogger(__name__)


class PatternDetectionMixin:
    _candles: List[Dict]
    _symbol: str
    _timeframe: str

    def _setup_pattern_tab(self, tab: QWidget) -> None:
        layout = QVBoxLayout(tab)

        ctrl = QHBoxLayout()
        ctrl.addWidget(QLabel("ZigZag Threshold %"))
        self._pat_threshold = QComboBox()
        self._pat_threshold.addItems(["0.5", "1.0", "2.0"])
        self._pat_threshold.setCurrentIndex(1)
        ctrl.addWidget(self._pat_threshold)

        run_btn = QPushButton("Detect Patterns")
        run_btn.clicked.connect(self._on_run_patterns)
        ctrl.addWidget(run_btn)
        ctrl.addStretch()
        layout.addLayout(ctrl)

        self._pat_table = QTableWidget()
        self._pat_table.setColumnCount(4)
        self._pat_table.setHorizontalHeaderLabels(["Pattern", "Score", "Info", "Source"])
        layout.addWidget(self._pat_table)

        layout.addStretch()

    def _on_run_patterns(self) -> None:
        df = self._get_current_df()
        if df is None or df.empty:
            return

        threshold = float(self._pat_threshold.currentText())
        pivots = detect_pivots_percent(df["close"], threshold_pct=threshold)

        detectors = [
            HeadAndShouldersDetector(),
            DoubleTopBottomDetector(),
            TriangleDetector(),
            FlagDetector(),
        ]
        patterns = []
        for det in detectors:
            try:
                pats = det.detect(pivots)
                patterns.extend(pats)
            except Exception as e:
                logger.warning("Pattern detector failed: %s", e)

        # Smart money patterns (use OHLC df)
        try:
            patterns.extend(detect_order_blocks(df))
            patterns.extend(detect_fvg(df))
        except Exception as e:
            logger.warning("SMC detection failed: %s", e)

        self._pat_table.setRowCount(0)
        for p in patterns:
            row = self._pat_table.rowCount()
            self._pat_table.insertRow(row)
            self._pat_table.setItem(row, 0, QTableWidgetItem(p.name))
            self._pat_table.setItem(row, 1, QTableWidgetItem(f"{p.score:.1f}"))
            meta = p.metadata or {}
            info = ", ".join(f"{k}={v}" for k, v in meta.items())
            self._pat_table.setItem(row, 2, QTableWidgetItem(info))
            self._pat_table.setItem(row, 3, QTableWidgetItem("Pivot" if isinstance(p.pivots, list) else "SMC"))

    def _get_current_df(self) -> pd.DataFrame | None:
        candles = getattr(self, "_candles", None) or []
        if not candles:
            return None
        df = pd.DataFrame(candles)
        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            df = df.set_index("timestamp").sort_index()
        return df
