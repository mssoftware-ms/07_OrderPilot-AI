# ✅ Umsetzungsplan + Checkliste: Binance BTCUSDT Liquidation-Heatmap (Background)

**Ziel:** In einer bestehenden Python-Tradingsoftware eine **ein-/ausschaltbare** Liquidations-Heatmap (Background-Layer) integrieren, basierend auf **Binance USD-M Futures** Liquidation-Streams (`btcusdt@forceOrder`).  
**Persistenz:** Livestream läuft **immer** im Hintergrund und schreibt nach **SQLite**; beim Aktivieren lädt die Heatmap den gespeicherten Stand und ergänzt live.  
**Neue Dateien:** ausschließlich unter `root/Heatmap/` (Integration/Anpassungen in bestehendem Code sind erlaubt, aber **keine neuen Dateien außerhalb**).  
**Max. Dateigröße:** keine `.py` Datei > **600 Zeilen** (bei Bedarf aufteilen).

---

## 0) Technische Eckpunkte (entscheidend)

### Datenquelle (Binance)
- **WebSocket Base URL:** `wss://fstream.binance.com` citeturn0search4  
- **Stream:** `<symbol>@forceOrder` (für BTCUSDT: `btcusdt@forceOrder`) citeturn0search0  
- **Wichtig:** Pro Symbol wird **nur die letzte Liquidation innerhalb 1000ms** gepusht (Snapshot). Keine Liquidation in 1000ms ⇒ keine Message. citeturn0search0  
- **Connection-Lifetime & Ping/Pong:** Verbindung max. 24h; Server pingt periodisch, Pong muss zurückkommen. citeturn0search20  
- **TickSize/Rules:** TickSize kann sich ändern; **immer** via `GET /fapi/v1/exchangeInfo` holen. citeturn0search1turn0search24  

### Rendering (Lightweight Charts)
- Heatmap als **Custom Series** via `addCustomSeries()` (Plugin-Mechanismus). citeturn0search2turn0search10  
- TradingView stellt eine **Heatmap-Series Plugin Example** bereit (Zellen pro Zeitpunkt, Preisbereiche). citeturn0search3turn0search7  

### Deine vorhandenen Libraries (relevant)
Du hast bereits alles Nötige an Bord: `websockets`, `aiohttp`, `PyQt6`, `PyQt6-WebEngine`, `qasync`, `numpy`, `SQLAlchemy` etc. fileciteturn0file0

---

## 1) Architektur (konkret & robust)

### 1.1 Komponenten (neu unter `root/Heatmap/`)
1. **Ingestion**
   - Binance WS-Client (`btcusdt@forceOrder`)
   - Auto-Reconnect (Backoff), Ping/Pong handling
   - Event-Parsing & Validierung (Schema)

2. **Storage (SQLite)**
   - Write-optimiert (WAL + Indizes)
   - Dedup/Guard (optional): `(ts_ms, order_id?)` falls vorhanden; sonst hash auf raw payload
   - Retention (z. B. 14 Tage) + Vacuum/Pragma Pflege

3. **Aggregation (on demand + live)**
   - Beim Heatmap-ON: Query DB für Window (2h/8h/2d) → Build Grid aus Low/High
   - Live: eingehende Events inkrementell in Grid addieren (rate-limited UI updates)

4. **UI-Bridge**
   - Python → JS: `setHeatmapData(cells)` + `appendHeatmapCells(delta)`
   - Heatmap als **Background** (Heatmap-Series zuerst anlegen, Candle-Series danach)

5. **Settings**
   - Settings-Model (Opacity, Palette, Normalisierung, Decay, Detailgrad/Auto)
   - UI: neuer Tab **„Heatmap“** in Hauptfenster → Settings

### 1.2 Datenfluss
- **App-Start:** Heatmap-Service startet (auch wenn Heatmap deaktiviert) → WS connect → Events → SQLite.
- **Heatmap OFF:** Renderer aus, aber Ingestion+DB laufen.
- **Heatmap ON:**  
  a) Window = {2h|8h|2d}  
  b) Low/High aus Chartfenster (dein Wunsch)  
  c) DB Query: Events im Window → Grid bauen → an JS schicken → live deltas ergänzen

---

## 2) DB-Schema (SQLite) – Minimal aber korrekt

### Tabelle `liq_events`
- `id INTEGER PRIMARY KEY`
- `ts_ms INTEGER NOT NULL`
- `symbol TEXT NOT NULL` (z. B. `BTCUSDT`)
- `side TEXT NOT NULL` (`BUY`/`SELL` bzw. long/short liquidation – abhängig vom Payload)
- `price REAL NOT NULL`
- `qty REAL NOT NULL`
- `notional REAL NOT NULL` (= price * qty)
- `source TEXT NOT NULL` (z. B. `BINANCE_USDM`)
- `raw_json TEXT NOT NULL` (optional, aber für Debug/Replay Gold wert)

**Indizes**
- `INDEX idx_liq_events_symbol_ts (symbol, ts_ms)`
- `INDEX idx_liq_events_ts (ts_ms)`

**Pragmas (empfohlen)**
- `journal_mode=WAL` (gleichzeitig lesen+schreiben)
- `synchronous=NORMAL` (Tradeoff ok für Market-Data)
- `temp_store=MEMORY`

---

## 3) Auflösung: an Fenster gekoppelt (deine Werte)

Dein Wunsch: High/Low des Fensters als Preisbereich.  
Ziel: ~2–3 px pro Preis-Bin.

- Startfenster: **1060×550**
- Maximiert: **1780×700**

**Empfehlung (Auto)**
- `rows_target = clamp(round(height / 2.3), 180, 380)`
- `cols_target = clamp(round(width / 1.15), 800, 1700)`

**Preis-Bin**
- `range = high - low`
- `raw_bin = range / rows_target`
- `bin = ceil(raw_bin / tickSize) * tickSize` (tickSize aus `exchangeInfo`) citeturn0search1turn0search24

**Zeit-Bin**
- `time_bin = window_seconds / cols_target`
- runden auf {5, 10, 15, 30, 60, 120, 180} Sekunden

---

## 4) Dateistruktur (alle neuen Dateien nur hier)

```
root/
  Heatmap/
    README.md
    __init__.py
    heatmap_service.py          # orchestriert Start/Stop/Status (<=600)
    heatmap_settings.py         # Settings-Model + Defaults (<=600)
    ingestion/
      __init__.py
      binance_forceorder_ws.py  # WS connect/parse/reconnect (<=600)
      exchange_info.py          # tickSize fetch + caching (<=600)
    storage/
      __init__.py
      sqlite_store.py           # schema init + inserts + retention (<=600)
      schema.sql
    aggregation/
      __init__.py
      grid_builder.py           # build grid from events + low/high (<=600)
      normalization.py          # log/sqrt/linear + scaling (<=600)
      decay.py                  # optional: time decay (<=600)
    ui/
      __init__.py
      bridge.py                 # PyQt6 <-> JS API (<=600)
      js/
        heatmap_series.js       # custom series (based on plugin example)
        heatmap_palette.js
    tests/
      test_ws_parse.py
      test_sqlite_store.py
      test_grid_builder.py
```

---

## 5) UI/Settings: Heatmap-Tab im Hauptfenster

**Pflichtfelder**
- [ ] Checkbox: „Heatmap aktiv“
- [ ] Datenquelle: „Binance (BTCUSDT Liquidations)“
- [ ] Window: 2h / 8h / 2 Tage
- [ ] Opacity (0–100%)
- [ ] Palette (z. B. 3 Presets)
- [ ] Normalisierung: linear / sqrt / log
- [ ] Decay: aus / 20m / 60m / 6h
- [ ] Auflösung: Auto / Manuell (rows/cols oder px/bin)

**Technisch**
- Persistenz in `QSettings` (oder dein bestehendes Settings-System).
- Beim Toggle ON: DB-load + render, beim Toggle OFF: series entfernen/unsichtbar.

---

# ✅ CHECKLISTE (zum Abhaken)

> Format orientiert sich an deiner Vorlage. fileciteturn0file1

## 📊 Status-Legende
- ⬜ Offen / Nicht begonnen
- 🔄 In Arbeit
- ✅ Abgeschlossen
- ❌ Fehler / Blockiert
- ⭐ Übersprungen / Nicht benötigt

---

## Phase 0: Vorbereitung & Repo-Struktur

- [ ] **0.1 Ordner `root/Heatmap/` anlegen + Grundstruktur erstellen**  
  Status: ⬜ → *Ordnerstruktur gemäß Abschnitt 4, leere `__init__.py` Dateien, README Skeleton*

- [ ] **0.2 Abhängigkeiten/Runtime-Check (nur vorhandene Libs verwenden)**  
  Status: ⬜ → *websockets/qasync/PyQt6-WebEngine/numpy verfügbar* fileciteturn0file0

- [ ] **0.3 Coding-Standards festlegen (≤600 Zeilen pro Datei, Logging, Typen, Tests)**  
  Status: ⬜ → *Repo-konform dokumentiert in `Heatmap/README.md`*

---

## Phase 1: Binance Ingestion (WS)

- [ ] **1.1 WS-Client: Verbindung zu `wss://fstream.binance.com/ws/btcusdt@forceOrder`**  
  Status: ⬜ → *Connect/Disconnect, Fehlerhandling, sauberes Shutdown* citeturn0search4turn0search0

- [ ] **1.2 Parser: forceOrder Payload → internes Event-Modell**  
  Status: ⬜ → *Validierung: ts_ms, price, qty, side, raw_json* citeturn0search0

- [ ] **1.3 Reconnect-Policy + Backoff + Jitter**  
  Status: ⬜ → *robust bei Netzproblemen; keine Busy-Loops*

- [ ] **1.4 Keepalive/Ping/Pong Handling + 24h Reconnect**  
  Status: ⬜ → *automatisch neu verbinden vor 24h* citeturn0search20

- [ ] **1.5 TickSize Cache via `GET /fapi/v1/exchangeInfo`**  
  Status: ⬜ → *TickSize extrahieren, refresh (z. B. 1x/Tag oder bei Fehlern)* citeturn0search1turn0search24

---

## Phase 2: SQLite Storage

- [ ] **2.1 SQLite Schema + Migration: `liq_events` + Indizes**  
  Status: ⬜ → *schema.sql + init im Store*

- [ ] **2.2 WAL + Pragmas setzen (Write+Read parallel)**  
  Status: ⬜ → *WAL aktiviert, synchronous NORMAL*

- [ ] **2.3 Writer: Batched Inserts (Queue → DB)**  
  Status: ⬜ → *Batches (z. B. 50–200 Events) mit Flush-Timer*

- [ ] **2.4 Retention: Daten z. B. >14 Tage löschen (konfigurierbar)**  
  Status: ⬜ → *Low-maintenance housekeeping*

- [ ] **2.5 Tests: Store Insert/Query/Retention**  
  Status: ⬜ → *unit tests (unittest)*

---

## Phase 3: Aggregation (Heatmap Grid)

- [ ] **3.1 Grid-Builder: DB-Events → Cells (rows/cols)**  
  Status: ⬜ → *Mapping price→row, ts→col, intensity addieren*

- [ ] **3.2 Auto-Auflösung aus Window High/Low + Fenstergröße**  
  Status: ⬜ → *rows_target/cols_target Auto; TickSize-Rundung* citeturn0search1turn0search24

- [ ] **3.3 Normalisierung (log/sqrt/linear) + Clipping**  
  Status: ⬜ → *Background-taugliche Intensitäten*

- [ ] **3.4 Live-Inkrement: eingehende Events → delta cells**  
  Status: ⬜ → *Rate-limit (z. B. 250–1000ms)*

- [ ] **3.5 Tests: Grid-Builder deterministisch (Fixdaten)**  
  Status: ⬜ → *Mapping korrekt, keine Off-by-one Fehler*

---

## Phase 4: UI Integration (Background Layer)

- [ ] **4.1 JS Heatmap-Series integrieren (Custom Series)**  
  Status: ⬜ → *Orientierung am offiziellen Heatmap-Series Beispiel* citeturn0search3turn0search10

- [ ] **4.2 Python↔JS Bridge: setData + appendDelta**  
  Status: ⬜ → *QWebEngineView runJavaScript / WebChannel*

- [ ] **4.3 Layering: Heatmap zuerst, Candles danach (Background)**  
  Status: ⬜ → *Candles bleiben lesbar, Alpha korrekt*

- [ ] **4.4 Toggle: ON lädt DB-Stand + Live ergänzt**  
  Status: ⬜ → *keine UI-Blocker (Worker/Thread/async)*

- [ ] **4.5 Toggle: OFF entfernt/hidden Series, Streaming läuft weiter**  
  Status: ⬜ → *keine Unterbrechung DB-Writes*

---

## Phase 5: Settings Tab „Heatmap“

- [ ] **5.1 Settings-Model (Defaults + Persistenz)**  
  Status: ⬜ → *Opacity, Palette, Normalisierung, Decay, Auto/Manual Auflösung*

- [ ] **5.2 UI: neuer Tab im Hauptfenster → Controls binden**  
  Status: ⬜ → *Live Preview bei Änderungen*

- [ ] **5.3 Screen/Resize Handling: Rebuild Grid bei Größenänderung**  
  Status: ⬜ → *keine Ruckler; debounce 300ms*

---

## Phase 6: Qualität, Performance, Betrieb

- [ ] **6.1 Logging (Info/Warn/Error) + Debug-Option (raw payload speichern)**  
  Status: ⬜ → *sauber filterbar*

- [ ] **6.2 Performance-Messpunkte: DB Insert Rate, Render FPS, Build-Zeit**  
  Status: ⬜ → *Messung im Log/Statusbar*

- [ ] **6.3 Stabilität: Reconnect Torture Test (Netz weg/da)**  
  Status: ⬜ → *keine Leaks, keine Zombie-Tasks*

- [ ] **6.4 Dokumentation in `Heatmap/README.md`**  
  Status: ⬜ → *Setup, Grenzen (Snapshot!), Troubleshooting* citeturn0search0

---

## Abnahmekriterien (DoD)
- [ ] Streaming schreibt dauerhaft nach SQLite, unabhängig vom UI-Status.
- [ ] Heatmap ON lädt DB-Historie für 2h/8h/2d und rendert als Background.
- [ ] Live-Updates ergänzen ohne UI-Freeze (Rate-limited).
- [ ] Heatmap OFF entfernt Darstellung, DB-Stream läuft weiter.
- [ ] TickSize wird aus `exchangeInfo` gezogen und Preis-Bins runden korrekt. citeturn0search1turn0search24
- [ ] Stabiler WS-Betrieb (Reconnections, Ping/Pong, 24h Reconnect). citeturn0search20
