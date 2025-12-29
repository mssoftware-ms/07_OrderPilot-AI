"""Parameter Optimization Dialog Tabs Mixin.

Contains tab creation methods for ParameterOptimizationDialog.
"""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QCheckBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QProgressBar,
    QScrollArea,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class OptimizationTabsMixin:
    """Mixin providing tab creation methods for ParameterOptimizationDialog."""

    def _create_config_tab(self) -> QWidget:
        """Create configuration tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Strategy Selection
        strategy_group = QGroupBox("Strategy")
        strategy_layout = QFormLayout()

        self.strategy_combo = QComboBox()
        self.strategy_combo.addItems([
            "SMA Crossover",
            "RSI Mean Reversion",
            "MACD Momentum"
        ])
        strategy_layout.addRow("Strategy:", self.strategy_combo)

        self.symbol_edit = QLineEdit()
        self.symbol_edit.setText(self.current_symbol.upper() if self.current_symbol else "AAPL")
        strategy_layout.addRow("Symbol:", self.symbol_edit)

        strategy_group.setLayout(strategy_layout)
        layout.addWidget(strategy_group)

        # Parameter Ranges
        param_group = QGroupBox("Parameter Ranges to Optimize")
        param_layout = QFormLayout()

        # Fast Period
        fast_label = QLabel("Fast Period:")
        fast_widget = QWidget()
        fast_layout = QHBoxLayout(fast_widget)
        fast_layout.setContentsMargins(0, 0, 0, 0)

        self.fast_min = QSpinBox()
        self.fast_min.setRange(5, 50)
        self.fast_min.setValue(10)
        self.fast_min.setPrefix("Min: ")
        fast_layout.addWidget(self.fast_min)

        self.fast_max = QSpinBox()
        self.fast_max.setRange(5, 50)
        self.fast_max.setValue(20)
        self.fast_max.setPrefix("Max: ")
        fast_layout.addWidget(self.fast_max)

        self.fast_step = QSpinBox()
        self.fast_step.setRange(1, 10)
        self.fast_step.setValue(5)
        self.fast_step.setPrefix("Step: ")
        fast_layout.addWidget(self.fast_step)

        param_layout.addRow(fast_label, fast_widget)

        # Slow Period
        slow_label = QLabel("Slow Period:")
        slow_widget = QWidget()
        slow_layout = QHBoxLayout(slow_widget)
        slow_layout.setContentsMargins(0, 0, 0, 0)

        self.slow_min = QSpinBox()
        self.slow_min.setRange(20, 100)
        self.slow_min.setValue(40)
        self.slow_min.setPrefix("Min: ")
        slow_layout.addWidget(self.slow_min)

        self.slow_max = QSpinBox()
        self.slow_max.setRange(20, 100)
        self.slow_max.setValue(60)
        self.slow_max.setPrefix("Max: ")
        slow_layout.addWidget(self.slow_max)

        self.slow_step = QSpinBox()
        self.slow_step.setRange(5, 20)
        self.slow_step.setValue(10)
        self.slow_step.setPrefix("Step: ")
        slow_layout.addWidget(self.slow_step)

        param_layout.addRow(slow_label, slow_widget)

        # Stop Loss
        sl_label = QLabel("Stop Loss %:")
        sl_widget = QWidget()
        sl_layout = QHBoxLayout(sl_widget)
        sl_layout.setContentsMargins(0, 0, 0, 0)

        self.sl_min = QDoubleSpinBox()
        self.sl_min.setRange(0.5, 10.0)
        self.sl_min.setValue(1.5)
        self.sl_min.setSingleStep(0.5)
        self.sl_min.setPrefix("Min: ")
        self.sl_min.setSuffix("%")
        sl_layout.addWidget(self.sl_min)

        self.sl_max = QDoubleSpinBox()
        self.sl_max.setRange(0.5, 10.0)
        self.sl_max.setValue(3.0)
        self.sl_max.setSingleStep(0.5)
        self.sl_max.setPrefix("Max: ")
        self.sl_max.setSuffix("%")
        sl_layout.addWidget(self.sl_max)

        self.sl_step = QDoubleSpinBox()
        self.sl_step.setRange(0.1, 2.0)
        self.sl_step.setValue(0.5)
        self.sl_step.setSingleStep(0.1)
        self.sl_step.setPrefix("Step: ")
        self.sl_step.setSuffix("%")
        sl_layout.addWidget(self.sl_step)

        param_layout.addRow(sl_label, sl_widget)

        param_group.setLayout(param_layout)
        layout.addWidget(param_group)

        # Optimization Settings
        opt_group = QGroupBox("Optimization Settings")
        opt_layout = QFormLayout()

        self.metric_combo = QComboBox()
        self.metric_combo.addItems([
            "Sharpe Ratio",
            "Sortino Ratio",
            "Total Return",
            "Profit Factor"
        ])
        opt_layout.addRow("Optimize For:", self.metric_combo)

        self.ai_guidance = QCheckBox("Enable AI Guidance")
        self.ai_guidance.setChecked(True)
        opt_layout.addRow("AI Guidance:", self.ai_guidance)

        self.iterations_spin = QSpinBox()
        self.iterations_spin.setRange(1, 5)
        self.iterations_spin.setValue(2)
        opt_layout.addRow("AI Iterations:", self.iterations_spin)

        opt_group.setLayout(opt_layout)
        layout.addWidget(opt_group)

        # Combination info
        self.combo_label = QLabel()
        self.combo_label.setStyleSheet("color: #888; font-style: italic; padding: 10px;")
        self._update_combination_count()

        # Connect signals to update count
        for widget in [self.fast_min, self.fast_max, self.fast_step,
                      self.slow_min, self.slow_max, self.slow_step,
                      self.sl_min, self.sl_max, self.sl_step]:
            widget.valueChanged.connect(self._update_combination_count)

        layout.addWidget(self.combo_label)
        layout.addStretch()

        return widget

    def _update_combination_count(self):
        """Update total combination count label."""
        import numpy as np

        fast_count = len(np.arange(
            self.fast_min.value(),
            self.fast_max.value() + 1,
            self.fast_step.value()
        ))

        slow_count = len(np.arange(
            self.slow_min.value(),
            self.slow_max.value() + 1,
            self.slow_step.value()
        ))

        sl_count = len(np.arange(
            self.sl_min.value(),
            self.sl_max.value() + 0.01,
            self.sl_step.value()
        ))

        total = fast_count * slow_count * sl_count

        self.combo_label.setText(
            f"Total combinations to test: {total} "
            f"({fast_count} × {slow_count} × {sl_count})\n"
            f"Estimated time: {total * 0.2:.1f}s (mock backtests)"
        )

    def _create_progress_tab(self) -> QWidget:
        """Create progress monitoring tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        # Status label
        self.status_label = QLabel("Ready to optimize")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("font-size: 14px; padding: 20px;")
        layout.addWidget(self.status_label)

        # Progress log
        self.progress_log = QTextEdit()
        self.progress_log.setReadOnly(True)
        layout.addWidget(self.progress_log)

        return widget

    def _create_results_tab(self) -> QWidget:
        """Create results display tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setPlainText("Run optimization to see results...")

        layout.addWidget(self.results_text)

        return widget

    def _create_ai_tab(self) -> QWidget:
        """Create AI insights tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        self.ai_content = QWidget()
        self.ai_layout = QVBoxLayout(self.ai_content)

        placeholder = QLabel("AI insights will appear here after optimization with AI guidance...")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder.setStyleSheet("color: #888; padding: 40px;")
        self.ai_layout.addWidget(placeholder)

        scroll.setWidget(self.ai_content)
        layout.addWidget(scroll)

        return widget

    def _create_chart_tab(self) -> QWidget:
        """Create chart visualization tab for best result."""
        from src.ui.widgets.backtest_chart_widget import BacktestChartWidget

        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # Info label
        info_label = QLabel("Best parameter set backtest visualization:")
        info_label.setStyleSheet("padding: 10px; font-weight: bold;")
        layout.addWidget(info_label)

        # Add BacktestChartWidget
        self.best_result_chart = BacktestChartWidget()
        layout.addWidget(self.best_result_chart)

        return widget
