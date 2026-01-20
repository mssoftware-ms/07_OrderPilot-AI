"""Reusable widgets for pattern analysis (shared between Entry Analyzer and Strategy Concept)."""

from __future__ import annotations

from typing import Optional, Dict, Any
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QSpinBox, QDoubleSpinBox, QComboBox, QCheckBox, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QColor
import logging

logger = logging.getLogger(__name__)


class PatternAnalysisSettings(QWidget):
    """Reusable pattern analysis settings panel."""

    settings_changed = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        """Setup all settings widgets - Dark/Orange theme."""
        layout = QFormLayout(self)

        # Dark/Orange Theme for input widgets
        self.setStyleSheet("""
            QSpinBox, QDoubleSpinBox, QComboBox {
                background-color: #1e1e1e;
                color: #e0e0e0;
                border: 1px solid #404040;
                border-radius: 3px;
                padding: 5px;
            }
            QSpinBox:hover, QDoubleSpinBox:hover, QComboBox:hover {
                border: 1px solid #ff6f00;
            }
            QSpinBox::up-button, QDoubleSpinBox::up-button {
                background-color: #2d2d2d;
                border: 1px solid #404040;
            }
            QSpinBox::down-button, QDoubleSpinBox::down-button {
                background-color: #2d2d2d;
                border: 1px solid #404040;
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
            QCheckBox {
                color: #e0e0e0;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 1px solid #404040;
                border-radius: 3px;
                background-color: #1e1e1e;
            }
            QCheckBox::indicator:checked {
                background-color: #ff6f00;
                border: 1px solid #ff6f00;
            }
            QLabel {
                color: #e0e0e0;
            }
        """)

        # Window size for pattern matching (auto-detected from chart)
        window_size_layout = QVBoxLayout()

        self.window_spin = QSpinBox()
        self.window_spin.setRange(10, 500)
        self.window_spin.setValue(20)
        self.window_spin.setSuffix(" bars")
        self.window_spin.setEnabled(False)  # Disabled - auto-detected from chart
        window_size_layout.addWidget(self.window_spin)

        window_size_note = QLabel("📊 Auto-detected from visible chart")
        window_size_note.setStyleSheet("color: #888; font-size: 10px; font-style: italic;")
        window_size_layout.addWidget(window_size_note)

        layout.addRow("Window Size:", window_size_layout)

        # Similarity threshold (0.5-0.99)
        self.similarity_spin = QDoubleSpinBox()
        self.similarity_spin.setRange(0.5, 0.99)
        self.similarity_spin.setValue(0.80)
        self.similarity_spin.setSingleStep(0.05)
        self.similarity_spin.setDecimals(2)
        self.similarity_spin.valueChanged.connect(self._on_settings_changed)
        layout.addRow("Similarity Threshold:", self.similarity_spin)

        # Minimum matches
        self.min_matches_spin = QSpinBox()
        self.min_matches_spin.setRange(3, 50)
        self.min_matches_spin.setValue(10)
        self.min_matches_spin.valueChanged.connect(self._on_settings_changed)
        layout.addRow("Min Matches:", self.min_matches_spin)

        # Signal direction
        self.direction_combo = QComboBox()
        self.direction_combo.addItems(["LONG", "SHORT"])
        self.direction_combo.currentTextChanged.connect(self._on_settings_changed)
        layout.addRow("Signal Direction:", self.direction_combo)

        # Cross-symbol search
        self.cross_symbol_cb = QCheckBox("Search across symbols")
        self.cross_symbol_cb.stateChanged.connect(self._on_settings_changed)
        layout.addRow("", self.cross_symbol_cb)

        # NEW: Target Timeframe (Phase 2)
        timeframe_layout = QVBoxLayout()

        self.target_timeframe_combo = QComboBox()
        self.target_timeframe_combo.addItems([
            "Auto (from chart)",  # Default: use chart's timeframe
            "1m",
            "5m",
            "10m",
            "15m",
            "30m",
            "1h",
            "4h",
            "1d"
        ])
        self.target_timeframe_combo.setCurrentText("Auto (from chart)")
        self.target_timeframe_combo.currentTextChanged.connect(self._on_settings_changed)
        timeframe_layout.addWidget(self.target_timeframe_combo)

        timeframe_note = QLabel("⏱️ Converts chart bars to target timeframe")
        timeframe_note.setStyleSheet("color: #888; font-size: 10px; font-style: italic;")
        timeframe_layout.addWidget(timeframe_note)

        layout.addRow("Target Timeframe:", timeframe_layout)

        # NEW: Partial Pattern Matching (Phase 3)
        partial_layout = QVBoxLayout()

        self.enable_partial_cb = QCheckBox("Enable Partial Pattern Matching")
        self.enable_partial_cb.setToolTip("Match incomplete patterns (early entry signals)")
        self.enable_partial_cb.stateChanged.connect(self._on_partial_toggle)
        self.enable_partial_cb.stateChanged.connect(self._on_settings_changed)
        partial_layout.addWidget(self.enable_partial_cb)

        # Minimum completion percentage (only shown when partial enabled)
        partial_settings_layout = QHBoxLayout()

        self.min_completion_spin = QSpinBox()
        self.min_completion_spin.setRange(30, 90)  # 30%-90% minimum completion
        self.min_completion_spin.setValue(50)  # Default: 50% minimum
        self.min_completion_spin.setSuffix("%")
        self.min_completion_spin.setToolTip("Minimum pattern completion required")
        self.min_completion_spin.valueChanged.connect(self._on_settings_changed)
        self.min_completion_spin.setEnabled(False)  # Disabled initially

        partial_settings_layout.addWidget(QLabel("Min Completion:"))
        partial_settings_layout.addWidget(self.min_completion_spin)
        partial_settings_layout.addStretch()
        partial_layout.addLayout(partial_settings_layout)

        partial_note = QLabel("⚡ Early entry detection for forming patterns")
        partial_note.setStyleSheet("color: #888; font-size: 10px; font-style: italic;")
        partial_layout.addWidget(partial_note)

        layout.addRow("", partial_layout)

    def _on_partial_toggle(self, state):
        """Enable/disable partial pattern settings."""
        enabled = state == Qt.CheckState.Checked.value
        self.min_completion_spin.setEnabled(enabled)

    def _on_settings_changed(self):
        """Emit settings_changed signal when any setting changes."""
        self.settings_changed.emit(self.get_settings())

    def get_settings(self) -> dict:
        """Return current settings as dict."""
        # Parse target timeframe (None for "Auto")
        target_tf = self.target_timeframe_combo.currentText()
        if target_tf == "Auto (from chart)":
            target_tf = None

        return {
            'window_size': self.window_spin.value(),
            'similarity_threshold': self.similarity_spin.value(),
            'min_matches': self.min_matches_spin.value(),
            'signal_direction': self.direction_combo.currentText().lower(),
            'cross_symbol': self.cross_symbol_cb.isChecked(),
            'target_timeframe': target_tf,  # Phase 2
            'enable_partial': self.enable_partial_cb.isChecked(),  # Phase 3
            'min_completion_pct': self.min_completion_spin.value(),  # Phase 3
        }


class PatternResultsDisplay(QWidget):
    """Reusable pattern analysis results display."""

    # Recommendation color scheme
    RECOMMENDATION_COLORS = {
        "strong_buy": "#4caf50",
        "buy": "#8bc34a",
        "neutral": "#ffeb3b",
        "avoid": "#ff9800",
        "strong_avoid": "#f44336"
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        """Setup results display widgets - Dark/Orange theme."""
        layout = QVBoxLayout(self)

        # Dark theme styling
        self.setStyleSheet("""
            QLabel {
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
        """)

        # Summary label (dark theme)
        self.summary_label = QLabel("No analysis yet")
        self.summary_label.setStyleSheet(
            "font-size: 14px; font-weight: bold; padding: 10px; "
            "background-color: #2d2d2d; border-radius: 5px; color: #b0b0b0;"
        )
        layout.addWidget(self.summary_label)

        # Statistics group
        stats_group = QGroupBox("Statistics")
        stats_layout = QFormLayout(stats_group)

        self.matches_count_label = QLabel("0")
        stats_layout.addRow("Matches Found:", self.matches_count_label)

        self.win_rate_label = QLabel("0%")
        stats_layout.addRow("Win Rate:", self.win_rate_label)

        self.avg_return_label = QLabel("0%")
        stats_layout.addRow("Avg Return:", self.avg_return_label)

        self.confidence_label = QLabel("0%")
        stats_layout.addRow("Confidence:", self.confidence_label)

        self.avg_similarity_label = QLabel("0.00")
        stats_layout.addRow("Avg Similarity:", self.avg_similarity_label)

        self.recommendation_label = QLabel("-")
        stats_layout.addRow("Recommendation:", self.recommendation_label)

        # Phase 3: Partial Pattern Info (hidden by default)
        self.completion_label = QLabel("-")
        self.completion_label.setStyleSheet("color: #ffa726;")  # Orange highlight
        self.completion_row = stats_layout.rowCount()
        stats_layout.addRow("Pattern Completion:", self.completion_label)

        self.projection_label = QLabel("-")
        self.projection_row = stats_layout.rowCount()
        stats_layout.addRow("Projection Method:", self.projection_label)

        self.early_entry_label = QLabel("-")
        self.early_entry_row = stats_layout.rowCount()
        stats_layout.addRow("Early Entry:", self.early_entry_label)

        # Hide partial pattern rows by default
        stats_layout.setRowVisible(self.completion_row, False)
        stats_layout.setRowVisible(self.projection_row, False)
        stats_layout.setRowVisible(self.early_entry_row, False)

        layout.addWidget(stats_group)

    def update_from_analysis(self, analysis) -> None:
        """
        Update display with analysis results.

        Args:
            analysis: PatternAnalysis or PartialPatternAnalysis object or None
        """
        if analysis is None:
            self.summary_label.setText("❌ Analysis failed - not enough data")
            self.summary_label.setStyleSheet(
                "font-size: 14px; font-weight: bold; padding: 10px; "
                "background-color: #3d2020; border-radius: 5px; color: #ff6f6f;"
            )
            return

        # Update summary with color coding
        bg_color = self.RECOMMENDATION_COLORS.get(analysis.recommendation, "#f5f5f5")

        # Phase 3: Check if partial pattern analysis
        is_partial = hasattr(analysis, 'completion_ratio')

        summary_text = f"✓ Analysis Complete: {analysis.recommendation.upper().replace('_', ' ')}"
        if is_partial:
            summary_text = f"⚡ Partial Pattern Analysis: {analysis.recommendation.upper().replace('_', ' ')}"

        self.summary_label.setText(summary_text)
        self.summary_label.setStyleSheet(
            f"font-size: 14px; font-weight: bold; padding: 10px; "
            f"background-color: {bg_color}; border-radius: 5px; color: white;"
        )

        # Update statistics
        self.matches_count_label.setText(str(analysis.similar_patterns_count))
        self.win_rate_label.setText(f"{analysis.win_rate:.1%}")
        self.avg_return_label.setText(f"{analysis.avg_return:+.2f}%")
        self.confidence_label.setText(f"{analysis.confidence:.1%}")
        self.avg_similarity_label.setText(f"{analysis.avg_similarity_score:.2f}")
        self.recommendation_label.setText(analysis.recommendation.replace('_', ' ').title())

        # Phase 3: Update partial pattern specific fields
        if is_partial:
            # Show completion ratio
            completion_text = f"{analysis.bars_formed}/{analysis.bars_required} bars ({analysis.completion_ratio:.1%})"
            self.completion_label.setText(completion_text)

            # Show projection method
            self.projection_label.setText(analysis.projection_method.replace('_', ' ').title())

            # Show early entry opportunity with color coding
            if analysis.early_entry_opportunity:
                self.early_entry_label.setText("✓ YES (High Confidence)")
                self.early_entry_label.setStyleSheet("color: #4caf50; font-weight: bold;")  # Green
            else:
                self.early_entry_label.setText("○ No")
                self.early_entry_label.setStyleSheet("color: #9e9e9e;")  # Gray

            # Show partial pattern rows
            layout = self.findChild(QFormLayout)
            if layout:
                layout.setRowVisible(self.completion_row, True)
                layout.setRowVisible(self.projection_row, True)
                layout.setRowVisible(self.early_entry_row, True)

            logger.info(
                f"Partial pattern analysis displayed: {analysis.bars_formed}/{analysis.bars_required} bars, "
                f"{analysis.similar_patterns_count} matches, {analysis.win_rate:.1%} win rate, "
                f"early_entry={analysis.early_entry_opportunity}"
            )
        else:
            # Hide partial pattern rows for full pattern analysis
            layout = self.findChild(QFormLayout)
            if layout:
                layout.setRowVisible(self.completion_row, False)
                layout.setRowVisible(self.projection_row, False)
                layout.setRowVisible(self.early_entry_row, False)

            logger.info(
                f"Pattern analysis displayed: {analysis.similar_patterns_count} matches, "
                f"{analysis.win_rate:.1%} win rate"
            )

    def clear(self) -> None:
        """Clear all displayed results."""
        self.summary_label.setText("No analysis yet")
        self.summary_label.setStyleSheet(
            "font-size: 14px; font-weight: bold; padding: 10px; "
            "background-color: #2d2d2d; border-radius: 5px; color: #b0b0b0;"
        )
        self.matches_count_label.setText("0")
        self.win_rate_label.setText("0%")
        self.avg_return_label.setText("0%")
        self.confidence_label.setText("0%")
        self.avg_similarity_label.setText("0.00")
        self.recommendation_label.setText("-")

        # Phase 3: Clear and hide partial pattern fields
        self.completion_label.setText("-")
        self.projection_label.setText("-")
        self.early_entry_label.setText("-")
        self.early_entry_label.setStyleSheet("color: #e0e0e0;")  # Reset to default

        layout = self.findChild(QFormLayout)
        if layout:
            layout.setRowVisible(self.completion_row, False)
            layout.setRowVisible(self.projection_row, False)
            layout.setRowVisible(self.early_entry_row, False)


class PatternMatchesTable(QTableWidget):
    """Reusable table for displaying pattern matches."""

    pattern_selected = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_table()

    def _setup_table(self):
        """Setup table structure."""
        self.setColumnCount(8)
        self.setHorizontalHeaderLabels([
            "Symbol",
            "Timeframe",
            "Date",
            "Similarity",
            "Trend",
            "Profitable",
            "Return %",
            "Outcome"
        ])

        # Dark/Orange Table Theme
        self.setStyleSheet("""
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
        """)

        # Table styling
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.setAlternatingRowColors(True)

    def populate_from_matches(self, matches: list, max_rows: int = 20) -> None:
        """
        Populate table with pattern matches.

        Args:
            matches: List of match objects with attributes (symbol, timeframe, timestamp, etc.)
            max_rows: Maximum number of rows to display
        """
        self.setRowCount(0)

        for match in matches[:max_rows]:
            row = self.rowCount()
            self.insertRow(row)

            # Column 0: Symbol
            self.setItem(row, 0, QTableWidgetItem(match.symbol))

            # Column 1: Timeframe
            self.setItem(row, 1, QTableWidgetItem(match.timeframe))

            # Column 2: Date
            date_str = (
                match.timestamp.strftime("%Y-%m-%d %H:%M")
                if hasattr(match.timestamp, 'strftime')
                else str(match.timestamp)
            )
            self.setItem(row, 2, QTableWidgetItem(date_str))

            # Column 3: Similarity
            self.setItem(row, 3, QTableWidgetItem(f"{match.score:.3f}"))

            # Column 4: Trend
            self.setItem(row, 4, QTableWidgetItem(match.trend_direction.upper()))

            # Column 5: Profitable (checkmark/X)
            profitable_str = "✓" if match.was_profitable else "✗"
            self.setItem(row, 5, QTableWidgetItem(profitable_str))

            # Column 6: Return %
            self.setItem(row, 6, QTableWidgetItem(f"{match.return_pct:+.2f}%"))

            # Column 7: Outcome (colored - dark theme compatible)
            outcome = "PROFIT" if match.was_profitable else "LOSS"
            outcome_item = QTableWidgetItem(outcome)
            outcome_item.setForeground(
                QColor("#66bb6a") if match.was_profitable else QColor("#ef5350")
            )
            self.setItem(row, 7, outcome_item)

    def clear_table(self) -> None:
        """Clear all rows from table."""
        self.setRowCount(0)
