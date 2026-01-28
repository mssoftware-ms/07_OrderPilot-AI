# Knowledge Base - OrderPilot-AI Trading System

**Version:** 2.0
**Last Updated:** 2026-01-28
**Status:** ✅ Complete

---

## 📚 Document Index

### CEL (Common Expression Language)

| Document | Description | LOC/Pages | Status |
|----------|-------------|-----------|--------|
| **CEL_Befehle_Liste_v2.md** | Complete CEL function reference (97 functions) | 1,200+ | ✅ |
| **CEL_Functions_Reference_v3.md** | Detailed function descriptions v3.1 | 520+ | ✅ |
| **CEL_Neue_Funktionen_v2.4.md** | New features v2.4 (No Entry, Regime functions) | 320+ | ✅ |
| **cel_help_trading.md** | CEL Editor trading guide (5 tabs) | 320+ | ✅ |

### JSON Integration & Configuration

| Document | Description | LOC/Pages | Status |
|----------|-------------|-----------|--------|
| **CEL_JSON_INTEGRATION.md** | CEL & JSON integration architecture | 650+ | ✅ |
| **JSON_Entry_System_Complete_Guide.md** | ⭐ JSON Entry System technical guide | 1,000+ | ✅ NEW |

### Regime Detection & Strategy

| Document | Description | LOC/Pages | Status |
|----------|-------------|-----------|--------|
| **Regime Erkennung JSON Template Rules Regime.md** | Regime detection JSON templates | 610+ | ✅ |

### Indicator System

| Document | Description | LOC/Pages | Status |
|----------|-------------|-----------|--------|
| **INDICATOR_TYPE_SYNC_ANALYSIS.md** | Indicator type synchronization analysis | 170+ | ✅ |

---

## 🎯 Quick Navigation

### For Traders

**Getting Started:**
1. Start here: `cel_help_trading.md` - CEL Editor basics (5 trading tabs)
2. Then read: `CEL_Befehle_Liste_v2.md` - Available functions (97 total)
3. For JSON Entry: `JSON_Entry_System_Complete_Guide.md` - Alternative entry system

**Strategy Development:**
- **Regime-Based Strategies:** `Regime Erkennung JSON Template Rules Regime.md`
- **JSON Configuration:** `CEL_JSON_INTEGRATION.md`
- **Advanced Features:** `CEL_Neue_Funktionen_v2.4.md`

### For Developers

**Architecture & Integration:**
1. `CEL_JSON_INTEGRATION.md` - System architecture overview
2. `JSON_Entry_System_Complete_Guide.md` - JSON Entry implementation
3. `INDICATOR_TYPE_SYNC_ANALYSIS.md` - Indicator system details

**API Reference:**
- `CEL_Functions_Reference_v3.md` - Detailed function API
- `CEL_Befehle_Liste_v2.md` - Function signatures & examples

---

## 🚀 New Features (v2.0)

### JSON Entry System (2026-01-28)

**Status:** ✅ Production Ready

**Overview:**
The JSON Entry System enables CEL-based entry logic via JSON configuration files, parallel to the standard CEL Editor system.

**Key Features:**
- ✅ CEL expressions in JSON (no code changes needed)
- ✅ Dual JSON sources (Regime + Indicator)
- ✅ Parallel execution (new "Start Bot (JSON Entry)" button)
- ✅ 70+ CEL functions available
- ✅ < 5ms evaluation per bar
- ✅ 38/38 unit tests passed (100%)

**Documentation:**
- **Technical Guide:** `JSON_Entry_System_Complete_Guide.md` (1,000+ lines)
- **User Guide:** `../docs/260128_JSON_Entry_System_README.md`
- **Integration Tests:** `../docs/260128_JSON_Entry_Integration_Tests.md`
- **Help UI:** `../Help/index.html#bot-json-entry`

**Example JSON:**
```json
{
  "schema_version": "2.0.0",
  "indicators": {
    "rsi14": {"type": "RSI", "period": 14},
    "adx14": {"type": "ADX", "period": 14}
  },
  "entry_expression": "rsi < 35 && adx > 25 && macd_hist > 0"
}
```

**Use Cases:**
- Entry strategy prototyping
- A/B testing different entry conditions
- Simple entry-focused strategies (SL/TP from UI)
- Quick strategy iteration without code changes

---

## 📖 Document Details

### CEL_Befehle_Liste_v2.md

**Purpose:** Complete reference of all 97 CEL functions

**Contents:**
- Price functions (10)
- Indicator functions (25)
- Regime functions (8)
- Trading functions (15)
- Math functions (12)
- Logic functions (10)
- Array/List functions (8)
- String functions (9)

**Use When:** Looking up function syntax, parameters, return values

---

### CEL_Functions_Reference_v3.md

**Purpose:** Detailed documentation for each CEL function

**Contents:**
- Function descriptions
- Parameter types
- Return values
- Usage examples
- Edge cases
- Best practices

**Use When:** Need detailed explanation of function behavior

---

### CEL_Neue_Funktionen_v2.4.md

**Purpose:** Documentation of new features in v2.4

**New Features:**
- No Entry Workflow (🚫 Entry Blocker)
- Regime functions (`last_closed_regime()`, `trigger_regime_analysis()`)
- 69+ available variables
- Enhanced trading context

**Use When:** Learning about latest CEL features

---

### cel_help_trading.md

**Purpose:** Practical guide for CEL Editor with 5 trading tabs

**Covers:**
- No Entry (entry blocker/safety filter)
- Entry (buy/sell conditions)
- Exit (take profit/stop loss)
- Before Exit (pre-exit checks)
- Update Stop (trailing stop logic)

**Variables Available:**
- `chart.*` - Price, volume, candle data
- `bot.*` - Bot configuration (risk, SL/TP, trailing)
- `regime.*` - Regime detection (optional)
- `trade.*` - Current trade state

**Use When:** Building strategies in CEL Editor UI

---

### CEL_JSON_INTEGRATION.md

**Purpose:** Architecture documentation for CEL & JSON integration

**Covers:**
- System architecture (Regime-Based System)
- Data flow (JSON → Loader → Detector → Router → CEL → Trading Bot)
- Component matrix
- JSON config format (Trading Bot Config v1.0)
- Regime detection (multi-regime, no early-exit)
- Strategy routing (regime-based selection)
- CEL evaluation (cached, fail-safe)

**Comparison:**
| System | CEL Usage | Complexity | Use Case |
|--------|-----------|------------|----------|
| Regime-Based | Entry/Exit/Stop via CEL Rules | High | Multi-strategy systems |
| JSON Entry | Entry expression only | Low | Entry-focused strategies |

**Use When:** Understanding system architecture, integrating CEL with JSON

---

### JSON_Entry_System_Complete_Guide.md ⭐ NEW

**Purpose:** Complete technical guide for JSON Entry System

**Covers:**
- Architecture (JsonEntryLoader, JsonEntryScorer, Pipeline)
- JSON file formats (Regime + Indicator JSON)
- CEL expression language (69+ variables)
- Implementation details (context building, reason codes)
- Usage guide (UI integration, log messages)
- Advanced features (A/B testing, regime-adaptive entry)
- Performance & optimization (< 5ms per bar)
- Testing & validation (38 unit tests, 12 integration tests)
- Troubleshooting (common issues, debugging workflow)
- API reference (complete class documentation)

**Use When:**
- Implementing JSON Entry strategies
- Understanding JSON Entry system architecture
- Troubleshooting JSON Entry issues
- Comparing Standard Entry vs. JSON Entry

---

### Regime Erkennung JSON Template Rules Regime.md

**Purpose:** Regime detection system documentation

**Covers:**
- Regime JSON template structure
- Threshold definitions (RSI, ADX, MACD, etc.)
- Multi-regime detection (no early-exit)
- Priority sorting
- CEL-based regime rules

**Use When:** Configuring regime detection, creating regime JSONs

---

### INDICATOR_TYPE_SYNC_ANALYSIS.md

**Purpose:** Analysis of indicator type synchronization

**Covers:**
- Indicator type definitions
- Field naming conventions
- Synchronization issues
- Migration strategies

**Use When:** Working with indicator system, debugging type mismatches

---

## 🔧 Development Workflow

### Strategy Development with CEL Editor

```
1. Read: cel_help_trading.md (basics)
   ↓
2. Design strategy (entry/exit/stop logic)
   ↓
3. Reference: CEL_Befehle_Liste_v2.md (functions)
   ↓
4. Implement in CEL Editor (5 tabs)
   ↓
5. Test in Paper Trading
   ↓
6. Refine based on results
```

### Strategy Development with JSON Entry

```
1. Read: JSON_Entry_System_Complete_Guide.md (overview)
   ↓
2. Create Regime JSON with entry_expression
   ↓
3. (Optional) Create Indicator JSON
   ↓
4. Reference: CEL_Befehle_Liste_v2.md (available variables)
   ↓
5. Test expression incrementally
   ↓
6. Click "Start Bot (JSON Entry)"
   ↓
7. Monitor logs, refine expression
```

### Integration Development

```
1. Read: CEL_JSON_INTEGRATION.md (architecture)
   ↓
2. Understand data flow (JSON → CEL → Bot)
   ↓
3. Implement custom features
   ↓
4. Reference: CEL_Functions_Reference_v3.md (API)
   ↓
5. Write unit tests
   ↓
6. Integration tests
```

---

## 📊 System Comparison

### CEL Editor (Regime-Based System)

**Pros:**
- ✅ Full control (Entry, Exit, Stop, No Entry, Before Exit)
- ✅ Complex multi-strategy routing
- ✅ Strategy sets with overrides
- ✅ Regime-based strategy selection

**Cons:**
- ❌ Higher complexity (5 tabs)
- ❌ Steeper learning curve
- ❌ More configuration required

**Best For:**
- Professional traders
- Complex multi-strategy systems
- Production trading with full automation
- Advanced regime-adaptive strategies

### JSON Entry System

**Pros:**
- ✅ Simple (single CEL expression)
- ✅ Fast prototyping
- ✅ Easy A/B testing
- ✅ Minimal configuration

**Cons:**
- ❌ Entry logic only (no Exit/Stop CEL rules)
- ❌ Less control (SL/TP from UI)
- ❌ No strategy routing

**Best For:**
- Strategy prototyping
- Entry condition testing
- Simple entry-focused strategies
- Beginners learning CEL

---

## 🎓 Learning Path

### Beginner

1. **Start:** `cel_help_trading.md` - Learn 5 trading tabs
2. **Practice:** Write simple entry/exit rules
3. **Reference:** `CEL_Befehle_Liste_v2.md` - Look up functions as needed
4. **Try:** `JSON_Entry_System_Complete_Guide.md` - Simpler entry-only approach

### Intermediate

1. **Advanced Features:** `CEL_Neue_Funktionen_v2.4.md` - No Entry, Regime functions
2. **Regime Strategies:** `Regime Erkennung JSON Template Rules Regime.md`
3. **JSON Integration:** `CEL_JSON_INTEGRATION.md` - Understand architecture
4. **JSON Entry:** Build strategies with JSON Entry System

### Advanced

1. **Deep Dive:** `CEL_Functions_Reference_v3.md` - Master all functions
2. **Architecture:** `CEL_JSON_INTEGRATION.md` - System internals
3. **Custom Development:** Extend CEL engine, add custom functions
4. **Production:** Deploy complex multi-strategy systems

---

## 📝 Quick Reference

### Most Used CEL Functions

```cel
// Price Functions
pct_change(from, to)              // Percentage change
price_above_sma(price, sma)       // Price above SMA

// Indicator Functions
rsi_oversold(rsi, threshold)      // RSI < threshold (default 30)
adx_strong(adx)                   // ADX > 25
macd_bullish(macd_hist)           // MACD histogram > 0

// Trading Functions
is_trade_open(trade)              // Check if trade is open
stop_hit_long(trade, price)       // Check if stop loss hit
tp_hit(trade, price)              // Check if take profit hit

// Regime Functions
in_regime(current, expected)      // Check regime match
last_closed_regime()              // Get last closed bar regime
trigger_regime_analysis()         // Trigger regime detection

// Logic Functions
coalesce(value1, value2)          // First non-null value
isnull(value)                     // Check if null
has(list, value)                  // Check if value in list
```

### Most Used Variables

```cel
// Chart Variables
chart.price, chart.open, chart.high, chart.low, chart.volume
chart.is_bullish, chart.is_bearish
chart.prev_close, chart.prev_high, chart.prev_low
chart.change, chart.change_pct

// Bot Variables
bot.paper_mode, bot.leverage, bot.risk_per_trade_pct
bot.trailing_stop_enabled, bot.trailing_stop_activation_pct
bot.sl_atr_multiplier, bot.tp_atr_multiplier

// Regime Variables
regime.current, regime.strength, regime.confidence

// Trade Variables
trade.entry_price, trade.stop_loss, trade.tp_price
trade.side, trade.quantity

// JSON Entry System Variables
close, open, high, low, volume
rsi, adx, macd, macd_hist, sma_20, ema_12, bb_pct
regime  // "BULL", "BEAR", "NEUTRAL"
side    // "long" or "short"
```

---

## 🔗 External Resources

**CEL Specification:**
- GitHub: https://github.com/google/cel-spec
- Language Definition: https://github.com/google/cel-spec/blob/master/doc/langdef.md
- Python Implementation: https://pypi.org/project/cel-python/

**JSON Schema:**
- JSON Schema Draft 2020-12: https://json-schema.org/draft/2020-12/schema
- Pydantic v2: https://docs.pydantic.dev/latest/

**OrderPilot-AI:**
- Documentation: `../docs/`
- Help UI: `../Help/index.html`
- Examples: `../03_JSON/Entry_Analyzer/`

---

## 📞 Support

**Issues & Questions:**
- GitHub Issues (internal)
- Team documentation
- Help UI (`Help/index.html`)

**Document Maintainers:**
- CEL System: Development Team
- JSON Entry System: Development Team (2026-01-28)
- Knowledge Base: Development Team

---

**Last Review:** 2026-01-28
**Next Review:** After next major feature release
**Status:** ✅ Complete & Up-to-Date
