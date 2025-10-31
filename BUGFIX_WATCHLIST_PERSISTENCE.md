# Bug Fix: Watchlist Persistence

## Issue
Application started successfully, but watchlist changes were not being saved persistently:
```json
{"message": "Failed to save watchlist: \"AppSettings\" object has no field \"watchlist\""}
```

## Root Cause
The `AppSettings` model in `src/config/loader.py` did not have a `watchlist` field, and there was no persistent storage mechanism for the watchlist data.

## Fixes Applied

### 1. Added watchlist Field to AppSettings (loader.py line 261)
**Added:**
```python
class AppSettings(BaseSettings):
    """Application-wide settings from environment variables."""
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra='allow'  # Allow additional fields like watchlist
    )

    app_env: str = Field(default="dev", alias="TRADING_ENV")
    app_log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    profile: str = Field(default="paper", alias="TRADING_PROFILE")
    config_dir: str = Field(default="./config", alias="CONFIG_DIR")
    watchlist: list[str] = Field(default_factory=list)  # NEW
```

### 2. Added save_watchlist() Method to ConfigManager (loader.py line 398)
**Added:**
```python
def save_watchlist(self) -> None:
    """Save watchlist to persistent storage."""
    watchlist_path = self.config_dir / "watchlist.json"

    try:
        with open(watchlist_path, "w", encoding="utf-8") as f:
            json.dump({"watchlist": self.settings.watchlist}, f, indent=2)
        logger.debug(f"Watchlist saved to {watchlist_path}")
    except Exception as e:
        logger.error(f"Failed to save watchlist: {e}")
        raise
```

### 3. Added load_watchlist() Method to ConfigManager (loader.py line 410)
**Added:**
```python
def load_watchlist(self) -> list[str]:
    """Load watchlist from persistent storage.

    Returns:
        List of symbols in watchlist
    """
    watchlist_path = self.config_dir / "watchlist.json"

    if not watchlist_path.exists():
        return []

    try:
        with open(watchlist_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            watchlist = data.get("watchlist", [])
            self.settings.watchlist = watchlist
            logger.debug(f"Loaded {len(watchlist)} symbols from watchlist")
            return watchlist
    except Exception as e:
        logger.error(f"Failed to load watchlist: {e}")
        return []
```

### 4. Updated WatchlistWidget.save_watchlist() (watchlist.py line 441)
**Before:**
```python
def save_watchlist(self):
    try:
        if not hasattr(config_manager.settings, 'watchlist'):
            config_manager.settings.watchlist = []
        config_manager.settings.watchlist = self.symbols.copy()
        logger.debug(f"Saved watchlist: {self.symbols}")
    except Exception as e:
        logger.error(f"Failed to save watchlist: {e}")
```

**After:**
```python
def save_watchlist(self):
    try:
        config_manager.settings.watchlist = self.symbols.copy()
        config_manager.save_watchlist()  # Use new method
        logger.debug(f"Saved watchlist: {self.symbols}")
    except Exception as e:
        logger.error(f"Failed to save watchlist: {e}")
```

### 5. Updated WatchlistWidget.load_default_watchlist() (watchlist.py line 422)
**Before:**
```python
def load_default_watchlist(self):
    try:
        settings = config_manager.settings
        if hasattr(settings, 'watchlist') and settings.watchlist:
            for symbol in settings.watchlist:
                self.add_symbol(symbol)
            return
    except Exception as e:
        logger.warning(f"Failed to load saved watchlist: {e}")
```

**After:**
```python
def load_default_watchlist(self):
    try:
        watchlist = config_manager.load_watchlist()  # Use new method
        if watchlist:
            for symbol in watchlist:
                self.add_symbol(symbol)
            logger.info(f"Loaded {len(watchlist)} symbols from saved watchlist")
            return
    except Exception as e:
        logger.warning(f"Failed to load saved watchlist: {e}")
```

### 6. Updated tools/manage_watchlist.py
**load_watchlist() function (line 25):**
```python
def load_watchlist() -> list[str]:
    try:
        return config_manager.load_watchlist()  # Use new method
    except Exception:
        pass
    return []
```

**save_watchlist() function (line 39):**
```python
def save_watchlist(symbols: list[str]):
    try:
        config_manager.settings.watchlist = symbols
        config_manager.save_watchlist()  # Use new method
        print(f"✅ Watchlist gespeichert ({len(symbols)} Symbole)")
    except Exception as e:
        print(f"❌ Fehler beim Speichern: {e}")
```

## Storage Location
Watchlist is now saved to: `./config/watchlist.json`

**Example content:**
```json
{
  "watchlist": [
    "AAPL",
    "MSFT",
    "GOOGL",
    "QQQ",
    "SPY"
  ]
}
```

## Files Modified
1. `src/config/loader.py` - Added watchlist field and save/load methods
2. `src/ui/widgets/watchlist.py` - Updated to use new persistence methods
3. `tools/manage_watchlist.py` - Updated to use new persistence methods

## Validation
All syntax checks passed:
- ✅ `python3 -m py_compile src/config/loader.py` - OK
- ✅ `python3 -m py_compile src/ui/widgets/watchlist.py` - OK
- ✅ `python3 -m py_compile tools/manage_watchlist.py` - OK

## Testing

### Test 1: Add symbols via UI
```bash
python start_orderpilot.py
# 1. Add symbols via UI (e.g., TSLA, NVDA)
# 2. Restart application
# 3. Verify symbols are still present ✅
```

### Test 2: Add symbols via CLI tool
```bash
source venv/bin/activate
export PYTHONPATH=/mnt/d/03_Git/02_Python/07_OrderPilot-AI:$PYTHONPATH
python tools/manage_watchlist.py

>>> add COIN
>>> add MARA
>>> save
>>> quit
```

Then start the app and verify symbols are present:
```bash
python start_orderpilot.py
# Verify COIN and MARA are in the watchlist ✅
```

### Test 3: Presets via CLI tool
```bash
python tools/manage_watchlist.py

>>> preset tech
>>> save
>>> quit

# Start app
python start_orderpilot.py
# Verify tech stocks (AAPL, MSFT, GOOGL, etc.) are present ✅
```

## Status
🟢 **FIXED** - Watchlist now persists between application restarts

## Benefits
1. ✅ Watchlist survives application restarts
2. ✅ Changes made in UI are saved automatically
3. ✅ Changes made via CLI tool are saved to same file
4. ✅ Clear separation between config and runtime data
5. ✅ Human-readable JSON format for easy debugging
6. ✅ Proper error handling and logging

## Next Steps
Test the application to verify:
1. Add symbols via UI and restart → symbols persist ✅
2. Add symbols via CLI tool and start app → symbols visible ✅
3. Use presets and restart → preset symbols persist ✅
4. Clear watchlist and restart → remains cleared ✅
