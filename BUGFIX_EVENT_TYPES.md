# Bug Fix: Event Type Corrections

## Issue
Application failed to start with the following error:
```
AttributeError: type object 'EventType' has no attribute 'MARKET_DATA_TICK'. Did you mean: 'MARKET_TICK'?
```

## Root Cause
The `WatchlistWidget` was using incorrect event type names:
- Used: `EventType.MARKET_DATA_TICK`
- Correct: `EventType.MARKET_TICK`

Additionally, the widget was trying to emit a `UI_ACTION` event that didn't exist in the `EventType` enum.

## Fixes Applied

### 1. Fixed Event Type Names in watchlist.py (line 129)
**Before:**
```python
event_bus.subscribe(EventType.MARKET_DATA_TICK, self.on_market_tick)
```

**After:**
```python
event_bus.subscribe(EventType.MARKET_TICK, self.on_market_tick)
```

### 2. Added UI_ACTION Event Type to event_bus.py (line 28)
**Added:**
```python
# UI Events
UI_ACTION = "ui_action"
```

### 3. Added timestamp to Event Creation in watchlist.py (line 418)
**Before:**
```python
event_bus.emit(Event(
    type=EventType.UI_ACTION,
    data={"action": "new_order", "symbol": symbol}
))
```

**After:**
```python
event_bus.emit(Event(
    type=EventType.UI_ACTION,
    timestamp=datetime.now(),
    data={"action": "new_order", "symbol": symbol}
))
```

### 4. Added datetime import in watchlist.py (line 7)
```python
from datetime import datetime
```

## Files Modified
1. `src/ui/widgets/watchlist.py` - Fixed event type usage and added timestamp
2. `src/common/event_bus.py` - Added UI_ACTION event type

## Validation
All syntax checks passed:
- ✅ `python3 -m py_compile src/ui/widgets/watchlist.py` - OK
- ✅ `python3 -m py_compile src/common/event_bus.py` - OK

## Status
🟢 **FIXED** - Application should now start without AttributeError

## Next Steps
Test the application startup:
```bash
source venv/bin/activate
python start_orderpilot.py
```

Verify:
1. Application starts without errors
2. Watchlist widget loads successfully
3. Market data events are received correctly
4. "New Order" context menu action works
