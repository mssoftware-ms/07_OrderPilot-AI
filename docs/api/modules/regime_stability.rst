Regime Stability
================

.. automodule:: src.core.tradingbot.regime_stability
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

Overview
--------

The ``RegimeStabilityTracker`` monitors regime stability over time to detect:

* **Oscillations**: Rapid switching between regimes (A→B→A pattern)
* **Transition Patterns**: Matrix of regime change frequencies
* **Confidence Trends**: Average confidence scores over time
* **Duration Analysis**: How long regimes persist

This is critical for production monitoring to avoid over-trading during unstable market conditions.

Key Features
------------

**Rolling Window Tracking:**
   Maintains history of regime changes within configurable time window (default 60 minutes).

**Oscillation Detection:**
   Identifies rapid regime switching that indicates market indecision.

**Stability Scoring:**
   Calculates 0-1 stability score with penalties for oscillations.

**Transition Matrix:**
   Tracks all regime-to-regime transitions for pattern analysis.

**Confidence Monitoring:**
   Averages regime classification confidence over time.

Usage Example
-------------

.. code-block:: python

    from src.core.tradingbot.regime_stability import RegimeStabilityTracker, RegimeChange
    from datetime import datetime

    # Initialize tracker
    tracker = RegimeStabilityTracker(window_minutes=60)

    # Record regime changes
    change1 = RegimeChange(
        timestamp=datetime.now(),
        from_regime="TREND_UP",
        to_regime="RANGE",
        confidence=0.82
    )
    tracker.record_change(change1)

    # Get stability metrics
    metrics = tracker.get_metrics(lookback_minutes=30)

    print(f"Stability Score: {metrics.stability_score:.2f}")
    print(f"Changes: {metrics.num_changes}")
    print(f"Oscillations: {metrics.oscillation_count}")
    print(f"Avg Confidence: {metrics.avg_confidence:.2%}")

    # Check for oscillation
    if tracker.detect_oscillation(window_minutes=10, threshold=5):
        print("⚠ WARNING: Rapid regime oscillation detected!")

Classes
-------

.. autoclass:: src.core.tradingbot.regime_stability.RegimeStabilityTracker
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

Key Methods
-----------

record_change(change)
~~~~~~~~~~~~~~~~~~~~~

.. automethod:: src.core.tradingbot.regime_stability.RegimeStabilityTracker.record_change

Record a regime change event.

**Parameters:**

* ``change`` (RegimeChange): Regime change event with timestamp, from_regime, to_regime, confidence

**Behavior:**

1. Appends change to history
2. Updates current regime
3. Prunes old history outside window
4. Auto-detects oscillations

**Example:**

.. code-block:: python

    change = RegimeChange(
        timestamp=datetime.now(),
        from_regime="RANGE",
        to_regime="TREND_UP",
        confidence=0.78
    )
    tracker.record_change(change)

get_metrics(lookback_minutes)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automethod:: src.core.tradingbot.regime_stability.RegimeStabilityTracker.get_metrics

Calculate comprehensive stability metrics.

**Parameters:**

* ``lookback_minutes`` (int, optional): Time window for analysis (defaults to window_minutes)

**Returns:**

* ``RegimeStabilityMetrics``: Stability score, confidence, changes, oscillations, transition matrix

**Stability Score Calculation:**

.. code-block:: python

    # Base stability (fewer changes = higher score)
    expected_max_changes = lookback_minutes / 10  # 1 change per 10 minutes
    base_stability = 1.0 - (num_changes / expected_max_changes)

    # Oscillation penalty (10% per oscillation)
    oscillation_penalty = 0.10 * oscillation_count

    # Final score (clamped 0-1)
    stability_score = max(0.0, min(1.0, base_stability - oscillation_penalty))

**Example:**

.. code-block:: python

    metrics = tracker.get_metrics(lookback_minutes=30)

    # Production alerts
    if metrics.stability_score < 0.50:
        alert("Low regime stability - consider pausing trading")

    if metrics.oscillation_count > 3:
        alert("Excessive oscillations detected")

    # Analyze transition patterns
    for (from_r, to_r), count in metrics.transition_matrix.items():
        if count > 5:
            print(f"Frequent transition: {from_r} → {to_r} ({count}x)")

detect_oscillation(window_minutes, threshold)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automethod:: src.core.tradingbot.regime_stability.RegimeStabilityTracker.detect_oscillation

Detect rapid regime switching (oscillation pattern).

**Parameters:**

* ``window_minutes`` (int): Time window for detection (default 10)
* ``threshold`` (int): Minimum changes to consider oscillation (default 5)

**Returns:**

* ``bool``: True if oscillation detected

**Detection Logic:**

.. code-block:: python

    # Count changes in recent window
    cutoff_time = now - timedelta(minutes=window_minutes)
    recent_changes = [c for c in self._history if c.timestamp >= cutoff_time]

    # Oscillation if changes ≥ threshold
    return len(recent_changes) >= threshold

**Use Case:**

.. code-block:: python

    # Check for oscillation every 5 minutes
    if tracker.detect_oscillation(window_minutes=10, threshold=5):
        # Pause trading to avoid whipsaw
        bot.pause_trading()
        logger.warning("Trading paused due to regime oscillation")

_prune_history()
~~~~~~~~~~~~~~~~

.. automethod:: src.core.tradingbot.regime_stability.RegimeStabilityTracker._prune_history

**Internal method** - Remove history outside rolling window.

**Behavior:**

.. code-block:: python

    cutoff_time = datetime.now() - timedelta(minutes=self._window_minutes)
    self._history = [c for c in self._history if c.timestamp >= cutoff_time]

**Called Automatically:**

- After every ``record_change()`` call

_build_transition_matrix(changes)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automethod:: src.core.tradingbot.regime_stability.RegimeStabilityTracker._build_transition_matrix

**Internal method** - Build regime-to-regime transition frequency matrix.

**Returns:**

.. code-block:: python

    {
        ("TREND_UP", "RANGE"): 3,
        ("RANGE", "TREND_DOWN"): 2,
        ("TREND_DOWN", "RANGE"): 1,
        ...
    }

**Used For:**

- Identifying most common regime transitions
- Detecting cyclical patterns
- Heatmap visualization

Data Models
-----------

RegimeChange (Dataclass)
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    @dataclass
    class RegimeChange:
        timestamp: datetime
        from_regime: str  # Previous regime type
        to_regime: str    # New regime type
        confidence: float  # Classification confidence (0-1)

RegimeStabilityMetrics (Dataclass)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    @dataclass
    class RegimeStabilityMetrics:
        stability_score: float  # 0-1 (higher = more stable)
        avg_confidence: float   # Average classification confidence
        num_changes: int        # Total regime changes in window
        avg_duration_minutes: float  # Average regime duration
        oscillation_count: int  # Number of oscillation patterns
        transition_matrix: dict[tuple[str, str], int]  # Transition frequencies

Metrics Interpretation
----------------------

**Stability Score:**

.. code-block:: text

    0.80 - 1.00: Excellent stability (safe to trade)
    0.60 - 0.80: Good stability (normal trading)
    0.40 - 0.60: Moderate stability (reduce position size)
    0.20 - 0.40: Low stability (consider pausing)
    0.00 - 0.20: Very low stability (pause recommended)

**Avg Confidence:**

.. code-block:: text

    0.80 - 1.00: High confidence classifications
    0.60 - 0.80: Good confidence
    < 0.60: Low confidence (may indicate noisy conditions)

**Num Changes:**

.. code-block:: text

    Expected: ~1 change per 10 minutes in stable markets
    > 6 changes per 60 min: High instability

**Oscillation Count:**

.. code-block:: text

    0-1: Normal
    2-3: Moderate concern
    4+: Significant oscillation (pause trading)

Best Practices
--------------

**1. Production Monitoring:**

.. code-block:: python

    # Check stability every 5 minutes
    def monitor_stability():
        metrics = tracker.get_metrics(lookback_minutes=30)

        if metrics.stability_score < 0.50:
            send_alert("Low regime stability", severity="high")
            bot.reduce_position_sizes(factor=0.5)

        if metrics.oscillation_count > 3:
            send_alert("Excessive oscillations", severity="critical")
            bot.pause_trading()

**2. Dynamic Position Sizing:**

.. code-block:: python

    def adjust_position_size(base_size: float) -> float:
        metrics = tracker.get_metrics()
        stability_factor = metrics.stability_score

        # Reduce size in unstable conditions
        adjusted_size = base_size * stability_factor

        # Hard cap during oscillations
        if metrics.oscillation_count > 2:
            adjusted_size *= 0.5

        return max(adjusted_size, MIN_POSITION_SIZE)

**3. Strategy Adaptation:**

.. code-block:: python

    def select_strategy():
        metrics = tracker.get_metrics()

        if metrics.stability_score > 0.75:
            # Stable market - use trend-following
            return "trend_following"
        elif metrics.oscillation_count > 2:
            # Oscillating market - avoid trading or use range strategies
            return "range_bound" if metrics.stability_score > 0.40 else None
        else:
            # Moderate stability - balanced approach
            return "balanced"

**4. Logging & Analysis:**

.. code-block:: python

    def log_stability_metrics():
        metrics = tracker.get_metrics()

        logger.info(
            f"Regime Stability Report:\n"
            f"  Score: {metrics.stability_score:.2f}\n"
            f"  Confidence: {metrics.avg_confidence:.2%}\n"
            f"  Changes (60m): {metrics.num_changes}\n"
            f"  Oscillations: {metrics.oscillation_count}\n"
            f"  Avg Duration: {metrics.avg_duration_minutes:.1f} min"
        )

        # Top 3 transitions
        top_transitions = sorted(
            metrics.transition_matrix.items(),
            key=lambda x: x[1],
            reverse=True
        )[:3]

        for (from_r, to_r), count in top_transitions:
            logger.info(f"  {from_r} → {to_r}: {count}x")

Integration Example
-------------------

**Complete Production Setup:**

.. code-block:: python

    from src.core.tradingbot.regime_stability import RegimeStabilityTracker
    from src.core.tradingbot.regime_engine import RegimeEngine
    from src.ui.widgets.performance_monitor_widget import PerformanceMonitorWidget

    # 1. Initialize tracker
    tracker = RegimeStabilityTracker(window_minutes=60)

    # 2. Connect to regime engine
    regime_engine = RegimeEngine()

    # 3. Record regime changes on every bar
    def on_new_bar(features):
        new_regime = regime_engine.classify(features)

        if regime_engine.detect_regime_change(current_regime, new_regime):
            change = RegimeChange(
                timestamp=datetime.now(),
                from_regime=current_regime.regime.name,
                to_regime=new_regime.regime.name,
                confidence=new_regime.regime_confidence
            )
            tracker.record_change(change)

            # Check for issues
            if tracker.detect_oscillation():
                logger.warning("Oscillation detected - pausing trading")
                bot.pause()

    # 4. UI monitoring (optional)
    monitor_widget = PerformanceMonitorWidget()
    monitor_widget.set_stability_tracker(tracker)
    monitor_widget.start_monitoring()

See Also
--------

* :doc:`regime_engine` - Generates regime classifications
* :doc:`bot_controller` - Uses stability for trading decisions
* :doc:`performance_monitor_widget` - Visualizes stability metrics
* :doc:`backtest_harness` - Tests regime stability in backtests
