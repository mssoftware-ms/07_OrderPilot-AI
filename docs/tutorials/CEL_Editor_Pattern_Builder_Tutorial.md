# CEL Editor - Pattern Builder Tutorial

**Welcome to the Pattern Builder!** 🎉

This interactive tutorial will guide you through creating your first candlestick pattern step-by-step. By the end, you'll have created a complete **Bullish Engulfing Pattern** and learned all the essential Pattern Builder features.

**Estimated Time**: 15 minutes
**Skill Level**: Beginner
**Prerequisites**: OrderPilot-AI installed and running

---

## Table of Contents

1. [What You'll Learn](#what-youll-learn)
2. [Tutorial Setup](#tutorial-setup)
3. [Lesson 1: Your First Candle](#lesson-1-your-first-candle)
4. [Lesson 2: Adding More Candles](#lesson-2-adding-more-candles)
5. [Lesson 3: Creating Relations](#lesson-3-creating-relations)
6. [Lesson 4: Editing Candle Properties](#lesson-4-editing-candle-properties)
7. [Lesson 5: Saving Your Pattern](#lesson-5-saving-your-pattern)
8. [Lesson 6: Advanced Features](#lesson-6-advanced-features)
9. [What's Next?](#whats-next)
10. [Troubleshooting](#troubleshooting)

---

## What You'll Learn

By completing this tutorial, you will be able to:

- ✅ **Add candles** to the canvas (bullish, bearish, doji)
- ✅ **Create relation lines** between candles
- ✅ **Edit candle properties** (OHLC values, type)
- ✅ **Use the properties panel** to fine-tune candles
- ✅ **Save and load patterns** for reuse
- ✅ **Use keyboard shortcuts** for efficiency
- ✅ **Understand pattern validation** rules

**Final Pattern**: You'll create a professional **Bullish Engulfing Pattern** used in real trading strategies.

---

## Tutorial Setup

### Step 1: Open Pattern Builder

1. Launch **OrderPilot-AI**
2. Navigate to: **Tools** → **CEL Editor**
3. Click on the **Pattern Builder** tab
4. You should see:
   - **Toolbar** at the top (with Bullish, Bearish, Doji buttons)
   - **Canvas** in the center (large white area)
   - **Properties Panel** on the right (currently disabled)

### Step 2: Familiarize Yourself

Take a moment to explore:
- **Hover over toolbar buttons** - tooltips explain each button
- **Right-click on canvas** - see the context menu
- **Try zooming** - use mouse wheel or Ctrl+Plus/Minus

✅ **Checkpoint**: Can you see all three interface areas? If yes, you're ready!

---

## Lesson 1: Your First Candle

### Goal

Add a **bearish candle** (red) to the canvas. This will represent the first candle in a Bullish Engulfing pattern.

### Instructions

**Step 1: Select Candle Type**

1. Look at the toolbar at the top
2. Find the **Bearish** button (red candle icon)
3. Click on it
4. The button should **highlight** (stay pressed)

💡 **Tip**: The highlighted button shows which candle type will be added next.

**Step 2: Add Candle to Canvas**

Method A (Recommended):
1. Click the **Add (+)** button in the toolbar
2. A red bearish candle appears on the canvas

Method B (Alternative):
1. Right-click anywhere on the canvas
2. Select **Add Candle** from the menu
3. A red bearish candle appears

**Step 3: Observe the Result**

You should see:
- A **red rectangular candle** with a wick
- The candle is **positioned on the left** side of the canvas
- A **small label** showing "Candle 0" or the index

**Step 4: Inspect the Candle**

1. Click on the candle to select it
2. The candle gets a **blue border** (selected state)
3. The **Properties Panel** on the right **enables**
4. You can now see the candle's details:
   - Type: Bearish
   - Open: 50.0
   - High: 90.0
   - Low: 30.0
   - Close: 40.0
   - Index: 0

✅ **Checkpoint**: Do you see a red candle on the canvas and the properties panel showing its values? Great! Move to Lesson 2.

---

## Lesson 2: Adding More Candles

### Goal

Add a **bullish candle** (green) that will "engulf" the bearish candle, creating the classic Bullish Engulfing pattern.

### Instructions

**Step 1: Change Candle Type**

1. Click on the **Bullish** button in the toolbar (green candle icon)
2. The Bullish button should now be highlighted
3. The Bearish button is no longer highlighted

💡 **Tip**: Only one candle type can be selected at a time.

**Step 2: Add Second Candle**

1. Click the **Add (+)** button in the toolbar
2. A **green bullish candle** appears to the **right** of the bearish candle

**Auto-Positioning**: Notice how the second candle automatically positioned itself to the right. Pattern Builder uses auto-positioning to keep candles organized.

**Step 3: View Your Pattern**

You should now see:
- **Candle 0** (Bearish, red) on the left
- **Candle 1** (Bullish, green) on the right

If the candles don't fit in the view:
1. Press **Ctrl+0** (Zoom Fit)
2. OR Click **View** → **Zoom Fit**
3. Both candles should now be visible

**Step 4: Practice Adding & Removing**

Let's practice:

1. **Add a third candle**:
   - Select **Doji** type (gray candle icon)
   - Click **Add (+)**
   - A gray doji candle appears

2. **Remove the doji** (we don't need it):
   - Click on the doji candle to select it
   - Press **Delete** key
   - OR Right-click → **Remove Candle**
   - The doji disappears

3. **Undo the removal**:
   - Press **Ctrl+Z** (Undo)
   - The doji reappears

4. **Remove it again**:
   - Press **Delete** key

✅ **Checkpoint**: Do you have exactly 2 candles (1 bearish, 1 bullish)? Perfect! On to relations.

---

## Lesson 3: Creating Relations

### Goal

Create a **relation line** showing that the bullish candle "engulfs" (is greater than) the bearish candle.

### What are Relations?

Relations define **logical relationships** between candles:
- **Greater (>)**: First candle's range > Second candle's range
- **Less (<)**: First candle's range < Second candle's range
- **Equal (=)**: Candles have equal ranges

For Bullish Engulfing:
- **Bearish candle (0) < Bullish candle (1)**
- The bullish candle's range should exceed the bearish candle's range

### Instructions

**Step 1: Understand the Relation**

We want to express:
```
Candle 0 (Bearish) < Candle 1 (Bullish)
```

Meaning: Candle 1 engulfs (is greater than) Candle 0.

**Step 2: Create the Relation**

Method A (Toolbar):

1. Click on **Candle 0** (bearish) to select it
2. Find the **Relation** button in toolbar (line with arrow icon)
3. Click the **Relation** button
4. Click on **Candle 1** (bullish)
5. A dialog appears: **"Choose Relation Type"**
6. Select **Less (<)** (Candle 0 is less than Candle 1)
7. Click **OK**

Method B (Right-Click Menu):

1. Click on **Candle 0** (bearish) to select it
2. Right-click anywhere on canvas
3. Select **Add Relation**
4. Click on **Candle 1** (bullish)
5. Dialog appears
6. Select **Less (<)**
7. Click **OK**

**Step 3: Observe the Result**

You should see:
- A **line connecting** the two candles
- An **arrow** pointing from Candle 0 to Candle 1
- A **label** showing "<" (less than)

**Visual Interpretation**:
```
Bearish ----<---- Bullish
(Candle 0 is less than Candle 1)
```

✅ **Checkpoint**: Do you see a line with "<" label connecting your candles? Excellent!

---

## Lesson 4: Editing Candle Properties

### Goal

Fine-tune the candles to create a **realistic Bullish Engulfing pattern** with proper OHLC values.

### What is OHLC?

**OHLC** = Open, High, Low, Close
- **Open**: Price at candle start
- **High**: Highest price during candle
- **Low**: Lowest price during candle
- **Close**: Price at candle end

### Instructions

**Step 1: Select Candle 0 (Bearish)**

1. Click on the **bearish candle** (left)
2. It gets a blue border (selected)
3. The **Properties Panel** shows its values

**Step 2: Understand Current Values**

Current default values:
```
Open:  50.0
High:  90.0
Low:   30.0
Close: 40.0
```

For a small bearish candle (being engulfed):
```
Open:  55.0  (slightly higher)
High:  60.0  (not too high)
Low:   45.0  (not too low)
Close: 48.0  (slightly below open)
```

**Step 3: Edit Candle 0 Properties**

In the Properties Panel:

1. **Open**: Change to `55.0`
   - Click in the "Open" box
   - Type `55.0`
   - Press Tab to move to next field

2. **High**: Change to `60.0`
   - Type `60.0`
   - Press Tab

3. **Low**: Change to `45.0`
   - Type `45.0`
   - Press Tab

4. **Close**: Change to `48.0`
   - Type `48.0`

5. Click **Apply Changes** button

**Result**: The bearish candle updates to show the new values (smaller body, shorter wicks).

**Step 4: Edit Candle 1 (Bullish)**

1. Click on the **bullish candle** (right)
2. Properties Panel shows its values

For a large bullish candle (engulfing the bearish):
```
Open:  40.0  (below bearish LOW!)
High:  95.0  (above bearish HIGH!)
Low:   35.0  (well below bearish)
Close: 90.0  (near the high, strong close)
```

Edit the values:

1. **Open**: `40.0`
2. **High**: `95.0`
3. **Low**: `35.0`
4. **Close**: `90.0`
5. Click **Apply Changes**

**Result**: The bullish candle becomes **much larger**, clearly engulfing the bearish candle.

**Step 5: Observe the Pattern**

Zoom out if needed (Ctrl+0 for Zoom Fit):

You should see:
- **Small red candle** (bearish) on the left
- **Large green candle** (bullish) on the right
- The green candle's **high/low exceeds** the red candle's range
- A **relation line** showing the relationship

**This is the Bullish Engulfing Pattern!** 📈

✅ **Checkpoint**: Does your pattern look like a small bearish candle followed by a large bullish candle that engulfs it? Perfect!

---

## Lesson 5: Saving Your Pattern

### Goal

Save the pattern to a file so you can use it in trading strategies and reload it later.

### Instructions

**Step 1: Save Pattern**

Method A (Menu):
1. Click **File** → **Save Pattern**

Method B (Keyboard):
1. Press **Ctrl+S**

**Step 2: Choose Location & Name**

1. A file dialog appears
2. Navigate to: `patterns/` folder (default location)
3. Enter filename: `bullish_engulfing.json`
4. Click **Save**

**Step 3: Verify Save**

1. Check the patterns/ folder
2. You should see: `bullish_engulfing.json`
3. File size: ~1-2 KB

**Step 4: Test Load (Optional)**

Let's verify the pattern saved correctly:

1. Click **Edit** → **Clear Pattern** (or Ctrl+Shift+N)
2. Confirm "Clear entire pattern?" → **Yes**
3. Canvas is now empty
4. Click **File** → **Load Pattern** (or Ctrl+O)
5. Select `bullish_engulfing.json`
6. Click **Open**
7. Your pattern reappears!

✅ **Checkpoint**: Were you able to save and reload your pattern? Great job!

---

## Lesson 6: Advanced Features

Now that you've mastered the basics, let's explore some advanced features.

### 6.1 Pattern Statistics

**View pattern statistics:**

1. Click **View** → **Pattern Statistics**
2. A window shows:
   ```
   Total Candles: 2
   Total Relations: 1
   Candle Types:
     - Bearish: 1
     - Bullish: 1
   ```

### 6.2 Zoom Operations

**Practice zooming:**

1. **Zoom In**: Press **Ctrl+Plus** (or mouse wheel up)
2. **Zoom Out**: Press **Ctrl+Minus** (or mouse wheel down)
3. **Zoom Fit**: Press **Ctrl+0** (shows all candles)
4. **Zoom 100%**: Press **Ctrl+1** (actual size)

### 6.3 Multiple Selection

**Select multiple candles:**

1. Hold **Ctrl** key
2. Click on Candle 0
3. Keep holding Ctrl, click on Candle 1
4. Both candles are selected (blue borders)
5. Properties Panel shows: "2 candles selected"

**Clear selection:**
1. Click on empty canvas area
2. OR Press **Esc** key

### 6.4 Keyboard Shortcuts

**Try these shortcuts:**

| Shortcut | Action |
|----------|--------|
| **Ctrl+B** | Add Bullish candle |
| **Ctrl+R** | Add Bearish candle |
| **Ctrl+D** | Add Doji candle |
| **Ctrl+Z** | Undo |
| **Ctrl+Y** | Redo |
| **Delete** | Remove selected |

### 6.5 Undo/Redo History

**Experiment with undo/redo:**

1. Make several changes (add candles, move them, etc.)
2. Press **Ctrl+Z** multiple times to undo
3. Press **Ctrl+Y** multiple times to redo
4. Notice how Pattern Builder remembers all operations

### 6.6 Pattern Validation

**Validate your pattern:**

1. Click **Tools** → **Validate Pattern**
2. Validation checks:
   - OHLC values are valid
   - Relations are consistent
   - No orphaned candles
3. You should see: **✅ Pattern is valid**

### 6.7 Export to CEL

**Export pattern as trading logic:**

1. Click **File** → **Export to CEL**
2. Enter function name: `isBullishEngulfing`
3. Click **Export**
4. CEL code is generated:

```cel
// Bullish Engulfing Pattern
function isBullishEngulfing(c0, c1) {
  return c1.close > c0.close &&
         c1.high > c0.high &&
         c1.low < c0.low &&
         c1.type == "bullish" &&
         c0.type == "bearish";
}
```

5. Copy this code to use in trading strategies!

✅ **Checkpoint**: You've now mastered all Pattern Builder features!

---

## What's Next?

### 🎓 You've Completed the Tutorial!

Congratulations! You now know how to:
- ✅ Create candlestick patterns visually
- ✅ Add and edit candles
- ✅ Create relation lines
- ✅ Use the properties panel
- ✅ Save and load patterns
- ✅ Use keyboard shortcuts
- ✅ Export patterns to CEL

### 📚 Continue Learning

**Next Steps:**

1. **Create More Patterns**:
   - Try creating: **Doji Star**, **Hammer**, **Shooting Star**
   - Experiment with 3-5 candle patterns
   - Build a pattern library

2. **Read the User Guide**:
   - Location: `docs/user_guides/CEL_Editor_Pattern_Builder_Guide.md`
   - Covers all features in detail
   - Troubleshooting section

3. **Study the API**:
   - Location: `docs/api/CEL_Editor_Pattern_Builder_API.md`
   - Learn programmatic pattern creation
   - Advanced usage examples

4. **Backtest Your Patterns**:
   - Load patterns into Backtest Engine
   - Test on historical data
   - Optimize for profitability

5. **Join the Community**:
   - Share patterns with other traders
   - Get feedback on pattern designs
   - Learn new strategies

### 🚀 Advanced Projects

**Challenge Yourself:**

1. **Create a 3-Candle Pattern**:
   - Example: **Morning Star** (Bearish → Doji → Bullish)
   - Use 2 relation lines
   - Export to CEL

2. **Build a Pattern Library**:
   - Create 10+ common patterns
   - Organize by category (reversals, continuations)
   - Document each pattern's use case

3. **Automate with Python**:
   - Use the Pattern Builder API
   - Create patterns programmatically
   - Batch test multiple patterns

---

## Troubleshooting

### Issue: "Can't add candle"

**Solution**:
1. Check that a candle type is selected (Bullish/Bearish/Doji button highlighted)
2. Try clicking the canvas directly instead of the Add button
3. Restart Pattern Builder if stuck

### Issue: "Properties panel is disabled"

**Solution**:
1. Make sure exactly 1 candle is selected
2. Click on a candle to select it
3. If multiple candles are selected, clear selection (Esc) and try again

### Issue: "OHLC validation error"

**Solution**:
1. Check that **High ≥ max(Open, Close)**
2. Check that **Low ≤ min(Open, Close)**
3. Example valid values:
   ```
   High: 90 ✅ (highest)
   Open: 50 ✅
   Close: 85 ✅
   Low: 30 ✅ (lowest)
   ```

### Issue: "Relation line won't create"

**Solution**:
1. Make sure you selected **source candle** first
2. Then click **Relation** button or right-click → Add Relation
3. Then select **target candle**
4. Choose relation type in dialog

### Issue: "Pattern won't save"

**Solution**:
1. Check filename (no special characters: / \ : * ? " < > |)
2. Ensure you have write permissions to the folder
3. Try saving to a different location

---

## Quiz: Test Your Knowledge

### Question 1: What do the OHLC letters stand for?

<details>
<summary>Click to reveal answer</summary>

**Answer**: Open, High, Low, Close

- **Open**: Price at candle start
- **High**: Highest price during candle
- **Low**: Lowest price during candle
- **Close**: Price at candle end
</details>

### Question 2: What relation type shows "engulfing"?

<details>
<summary>Click to reveal answer</summary>

**Answer**: **Less (<)**

For Bullish Engulfing:
```
Small Bearish Candle < Large Bullish Candle
```

The bullish candle **engulfs** (is greater than) the bearish candle.
</details>

### Question 3: What keyboard shortcut adds a Bullish candle?

<details>
<summary>Click to reveal answer</summary>

**Answer**: **Ctrl+B**

Shortcuts:
- Ctrl+B = Bullish
- Ctrl+R = Bearish (Red)
- Ctrl+D = Doji
</details>

### Question 4: How do you validate your pattern?

<details>
<summary>Click to reveal answer</summary>

**Answer**: **Tools → Validate Pattern**

This checks:
- OHLC values are valid
- Relations are consistent
- No orphaned candles
</details>

### Question 5: What's the maximum recommended number of candles per pattern?

<details>
<summary>Click to reveal answer</summary>

**Answer**: **5-7 candles**

Reasoning:
- Simpler patterns (2-3 candles) are easier to match
- Complex patterns (10+ candles) rarely occur
- 5-7 candles balances specificity with practicality
- Pattern Builder can handle 100+ candles but typical patterns use fewer
</details>

---

## Feedback

**How was this tutorial?**

We'd love to hear your feedback:
- 📧 Email: support@orderpilot.ai
- 💬 Discord: [Join our community]
- 🐛 Bug reports: [GitHub Issues]

**Help us improve:**
- What was unclear?
- What topics should we add?
- What examples would help?

---

## Resources

**Documentation**:
- 📖 User Guide: `docs/user_guides/CEL_Editor_Pattern_Builder_Guide.md`
- 🔧 API Reference: `docs/api/CEL_Editor_Pattern_Builder_API.md`
- 🧪 Test Results: `docs/testing/CEL_Editor_Phase_2_7_*.md`

**Example Patterns**:
- 📁 Pattern Library: `patterns/` folder
- 🌐 Online Gallery: [Pattern Gallery]
- 👥 Community Patterns: [Discord #patterns channel]

**Video Tutorials** (Coming Soon):
- 🎥 Pattern Builder Basics (10 min)
- 🎥 Advanced Techniques (15 min)
- 🎥 Backtesting Patterns (20 min)

---

**Thank you for completing the CEL Editor Pattern Builder Tutorial!** 🎉

You're now ready to create professional trading patterns. Happy trading! 📈

---

**End of Tutorial**

*Last Updated: 2026-01-20*
*Version: 1.0*
*For OrderPilot-AI v2.0+*
