# Analyse 2: Umsetzung auf Bitunix in deiner eigenen Trading-Software (API‑fähig, Tick‑basiert)

> Ziel: Das im Transkript beschriebene System so übersetzen, dass du es **mit Bitunix‑Daten + eigener Software** sauber implementieren kannst.
> Keine „Trading‑Empfehlung“, sondern technische Regel-/Daten-/Tool‑Umsetzung.

---

## 0) Ausgangslage (dein Setup)
- Du hast eine eigene Trading-Software.
- Bitunix liefert dir Ticks (ca. 1 Hz) und Volumen.
- Du kannst Kerzen bis 1s bauen (oder direkt 1s‑Bars in deiner App berechnen).
- Unklar ist aktuell: **Welche Marktdaten liefert Bitunix zusätzlich** (Trades/Tape, Orderbuch-Depth, Funding/Mark/Index etc.).

Wichtig: Für den Eugen‑Ansatz brauchst du **nicht nur 1s‑OHLCV**, sondern **Trades + Orderbuch** (Orderflow).

---

## 1) Minimum-Datenanforderungen für „Eugen‑Style“
Wenn du *wirklich* Heatmap/Absorption/CVD machen willst, brauchst du:

### 1.1 Trade‑Prints (Time & Sales)
Pro Trade idealerweise:
- timestamp (ms)
- price
- size/amount
- side (aggressiver Käufer vs. aggressiver Verkäufer)

**Warum:** Daraus baust du
- CVD (kumulatives Delta)
- Volume‑at‑Price (Profil)
- Tickbars/Volumenbars
- „Aggressor Flip“ (Step 3 der Ablehnung)

> Wenn Bitunix dir nur 1‑Sekunden‑Ticker ohne Trade‑Stream liefert, fehlt dir CVD/Orderflow‑Kern.

### 1.2 Orderbuch‑Depth (Level 2)
Idealerweise:
- mehrere Preislevel (Top N bids/asks)
- möglichst frequent updates (diffs oder snapshots)

**Warum:** Daraus baust du
- Heatmap (Liquidity over Time)
- Liquidity walls / Pulls / Adds
- Absorption (Preis hält trotz aggressiver Trades, weil passives Buch „steht“)

---

## 2) Was du aus deinen vorhandenen 1s‑Kerzen trotzdem schon nutzen kannst
Auch ohne volles Orderflow kann dein System schon:
- Price Action Struktur (HH/HL, LH/LL)
- Volumen-Spikes, Range/Volatilität
- robuste Risk‑Engine (Positionsgröße, SL/TP, max loss/day)
- Setup‑Klassifikation (Breakout / Rejection / Continuation) – aber ohne Orderflow wird es „weicher“

Realistisch: **Ohne Trades+Depth ist es nicht Eugens Methode**, sondern eine abgespeckte Price‑Action/Volumen‑Variante.

---

## 3) Wie du aus Bitunix-Daten exakt die benötigten „Eugen‑Features“ baust

### 3.1 Bar‑Builder (dein Vorteil: du hast Tick‑basierte Architektur)
Du kannst parallel mehrere Bar‑Typen generieren:

1) **1s‑Bars (zeitbasiert)**
- gut als „Debug/Live‑Baseline“

2) **Tickbars (Eugen‑Style)**
- Bar schließt nach N Trades (z. B. 900 Trades)
- Vorteil: Marktaktivität bestimmt die Granularität

3) **Volumenbars**
- Bar schließt nach X gehandelte Menge
- Vorteil: stabil bei unterschiedlichen Volatilitätsphasen

4) Optional **Rangebars**
- Bar schließt nach X Preisbewegung
- Vorteil: reduziert Seitwärtsrauschen

Empfehlung: Für Orderflow‑Logik nutze Tick- oder Volumenbars als Primär-Execution‑Chart.

---

### 3.2 CVD (kumulatives Delta) aus Trade‑Prints
Definition:
- pro Trade: +size bei aggressiven Buys, −size bei aggressiven Sells
- CVD(t) = Summe über Zeitfenster (oder kontinuierlich)

Abgeleitete Signale:
- **Delta Divergence**: Preis macht neues Low, CVD nicht → Absorption/Exhaustion möglich
- **Aggressor Flip**: CVD dreht nach längerer Dominanz

---

### 3.3 Volume Profile (D/W/M) aus Trades
Du baust **Volume‑at‑Price**:
- bucketize price (Ticksize oder Preisraster)
- summiere Volumen je Preisbucket über Session

Outputs:
- **POC** (max volume bucket)
- Value Area (z. B. 70% Volumen)
- **HVN** (High Volume Nodes), **LVN** (Low Volume Zones)

Das ist die Basis für:
- „Spielfeld/Zielzonen“ (Eugen)
- Acceptance vs. Rejection

---

### 3.4 Heatmap (Liquidity over Time) aus Depth
Du speicherst über Zeit:
- Preislevel → verfügbare bid/ask size

Daraus:
- Heatmap-Rendering (Zeitachse vs Preis vs Size)
- Events:
  - **Add** (Liquidity steigt)
  - **Pull** (Liquidity fällt)
  - **Sweep** (Level wird gehandelt/„weggefressen“)

---

### 3.5 Absorption‑Detektor (seine „Step‑1“-Komponente)
Ein robuster technischer Ansatz:

**Absorption Long‑Zone (Beispiel):**
- Preis fällt in Zone (aus Volume Profile / struktur)
- aggressives Sell‑Volumen steigt (Trade‑Prints)
- CVD fällt weiter
- Preis macht aber kein neues Low oder hält in kleinem Band
- gleichzeitig zeigt Depth/Heatmap: bid‑Liquidity steht/bleibt (oder wird nachgelegt)

Score/Trigger:
- AbsorptionScore = f(DeltaNegativität, Preis-Stagnation, Bid-Liquidity‑Persistenz)

---

## 4) Umsetzung seiner 3 Setup‑Klassen als harte Regeln (ohne „magische“ Indikatoren)

### 4.1 Breakout
Voraussetzungen:
- Bias (BU) ist in Richtung Breakout
- Breakout über Zone (z. B. Value Area High / LVN‑Rand)

Orderflow‑Bestätigung:
- Liquidity wird gesweept (Heatmap)
- danach Acceptance: Volumen baut sich über dem Level auf (Volume‑at‑Price)
- CVD unterstützt die Richtung oder zumindest kein starker Gegenimpuls

Stop/Exit:
- SL hinter dem Level (oder hinter nächster Liquidity‑Wall)
- Zielzone = nächster HVN/POC

---

### 4.2 Rejection (Ablehnung) = sein Parade‑Setup
Harte 3‑Step‑Regel (für Long‑Rejection):
1) Absorption: CVD ↓, Preis hält, bid‑Liquidity persistent
2) Druck lässt nach: Sell‑Aggression sinkt, weniger negative Delta‑Impulse
3) Aktive Käufer übernehmen: CVD dreht ↑, Preis löst aus

Entry:
- nach Step 3 (nicht früher)

SL:
- unterhalb Absorptionszone / unterhalb letzter Liquidity‑Wand

Ziel:
- POC/HVN oder nächste definierte Zone aus Profil

---

### 4.3 Trendfolge / Continuation
Kontext:
- klarer Bias in Trendrichtung
- Pullback in Zone (z. B. HVN‑Rand oder Strukturlevel)

Bestätigung:
- Pullback wird absorbiert (wie oben, aber „kleiner“)
- dann erneuter Aggressor‑Schub in Trendrichtung

---

## 5) Bias („BU“) als implementierbarer Score
Du brauchst eine maschinenlesbare BU‑Definition. Beispiel (Score‑Modell):

### Inputs (Beispiele)
- Distanz zu POC / HVNs / LVNs (D/W/M)
- Struktur (HH/HL vs LH/LL)
- CVD Trend (steigend/fallend), Divergenzen
- Liquidity Asymmetrie (bid vs ask) nahe Key‑Levels
- Volatilität/Regime (Range vs Trend)

### Output
- BU.direction ∈ {LONG, SHORT, NEUTRAL}
- BU.confidence ∈ [0..100]
- BU.target_zones = [Z1, Z2, Z3]

Praxis:
- ab z. B. confidence ≥ 70: nur Trades in BU‑Richtung erlauben

---

## 6) Risk‑Engine: Der Teil, der am Ende „entscheidet“
Wenn du Eugens Aussagen ernst nimmst, implementierst du harte Limits:

### 6.1 „10 Losses survivable“-Regel
- MaxRiskPerTrade so wählen, dass 10 aufeinanderfolgende SL nicht „Game Over“ sind.
- Beispiel als Technik (nicht als Empfehlung): MaxRiskPerTrade ≤ 1% ⇒ 10 SL ≈ −10% (vereinfacht, ohne Slippage).

### 6.2 Tages-/Wochengrenzen
- MaxDailyLoss
- Stop‑Trading nach N Verlusttrades oder nach Drawdown‑Grenze
- Cooldown‑Timer (gegen Revenge Trades)

### 6.3 Positionsaufbau (Add‑to‑Winner) technisch sauber
- Erlaube Adds nur wenn:
  - unrealized PnL > Schwelle
  - Stop bereits in Richtung BE/Profit gezogen
  - zusätzlicher Add riskiert nicht mehr als definierte Add‑Budget‑Tranche

Wichtig:
- Kein Average Down (keine Adds im Minus)

---

## 7) Hedging/„Freeze“ auf Bitunix (wenn Hedge‑Mode vorhanden)
Eugen friert im Swing PnL ein. Das kannst du konzeptionell abbilden:

### „Freeze“-Mechanik
- Du hast eine Position (z. B. Long).
- Wenn Markt gegen dich läuft und du die These nicht verwerfen willst:
  - eröffne Gegenposition (Short) in Hedge‑Mode
- Ziel: Netto‑Delta reduzieren / PnL stabilisieren

### „Handbremse lösen“
- Wenn Kontext wieder pro Long ist:
  - schließe die Hedge‑Komponente stückweise
  - lasse ursprüngliche Position weiterlaufen

Achtung:
- Das ist fortgeschritten: Fees/Funding/Slippage können den „Freeze“ teuer machen.
- Du brauchst sehr klare Regeln, wann Freeze erlaubt ist (z. B. nur im Swing‑Modus, nicht im Intraday‑Scalp).

---

## 8) Was du von Bitunix API/WS konkret „prüfen“ solltest (Checkliste)
Du hast Zugang – also prüfe gezielt, ob du Folgendes bekommst:

### Public Market Data
- Trade‑Stream (Time & Sales) mit side
- Orderbook‑Depth (N Levels), Snapshot + Diffs
- Funding/Mark/Index Price (für Perps)
- Rate limits / Latenz / Reconnect‑Verhalten

### Trading/Account
- Hedge‑Mode vs One‑Way Mode
- reduceOnly / closePosition / TP/SL‑Orders (order‑seitig oder positions‑seitig)
- Order‑Status/Fill‑Events (am besten via WS)
- Positions‑Endpoint (avg entry, size, unrealized pnl)

Wenn dir ein Punkt fehlt:
- baue Workarounds (z. B. CVD ohne side ist unzuverlässig)
- oder ändere die Strategiekomponente (z. B. Absorption nur über Preis/Volumen wäre deutlich schwächer)

---

## 9) Architektur-Blueprint für deine Software (modular, wartbar)

### 9.1 Module
1) **ingestion/**
   - bitunix_ws_client.py (trades/depth/mark)
   - bitunix_rest_client.py (fallback snapshots)
   - reconnect + backoff + heartbeat

2) **marketdata/**
   - trade_store (append-only, ringbuffer + persist)
   - orderbook_state (in‑memory book + time snapshots)
   - bar_builder (1s/tick/vol/range)
   - session_manager (D/W/M Fenster)

3) **orderflow/**
   - cvd.py
   - volume_profile.py
   - heatmap_model.py
   - absorption_detector.py

4) **strategy/**
   - bias_engine.py (BU score)
   - setups.py (breakout/rejection/continuation)
   - signal_router.py (nur trades in BU‑Richtung)

5) **risk/**
   - position_sizing.py
   - daily_limits.py
   - pyramiding.py (add‑to‑winner rules)
   - hedge_manager.py (optional)

6) **execution/**
   - order_manager.py (place/modify/cancel)
   - tp_sl_manager.py
   - fill_reconciler.py (WS fills vs REST history)

7) **ui/**
   - charts (1s vs tickbars)
   - overlays (POC/HVN/LVN, CVD panel, Heatmap)
   - replay mode (Session Review)

### 9.2 Replay/Review (entscheidend)
Eugen sagt sinngemäß: Sessions aufnehmen, auswerten, Backtesting.
=> Du brauchst:
- „Market Replay“ aus gespeicherten Trades+Depth
- event‑basierte Reproduktion (damit du Absorption/Heatmap visuell überprüfen kannst)

---

## 10) Konkreter nächster Schritt (ohne Umwege)
Da du schon 1s‑Ticks bekommst, ist der nächste sinnvolle technische Schritt:

1) **Ermittle, ob Bitunix dir Trade‑Prints mit side liefert.**
2) **Ermittle, ob du Depth‑Daten in ausreichender Tiefe/Frequenz bekommst.**
3) Wenn ja: implementiere zuerst **CVD + Daily Volume Profile + simple Heatmap**.
4) Danach: implementiere **Rejection‑3‑Step** als erstes „echtes“ Setup.
5) Erst danach: Positionsaufbau/Add‑to‑Winner und Hedge‑Freeze (weil diese Teile ohne saubere Signale gefährlich werden).

---

## 11) Ergebnis: Was du dann wirklich hast
Wenn du Trades + Depth zuverlässig bekommst und die vier Kernmodule (CVD, Volume Profile, Heatmap, Absorption) implementierst, kannst du den Eugen‑Ansatz **auf Bitunix** sehr nah nachbauen – ohne externe Tools.

Wenn du diese Daten **nicht** bekommst, bleibt dir:
- Price Action + klassisches Volumen + Risk (immer noch brauchbar)
- aber nicht der im Transkript beschriebene Orderflow‑Vorteil.

