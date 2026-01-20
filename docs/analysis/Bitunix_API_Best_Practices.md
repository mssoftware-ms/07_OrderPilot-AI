# Bitunix API Best Practices für Gap-Filling & Incremental Updates
**Datum:** 2026-01-20
**Quelle:** Web Research + Existing Code Analysis

---

## 1. Bitunix API Übersicht

### REST API (Historical Data)

**Endpoint:**
```
GET https://fapi.bitunix.com/api/v1/futures/market/kline
```

**Parameter:**
- `symbol`: Trading-Symbol (z.B. "BTCUSDT", "ETHUSDT")
- `interval`: Timeframe-String ("1m", "5m", "15m", "1h", "4h", "1d")
- `startTime`: Start-Timestamp in Millisekunden
- `endTime`: End-Timestamp in Millisekunden
- `limit`: Max. Anzahl Kerzen pro Request (max: 200)

**Rate Limit:**
- **10 Requests/Sekunde pro IP**
- Implementiert mit 0.15s Delay (safety margin)

**Response Format:**
```json
{
  "code": 0,
  "message": "success",
  "data": [
    {
      "time": 1609459200000,
      "open": "29000.0",
      "high": "29500.0",
      "low": "28800.0",
      "close": "29300.0",
      "baseVol": "123.45",
      "quoteVol": "3600000.0"
    }
  ]
}
```

**Wichtig:** Daten werden in **DESCENDING Order** (neueste zuerst) zurückgegeben!

### WebSocket API (Live Updates)

**Endpoint:**
```
wss://fapi.bitunix.com/api/v1/futures/market/ws
```

**Features:**
- Push-Intervall: **500ms**
- Initial Snapshot + fortlaufende Updates
- Empfohlen für Real-time Daten

**Channel:**
```json
{
  "method": "subscribe",
  "params": {
    "channel": "kline",
    "symbol": "BTCUSDT",
    "interval": "1m"
  }
}
```

---

## 2. Gap-Filling Strategy (Best Practice)

### Problem: Datenlücken durch verschiedene Szenarien

| Szenario | Datenlücke | Strategie |
|----------|-----------|-----------|
| **App 5 Min geschlossen** | 5 Kerzen (bei 1min) | ✅ WebSocket-Reconnect ausreichend |
| **Rechner 1 Tag aus** | 1,440 Kerzen (bei 1min) | ⚠️ REST API Gap-Fill (7 Requests @ 200/req) |
| **Rechner 1 Woche aus** | 10,080 Kerzen (bei 1min) | ⚠️ REST API Gap-Fill (51 Requests) |
| **Komplett neue Datenbank** | Unbegrenzt | ✅ Full Historical Download |

### Best Practice: Hybrid-Approach

```
┌─────────────────────────────────────────────────────────┐
│  WebSocket (Live)                                       │
│  ↓ Neue Kerzen alle 500ms                               │
│  ↓ Automatisch in Pattern-DB einfügen                   │
└─────────────────────────────────────────────────────────┘
           │
           │ (Verbindung unterbrochen)
           ▼
┌─────────────────────────────────────────────────────────┐
│  Gap Detection                                          │
│  ↓ Prüfe letzte Kerze in DB vs. aktuelle Zeit           │
│  ↓ Berechne Datenlücke in Kerzen                        │
└─────────────────────────────────────────────────────────┘
           │
           │ (Lücke > 10 Kerzen)
           ▼
┌─────────────────────────────────────────────────────────┐
│  REST API Gap-Fill                                      │
│  ↓ Lade fehlende Daten in 200-Kerzen-Batches            │
│  ↓ Respektiere Rate-Limit (10 req/s)                    │
│  ↓ Füge Patterns in Qdrant ein                          │
└─────────────────────────────────────────────────────────┘
```

---

## 3. Gap Detection Algorithmus

### Pseudo-Code

```python
async def detect_gaps(symbol: str, timeframe: str) -> list[tuple[datetime, datetime]]:
    """
    Findet Datenlücken in der Pattern-DB.

    Returns:
        Liste von (start_gap, end_gap) Tupeln
    """
    # 1. Lade letzte Pattern-Timestamps aus Qdrant
    db = TradingPatternDB()
    await db.initialize()

    # Qdrant-Query: Alle Patterns für Symbol + Timeframe, sortiert nach Timestamp
    patterns = await db.search_patterns(
        symbol=symbol,
        timeframe=timeframe,
        sort_by="start_time",
        limit=10000  # Alle Patterns
    )

    if not patterns:
        # Keine Daten vorhanden → Full Historical Download
        now = datetime.now(timezone.utc)
        one_year_ago = now - timedelta(days=365)
        return [(one_year_ago, now)]

    # 2. Sortiere Patterns nach Timestamp
    sorted_timestamps = sorted([p.start_time for p in patterns])

    # 3. Finde Lücken (z.B. > 2x Timeframe-Intervall)
    interval_minutes = _timeframe_to_minutes(timeframe)
    max_gap_minutes = interval_minutes * 2  # 2x Intervall = Lücke

    gaps = []
    for i in range(len(sorted_timestamps) - 1):
        current = sorted_timestamps[i]
        next_timestamp = sorted_timestamps[i + 1]
        gap_minutes = (next_timestamp - current).total_seconds() / 60

        if gap_minutes > max_gap_minutes:
            gap_start = current + timedelta(minutes=interval_minutes)
            gap_end = next_timestamp
            gaps.append((gap_start, gap_end))

    # 4. Prüfe Lücke vom neuesten Pattern bis jetzt
    latest_pattern = sorted_timestamps[-1]
    now = datetime.now(timezone.utc)
    time_since_latest = (now - latest_pattern).total_seconds() / 60

    if time_since_latest > max_gap_minutes:
        gap_start = latest_pattern + timedelta(minutes=interval_minutes)
        gaps.append((gap_start, now))

    return gaps


def _timeframe_to_minutes(timeframe: str) -> int:
    """Convert timeframe string to minutes."""
    mapping = {
        "1m": 1,
        "5m": 5,
        "10m": 10,
        "15m": 15,
        "30m": 30,
        "1h": 60,
        "4h": 240,
        "1d": 1440
    }
    return mapping.get(timeframe, 1)
```

### Performance-Optimierung

**Problem:** 10,000+ Patterns aus Qdrant laden ist langsam.

**Lösung:** Metadaten-basierte Suche
```python
# Statt alle Patterns zu laden, nur Metadaten abfragen
async def get_latest_pattern_timestamp(symbol: str, timeframe: str) -> datetime | None:
    """Schnelle Abfrage: Neuestes Pattern-Timestamp."""
    # Qdrant Scroll API mit limit=1, sortiert nach start_time DESC
    result = await db.scroll(
        collection_name="trading_patterns",
        scroll_filter={
            "must": [
                {"key": "symbol", "match": {"value": symbol}},
                {"key": "timeframe", "match": {"value": timeframe}}
            ]
        },
        order_by={"key": "start_time", "direction": "desc"},
        limit=1
    )

    if result.points:
        return datetime.fromisoformat(result.points[0].payload["start_time"])
    return None
```

---

## 4. Incremental Update Strategy

### Batch-Size-Berechnung

**Ziel:** Minimiere Requests, maximiere Effizienz

```python
def calculate_optimal_batch_size(gap_minutes: int, interval_minutes: int) -> int:
    """
    Berechnet optimale Batch-Size für Gap-Filling.

    Args:
        gap_minutes: Größe der Datenlücke in Minuten
        interval_minutes: Kerzen-Intervall in Minuten

    Returns:
        Anzahl Kerzen pro Request (max 200)
    """
    total_candles = gap_minutes / interval_minutes

    if total_candles <= 200:
        # Kleine Lücke: 1 Request reicht
        return int(total_candles)
    else:
        # Große Lücke: Verwende max. 200 pro Request
        return 200


async def fill_gap(symbol: str, timeframe: str, gap_start: datetime, gap_end: datetime):
    """
    Füllt eine Datenlücke mit Bitunix API.

    Args:
        symbol: Trading-Symbol
        timeframe: Kerzen-Intervall
        gap_start: Start der Lücke
        gap_end: Ende der Lücke
    """
    provider = BitunixProvider()
    extractor = PatternExtractor(window_size=20, step_size=5, outcome_bars=5)
    db = TradingPatternDB()
    await db.initialize()

    # 1. Lade fehlende Bars
    bars = await provider.fetch_bars(
        symbol=symbol,
        start_date=gap_start,
        end_date=gap_end,
        timeframe=Timeframe.from_string(timeframe)
    )

    if not bars:
        logger.warning(f"No bars fetched for gap: {gap_start} → {gap_end}")
        return

    # 2. Extrahiere Patterns
    patterns = list(extractor.extract_patterns(bars, symbol, timeframe))

    # 3. Füge in Qdrant ein
    if patterns:
        inserted = await db.insert_patterns_batch(patterns, batch_size=500)
        logger.info(f"✅ Filled gap: {gap_start} → {gap_end} | {inserted} patterns inserted")
```

---

## 5. Background Worker Implementation

### QThread-basierter Worker

```python
from PyQt6.QtCore import QThread, pyqtSignal
import asyncio

class PatternUpdateWorker(QThread):
    """
    Background-Worker für automatische Pattern-DB-Updates.

    Features:
    - Periodisches Gap-Scanning (alle 5 Minuten)
    - Automatisches Gap-Filling via REST API
    - Event-Bus-Integration für neue Bars (WebSocket)
    """

    progress = pyqtSignal(str, int, int)  # (status, current, total)
    update_completed = pyqtSignal(int)  # (patterns_inserted)
    error_occurred = pyqtSignal(str)  # (error_message)

    def __init__(self, symbols: list[str], timeframes: list[str]):
        super().__init__()
        self.symbols = symbols
        self.timeframes = timeframes
        self.running = True
        self.scan_interval = 300  # 5 Minuten

    def run(self):
        """Main worker loop."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            while self.running:
                loop.run_until_complete(self._scan_and_fill_gaps())
                # Sleep 5 Minuten (check every second for stop signal)
                for _ in range(self.scan_interval):
                    if not self.running:
                        break
                    time.sleep(1)
        finally:
            loop.close()

    async def _scan_and_fill_gaps(self):
        """Scannt alle Symbole/Timeframes und füllt Lücken."""
        total_patterns = 0

        for symbol in self.symbols:
            for timeframe in self.timeframes:
                try:
                    self.progress.emit(
                        f"🔍 Scanning {symbol} {timeframe}...", 0, 0
                    )

                    # 1. Detect gaps
                    gaps = await detect_gaps(symbol, timeframe)

                    if not gaps:
                        logger.info(f"✅ No gaps for {symbol} {timeframe}")
                        continue

                    # 2. Fill each gap
                    for i, (gap_start, gap_end) in enumerate(gaps):
                        self.progress.emit(
                            f"📥 Filling gap {i+1}/{len(gaps)} for {symbol}...",
                            i + 1,
                            len(gaps)
                        )

                        patterns_inserted = await fill_gap(
                            symbol, timeframe, gap_start, gap_end
                        )
                        total_patterns += patterns_inserted

                except Exception as e:
                    logger.error(f"❌ Error filling gaps for {symbol}: {e}")
                    self.error_occurred.emit(str(e))

        self.update_completed.emit(total_patterns)

    def stop(self):
        """Stop worker gracefully."""
        self.running = False
```

---

## 6. Rate Limit Best Practices

### Bitunix Rate Limit: 10 req/s

**Strategie:**
```python
# Delay zwischen Requests
RATE_LIMIT_DELAY = 0.15  # 150ms = ~6.67 req/s (safety margin)

# Bei großen Downloads: Batch mit Progress
async def fetch_large_dataset(symbol, start, end, timeframe):
    total_batches = calculate_batches(start, end, timeframe)

    for batch_num in range(total_batches):
        # Fetch batch
        bars = await provider.fetch_bars(...)

        # Respect rate limit
        await asyncio.sleep(RATE_LIMIT_DELAY)

        # Progress callback
        progress_callback(batch_num + 1, total_batches, len(bars))
```

### Exponential Backoff bei Errors

```python
async def fetch_with_retry(url, params, max_retries=3):
    """Fetch mit automatischem Retry bei 429 (Rate Limit Exceeded)."""
    for attempt in range(max_retries):
        try:
            async with session.get(url, params=params) as response:
                if response.status == 429:
                    # Rate limit exceeded → Exponential Backoff
                    wait_time = (2 ** attempt) * RATE_LIMIT_DELAY
                    logger.warning(f"⚠️ Rate limit hit, waiting {wait_time}s...")
                    await asyncio.sleep(wait_time)
                    continue

                if response.status == 200:
                    return await response.json()

                # Other errors
                raise Exception(f"HTTP {response.status}")

        except aiohttp.ClientError as e:
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(RATE_LIMIT_DELAY * (attempt + 1))

    raise Exception(f"Max retries ({max_retries}) exceeded")
```

---

## 7. WebSocket Integration (Real-time Updates)

### Live-Update-Strategie

```python
class BitunixWebSocketListener:
    """
    Listet auf WebSocket-Kline-Updates und aktualisiert Pattern-DB live.
    """

    def __init__(self, symbols: list[str], timeframe: str):
        self.symbols = symbols
        self.timeframe = timeframe
        self.extractor = PatternExtractor(window_size=20)
        self.db = TradingPatternDB()

    async def connect(self):
        """Verbindet mit Bitunix WebSocket."""
        uri = "wss://fapi.bitunix.com/api/v1/futures/market/ws"

        async with websockets.connect(uri) as ws:
            # Subscribe to kline channel for each symbol
            for symbol in self.symbols:
                await ws.send(json.dumps({
                    "method": "subscribe",
                    "params": {
                        "channel": "kline",
                        "symbol": symbol,
                        "interval": self.timeframe
                    }
                }))

            # Listen for updates
            async for message in ws:
                await self._handle_message(json.loads(message))

    async def _handle_message(self, data: dict):
        """Verarbeitet WebSocket-Message."""
        if data.get("channel") == "kline":
            # Neue Kerze empfangen
            kline = data["data"]
            bar = self._parse_kline(kline)

            # Extrahiere Pattern aus letzten 20 Bars (inkl. neuer)
            recent_bars = await self._get_recent_bars(
                bar.symbol, self.timeframe, count=20
            )
            recent_bars.append(bar)

            pattern = self.extractor.extract_current_pattern(
                recent_bars, bar.symbol, self.timeframe
            )

            if pattern:
                # Füge Pattern in Qdrant ein
                await self.db.insert_pattern(pattern)
                logger.info(f"✅ Live Pattern inserted: {bar.symbol} @ {bar.timestamp}")
```

---

## 8. Performance-Metriken

### Benchmark: Gap-Filling-Geschwindigkeit

**Szenario:** 1 Woche Daten (1min Timeframe) für BTCUSDT

- **Total Bars:** 10,080 Kerzen
- **Requests nötig:** 51 (@ 200 bars/req)
- **Zeit @ 10 req/s:** 5.1 Sekunden (theoretisch)
- **Zeit @ 6.67 req/s (safety):** 7.6 Sekunden (praktisch)
- **Pattern-Extraktion:** ~2,000 Patterns (window=20, step=5)
- **Qdrant-Insert:** 2,000 patterns @ 500/batch = 4 batches = ~2 Sekunden

**Gesamt:** ~10 Sekunden für 1 Woche 1-Min-Daten

### Optimierungspotenzial

1. **Parallel Symbols:** Mehrere Symbole gleichzeitig laden (z.B. BTCUSDT + ETHUSDT parallel)
2. **Batch-Insert-Optimierung:** Größere Qdrant-Batches (500 → 1000)
3. **Caching:** Bereits geladene Bars cachen (SQLite Auto-Cache)

---

## 9. Fehlerbehandlung & Edge Cases

### Edge Case 1: Erste Patterns < 20 Bars

**Problem:** PatternExtractor braucht min. 20 Bars + 5 Outcome-Bars = 25 Bars

**Lösung:**
```python
if len(bars) < 25:
    logger.warning(f"Not enough bars for pattern extraction: {len(bars)} < 25")
    # Füge rohe Bars in SQLite ein, aber keine Patterns
    return []
```

### Edge Case 2: Qdrant Collection noch nicht existiert

**Lösung:**
```python
async def safe_insert_patterns(patterns):
    """Insert mit automatischer Collection-Erstellung."""
    try:
        await db.insert_patterns_batch(patterns)
    except Exception as e:
        if "collection not found" in str(e):
            logger.info("📦 Creating Qdrant collection...")
            await db.initialize()
            await db.insert_patterns_batch(patterns)
        else:
            raise
```

### Edge Case 3: API Downtime

**Lösung:**
```python
async def fetch_with_fallback(symbol, start, end, timeframe):
    """Versuche Bitunix, fallback zu cached SQLite data."""
    try:
        return await bitunix_provider.fetch_bars(...)
    except Exception as e:
        logger.warning(f"⚠️ Bitunix API failed: {e}")
        logger.info("📂 Falling back to cached SQLite data...")

        # Lade aus SQLite Cache
        from src.database import get_cached_bars
        return get_cached_bars(symbol, start, end, timeframe)
```

---

## 10. Zusammenfassung: Best Practices

✅ **DO's:**
1. **Hybrid-Approach:** WebSocket für Live, REST für Gap-Filling
2. **Gap Detection:** Intelligentes Scannen nach Datenlücken
3. **Incremental Updates:** Nur fehlende Daten nachladen
4. **Rate-Limit-Respekt:** 0.15s Delay + Exponential Backoff
5. **Background Workers:** Nicht-blockierende Updates via QThread
6. **Error Handling:** Retry-Logic + Fallback zu SQLite Cache
7. **Progress Tracking:** UI-Updates für lange Downloads

❌ **DON'Ts:**
1. **Full Rebuild:** Nicht gesamte DB neu bauen bei kleinen Lücken
2. **Synchronous Blocking:** Nicht UI-Thread blockieren
3. **API-Spam:** Rate-Limits respektieren, sonst Ban-Risiko
4. **Fehlende Validierung:** OHLC-Daten validieren (High < Open/Close → Fix)
5. **Keine Deduplication:** Duplikate vermeiden bei Overlapping-Requests

---

## Quellen

- [Bitunix OpenAPI Kline Endpoint](https://openapidoc.bitunix.com/doc/market/get_kline.html)
- [Bitunix WebSocket Kline Channel](https://openapidoc.bitunix.com/doc/websocket/public/kline%20channel.html)
- [Bitunix API Introduction](https://openapidoc.bitunix.com/doc/common/introduction.html)
- [CoinAPI: Historical Crypto Data Guide](https://www.coinapi.io/blog/historical-crypto-data-guide-why-volume-numbers-look-different)
- [Crypto Data Download: Gap Analysis](https://www.cryptodatadownload.com/)
