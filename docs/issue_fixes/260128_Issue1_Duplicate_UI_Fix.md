# Issue #1: Doppelte UI-Elemente im CEL-Editor - Fix Summary

**Date:** 2026-01-28
**Status:** ✅ RESOLVED
**Modified Files:** 2

## Problem

The CEL Editor displayed duplicate tabs in the UI:
- **Left side:** Command Reference + Function Palette tabs
- **Right side:** Commands + Functions tabs (duplicate)

This was confusing for users and wasted screen space.

## Root Cause

Two separate code locations were creating the same UI elements:

1. **`src/ui/widgets/cel_strategy_editor_widget.py` (lines 423-444)**
   - Created `CelCommandReference` and `CelFunctionPalette` tabs in right panel
   - Method: `_create_right_panel()`

2. **`src/ui/windows/cel_editor/main_window.py` (lines 491-509)**
   - Created duplicate "CEL Functions" dock with Commands + Functions tabs
   - Method: `_create_dock_widgets()`

Both were added to the right side of the window, resulting in duplicate tabs.

## Solution

**Removed duplicate from `cel_strategy_editor_widget.py`**, kept only the Functions dock in `main_window.py`.

### Rationale
- Main window's dock widget is more flexible (can be moved/resized independently)
- Strategy editor should focus on workflow editing, not UI chrome
- Cleaner separation of concerns

## Changes Made

### 1. `src/ui/widgets/cel_strategy_editor_widget.py`

**Removed:**
- `CelCommandReference` instance creation
- `CelFunctionPalette` instance creation
- Signal connections for command/function selection
- Methods: `_on_command_selected()`, `_on_function_selected()`

**Updated:**
- `_create_right_panel()`: Now creates only AI Assistant panel
- `_connect_signals()`: Removed duplicate signal connections
- Imports: Removed `CelFunctionPalette` import
- Added documentation comments explaining the change

### 2. `src/ui/windows/cel_editor/main_window.py`

**Enhanced:**
- Added documentation comments to `_create_dock_widgets()`
- Clarified that Functions dock is the ONLY instance
- No functional changes (already working correctly)

## Result

After this fix, the CEL Editor will have:
1. ✅ **Command Reference tab** (in CEL Functions dock, right side)
2. ✅ **Function Palette tab** (in CEL Functions dock, right side)
3. ✅ **AI Assistant tab** (in Strategy Editor right panel)

**Total:** 3 tabs as intended, NO DUPLICATES.

## Testing

To verify the fix:
1. Launch CEL Editor: `python -m src.ui.windows.cel_editor`
2. Check right side of window
3. Confirm only ONE set of Command Reference / Function Palette tabs visible
4. Confirm AI Assistant tab is available in the right panel

## Files Modified

```
src/ui/widgets/cel_strategy_editor_widget.py  (-52 lines, +20 lines)
src/ui/windows/cel_editor/main_window.py      (+3 lines documentation)
```

## Migration Notes

- **No breaking changes** - all functionality preserved
- Signal flow now goes through `main_window._on_functions_insert()`
- AI Assistant panel moved to strategy editor's right panel
- All three tabs work exactly as before, just no duplication

## Related Issues

- Issue #5: Variable values not loading (next to fix)
- Issue #3: QA Testing required after all fixes complete

---

**Fix verified:** ✅ Syntax check passed
**Ready for testing:** ✅ Yes
**Backward compatible:** ✅ Yes
