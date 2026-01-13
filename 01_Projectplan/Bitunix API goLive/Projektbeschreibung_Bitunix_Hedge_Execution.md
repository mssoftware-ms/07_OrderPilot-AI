# Projektbeschreibung: Bitunix Hedge Execution (Single-Trade) + Adaptive Limit + Trailing SL

**Start:** 2026-01-13  
**Letzte Aktualisierung:** 2026-01-13  
**Zielsystem:** Deine bestehende Tradingsoftware (Desktop, Python)  
**Integration:** Fenster **„Trading Bot“** → Tab **„Signals“** → neue **GroupBox im Header** des Tabs

---

## 1. Zielbild (was am Ende funktioniert)

Du bekommst im „Signals“-Tab ein **Order-Execution-Panel** für Bitunix Futures im **HEDGE-Mode**, das in deiner Software:

1) **Maximal genau 1 Trade gleichzeitig** zulässt (Single-Trade-Controller).  
2) **Orders platziert** und die **zurückgegebene `orderId`** sofort anzeigt (und weiterverwendet).  
3) Zwei Entry-Methoden unterstützt:

### Option A — Standard-Order (HEDGE, deterministisch)
- Du wählst **Long/Short** in der UI.
- Die Software ruft `place_order` auf und zeigt die `orderId` an.
- Optional: TP/SL schon beim Place-Order mitgeben (Bitunix unterstützt `tpPrice/slPrice` direkt im `place_order`). citeturn1view1

### Option B — Adaptive Limit Order (tickbasiert nachgezogen)
- Es wird eine LIMIT-Order platziert und **bei jedem Tick** (mit Throttling) via `modify_order` neu bepreist:
  - **Long:** `price = last_price * (1 + offset_pct)`
  - **Short:** `price = last_price * (1 - offset_pct)`
- `offset_pct` ist über **Slider + Editfeld** einstellbar (Default 0.05%).  
- `modify_order` erfordert **immer** `qty` und `price` und akzeptiert `orderId` oder `clientId`. citeturn1view2  
- Wichtige Limits/Validierung über „Get Trading Pairs“ (Min/Max-Offsets, Precision, minTradeVolume, maxLeverage…). citeturn1view0

4) Einen **Trailing Stop** in deiner Software führt und den Börsen-SL **nachzieht**:
- Pro Position wird **genau ein** Position-TP/SL-Objekt auf Bitunix angelegt. citeturn3view0  
- Der Trailing berechnet neue `slPrice` und aktualisiert über `tpsl/position/modify_order`. citeturn1view3

5) Den Order-/Positionsstatus **nicht nur per REST** bewertet, sondern per **WebSocket Push** (Order Channel):
- Bitunix weist explizit darauf hin, dass REST-Erfolg ≠ tatsächlicher Erfolg sein muss; WS-Push ist maßgeblich. citeturn1view2turn3view2

---

## 2. Kern-API-Endpunkte (Futures)

### 2.1 Mode / Risiko-Parameter
- **HEDGE aktivieren:** `POST /api/v1/futures/account/change_position_mode` (`positionMode=HEDGE`) citeturn1view5  
- **Leverage setzen:** `POST /api/v1/futures/account/change_leverage` citeturn4search0  
- (Optional) **Margin Mode setzen:** `POST /api/v1/futures/account/change_margin_mode` (Achtung: laut Doku nicht nutzbar, wenn offene Position/Order existiert) citeturn4search1  

### 2.2 Orders
- **Place Order:** `POST /api/v1/futures/trade/place_order` citeturn1view1  
- **Modify Order (preis/qty/tp/sl):** `POST /api/v1/futures/trade/modify_order` (10 req/sec/uid) citeturn1view2  
- **Cancel Orders:** `POST /api/v1/futures/trade/cancel_orders` (5 req/sec/uid) citeturn4search2  
- **Get Pending Orders:** `GET /api/v1/futures/trade/get_pending_orders` citeturn2search3  

### 2.3 Positionen
- **Get Pending Positions:** `GET /api/v1/futures/position/get_pending_positions` (liefert `positionId`, Side LONG/SHORT, leverage etc.) citeturn1view4  
- **Flash Close:** `POST /api/v1/futures/trade/flash_close_position` (Close per `positionId`) citeturn3view1  
- **Close All Position:** `POST /api/v1/futures/trade/close_all_position` (Notfall) citeturn2search1  

### 2.4 TP/SL auf Positionsebene (Trailing kompatibel)
- **Place Position TP/SL:** `POST /api/v1/futures/tpsl/position/place_order` (ein Objekt pro Position) citeturn3view0  
- **Modify Position TP/SL:** `POST /api/v1/futures/tpsl/position/modify_order` citeturn1view3  

### 2.5 Referenzdaten / Constraints
- **Trading Pair Details:** `GET /api/v1/futures/market/trading_pairs` (Precision, Offsets, minTradeVolume, maxLeverage…) citeturn1view0  

### 2.6 Status-Truth: WebSocket
- **Order Channel:** WS Push für CREATE/UPDATE/CLOSE inkl. `orderId`, `orderStatus`, TP/SL Felder etc. citeturn3view2  

---

## 3. Zustandsmodell (Single-Trade Controller)

Du brauchst eine klare State Machine, sonst entstehen „Geisterorders“ und Inkonsistenzen.

### 3.1 States
- `IDLE` (kein Trade)
- `ENTRY_PENDING` (Order platziert, wartet auf Fill/Partial)
- `POSITION_OPEN` (Position existiert; `positionId` bekannt)
- `EXIT_PENDING` (Exit-Order/Close läuft)
- `CLOSED` (Trade abgeschlossen; Reset)
- `ERROR_LOCK` (Fehlerzustand, manuelle Entsperrung)

### 3.2 Identitäten
- `clientId` (dein eigener stabiler Identifier pro Trade; optional, hilft beim Reconnect)
- `orderId` (von Bitunix zurück, wird angezeigt und als Primary Key genutzt) citeturn3view2  
- `positionId` (erst nach Fill bzw. via Pending Positions verfügbar) citeturn1view4  
- `tpslPositionOrderId` (wenn du Position-TP/SL anlegst, bekommst du `orderId`) citeturn3view0  

---

## 4. UI/UX Spezifikation (Trading Bot → Signals → GroupBox im Header)

### 4.1 GroupBox Vorschlag: „Bitunix Execution (HEDGE)“
**Linke Spalte (Konfiguration):**
- Symbol (default: BTCUSDT)
- MarginCoin (default: USDT)
- Hedge Mode Status (read-only) + Button „auf HEDGE stellen“
- Leverage (SpinBox/Slider, validiert über maxLeverage/minLeverage) citeturn1view0turn4search0  
- Order Qty (Base Coin), validiert über minTradeVolume/basePrecision citeturn1view0  

**Mittlere Spalte (Entry):**
- Richtung: Long / Short (Pflicht)
- Entry Mode:  
  - (A) Standard (Market/Limit, effect=GTC/POST_ONLY) citeturn1view1  
  - (B) Adaptive Limit (tickbasiert)
- Offset %: Slider + Editfeld (z.B. 0.01%–0.50%)  
- Update-Rate/Throttle: z.B. 250–500ms (intern, nicht UI-pflichtig)

**Rechte Spalte (TP/SL & Trailing):**
- TP optional (Trigger type MARK_PRICE default) citeturn1view1  
- SL Pflicht (für deinen Sicherheitsstandard)
- Trailing Stop: Aktiv/Deaktiv + Parameter (dein bestehender Trailing Wert)
- „Sync SL to Exchange“ (zeigt letzten gesetzten SL und Zeitpunkt)

**Footer/Statuszeile in der GroupBox:**
- `orderId`, `positionId`, `orderStatus`, letzter WS Event-Timestamp
- API Health: letzte Signatur/Nonce/Timestamp Abweichung, letzte Fehlermeldung

---

## 5. Algorithmik-Details

### 5.1 Option B: Adaptive Limit – korrekt und API-konform
**Problem:** „bei jedem Tick neu berechnen“ kann leicht Rate-Limits und unnötige Orders erzeugen.

**Lösung:** Debounce + Quantisierung + Only-If-Changed
- Debounce: max. X Updates/s (z.B. 2–4/s, nicht 20/s)
- Preis quantisieren auf `quotePrecision` aus trading_pairs citeturn1view0  
- Nur ändern, wenn neuer Preis ≠ alter Preis nach Quantisierung.
- `modify_order` immer mit `qty` + `price` senden. citeturn1view2  
- Erfolg über Order-WS bestätigen (INIT/NEW/PART_FILLED/FILLED…). citeturn3view2  

**Offset-Constraints:**
- Nutze `minBuyPriceOffset` / `maxSellPriceOffset` (falls diese als harte Grenzen gelten; du validierst dagegen). citeturn1view0  

### 5.2 Trailing Stop (clientseitig) + Börsen-SL (serverseitig)
- Position-TP/SL wird einmal angelegt: „each position can only have one Position TP/SL Order“ citeturn3view0  
- Bei jedem Trailing-Update: `tpsl/position/modify_order` setzen (nur wenn SL besser wird). citeturn1view3  
- Trigger type Default: `MARK_PRICE` (robuster) – als Default setzen. citeturn1view1turn1view3  

---

## 6. Fehlende Punkte, die du sehr wahrscheinlich sonst vergisst (und dann teuer werden)

1) **Re-connect & State-Recovery** (App-Neustart):  
   - Pending Orders + Pending Positions abfragen und Controller-Status rekonstruieren. citeturn2search3turn1view4  

2) **Partial Fills**:  
   - Adaptive Limit darf bei PART_FILLED nicht blind qty „zurück“ erhöhen. WS orderStatus beachten. citeturn3view2  

3) **Cancel/Replace Safety**:  
   - „Cancel“ per API ist wieder nur „wahrscheinlich“ erfolgreich → WS bestätigt final. citeturn4search2turn3view2  

4) **HEDGE-Modus Umschalten blockiert** bei offenen Orders/Positionen. citeturn1view5  

5) **Rate Limits**:  
   - trading_pairs 10 req/sec/ip, modify_order 10 req/sec/uid, flash_close 5 req/sec/uid etc. citeturn1view0turn1view2turn3view1  

---

## 7. Python-Request-Beispiele (als Referenz)

> Hinweis: Diese Snippets sind absichtlich „Client-unabhängig“. Du musst sie an deine bestehende Signatur-/REST-Schicht (api-key, nonce, timestamp, sign) anbinden.

### 7.1 Hedge Mode setzen
```python
client.send("POST", "/api/v1/futures/account/change_position_mode", body={"positionMode": "HEDGE"})
```
citeturn1view5  

### 7.2 Leverage setzen
```python
client.send("POST", "/api/v1/futures/account/change_leverage", body={"symbol": "BTCUSDT", "leverage": 25})
```
citeturn4search0  

### 7.3 Entry (Option A) – Long Limit mit TP/SL
```python
resp = client.send("POST", "/api/v1/futures/trade/place_order", body={
    "symbol": "BTCUSDT",
    "qty": "0.001",
    "orderType": "LIMIT",
    "price": "93000",
    "side": "BUY",
    "tradeSide": "OPEN",
    "effect": "GTC",
    "tpStopType": "MARK_PRICE",
    "tpPrice": "94000",
    "slStopType": "MARK_PRICE",
    "slPrice": "92500",
})
order_id = resp["data"]["orderId"]
```
citeturn1view1  

### 7.4 Entry (Option B) – Adaptive Limit per modify_order nachziehen
```python
client.send("POST", "/api/v1/futures/trade/modify_order", body={
    "orderId": order_id,
    "qty": "0.001",
    "price": new_price
})
```
citeturn1view2  

### 7.5 Position-SL anlegen + nachziehen (Trailing)
```python
# einmalig
tpsl = client.send("POST", "/api/v1/futures/tpsl/position/place_order", body={
    "symbol": "BTCUSDT",
    "positionId": position_id,
    "slStopType": "MARK_PRICE",
    "slPrice": "92500",
})
tpsl_order_id = tpsl["data"]["orderId"]

# später: SL nachziehen
client.send("POST", "/api/v1/futures/tpsl/position/modify_order", body={
    "symbol": "BTCUSDT",
    "positionId": position_id,
    "slStopType": "MARK_PRICE",
    "slPrice": "92850",
})
```
citeturn3view0turn1view3  

---

## 8. Definition of Done (DoD)

- HEDGE wird beim Start validiert und kann (falls möglich) gesetzt werden. citeturn1view5  
- Entry Option A + Option B funktionieren auf BTCUSDT mit Live/Paper (je nach Umgebung).  
- `orderId` wird angezeigt und in Logs persistiert. citeturn3view2  
- WS Order Channel ist angebunden und steuert State Machine. citeturn3view2  
- Trailing Stop zieht `slPrice` korrekt nach und respektiert „1 Position-TP/SL pro Position“. citeturn3view0turn1view3  
- Rate-Limit- und Reconnect-Szenarien sind getestet. citeturn1view2turn1view0  
