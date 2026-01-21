Performance Monitor Widget
==========================

.. automodule:: src.ui.widgets.performance_monitor_widget
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

Overview
--------

The ``PerformanceMonitorWidget`` provides real-time visualization of regime-based trading performance:

* **Stability Score Tracking**: Live chart of regime stability over time
* **Oscillation Detection**: Alerts when rapid regime switching occurs
* **Transition Matrix**: Heatmap showing regime transition patterns
* **Confidence Trends**: Tracks regime confidence over time
* **Strategy Switching Timeline**: Visualizes strategy changes
* **Parameter Override Tracking**: Monitors when parameters are modified

Key Features
------------

**Real-Time Monitoring:**
   Updates metrics at configurable intervals (1s-60s) with automatic data collection.

**Visual Feedback:**
   Matplotlib charts with 2x2 subplot layout showing stability, confidence, transitions, and timeline.

**Alert System:**
   Emits PyQt signals when stability drops below threshold or oscillations detected.

**Configurable Display:**
   Adjustable lookback window (10-240 minutes) and update intervals.

**Fallback Mode:**
   Table-based display if matplotlib not available.

Usage Example
-------------

.. code-block:: python

    from src.ui.widgets.performance_monitor_widget import PerformanceMonitorWidget
    from src.core.tradingbot.regime_stability import RegimeStabilityTracker
    from PyQt6.QtWidgets import QApplication

    # 1. Create Qt application
    app = QApplication([])

    # 2. Initialize stability tracker
    tracker = RegimeStabilityTracker(window_minutes=60)

    # 3. Create performance monitor widget
    monitor = PerformanceMonitorWidget()

    # 4. Connect to tracker
    monitor.set_stability_tracker(tracker)

    # 5. Connect to alert signals
    monitor.stability_alert.connect(
        lambda score: print(f"⚠ Low stability: {score:.2%}")
    )
    monitor.oscillation_detected.connect(
        lambda count: print(f"⚠ Oscillations detected: {count}")
    )

    # 6. Start monitoring
    monitor.start_monitoring(update_interval_ms=1000)  # Update every 1 second

    # 7. Show widget
    monitor.show()

    # 8. Run application
    app.exec()

Classes
-------

.. autoclass:: src.ui.widgets.performance_monitor_widget.PerformanceMonitorWidget
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

Signals
-------

stability_alert(float)
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    stability_alert = pyqtSignal(float)  # stability_score

**Emitted when**: Stability score drops below threshold (default: 0.7)

**Parameter**: Current stability score (0.0 to 1.0)

**Example:**

.. code-block:: python

    def on_stability_alert(score: float):
        if score < 0.5:
            print(f"🔴 CRITICAL: Stability very low ({score:.2%})")
            # Reduce trading activity
            bot.set_conservative_mode(True)
        elif score < 0.7:
            print(f"🟡 WARNING: Stability degraded ({score:.2%})")
            # Monitor closely
            bot.increase_monitoring_frequency()

    monitor.stability_alert.connect(on_stability_alert)

oscillation_detected(int)
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    oscillation_detected = pyqtSignal(int)  # oscillation_count

**Emitted when**: Rapid regime switching (oscillations) detected

**Parameter**: Number of oscillations in current window

**Example:**

.. code-block:: python

    def on_oscillation_detected(count: int):
        print(f"⚠ {count} regime oscillations detected!")

        if count >= 5:
            print("🔴 CRITICAL: Excessive oscillations - pause trading")
            bot.pause_trading()
        elif count >= 3:
            print("🟡 WARNING: Multiple oscillations - tighten filters")
            bot.increase_regime_filter_threshold()

    monitor.oscillation_detected.connect(on_oscillation_detected)

Key Methods
-----------

set_stability_tracker(tracker)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automethod:: src.ui.widgets.performance_monitor_widget.PerformanceMonitorWidget.set_stability_tracker

Set the RegimeStabilityTracker to monitor.

**Parameters:**

* ``tracker`` (RegimeStabilityTracker): Tracker instance to monitor

**Example:**

.. code-block:: python

    # Create tracker
    tracker = RegimeStabilityTracker(window_minutes=60)

    # Attach to monitor
    monitor.set_stability_tracker(tracker)

    # Now monitor will automatically pull metrics from tracker

start_monitoring(update_interval_ms)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automethod:: src.ui.widgets.performance_monitor_widget.PerformanceMonitorWidget.start_monitoring

Start real-time monitoring with specified update interval.

**Parameters:**

* ``update_interval_ms`` (int): Update interval in milliseconds (default: 1000)

**Algorithm:**

.. code-block:: python

    def start_monitoring(self, update_interval_ms: int = 1000):
        # 1. Validate tracker is set
        if self._tracker is None:
            raise ValueError("No stability tracker set. Call set_stability_tracker() first.")

        # 2. Configure timer
        self._update_timer.setInterval(update_interval_ms)

        # 3. Start timer (calls _update_metrics on each interval)
        self._update_timer.start()

        # 4. Update UI
        self.start_btn.setText("⏸ Pause Monitoring")
        self.start_btn.setStyleSheet("background-color: #ef5350; color: white;")

        logger.info(f"Monitoring started (interval: {update_interval_ms}ms)")

**Example:**

.. code-block:: python

    # Update every second
    monitor.start_monitoring(update_interval_ms=1000)

    # Update every 5 seconds (less overhead)
    monitor.start_monitoring(update_interval_ms=5000)

    # Update every 30 seconds (for long-term monitoring)
    monitor.start_monitoring(update_interval_ms=30000)

stop_monitoring()
~~~~~~~~~~~~~~~~~

.. automethod:: src.ui.widgets.performance_monitor_widget.PerformanceMonitorWidget.stop_monitoring

Stop real-time monitoring.

**Example:**

.. code-block:: python

    # Stop monitoring
    monitor.stop_monitoring()

    # Check if monitoring is active
    if monitor.is_monitoring():
        print("Still monitoring")
    else:
        print("Monitoring stopped")

_update_metrics()
~~~~~~~~~~~~~~~~~

.. automethod:: src.ui.widgets.performance_monitor_widget.PerformanceMonitorWidget._update_metrics

**Internal method** - Update all metrics and charts.

Called automatically by timer at configured interval.

**Algorithm:**

.. code-block:: python

    def _update_metrics(self):
        if not self._tracker:
            return

        # 1. Get current metrics
        metrics = self._tracker.get_current_metrics()

        # 2. Store timestamp and scores
        self._timestamps.append(datetime.now())
        self._stability_scores.append(metrics.stability_score)
        self._confidence_scores.append(metrics.avg_confidence)

        # 3. Trim to lookback window
        cutoff_time = datetime.now() - timedelta(minutes=self._lookback_minutes)
        self._trim_data_before(cutoff_time)

        # 4. Update charts
        if MATPLOTLIB_AVAILABLE:
            self._update_stability_chart()
            self._update_confidence_chart()
            self._update_transition_matrix()
            self._update_timeline_chart()
            self.canvas.draw()
        else:
            self._update_metrics_table(metrics)

        # 5. Check for alerts
        if metrics.stability_score < self._stability_threshold:
            self.stability_alert.emit(metrics.stability_score)

        if metrics.oscillation_count >= 3:
            self.oscillation_detected.emit(metrics.oscillation_count)

_update_stability_chart()
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automethod:: src.ui.widgets.performance_monitor_widget.PerformanceMonitorWidget._update_stability_chart

**Internal method** - Update stability score chart.

**Chart Details:**

.. code-block:: python

    # Subplot 1: Stability Score Over Time
    self.ax_stability.clear()

    # Plot line
    self.ax_stability.plot(
        self._timestamps,
        self._stability_scores,
        color='#26a69a',  # Green
        linewidth=2,
        label='Stability Score'
    )

    # Add threshold line
    self.ax_stability.axhline(
        y=self._stability_threshold,
        color='#ef5350',  # Red
        linestyle='--',
        label=f'Threshold ({self._stability_threshold:.2%})'
    )

    # Fill below threshold in red
    self.ax_stability.fill_between(
        self._timestamps,
        self._stability_scores,
        self._stability_threshold,
        where=[s < self._stability_threshold for s in self._stability_scores],
        color='#ef5350',
        alpha=0.3
    )

    # Labels
    self.ax_stability.set_title('Regime Stability Over Time')
    self.ax_stability.set_xlabel('Time')
    self.ax_stability.set_ylabel('Stability Score')
    self.ax_stability.legend()
    self.ax_stability.grid(True, alpha=0.3)

_update_transition_matrix()
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automethod:: src.ui.widgets.performance_monitor_widget.PerformanceMonitorWidget._update_transition_matrix

**Internal method** - Update regime transition matrix heatmap.

**Chart Details:**

.. code-block:: python

    # Subplot 3: Transition Matrix Heatmap
    transition_matrix = self._tracker.get_transition_matrix()

    # Create heatmap
    im = self.ax_transitions.imshow(
        transition_matrix,
        cmap='YlOrRd',  # Yellow-Orange-Red
        aspect='auto'
    )

    # Add text annotations (transition counts)
    for i in range(len(transition_matrix)):
        for j in range(len(transition_matrix[0])):
            text = self.ax_transitions.text(
                j, i, int(transition_matrix[i][j]),
                ha="center", va="center", color="black"
            )

    # Labels
    regime_names = ['UP', 'DOWN', 'RANGE']
    self.ax_transitions.set_xticks(range(len(regime_names)))
    self.ax_transitions.set_yticks(range(len(regime_names)))
    self.ax_transitions.set_xticklabels(regime_names)
    self.ax_transitions.set_yticklabels(regime_names)
    self.ax_transitions.set_title('Regime Transition Matrix')
    self.ax_transitions.set_xlabel('To Regime')
    self.ax_transitions.set_ylabel('From Regime')

Common Patterns
---------------

**Pattern 1: Embedded in Trading Bot UI**

.. code-block:: python

    class TradingBotWindow(QMainWindow):
        def __init__(self):
            super().__init__()

            # Create bot components
            self.tracker = RegimeStabilityTracker()
            self.bot_controller = BotController()

            # Create performance monitor
            self.monitor = PerformanceMonitorWidget()
            self.monitor.set_stability_tracker(self.tracker)

            # Add to UI
            self.setCentralWidget(self.monitor)

            # Connect signals
            self.monitor.stability_alert.connect(self._on_stability_alert)
            self.monitor.oscillation_detected.connect(self._on_oscillations)

            # Start monitoring
            self.monitor.start_monitoring(1000)

        def _on_stability_alert(self, score: float):
            # Reduce risk when stability is low
            if score < 0.5:
                self.bot_controller.set_risk_multiplier(0.5)

        def _on_oscillations(self, count: int):
            # Pause trading if excessive oscillations
            if count >= 5:
                self.bot_controller.pause_trading()

**Pattern 2: Standalone Monitoring Dashboard**

.. code-block:: python

    # Create standalone dashboard
    app = QApplication([])

    # Load tracker from saved state
    tracker = RegimeStabilityTracker.from_file('tracker_state.json')

    # Create monitor with custom settings
    monitor = PerformanceMonitorWidget()
    monitor.set_stability_tracker(tracker)
    monitor.set_stability_threshold(0.6)  # Lower threshold
    monitor.set_lookback_minutes(120)  # 2 hours

    # Start monitoring
    monitor.start_monitoring(update_interval_ms=5000)

    # Show fullscreen
    monitor.showMaximized()

    app.exec()

**Pattern 3: Alert-Based Trading Control**

.. code-block:: python

    class AlertBasedBot:
        def __init__(self):
            self.tracker = RegimeStabilityTracker()
            self.monitor = PerformanceMonitorWidget()
            self.monitor.set_stability_tracker(self.tracker)

            # Configure thresholds
            self.monitor.set_stability_threshold(0.7)

            # Connect alerts to trading logic
            self.monitor.stability_alert.connect(self._handle_stability_alert)
            self.monitor.oscillation_detected.connect(self._handle_oscillations)

            self.position_size_multiplier = 1.0
            self.trading_paused = False

        def _handle_stability_alert(self, score: float):
            # Adjust position sizing based on stability
            if score < 0.5:
                self.position_size_multiplier = 0.3  # 30% of normal
            elif score < 0.7:
                self.position_size_multiplier = 0.6  # 60% of normal
            else:
                self.position_size_multiplier = 1.0  # 100% normal

            logger.info(f"Position size adjusted to {self.position_size_multiplier:.0%}")

        def _handle_oscillations(self, count: int):
            # Pause trading if oscillations too high
            if count >= 5:
                self.trading_paused = True
                logger.warning("Trading paused due to regime oscillations")

                # Auto-resume after stability improves
                QTimer.singleShot(300000, self._check_resume)  # Check in 5 minutes

        def _check_resume(self):
            metrics = self.tracker.get_current_metrics()
            if metrics.oscillation_count < 3:
                self.trading_paused = False
                logger.info("Trading resumed - oscillations reduced")

**Pattern 4: Performance Reporting**

.. code-block:: python

    # Generate performance report from monitor
    def generate_performance_report(monitor: PerformanceMonitorWidget):
        metrics = monitor.get_current_metrics()

        report = f"""
        Performance Report ({datetime.now().strftime('%Y-%m-%d %H:%M')})
        =====================================================

        Stability Score: {metrics.stability_score:.2%}
        Average Confidence: {metrics.avg_confidence:.2%}
        Regime Changes (1h): {metrics.regime_changes_1h}
        Oscillations Detected: {metrics.oscillation_count}

        Regime Distribution:
        - TREND_UP: {metrics.regime_distribution['TREND_UP']:.1%}
        - TREND_DOWN: {metrics.regime_distribution['TREND_DOWN']:.1%}
        - RANGE: {metrics.regime_distribution['RANGE']:.1%}

        Most Common Transition: {metrics.most_common_transition}

        Recommendations:
        """

        if metrics.stability_score < 0.5:
            report += "- 🔴 CRITICAL: Very low stability - consider pausing trading\n"
        elif metrics.stability_score < 0.7:
            report += "- 🟡 WARNING: Degraded stability - reduce position sizes\n"
        else:
            report += "- ✅ OK: Good stability - normal operations\n"

        if metrics.oscillation_count >= 5:
            report += "- 🔴 CRITICAL: Excessive oscillations - review regime thresholds\n"
        elif metrics.oscillation_count >= 3:
            report += "- 🟡 WARNING: Multiple oscillations - tighten filters\n"

        return report

Configuration Methods
---------------------

set_stability_threshold(threshold)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    monitor.set_stability_threshold(0.6)  # Alert if below 60%

Set threshold for stability alerts (0.0 to 1.0).

set_lookback_minutes(minutes)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    monitor.set_lookback_minutes(120)  # 2 hours

Set rolling window size for chart display (10 to 240 minutes).

set_update_interval(interval_ms)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    monitor.set_update_interval(5000)  # Update every 5 seconds

Change update frequency (must call while monitoring is stopped).

Best Practices
--------------

**1. Choose Appropriate Update Interval:**

.. code-block:: python

    # ✅ Good: Match update interval to timeframe
    # For 1m chart, update every 1-5 seconds
    monitor.start_monitoring(update_interval_ms=1000)

    # For 15m chart, update every 15-30 seconds
    monitor.start_monitoring(update_interval_ms=15000)

    # ❌ Bad: Update too frequently (wastes CPU)
    # For 1h chart, don't update every second
    monitor.start_monitoring(update_interval_ms=1000)  # Overkill

**2. Set Appropriate Lookback Window:**

.. code-block:: python

    # ✅ Good: Lookback matches strategy timeframe
    # For day trading (1m-5m), use 60-120 minutes
    monitor.set_lookback_minutes(60)

    # For swing trading (1h-4h), use longer window
    monitor.set_lookback_minutes(240)

    # ❌ Bad: Very short lookback for long timeframes
    monitor.set_lookback_minutes(10)  # Too short for 1h trading

**3. Handle Alerts Appropriately:**

.. code-block:: python

    # ✅ Good: Gradual risk reduction
    def on_stability_alert(score: float):
        if score < 0.5:
            bot.set_risk_multiplier(0.3)
        elif score < 0.7:
            bot.set_risk_multiplier(0.6)
        # Gradual adjustment based on severity

    # ❌ Bad: Binary on/off
    def on_stability_alert(score: float):
        bot.stop_trading()  # Too extreme, no gradation

**4. Stop Monitoring When Not Needed:**

.. code-block:: python

    # ✅ Good: Stop when bot is paused
    bot.on_pause.connect(monitor.stop_monitoring)
    bot.on_resume.connect(lambda: monitor.start_monitoring(1000))

    # ❌ Bad: Keep monitoring even when bot stopped
    # Wastes resources

See Also
--------

* :doc:`regime_stability` - RegimeStabilityTracker tracked by this widget
* :doc:`regime_engine` - RegimeEngine that classifies regimes
* :doc:`bot_controller` - BotController integration with monitoring
