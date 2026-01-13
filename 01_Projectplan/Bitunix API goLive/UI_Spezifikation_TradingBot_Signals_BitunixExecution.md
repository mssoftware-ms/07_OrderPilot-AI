# UI-Spezifikation: Trading Bot → Tab „Signals“ → GroupBox „Bitunix Execution (HEDGE)“

**Datum:** 2026-01-13  
**Ziel:** Schnelle, sichere Order-Ausführung via Bitunix Futures API (HEDGE), Single-Trade, inkl. Adaptive Limit + Trailing-SL-Sync.

---

## 1) Platzierung & Grundlayout

**Ort:** Fenster „Trading Bot“ → Tab „Signals“ → **Header-Bereich** (oberhalb der Signal-Liste)  
**Container:** `QGroupBox("Bitunix Execution (HEDGE)")` mit 3-Spalten-Grid + Status-Footer.

Empfohlene Struktur:

- **Spalte A: Connection & Risk**
- **Spalte B: Entry (Standard / Adaptive)**
- **Spalte C: TP/SL & Trailing**
- **Footer:** Status/IDs/WS/Rate-Limit + Actions (Cancel/Close/Kill)

---

## 2) Controls (konkret, 1:1 umsetzbar)

### 2.1 Spalte A — Connection & Risk

1. **Provider Status**
   - Label: `Connected / Disconnected`
   - Sub-Label: `REST OK`, `WS OK`, `Last WS event: <ts>`

2. **Symbol**
   - ComboBox (aus Trading Pair Cache)
   - Default: `BTCUSDT`
   - Beim Wechsel: Trade-Gate nur wenn `IDLE`.

3. **MarginCoin**
   - ComboBox (Default `USDT`)

4. **Position Mode**
   - Read-only Label: `HEDGE` / `ONE_WAY`
   - Button: `Set HEDGE`
   - Disabled, wenn offene Orders/Positionen erkannt (Warntext).

5. **Leverage**
   - Slider + SpinBox (synchron)
   - Range: 1..maxLeverage (aus trading_pairs)
   - Button: `Apply Leverage`

6. **Order Qty (Base)**
   - DoubleSpinBox (Precision: basePrecision)
   - Validierung: >= minTradeVolume
   - Zusatz: Notional Preview (Label): `Notional ≈ qty * price`

7. **Risk Guards (Checkboxes)**
   - `Require SL` (Default: ON)
   - `Confirm Market / Flash Close` (Default: ON)
   - `Max Notional` (Edit + Toggle)
   - `Max Leverage` (Edit + Toggle)
   - `Price Collar` (Edit %; Default 0.30%)

---

### 2.2 Spalte B — Entry (Standard / Adaptive)

1. **Direction**
   - Radio: `Long` / `Short` (Pflicht)
   - Intern: Long → `side=BUY`, Short → `side=SELL`, `tradeSide=OPEN`

2. **Entry Mode**
   - ComboBox:
     - `Standard`
     - `Adaptive Limit (tick-follow)`

3. **OrderType (nur Standard)**
   - Radio: `LIMIT` / `MARKET`
   - LIMIT: Preisfeld aktiv
   - MARKET: Preisfeld inaktiv, Confirmation aktiv

4. **Effect (Time-in-Force) (nur LIMIT)**
   - ComboBox: `GTC` (Default), `POST_ONLY`, `IOC`, `FOK`
   - Tipp: Default `POST_ONLY` für Scalping/Execution ohne Sofort-Fill-Risiko.

5. **Price (nur Standard LIMIT)**
   - DoubleSpinBox (Precision: quotePrecision)
   - Button: `Use Last` (setzt aktuellen Tick)

6. **Adaptive Offset % (nur Adaptive)**
   - Slider + Editfeld (synchron)
   - Default: `0.05%`
   - Range: z.B. `0.01%..0.50%` (zusätzlich gegen min/max offsets validieren, falls vorhanden)
   - Anzeige: `Target Price` (berechnet und quantisiert)

7. **Adaptive Update Rate (intern)**
   - Nicht zwingend UI, aber empfehlenswert als Advanced-Setting:
   - Default: 250–500ms Debounce
   - Max: 2–4 `modify_order`/s

8. **Actions**
   - Button: `ARM` (setzt „armed“ für 3 Sekunden)
   - Button: `SEND` (nur wenn ARMed + alle Validierungen ok)
   - Button: `Cancel Pending` (nur wenn Entry-Pending)

---

### 2.3 Spalte C — TP/SL & Trailing

1. **TP Enable**
   - Checkbox + Preisfeld
   - Trigger Type: Combo `MARK_PRICE` (Default) / `LAST_PRICE`

2. **SL Enable (Pflicht-Default)**
   - Checkbox + Preisfeld
   - Trigger Type: Combo `MARK_PRICE` (Default) / `LAST_PRICE`
   - Button: `Sync SL to Exchange (Now)`

3. **Trailing Stop**
   - Checkbox: `Use Trailing Stop`
   - Parameter-Anzeige: „Trailing: <dein interner Wert>“
   - Info-Label: `Last SL pushed: <ts>`

4. **Exit Controls**
   - Button: `Close Position (Market)` (CLOSE-Order)
   - Button: `Flash Close` (Notfall)
   - Checkbox: `Require Confirm`

---

### 2.4 Footer — Status/IDs/WS/Rate-Limit

- `State:` IDLE / ENTRY_PENDING / POSITION_OPEN / EXIT_PENDING / ERROR_LOCK
- `orderId:` (copy button)
- `positionId:` (copy button)
- `tpslPositionOrderId:` (optional)
- `Last REST:` ok/err + code
- `RateLimit:` modify calls/min, 429 count
- `Kill Switch:` Button „STOP ALL (Cancel + Disable Adaptive)“

---

## 3) Interaktionsabläufe (deterministisch)

### 3.1 Startup / Recovery (App-Start oder Tab-Open)
1) Lade Trading Pairs → Precision/MinQty/MaxLeverage.  
2) Lade Pending Orders + Pending Positions.
3) Wenn etwas offen ist: Controller auf passenden State setzen und IDs in UI anzeigen.
4) Starte WS und subscribe Order Channel; WS ist „Source of Truth“.

### 3.2 Entry Standard (Market/Limit)
1) User setzt Long/Short, qty, ggf. price/effect, TP/SL.
2) Klick `ARM` → UI zeigt Countdown (3s).
3) Klick `SEND`:
   - Validierung (minQty, Precision, Price Collar, MaxNotional, SL Pflicht, Hedge Mode).
   - `place_order` → orderId speichern/anzeigen.
   - State → ENTRY_PENDING.
4) WS meldet NEW/PART_FILLED/FILLED.
5) Bei FILLED:
   - Hol `positionId` via pending_positions oder WS payload.
   - Lege Position-TP/SL an (oder nutze TP/SL im place_order).
   - State → POSITION_OPEN.

### 3.3 Entry Adaptive Limit (tick-follow)
1) User setzt Long/Short, qty, offset%.
2) Klick `ARM` + `SEND`:
   - Berechne initialen Target-Preis:  
     - Long: last*(1+offset)  
     - Short: last*(1-offset)
   - Quantisieren auf quotePrecision.
   - `place_order` LIMIT + effect (Default POST_ONLY oder GTC).
   - orderId anzeigen; State ENTRY_PENDING.
3) Tick-Loop:
   - Debounce (z.B. 250–500ms).
   - Only-If-Changed nach Quantisierung.
   - `modify_order(orderId, qty, new_price)`.
4) Stop conditions:
   - WS FILLED → stop modify loop, Position öffnen.
   - WS CANCELED/REJECTED → stop loop, ERROR oder IDLE.

### 3.4 Trailing Stop → Exchange SL Sync
1) In POSITION_OPEN läuft dein Trailing wie bisher.
2) Bei neuem SL:
   - Nur senden, wenn „besser“ (Long: SL höher; Short: SL niedriger).
   - Debounce (<=2/s).
   - `tpsl/position/modify_order(symbol, positionId, slPrice, slStopType)`.
3) UI zeigt „Last SL pushed“.

### 3.5 Exit
- „Close Position“: kontrollierter Exit (CLOSE-Order) mit Confirmation.
- „Flash Close“: Notfall; Confirmation + extra Warntext; danach Cleanup.

---

## 4) Defaults (empfohlen)

- Mode: HEDGE (pflicht)
- Entry: Standard LIMIT + `POST_ONLY`
- Offset: 0.05%
- SL: Pflicht ON, StopType `MARK_PRICE`
- TP: optional OFF
- Confirm: Market + Flash Close ON
- Throttle: Adaptive modify 2–4/s, SL modify 1–2/s

---

## 5) Hotkeys (optional, aber sehr sinnvoll)

- `Ctrl+L` = Arm + Send Long (nur wenn Fokus im Panel)
- `Ctrl+S` = Arm + Send Short
- `Esc` = Cancel Pending / Stop Adaptive
- `Ctrl+Shift+X` = Flash Close (immer Confirmation)

---

## 6) Validierungsregeln (nicht verhandelbar)

- Long/Short muss gesetzt sein.
- qty ≥ minTradeVolume und auf basePrecision gerundet.
- price auf quotePrecision gerundet.
- Price Collar: Preis darf nicht > X% vom lastPrice abweichen (Default 0.30%).
- Single-Trade: kein zweiter Entry wenn State != IDLE.
- WS down → kein SEND (oder nur mit „I understand“-Override).

---

## 7) Logging / Audit

- Jede Aktion mit Korrelation: clientId, orderId, positionId
- Persist: letzter State + IDs für Recovery.
- Metriken: modify_order count/min, 429 count, WS reconnects.

