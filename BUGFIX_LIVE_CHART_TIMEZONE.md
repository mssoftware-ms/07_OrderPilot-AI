# Bugfix Report: Live Chart Update Issue

## Issue Description
The live chart in the popup window was not updating in real-time. The logs showed the error:
`js: Error: Cannot update oldest data, last time=[object Object], new time=[object Object]`

## Root Cause Analysis
The `EmbeddedTradingViewChart` widget processes live market ticks in `_on_market_tick`.
- **Previous Behavior:** The code ignored the timestamp from the `MARKET_DATA_TICK` event and generated a new timestamp using `datetime.now()` (local system time).
- **The Conflict:** Historical data loaded from Alpaca is typically in UTC. If the local system time (e.g., CET) is different or slightly behind the server time, or if the timezone handling creates a timestamp value smaller than the last historical bar, the charting library rejects the update to preserve chronological order.

## Fix Implementation
Modified `src/ui/widgets/embedded_tradingview_chart.py`:
1.  **Imports:** Added `timezone` to `datetime` imports.
2.  **Logic Update:** Refactored `_on_market_tick` to:
    - Attempt to retrieve the timestamp from `tick_data['timestamp']`.
    - Fallback to `event.timestamp`.
    - Fallback to `datetime.now(timezone.utc)` only if no event timestamp is present.
    - Explicitly convert the timestamp to UTC before converting to a Unix timestamp.

## Code Changes
```python
# src/ui/widgets/embedded_tradingview_chart.py

# ... imports ...
from datetime import datetime, timezone

# ... inside _on_market_tick ...
            # --- Time Handling Fix ---
            # Use timestamp from event, NOT system time
            ts = tick_data.get('timestamp')
            if ts is None:
                ts = event.timestamp

            if ts is None:
                ts = datetime.now(timezone.utc)
            
            # ... conversions to ensure UTC ...
```

## Verification
The fix ensures that live ticks use the same time reference (Server/UTC) as the historical bars, resolving the "Cannot update oldest data" error and allowing the candle to build up in real-time.
