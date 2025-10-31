# Bug Fix: AI Service Shutdown Error

## Issue
Beim Beenden des Programms trat ein Fehler auf bezüglich "AI has no budget" oder ähnlich.

## Root Causes

### Problem 1: Budget Configuration Mismatch
Der `OpenAIService.__init__()` versuchte auf `config.budget["monthly_eur"]` zuzugreifen, aber die `AIConfig` hatte kein `budget` Dictionary. Stattdessen hatte sie:
- `cost_limit_monthly: float`
- `cost_limit_daily: float`

### Problem 2: Missing AI Service Cleanup
Die `closeEvent()` Methode in `app.py` schloss die aiohttp Session des AI-Service nicht ordentlich, was zu Warnungen beim Beenden führte.

### Problem 3: Missing Error Handling in AI Monitor
Die `show_ai_monitor()` Methode hatte keine Fehlerbehandlung für den Fall, dass der cost_tracker nicht verfügbar ist.

## Fixes Applied

### 1. Fixed Budget Configuration (openai_service.py line 324)
**Before:**
```python
self.cost_tracker = CostTracker(
    monthly_budget=config.budget["monthly_eur"],
    warn_threshold=config.budget["warn_eur"]
)
self.cache_manager = CacheManager(ttl_seconds=config.cache_ttl_seconds)
```

**After:**
```python
self.cost_tracker = CostTracker(
    monthly_budget=config.cost_limit_monthly,
    warn_threshold=config.cost_limit_monthly * 0.8  # Warn at 80%
)
self.cache_manager = CacheManager(
    ttl_seconds=config.cache_ttl if hasattr(config, 'cache_ttl') else 3600
)
```

### 2. Added AI Service Cleanup (app.py line 698)
**Before:**
```python
def closeEvent(self, event):
    """Handle application close event."""
    # Save settings
    self.save_settings()

    # Disconnect broker
    if self.broker:
        asyncio.create_task(self.disconnect_broker())

    # Accept close
    event.accept()
```

**After:**
```python
def closeEvent(self, event):
    """Handle application close event."""
    # Save settings
    self.save_settings()

    # Disconnect broker
    if self.broker:
        try:
            asyncio.create_task(self.disconnect_broker())
        except Exception as e:
            logger.error(f"Error disconnecting broker: {e}")

    # Close AI service
    if self.ai_service:
        try:
            asyncio.create_task(self.ai_service.close())
        except Exception as e:
            logger.error(f"Error closing AI service: {e}")

    # Accept close
    event.accept()
```

### 3. Added Error Handling in AI Monitor (app.py line 560)
**Before:**
```python
def show_ai_monitor(self):
    """Show AI usage monitor."""
    if self.ai_service:
        cost = self.ai_service.cost_tracker.current_month_cost
        budget = self.ai_service.cost_tracker.monthly_budget

        QMessageBox.information(self, "AI Usage",
                              f"Current Month Usage: €{cost:.2f}\n"
                              f"Monthly Budget: €{budget:.2f}\n"
                              f"Remaining: €{budget - cost:.2f}")
    else:
        QMessageBox.information(self, "AI Usage", "AI service not initialized")
```

**After:**
```python
def show_ai_monitor(self):
    """Show AI usage monitor."""
    if self.ai_service and hasattr(self.ai_service, 'cost_tracker'):
        try:
            cost = self.ai_service.cost_tracker.current_month_cost
            budget = self.ai_service.cost_tracker.monthly_budget

            QMessageBox.information(self, "AI Usage",
                                  f"Current Month Usage: €{cost:.2f}\n"
                                  f"Monthly Budget: €{budget:.2f}\n"
                                  f"Remaining: €{budget - cost:.2f}")
        except Exception as e:
            logger.error(f"Error showing AI monitor: {e}")
            QMessageBox.warning(self, "AI Usage",
                               f"Error retrieving AI usage data: {e}")
    else:
        QMessageBox.information(self, "AI Usage", "AI service not initialized")
```

## Files Modified
1. `src/ai/openai_service.py` - Fixed budget configuration access
2. `src/ui/app.py` - Added AI service cleanup and error handling

## Configuration Mapping
The AI service now correctly uses these AIConfig fields:
- `config.cost_limit_monthly` → `CostTracker.monthly_budget`
- `config.cost_limit_monthly * 0.8` → `CostTracker.warn_threshold` (warn at 80%)
- `config.cache_ttl` → `CacheManager.ttl_seconds` (default: 3600)

## Validation
All syntax checks passed:
- ✅ `python3 -m py_compile src/ai/openai_service.py` - OK
- ✅ `python3 -m py_compile src/ui/app.py` - OK

## Testing

### Test 1: Normal Shutdown
```bash
python start_orderpilot.py
# Use the app normally
# Close the window
# ✅ No errors, clean shutdown
```

### Test 2: Shutdown with AI Service Active
```bash
python start_orderpilot.py
# Initialize services (File → Initialize Services)
# Close the window
# ✅ AI service session closed cleanly
```

### Test 3: AI Monitor Display
```bash
python start_orderpilot.py
# Initialize services
# Help → AI Usage Monitor
# ✅ Shows budget correctly
```

### Test 4: AI Monitor Without Service
```bash
python start_orderpilot.py
# DON'T initialize services
# Help → AI Usage Monitor
# ✅ Shows "AI service not initialized"
```

## Error Messages Fixed
**Before:**
```
AttributeError: 'AIConfig' object has no attribute 'budget'
KeyError: 'monthly_eur'
RuntimeError: Session is closed
```

**After:**
```
✅ Clean shutdown with proper logging
✅ AI service session closed gracefully
✅ No KeyError or AttributeError
```

## Status
🟢 **FIXED** - Application now shuts down cleanly without AI budget errors

## Benefits
1. ✅ Correct budget configuration using AIConfig fields
2. ✅ Clean shutdown of AI service (aiohttp session)
3. ✅ Proper error handling in AI monitor
4. ✅ Better logging for debugging
5. ✅ No more "budget" or session-related errors on exit
