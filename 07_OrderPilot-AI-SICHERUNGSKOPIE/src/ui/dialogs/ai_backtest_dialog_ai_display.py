"""AI Backtest Dialog AI Display - AI Analysis Formatting and Display.

Refactored from ai_backtest_dialog.py.

Contains:
- display_ai_analysis: Main method to format and display AI review
- _add_section: Helper for title + content sections
- _add_list_section: Helper for bullet-point lists with color
- _add_dict_section: Helper for dictionary data as form layout
- _create_improvement_widget: Helper for improvement cards
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from src.ai.openai_service import BacktestReview

if TYPE_CHECKING:
    from .ai_backtest_dialog import AIBacktestDialog


class AIBacktestDialogAIDisplay:
    """Helper for AI analysis display."""

    def __init__(self, parent: "AIBacktestDialog"):
        self.parent = parent

    def display_ai_analysis(self, review: BacktestReview):
        """Display AI analysis results."""
        # Clear previous content
        for i in reversed(range(self.parent.ai_layout.count())):
            self.parent.ai_layout.itemAt(i).widget().setParent(None)

        # Overall Assessment
        self._add_section("📊 Overall Assessment", review.overall_assessment)

        # Performance Rating
        rating_widget = QWidget()
        rating_layout = QHBoxLayout(rating_widget)
        rating_label = QLabel(f"⭐ Performance Rating:")
        rating_value = QLabel(f"{review.performance_rating:.1f}/10")
        rating_value.setStyleSheet(
            "font-size: 24px; font-weight: bold; color: #4CAF50;"
        )
        rating_layout.addWidget(rating_label)
        rating_layout.addWidget(rating_value)
        rating_layout.addStretch()
        self.parent.ai_layout.addWidget(rating_widget)

        # Adaptability Score
        adapt_widget = QWidget()
        adapt_layout = QHBoxLayout(adapt_widget)
        adapt_label = QLabel(f"🎯 Adaptability Score:")
        adapt_value = QLabel(f"{review.adaptability_score:.1%}")
        adapt_value.setStyleSheet("font-size: 20px; font-weight: bold; color: #2196F3;")
        adapt_layout.addWidget(adapt_label)
        adapt_layout.addWidget(adapt_value)
        adapt_layout.addStretch()
        self.parent.ai_layout.addWidget(adapt_widget)

        # Strengths
        self._add_list_section("💪 Strengths", review.strengths, "#4CAF50")

        # Weaknesses
        self._add_list_section("⚠️ Weaknesses", review.weaknesses, "#FF9800")

        # Suggested Improvements
        improvements_group = QGroupBox("🔧 Suggested Improvements")
        improvements_layout = QVBoxLayout()

        for i, improvement in enumerate(review.suggested_improvements, 1):
            imp_widget = self._create_improvement_widget(i, improvement)
            improvements_layout.addWidget(imp_widget)

        improvements_group.setLayout(improvements_layout)
        self.parent.ai_layout.addWidget(improvements_group)

        # Parameter Recommendations
        if review.parameter_recommendations:
            self._add_dict_section("📈 Parameter Recommendations",
                                   review.parameter_recommendations)

        # Risk Assessment
        self._add_section("⚖️ Risk Assessment", review.risk_assessment)

        # Drawdown Analysis
        self._add_section("📉 Max Drawdown Analysis", review.max_drawdown_analysis)

        # Market Conditions
        self._add_section("🌍 Market Conditions", review.market_conditions_analysis)

        self.parent.ai_layout.addStretch()

    def _add_section(self, title: str, content: str):
        """Add a section with title and content."""
        group = QGroupBox(title)
        layout = QVBoxLayout()

        text = QLabel(content)
        text.setWordWrap(True)
        text.setStyleSheet("padding: 10px; font-size: 12px;")
        layout.addWidget(text)

        group.setLayout(layout)
        self.parent.ai_layout.addWidget(group)

    def _add_list_section(self, title: str, items: list[str], color: str):
        """Add a section with a bullet-point list."""
        group = QGroupBox(title)
        layout = QVBoxLayout()

        for item in items:
            label = QLabel(f"• {item}")
            label.setWordWrap(True)
            label.setStyleSheet(f"padding: 5px; color: {color}; font-size: 12px;")
            layout.addWidget(label)

        group.setLayout(layout)
        self.parent.ai_layout.addWidget(group)

    def _add_dict_section(self, title: str, data: dict):
        """Add a section displaying dictionary data."""
        group = QGroupBox(title)
        layout = QFormLayout()

        for key, value in data.items():
            layout.addRow(f"{key}:", QLabel(str(value)))

        group.setLayout(layout)
        self.parent.ai_layout.addWidget(group)

    def _create_improvement_widget(self, index: int, improvement: dict) -> QWidget:
        """Create widget for improvement suggestion."""
        widget = QGroupBox(f"Improvement #{index}")
        layout = QVBoxLayout()

        # Improvement text
        imp_text = QLabel(improvement.get("improvement", "N/A"))
        imp_text.setWordWrap(True)
        imp_text.setStyleSheet("font-weight: bold; padding: 5px;")
        layout.addWidget(imp_text)

        # Impact
        impact_label = QLabel(f"Expected Impact: {improvement.get('expected_impact', 'N/A')}")
        impact_label.setStyleSheet("padding: 5px; color: #4CAF50;")
        layout.addWidget(impact_label)

        # Difficulty
        difficulty = improvement.get("implementation_difficulty", "medium")
        color = {"easy": "#4CAF50", "medium": "#FF9800", "hard": "#F44336"}.get(difficulty, "#888")
        diff_label = QLabel(f"Difficulty: {difficulty.upper()}")
        diff_label.setStyleSheet(f"padding: 5px; color: {color}; font-weight: bold;")
        layout.addWidget(diff_label)

        widget.setLayout(layout)
        return widget
