"""Performance Monitor Widget for Regime-Based Trading Bot.

Provides real-time visualization of:
    - Regime stability metrics
    - Strategy switching timeline
    - Parameter override tracking
    - Performance degradation detection

Author: Claude Code
Date: 2026-01-20
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

import numpy as np
from PyQt6.QtCore import QTimer, pyqtSignal, Qt
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QGroupBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QComboBox,
    QSpinBox,
)
from PyQt6.QtGui import QColor

try:
    import matplotlib
    matplotlib.use('QtAgg')
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
    from matplotlib.figure import Figure
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

if TYPE_CHECKING:
    from src.core.tradingbot.regime_stability import (
        RegimeStabilityTracker,
        RegimeStabilityMetrics,
    )

logger = logging.getLogger(__name__)


class PerformanceMonitorWidget(QWidget):
    """Real-time performance monitoring widget for regime-based trading.

    Features:
        - Live stability score chart (rolling window)
        - Oscillation detection alerts
        - Transition matrix heatmap
        - Confidence trends over time
        - Strategy switching timeline
        - Parameter override tracking

    Signals:
        stability_alert: Emitted when stability drops below threshold
        oscillation_detected: Emitted when rapid regime switching detected

    Example:
        >>> monitor = PerformanceMonitorWidget()
        >>> monitor.set_stability_tracker(tracker)
        >>> monitor.start_monitoring(update_interval_ms=1000)
    """

    # Signals
    stability_alert = pyqtSignal(float)  # stability_score
    oscillation_detected = pyqtSignal(int)  # oscillation_count

    def __init__(self, parent: QWidget | None = None):
        """Initialize performance monitor widget.

        Args:
            parent: Parent widget (optional)
        """
        super().__init__(parent)

        self._tracker: RegimeStabilityTracker | None = None
        self._update_timer = QTimer()
        self._update_timer.timeout.connect(self._update_metrics)

        # Settings
        self._update_interval_ms = 1000  # 1 second
        self._stability_threshold = 0.7  # Alert if below 70%
        self._lookback_minutes = 60

        # Data storage for charts
        self._timestamps: list[datetime] = []
        self._stability_scores: list[float] = []
        self._confidence_scores: list[float] = []

        self._setup_ui()

        logger.info("PerformanceMonitorWidget initialized")

    def _setup_ui(self):
        """Setup UI components."""
        layout = QVBoxLayout(self)

        # Header with controls
        header = self._create_header()
        layout.addWidget(header)

        # Main content area
        if MATPLOTLIB_AVAILABLE:
            content = self._create_chart_area()
        else:
            content = self._create_table_area()
            logger.warning("Matplotlib not available, using table display")

        layout.addWidget(content)

        # Status bar at bottom
        status_bar = self._create_status_bar()
        layout.addWidget(status_bar)

    def _create_header(self) -> QGroupBox:
        """Create header with controls."""
        group = QGroupBox("Performance Monitor")
        layout = QHBoxLayout(group)

        # Start/Stop button
        self.start_btn = QPushButton("▶ Start Monitoring")
        self.start_btn.clicked.connect(self._toggle_monitoring)
        self.start_btn.setStyleSheet("background-color: #26a69a; color: white;")
        layout.addWidget(self.start_btn)

        # Lookback period selector
        layout.addWidget(QLabel("Lookback:"))
        self.lookback_spin = QSpinBox()
        self.lookback_spin.setRange(10, 240)
        self.lookback_spin.setValue(self._lookback_minutes)
        self.lookback_spin.setSuffix(" min")
        self.lookback_spin.valueChanged.connect(self._on_lookback_changed)
        layout.addWidget(self.lookback_spin)

        # Update interval selector
        layout.addWidget(QLabel("Update:"))
        self.interval_combo = QComboBox()
        self.interval_combo.addItems(["1s", "5s", "10s", "30s", "60s"])
        self.interval_combo.setCurrentText("1s")
        self.interval_combo.currentTextChanged.connect(self._on_interval_changed)
        layout.addWidget(self.interval_combo)

        layout.addStretch()

        # Clear data button
        clear_btn = QPushButton("🗑️ Clear Data")
        clear_btn.clicked.connect(self._clear_data)
        layout.addWidget(clear_btn)

        return group

    def _create_chart_area(self) -> QWidget:
        """Create matplotlib chart area."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Create matplotlib figure with 2x2 subplots
        self.figure = Figure(figsize=(12, 8))
        self.canvas = FigureCanvasQTAgg(self.figure)

        # Create subplots
        self.ax_stability = self.figure.add_subplot(2, 2, 1)
        self.ax_confidence = self.figure.add_subplot(2, 2, 2)
        self.ax_transitions = self.figure.add_subplot(2, 2, 3)
        self.ax_timeline = self.figure.add_subplot(2, 2, 4)

        self.figure.tight_layout(pad=3.0)

        layout.addWidget(self.canvas)

        return widget

    def _create_table_area(self) -> QWidget:
        """Create table-based display (fallback without matplotlib)."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Metrics table
        self.metrics_table = QTableWidget()
        self.metrics_table.setColumnCount(2)
        self.metrics_table.setHorizontalHeaderLabels(["Metric", "Value"])
        self.metrics_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        # Populate initial rows
        metrics = [
            "Stability Score",
            "Avg Confidence",
            "Regime Changes (1h)",
            "Oscillations Detected",
            "Avg Duration (min)",
            "Current Regime",
        ]

        self.metrics_table.setRowCount(len(metrics))
        for i, metric in enumerate(metrics):
            self.metrics_table.setItem(i, 0, QTableWidgetItem(metric))
            self.metrics_table.setItem(i, 1, QTableWidgetItem("--"))

        layout.addWidget(self.metrics_table)

        return widget

    def _create_status_bar(self) -> QWidget:
        """Create status bar with alerts."""
        widget = QWidget()
        layout = QHBoxLayout(widget)

        self.status_label = QLabel("Status: Not monitoring")
        self.status_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(self.status_label)

        layout.addStretch()

        self.alert_label = QLabel("")
        self.alert_label.setStyleSheet("color: red; font-weight: bold;")
        layout.addWidget(self.alert_label)

        return widget

    # Public API

    def set_stability_tracker(self, tracker: RegimeStabilityTracker):
        """Set the regime stability tracker to monitor.

        Args:
            tracker: RegimeStabilityTracker instance
        """
        self._tracker = tracker
        logger.info("Stability tracker set")

    def start_monitoring(self, update_interval_ms: int = 1000):
        """Start real-time monitoring.

        Args:
            update_interval_ms: Update interval in milliseconds
        """
        if self._tracker is None:
            logger.error("Cannot start monitoring: no tracker set")
            self.status_label.setText("Status: Error - No tracker")
            return

        self._update_interval_ms = update_interval_ms
        self._update_timer.start(self._update_interval_ms)

        self.start_btn.setText("⏸ Stop Monitoring")
        self.start_btn.setStyleSheet("background-color: #ef5350; color: white;")
        self.status_label.setText("Status: Monitoring active")

        logger.info(f"Monitoring started (interval: {update_interval_ms}ms)")

    def stop_monitoring(self):
        """Stop real-time monitoring."""
        self._update_timer.stop()

        self.start_btn.setText("▶ Start Monitoring")
        self.start_btn.setStyleSheet("background-color: #26a69a; color: white;")
        self.status_label.setText("Status: Monitoring stopped")

        logger.info("Monitoring stopped")

    def is_monitoring(self) -> bool:
        """Check if monitoring is active.

        Returns:
            True if monitoring, False otherwise
        """
        return self._update_timer.isActive()

    # Private methods

    def _toggle_monitoring(self):
        """Toggle monitoring on/off."""
        if self.is_monitoring():
            self.stop_monitoring()
        else:
            self.start_monitoring(self._update_interval_ms)

    def _on_lookback_changed(self, value: int):
        """Handle lookback period change."""
        self._lookback_minutes = value
        logger.debug(f"Lookback changed to {value} minutes")

    def _on_interval_changed(self, text: str):
        """Handle update interval change."""
        # Parse interval text (e.g., "1s" -> 1000ms)
        interval_map = {
            "1s": 1000,
            "5s": 5000,
            "10s": 10000,
            "30s": 30000,
            "60s": 60000,
        }

        self._update_interval_ms = interval_map.get(text, 1000)

        # Restart timer if monitoring
        if self.is_monitoring():
            self.stop_monitoring()
            self.start_monitoring(self._update_interval_ms)

        logger.debug(f"Update interval changed to {text}")

    def _clear_data(self):
        """Clear all stored data."""
        self._timestamps.clear()
        self._stability_scores.clear()
        self._confidence_scores.clear()

        if MATPLOTLIB_AVAILABLE:
            self._clear_charts()

        logger.info("Data cleared")

    def _update_metrics(self):
        """Update metrics (called by timer)."""
        if self._tracker is None:
            return

        try:
            # Get current metrics
            metrics = self._tracker.get_metrics(lookback_minutes=self._lookback_minutes)

            # Store for charts
            self._timestamps.append(datetime.now())
            self._stability_scores.append(metrics.stability_score)
            self._confidence_scores.append(metrics.avg_confidence)

            # Limit data points (keep last 500)
            if len(self._timestamps) > 500:
                self._timestamps = self._timestamps[-500:]
                self._stability_scores = self._stability_scores[-500:]
                self._confidence_scores = self._confidence_scores[-500:]

            # Update display
            if MATPLOTLIB_AVAILABLE:
                self._update_charts(metrics)
            else:
                self._update_table(metrics)

            # Check for alerts
            self._check_alerts(metrics)

        except Exception as e:
            logger.error(f"Error updating metrics: {e}", exc_info=True)
            self.status_label.setText(f"Status: Error - {e}")

    def _update_charts(self, metrics: RegimeStabilityMetrics):
        """Update matplotlib charts."""
        # Clear all axes
        for ax in [self.ax_stability, self.ax_confidence, self.ax_transitions, self.ax_timeline]:
            ax.clear()

        # Chart 1: Stability Score over time
        if len(self._timestamps) > 1:
            self.ax_stability.plot(self._timestamps, self._stability_scores, 'b-', linewidth=2)
            self.ax_stability.axhline(y=self._stability_threshold, color='r', linestyle='--', label='Threshold')
            self.ax_stability.fill_between(
                self._timestamps,
                self._stability_scores,
                self._stability_threshold,
                where=np.array(self._stability_scores) >= self._stability_threshold,
                alpha=0.3,
                color='green',
            )
            self.ax_stability.set_title("Regime Stability Score")
            self.ax_stability.set_ylabel("Stability (0-1)")
            self.ax_stability.legend()
            self.ax_stability.grid(True, alpha=0.3)

        # Chart 2: Confidence over time
        if len(self._timestamps) > 1:
            self.ax_confidence.plot(self._timestamps, self._confidence_scores, 'g-', linewidth=2)
            self.ax_confidence.set_title("Average Confidence")
            self.ax_confidence.set_ylabel("Confidence (0-1)")
            self.ax_confidence.grid(True, alpha=0.3)

        # Chart 3: Transition Matrix Heatmap
        if metrics.transition_matrix:
            matrix_data = self._build_transition_matrix_array(metrics.transition_matrix)
            if matrix_data is not None:
                im = self.ax_transitions.imshow(matrix_data, cmap='YlOrRd', aspect='auto')
                self.ax_transitions.set_title("Regime Transition Matrix")
                self.figure.colorbar(im, ax=self.ax_transitions)

        # Chart 4: Timeline (last 20 changes)
        history = self._tracker._history[-20:]  # Last 20 changes
        if history:
            times = [change.timestamp for change in history]
            regimes = [change.to_regime for change in history]

            # Create categorical y-axis
            unique_regimes = list(set(regimes))
            y_values = [unique_regimes.index(r) for r in regimes]

            self.ax_timeline.scatter(times, y_values, c='blue', s=50, alpha=0.6)
            self.ax_timeline.set_yticks(range(len(unique_regimes)))
            self.ax_timeline.set_yticklabels(unique_regimes)
            self.ax_timeline.set_title("Recent Regime Changes")
            self.ax_timeline.grid(True, alpha=0.3)

        self.canvas.draw()

    def _build_transition_matrix_array(self, transition_matrix: dict[str, dict[str, int]]) -> np.ndarray | None:
        """Build numpy array from transition matrix dict."""
        if not transition_matrix:
            return None

        # Get unique regimes
        regimes = sorted(set(transition_matrix.keys()))
        if not regimes:
            return None

        # Build matrix
        n = len(regimes)
        matrix = np.zeros((n, n))

        for i, from_regime in enumerate(regimes):
            for j, to_regime in enumerate(regimes):
                count = transition_matrix.get(from_regime, {}).get(to_regime, 0)
                matrix[i, j] = count

        return matrix

    def _update_table(self, metrics: RegimeStabilityMetrics):
        """Update table display (fallback)."""
        values = [
            f"{metrics.stability_score:.2%}",
            f"{metrics.avg_confidence:.2%}",
            str(metrics.num_changes),
            str(metrics.oscillation_count),
            f"{metrics.avg_duration_minutes:.1f}",
            self._tracker._current_regime or "N/A",
        ]

        for i, value in enumerate(values):
            self.metrics_table.setItem(i, 1, QTableWidgetItem(value))

            # Color code stability score
            if i == 0:  # Stability score row
                score = metrics.stability_score
                if score >= self._stability_threshold:
                    self.metrics_table.item(i, 1).setBackground(QColor("#c8e6c9"))  # Green
                else:
                    self.metrics_table.item(i, 1).setBackground(QColor("#ffcdd2"))  # Red

    def _check_alerts(self, metrics: RegimeStabilityMetrics):
        """Check for alert conditions."""
        alerts = []

        # Low stability
        if metrics.stability_score < self._stability_threshold:
            alerts.append(f"⚠ Low stability: {metrics.stability_score:.1%}")
            self.stability_alert.emit(metrics.stability_score)

        # Oscillations detected
        if metrics.oscillation_count > 0:
            alerts.append(f"⚠ {metrics.oscillation_count} oscillations detected")
            self.oscillation_detected.emit(metrics.oscillation_count)

        # Update alert label
        if alerts:
            self.alert_label.setText(" | ".join(alerts))
        else:
            self.alert_label.setText("")

    def _clear_charts(self):
        """Clear all matplotlib charts."""
        for ax in [self.ax_stability, self.ax_confidence, self.ax_transitions, self.ax_timeline]:
            ax.clear()

        self.canvas.draw()


# Standalone test/demo
if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication
    from src.core.tradingbot.regime_stability import RegimeStabilityTracker, RegimeChange

    app = QApplication(sys.argv)

    # Create widget
    widget = PerformanceMonitorWidget()
    widget.setWindowTitle("Performance Monitor - Demo")
    widget.resize(1200, 800)

    # Create demo tracker with sample data
    tracker = RegimeStabilityTracker(window_minutes=60)

    # Add sample regime changes
    now = datetime.now()
    for i in range(10):
        change = RegimeChange(
            timestamp=now - timedelta(minutes=60 - i * 6),
            from_regime="TREND_UP" if i % 2 == 0 else "RANGE",
            to_regime="RANGE" if i % 2 == 0 else "TREND_UP",
            confidence=0.75 + (i % 3) * 0.08,
        )
        tracker.record_change(change)

    # Connect tracker
    widget.set_stability_tracker(tracker)

    # Show widget
    widget.show()

    # Auto-start monitoring
    widget.start_monitoring(update_interval_ms=2000)

    sys.exit(app.exec())
