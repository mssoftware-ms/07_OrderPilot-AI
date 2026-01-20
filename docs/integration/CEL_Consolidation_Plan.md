# CEL System Redesign & UI Consolidation Plan

## Executive Summary

**Problem**: Three redundant UI windows (Strategy Settings Dialog, Strategy Concept Window, Entry Analyzer) performing overlapping functions, with CEL system misimplemented as a rule evaluation engine instead of the required script programming interface.

**Solution**: Consolidate all three windows into ONE unified **CEL Script Editor** that provides a Pine Script-like programming interface for creating fully customizable trading strategies.

**Timeline**: 4-5 weeks (detailed breakdown in Implementation Phases)

---

## 1. Current State Analysis

### 1.1 Three Redundant Windows

#### Window 1: StrategySettingsDialog (`src/ui/dialogs/strategy_settings_dialog.py`, 694 lines)

**Features**:
- JSON strategy file management (load/delete/create/edit)
- Live regime display with auto-refresh (5 seconds)
- Strategy table with 6 columns (Name, Type, Indicators, Entry/Exit Conditions, Active)
- Market analysis with regime detection and strategy routing
- Loads strategies from `03_JSON/Trading_Bot/` directory

**Overlapping Functions**:
- ✗ JSON config loading (also in Entry Analyzer)
- ✗ Strategy management (also in Strategy Concept)
- ✗ Regime display (also in Entry Analyzer backtest)

**What to Keep**:
- ✓ Live regime detection integration
- ✓ Strategy activation/deactivation concept
- ✓ Auto-refresh mechanism

#### Window 2: Strategy Concept Window (`src/ui/dialogs/strategy_concept_window.py`, 287 lines)

**Features**:
- Simple wrapper with 2 tabs:
  - Tab 1: Pattern Recognition Widget (detect patterns in chart)
  - Tab 2: Pattern Integration Widget (map patterns to strategies)
- "Apply to Bot" button
- Cross-tab communication (detected patterns → strategy suggestions)

**Overlapping Functions**:
- ✗ Pattern-based strategy creation (should be in unified editor)
- ✗ "Apply to Bot" (also in Strategy Settings)

**What to Keep**:
- ✓ Pattern recognition engine integration
- ✓ Pattern-to-strategy mapping concept
- ✓ Cross-widget communication pattern

#### Window 3: Entry Analyzer Popup (`src/ui/dialogs/entry_analyzer_popup.py`, 1900+ lines)

**Features**:
- **5 main tabs**:
  1. **Backtest Setup**: JSON loader, date range, capital, symbol, "Run Backtest" button
  2. **Visible Range Analysis**: Current entry analysis
  3. **Backtest Results**: Performance summary, trade list, regime boundaries visualization
  4. **AI Copilot**: AI entry recommendations (LLM-based analysis)
  5. **Validation**: Walk-forward validation for robustness testing
- **Indicator Optimization**: Parameter ranges, multi-indicator testing
- **Regime-based backtesting** with visual regime boundaries on chart
- **Three worker threads**: CopilotWorker, ValidationWorker, BacktestWorker
- Complex UI with tables, charts, progress bars

**Overlapping Functions**:
- ✗ JSON strategy loading (also in Strategy Settings)
- ✗ Regime analysis (also in Strategy Settings)
- ✗ Strategy testing/validation (should be in unified editor)

**What to Keep**:
- ✓ Backtest engine integration (BacktestWorker)
- ✓ AI Copilot for strategy recommendations
- ✓ Walk-forward validation
- ✓ Indicator optimization framework
- ✓ Regime boundary visualization on chart
- ✓ Multi-timeframe backtesting

### 1.2 Overlap Matrix

| Feature | Strategy Settings | Strategy Concept | Entry Analyzer |
|---------|-------------------|------------------|----------------|
| JSON Strategy Management | ✓ | ✗ | ✓ |
| Live Regime Display | ✓ | ✗ | ✓ (in backtest) |
| Pattern Recognition | ✗ | ✓ | ✗ |
| Backtesting | ✗ | ✗ | ✓ |
| AI Analysis | ✗ | ✗ | ✓ |
| Validation | ✗ | ✗ | ✓ |
| Apply to Bot | ✓ (indirect) | ✓ | ✗ |

**Total Overlap**: ~40% of functionality is duplicated across windows

---

## 2. CEL System Fundamental Redesign

### 2.1 Current Implementation (WRONG)

**What Was Built** (Phase 1-4, 94 tests):
```python
# Rule-based evaluation engine
class RulePack:
    rules_version: str
    engine: str = "CEL"
    packs: list[Pack]  # risk, entry, exit, update_stop

class Pack:
    pack_type: str  # "risk" | "entry" | "exit" | "update_stop"
    rules: list[Rule]

class Rule:
    id: str
    name: str
    expression: str  # CEL expression (Google CEL)
    severity: str  # "block" | "warn" | "exit" | "update_stop"
    message: str
```

**Problems**:
- ✗ Hard-coded rule types (risk, entry, exit, update_stop)
- ✗ Limited expression language (Google CEL subset)
- ✗ No script editor for users
- ✗ Cannot implement complex patterns from Chartmuster_Erweitert_2026.md
- ✗ Not extensible for custom indicator logic

### 2.2 Required Implementation (CORRECT)

**What User Actually Needs** (Pine Script-like):
```python
# Script-based programming interface
class TradingScript:
    script_id: str
    name: str
    description: str
    script_code: str  # Full Python-like trading logic
    indicator_config: dict  # Indicator parameters
    entry_logic: str  # Entry condition script
    exit_logic: str  # Exit condition script
    risk_logic: str  # Risk management script
    metadata: dict  # Author, version, tags, etc.

# Example script structure
"""
@indicator RSI(14)
@indicator MACD(12, 26, 9)
@indicator EMA(34)
@indicator Stochastic(5, 3, 3)

@pattern PinBar:
    wick_ratio >= 2.0
    body_size < 0.3 * range

@entry LONG:
    stochastic.k < 20
    stochastic.crossed_above(stochastic.d)
    close > ema_34
    pattern.is_bullish_pinbar()
    volume > avg_volume(20) * 1.2

@exit:
    stochastic.k > 80
    OR close < ema_34
    OR trailing_stop_hit()

@risk:
    stop_loss = entry - (2 * atr_14)
    take_profit = entry + (3 * atr_14)
    position_size = 2% of capital
"""
```

**Key Features**:
- ✓ Full scripting language (Python-based DSL)
- ✓ User-editable code in script editor
- ✓ Query API for indicators, patterns, market structure
- ✓ Multi-timeframe support
- ✓ Extensible for any custom logic
- ✓ Scripts stored in JSON files
- ✓ Bot reads and executes scripts dynamically

---

## 3. CEL Script Language Design

### 3.1 Language Syntax

**Inspired by Pine Script, but Python-based for familiarity**:

```python
# Script Header (metadata)
@strategy(
    name="Scalping Stochastic Pin Bar",
    version="1.0",
    timeframe="1min",
    regime="TREND_UP",
    description="86% win rate scalping with Stochastic + EMA + Pin Bar"
)

# Indicator Declarations
@indicator RSI(period=14, source='close')
@indicator MACD(fast=12, slow=26, signal=9)
@indicator EMA(period=34, source='close')
@indicator Stochastic(k_period=5, d_period=3, smooth=3)
@indicator ATR(period=14)
@indicator Volume(sma_period=20)

# Custom Pattern Definitions
@pattern BullishPinBar:
    lower_wick = low - min(open, close)
    upper_wick = max(open, close) - high
    body = abs(close - open)
    candle_range = high - low

    # Pin bar criteria
    lower_wick >= 2.0 * body
    upper_wick <= 0.3 * body
    body < 0.5 * candle_range
    close > open  # Bullish

@pattern BearishPinBar:
    lower_wick = low - min(open, close)
    upper_wick = max(open, close) - high
    body = abs(close - open)
    candle_range = high - low

    # Inverted pin bar
    upper_wick >= 2.0 * body
    lower_wick <= 0.3 * body
    body < 0.5 * candle_range
    close < open  # Bearish

# Market Structure Detection
@structure OrderBlock:
    # Last candle before strong move
    displacement = abs(close[0] - close[1]) / close[1]
    displacement > 0.01  # 1% move
    volume > volume.sma(20) * 1.5

    # Mark the candle before displacement
    ob_high = high[-1]
    ob_low = low[-1]
    ob_level = (ob_high + ob_low) / 2

@structure FairValueGap:
    # Gap between candles
    gap_up = low[0] > high[-2]
    gap_down = high[0] < low[-2]

    if gap_up:
        fvg_top = low[0]
        fvg_bottom = high[-2]
        fvg_direction = "bullish"

    if gap_down:
        fvg_top = low[-2]
        fvg_bottom = high[0]
        fvg_direction = "bearish"

@structure LiquiditySweep:
    # Price spikes beyond swing high/low
    swing_high = highest(high, 20)
    sweep_high = high > swing_high[-1]
    rejection_candle = close < open AND (high - close) > 2 * (close - open)

    sweep_confirmed = sweep_high AND rejection_candle

# Entry Logic (LONG)
@entry LONG:
    # Stochastic oversold and crossing up
    stochastic.k < 20
    stochastic.crossed_above(stochastic.d)

    # Price above EMA (uptrend filter)
    close > ema_34

    # Bullish pin bar confirmation
    pattern.BullishPinBar

    # Volume confirmation
    volume > volume.sma(20) * 1.2

    # Optional: Multi-timeframe confirmation
    timeframe.higher("5min").ema_34 is rising

    # Entry price
    entry_price = close

    # Smart Money Concepts (optional)
    # near_order_block = close within 0.5% of OrderBlock.ob_level
    # fvg_unfilled = FairValueGap.fvg_direction == "bullish" AND not filled

# Entry Logic (SHORT)
@entry SHORT:
    # Stochastic overbought and crossing down
    stochastic.k > 80
    stochastic.crossed_below(stochastic.d)

    # Price below EMA (downtrend filter)
    close < ema_34

    # Bearish pin bar confirmation
    pattern.BearishPinBar

    # Volume confirmation
    volume > volume.sma(20) * 1.2

    entry_price = close

# Exit Logic
@exit:
    # Opposite Stochastic signal
    if position.side == LONG:
        stochastic.k > 80

    if position.side == SHORT:
        stochastic.k < 20

    # Price crosses EMA (trend reversal)
    if position.side == LONG:
        close < ema_34

    if position.side == SHORT:
        close > ema_34

    # Trailing stop hit
    trailing_stop_hit()

    # Time-based exit (optional)
    bars_in_trade > 20  # Exit after 20 candles (20 minutes for 1min chart)

# Risk Management
@risk:
    # Stop loss: 2x ATR
    if position.side == LONG:
        stop_loss = entry_price - (2 * atr_14)

    if position.side == SHORT:
        stop_loss = entry_price + (2 * atr_14)

    # Take profit: 3x ATR (1.5 R/R)
    if position.side == LONG:
        take_profit = entry_price + (3 * atr_14)

    if position.side == SHORT:
        take_profit = entry_price - (3 * atr_14)

    # Position size: 2% of capital
    risk_amount = capital * 0.02
    stop_distance = abs(entry_price - stop_loss)
    position_size = risk_amount / stop_distance

    # Trailing stop: move to breakeven after 1.5x ATR profit
    if position.profit >= 1.5 * atr_14:
        trailing_stop = entry_price  # Breakeven

# Regime Filter (optional)
@regime_filter:
    # Only trade in trending markets
    allowed_regimes = ["TREND_UP", "TREND_DOWN"]
    current_regime in allowed_regimes

    # ADX confirmation
    adx > 25  # Strong trend
```

### 3.2 Query API Design

**Core API Functions** (available in scripts):

```python
# Indicator Access
rsi(period: int = 14, source: str = 'close') -> float
macd(fast: int = 12, slow: int = 26, signal: int = 9) -> tuple[float, float, float]
ema(period: int, source: str = 'close') -> float
sma(period: int, source: str = 'close') -> float
stochastic(k: int = 14, d: int = 3, smooth: int = 3) -> tuple[float, float]
atr(period: int = 14) -> float
adx(period: int = 14) -> float
bollinger_bands(period: int = 20, std_dev: float = 2.0) -> tuple[float, float, float]

# Price Access
close[offset: int = 0] -> float  # close, close[-1], close[-2], etc.
open[offset: int = 0] -> float
high[offset: int = 0] -> float
low[offset: int = 0] -> float
volume[offset: int = 0] -> float

# Historical Functions
highest(series: str, length: int) -> float
lowest(series: str, length: int) -> float
avg(series: str, length: int) -> float
sum(series: str, length: int) -> float

# Cross Functions
crossed_above(a: float, b: float) -> bool
crossed_below(a: float, b: float) -> bool

# Pattern Detection API
pattern.is_bullish_pinbar(wick_ratio: float = 2.0) -> bool
pattern.is_bearish_pinbar(wick_ratio: float = 2.0) -> bool
pattern.is_inside_bar() -> bool
pattern.is_bullish_engulfing() -> bool
pattern.is_bearish_engulfing() -> bool
pattern.is_hammer() -> bool
pattern.is_shooting_star() -> bool
pattern.is_doji() -> bool

# Market Structure API
structure.order_block(displacement_threshold: float = 0.01) -> dict
structure.fair_value_gap() -> dict
structure.liquidity_sweep(lookback: int = 20) -> bool
structure.break_of_structure() -> bool
structure.change_of_character() -> bool

# Multi-Timeframe API
timeframe.higher(tf: str).close -> float
timeframe.higher(tf: str).ema(period: int) -> float
timeframe.higher(tf: str).regime -> str

# Position API
position.side -> str  # "LONG" | "SHORT" | "NONE"
position.entry_price -> float
position.stop_loss -> float
position.take_profit -> float
position.profit -> float
position.profit_pct -> float
position.bars_held -> int

# Regime API
regime.current -> str  # "TREND_UP" | "TREND_DOWN" | "RANGE"
regime.volatility -> str  # "LOW" | "NORMAL" | "HIGH" | "EXTREME"
regime.confidence -> float  # 0.0 - 1.0
regime.adx -> float
regime.atr_pct -> float

# Time API
time.hour -> int
time.minute -> int
time.day_of_week -> int  # 0=Monday, 6=Sunday
time.is_market_open() -> bool
```

### 3.3 Script Storage Format (JSON)

**JSON Structure** for storing scripts:

```json
{
  "script_id": "scalping_stoch_pinbar_v1",
  "metadata": {
    "name": "Scalping Stochastic Pin Bar",
    "version": "1.0.0",
    "author": "User",
    "created_at": "2026-01-20T10:00:00Z",
    "updated_at": "2026-01-20T10:00:00Z",
    "tags": ["scalping", "pinbar", "stochastic", "ema"],
    "timeframe": "1min",
    "regime": "TREND_UP",
    "description": "86% win rate scalping strategy combining Stochastic oversold/overbought signals with EMA trend filter and Pin Bar confirmation."
  },
  "indicators": [
    {"type": "RSI", "params": {"period": 14}},
    {"type": "MACD", "params": {"fast": 12, "slow": 26, "signal": 9}},
    {"type": "EMA", "params": {"period": 34}},
    {"type": "Stochastic", "params": {"k_period": 5, "d_period": 3, "smooth": 3}},
    {"type": "ATR", "params": {"period": 14}},
    {"type": "Volume", "params": {"sma_period": 20}}
  ],
  "patterns": [
    {
      "name": "BullishPinBar",
      "code": "lower_wick >= 2.0 * body AND upper_wick <= 0.3 * body AND body < 0.5 * candle_range AND close > open"
    },
    {
      "name": "BearishPinBar",
      "code": "upper_wick >= 2.0 * body AND lower_wick <= 0.3 * body AND body < 0.5 * candle_range AND close < open"
    }
  ],
  "entry": {
    "long": "stochastic.k < 20 AND stochastic.crossed_above(stochastic.d) AND close > ema_34 AND pattern.BullishPinBar AND volume > volume.sma(20) * 1.2",
    "short": "stochastic.k > 80 AND stochastic.crossed_below(stochastic.d) AND close < ema_34 AND pattern.BearishPinBar AND volume > volume.sma(20) * 1.2"
  },
  "exit": {
    "code": "(position.side == LONG AND stochastic.k > 80) OR (position.side == SHORT AND stochastic.k < 20) OR (position.side == LONG AND close < ema_34) OR (position.side == SHORT AND close > ema_34) OR trailing_stop_hit() OR bars_in_trade > 20"
  },
  "risk": {
    "stop_loss_atr_multiplier": 2.0,
    "take_profit_atr_multiplier": 3.0,
    "position_size_pct": 2.0,
    "trailing_stop_profit_threshold": 1.5
  },
  "regime_filter": {
    "allowed_regimes": ["TREND_UP", "TREND_DOWN"],
    "min_adx": 25
  },
  "performance": {
    "win_rate": 0.86,
    "avg_return": 1.5,
    "profit_factor": 2.3,
    "sharpe_ratio": 1.8,
    "max_drawdown": 0.08,
    "total_trades": 127,
    "last_backtest_date": "2026-01-20T10:00:00Z"
  }
}
```

---

## 4. Unified CEL Script Editor Architecture

### 4.1 Single Consolidated Window

**Name**: CEL Script Editor (replaces all three windows)

**Main Components**:

```
┌─────────────────────────────────────────────────────────────┐
│ 📝 CEL Script Editor - [Strategy Name]                     │
├─────────────────────────────────────────────────────────────┤
│ [File] [Edit] [Strategy] [Backtest] [Tools] [Help]         │
├──────────────────┬──────────────────────────────────────────┤
│                  │                                          │
│  Pattern Library │  ╔═══════════════════════════════════╗ │
│  ────────────────│  ║ Script Editor (Monaco/CodeMirror)║ │
│  📊 Scalping     │  ║                                   ║ │
│    └ Stoch+EMA   │  ║ @strategy(                        ║ │
│    └ Pin Bar     │  ║   name="My Strategy"              ║ │
│  📈 Day Trading  │  ║ )                                 ║ │
│    └ Cup&Handle  │  ║                                   ║ │
│    └ Bull Flag   │  ║ @indicator RSI(14)                ║ │
│  📉 Smart Money  │  ║ @indicator EMA(34)                ║ │
│    └ Order Blocks│  ║                                   ║ │
│    └ FVG         │  ║ @entry LONG:                      ║ │
│    └ Liq. Sweep  │  ║   rsi < 30                        ║ │
│  🎯 Custom       │  ║   close > ema_34                  ║ │
│    └ My Scripts  │  ║   pattern.BullishPinBar           ║ │
│                  │  ║                                   ║ │
│  [+ New Script]  │  ╚═══════════════════════════════════╝ │
│  [Import]        │                                          │
│                  │  ╔══════════════════════════════════╗  │
│                  │  ║ Console / Errors / Validation    ║  │
│                  │  ╚══════════════════════════════════╝  │
├──────────────────┴──────────────────────────────────────────┤
│ Tabs: [Properties] [Backtest] [Results] [AI Copilot]       │
├─────────────────────────────────────────────────────────────┤
│ Active Tab Content Area                                    │
│ ┌──────────────────────────────────────────────────────┐  │
│ │ [Tab 1: Properties]                                  │  │
│ │ Script Name: _______________                         │  │
│ │ Timeframe: [1min ▼]  Regime: [TREND_UP ▼]          │  │
│ │ Description: _______________________________________ │  │
│ │ Tags: [scalping] [pinbar] [+]                       │  │
│ │                                                      │  │
│ │ [Tab 2: Backtest Setup]                             │  │
│ │ Symbol: [AAPL ▼]  Start: [2024-01-01] End: [Now]   │  │
│ │ Capital: [$10,000]  Fees: [0.1%]                    │  │
│ │ [▶ Run Backtest] [⏸ Pause] [⏹ Stop]                │  │
│ │                                                      │  │
│ │ [Tab 3: Results]                                     │  │
│ │ Net Profit: $2,340 (23.4%)  Win Rate: 86%          │  │
│ │ Trades: 127  Profit Factor: 2.3  Sharpe: 1.8       │  │
│ │ [Trade List] [Equity Curve] [Regime Boundaries]     │  │
│ │                                                      │  │
│ │ [Tab 4: AI Copilot]                                  │  │
│ │ [🤖 Analyze Strategy] [💡 Suggest Improvements]     │  │
│ │ AI Recommendations: ...                              │  │
│ └──────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│ [💾 Save] [▶ Run Live] [📊 Deploy to Bot] [❌ Close]      │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 Component Breakdown

#### Left Panel: Pattern Library Browser
- **Chartmuster_Erweitert_2026.md patterns** organized by category
- Drag-and-drop pattern templates into editor
- Search/filter patterns
- "New Script" button
- Import existing scripts

#### Center Panel: Script Editor
- **Monaco Editor** (VS Code's editor) or **CodeMirror**
- Syntax highlighting for CEL Script Language
- Auto-completion for API functions (RSI, MACD, pattern.*, etc.)
- Inline error checking
- Code folding
- Line numbers

#### Bottom Panel: Console/Errors
- Real-time syntax validation
- Error messages with line numbers
- Warnings (e.g., "Missing stop loss logic")
- Execution logs during backtesting

#### Right Panel: Tabbed Information
**Tab 1: Properties**
- Script metadata (name, version, author, tags)
- Timeframe selection
- Regime filter settings
- Description

**Tab 2: Backtest Setup**
- Symbol selection
- Date range
- Initial capital
- Fee structure
- "Run Backtest" button
- Progress bar

**Tab 3: Results**
- Performance metrics (Net Profit, Win Rate, Profit Factor, Sharpe, Max DD)
- Trade list table
- Equity curve chart
- Regime boundaries visualization (integrated from Entry Analyzer)
- Indicator optimization results (from Entry Analyzer)

**Tab 4: AI Copilot**
- AI strategy analysis (from Entry Analyzer's CopilotWorker)
- Improvement suggestions
- Pattern match recommendations
- Risk assessment

**Tab 5: Validation** (optional)
- Walk-forward validation (from Entry Analyzer's ValidationWorker)
- Out-of-sample testing
- Robustness metrics

#### Footer Actions
- **Save**: Save script to JSON file
- **Run Live**: Test script on live market data (paper trading)
- **Deploy to Bot**: Activate script in trading bot
- **Close**: Close editor

---

## 5. Pattern Implementation Strategy

### 5.1 All Patterns from Chartmuster_Erweitert_2026.md

**Total**: 800+ lines, 50+ patterns across 8 categories

#### Category 1: Scalping Strategies

**1. Stochastic(5,3,3) + EMA(34) + Pin Bar** (86% win rate, 1min)
```python
@strategy(name="Scalping Stoch Pin Bar", timeframe="1min", regime="TREND_UP")

@indicator Stochastic(5, 3, 3)
@indicator EMA(34)
@indicator RSI(5)
@indicator ATR(14)
@indicator Volume(20)

@pattern BullishPinBar:
    lower_wick >= 2.0 * body
    upper_wick <= 0.3 * body
    close > open

@entry LONG:
    stochastic.k < 20
    stochastic.crossed_above(stochastic.d)
    close > ema_34
    pattern.BullishPinBar
    volume > volume.sma(20) * 1.2

@exit:
    stochastic.k > 80 OR close < ema_34 OR bars_in_trade > 20

@risk:
    stop_loss = entry - (2 * atr)
    take_profit = entry + (3 * atr)
    position_size = 2% of capital
```

**2. RSI(5-7) Multi-Timeframe** (5min exit on 1min entries)
```python
@strategy(name="RSI Multi-TF Scalping", timeframe="1min")

@indicator RSI(7)
@indicator ATR(14)

@entry LONG:
    rsi < 25
    timeframe.higher("5min").rsi > 40  # 5min not oversold yet

@exit:
    timeframe.higher("5min").rsi > 60  # 5min overbought

@risk:
    stop_loss = entry - (1.5 * atr)
    take_profit = entry + (2.5 * atr)
```

#### Category 2: Day Trading Patterns

**3. Cup & Handle** (95% win rate, daily)
```python
@strategy(name="Cup and Handle", timeframe="1day")

@pattern CupAndHandle:
    # Cup: U-shaped base (20-65 days)
    cup_depth = 0.12 to 0.33  # 12-33% correction
    cup_duration = 20 to 65 bars
    rounded_bottom = true  # No V-shape

    # Handle: 1-4 weeks, slight downtrend
    handle_duration = 5 to 20 bars
    handle_depth < 0.5 * cup_depth
    handle_retracement = 0.3 to 0.5 of cup rally

    # Breakout
    volume_on_breakout > avg_volume(50) * 1.5
    close > cup_resistance

@entry LONG:
    pattern.CupAndHandle
    breakout_confirmed = close > cup_resistance
    volume > volume.sma(50) * 1.5

@exit:
    take_profit = entry + (cup_depth * 1.5)  # Target = cup depth × 1.5
    stop_loss = handle_low

@risk:
    position_size = 3% of capital  # Higher conviction
```

**4. Bull Flag** (88% win rate, intraday)
```python
@strategy(name="Bull Flag Breakout", timeframe="5min")

@pattern BullFlag:
    # Flagpole: strong upward move
    flagpole_gain > 0.05  # 5% gain
    flagpole_duration = 3 to 10 bars

    # Flag: consolidation (parallel channels)
    flag_slope = -0.3 to 0.3  # Slight downward or flat
    flag_duration = 5 to 20 bars
    flag_retracement < 0.38 of flagpole  # Max 38.2% Fibonacci

    # Breakout
    close > flag_upper_channel
    volume > avg_volume(20) * 1.3

@entry LONG:
    pattern.BullFlag
    breakout_volume_confirmed = volume > volume.sma(20) * 1.3

@exit:
    target = entry + flagpole_height  # Flag pattern projection
    stop_loss = flag_lower_channel

@risk:
    position_size = 2.5% of capital
```

**5. Double Bottom** (88% win rate, weekly)
```python
@strategy(name="Double Bottom Reversal", timeframe="1week")

@pattern DoubleBottom:
    # Two lows at similar level
    low1 = lowest(low, 20)
    low2 = lowest(low, 10)

    price_diff = abs(low1 - low2) / low1
    price_diff < 0.03  # Within 3%

    # Time between lows: 4-12 weeks
    bars_between = 4 to 12

    # Neckline breakout
    neckline = (high[low1_index] + high[low2_index]) / 2
    close > neckline
    volume_on_breakout > avg_volume(20) * 1.5

@entry LONG:
    pattern.DoubleBottom
    neckline_breakout = close > neckline
    volume > volume.sma(20) * 1.5

@exit:
    target = neckline + (neckline - low2)  # Pattern height projection
    stop_loss = low2 - (0.02 * low2)  # 2% below second low

@risk:
    position_size = 3% of capital
```

#### Category 3: Range Trading

**6. Grid Trading** (75-80% win rate, 15min sideways)
```python
@strategy(name="Grid Trading Range", timeframe="15min")

@indicator BB(20, 2)
@indicator RSI(14)

@setup:
    # Identify range
    range_high = highest(high, 50)
    range_low = lowest(low, 50)
    range_mid = (range_high + range_low) / 2

    # Grid levels (5 levels)
    grid_levels = [
        range_low,
        range_mid - (range_mid - range_low) / 2,
        range_mid,
        range_mid + (range_high - range_mid) / 2,
        range_high
    ]

@entry LONG:
    regime == "RANGE"  # Only in sideways market
    close <= grid_levels[1]  # Near support
    rsi < 40

@entry SHORT:
    close >= grid_levels[3]  # Near resistance
    rsi > 60

@exit:
    if position.side == LONG:
        close >= range_mid  # Exit at mid-range

    if position.side == SHORT:
        close <= range_mid

@risk:
    stop_loss = range_low - (0.01 * range_low) if LONG else range_high + (0.01 * range_high)
    position_size = 1.5% of capital  # Lower risk per trade, multiple trades
```

**7. BB + RSI 70/30** (Range Bounce)
```python
@strategy(name="BB RSI Range Bounce", timeframe="1hour")

@indicator BB(20, 2)
@indicator RSI(14)

@entry LONG:
    regime == "RANGE"
    close <= bb_lower
    rsi < 30

@entry SHORT:
    close >= bb_upper
    rsi > 70

@exit:
    if position.side == LONG:
        close >= bb_middle OR rsi > 55

    if position.side == SHORT:
        close <= bb_middle OR rsi < 45

@risk:
    stop_loss = entry - (bb_middle - bb_lower) if LONG else entry + (bb_upper - bb_middle)
    take_profit = bb_middle
```

#### Category 4: Breakout Strategies

**8. 3-Layer Confirmation Filter** (82-88% win rate with volume)
```python
@strategy(name="3-Layer Breakout Filter", timeframe="5min")

@indicator EMA(9)
@indicator EMA(21)
@indicator ATR(14)
@indicator Volume(20)

@setup:
    # Define resistance level (recent swing high)
    resistance = highest(high, 20)
    support = lowest(low, 20)

@entry LONG (3-Layer Filter):
    # Layer 1: Structural Breakout
    close > resistance
    higher_highs_count >= 3  # Staircase pattern

    # Layer 2: Flow Confirmation (Volume + Momentum)
    volume > volume.sma(20) * 2.0  # 2x avg volume
    ema_9 > ema_21  # Momentum

    # Layer 3: Human Confirmation (Rejection Test)
    first_rejection_failed = high[-1] > resistance AND close[-1] < resistance
    second_attempt_success = close > resistance

    # All 3 layers must confirm
    all_layers_confirmed = true

@exit:
    # Profit target: 2x ATR
    take_profit = entry + (2 * atr)

    # Stop loss: below breakout candle low
    stop_loss = low[breakout_candle_index]

    # Trailing stop after 1x ATR profit
    if profit >= atr:
        trailing_stop = entry + (0.5 * atr)

@risk:
    position_size = 2% of capital
```

#### Category 5: Volatility Squeeze

**9. Bollinger Band Squeeze-Surge** (70-80% win rate)
```python
@strategy(name="BB Squeeze Surge", timeframe="15min")

@indicator BB(20, 2)
@indicator ATR(14)
@indicator Volume(20)

@pattern Squeeze:
    # BB Width contraction
    bb_width = (bb_upper - bb_lower) / bb_middle
    bb_width_pct = bb_width * 100

    squeeze_confirmed = bb_width_pct < 20  # BB Width < 20%

    # Multi-day contraction
    bb_width_declining = bb_width < bb_width[-1] AND bb_width[-1] < bb_width[-2]

@pattern Surge:
    # Breakout from squeeze
    close > bb_upper OR close < bb_lower
    volume > volume.sma(20) * 1.5
    atr > atr[-1]  # Volatility expansion

@entry LONG:
    pattern.Squeeze in last 5 bars
    pattern.Surge
    close > bb_upper

@entry SHORT:
    pattern.Squeeze in last 5 bars
    pattern.Surge
    close < bb_lower

@exit:
    # Exit when BB Width expands > 40%
    bb_width_pct > 40

    # Or profit target: 3x ATR
    take_profit = entry + (3 * atr) if LONG else entry - (3 * atr)

@risk:
    stop_loss = entry - (1.5 * atr) if LONG else entry + (1.5 * atr)
    position_size = 2.5% of capital
```

#### Category 6: Price Action Patterns

**10. Pin Bar + Inside Bar Combo**
```python
@strategy(name="Pin+Inside Combo", timeframe="1hour")

@pattern BullishPinBar:
    lower_wick >= 2.0 * body
    upper_wick <= 0.3 * body
    close > open

@pattern InsideBar:
    high < high[-1]
    low > low[-1]

@pattern PinInsideCombo:
    # Pin bar followed by inside bar
    pattern.BullishPinBar at candle[-1]
    pattern.InsideBar at candle[0]

@entry LONG:
    pattern.PinInsideCombo
    close > high[-1]  # Breakout above pin bar high

@exit:
    # Target: 2x pin bar range
    pin_range = high[-1] - low[-1]
    take_profit = entry + (2 * pin_range)

    # Stop: below pin bar low
    stop_loss = low[-1]

@risk:
    position_size = 2% of capital
```

#### Category 7: Harmonic Patterns

**11. Bat Pattern** (70-75% win rate, konservativ)
```python
@strategy(name="Bat Harmonic", timeframe="4hour")

@pattern BatPattern:
    # Fibonacci ratios (strict)
    XA = swing_range(X, A)
    AB = swing_range(A, B)
    BC = swing_range(B, C)
    CD = swing_range(C, D)

    # Bat ratios
    AB_retracement = AB / XA
    BC_retracement = BC / AB
    CD_extension = CD / BC

    # Validation
    AB_retracement in [0.382, 0.50]  # 38.2%-50% of XA
    BC_retracement in [0.382, 0.886]  # 38.2%-88.6% of AB
    CD_extension == 1.618  # 161.8% of BC (exact)
    D_retracement = (X - D) / XA
    D_retracement == 0.886  # D at 88.6% of XA (critical!)

    # PRZ (Potential Reversal Zone)
    prz_confluence = abs(D - (X + 0.886 * XA)) < 0.002 * X

@entry LONG:
    pattern.BatPattern
    close > D  # Confirmation above point D
    rsi < 30  # Oversold at PRZ

@exit:
    # Targets: Fibonacci levels
    target_1 = D + (0.382 * CD)  # 38.2% retracement
    target_2 = D + (0.618 * CD)  # 61.8% retracement

    # Conservative exit at 38.2%
    take_profit = target_1

    # Stop: below X
    stop_loss = X - (0.02 * X)

@risk:
    position_size = 2% of capital  # Conservative
```

**12. Butterfly Pattern** (70-75% win rate, aggressiv)
```python
@strategy(name="Butterfly Harmonic", timeframe="4hour")

@pattern ButterflyPattern:
    # Fibonacci ratios (Butterfly specific)
    AB_retracement = AB / XA
    BC_retracement = BC / AB
    CD_extension = CD / BC

    # Butterfly ratios (different from Bat!)
    AB_retracement == 0.786  # 78.6% of XA
    BC_retracement in [0.382, 0.886]
    CD_extension in [1.618, 2.618]  # 161.8%-261.8% of BC
    D_extension = (D - X) / XA
    D_extension == 1.27 OR D_extension == 1.618  # D beyond X (127%-161.8%)

    # PRZ
    prz_level = X + (1.27 * XA)  # Most common

@entry LONG:
    pattern.ButterflyPattern
    close > D
    rsi < 25  # Very oversold

@exit:
    # Aggressive profit targets
    target_1 = D + (0.382 * AD)
    target_2 = D + (0.618 * AD)
    target_3 = A  # Full retracement back to A

    # Aggressive: aim for target_2 or target_3
    take_profit = target_2

    # Stop: below D
    stop_loss = D - (0.02 * D)

@risk:
    position_size = 2.5% of capital  # Slightly aggressive
```

**13. Crab Pattern** (70-75% win rate, präzision, 40-70% profit)
```python
@strategy(name="Crab Harmonic", timeframe="1day")

@pattern CrabPattern:
    # Fibonacci ratios (Crab = most extreme)
    AB_retracement = AB / XA
    BC_retracement = BC / AB
    CD_extension = CD / BC

    # Crab ratios
    AB_retracement in [0.382, 0.618]
    BC_retracement in [0.382, 0.886]
    CD_extension in [2.618, 3.618]  # Extreme extension! (261.8%-361.8%)
    D_extension = (D - X) / XA
    D_extension == 1.618  # D at 161.8% extension of XA (critical!)

    # PRZ (very precise)
    prz_exact = X + (1.618 * XA)

@entry LONG:
    pattern.CrabPattern
    close > D
    rsi < 20  # Extremely oversold

    # Additional confirmation: reversal candle
    reversal_candle = close > open AND (close - open) > 0.5 * (high - low)

@exit:
    # High precision = high profit potential
    target_1 = D + (0.618 * AD)  # 61.8% retracement (40% profit typical)
    target_2 = A  # Full retracement (70% profit typical)

    # Conservative: 61.8% target
    take_profit = target_1

    # Stop: tight (pattern is precise)
    stop_loss = D - (0.01 * D)

@risk:
    position_size = 3% of capital  # Higher conviction due to precision
```

#### Category 8: Smart Money Concepts (ICT - Inner Circle Trader)

**14. Order Block + FVG + Liquidity Sweep (3-Act Model)**
```python
@strategy(name="Smart Money 3-Act", timeframe="15min")

@structure LiquidityPool:
    # Swing highs/lows with equal highs (inducement)
    swing_high = highest(high, 20)
    equal_highs = count_equal_highs(swing_high, tolerance=0.001)
    liquidity_zone = swing_high if equal_highs >= 2 else None

@structure LiquiditySweep:
    # Step 1: Identify liquidity zone
    liq_zone = LiquidityPool.liquidity_zone

    # Step 2: Wait for sweep
    sweep_candle = high > liq_zone AND volume > volume.sma(20) * 1.5

    # Step 3: Rejection (wick)
    rejection = (high - close) > 2 * (close - open)  # Wick > 2x body

    sweep_confirmed = sweep_candle AND rejection

@structure OrderBlock:
    # Step 4: Last candle before strong move (displacement)
    displacement = abs(close[0] - close[-1]) / close[-1]
    displacement_confirmed = displacement > 0.01  # 1% move

    volume_spike = volume > volume.sma(20) * 1.5

    # Order Block = candle BEFORE displacement
    ob_high = high[-1]
    ob_low = low[-1]
    ob_level = (ob_high + ob_low) / 2

    order_block_formed = displacement_confirmed AND volume_spike

@structure FairValueGap:
    # Step 5: Gap during displacement
    gap_up = low[0] > high[-2]  # Current low > 2 candles ago high
    gap_down = high[0] < low[-2]

    if gap_up:
        fvg_top = low[0]
        fvg_bottom = high[-2]
        fvg_direction = "bullish"

    if gap_down:
        fvg_top = low[-2]
        fvg_bottom = high[0]
        fvg_direction = "bearish"

@structure BreakOfStructure:
    # Step 6: Lower timeframe BOS (change of character)
    ltf = timeframe.lower("5min")  # If on 15min, check 5min

    ltf_higher_high = ltf.high > ltf.highest(high, 10)
    ltf_higher_low = ltf.low > ltf.highest(low, 10)

    bos_bullish = ltf_higher_high AND ltf_higher_low

@entry LONG (3-Act Confirmation):
    # Act 1: Inducement (Liquidity Sweep)
    LiquiditySweep.sweep_confirmed

    # Act 2: Displacement + Order Block
    OrderBlock.order_block_formed

    # Act 3: Retest + Entry
    close within 0.5% of OrderBlock.ob_level  # Price retest OB
    BreakOfStructure.bos_bullish  # LTF confirmation
    FairValueGap.fvg_direction == "bullish"  # FVG present

    # All 3 acts confirmed
    entry_price = close

@exit:
    # Target: FVG fill level
    take_profit = FairValueGap.fvg_top

    # Stop: below Order Block
    stop_loss = OrderBlock.ob_low - (0.005 * OrderBlock.ob_low)

@risk:
    position_size = 2% of capital

    # Risk-Reward
    risk = entry_price - stop_loss
    reward = take_profit - entry_price
    reward_to_risk_ratio = reward / risk

    # Only enter if R:R >= 2:1
    if reward_to_risk_ratio < 2.0:
        skip_entry = true
```

### 5.2 Pattern Organization

**Pattern Library Structure**:
```
03_JSON/CEL_Patterns/
├── scalping/
│   ├── stochastic_ema_pinbar.json
│   ├── rsi_multi_tf.json
│   └── volume_spike_scalp.json
├── daytrading/
│   ├── cup_and_handle.json
│   ├── bull_flag.json
│   ├── double_bottom.json
│   ├── ascending_triangle.json
│   └── engulfing_pattern.json
├── range_trading/
│   ├── grid_trading.json
│   ├── bb_rsi_bounce.json
│   └── support_resistance_levels.json
├── breakout/
│   ├── three_layer_confirmation.json
│   ├── volume_breakout.json
│   └── false_breakout_filter.json
├── volatility/
│   ├── bb_squeeze_surge.json
│   └── atr_expansion.json
├── price_action/
│   ├── pin_bar.json
│   ├── inside_bar.json
│   ├── pin_inside_combo.json
│   ├── hammer.json
│   ├── shooting_star.json
│   └── doji.json
├── harmonic/
│   ├── bat_pattern.json
│   ├── butterfly_pattern.json
│   ├── crab_pattern.json
│   └── gartley_pattern.json
└── smart_money/
    ├── order_blocks.json
    ├── fair_value_gaps.json
    ├── liquidity_sweeps.json
    ├── break_of_structure.json
    └── three_act_model.json
```

---

## 6. Script Execution Engine

### 6.1 Architecture

```
┌─────────────────────────────────────────────────────────┐
│ User writes script in CEL Script Editor                │
│ ┌──────────────────────────────────────────────────┐  │
│ │ @strategy(name="My Strategy")                    │  │
│ │ @indicator RSI(14)                               │  │
│ │ @entry LONG: rsi < 30 AND close > ema_34        │  │
│ └──────────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────────┘
                     │ Save
                     ▼
┌─────────────────────────────────────────────────────────┐
│ Script Parser (src/core/tradingbot/cel/parser.py)      │
│ ┌──────────────────────────────────────────────────┐  │
│ │ Parse DSL → Python AST                           │  │
│ │ Validate syntax                                  │  │
│ │ Extract indicators, patterns, entry/exit logic   │  │
│ └──────────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────────┘
                     │ Compile
                     ▼
┌─────────────────────────────────────────────────────────┐
│ Script Compiler (src/core/tradingbot/cel/compiler.py)  │
│ ┌──────────────────────────────────────────────────┐  │
│ │ Convert to executable Python code                │  │
│ │ Generate indicator calculation functions         │  │
│ │ Generate entry/exit condition functions          │  │
│ └──────────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────────┘
                     │ Store
                     ▼
┌─────────────────────────────────────────────────────────┐
│ JSON Strategy File (03_JSON/CEL_Patterns/*.json)       │
│ ┌──────────────────────────────────────────────────┐  │
│ │ {                                                │  │
│ │   "script_id": "my_strategy_v1",                 │  │
│ │   "indicators": [...],                           │  │
│ │   "entry": { "long": "compiled_code" },          │  │
│ │   "exit": { "code": "compiled_code" },           │  │
│ │   "risk": {...}                                  │  │
│ │ }                                                │  │
│ └──────────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────────┘
                     │ Load
                     ▼
┌─────────────────────────────────────────────────────────┐
│ Bot Controller (src/core/tradingbot/bot_controller.py) │
│ ┌──────────────────────────────────────────────────┐  │
│ │ Load JSON strategy                               │  │
│ │ Initialize Script Executor                       │  │
│ │ On each new bar:                                 │  │
│ │   1. Calculate indicators                        │  │
│ │   2. Execute entry logic                         │  │
│ │   3. Execute exit logic (if in position)         │  │
│ │   4. Execute risk management                     │  │
│ └──────────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────────┘
                     │ Execute
                     ▼
┌─────────────────────────────────────────────────────────┐
│ Script Executor (src/core/tradingbot/cel/executor.py)  │
│ ┌──────────────────────────────────────────────────┐  │
│ │ CEL Script API (RSI, MACD, pattern.*, etc.)      │  │
│ │ Execute compiled entry/exit conditions           │  │
│ │ Return signals: LONG, SHORT, EXIT, HOLD          │  │
│ └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### 6.2 Core Components

#### 1. Script Parser (`src/core/tradingbot/cel/parser.py`)
```python
class CELScriptParser:
    """Parse CEL Script DSL to Python AST."""

    def parse(self, script_code: str) -> ParsedScript:
        """Parse script and extract components.

        Returns:
            ParsedScript with:
            - metadata (strategy info)
            - indicators (list of indicator declarations)
            - patterns (custom pattern definitions)
            - entry_logic (compiled entry conditions)
            - exit_logic (compiled exit conditions)
            - risk_logic (compiled risk management)
        """
        # Parse DSL syntax
        # Extract @strategy, @indicator, @pattern, @entry, @exit, @risk sections
        # Validate syntax
        # Return structured ParsedScript object
```

#### 2. Script Compiler (`src/core/tradingbot/cel/compiler.py`)
```python
class CELScriptCompiler:
    """Compile parsed script to executable Python code."""

    def compile(self, parsed_script: ParsedScript) -> CompiledScript:
        """Compile to executable functions.

        Returns:
            CompiledScript with:
            - entry_fn: Callable[[FeatureVector], bool]  # Returns True if entry signal
            - exit_fn: Callable[[FeatureVector, Position], bool]
            - risk_fn: Callable[[FeatureVector], RiskParams]
            - pattern_fns: dict[str, Callable]
        """
        # Generate Python functions from DSL
        # Inject CEL API (RSI, MACD, pattern.*, etc.)
        # Return compiled executable functions
```

#### 3. Script Executor (`src/core/tradingbot/cel/executor.py`)
```python
class CELScriptExecutor:
    """Execute compiled scripts."""

    def __init__(self, compiled_script: CompiledScript):
        self.compiled_script = compiled_script
        self.api = CELScriptAPI()  # Provides RSI(), MACD(), pattern.*, etc.

    def evaluate_entry(self, features: FeatureVector) -> TradeSide | None:
        """Evaluate entry conditions.

        Returns:
            TradeSide.LONG if long entry
            TradeSide.SHORT if short entry
            None if no entry
        """
        # Execute compiled entry logic
        # Return signal

    def evaluate_exit(self, features: FeatureVector, position: Position) -> bool:
        """Evaluate exit conditions.

        Returns:
            True if should exit
            False otherwise
        """
        # Execute compiled exit logic

    def calculate_risk(self, features: FeatureVector) -> RiskParams:
        """Calculate risk parameters.

        Returns:
            RiskParams with stop_loss, take_profit, position_size
        """
        # Execute compiled risk logic
```

#### 4. CEL Script API (`src/core/tradingbot/cel/api.py`)
```python
class CELScriptAPI:
    """API functions available in CEL scripts."""

    def __init__(self, features: FeatureVector, candles: list[dict]):
        self.features = features
        self.candles = candles
        self._indicator_cache = {}

    # Indicator Functions
    def rsi(self, period: int = 14, source: str = 'close') -> float:
        """Calculate RSI."""
        # Implementation

    def macd(self, fast: int = 12, slow: int = 26, signal: int = 9) -> tuple[float, float, float]:
        """Calculate MACD."""
        # Implementation

    def ema(self, period: int, source: str = 'close') -> float:
        """Calculate EMA."""
        # Implementation

    # Pattern Detection
    def is_bullish_pinbar(self, wick_ratio: float = 2.0) -> bool:
        """Detect bullish pin bar."""
        # Implementation

    def is_bearish_pinbar(self, wick_ratio: float = 2.0) -> bool:
        """Detect bearish pin bar."""
        # Implementation

    # Market Structure
    def detect_order_block(self, displacement_threshold: float = 0.01) -> dict | None:
        """Detect order block."""
        # Implementation

    def detect_fair_value_gap(self) -> dict | None:
        """Detect fair value gap."""
        # Implementation

    def detect_liquidity_sweep(self, lookback: int = 20) -> bool:
        """Detect liquidity sweep."""
        # Implementation

    # Multi-Timeframe
    def higher_timeframe(self, tf: str) -> CELScriptAPI:
        """Access higher timeframe data."""
        # Return new API instance with higher TF data
```

### 6.3 Integration with Bot Controller

**Modified `bot_controller.py`** (add CEL script support):

```python
class BotController:
    def __init__(self, config: FullBotConfig, ...):
        # Existing code...

        # CEL Script support
        self._cel_script: CompiledScript | None = None
        self._cel_executor: CELScriptExecutor | None = None

    def load_cel_script(self, script_path: str) -> bool:
        """Load CEL script from JSON file.

        Args:
            script_path: Path to JSON script file

        Returns:
            True if loaded successfully
        """
        try:
            with open(script_path, 'r') as f:
                script_data = json.load(f)

            # Parse script
            parser = CELScriptParser()
            parsed = parser.parse(script_data['script_code'])

            # Compile script
            compiler = CELScriptCompiler()
            compiled = compiler.compile(parsed)

            # Initialize executor
            self._cel_executor = CELScriptExecutor(compiled)

            logger.info(f"CEL script loaded: {script_data['metadata']['name']}")
            return True

        except Exception as e:
            logger.error(f"Failed to load CEL script: {e}")
            return False

    async def process_bar(self, bar: dict) -> BotDecision | None:
        """Process new bar with CEL script support."""
        features = self.feature_engine.process_bar(bar)

        # If CEL script is loaded, use it for entry/exit logic
        if self._cel_executor:
            if self._state_machine.current_state == BotState.FLAT:
                # Evaluate entry
                entry_signal = self._cel_executor.evaluate_entry(features)
                if entry_signal:
                    # Calculate risk params
                    risk_params = self._cel_executor.calculate_risk(features)

                    # Create signal
                    signal = self._create_signal_from_cel(features, entry_signal, risk_params)
                    self._current_signal = signal

                    # Transition to SIGNAL state
                    self._state_machine.on_signal(signal, confirmed=False)

                    return self._create_decision(
                        BotAction.NO_TRADE,
                        entry_signal,
                        features,
                        ["CEL_SIGNAL_DETECTED"]
                    )

            elif self._state_machine.current_state == BotState.MANAGE:
                # Evaluate exit
                should_exit = self._cel_executor.evaluate_exit(features, self._position)
                if should_exit:
                    return await self._exit.handle_exit_signal(features, exit_signal="CEL_EXIT")

        # Fallback to existing logic if no CEL script
        return await super().process_bar(bar)
```

---

## 7. UI Implementation Details

### 7.1 Technology Stack

**Editor Component**:
- **Monaco Editor** (VS Code's editor): https://microsoft.github.io/monaco-editor/
  - Pros: Full VS Code features, TypeScript/Python support, extensions
  - Cons: ~3MB bundle size
- **Alternative**: **CodeMirror 6**: https://codemirror.net/
  - Pros: Lightweight (~500KB), highly customizable
  - Cons: Less features out-of-box

**Recommendation**: **Monaco Editor** (familiarity for users)

### 7.2 PyQt6 Integration

**Example Monaco Editor Integration**:

```python
from PyQt6.QtCore import QUrl, pyqtSignal
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import QWidget, QVBoxLayout

class MonacoEditor(QWidget):
    """Monaco Editor widget for CEL Script editing."""

    code_changed = pyqtSignal(str)  # Emitted when code changes
    syntax_error = pyqtSignal(str, int)  # (error message, line number)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Web view for Monaco Editor
        self.web_view = QWebEngineView()
        self.web_view.setMinimumSize(800, 600)

        # Load Monaco Editor HTML
        html_path = "src/ui/resources/monaco_editor.html"
        self.web_view.setUrl(QUrl.fromLocalFile(html_path))

        layout.addWidget(self.web_view)

    def set_code(self, code: str):
        """Set editor content."""
        js_code = f"editor.setValue(`{code}`)"
        self.web_view.page().runJavaScript(js_code)

    def get_code(self) -> str:
        """Get current editor content (async)."""
        # Use QWebChannel for Python-JS communication
        pass

    def set_language(self, language: str):
        """Set editor language (python, json, etc.)."""
        js_code = f"monaco.editor.setModelLanguage(editor.getModel(), '{language}')"
        self.web_view.page().runJavaScript(js_code)

    def add_marker(self, line: int, message: str, severity: str = "error"):
        """Add error/warning marker at line."""
        js_code = f"""
        monaco.editor.setModelMarkers(editor.getModel(), 'cel', [{{
            startLineNumber: {line},
            startColumn: 1,
            endLineNumber: {line},
            endColumn: 1000,
            message: '{message}',
            severity: monaco.MarkerSeverity.{severity.upper()}
        }}])
        """
        self.web_view.page().runJavaScript(js_code)
```

**Monaco Editor HTML Template** (`src/ui/resources/monaco_editor.html`):

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body { margin: 0; padding: 0; }
        #container { width: 100%; height: 100vh; }
    </style>
    <script src="https://cdn.jsdelivr.net/npm/monaco-editor@0.44.0/min/vs/loader.js"></script>
</head>
<body>
    <div id="container"></div>
    <script>
        require.config({ paths: { 'vs': 'https://cdn.jsdelivr.net/npm/monaco-editor@0.44.0/min/vs' }});

        require(['vs/editor/editor.main'], function() {
            // Define CEL Script language
            monaco.languages.register({ id: 'cel-script' });

            // Syntax highlighting rules
            monaco.languages.setMonarchTokensProvider('cel-script', {
                keywords: [
                    'strategy', 'indicator', 'pattern', 'entry', 'exit', 'risk',
                    'if', 'else', 'AND', 'OR', 'NOT', 'true', 'false',
                    'LONG', 'SHORT', 'regime', 'structure', 'timeframe'
                ],
                operators: [
                    '=', '>', '<', '!', '~', '?', ':', '==', '<=', '>=', '!=',
                    '&&', '||', '++', '--', '+', '-', '*', '/', '&', '|', '^', '%',
                    '<<', '>>', '>>>', '+=', '-=', '*=', '/=', '&=', '|=', '^=',
                    '%=', '<<=', '>>=', '>>>='
                ],
                symbols: /[=><!~?:&|+\-*\/\^%]+/,
                tokenizer: {
                    root: [
                        [/@[a-z_]\w*/, 'annotation'],
                        [/[a-z_]\w*/, {
                            cases: {
                                '@keywords': 'keyword',
                                '@default': 'identifier'
                            }
                        }],
                        [/[0-9]+(\.[0-9]+)?/, 'number'],
                        [/"([^"\\]|\\.)*$/, 'string.invalid'],
                        [/"/, 'string', '@string'],
                        [/\/\/.*$/, 'comment']
                    ],
                    string: [
                        [/[^\\"]+/, 'string'],
                        [/"/, 'string', '@pop']
                    ]
                }
            });

            // Auto-completion
            monaco.languages.registerCompletionItemProvider('cel-script', {
                provideCompletionItems: function(model, position) {
                    var suggestions = [
                        // Decorators
                        { label: '@strategy', kind: monaco.languages.CompletionItemKind.Keyword, insertText: '@strategy(name="${1:Strategy Name}", timeframe="${2:1min}")' },
                        { label: '@indicator', kind: monaco.languages.CompletionItemKind.Keyword, insertText: '@indicator ${1:RSI}(${2:14})' },
                        { label: '@pattern', kind: monaco.languages.CompletionItemKind.Keyword, insertText: '@pattern ${1:PatternName}:\n\t${2:condition}' },
                        { label: '@entry', kind: monaco.languages.CompletionItemKind.Keyword, insertText: '@entry ${1:LONG}:\n\t${2:condition}' },
                        { label: '@exit', kind: monaco.languages.CompletionItemKind.Keyword, insertText: '@exit:\n\t${1:condition}' },
                        { label: '@risk', kind: monaco.languages.CompletionItemKind.Keyword, insertText: '@risk:\n\tstop_loss = ${1:entry - (2 * atr)}\n\ttake_profit = ${2:entry + (3 * atr)}' },

                        // Indicators
                        { label: 'rsi', kind: monaco.languages.CompletionItemKind.Function, insertText: 'rsi(${1:14})' },
                        { label: 'macd', kind: monaco.languages.CompletionItemKind.Function, insertText: 'macd(${1:12}, ${2:26}, ${3:9})' },
                        { label: 'ema', kind: monaco.languages.CompletionItemKind.Function, insertText: 'ema(${1:34})' },
                        { label: 'sma', kind: monaco.languages.CompletionItemKind.Function, insertText: 'sma(${1:20})' },
                        { label: 'stochastic', kind: monaco.languages.CompletionItemKind.Function, insertText: 'stochastic(${1:14}, ${2:3}, ${3:3})' },
                        { label: 'atr', kind: monaco.languages.CompletionItemKind.Function, insertText: 'atr(${1:14})' },
                        { label: 'adx', kind: monaco.languages.CompletionItemKind.Function, insertText: 'adx(${1:14})' },

                        // Pattern functions
                        { label: 'pattern.is_bullish_pinbar', kind: monaco.languages.CompletionItemKind.Method, insertText: 'pattern.is_bullish_pinbar()' },
                        { label: 'pattern.is_bearish_pinbar', kind: monaco.languages.CompletionItemKind.Method, insertText: 'pattern.is_bearish_pinbar()' },
                        { label: 'pattern.is_inside_bar', kind: monaco.languages.CompletionItemKind.Method, insertText: 'pattern.is_inside_bar()' },

                        // Market structure
                        { label: 'structure.order_block', kind: monaco.languages.CompletionItemKind.Method, insertText: 'structure.order_block()' },
                        { label: 'structure.fair_value_gap', kind: monaco.languages.CompletionItemKind.Method, insertText: 'structure.fair_value_gap()' },
                        { label: 'structure.liquidity_sweep', kind: monaco.languages.CompletionItemKind.Method, insertText: 'structure.liquidity_sweep()' },

                        // Price access
                        { label: 'close', kind: monaco.languages.CompletionItemKind.Variable, insertText: 'close' },
                        { label: 'open', kind: monaco.languages.CompletionItemKind.Variable, insertText: 'open' },
                        { label: 'high', kind: monaco.languages.CompletionItemKind.Variable, insertText: 'high' },
                        { label: 'low', kind: monaco.languages.CompletionItemKind.Variable, insertText: 'low' },
                        { label: 'volume', kind: monaco.languages.CompletionItemKind.Variable, insertText: 'volume' }
                    ];
                    return { suggestions: suggestions };
                }
            });

            // Create editor
            window.editor = monaco.editor.create(document.getElementById('container'), {
                value: '// CEL Script Editor\n// Write your trading strategy here\n\n',
                language: 'cel-script',
                theme: 'vs-dark',
                automaticLayout: true,
                minimap: { enabled: true },
                scrollBeyondLastLine: false,
                fontSize: 14,
                tabSize: 4
            });

            // Listen to content changes
            window.editor.onDidChangeModelContent(function() {
                var code = window.editor.getValue();
                // Send to Python via QWebChannel (setup required)
            });
        });
    </script>
</body>
</html>
```

### 7.3 Main Window Layout (`src/ui/dialogs/cel_script_editor.py`)

```python
class CELScriptEditor(QDialog):
    """Unified CEL Script Editor (replaces 3 windows)."""

    script_saved = pyqtSignal(str)  # script_path
    script_deployed = pyqtSignal(str)  # script_id

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("CEL Script Editor")
        self.setMinimumSize(1400, 900)
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)

        # Left Panel: Pattern Library (250px)
        self.pattern_library = PatternLibraryWidget(self)
        self.pattern_library.setFixedWidth(250)
        self.pattern_library.pattern_selected.connect(self._on_pattern_selected)
        layout.addWidget(self.pattern_library)

        # Center Panel: Editor + Console
        center_splitter = QSplitter(Qt.Orientation.Vertical)

        # Monaco Editor
        self.editor = MonacoEditor(self)
        self.editor.code_changed.connect(self._on_code_changed)
        center_splitter.addWidget(self.editor)

        # Console
        self.console = ConsoleWidget(self)
        self.console.setMaximumHeight(150)
        center_splitter.addWidget(self.console)

        center_splitter.setStretchFactor(0, 3)  # Editor gets 75% height
        center_splitter.setStretchFactor(1, 1)  # Console gets 25%

        layout.addWidget(center_splitter, stretch=3)

        # Right Panel: Tabs (400px)
        right_panel = QWidget()
        right_panel.setFixedWidth(400)
        right_layout = QVBoxLayout(right_panel)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._create_properties_tab(), "Properties")
        self.tabs.addTab(self._create_backtest_tab(), "Backtest")
        self.tabs.addTab(self._create_results_tab(), "Results")
        self.tabs.addTab(self._create_ai_copilot_tab(), "AI Copilot")

        right_layout.addWidget(self.tabs)

        # Footer Actions
        footer_layout = QHBoxLayout()

        self.save_btn = QPushButton("💾 Save")
        self.save_btn.clicked.connect(self._on_save_clicked)
        footer_layout.addWidget(self.save_btn)

        self.run_live_btn = QPushButton("▶ Run Live")
        self.run_live_btn.clicked.connect(self._on_run_live_clicked)
        footer_layout.addWidget(self.run_live_btn)

        self.deploy_btn = QPushButton("📊 Deploy to Bot")
        self.deploy_btn.clicked.connect(self._on_deploy_clicked)
        footer_layout.addWidget(self.deploy_btn)

        self.close_btn = QPushButton("❌ Close")
        self.close_btn.clicked.connect(self.accept)
        footer_layout.addWidget(self.close_btn)

        right_layout.addLayout(footer_layout)

        layout.addWidget(right_panel)
```

---

## 8. Migration Strategy

### 8.1 Phased Approach

**Phase 1: Parser & Compiler (Week 1-2)**
- Implement CEL Script Parser
- Implement CEL Script Compiler
- Unit tests for parsing/compiling
- Example scripts for all pattern categories

**Phase 2: Script API & Executor (Week 2-3)**
- Implement CEL Script API (indicators, patterns, market structure)
- Implement Script Executor
- Integration with FeatureEngine
- Unit tests for API functions

**Phase 3: Editor UI (Week 3-4)**
- Implement Monaco Editor integration
- Implement Pattern Library Widget
- Implement Console/Error display
- Syntax highlighting and auto-completion

**Phase 4: Backtest Integration (Week 4)**
- Integrate BacktestEngine with CEL scripts
- Regime boundary visualization (from Entry Analyzer)
- Results display

**Phase 5: AI Copilot & Validation (Week 5)**
- Integrate AI Copilot (from Entry Analyzer's CopilotWorker)
- Walk-forward validation (from Entry Analyzer's ValidationWorker)
- Indicator optimization (from Entry Analyzer)

**Phase 6: Bot Integration & Testing (Week 6)**
- Integrate with BotController
- Live paper trading testing
- Bug fixes and refinements

### 8.2 Backward Compatibility

**Existing JSON Configs** (`03_JSON/Trading_Bot/*.json`):
- Keep existing JSON format for regime-based strategy routing
- CEL Scripts are **additional** to existing system (not replacement initially)
- Migration tool to convert old JSONs to CEL scripts (optional)

**Existing Windows**:
- **Strategy Settings Dialog**: Keep for now (for JSON config management)
- **Strategy Concept Window**: Deprecate (functionality moved to CEL Editor)
- **Entry Analyzer**: Deprecate (functionality moved to CEL Editor)

### 8.3 Deprecation Timeline

- **Month 1**: CEL Script Editor released, existing windows still available
- **Month 2**: Warning messages in old windows ("Use CEL Script Editor for new strategies")
- **Month 3**: Old windows marked as deprecated
- **Month 4+**: Remove old windows (if users migrate successfully)

---

## 9. Implementation Estimate

### 9.1 Time Breakdown

| Phase | Tasks | Hours | Complexity |
|-------|-------|-------|------------|
| **1. Parser & Compiler** | DSL parsing, AST generation, code compilation | 40h | High |
| **2. Script API** | Indicator functions, pattern detection, market structure | 32h | Medium |
| **3. Script Executor** | Execution engine, integration with BotController | 24h | Medium |
| **4. Editor UI** | Monaco integration, Pattern Library, Console | 40h | High |
| **5. Backtest Integration** | BacktestEngine, regime visualization, results | 24h | Medium |
| **6. AI & Validation** | AI Copilot, walk-forward validation, optimization | 24h | Medium |
| **7. Pattern Implementation** | All 50+ patterns as script templates | 32h | Medium |
| **8. Testing & Docs** | Unit tests, integration tests, user docs | 32h | Medium |
| **9. Bug Fixes & Polish** | UI refinements, edge cases, performance | 24h | Low |

**Total**: ~272 hours (~34 working days = **6-7 weeks** for one developer)

### 9.2 Critical Path

```
Parser/Compiler → API → Executor → Editor UI → Backtest → AI/Validation → Patterns → Testing
   (Week 1-2)    (Week 2)  (Week 3)   (Week 3-4)   (Week 4)    (Week 5)     (Week 5-6)  (Week 6)
```

### 9.3 Risks & Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Parser complexity too high | High | Medium | Use existing Python parser libraries (ast, parso) |
| Monaco Editor integration issues | Medium | Low | Fallback to CodeMirror if needed |
| Performance issues with complex scripts | Medium | Medium | Add caching, optimize indicator calculations |
| User learning curve for new syntax | Medium | High | Provide extensive examples, templates, and tutorials |
| Migration resistance (users prefer old UI) | Low | Medium | Keep old windows available initially, show benefits |

---

## 10. Success Criteria

### 10.1 Functional Requirements

✅ **Must Have**:
1. Script editor with syntax highlighting and auto-completion
2. All 50+ patterns from Chartmuster_Erweitert_2026.md as templates
3. Query API for indicators, patterns, market structure
4. Backtest integration with regime visualization
5. Save/load scripts as JSON files
6. Deploy scripts to BotController
7. Error validation with line numbers

✅ **Should Have**:
8. AI Copilot for strategy recommendations
9. Walk-forward validation
10. Indicator parameter optimization
11. Multi-timeframe support
12. Live paper trading testing

✅ **Nice to Have**:
13. Script versioning and history
14. Collaborative editing (multiple users)
15. Script marketplace (community scripts)
16. Performance profiling for scripts

### 10.2 User Acceptance Criteria

1. **User can create a new strategy** from scratch in < 10 minutes using pattern templates
2. **User can edit existing patterns** (e.g., change Pin Bar wick ratio from 2.0 to 2.5)
3. **User can backtest a strategy** and see results with regime boundaries on chart
4. **User can deploy a strategy** to trading bot with one click
5. **User gets real-time error feedback** when script has syntax errors
6. **User can access all patterns** from Chartmuster_Erweitert_2026.md as drag-and-drop templates
7. **No more redundant windows** - everything in ONE unified editor

---

## 11. Next Steps

### 11.1 Immediate Actions (This Week)

1. **User Review of This Plan**
   - Review all 11 sections
   - Confirm CEL Script Language syntax is acceptable
   - Confirm UI mockup meets requirements
   - Confirm pattern implementation approach
   - Approve or request changes

2. **Finalize Design Decisions**
   - Monaco Editor vs CodeMirror (recommendation: Monaco)
   - Python-based DSL vs custom syntax (recommendation: Python-based)
   - JSON storage format (recommendation: as shown in Section 3.3)

3. **Create Prototype**
   - Implement simple parser for one pattern (e.g., Pin Bar)
   - Show proof-of-concept with editor and execution

### 11.2 Development Kickoff (Next Week)

1. **Set up project structure**:
   ```
   src/core/tradingbot/cel/
   ├── __init__.py
   ├── parser.py          # CEL Script Parser
   ├── compiler.py        # CEL Script Compiler
   ├── executor.py        # Script Executor
   ├── api.py             # CEL Script API (RSI, MACD, pattern.*, etc.)
   └── patterns/          # Pattern detection functions
       ├── pinbar.py
       ├── inside_bar.py
       ├── order_blocks.py
       └── ...

   src/ui/dialogs/
   └── cel_script_editor.py  # Main unified editor window

   src/ui/widgets/
   ├── monaco_editor.py      # Monaco Editor integration
   ├── pattern_library_widget.py
   └── console_widget.py

   src/ui/resources/
   └── monaco_editor.html    # Monaco HTML template

   03_JSON/CEL_Patterns/     # Pattern templates
   ├── scalping/
   ├── daytrading/
   ├── smart_money/
   └── ...
   ```

2. **Start Phase 1**: Parser & Compiler implementation

3. **Create first 5 pattern templates**:
   - Stochastic + EMA + Pin Bar (scalping)
   - Cup & Handle (day trading)
   - Grid Trading (range)
   - 3-Layer Breakout (breakout)
   - Order Block + FVG (smart money)

---

## 12. Summary

**Problem**: Three redundant UI windows (Strategy Settings, Strategy Concept, Entry Analyzer) with CEL misimplemented as a rule engine instead of a script programming interface.

**Solution**: Consolidate into ONE **CEL Script Editor** with:
- Script programming language (Python-based DSL)
- Monaco Editor with syntax highlighting
- Pattern library with 50+ templates from Chartmuster_Erweitert_2026.md
- Query API for indicators, patterns, market structure
- Integrated backtesting with regime visualization
- AI Copilot and validation
- Deploy to trading bot

**Timeline**: 6-7 weeks

**Next Step**: **USER APPROVAL** of this plan before implementation starts.

---

**Questions for User**:
1. Do you approve the CEL Script Language syntax shown in Section 3.1?
2. Do you approve the unified window design shown in Section 4.1?
3. Are there any specific patterns from Chartmuster_Erweitert_2026.md that should be prioritized?
4. Should we keep the existing Strategy Settings Dialog for JSON config management, or deprecate it immediately?
5. Any other requirements or changes needed?
