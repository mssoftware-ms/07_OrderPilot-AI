"""Entry Analyzer - Pattern Recognition Mixin.

Extracted from entry_analyzer_ai.py to keep files under 550 LOC.
Handles historical pattern matching and analysis:
- Pattern Recognition tab with similarity-based search
- Cross-symbol pattern matching
- Win rate and outcome analysis
- Report generation (Markdown/JSON)

Date: 2026-01-21
LOC: ~450
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

# Import icon provider (Issue #12)
from src.ui.icons import get_icon

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class AIPatternsMixin:
    """Pattern Recognition functionality for entry analysis.

    Provides historical pattern matching with:
    - Similarity-based pattern search
    - Cross-symbol pattern database
    - Win rate and outcome statistics
    - Pattern overlay comparison (future)
    - Report generation (Markdown/JSON export)

    Attributes (defined in parent class):
        pattern_window_spin: QSpinBox - Pattern window size
        pattern_similarity_threshold_spin: QDoubleSpinBox - Similarity threshold
        pattern_min_matches_spin: QSpinBox - Min similar patterns
        pattern_signal_direction_combo: QComboBox - LONG/SHORT
        pattern_cross_symbol_cb: QCheckBox - Cross-symbol search
        pattern_analyze_btn: QPushButton - Analyze button
        pattern_progress: QProgressBar - Progress indicator
        pattern_summary_label: QLabel - Summary text
        pattern_matches_count_label: QLabel - Match count
        pattern_win_rate_label: QLabel - Win rate %
        pattern_avg_return_label: QLabel - Avg return %
        pattern_confidence_label: QLabel - Confidence score
        pattern_avg_similarity_label: QLabel - Avg similarity
        pattern_recommendation_label: QLabel - Recommendation
        similar_patterns_table: QTableWidget - Results table
        _result: AnalysisResult | None - Analysis data
        _symbol: str | None - Trading symbol
        _timeframe: str | None - Chart timeframe
        _validation_result: Any | None - Validation data
    """

    # Type hints for parent class attributes
    pattern_window_spin: QSpinBox
    pattern_similarity_threshold_spin: QDoubleSpinBox
    pattern_min_matches_spin: QSpinBox
    pattern_signal_direction_combo: QComboBox
    pattern_cross_symbol_cb: QCheckBox
    pattern_analyze_btn: QPushButton
    pattern_progress: QProgressBar
    pattern_summary_label: QLabel
    pattern_matches_count_label: QLabel
    pattern_win_rate_label: QLabel
    pattern_avg_return_label: QLabel
    pattern_confidence_label: QLabel
    pattern_avg_similarity_label: QLabel
    pattern_recommendation_label: QLabel
    similar_patterns_table: QTableWidget
    _result: Any | None
    _symbol: str | None
    _timeframe: str | None
    _validation_result: Any | None

    def _setup_pattern_recognition_tab(self, tab: QWidget) -> None:
        """Setup Pattern Recognition tab.

        Original: entry_analyzer_popup.py:2813-2942

        Creates:
        - Pattern Analysis Settings (window size, similarity threshold, min matches, signal direction, cross-symbol search)
        - Analyze Current Pattern button
        - Progress bar
        - Pattern Analysis Results (summary, statistics grid)
        - Top Similar Patterns table (8 columns: Symbol, Timeframe, Date, Similarity, Trend, Win, Return %, Outcome)
        - Info label with usage tips

        Uses PatternService to find similar historical patterns and analyze win probability.
        """
        layout = QVBoxLayout(tab)

        # Header
        header_label = QLabel(
            "🔍 Find similar historical patterns to the current chart situation.\n"
            "The system analyzes pattern outcomes to estimate win probability."
        )
        header_label.setWordWrap(True)
        header_label.setStyleSheet("color: #666; font-size: 11px; padding: 5px;")
        layout.addWidget(header_label)

        # Pattern Analysis Settings Group
        settings_group = QGroupBox("Pattern Analysis Settings")
        settings_layout = QFormLayout(settings_group)

        # Window Size
        self.pattern_window_spin = QSpinBox()
        self.pattern_window_spin.setRange(10, 100)
        self.pattern_window_spin.setValue(20)
        self.pattern_window_spin.setToolTip("Number of bars to analyze for pattern matching")
        settings_layout.addRow("Pattern Window Size:", self.pattern_window_spin)

        # Similarity Threshold
        self.pattern_similarity_threshold_spin = QDoubleSpinBox()
        self.pattern_similarity_threshold_spin.setRange(0.5, 0.99)
        self.pattern_similarity_threshold_spin.setSingleStep(0.05)
        self.pattern_similarity_threshold_spin.setValue(0.75)
        self.pattern_similarity_threshold_spin.setToolTip("Minimum similarity score (0.5-0.99)")
        settings_layout.addRow("Similarity Threshold:", self.pattern_similarity_threshold_spin)

        # Min Similar Patterns
        self.pattern_min_matches_spin = QSpinBox()
        self.pattern_min_matches_spin.setRange(3, 50)
        self.pattern_min_matches_spin.setValue(5)
        self.pattern_min_matches_spin.setToolTip("Minimum number of similar patterns needed")
        settings_layout.addRow("Min Similar Patterns:", self.pattern_min_matches_spin)

        # Signal Direction
        self.pattern_signal_direction_combo = QComboBox()
        self.pattern_signal_direction_combo.addItems(["LONG", "SHORT"])
        self.pattern_signal_direction_combo.setCurrentIndex(0)
        settings_layout.addRow("Signal Direction:", self.pattern_signal_direction_combo)

        # Cross-Symbol Search
        self.pattern_cross_symbol_cb = QCheckBox("Search across all symbols")
        self.pattern_cross_symbol_cb.setChecked(True)
        self.pattern_cross_symbol_cb.setToolTip("Search patterns from all symbols (recommended)")
        settings_layout.addRow("", self.pattern_cross_symbol_cb)

        layout.addWidget(settings_group)

        # Analyze Button (Issue #12: Material Design icon + theme color)
        self.pattern_analyze_btn = QPushButton(" Analyze Current Pattern")
        self.pattern_analyze_btn.setIcon(get_icon("psychology"))
        self.pattern_analyze_btn.setProperty("class", "info")  # Use theme info color
        self.pattern_analyze_btn.clicked.connect(self._on_pattern_analyze_clicked)
        layout.addWidget(self.pattern_analyze_btn)

        # Progress bar
        self.pattern_progress = QProgressBar()
        self.pattern_progress.setVisible(False)
        layout.addWidget(self.pattern_progress)

        # Results Group
        results_group = QGroupBox("Pattern Analysis Results")
        results_layout = QVBoxLayout(results_group)

        # Summary Label
        self.pattern_summary_label = QLabel("No analysis performed yet")
        self.pattern_summary_label.setStyleSheet(
            "font-size: 14px; font-weight: bold; padding: 10px; "
            "background-color: #f5f5f5; border-radius: 5px;"
        )
        self.pattern_summary_label.setWordWrap(True)
        results_layout.addWidget(self.pattern_summary_label)

        # Statistics Grid
        stats_grid = QFormLayout()
        self.pattern_matches_count_label = QLabel("-")
        self.pattern_win_rate_label = QLabel("-")
        self.pattern_avg_return_label = QLabel("-")
        self.pattern_confidence_label = QLabel("-")
        self.pattern_avg_similarity_label = QLabel("-")
        self.pattern_recommendation_label = QLabel("-")

        stats_grid.addRow("Similar Patterns Found:", self.pattern_matches_count_label)
        stats_grid.addRow("Win Rate:", self.pattern_win_rate_label)
        stats_grid.addRow("Avg Return:", self.pattern_avg_return_label)
        stats_grid.addRow("Confidence:", self.pattern_confidence_label)
        stats_grid.addRow("Avg Similarity:", self.pattern_avg_similarity_label)
        stats_grid.addRow("Recommendation:", self.pattern_recommendation_label)

        results_layout.addLayout(stats_grid)
        layout.addWidget(results_group)

        # Similar Patterns Table
        patterns_table_group = QGroupBox("Top Similar Patterns")
        patterns_table_layout = QVBoxLayout(patterns_table_group)

        self.similar_patterns_table = QTableWidget()
        self.similar_patterns_table.setColumnCount(8)
        self.similar_patterns_table.setHorizontalHeaderLabels(
            ["Symbol", "Timeframe", "Date", "Similarity", "Trend", "Win", "Return %", "Outcome"]
        )
        self.similar_patterns_table.horizontalHeader().setStretchLastSection(True)
        self.similar_patterns_table.setAlternatingRowColors(True)
        self.similar_patterns_table.setSortingEnabled(True)
        self.similar_patterns_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.similar_patterns_table.itemDoubleClicked.connect(self._on_pattern_double_clicked)

        patterns_table_layout.addWidget(self.similar_patterns_table)
        layout.addWidget(patterns_table_group)

        # Info label
        info_label = QLabel(
            "💡 Tip: Double-click a pattern to see detailed chart comparison. "
            "Higher similarity scores (>0.8) indicate very similar market conditions."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #666; font-size: 10px; padding: 5px;")
        layout.addWidget(info_label)

    def _on_pattern_analyze_clicked(self) -> None:
        """Handle pattern analyze button click.

        Original: entry_analyzer_popup.py:2944-3040

        Process:
        1. Get chart data from parent
        2. Get pattern analysis settings (window size, similarity threshold, etc.)
        3. Convert chart data to HistoricalBar objects
        4. Run pattern analysis with PatternService (async)
        5. Display results with _display_pattern_analysis_results()
        """
        try:
            # Get current chart data
            if not hasattr(self.parent(), "chart_widget") or not hasattr(
                self.parent().chart_widget, "data"
            ):
                QMessageBox.warning(
                    self, "No Data", "No chart data available for pattern analysis."
                )
                return

            chart_data = self.parent().chart_widget.data
            if chart_data is None or len(chart_data) == 0:
                QMessageBox.warning(self, "No Data", "Chart data is empty.")
                return

            # Get settings
            window_size = self.pattern_window_spin.value()
            similarity_threshold = self.pattern_similarity_threshold_spin.value()
            min_matches = self.pattern_min_matches_spin.value()
            signal_direction = self.pattern_signal_direction_combo.currentText().lower()
            cross_symbol = self.pattern_cross_symbol_cb.isChecked()

            # Show progress
            self.pattern_progress.setVisible(True)
            self.pattern_progress.setRange(0, 0)  # Indeterminate
            self.pattern_analyze_btn.setEnabled(False)

            # Convert chart_data to bars
            from src.core.market_data.types import HistoricalBar

            bars = []
            for timestamp, row in chart_data.tail(window_size + 50).iterrows():
                bar = HistoricalBar(
                    timestamp=timestamp,
                    open=float(row["open"]),
                    high=float(row["high"]),
                    low=float(row["low"]),
                    close=float(row["close"]),
                    volume=float(row.get("volume", 0)),
                )
                bars.append(bar)

            # Get symbol and timeframe
            symbol = getattr(self.parent().chart_widget, "current_symbol", "UNKNOWN")
            timeframe = getattr(self.parent().chart_widget, "timeframe", "1m")

            # Run pattern analysis in background
            from src.core.pattern_db.pattern_service import PatternService

            async def run_analysis():
                service = PatternService(
                    window_size=window_size,
                    min_similar_patterns=min_matches,
                    similarity_threshold=similarity_threshold,
                )
                await service.initialize()
                return await service.analyze_signal(
                    bars=bars,
                    symbol=symbol,
                    timeframe=timeframe,
                    signal_direction=signal_direction,
                    cross_symbol_search=cross_symbol,
                )

            # Run in event loop
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Create task
                task = asyncio.create_task(run_analysis())
                # Wait for completion (blocking UI is OK for analysis)
                loop.run_until_complete(task)
                result = task.result()
            else:
                result = loop.run_until_complete(run_analysis())

            # Display results
            self._display_pattern_analysis_results(result)

            # Hide progress
            self.pattern_progress.setVisible(False)
            self.pattern_analyze_btn.setEnabled(True)

        except Exception as e:
            logger.error(f"Pattern analysis failed: {e}", exc_info=True)
            QMessageBox.critical(self, "Analysis Error", f"Pattern analysis failed:\n{e}")
            self.pattern_progress.setVisible(False)
            self.pattern_analyze_btn.setEnabled(True)

    def _display_pattern_analysis_results(self, analysis) -> None:
        """Display pattern analysis results.

        Original: entry_analyzer_popup.py:3042-3101

        Updates:
        - Summary label with color-coded recommendation
        - Statistics labels (matches count, win rate, avg return, confidence, avg similarity)
        - Similar patterns table (top 20 matches)

        Args:
            analysis: PatternAnalysis object or None
        """
        if analysis is None:
            self.pattern_summary_label.setText("❌ Analysis failed - not enough data")
            self.pattern_summary_label.setStyleSheet(
                "font-size: 14px; font-weight: bold; padding: 10px; "
                "background-color: #ffebee; border-radius: 5px;"
            )
            return

        # Update summary
        recommendation_colors = {
            "strong_buy": "#4caf50",
            "buy": "#8bc34a",
            "neutral": "#ffeb3b",
            "avoid": "#ff9800",
            "strong_avoid": "#f44336",
        }
        bg_color = recommendation_colors.get(analysis.recommendation, "#f5f5f5")

        self.pattern_summary_label.setText(
            f"✓ Analysis Complete: {analysis.recommendation.upper().replace('_', ' ')}"
        )
        self.pattern_summary_label.setStyleSheet(
            f"font-size: 14px; font-weight: bold; padding: 10px; "
            f"background-color: {bg_color}; border-radius: 5px; color: white;"
        )

        # Update statistics
        self.pattern_matches_count_label.setText(str(analysis.similar_patterns_count))
        self.pattern_win_rate_label.setText(f"{analysis.win_rate:.1%}")
        self.pattern_avg_return_label.setText(f"{analysis.avg_return:+.2f}%")
        self.pattern_confidence_label.setText(f"{analysis.confidence:.1%}")
        self.pattern_avg_similarity_label.setText(f"{analysis.avg_similarity_score:.2f}")
        self.pattern_recommendation_label.setText(analysis.recommendation.replace("_", " ").title())

        # Update table
        self.similar_patterns_table.setRowCount(0)
        for match in analysis.best_matches[:20]:  # Show top 20
            row = self.similar_patterns_table.rowCount()
            self.similar_patterns_table.insertRow(row)

            self.similar_patterns_table.setItem(row, 0, QTableWidgetItem(match.symbol))
            self.similar_patterns_table.setItem(row, 1, QTableWidgetItem(match.timeframe))
            self.similar_patterns_table.setItem(
                row,
                2,
                QTableWidgetItem(
                    match.timestamp.strftime("%Y-%m-%d %H:%M")
                    if hasattr(match.timestamp, "strftime")
                    else str(match.timestamp)
                ),
            )
            self.similar_patterns_table.setItem(row, 3, QTableWidgetItem(f"{match.score:.3f}"))
            self.similar_patterns_table.setItem(
                row, 4, QTableWidgetItem(match.trend_direction.upper())
            )
            self.similar_patterns_table.setItem(
                row, 5, QTableWidgetItem("✓" if match.was_profitable else "✗")
            )
            self.similar_patterns_table.setItem(
                row, 6, QTableWidgetItem(f"{match.return_pct:+.2f}%")
            )

            outcome = "PROFIT" if match.was_profitable else "LOSS"
            outcome_item = QTableWidgetItem(outcome)
            outcome_item.setForeground(
                Qt.GlobalColor.green if match.was_profitable else Qt.GlobalColor.red
            )
            self.similar_patterns_table.setItem(row, 7, outcome_item)

        logger.info(
            f"Pattern analysis displayed: {analysis.similar_patterns_count} matches, {analysis.win_rate:.1%} win rate"
        )

    def _on_pattern_double_clicked(self, item) -> None:
        """Handle pattern table double-click - show detailed comparison.

        Original: entry_analyzer_popup.py:3103-3118

        Shows message box with pattern details (symbol, date, similarity).
        Future enhancement: Chart overlay comparison.
        """
        row = item.row()
        symbol = self.similar_patterns_table.item(row, 0).text()
        date = self.similar_patterns_table.item(row, 2).text()
        similarity = self.similar_patterns_table.item(row, 3).text()

        QMessageBox.information(
            self,
            "Pattern Details",
            f"Similar Pattern Details:\n\n"
            f"Symbol: {symbol}\n"
            f"Date: {date}\n"
            f"Similarity: {similarity}\n\n"
            f"Feature: Chart overlay comparison coming soon...",
        )

    def _on_report_clicked(self) -> None:
        """Handle report generation button click.

        Original: entry_analyzer_popup.py:3120-3167

        Process:
        1. Check for analysis result
        2. Ask for save location (Markdown/JSON)
        3. Create report data with ReportGenerator
        4. Generate and save report
        5. Show confirmation message
        """
        if not self._result:
            QMessageBox.warning(self, "No Data", "Run analysis first")
            return

        # Ask for save location
        default_name = f"entry_analysis_{self._symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Report",
            str(Path.home() / f"{default_name}.md"),
            "Markdown (*.md);;JSON (*.json);;All Files (*)",
        )

        if not file_path:
            return

        try:
            from src.analysis.visible_chart.report_generator import (
                ReportGenerator,
                create_report_from_analysis,
            )

            # Create report data
            report_data = create_report_from_analysis(
                analysis=self._result,
                symbol=self._symbol,
                timeframe=self._timeframe,
                validation=self._validation_result,
            )

            generator = ReportGenerator()
            path = Path(file_path)

            if path.suffix == ".json":
                content = generator.generate_json(report_data)
                path.write_text(json.dumps(content, indent=2), encoding="utf-8")
            else:
                content = generator.generate_markdown(report_data)
                path.write_text(content, encoding="utf-8")

            QMessageBox.information(self, "Report Saved", f"Report saved to:\n{path}")
            logger.info("Report saved: %s", path)

        except Exception as e:
            logger.exception("Report generation failed")
            QMessageBox.critical(self, "Error", f"Failed to generate report:\n{e}")
