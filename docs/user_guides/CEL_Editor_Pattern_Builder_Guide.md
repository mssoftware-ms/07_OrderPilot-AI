# CEL Editor - Pattern Builder User Guide

**Version**: 1.0
**Date**: 2026-01-20
**For**: OrderPilot-AI Trading Platform

---

## Table of Contents

1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [Creating Your First Pattern](#creating-your-first-pattern)
4. [Working with Candles](#working-with-candles)
5. [Creating Relation Lines](#creating-relation-lines)
6. [Using the Properties Panel](#using-the-properties-panel)
7. [Pattern Management](#pattern-management)
8. [Tips & Best Practices](#tips--best-practices)
9. [Keyboard Shortcuts](#keyboard-shortcuts)
10. [Troubleshooting](#troubleshooting)

---

## Introduction

### What is the Pattern Builder?

The **CEL Editor Pattern Builder** is a visual tool for creating candlestick patterns used in trading strategies. It allows you to:

- **Design custom patterns** with multiple candles
- **Define relationships** between candles (greater, less, equal)
- **Set precise OHLC values** (Open, High, Low, Close)
- **Save and load patterns** for reuse
- **Export patterns** to CEL (Common Expression Language) for automated trading

### Use Cases

- **Strategy Development**: Create visual representations of entry/exit conditions
- **Pattern Recognition**: Define custom candlestick patterns for backtesting
- **Technical Analysis**: Build complex multi-candle patterns
- **Automated Trading**: Export patterns as executable trading rules

---

## Getting Started

### Opening the Pattern Builder

1. Launch **OrderPilot-AI**
2. Navigate to **Tools** → **CEL Editor**
3. Select **Pattern Builder** tab
4. You'll see three main areas:
   - **Toolbar** (top) - Candle type selection
   - **Canvas** (center) - Visual pattern design area
   - **Properties Panel** (right) - Candle details editor

### Interface Overview

```
┌─────────────────────────────────────────────────────────┐
│  Toolbar: [Bullish] [Bearish] [Doji] [+] [Undo] [Redo] │
├───────────────────────────────┬─────────────────────────┤
│                               │  Properties Panel       │
│                               │  ┌───────────────────┐  │
│        Canvas                 │  │ Candle Type: ...  │  │
│     (Drop candles here)       │  │ Open:      50.00  │  │
│                               │  │ High:      90.00  │  │
│                               │  │ Low:       30.00  │  │
│                               │  │ Close:     85.00  │  │
│                               │  │ Index:     0      │  │
│                               │  │ [Apply Changes]   │  │
│                               │  └───────────────────┘  │
└───────────────────────────────┴─────────────────────────┘
```

---

## Creating Your First Pattern

### Step 1: Add a Bullish Candle

1. **Select candle type** in toolbar:
   - Click **Bullish** button (green)
   - Button will highlight to show selection

2. **Add candle to canvas**:
   - Click **Add (+)** button in toolbar
   - OR right-click on canvas → **Add Candle**
   - A green bullish candle appears on canvas

3. **Position the candle**:
   - Click and drag the candle to move it
   - Candles auto-position by default (left to right)

### Step 2: Add a Bearish Candle

1. **Select candle type**:
   - Click **Bearish** button (red) in toolbar

2. **Add candle**:
   - Click **Add (+)** button
   - Red bearish candle appears to the right of first candle

### Step 3: Create a Relation Line

1. **Select first candle**:
   - Click on the **bullish candle** (it highlights)

2. **Add relation**:
   - Right-click on canvas → **Add Relation**
   - OR use toolbar **Relation** button

3. **Select second candle**:
   - Click on the **bearish candle**
   - Relation line appears connecting the two candles

4. **Choose relation type**:
   - Dialog appears: **Greater (>)**, **Less (<)**, **Equal (=)**
   - Select **Greater (>)** (bullish candle is higher than bearish)
   - Click **OK**

### Step 4: Save Your Pattern

1. **Save pattern**:
   - Click **File** → **Save Pattern**
   - OR press **Ctrl+S**

2. **Enter pattern name**:
   - Example: "Bullish Reversal"
   - Click **Save**

**Congratulations!** You've created your first pattern.

---

## Working with Candles

### Candle Types

**Three candle types available:**

1. **Bullish (Green)**
   - Close > Open
   - Indicates upward price movement
   - Visual: Green body, wick above/below

2. **Bearish (Red)**
   - Close < Open
   - Indicates downward price movement
   - Visual: Red body, wick above/below

3. **Doji (Gray)**
   - Close ≈ Open
   - Indicates indecision/reversal
   - Visual: Small/no body, long wicks

### Adding Candles

**Method 1: Toolbar**
```
1. Select candle type (Bullish/Bearish/Doji)
2. Click Add (+) button
3. Candle appears on canvas
```

**Method 2: Right-Click Menu**
```
1. Right-click on canvas
2. Select "Add Candle"
3. Choose type from submenu
```

**Method 3: Keyboard Shortcut**
```
Ctrl+B = Add Bullish
Ctrl+R = Add Bearish (Red)
Ctrl+D = Add Doji
```

### Moving Candles

**Drag & Drop:**
- Click and hold on candle
- Drag to desired position
- Release to drop

**Snap to Grid:** (Optional)
- Enable: **View** → **Snap to Grid**
- Candles align to grid positions

### Removing Candles

**Method 1: Delete Key**
```
1. Select candle (click on it)
2. Press Delete key
```

**Method 2: Right-Click Menu**
```
1. Right-click on candle
2. Select "Remove Candle"
```

**Method 3: Toolbar**
```
1. Select candle
2. Click Remove (-) button in toolbar
```

### Changing Candle Type

**Via Properties Panel:**
```
1. Select candle on canvas
2. Properties panel shows candle details
3. Change "Candle Type" dropdown
4. Click "Apply Changes"
```

**Via Right-Click Menu:**
```
1. Right-click on candle
2. Select "Change Type" → choose new type
```

### Candle Selection

**Single Selection:**
- Click on candle
- Candle highlights (blue border)
- Properties panel enables

**Multiple Selection:**
- Hold **Ctrl** and click multiple candles
- OR drag selection box around candles
- Properties panel shows "X candles selected"

**Clear Selection:**
- Click on empty canvas area
- OR press **Esc** key

---

## Creating Relation Lines

### What are Relation Lines?

Relation lines define **relationships between candles**:

- **Greater (>)**: First candle's value > Second candle's value
- **Less (<)**: First candle's value < Second candle's value
- **Equal (=)**: First candle's value = Second candle's value

### Adding Relations

**Step-by-Step:**

1. **Select source candle**:
   - Click on first candle (e.g., candle at index 0)

2. **Initiate relation**:
   - Right-click → **Add Relation**
   - OR click **Relation** button in toolbar

3. **Select target candle**:
   - Click on second candle (e.g., candle at index 1)

4. **Choose relation type**:
   - Dialog appears with options:
     - **Greater (>)** - Source > Target
     - **Less (<)** - Source < Target
     - **Equal (=)** - Source = Target
   - Select appropriate type
   - Click **OK**

5. **Relation appears**:
   - Line connects the two candles
   - Arrow shows direction
   - Label shows relation type (>, <, =)

### Relation Examples

**Bullish Continuation:**
```
Candle 0 (Bullish) > Candle 1 (Doji) > Candle 2 (Bullish)

Interpretation:
- First bullish candle is stronger than doji
- Doji shows consolidation
- Second bullish candle confirms continuation
```

**Bearish Reversal:**
```
Candle 0 (Bullish) < Candle 1 (Bearish)

Interpretation:
- Bullish candle loses strength
- Bearish candle engulfs/exceeds bullish
- Indicates potential reversal
```

### Removing Relations

**Method 1: Select & Delete**
```
1. Click on relation line
2. Press Delete key
```

**Method 2: Right-Click Menu**
```
1. Right-click on relation line
2. Select "Remove Relation"
```

### Editing Relations

**Change relation type:**
```
1. Right-click on relation line
2. Select "Change Relation Type"
3. Choose new type (>, <, =)
4. Click OK
```

---

## Using the Properties Panel

### Overview

The **Properties Panel** shows detailed information about selected candles and allows precise editing.

**Location**: Right side of Pattern Builder window

**States**:
- **Disabled** (gray) - No candle selected
- **Single Candle** (enabled) - One candle selected
- **Multiple Candles** (disabled) - Multiple candles selected

### Editing Candle Properties

**When Single Candle Selected:**

1. **Candle Type**:
   - Dropdown: Bullish, Bearish, Doji
   - Changes candle color and behavior

2. **Open**:
   - Opening price (numeric)
   - Default: 50.0

3. **High**:
   - Highest price (numeric)
   - Must be ≥ Open and Close
   - Default: 90.0

4. **Low**:
   - Lowest price (numeric)
   - Must be ≤ Open and Close
   - Default: 30.0

5. **Close**:
   - Closing price (numeric)
   - Default: 85.0

6. **Index**:
   - Candle position in pattern (read-only)
   - Auto-assigned: 0, 1, 2, ...

### OHLC Validation Rules

**Automatic validation ensures candle integrity:**

✅ **Valid OHLC:**
```
High = 90.0 (highest)
Open = 50.0
Close = 85.0
Low = 30.0 (lowest)

✓ High ≥ Open, Close
✓ Low ≤ Open, Close
```

❌ **Invalid OHLC:**
```
High = 50.0  ← Error!
Open = 50.0
Close = 85.0
Low = 30.0

✗ High < Close (violates rule)
```

**Validation Messages:**
- **⚠ High must be >= Open, Low, and Close**
- **⚠ Low must be <= Open, High, and Close**
- **⚠ Open and Close must be between High and Low**

### Applying Changes

**After editing properties:**

1. **Click "Apply Changes" button**
   - Changes apply to canvas immediately
   - Candle visual updates
   - Pattern recalculates

2. **Visual Feedback**:
   - Candle color changes (if type changed)
   - Candle size adjusts (if OHLC changed)
   - Validation message appears (if invalid)

3. **Undo if Needed**:
   - Press **Ctrl+Z** to undo
   - OR click **Undo** button in toolbar

---

## Pattern Management

### Saving Patterns

**Save Pattern to File:**

1. **Click File → Save Pattern**
   - OR press **Ctrl+S**

2. **Choose location**:
   - Navigate to desired folder
   - Default: `patterns/` directory

3. **Enter filename**:
   - Example: `bullish_engulfing.json`
   - Click **Save**

**Pattern Data Includes:**
- All candles (type, OHLC, index)
- All relations (type, source, target)
- Pattern metadata (name, created date)

### Loading Patterns

**Load Pattern from File:**

1. **Click File → Load Pattern**
   - OR press **Ctrl+O**

2. **Select file**:
   - Navigate to pattern file (.json)
   - Click **Open**

3. **Pattern loads**:
   - Canvas clears
   - All candles recreated
   - All relations recreated
   - Zoom adjusts to fit

**Merge Pattern:**
- **File → Merge Pattern**
- Adds pattern to existing canvas (doesn't clear)

### Clearing Pattern

**Clear All Candles & Relations:**

1. **Click Edit → Clear Pattern**
   - OR press **Ctrl+Shift+N**

2. **Confirmation dialog**:
   - "Clear entire pattern?"
   - Click **Yes** to proceed

**⚠️ Warning**: This action can be undone with **Ctrl+Z**.

### Exporting Patterns

**Export to CEL (Common Expression Language):**

1. **Click File → Export to CEL**

2. **Enter export settings**:
   - CEL function name (e.g., `isBullishEngulfing`)
   - Variable names for candles (c0, c1, c2, ...)

3. **Click Export**:
   - CEL code generated
   - Copy to clipboard or save to file

**Example Export:**
```cel
// Bullish Engulfing Pattern
function isBullishEngulfing(c0, c1) {
  return c1.close > c0.close &&
         c1.open < c0.open &&
         c1.type == "bullish" &&
         c0.type == "bearish";
}
```

---

## Tips & Best Practices

### Pattern Design

✅ **DO:**
- **Start simple**: Begin with 2-3 candles, add complexity later
- **Use descriptive names**: "Bullish Reversal" not "Pattern1"
- **Test patterns**: Load into backtest engine to verify effectiveness
- **Save frequently**: Use **Ctrl+S** often
- **Document patterns**: Add comments explaining strategy logic

❌ **DON'T:**
- **Overcomplicate**: Avoid 10+ candle patterns (hard to match)
- **Ignore OHLC validation**: Invalid candles won't match real data
- **Forget relations**: Relations define pattern logic (essential)
- **Skip testing**: Always backtest before live trading

### Performance Optimization

**For Large Patterns (50+ candles):**
- **Use Zoom Fit**: **View → Zoom Fit** (or **Ctrl+0**) to see all candles
- **Group related candles**: Use **Ctrl+G** to group (future feature)
- **Limit relations**: Too many relations (100+) can slow rendering

**Memory Management:**
- Pattern Builder handles **500+ candles** efficiently
- Typical patterns use **<5 MB memory**
- Clear unused patterns to free memory

### Workflow Efficiency

**Keyboard-First Approach:**
```
Ctrl+B    = Add Bullish candle
Ctrl+R    = Add Bearish candle
Ctrl+D    = Add Doji candle
Ctrl+Z    = Undo
Ctrl+Y    = Redo
Ctrl+S    = Save pattern
Ctrl+O    = Open pattern
Delete    = Remove selected candle/relation
Esc       = Clear selection
```

**Right-Click Menu:**
- Fastest for context-specific actions
- Available on candles, relations, and canvas

---

## Keyboard Shortcuts

### Global Shortcuts

| Shortcut | Action |
|----------|--------|
| **Ctrl+N** | New pattern |
| **Ctrl+O** | Open pattern |
| **Ctrl+S** | Save pattern |
| **Ctrl+Shift+S** | Save pattern as... |
| **Ctrl+W** | Close window |
| **Ctrl+Q** | Quit application |

### Editing Shortcuts

| Shortcut | Action |
|----------|--------|
| **Ctrl+Z** | Undo |
| **Ctrl+Y** | Redo |
| **Ctrl+X** | Cut selection |
| **Ctrl+C** | Copy selection |
| **Ctrl+V** | Paste |
| **Delete** | Remove selected |
| **Ctrl+A** | Select all |
| **Esc** | Clear selection |

### Candle Shortcuts

| Shortcut | Action |
|----------|--------|
| **Ctrl+B** | Add Bullish candle |
| **Ctrl+R** | Add Bearish candle |
| **Ctrl+D** | Add Doji candle |
| **Ctrl+E** | Edit candle properties |
| **Ctrl+L** | Add relation line |

### View Shortcuts

| Shortcut | Action |
|----------|--------|
| **Ctrl+Plus** | Zoom in |
| **Ctrl+Minus** | Zoom out |
| **Ctrl+0** | Zoom fit |
| **Ctrl+1** | Zoom 100% |
| **Ctrl+G** | Toggle grid |

---

## Troubleshooting

### Common Issues

#### Issue: Candle won't add to canvas

**Symptoms**:
- Click Add (+) button, nothing happens
- OR error message appears

**Solutions**:
1. **Check candle type selected**:
   - Ensure Bullish/Bearish/Doji button is highlighted
   - If none selected, click one

2. **Check canvas space**:
   - Zoom out if canvas appears full
   - Use **Ctrl+0** to zoom fit

3. **Check memory**:
   - Close other applications if system slow
   - Pattern Builder uses <100 MB for typical patterns

#### Issue: Properties panel disabled

**Symptoms**:
- Properties panel grayed out
- Can't edit OHLC values

**Solutions**:
1. **Select a single candle**:
   - Click on one candle only
   - Multiple selection disables properties panel

2. **Clear selection and reselect**:
   - Click on empty canvas area
   - Click on desired candle

#### Issue: Relation line won't create

**Symptoms**:
- Click two candles, no line appears
- OR error message "Invalid relation"

**Solutions**:
1. **Check selection order**:
   - Select source candle FIRST
   - Then initiate relation (right-click → Add Relation)
   - Then select target candle

2. **Check if relation already exists**:
   - Remove existing relation between candles
   - Create new relation

3. **Check candle indices**:
   - Relations work best between adjacent candles (0→1, 1→2)
   - Avoid long-distance relations (0→10) if possible

#### Issue: OHLC validation error

**Symptoms**:
- **⚠ High must be >= Open, Low, and Close**
- Changes don't apply

**Solutions**:
1. **Fix OHLC values**:
   ```
   High = 90.0  (must be highest)
   Open = 50.0
   Close = 85.0
   Low = 30.0   (must be lowest)
   ```

2. **Common mistakes**:
   - High < Close → Increase High
   - Low > Open → Decrease Low

3. **Use realistic values**:
   - Open: 40-60
   - High: 80-100
   - Low: 20-40
   - Close: 70-90

#### Issue: Pattern won't save

**Symptoms**:
- Click Save, error appears
- OR file not created

**Solutions**:
1. **Check file permissions**:
   - Ensure write access to patterns/ directory
   - Try saving to different location

2. **Check filename**:
   - Avoid special characters (/, \, :, *, ?, ", <, >, |)
   - Use alphanumeric + underscore only
   - Example: `bullish_engulfing.json`

3. **Check disk space**:
   - Ensure sufficient disk space (patterns are <1 MB)

#### Issue: Undo/Redo not working

**Symptoms**:
- Ctrl+Z does nothing
- Undo button grayed out

**Solutions**:
1. **Check undo stack**:
   - Undo only works after making changes
   - Load pattern doesn't populate undo stack (by design)

2. **Try redo**:
   - If you undid too far, use **Ctrl+Y** to redo

3. **Restart if stuck**:
   - Close and reopen Pattern Builder
   - Load last saved pattern

---

## Advanced Features

### Pattern Statistics

**View pattern statistics:**

1. **Click View → Pattern Statistics**
2. **Statistics window shows**:
   - Total candles
   - Total relations
   - Candle type breakdown (Bullish: X, Bearish: Y, Doji: Z)
   - Pattern complexity score

**Use statistics to:**
- Evaluate pattern complexity
- Ensure balanced candle types
- Identify overly complex patterns

### Pattern Validation

**Validate pattern before export:**

1. **Click Tools → Validate Pattern**
2. **Validation checks**:
   - All candles have valid OHLC
   - Relations are logically consistent
   - No orphaned candles (not connected)
   - No circular relations

3. **Validation report**:
   - ✅ Pattern valid for export
   - OR ❌ Errors/warnings listed

### Batch Operations

**Apply changes to multiple candles:**

1. **Select multiple candles** (Ctrl+Click or drag select)
2. **Right-click → Batch Edit**
3. **Choose operation**:
   - Change type (all to Bullish/Bearish/Doji)
   - Scale OHLC (multiply by factor)
   - Align candles (horizontal/vertical)

---

## Next Steps

**After mastering Pattern Builder:**

1. **Export patterns to CEL**:
   - Use patterns in trading strategies
   - Combine with other CEL functions

2. **Backtest patterns**:
   - Load patterns into Backtest Engine
   - Test on historical data
   - Optimize for profit

3. **Create pattern library**:
   - Save common patterns
   - Organize by category (reversals, continuations, etc.)
   - Share with team

4. **Advanced CEL integration**:
   - Read CEL Editor documentation
   - Combine patterns with custom logic
   - Build complete trading systems

---

## Support & Resources

**Documentation**:
- CEL Editor API Reference: `docs/api/CEL_Editor_API.md`
- Trading Strategy Guide: `docs/guides/Trading_Strategy_Guide.md`
- Backtest Engine Guide: `docs/guides/Backtest_Engine_Guide.md`

**Community**:
- GitHub Issues: [Report bugs or request features]
- Discord: [Join trading strategy discussions]
- Forum: [Share patterns and strategies]

**Updates**:
- Check for updates: **Help → Check for Updates**
- Release notes: `CHANGELOG.md`
- Roadmap: `docs/ROADMAP.md`

---

## Glossary

**Terms used in Pattern Builder:**

- **Candle**: Visual representation of price movement (OHLC)
- **OHLC**: Open, High, Low, Close prices
- **Bullish**: Upward price movement (Close > Open)
- **Bearish**: Downward price movement (Close < Open)
- **Doji**: Indecision candle (Close ≈ Open)
- **Relation**: Comparison between two candles (>, <, =)
- **Pattern**: Collection of candles and relations
- **CEL**: Common Expression Language (for trading logic)
- **Index**: Candle position in pattern (0, 1, 2, ...)
- **Canvas**: Visual area for pattern design
- **Properties Panel**: Editor for candle details

---

**End of User Guide**

For technical details, see **API Documentation** (`docs/api/CEL_Editor_API.md`).

For tutorials, see **CEL Editor Tutorial** (`docs/tutorials/CEL_Editor_Tutorial.md`).
