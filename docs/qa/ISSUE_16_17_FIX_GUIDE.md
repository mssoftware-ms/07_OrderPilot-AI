# Issue 16 & 17: Implementation Fix Guide

**Quick Reference:** 5 critical fixes needed. Total effort: 6-8 hours. Priority: HIGH.

---

## FIX #1: CRITICAL - Enable Checked State Styling

### Problem
`QPushButton:checked` stylesheet rules in themes.py are ignored because buttons are set to checked before stylesheet is applied.

### Root Cause
1. Button created and state set before theme stylesheet loads
2. Qt stylesheet engine doesn't retroactively apply `:checked` selectors to already-checked buttons
3. Need to explicitly refresh stylesheet after state change

### Files to Modify
- `src/ui/widgets/chart_mixins/toolbar_mixin_row1.py`

### Implementation

**Step 1: Create helper function in toolbar_mixin_row1.py**

```python
# Add this method to ToolbarMixinRow1 class (around line 30)

@staticmethod
def _refresh_button_stylesheet(button: QPushButton) -> None:
    """Refresh button stylesheet to apply :checked and other pseudo-selectors.

    Call this after changing button state (setChecked, setEnabled, etc.)
    to ensure stylesheet pseudo-selectors like :checked are re-evaluated.
    """
    button.style().unpolish(button)
    button.style().polish(button)
    button.update()
```

**Step 2: Apply to connect button (line 78-89)**

Change from:
```python
self.parent.chart_connect_button.setCheckable(True)
self.parent.chart_connect_button.setToolTip(...)
self.parent.chart_connect_button.setFixedHeight(self.BUTTON_HEIGHT)
self.parent.chart_connect_button.setFixedWidth(40)
self.parent.chart_connect_button.clicked.connect(self._on_broker_connect_clicked)
toolbar.addWidget(self.parent.chart_connect_button)
```

To:
```python
self.parent.chart_connect_button.setCheckable(True)
self.parent.chart_connect_button.setToolTip(...)
self.parent.chart_connect_button.setFixedHeight(self.BUTTON_HEIGHT)
self.parent.chart_connect_button.setFixedWidth(40)
self.parent.chart_connect_button.clicked.connect(self._on_broker_connect_clicked)
toolbar.addWidget(self.parent.chart_connect_button)

# FIX #1: Refresh stylesheet so :checked selector works
self._refresh_button_stylesheet(self.parent.chart_connect_button)
```

**Step 3: Apply to watchlist button (line 167-174)**

Change from:
```python
self.parent.watchlist_toggle_btn.setCheckable(True)
self.parent.watchlist_toggle_btn.setChecked(True)  # Default: visible
self.parent.watchlist_toggle_btn.setToolTip("Watchlist ein/ausblenden")
self.parent.watchlist_toggle_btn.setFixedHeight(self.BUTTON_HEIGHT)
self.parent.watchlist_toggle_btn.setFixedWidth(40)
self.parent.watchlist_toggle_btn.setProperty("class", "toolbar-button")
self.parent.watchlist_toggle_btn.clicked.connect(self._toggle_watchlist)
toolbar.addWidget(self.parent.watchlist_toggle_btn)
```

To:
```python
self.parent.watchlist_toggle_btn.setCheckable(True)
self.parent.watchlist_toggle_btn.setChecked(True)  # Default: visible
self.parent.watchlist_toggle_btn.setToolTip("Watchlist ein/ausblenden")
self.parent.watchlist_toggle_btn.setFixedHeight(self.BUTTON_HEIGHT)
self.parent.watchlist_toggle_btn.setFixedWidth(40)
self.parent.watchlist_toggle_btn.setProperty("class", "toolbar-button")
self.parent.watchlist_toggle_btn.clicked.connect(self._toggle_watchlist)

# FIX #1: Refresh stylesheet so :checked selector works
self._refresh_button_stylesheet(self.parent.watchlist_toggle_btn)
toolbar.addWidget(self.parent.watchlist_toggle_btn)
```

**Step 4: Update _update_broker_ui_state method (line 144-158)**

Change from:
```python
def _update_broker_ui_state(self, connected: bool, broker_type: str) -> None:
    """Update broker-related UI elements."""
    from src.ui.icons import get_icon

    if not hasattr(self.parent, 'chart_connect_button'):
        return

    if connected:
        self.parent.chart_connect_button.setIcon(get_icon("disconnect"))
        self.parent.chart_connect_button.setChecked(True)
        self.parent.chart_connect_button.setToolTip(f"Verbunden: {broker_type}\nKlicken zum Trennen")
    else:
        self.parent.chart_connect_button.setIcon(get_icon("connect"))
        self.parent.chart_connect_button.setChecked(False)
        self.parent.chart_connect_button.setToolTip("Nicht verbunden\nKlicken zum Verbinden")
```

To:
```python
def _update_broker_ui_state(self, connected: bool, broker_type: str) -> None:
    """Update broker-related UI elements."""
    from src.ui.icons import get_icon

    if not hasattr(self.parent, 'chart_connect_button'):
        return

    if connected:
        self.parent.chart_connect_button.setIcon(get_icon("disconnect"))
        self.parent.chart_connect_button.setChecked(True)
        self.parent.chart_connect_button.setToolTip(f"Verbunden: {broker_type}\nKlicken zum Trennen")
    else:
        self.parent.chart_connect_button.setIcon(get_icon("connect"))
        self.parent.chart_connect_button.setChecked(False)
        self.parent.chart_connect_button.setToolTip("Nicht verbunden\nKlicken zum Verbinden")

    # FIX #1: Refresh stylesheet to apply :checked styles
    self._refresh_button_stylesheet(self.parent.chart_connect_button)
```

### Verification
```bash
# After applying fix, run this to verify:
# 1. Start app and connect broker
# 2. Connect button should show:
#    - Orange/active background (Dark Orange theme)
#    - Bold text
#    - Different border color
# 3. Click to disconnect
# 4. Button should return to default inactive style
```

---

## FIX #2: CRITICAL - Add Missing Timeframe Resolutions

### Problem
New timeframes (1S, 2H, 8H) added to toolbar but not in streaming resolution maps. Causes candle misalignment.

### Files to Modify
- `src/ui/widgets/chart_mixins/streaming_mixin.py`
- `src/ui/widgets/chart_mixins/alpaca_streaming_mixin.py`
- `src/ui/widgets/chart_mixins/bitunix_streaming_mixin.py`

### Implementation

**Change 1: streaming_mixin.py (Lines 203-214)**

From:
```python
def _get_resolution_seconds(self) -> int:
    """Get current chart timeframe resolution in seconds.

    Maps timeframe string (e.g., "5T") to seconds (e.g., 300).
    """
    timeframe_to_seconds = {
        "1T": 60,      # 1 minute
        "5T": 300,     # 5 minutes
        "10T": 600,    # 10 minutes
        "15T": 900,    # 15 minutes
        "30T": 1800,   # 30 minutes
        "1H": 3600,    # 1 hour
        "4H": 14400,   # 4 hours
        "1D": 86400,   # 1 day
    }
    current_tf = getattr(self, 'current_timeframe', '1T')
    return timeframe_to_seconds.get(current_tf, 60)
```

To:
```python
def _get_resolution_seconds(self) -> int:
    """Get current chart timeframe resolution in seconds.

    Maps timeframe string (e.g., "5T") to seconds (e.g., 300).
    """
    timeframe_to_seconds = {
        "1S": 1,       # 1 second - Issue #38
        "1T": 60,      # 1 minute
        "5T": 300,     # 5 minutes
        "10T": 600,    # 10 minutes
        "15T": 900,    # 15 minutes
        "30T": 1800,   # 30 minutes
        "1H": 3600,    # 1 hour
        "2H": 7200,    # 2 hours - Issue #42
        "4H": 14400,   # 4 hours
        "8H": 28800,   # 8 hours - Issue #42
        "1D": 86400,   # 1 day
    }
    current_tf = getattr(self, 'current_timeframe', '1T')
    return timeframe_to_seconds.get(current_tf, 60)
```

**Change 2: alpaca_streaming_mixin.py (Lines 184-195)**

Apply same change as above.

**Change 3: bitunix_streaming_mixin.py (Lines 140-151)**

Apply same change as above.

### Verification
```bash
# Test all timeframes:
# 1. Select "1 Sekunde" timeframe
# 2. Live stream a symbol
# 3. Verify candles are 1-second wide (not 60-second)
# 4. Select "2 Stunden" timeframe
# 5. Verify candles are 2-hour wide
# 6. Select "8 Stunden" timeframe
# 7. Verify candles are 8-hour wide

# Python verification:
from src.ui.widgets.chart_mixins.streaming_mixin import StreamingMixin
mixin = StreamingMixin()
mixin.current_timeframe = "1S"
assert mixin._get_resolution_seconds() == 1, "1S should be 1 second"
mixin.current_timeframe = "2H"
assert mixin._get_resolution_seconds() == 7200, "2H should be 7200 seconds"
```

---

## FIX #3: HIGH - Replace Hardcoded Status Colors with Theme System

### Problem
Market status labels use hardcoded #FF0000, #00FF00, #888 colors, bypassing theme system.

### Files to Modify
- `src/ui/widgets/chart_mixins/streaming_mixin.py`
- `src/ui/widgets/chart_mixins/alpaca_streaming_mixin.py`
- `src/ui/widgets/chart_mixins/bitunix_streaming_mixin.py`
- `src/ui/themes.py` (add style definitions)

### Implementation

**Step 1: Add status label styles to themes.py (after line 322)**

```python
# Add this after the disclaimer label section (around line 323)

        /* Status Label for Market Connection */
        QLabel[class="market-status"][state="streaming"] {{
            color: {p.error};  /* Red for streaming active */
            font-weight: bold;
            padding: 5px;
        }}
        QLabel[class="market-status"][state="ready"] {{
            color: {p.text_secondary};  /* Gray for ready/idle */
            font-weight: bold;
            padding: 5px;
        }}
        QLabel[class="market-status"][state="connected"] {{
            color: {p.success};  /* Green for live connection */
            font-weight: bold;
            padding: 5px;
        }}
        QLabel[class="market-status"][state="error"] {{
            color: {p.error};  /* Red for errors */
            font-weight: bold;
            padding: 5px;
        }}
```

**Step 2: Add helper method to StreamingMixin (around line 20)**

```python
# Add this method to StreamingMixin class

def _set_market_status_themed(self, text: str, state: str) -> None:
    """Update market status label with theme-aware colors.

    Args:
        text: Status text to display
        state: 'streaming', 'ready', 'connected', 'error'
    """
    self.market_status_label.setText(text)
    self.market_status_label.setProperty("class", "market-status")
    self.market_status_label.setProperty("state", state)

    # Refresh stylesheet to apply state selector
    self.market_status_label.style().unpolish(self.market_status_label)
    self.market_status_label.style().polish(self.market_status_label)
    self.market_status_label.update()
```

**Step 3: Replace all hardcoded color calls in streaming_mixin.py**

From (Line 413):
```python
self.market_status_label.setText("🔴 Streaming...")
self.market_status_label.setStyleSheet("color: #FF0000; font-weight: bold; padding: 5px;")
```

To:
```python
self._set_market_status_themed("🔴 Streaming...", "streaming")
```

From (Line 427):
```python
self.market_status_label.setText("Ready")
self.market_status_label.setStyleSheet("color: #888; font-weight: bold; padding: 5px;")
```

To:
```python
self._set_market_status_themed("Ready", "ready")
```

From (Line 476):
```python
self.market_status_label.setText(f"🟢 Live ({asset_type}): {self.current_symbol}")
self.market_status_label.setStyleSheet("color: #00FF00; font-weight: bold; padding: 5px;")
```

To:
```python
self._set_market_status_themed(f"🟢 Live ({asset_type}): {self.current_symbol}", "connected")
```

**Step 4: Apply same changes to alpaca_streaming_mixin.py and bitunix_streaming_mixin.py**

Replace all instances of:
- `self.market_status_label.setStyleSheet("color: #FF0000;...` → `self._set_market_status_themed(..., "streaming" or "error")`
- `self.market_status_label.setStyleSheet("color: #00FF00;...` → `self._set_market_status_themed(..., "connected")`
- `self.market_status_label.setStyleSheet("color: #888;...` → `self._set_market_status_themed(..., "ready")`

### Verification
```bash
# After applying fix:
# 1. Start app and load chart
# 2. Status should show "Ready" in secondary text color
# 3. Click Live Stream button
# 4. Status should show "🔴 Streaming..." in error color (red)
# 5. When stream connects, show "🟢 Live ..." in success color (green)
# 6. Switch theme (Dark Orange → Dark White)
# 7. Verify status colors update accordingly
```

---

## FIX #4: HIGH - Consolidate Duplicate Streaming Code (Refactoring)

### Problem
2,400+ lines of identical code across 3 streaming mixin files violates DRY principle.

### Complexity
This is a significant refactoring. Estimated effort: 3-4 hours.

### Recommended Approach

**Option A: Quick Fix (1-2 hours)**
Keep 3 files but extract common methods to base class.

**Option B: Proper Fix (3-4 hours)**
Use Strategy pattern for tick filtering, merge implementations.

### Recommended: Option B (Proper Fix)

Create new file: `src/ui/widgets/chart_mixins/tick_filter.py`

```python
"""Tick validation strategies for different data sources."""

from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


class TickFilterStrategy(ABC):
    """Abstract base for tick validation strategies."""

    @abstractmethod
    def should_filter_tick(self, price: float, reference_price: float | None) -> bool:
        """Determine if tick should be filtered (rejected).

        Args:
            price: New tick price
            reference_price: Previous valid price for comparison

        Returns:
            True if tick should be FILTERED OUT (invalid), False if valid
        """
        pass


class AlpacaTickFilter(TickFilterStrategy):
    """Alpaca tick filter - 5% deviation filter for bad ticks."""

    MAX_DEVIATION_PCT = 5.0

    def should_filter_tick(self, price: float, reference_price: float | None) -> bool:
        """Apply 5% deviation filter (Alpaca has bad ticks)."""
        if price <= 0:
            return True  # Filter: invalid price

        if reference_price is None or reference_price <= 0:
            return False  # Valid: no reference to compare

        deviation_pct = abs((price - reference_price) / reference_price) * 100

        if deviation_pct > self.MAX_DEVIATION_PCT:
            logger.warning(
                f"Alpaca bad tick filtered: price={price:.2f} "
                f"deviates {deviation_pct:.1f}% from reference={reference_price:.2f}"
            )
            return True  # Filter: too much deviation

        return False  # Valid: within tolerance


class BitunixTickFilter(TickFilterStrategy):
    """Bitunix tick filter - no filtering (provider handles Z-Score filtering)."""

    def should_filter_tick(self, price: float, reference_price: float | None) -> bool:
        """No filtering needed - Bitunix provider already filters ticks."""
        return False  # Never filter - provider handles it


class GenericTickFilter(TickFilterStrategy):
    """Generic tick filter - applies broker-specific logic based on source."""

    def __init__(self, strict_alpaca: bool = True):
        """Initialize generic filter.

        Args:
            strict_alpaca: If True, apply Alpaca filter to Alpaca data
        """
        self.alpaca_filter = AlpacaTickFilter()
        self.bitunix_filter = BitunixTickFilter()
        self.strict_alpaca = strict_alpaca

    def should_filter_tick(self, price: float, reference_price: float | None, source: str = "unknown") -> bool:
        """Apply appropriate filter based on data source."""
        if "bitunix" in source.lower():
            return self.bitunix_filter.should_filter_tick(price, reference_price)
        elif "alpaca" in source.lower() and self.strict_alpaca:
            return self.alpaca_filter.should_filter_tick(price, reference_price)
        else:
            # Default: no filtering
            return False
```

Then update streaming_mixin.py to use:

```python
# In _on_market_tick method
from .tick_filter import GenericTickFilter

# During init:
self.tick_filter = GenericTickFilter()

# In _on_market_tick:
event_source = str(getattr(event, 'source', ''))
if self.tick_filter.should_filter_tick(price, reference_price, event_source):
    return
```

### Verification
```bash
# After refactoring:
# 1. All 3 mixins work identically
# 2. Bug fixes apply to all brokers automatically
# 3. New brokers can be added by creating new TickFilter subclass
# 4. 1,000+ LOC eliminated
```

---

## FIX #5: MEDIUM - Add Missing Null Checks & Logging

### Files to Modify
- `toolbar_mixin_row1.py`
- All streaming mixins

### Implementation

**In toolbar_mixin_row1.py _toggle_watchlist() (Line 176-197):**

```python
def _toggle_watchlist(self) -> None:
    """Toggle watchlist dock visibility."""
    # Find ChartWindow - self.parent is EmbeddedTradingViewChart, need to go up to ChartWindow
    chart_window = None
    widget = self.parent
    max_iterations = 5
    iteration = 0

    while widget is not None and iteration < max_iterations:
        iteration += 1
        if hasattr(widget, '_watchlist_dock'):
            chart_window = widget
            break
        widget = widget.parent() if hasattr(widget, 'parent') and callable(widget.parent) else None

    if not chart_window:
        logger.warning("Could not find ChartWindow in parent hierarchy (searched %d levels)", iteration)
        return

    if not hasattr(chart_window, '_watchlist_dock') or not chart_window._watchlist_dock:
        logger.warning("Watchlist dock not found")
        return

    try:
        is_visible = chart_window._watchlist_dock.isVisible()
        if is_visible:
            chart_window._watchlist_dock.hide()
            self.parent.watchlist_toggle_btn.setChecked(False)
        else:
            chart_window._watchlist_dock.show()
            self.parent.watchlist_toggle_btn.setChecked(True)

        logger.info(f"Watchlist visibility toggled: {not is_visible}")
    except Exception as e:
        logger.error(f"Error toggling watchlist: {e}", exc_info=True)
```

---

## Testing Checklist

### Manual Testing

- [ ] Theme switching works without crashes
- [ ] Connect button shows active state (orange background) when connected
- [ ] Connect button shows inactive state when disconnected
- [ ] Watchlist toggle button shows checked state visually
- [ ] Strategy Settings button shows checked state visually
- [ ] Select "1 Sekunde" timeframe and verify 1-second candles
- [ ] Select "2 Stunden" timeframe and verify 2-hour candles
- [ ] Select "8 Stunden" timeframe and verify 8-hour candles
- [ ] Market status shows correct colors for streaming/ready/connected states
- [ ] Theme switch updates status label colors

### Automated Testing

```bash
# Run these tests after fixes
pytest tests/ui/test_theme_system.py -v
pytest tests/ui/test_toolbar_buttons.py -v
pytest tests/ui/test_streaming_mixins.py -v
pytest tests/ui/test_timeframe_resolution.py -v
```

---

## Implementation Order

1. **FIX #2** (15 min) - Add missing timeframes - LOWEST RISK
2. **FIX #1** (30 min) - Fix button checked styling - LOW RISK
3. **FIX #3** (45 min) - Replace hardcoded colors - LOW RISK
4. **FIX #4** (3-4 hrs) - Consolidate streaming code - MEDIUM RISK
5. **FIX #5** (20 min) - Add null checks - LOW RISK

**Estimated Total Time:** 6-8 hours
**Recommended Approach:** Apply fixes 1-3 and 5 immediately, schedule FIX #4 for next sprint.

