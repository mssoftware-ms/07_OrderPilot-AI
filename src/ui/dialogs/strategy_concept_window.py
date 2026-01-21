"""Strategy Concept Window - Main dialog for pattern-based strategy development.

Combines Pattern Recognition (Tab 1) and Pattern Integration (Tab 2) workflows.
"""

from __future__ import annotations

from typing import Optional, TYPE_CHECKING
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QPushButton, QLabel
)
from PyQt6.QtCore import Qt, pyqtSignal
import logging

from src.ui.widgets.pattern_recognition_widget import PatternRecognitionWidget
from src.ui.widgets.pattern_integration_widget import PatternIntegrationWidget
from src.ui.widgets.cel_strategy_editor_widget import CelStrategyEditorWidget

if TYPE_CHECKING:
    from src.ui.widgets.chart_window import ChartWindow

logger = logging.getLogger(__name__)


class StrategyConceptWindow(QDialog):
    """Main window for Pattern-Based Strategy Development.

    Features:
    - Tab 1: Pattern Recognition (detect patterns in current chart)
    - Tab 2: Pattern Integration (map patterns to trading strategies)
    - Tab 3: CEL Strategy Editor (develop custom CEL-based strategies with JSON load/save)
    - Cross-tab communication (detected patterns → strategy suggestions)
    """

    # Signals
    strategy_applied = pyqtSignal(str, dict)  # (pattern_type, strategy_config)
    closed = pyqtSignal()

    def __init__(self, parent: Optional['ChartWindow'] = None):
        """Initialize Strategy Concept Window.

        Args:
            parent: Chart window (for data access)
        """
        super().__init__(parent)
        self.chart_window = parent
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Setup main window UI."""
        self.setWindowTitle("Strategy Concept - Pattern-Based Trading")
        self.setMinimumSize(1150, 850)

        # Set window flags for normal window (with minimize/maximize buttons)
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowMinimizeButtonHint |
            Qt.WindowType.WindowMaximizeButtonHint |
            Qt.WindowType.WindowCloseButtonHint
        )

        layout = QVBoxLayout(self)

        # Set dark background for entire dialog
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e1e;
                color: #e0e0e0;
            }
        """)

        # Header - Dark/Teal Theme (Trading Bot style)
        header = QLabel("📊 Strategy Concept - Pattern Recognition & Integration")
        header.setStyleSheet(
            "font-size: 18px; font-weight: bold; padding: 15px; "
            "background-color: #2d2d2d; color: #ffa726; border-radius: 5px; border: 1px solid #404040;"
        )
        layout.addWidget(header)

        # Tab Widget - Dark/Teal Theme (Trading Bot style)
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #404040;
                background: #2d2d2d;
            }
            QTabBar::tab {
                background: #1e1e1e;
                color: #b0b0b0;
                padding: 10px 20px;
                margin: 2px;
                border: 1px solid #404040;
                border-bottom: none;
                border-radius: 5px 5px 0 0;
            }
            QTabBar::tab:selected {
                background: #2d2d2d;
                color: #ffa726;
                border-bottom: 2px solid #26a69a;
                font-weight: bold;
            }
            QTabBar::tab:hover {
                background: #353535;
                color: #26a69a;
            }
        """)

        # Tab 1: Pattern Recognition
        self.pattern_recognition = PatternRecognitionWidget(
            parent=self,
            chart_window=self.chart_window
        )
        self.tabs.addTab(self.pattern_recognition, "🔍 Pattern Recognition")

        # Tab 2: Pattern Integration
        self.pattern_integration = PatternIntegrationWidget(parent=self)
        self.tabs.addTab(self.pattern_integration, "🎯 Pattern Integration")

        # Tab 3: CEL Strategy Editor
        self.cel_strategy_editor = CelStrategyEditorWidget(parent=self)
        self.tabs.addTab(self.cel_strategy_editor, "📝 CEL Strategy Editor")

        layout.addWidget(self.tabs)

        # Footer Actions
        footer_layout = QHBoxLayout()

        self.info_label = QLabel("Welcome! Start by analyzing patterns or browse the pattern library.")
        self.info_label.setStyleSheet("color: #b0b0b0; padding: 5px;")
        footer_layout.addWidget(self.info_label)

        footer_layout.addStretch()

        # Apply to Bot button - Dark/Teal Theme (Trading Bot style)
        self.apply_to_bot_btn = QPushButton("🤖 Apply to Bot")
        self.apply_to_bot_btn.setStyleSheet(
            """
            QPushButton {
                padding: 8px 20px;
                font-size: 14px;
                background-color: #26a69a;
                color: white;
                border: none;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2bbbad;
            }
            QPushButton:pressed {
                background-color: #00897b;
            }
            """
        )
        self.apply_to_bot_btn.setToolTip(
            "Apply selected strategy to Trading Bot for automated execution"
        )
        self.apply_to_bot_btn.clicked.connect(self._on_apply_to_bot_clicked)
        footer_layout.addWidget(self.apply_to_bot_btn)

        self.close_btn = QPushButton("Close")
        self.close_btn.setStyleSheet(
            """
            QPushButton {
                padding: 8px 20px;
                font-size: 14px;
                background-color: #404040;
                color: #e0e0e0;
                border: 1px solid #606060;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #505050;
                border: 1px solid #ff6f00;
            }
            QPushButton:pressed {
                background-color: #303030;
            }
            """
        )
        self.close_btn.clicked.connect(self.accept)
        footer_layout.addWidget(self.close_btn)

        layout.addLayout(footer_layout)

    def _connect_signals(self):
        """Connect signals between tabs."""
        # Tab 1 → Tab 2: When patterns detected, notify Tab 2
        self.pattern_recognition.patterns_detected.connect(
            self._on_patterns_detected
        )

        # Tab 1: When analysis completed, update info label
        self.pattern_recognition.analysis_completed.connect(
            self._on_analysis_completed
        )

        # Tab 2: When strategy selected, emit to parent
        self.pattern_integration.strategy_selected.connect(
            self._on_strategy_selected
        )

    def _on_patterns_detected(self, patterns: list):
        """Handle patterns detected from Tab 1.

        Args:
            patterns: List of detected Pattern objects
        """
        logger.info(f"Patterns detected: {len(patterns)}")

        # Update info label
        if patterns:
            self.info_label.setText(
                f"✓ {len(patterns)} pattern(s) detected. Switch to Pattern Integration to map strategies."
            )
            self.info_label.setStyleSheet("color: #26a69a; padding: 5px; font-weight: bold;")

            # Notify Tab 2
            self.pattern_integration.update_patterns(patterns)
        else:
            self.info_label.setText("No patterns detected. Try adjusting analysis settings.")
            self.info_label.setStyleSheet("color: #ffa726; padding: 5px;")

    def _on_analysis_completed(self, analysis):
        """Handle analysis completion from Tab 1.

        Args:
            analysis: PatternAnalysis object
        """
        logger.info(f"Analysis completed: {analysis.similar_patterns_count} matches")

        # Update info label with match statistics
        self.info_label.setText(
            f"📊 Found {analysis.similar_patterns_count} similar patterns. "
            f"Win Rate: {analysis.win_rate:.1%}, Avg Return: {analysis.avg_return:.1f}%"
        )
        self.info_label.setStyleSheet("color: #26a69a; padding: 5px;")

    def _on_strategy_selected(self, pattern_type: str, strategy: dict):
        """Handle strategy selection from Tab 2.

        Args:
            pattern_type: Pattern type identifier
            strategy: Strategy configuration dict
        """
        logger.info(f"Strategy selected: {pattern_type}")

        # Update info label
        pattern_name = strategy.get('pattern_name', pattern_type)
        success_rate = strategy.get('strategy', {}).get('success_rate', 0)

        self.info_label.setText(
            f"✓ Strategy selected: {pattern_name} (Success Rate: {success_rate:.1f}%)"
        )
        self.info_label.setStyleSheet("color: #26a69a; padding: 5px; font-weight: bold;")

        # Emit to parent
        self.strategy_applied.emit(pattern_type, strategy)

    def show_pattern_recognition_tab(self):
        """Switch to Pattern Recognition tab (Tab 1)."""
        self.tabs.setCurrentIndex(0)

    def show_pattern_integration_tab(self):
        """Switch to Pattern Integration tab (Tab 2)."""
        self.tabs.setCurrentIndex(1)

    def show_cel_strategy_editor_tab(self):
        """Switch to CEL Strategy Editor tab (Tab 3)."""
        self.tabs.setCurrentIndex(2)

    def _on_apply_to_bot_clicked(self):
        """Handle Apply to Bot button click (Enhancement 4: Bot Integration)."""
        # Delegate to parent chart widget's bot integration method
        parent_chart = self.parent()
        if hasattr(parent_chart, 'show_bot_integration_dialog'):
            parent_chart.show_bot_integration_dialog()
        else:
            logger.warning("Parent chart does not have bot integration support")
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(
                self,
                "Bot Integration Not Available",
                "Bot integration is not available in this context."
            )

    def closeEvent(self, event):
        """Handle window close event.

        Args:
            event: Close event
        """
        logger.info("Strategy Concept Window closing")
        self.closed.emit()
        super().closeEvent(event)
