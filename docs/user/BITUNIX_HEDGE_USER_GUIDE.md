# Bitunix HEDGE Execution - User Guide

**Task 5.23**: Interactive user workflow documentation

---

## Table of Contents
1. [Overview](#overview)
2. [Setup & Configuration](#setup--configuration)
3. [Basic Workflow](#basic-workflow)
4. [Advanced Features](#advanced-features)
5. [Safety & Risk Management](#safety--risk-management)
6. [Troubleshooting](#troubleshooting)

---

## Overview

### What is HEDGE Mode?
HEDGE mode allows you to hold **simultaneous LONG and SHORT positions** on the same trading pair. This is different from ONE_WAY mode where you can only have one position direction at a time.

**Example**:
- HEDGE Mode: You can be LONG 0.5 BTC AND SHORT 0.3 BTC at the same time
- ONE_WAY Mode: You can only be LONG 0.5 BTC OR SHORT 0.3 BTC

### Key Features
✅ Adaptive Limit Entry - Orders adjust to market automatically
✅ Trailing Stop Loss - Lock in profits as market moves
✅ Single-Trade Gate - Maximum 1 active trade (safety)
✅ WebSocket Real-Time - Instant order updates
✅ Rate-Limit Protection - Prevents API abuse
✅ State Persistence - Resume after restart

---

## Setup & Configuration

### 1. Set Environment Variables (Windows)

**IMPORTANT**: Never hardcode API keys!

1. Press `Win + R`, type `sysdm.cpl`, press Enter
2. Click "Advanced" tab → "Environment Variables"
3. Under "User variables", click "New"
4. Add these variables:

```
Variable Name: BITUNIX_API_KEY
Variable Value: your-api-key-here

Variable Name: BITUNIX_API_SECRET
Variable Value: your-api-secret-here

Variable Name: BITUNIX_USE_TESTNET
Variable Value: true  (use "false" for mainnet)
```

5. Click OK and **restart application**

### 2. Launch Application

1. Open OrderPilot-AI
2. Navigate to "Trading Bot" tab
3. Find "Bitunix HEDGE Execution" widget

### 3. Initial Connection

1. Click **"Connect"** button
2. Wait for status to show **"Connected"** (green)
3. Click **"Set HEDGE"** button
4. Mode label should show **"HEDGE"** (green)

✅ **You're now ready to trade!**

---

## Basic Workflow

### Step 1: Select Trading Pair & Leverage

1. **Symbol**: Choose from dropdown (e.g., BTCUSDT)
2. **Leverage**: Set leverage (1x-20x, default: 5x)
3. Click **"Apply Leverage"**
4. Wait for confirmation

**Limits Display**: Shows minimum quantity, precision, and leverage range for selected pair.

### Step 2: Configure Entry

1. **Side**: Select LONG or SHORT
2. **Order Type**: LIMIT or MARKET
3. **Effect**: POST_ONLY (recommended) or GTC/IOC/FOK
4. **Price**: Set limit price (LIMIT orders only)
5. **Quantity**: Enter position size (e.g., 0.001 BTC)
6. **Offset %**: Set adaptive offset (0.001% - 0.500%)

**Adaptive Offset Explained**:
- **LONG**: Order price = Market × (1 + offset)
  - Example: Market $93,000, Offset 0.05% → Order at $93,046.50
- **SHORT**: Order price = Market × (1 - offset)
  - Example: Market $93,000, Offset 0.05% → Order at $92,953.50

### Step 3: Place Order (ARM & SEND)

**Safety Mechanism**: Two-step entry to prevent accidental orders

1. Click **"ARM (3s)"**
2. SEND button activates (green)
3. You have **3 seconds** to click **"SEND"**
4. If you wait >3s, it auto-disarms (safety timeout)

**After clicking SEND**:
- State changes to **"ENTRY_PENDING"** (orange)
- Order ID appears in footer
- Adaptive price tracking starts (if using adaptive)
- Cancel button enables

### Step 4: Monitor Order

**Adaptive Price Display**: Shows last calculated price and timestamp
- Format: `93046.5 @ 14:32:15`
- Updates every ~500ms
- Modify calls rate-limited to 4/s

**What's Happening**:
1. Order placed as LIMIT at calculated price
2. System monitors market price continuously
3. Recalculates entry price with offset
4. Modifies order if price changed
5. Stops on FILLED, CANCELLED, or timeout (5 minutes)

### Step 5: Position Open

**When Order Fills**:
- State changes to **"POSITION_OPEN"** (green)
- Position ID displayed
- Exit buttons enable (Close, Flash Close)
- Adaptive tracking stops

**TP/SL Setup** (Optional):
- If TP/SL configured: Automatically placed on exchange
- Exchange SL display shows current SL price
- Format: `Exchange SL: 91500.0 @ 14:35:20`

### Step 6: Trailing Stop (Optional)

**Enable Trailing**:
1. Check **"Use Trailing Stop"**
2. Trailing starts automatically
3. SL adjusts as market moves favorably

**How It Works**:
- **LONG**: SL trails UP as price rises
  - Example: Entry $93,000, Trail 2%
  - Price → $94,000: SL → $92,120 (94,000 × 0.98)
  - Price → $95,000: SL → $93,100 (95,000 × 0.98)
- **SHORT**: SL trails DOWN as price falls
  - Example: Entry $93,000, Trail 2%
  - Price → $92,000: SL → $93,840 (92,000 × 1.02)
  - Price → $91,000: SL → $92,820 (91,000 × 1.02)

**Important**:
- SL only moves in **favorable direction** (protects profit)
- LONG: SL never moves down
- SHORT: SL never moves up
- Updates debounced to 2/s (prevents spam)

### Step 7: Exit Position

**Option A: Normal Close**
1. Click **"Close Position"**
2. Close order placed
3. State → "EXIT_PENDING"
4. Wait for fill
5. State → "CLOSED"

**Option B: Flash Close (Emergency)**
1. Click **"Flash Close"** (red button)
2. **WARNING DIALOG** appears
3. Read warning carefully
4. Confirm if necessary
5. Position closed at MARKET immediately
6. **No price protection - use only in emergency!**

---

## Advanced Features

### Adaptive Limit Entry

**Benefits**:
- Avoids market impact (no market order slippage)
- Stays at front of order book
- Increases fill probability
- Rate-limited to prevent API abuse

**Stop Adaptive**:
- Click **"Stop Adaptive"** button
- Confirmation dialog
- Order remains at last calculated price
- No more modifications

### Cancel Pending Order

1. Click **"Cancel"** button (only enabled in ENTRY_PENDING)
2. Confirmation dialog
3. Order cancelled on exchange
4. State returns to IDLE

### ERROR_LOCK Recovery

**If System Enters ERROR_LOCK**:
- State turns red
- "Unlock ERROR_LOCK" button appears

**To Unlock**:
1. **IMPORTANT**: First verify no open orders/positions exist!
2. Click "Unlock ERROR_LOCK"
3. Read warning
4. Confirm unlock
5. State returns to IDLE

**Before Unlocking**:
- Check exchange UI for open orders
- Understand what caused the error
- Fix underlying issue
- DO NOT unlock if positions are open!

---

## Safety & Risk Management

### Safety Limits (Configurable)

**Default Limits** (can be changed in config):
- Max Notional: $10,000 USD
- Max Leverage: 20x
- Max Position Size: 1.0 BTC

**What Happens If Exceeded**:
- Order rejected BEFORE sending to exchange
- Clear error message displayed
- No API call made

### KILL SWITCH (Emergency Only)

**⚠️ USE ONLY IN EMERGENCY ⚠️**

**What It Does**:
- Closes ALL open positions for selected symbol
- Uses MARKET orders (immediate execution)
- Cannot be undone
- Irreversible

**How to Use**:
1. Click **"KILL SWITCH"** (red button)
2. **Triple Confirmation**:
   - Warning dialog: Click YES
   - Type symbol to confirm: Type exact symbol
   - Final warning: Click YES
3. All positions closed
4. Success message shown

**When to Use**:
- Exchange hack/system issue
- Account compromise suspected
- Catastrophic market event
- Application malfunction

### Single-Trade Gate

**Protection**: Maximum 1 active trade at a time

**Why**:
- Prevents double-entry bugs
- Simplifies state management
- Reduces risk of multiple simultaneous losses

**What It Means**:
- Cannot place order if position already open
- Cannot open second LONG/SHORT until first closed
- Clear error message if attempted

### Rate Limiting

**Automatic Protection Against**:
- API abuse
- Account suspension
- IP bans

**Limits**:
- place_order: 8/s
- modify_order: 4/s
- cancel_order: 4/s
- flash_close: 4/s
- TP/SL operations: 2/s

**User Impact**:
- Orders/modifications slightly delayed if burst
- Transparent - handled automatically
- Prevents 429 errors

---

## Troubleshooting

### Connection Issues

**Symptom**: Status shows "Failed" or stuck on "Connecting"

**Solutions**:
1. Check internet connection
2. Verify API keys in environment variables
3. Restart application
4. Check Bitunix API status (exchange website)
5. Check logs: `data/trade_audit.log`

### HEDGE Mode Not Setting

**Symptom**: Mode stays at "—" after clicking "Set HEDGE"

**Solutions**:
1. Ensure connected first
2. Close all existing positions on exchange
3. Try different symbol
4. Check error in logs

### Order Not Filling

**Symptom**: Stuck in ENTRY_PENDING for long time

**Solutions**:
1. Check if price too far from market (large offset)
2. Verify sufficient balance
3. Cancel and retry with closer price
4. Check exchange UI for order status
5. Wait for timeout (5 minutes) if stuck

### Adaptive Limit Not Working

**Symptom**: Price not updating in display

**Solutions**:
1. Verify order is in ENTRY_PENDING state
2. Check WebSocket connection (status: Connected)
3. Feed market price data (check if ticks arriving)
4. Review logs for modify_order calls
5. Check rate limit not exceeded

### Position Not Closing

**Symptom**: Close order stuck or failed

**Solutions**:
1. Try Flash Close (emergency)
2. Check exchange UI - close manually if needed
3. Verify position ID correct
4. Check balance for close order
5. Use KILL SWITCH as last resort

### High Memory Usage

**Symptom**: Application slow or high RAM usage

**Solutions**:
1. Restart application periodically
2. Disable raw WS event logging if enabled
3. Clear old log files
4. Check for memory leaks (report as bug)

### State Machine Stuck

**Symptom**: Cannot place orders, state shows unexpected value

**Solutions**:
1. Check `data/hedge_state.json` file
2. Verify state matches reality (check exchange UI)
3. Use ERROR_LOCK unlock if appropriate
4. Manually edit state file (advanced users only)
5. Delete state file and restart (loses state)

---

## Logs & Diagnostics

### Log Files

**Location**: `data/`

- `trade_audit.log` - All trading actions
- `hedge_state.json` - Current state (persisted)

### Log Levels

- **INFO**: Normal operations
- **WARNING**: Non-critical issues (rate limits, reconnects)
- **ERROR**: Operation failures
- **CRITICAL**: Severe issues (ERROR_LOCK, KILL SWITCH)

### Enable Debug Logging

**For troubleshooting only** (verbose):

Edit source: `src/core/broker/bitunix_hedge_executor.py`
```python
logging.basicConfig(level=logging.DEBUG)
```

**Remember**: Disable after troubleshooting (high I/O)

---

## Best Practices

### Do's ✅
- Always test in TESTNET first
- Use reasonable leverage (≤10x recommended)
- Set stop losses
- Monitor positions regularly
- Keep API keys secure (environment variables only)
- Review logs after errors
- Use POST_ONLY for limit orders (better fills)
- Start with small position sizes

### Don'ts ❌
- Don't hardcode API keys
- Don't use KILL SWITCH casually
- Don't ignore ERROR_LOCK state
- Don't exceed safety limits without understanding risk
- Don't run on unstable network
- Don't disable rate limiting
- Don't modify state file unless you know what you're doing
- Don't use Flash Close unless emergency

---

## Support & Resources

### Documentation
- `/docs/ARCHITECTURE.md` - System architecture
- `/docs/testing/` - QA checklists and tests
- `/01_Projectplan/Bitunix API goLive/` - Implementation details

### Getting Help
1. Check this guide first
2. Review logs for errors
3. Search GitHub issues
4. Report bugs with:
   - Log excerpt
   - Steps to reproduce
   - Expected vs actual behavior

---

**Version**: 1.0.0
**Last Updated**: 2026-01-13
**Task**: 5.23 - User Documentation COMPLETE
