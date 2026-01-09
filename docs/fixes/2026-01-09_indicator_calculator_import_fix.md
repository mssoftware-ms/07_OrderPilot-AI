# Fix: Import Errors After market_context.py Refactoring

**Date:** 2026-01-09
**Issues:** Multiple ImportError issues after module refactoring
**Status:** ✅ ALL RESOLVED

## Problems

The application failed to start with TWO sequential import errors:

### Error 1: IndicatorCalculator
```python
ImportError: cannot import name 'IndicatorCalculator' from 'src.core.trading_bot.market_context_indicators'
```

### Error 2: Level (after fixing Error 1)
```python
ImportError: cannot import name 'Level' from 'src.core.trading_bot.level_engine'
```

The error occurred in the import chain:
```
start_orderpilot.py
  → ui.app
    → ui.app_components
      → ui.chart_window_manager
        → ui.widgets.chart_window
          → ui.widgets.bitunix_trading
            → bot_tab
              → src.core.trading_bot
                → market_context_builder
                  ❌ from .market_context_indicators import IndicatorCalculator
```

## Root Cause

During a refactoring of `market_context.py` (868 LOC monolith → 8 modular files), the `IndicatorCalculator` class was removed but `market_context_builder.py` still tried to import it.

**What happened:**
- `market_context_indicators.py` now only contains the `IndicatorSnapshot` dataclass
- The indicator calculation functionality was already moved to `src/core/indicators/engine.py` (IndicatorEngine)
- `market_context_builder.py` was still trying to import the non-existent `IndicatorCalculator`

## Solutions

### Fix 1: IndicatorCalculator Import

#### 1. Created New Adapter Class

Created `/src/core/trading_bot/indicator_calculator.py` as a wrapper around the existing `IndicatorEngine`:

**Key features:**
- Provides a simple `calculate_indicators(df)` method expected by `MarketContextBuilder`
- Uses the existing `IndicatorEngine` from `src.core.indicators`
- Calculates all required indicators:
  - EMAs (9, 20, 50, 200)
  - RSI (14)
  - MACD (12/26/9)
  - Stochastic (14/3)
  - Bollinger Bands (20/2)
  - ATR (14)
  - ADX (14)
  - Volume indicators
- Adds calculated values as DataFrame columns

### 2. Updated Import in market_context_builder.py

**Before:**
```python
from .market_context_indicators import IndicatorCalculator
```

**After:**
```python
from .indicator_calculator import IndicatorCalculator
```

### 3. Fixed Method Call

Fixed incorrect method call on line 333:

**Before:**
```python
volatility_state = self._determine_volatility_state(atr_pct) if atr_pct else "NORMAL"
```

**After:**
```python
volatility_state = self._regime_detector.determine_volatility_state(atr_pct) if atr_pct else "NORMAL"
```

The method exists in `RegimeDetector`, not `MarketContextBuilder`.

### Fix 2: Level and Related Classes Export

The `level_engine.py` module was not re-exporting classes from `level_engine_state.py` that the `__init__.py` was trying to import.

**Updated:** `/src/core/trading_bot/level_engine.py`

Added re-exports to the import section:
```python
from src.core.trading_bot.level_engine_state import (
    DetectionMethod,      # ← Added
    Level,                # ← Added
    LevelEngineConfig,
    LevelsResult,
    LevelStrength,        # ← Added
    LevelType,
)
```

Updated `__all__` to include the re-exported classes:
```python
__all__ = [
    # Main class and functions
    "LevelEngine",
    "get_level_engine",
    "reset_level_engine",
    "detect_levels",
    # Re-exported from level_engine_state for convenience
    "Level",              # ← Added
    "LevelEngineConfig",
    "LevelsResult",
    "LevelType",
    "LevelStrength",      # ← Added
    "DetectionMethod",    # ← Added
]
```

## Files Modified

1. ✅ **Created:** `/src/core/trading_bot/indicator_calculator.py` (178 lines)
2. ✅ **Modified:** `/src/core/trading_bot/market_context_builder.py`
   - Line 35: Updated import statement (IndicatorCalculator)
   - Line 333: Fixed volatility state calculation (RegimeDetector method)
3. ✅ **Modified:** `/src/core/trading_bot/level_engine.py`
   - Lines 27-28, 31-32: Added DetectionMethod, Level, LevelStrength to imports
   - Lines 221-226: Added re-exported classes to `__all__`

## Verification

The fixes were verified by:

1. ✅ `python start_orderpilot.py --help` - Works without import errors
2. ✅ No other files import `IndicatorCalculator` from `market_context_indicators`
3. ✅ Application startup banner displays correctly
4. ✅ Import test shows all modules can be imported (only sqlalchemy dependency missing in test env)
5. ✅ Both ImportError issues resolved
6. ✅ Application ready to start in Windows with .venv

## Architecture Notes

The indicator calculation architecture now follows this pattern:

```
MarketContextBuilder
  └─> IndicatorCalculator (adapter/wrapper)
       └─> IndicatorEngine (src/core/indicators)
            └─> TrendIndicators, MomentumIndicators, VolatilityIndicators, etc.
```

This maintains separation of concerns:
- `IndicatorEngine`: Generic, reusable indicator calculation
- `IndicatorCalculator`: Trading-bot-specific wrapper that knows which indicators to calculate
- `MarketContextBuilder`: High-level context builder that doesn't need to know indicator details

## Related Files

- `/src/core/indicators/` - Main indicator calculation system
- `/src/core/trading_bot/market_context_detectors.py` - RegimeDetector with volatility_state method
- `/src/core/trading_bot/market_context_indicators.py` - Only contains IndicatorSnapshot dataclass
- `/src/core/trading_bot/market_context_factories.py` - Factory functions for creating contexts

## Testing Checklist

- [x] Application starts without ImportError for IndicatorCalculator
- [x] Application starts without ImportError for Level
- [x] Help command works (`--help`)
- [x] Dependency check runs without import errors (only missing dependencies shown)
- [x] All trading_bot module imports work correctly
- [ ] Full application startup in Windows with .venv (ready for user to test)
- [ ] Indicator calculation produces correct DataFrame columns (requires integration test)
- [ ] Level detection works with refactored modules (requires integration test)

## Notes for Future Refactoring

- Consider renaming `IndicatorCalculator` to `TradingBotIndicatorAdapter` for clarity
- Document the relationship between `IndicatorEngine` and `IndicatorCalculator` in ARCHITECTURE.md
- Add unit tests for `IndicatorCalculator.calculate_indicators()` method
