# Final Manual QA Checklist - Bitunix HEDGE Execution

**Task 5.22**: Final manual QA before production release

**Date**: _________________
**Tester**: _________________
**Environment**: TESTNET / MAINNET (circle one)

---

## Phase 0: Setup & Configuration

### Environment Setup
- [ ] Windows system environment variables verified
  - [ ] `BITUNIX_API_KEY` set
  - [ ] `BITUNIX_API_SECRET` set
  - [ ] `BITUNIX_USE_TESTNET=true` for testnet
- [ ] Application launches without errors
- [ ] Logs directory created (`data/`)
- [ ] State file writable (`data/hedge_state.json`)

### UI Initialization
- [ ] Bitunix HEDGE Execution widget visible
- [ ] All UI controls enabled/disabled correctly
- [ ] Default values loaded from QSettings
- [ ] Symbol dropdown populated
- [ ] Mode label shows "—" initially

---

## Phase 1: Connection & Setup

### 1.1 Connect to Bitunix
- [ ] Click "Connect" button
- [ ] Status changes to "Connected" (green)
- [ ] WebSocket connection established
- [ ] No errors in logs

### 1.2 Set HEDGE Mode
- [ ] Click "Set HEDGE" button
- [ ] Mode label changes to "HEDGE" (green)
- [ ] Confirmation in logs
- [ ] No API errors

### 1.3 Apply Leverage
- [ ] Set leverage (e.g., 5x)
- [ ] Click "Apply Leverage"
- [ ] Success message displayed
- [ ] Leverage confirmed in logs

### 1.4 Trading Pair Limits
- [ ] Select symbol "BTCUSDT"
- [ ] Limits label updates automatically
- [ ] Shows: "Min: 0.001, Prec: 0.001/0.1, Lev: 1-125x"
- [ ] Quantity spinbox minimum updated

---

## Phase 2: Entry (Adaptive Limit)

### 2.1 Configure Entry
- [ ] Select side: LONG / SHORT
- [ ] Set quantity (e.g., 0.001)
- [ ] Set offset (e.g., 0.05%)
- [ ] Verify offset slider/spinbox sync

### 2.2 ARM & SEND Order
- [ ] Click "ARM (3s)"
- [ ] SEND button enables
- [ ] Wait 3 seconds
- [ ] SEND button disables (timeout test)
- [ ] Click ARM again
- [ ] Click SEND within 3 seconds
- [ ] Order placed successfully

### 2.3 Verify Order State
- [ ] State changes to "ENTRY_PENDING" (orange)
- [ ] Order ID displayed in footer
- [ ] Cancel button enabled
- [ ] Adaptive price display starts updating

### 2.4 Adaptive Limit Tracking
- [ ] Adaptive price updates every ~500ms
- [ ] Price shows format: "93046.5 @ 14:32:15"
- [ ] Modify calls logged (check logs)
- [ ] Rate limited to ~4/s (check logs)

### 2.5 Cancel Order (Optional)
- [ ] Click "Cancel" button
- [ ] Confirmation dialog appears
- [ ] Confirm cancellation
- [ ] State returns to "IDLE"
- [ ] Order ID clears

---

## Phase 3: Position Open

### 3.1 Wait for Fill
- [ ] Let order fill naturally OR
- [ ] Force fill via exchange UI (testnet)
- [ ] State changes to "POSITION_OPEN" (green)
- [ ] Position ID displayed
- [ ] Adaptive tracking stops

### 3.2 TP/SL Order
- [ ] TP/SL order placed automatically (if configured)
- [ ] TPSL Order ID stored
- [ ] Exchange SL display updates
- [ ] Shows format: "Exchange SL: 91500.0 @ 14:35:20"

### 3.3 Trailing Stop (If Enabled)
- [ ] Enable "Use Trailing Stop" checkbox
- [ ] Trailing stop starts
- [ ] Exchange SL updates as market moves
- [ ] LONG: SL only moves UP
- [ ] SHORT: SL only moves DOWN
- [ ] Debounced to ~2/s (check logs)

---

## Phase 4: Exit Flow

### 4.1 Flash Close
- [ ] Click "Flash Close" button
- [ ] Warning dialog appears (double confirmation)
- [ ] Confirm flash close
- [ ] Position closed at market
- [ ] State transitions to "CLOSED"
- [ ] UI resets

### 4.2 Normal Close (Alternative)
- [ ] Click "Close Position" button
- [ ] Close order placed
- [ ] State transitions to "EXIT_PENDING"
- [ ] After fill: State → "CLOSED"

---

## Phase 5: Error Handling & Recovery

### 5.1 ERROR_LOCK State
- [ ] Trigger error (e.g., invalid API call)
- [ ] State changes to "ERROR_LOCK" (red)
- [ ] Unlock button becomes visible
- [ ] Click "Unlock ERROR_LOCK"
- [ ] Warning dialog shown
- [ ] Confirm unlock
- [ ] State returns to "IDLE"

### 5.2 Rate Limit Handling
- [ ] Spam modify_order (rapid offset changes)
- [ ] Verify throttling (4/s max)
- [ ] No 429 errors in logs
- [ ] Backoff works if 429 occurs

### 5.3 WebSocket Reconnection
- [ ] Disconnect network briefly
- [ ] Verify auto-reconnect
- [ ] Connection restored
- [ ] Order events still received

---

## Phase 6: Kill Switch & Emergency

### 6.1 Stop Adaptive
- [ ] While adaptive running
- [ ] Click "Stop Adaptive"
- [ ] Confirmation dialog
- [ ] Confirm stop
- [ ] Adaptive stops
- [ ] Order remains at last price

### 6.2 KILL SWITCH
- [ ] Click "KILL SWITCH" button
- [ ] Triple confirmation dialogs:
  1. Initial warning
  2. Type symbol to confirm
  3. Final warning
- [ ] Complete all confirmations
- [ ] All positions closed
- [ ] State resets
- [ ] Success message shown

---

## Phase 7: Persistence & Restart

### 7.1 Save State
- [ ] Place order (ENTRY_PENDING state)
- [ ] Note order ID
- [ ] Close application
- [ ] Check `data/hedge_state.json` exists
- [ ] Verify order_id in JSON

### 7.2 Restore State
- [ ] Relaunch application
- [ ] Connect
- [ ] State restored to ENTRY_PENDING
- [ ] Order ID matches
- [ ] Can resume or cancel

### 7.3 QSettings Persistence
- [ ] Set custom values (symbol, leverage, offset, qty)
- [ ] Close application
- [ ] Relaunch
- [ ] Verify values restored

---

## Phase 8: Safety Limits

### 8.1 Max Notional Check
- [ ] Try to place order > $10k notional
- [ ] Order rejected with clear message
- [ ] No order sent to exchange

### 8.2 Max Leverage Check
- [ ] Try to set leverage > 20x
- [ ] Rejected with clear message
- [ ] Leverage not applied

### 8.3 Max Position Size
- [ ] Try to place order > 1.0 BTC
- [ ] Order rejected
- [ ] Clear error message

---

## Test Results

### Overall Status
- [ ] ✅ ALL TESTS PASSED
- [ ] ⚠️ SOME TESTS FAILED (document below)
- [ ] ❌ CRITICAL FAILURES (do not release)

### Failed Tests
Test ID | Description | Severity | Notes
--------|-------------|----------|-------
        |             |          |
        |             |          |
        |             |          |

### Sign-Off
- [ ] Tested by: _________________
- [ ] Date: _________________
- [ ] Approved for release: YES / NO
- [ ] Signature: _________________

---

**Notes**:
_______________________________________________________________
_______________________________________________________________
_______________________________________________________________

---

**Task 5.22**: COMPLETE
**Next**: Task 5.23 - Documentation
