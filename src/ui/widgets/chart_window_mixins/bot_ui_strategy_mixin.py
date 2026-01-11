from __future__ import annotations


from PyQt6.QtWidgets import QFormLayout, QGroupBox, QHBoxLayout, QHeaderView, QLabel, QPushButton, QTableWidget, QTextEdit, QVBoxLayout, QWidget

class BotUIStrategyMixin:
    """BotUIStrategyMixin extracted from BotUIPanelsMixin."""
    def _create_strategy_selection_tab(self) -> QWidget:
        """Create daily strategy selection tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # ==================== CURRENT STRATEGY ====================
        current_group = QGroupBox("Current Strategy")
        current_layout = QFormLayout()

        self.active_strategy_label = QLabel("None")
        self.active_strategy_label.setStyleSheet(
            "font-weight: bold; font-size: 14px; color: #26a69a;"
        )
        current_layout.addRow("Active:", self.active_strategy_label)

        self.regime_label = QLabel("Unknown")
        current_layout.addRow("Regime:", self.regime_label)

        self.volatility_label = QLabel("Normal")
        current_layout.addRow("Volatility:", self.volatility_label)

        self.selection_time_label = QLabel("-")
        current_layout.addRow("Selected At:", self.selection_time_label)

        self.next_selection_label = QLabel("-")
        current_layout.addRow("Next Selection:", self.next_selection_label)

        # Issue #2: Add indicator set display
        self.strategy_indicators_label = QLabel("-")
        self.strategy_indicators_label.setStyleSheet("color: #888; font-size: 11px;")
        self.strategy_indicators_label.setWordWrap(True)
        current_layout.addRow("Indicators:", self.strategy_indicators_label)

        current_group.setLayout(current_layout)
        layout.addWidget(current_group)

        # ==================== STRATEGY SCORES ====================
        scores_group = QGroupBox("Strategy Scores")
        scores_layout = QVBoxLayout()

        self.strategy_scores_table = QTableWidget()
        self.strategy_scores_table.setColumnCount(5)
        self.strategy_scores_table.setHorizontalHeaderLabels([
            "Strategy", "Score", "PF", "WinRate", "MaxDD"
        ])
        self.strategy_scores_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self.strategy_scores_table.setAlternatingRowColors(True)
        self.strategy_scores_table.setMaximumHeight(200)
        scores_layout.addWidget(self.strategy_scores_table)

        scores_group.setLayout(scores_layout)
        layout.addWidget(scores_group)

        # ==================== WALK-FORWARD RESULTS ====================
        wf_group = QGroupBox("Walk-Forward Results")
        wf_layout = QVBoxLayout()

        self.wf_results_text = QTextEdit()
        self.wf_results_text.setReadOnly(True)
        self.wf_results_text.setMaximumHeight(150)
        self.wf_results_text.setPlaceholderText(
            "Walk-forward evaluation results will appear here..."
        )
        wf_layout.addWidget(self.wf_results_text)

        wf_group.setLayout(wf_layout)
        layout.addWidget(wf_group)

        # Manual override button
        override_layout = QHBoxLayout()
        self.force_reselect_btn = QPushButton("Force Re-Selection")
        self.force_reselect_btn.clicked.connect(self._on_force_reselect)
        override_layout.addWidget(self.force_reselect_btn)
        override_layout.addStretch()
        layout.addLayout(override_layout)

        layout.addStretch()
        return widget
