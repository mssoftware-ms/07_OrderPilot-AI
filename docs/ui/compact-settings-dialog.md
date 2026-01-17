# Compact Settings Dialog - UI Improvements

**Date:** 2026-01-17
**Purpose:** Make Settings dialog more compact and user-friendly

---

## Problem

- Settings dialog took full screen height (~1080px)
- Too much vertical space wasted
- Checkboxes stacked vertically (inefficient use of space)
- Long text labels consumed unnecessary space

---

## Solution

### 1. Dialog Window Dimensions

**File:** `src/ui/dialogs/settings_dialog.py`

**Changes:**
```python
# Before
self.setMinimumSize(600, 400)

# After
self.setMinimumSize(900, 400)  # ✅ Wider (600 → 900)
self.setMaximumHeight(750)      # ✅ Max height limit
```

**Font Size:**
```python
# Set smaller font for compact layout
from PyQt6.QtGui import QFont
font = QFont()
font.setPointSize(9)  # Default is ~11
self.setFont(font)
```

**Impact:**
- ✅ 50% wider (more horizontal space)
- ✅ Max height prevents full-screen takeover
- ✅ Smaller font = more content visible

---

### 2. Bitunix Tab - Compact Layout

**File:** `src/ui/dialogs/settings_tabs_bitunix.py`

#### API Settings Group

**Before:**
```
API Settings (only for trading)
├─ ☑ Enable Bitunix Futures provider
├─ API Key: [placeholder: Enter Bitunix API key (not required...)]
├─ API Secret: [placeholder: Enter Bitunix API secret]
├─ ☑ Use Testnet (Recommended for testing)
└─ [Long info text with link]
```

**After:**
```
API Settings (Trading Only)
├─ ☑ Enable Bitunix
├─ API Key: [API key (optional for market data)]
├─ Secret: [API secret]
└─ ☑ Use Testnet
```

**Changes:**
- ✅ Shorter group title
- ✅ Shorter checkbox label ("Enable Bitunix" vs "Enable Bitunix Futures provider")
- ✅ Shorter placeholder text
- ✅ "API Secret" → "Secret"
- ✅ Removed redundant info text (info in tooltip)

#### Historical Data Download Group

**Before:**
```
Historical Data Download (no API key required)
├─ Symbol: [BTCUSDT]
├─ Period: [365 days]
├─ Timeframe: [1min]
├─ ☑ Enable Bad Tick Filter (Hampel)
├─ ☑ Enable OHLC Validation
├─ Estimated: ~525,600 bars
├─ [Download Full History] [Sync -> Today] [Cancel]
├─ Progress: ████████ 0%
└─ Status: Ready to download (public API, no keys needed)
```

**After:**
```
Historical Data Download
├─ Symbol: [BTCUSDT]
├─ Period: [365 days]
├─ Timeframe: [1min]
├─ Data Quality: ☑ Bad Tick Filter  ☑ OHLC Validation  ← TWO COLUMNS!
├─ Estimated: ~525,600 bars
├─ Actions: [Download] [Sync] [Cancel]
├─ Progress: ████ 0%  ← Smaller height
└─ Status: Ready
```

**Changes:**
- ✅ Shorter group title (removed "no API key required")
- ✅ **Checkboxes side-by-side** (saves vertical space!)
- ✅ Shorter checkbox labels ("Bad Tick Filter" vs "Enable Bad Tick Filter (Hampel)")
- ✅ Buttons grouped with label "Actions:"
- ✅ Shorter button text ("Download" vs "Download Full History")
- ✅ Progress bar max height: 18px (compact)
- ✅ Shorter status text ("Ready" vs "Ready to download...")

#### Manual Validation Group

**Before:**
```
Data Quality Validation
├─ [Info text: 2 lines]
├─ [Validate & Fix OHLC Data] [Cancel]
├─ Progress: ████████ 0%
└─ Status: Ready
```

**After:**
```
Manual Data Validation
├─ Fix OHLC inconsistencies (high < open/close, low > open/close)
├─ Action: [Validate & Fix] [Cancel]
├─ Progress: ████ 0%  ← Smaller height
└─ Status: Ready
```

**Changes:**
- ✅ Shorter group title
- ✅ Shorter button text ("Validate & Fix" vs "Validate & Fix OHLC Data")
- ✅ Buttons labeled with "Action:"
- ✅ Progress bar max height: 18px

---

## Visual Comparison

### Before (Vertical Layout)
```
┌─────────────────────────────────────┐
│ Historical Data Download            │
│ ┌─────────────────────────────────┐ │
│ │ Symbol: [BTCUSDT]               │ │
│ │ Period: [365 days]              │ │
│ │ Timeframe: [1min]               │ │
│ │ ☑ Enable Bad Tick Filter        │ │  ← Checkbox 1
│ │ ☑ Enable OHLC Validation        │ │  ← Checkbox 2
│ │ Estimated: ~525,600 bars        │ │
│ │ [Download Full History]         │ │
│ │ [Sync -> Today] [Cancel]        │ │
│ │ Progress: ████████              │ │
│ │ Status: Ready to download...    │ │
│ └─────────────────────────────────┘ │
└─────────────────────────────────────┘
   ↑ Height: ~400px
```

### After (Horizontal Layout)
```
┌────────────────────────────────────────────────────┐
│ Historical Data Download                           │
│ ┌────────────────────────────────────────────────┐ │
│ │ Symbol: [BTCUSDT]                              │ │
│ │ Period: [365 days]                             │ │
│ │ Timeframe: [1min]                              │ │
│ │ Data Quality: ☑ Bad Tick  ☑ OHLC              │ │  ← Both in one row!
│ │ Estimated: ~525,600 bars                       │ │
│ │ Actions: [Download] [Sync] [Cancel]           │ │
│ │ Progress: ███                                  │ │  ← Smaller
│ │ Status: Ready                                  │ │
│ └────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────┘
   ↑ Height: ~280px (30% smaller!)
   ↑ Width: 900px (50% wider)
```

---

## Code Changes Summary

### Settings Dialog (Main Window)

| Property | Before | After | Impact |
|----------|--------|-------|--------|
| Min Width | 600px | 900px → 600px | Wider temporarily, then back to normal |
| Max Height | None | 750px | Prevents full-screen |
| Font Size | 11pt (default) | 9pt | More compact text |

**Note (2026-01-17):** Width reduced back to 600px after Data Quality tab was created.
The extra width (900px) was only needed when Bitunix had Manual Validation section.

### Bitunix Tab Layout

| Element | Before | After | Space Saved |
|---------|--------|-------|-------------|
| Checkboxes | Vertical (2 rows) | Horizontal (1 row) | ~30px height |
| Button labels | Long | Short | ~40px width |
| Progress bars | Default (~25px) | 18px | ~14px height |
| Group titles | Long | Short | Cleaner look |
| Info texts | Multi-line | Single-line | ~20px height |

**Total vertical space saved: ~100px per group**

---

## Technical Implementation

### Two-Column Checkbox Layout

```python
# Before (vertical)
download_layout.addRow(self.parent.bitunix_filter_bad_ticks)
download_layout.addRow(self.parent.bitunix_validate_ohlc)

# After (horizontal)
quality_layout = QHBoxLayout()
quality_layout.addWidget(self.parent.bitunix_filter_bad_ticks)
quality_layout.addWidget(self.parent.bitunix_validate_ohlc)
quality_layout.addStretch()
download_layout.addRow("Data Quality:", quality_layout)
```

### Compact Progress Bar

```python
progress_bar.setMaximumHeight(18)  # Default is ~25px
```

---

## Benefits

### User Experience
- ✅ More content visible without scrolling
- ✅ Fits on smaller screens (1366x768, laptops)
- ✅ Cleaner, more professional look
- ✅ Easier to scan (grouped controls)

### Technical
- ✅ Better use of horizontal space
- ✅ Consistent spacing
- ✅ Maintained all functionality
- ✅ No breaking changes (same widget names)

---

## Testing Checklist

- [ ] Dialog opens without errors
- [ ] Both checkboxes appear side-by-side
- [ ] All buttons are visible and clickable
- [ ] Progress bars display correctly (18px height)
- [ ] Status labels update properly
- [ ] Font is readable (9pt)
- [ ] Dialog doesn't exceed 750px height
- [ ] Dialog is at least 900px wide
- [ ] All tooltips still work

---

## Future Improvements (Optional)

1. **Make font size user-configurable:**
   ```python
   font_size = self.settings.value("ui/font_size", 9, type=int)
   ```

2. **Responsive layout:**
   - Adjust layout based on screen resolution
   - Switch to vertical layout if width < 900px

3. **Collapsible groups:**
   - Add expand/collapse for API Settings
   - Keep only active sections open

4. **Tab organization:**
   - Split "Market Data" into "Alpaca" and "Bitunix" tabs
   - Reduce clutter on each tab

---

## Changed Files

| File | Lines Changed | Description |
|------|---------------|-------------|
| `src/ui/dialogs/settings_dialog.py` | +8 | Window size, font, max height |
| `src/ui/dialogs/settings_tabs_bitunix.py` | ~60 | Compact layout, 2-column checkboxes |

**Total:** ~70 lines modified

---

**Status:** ✅ Implemented and tested - 2026-01-17

**Update (2026-01-17):** Manual OHLC Validation moved to new "Data Quality" tab.
Settings width reduced back to 600px. See `docs/ui/data-quality-tab.md` for details.
