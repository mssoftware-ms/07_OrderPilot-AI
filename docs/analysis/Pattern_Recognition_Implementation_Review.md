# Pattern Recognition Implementation Review
**Status:** Vergleich Implementierung vs. Spezifikation
**Datum:** 2026-01-20
**Schwerpunkt:** Live-Daten, Zeitrahmen-Konvertierung, Teilmustererkennung

---

## Executive Summary

Die aktuelle Implementierung bietet eine **solide Basis** für Pattern Recognition mit Qdrant-basierter Ähnlichkeitssuche. Allerdings fehlen **kritische Features** aus der Spezifikation, insbesondere:

1. ❌ **Live-Daten-Updates** - Pattern-DB ist statisch (manueller Build erforderlich)
2. ⚠️ **Multi-Timeframe-Support** - Keine automatische Zeitrahmen-Konvertierung
3. ❌ **Teilmustererkennung** - Keine Erkennung aktuell bildender Muster
4. ⚠️ **DTW-Algorithmus** - Verwendet Cosine-Similarity statt DTW
5. ❌ **Heikin-Ashi-Smoothing** - Keine Datenglättung vor Pattern-Extraktion

**Empfehlung:** Schrittweise Ergänzung fehlender Features gemäß Priorisierung (siehe Kapitel 5).

---

## 1. Aktuelle Implementierung (Ist-Zustand)

### 1.1 Architektur-Übersicht

```
┌─────────────────────┐
│  UI Layer           │
│  PatternRecognition │  ← Benutzer-Interaktion
│  Widget             │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Service Layer      │
│  PatternService     │  ← Orchestrierung
└──────────┬──────────┘
           │
           ├──────────────────────────┐
           ▼                          ▼
┌──────────────────┐      ┌──────────────────┐
│  Pattern DB      │      │  Chart Data      │
│  (Qdrant)        │      │  (SQLite)        │
│                  │      │                  │
│  - Embeddings    │      │  - OHLCV Bars    │
│  - Metadata      │      │  - Auto-Cached   │
│  - Manual Build  │      │  - Auto-Updated  │
└──────────────────┘      └──────────────────┘
```

### 1.2 Pattern-Extraktion (`extractor.py`)

**Algorithmus:**
```python
# Sliding Window mit fester Größe
window_size = 20 bars  # Standard
step_size = 5 bars     # Overlap
outcome_bars = 5 bars  # Forward-Looking

# Normalisierung: Relative Änderung zum ersten Preis
normalized = (price - first_price) / first_price * 100
```

**Features:**
- ✅ Sliding Window Pattern-Extraktion
- ✅ Normalisierung (0-100% relative zum Startpreis)
- ✅ Outcome-Labeling (win/loss/neutral)
- ✅ Trend-Klassifizierung (up/down/sideways)
- ✅ Volatilitäts-Berechnung (Standardabweichung der Returns)
- ✅ Volume-Trend-Analyse

**Fehlende Features (vs. Spec):**
- ❌ **Heikin-Ashi-Smoothing** - Keine Glättung vor Extraktion
- ❌ **Multi-Timeframe-Resampling** - Keine automatische Konvertierung 1min → 15min
- ❌ **Partielle Patterns** - `extract_current_pattern()` existiert, aber nur für vollständige 20-Bar-Windows

### 1.3 Pattern-Embeddings (`embedder.py`)

**Embedding-Dimension:** 96 (20 bars × 4 OHLC + 16 statistische Features)

**Komponenten:**
1. **Flattened OHLC** (80 dim): Normalisierte OHLC-Daten als Vektor
2. **Statistische Features** (16 dim):
   - Price Change %
   - Volatility
   - Body-to-Range Ratio
   - Upper/Lower Shadows
   - Trend Consistency
   - Momentum
   - Range Expansion
   - Volume Features (2)
   - Shape Features (Mean, Std, Range) (3)
   - Trend Linearity (R²)
   - Trend Encoding (up=1, down=-1, sideways=0)

**Ähnlichkeitsmetrik:**
```python
# L2-Normalisierung + Cosine-Similarity
embedding = embedding / np.linalg.norm(embedding)
```

**Spec-Vergleich:**
- ⚠️ Spec empfiehlt **DTW (Dynamic Time Warping)** für Zeitreihen-Ähnlichkeit
- ✅ Aktuelle Implementierung nutzt **Cosine-Similarity** (schneller, skalierbar)
- **Trade-off:** Cosine-Similarity ignoriert zeitliche Verschiebungen (DTW robuster bei Phase-Shifts)

### 1.4 Qdrant-Integration (`qdrant_client.py`)

**Konfiguration:**
- Host: `localhost`
- Port: `6335` (separater Container für OrderPilot)
- Collection: `trading_patterns`
- Vector Distance: `COSINE`

**Indizes:**
- `symbol` (Keyword)
- `timeframe` (Keyword)
- `trend_direction` (Keyword)
- `outcome_label` (Keyword)

**Probleme:**
- ❌ **Statische Datenbank** - Keine automatische Aktualisierung
- ❌ **Manueller Build** - Muss via `build_patterns_quick.py` gefüllt werden
- ⚠️ **Keine TTL/Expiration** - Alte Patterns werden nicht automatisch entfernt

### 1.5 UI-Integration (`pattern_recognition_widget.py`)

**Features:**
- ✅ Fortschrittsbalken (0%, 10%, 30%, 50%, 80%, 100%)
- ✅ Status-Label mit Emoji-Indikatoren
- ✅ QThread für Event-Loop-Isolation
- ✅ Error-Printing zu CMD/Console
- ✅ Pattern-Matches-Tabelle
- ✅ Ergebnis-Statistiken (Win Rate, Avg Return)

**Fehlende Features:**
- ❌ Live-Daten-Refresh-Button
- ❌ Zeitrahmen-Auswahl (1min → 5min → 15min Konvertierung)
- ❌ Teilmuster-Detection-Toggle
- ❌ Chart-Overlay mit Regime-Grenzen

---

## 2. Spezifikations-Anforderungen (Soll-Zustand)

### 2.1 Kernkonzepte aus `mustererkennung_komplett.md`

#### A) DTW-basierte Ähnlichkeitssuche

**Goldstandard-Algorithmus:**
```python
from scipy.spatial.distance import euclidean
from dtaidistance import dtw

# DTW-Distanz mit Warping-Pfad
distance = dtw.distance(
    pattern1_close_prices,
    pattern2_close_prices,
    window=5  # Sakoe-Chiba Band
)
```

**Vorteile gegenüber Cosine-Similarity:**
- Robust gegen zeitliche Verschiebungen (Phase-Shifts)
- Berücksichtigt zeitliche Reihenfolge
- Bessere Matches für ähnliche Muster mit unterschiedlicher Geschwindigkeit

**Spec-Empfehlung:**
> "DTW als Goldstandard für Zeitreihen-Vergleich, ergänzt durch Cosine-Similarity für globale Shape-Ähnlichkeit."

#### B) Heikin-Ashi-Smoothing

**Datenglättungs-Pipeline:**
```python
# 1. Heikin-Ashi-Transformation
ha_close = (open + high + low + close) / 4
ha_open = (prev_ha_open + prev_ha_close) / 2
ha_high = max(high, ha_open, ha_close)
ha_low = min(low, ha_open, ha_close)

# 2. EMA-Glättung (optional)
ha_close_ema = ema(ha_close, period=3)

# 3. Savitzky-Golay-Filter (optional)
from scipy.signal import savgol_filter
smoothed = savgol_filter(ha_close_ema, window_length=5, polyorder=2)
```

**Begründung:**
- Reduziert Rauschen in 1-Min-Kerzen (SNR 0.8-1.5 → 2.5-3.2 bei 15-Min)
- Verbessert Pattern-Erkennungsrate um 15-25%
- Empfohlen für Timeframes < 5 Minuten

**Aktuelle Implementierung:** ❌ Keine Glättung vorhanden

#### C) Multi-Timeframe-Approach

**Empfohlene Timeframes (aus Spec):**

| Timeframe | SNR (Signal-Noise) | Empfehlung | Use Case |
|-----------|-------------------|------------|----------|
| 1 Min | 0.8 - 1.5 | ⚠️ Mit Smoothing | Scalping, Live-Detection |
| 5 Min | 1.8 - 2.3 | ✅ Gut | Daytrading |
| **15 Min** | **2.5 - 3.2** | **✅ Sweet Spot** | **Pattern Discovery** |
| 1 Hour | 3.0 - 4.0 | ✅ Sehr gut | Swing Trading |

**Spec-Empfehlung:**
> "15-Minuten als Sweet-Spot für Pattern-Erkennung (Discovery), Bestätigung auf 5-Min (Validation), Entry auf 1-Min (Forward Testing)."

**Aktuelle Implementierung:**
- ⚠️ Unterstützt verschiedene Timeframes (1min, 5min, 15min)
- ❌ Keine automatische Konvertierung 1min → 15min
- ❌ Keine Multi-Timeframe-Confirmation

#### D) Drei-Phasen-Backtesting

**Phase 1: Discovery (6-12 Monate)**
- Timeframe: 15 Minuten
- Ziel: Muster-Identifikation mit hoher Confidence
- Minimum: 100-200 Patterns pro Kategorie

**Phase 2: Validation (3-6 Monate)**
- Timeframe: 5 Minuten
- Ziel: Out-of-Sample-Verifizierung
- Konfidenz-Schwelle: >70%

**Phase 3: Forward Testing (2-8 Wochen)**
- Timeframe: 1 Minute (Live)
- Ziel: Live-Validierung mit Paper-Trading
- Stop-Loss: <3% Max Drawdown

**Aktuelle Implementierung:** ❌ Keine Backtesting-Phasen implementiert

#### E) Confidence-Scoring

**Spec-Formel:**
```python
def calculate_confidence(similarity_score, num_matches, outcome_consistency):
    # Sigmoid-Mapping: 0-1 → 0-100%
    base_confidence = 1 / (1 + np.exp(-10 * (similarity_score - 0.5)))

    # Bonusfaktoren
    match_bonus = min(num_matches / 50, 0.2)  # Max 20% Bonus bei 50+ Matches
    outcome_bonus = outcome_consistency * 0.15  # Max 15% Bonus bei konsistenten Outcomes

    return min((base_confidence + match_bonus + outcome_bonus) * 100, 100)
```

**Aktuelle Implementierung:**
- ⚠️ Verwendet direkt Cosine-Similarity (0-1 Range)
- ❌ Keine Sigmoid-Transformation
- ❌ Keine Bonusfaktoren für Match-Count/Outcome-Consistency

---

## 3. Kritische Lücken (User-Anforderungen)

### 3.1 ❌ Live-Daten-Updates (PRIORITY 1)

**Problem:**
- Pattern-DB wird manuell via `build_patterns_quick.py` gebaut
- Enthält nur historische Daten bis zum Build-Zeitpunkt
- Keine Aktualisierung bei neuen Marktdaten

**User-Anforderung:**
> "Das wichtigste ist wohl erst die daten aus der datenbank zu aktualisieren so das sie den live zustand haben"

**Fehlende Komponenten:**
1. **Auto-Update-Mechanismus**
   - Trigger: Neue Bars empfangen (ChartDataListener)
   - Aktion: Pattern-Extraktion + Qdrant-Insert
   - Frequenz: Echtzeit (jede neue Kerze) oder periodisch (z.B. jede Stunde)

2. **Incremental Pattern Insertion**
   ```python
   async def update_patterns_incremental(symbol, timeframe, new_bars):
       # Extract patterns from newest bars only
       patterns = extractor.extract_patterns(new_bars, symbol, timeframe)

       # Insert into Qdrant
       await db.insert_patterns_batch(patterns)
   ```

3. **Pattern Expiration/TTL**
   - Alte Patterns (>1 Jahr) automatisch entfernen
   - Relevanz-Score basierend auf Aktualität

**Lösung:**
- Background Worker, der neue Chart-Daten überwacht
- Automatisches Pattern-Update bei neuen Bars
- Optional: Scheduled Task (z.B. täglich um 00:00 Uhr full rebuild)

### 3.2 ⚠️ Zeitrahmen-Konvertierung (PRIORITY 2)

**Problem:**
- Pattern-DB enthält 1min, 5min, 15min separat
- Keine Konvertierung zwischen Timeframes
- User möchte: "1min Kerzen → alle höheren Zeiteinheiten umrechnen"

**User-Anforderung:**
> "eigentlich reicht 1min kerzen, da man sie auf alle anderen höheren zeiteinheiten umrechnen kann"

**Fehlende Komponenten:**

1. **OHLC Resampling**
   ```python
   import pandas as pd

   def resample_bars(bars_1min, target_timeframe):
       df = pd.DataFrame([{
           'timestamp': b.timestamp,
           'open': b.open,
           'high': b.high,
           'low': b.low,
           'close': b.close,
           'volume': b.volume
       } for b in bars_1min])

       df.set_index('timestamp', inplace=True)

       resampled = df.resample(target_timeframe).agg({
           'open': 'first',
           'high': 'max',
           'low': 'min',
           'close': 'last',
           'volume': 'sum'
       })

       return resampled
   ```

2. **UI-Dropdown für Timeframe-Auswahl**
   - Benutzer wählt Ziel-Timeframe (1min, 5min, 15min, 1h)
   - Automatische Konvertierung vor Pattern-Analyse

3. **Multi-Timeframe-Confirmation**
   - Pattern auf 15min identifizieren
   - Bestätigung auf 5min prüfen
   - Entry-Signal auf 1min generieren

**Lösung:**
- `TimeframeConverter` Utility-Klasse
- Integration in PatternService.analyze_signal()
- UI-Element für Timeframe-Auswahl

### 3.3 ❌ Teilmustererkennung (PRIORITY 3)

**Problem:**
- `extract_current_pattern()` existiert, aber erfordert vollständige 20-Bar-Window
- Keine Erkennung partieller Muster (z.B. nur 15 von 20 Bars)

**User-Anforderung:**
> "Es ist ja auch durchaus möglich das der aktuelle chart ein muster bildet also cool wäre dann auch eine Teilmustererkennung"

**Use Case:**
```
Historisches Muster:  [====================] (20 Bars, vollständig)
Aktuelles Muster:     [===============?????] (15 Bars, 5 fehlen noch)

Frage: Ist das aktuelle Muster auf dem Weg, das historische zu replizieren?
```

**Fehlende Komponenten:**

1. **Partial Pattern Matching**
   ```python
   def extract_partial_pattern(bars, min_bars=15, max_bars=20):
       """Extract pattern even if incomplete."""
       if len(bars) < min_bars:
           return None

       # Use available bars, pad rest with zeros
       actual_bars = min(len(bars), max_bars)
       pattern = extractor._create_pattern(
           window_bars=bars[-actual_bars:],
           outcome_bars=[],  # No outcome yet
           symbol=symbol,
           timeframe=timeframe
       )

       pattern.metadata['is_partial'] = True
       pattern.metadata['completion'] = actual_bars / max_bars
       return pattern
   ```

2. **DTW mit variablen Längen**
   - DTW kann Patterns unterschiedlicher Länge vergleichen
   - Spec empfiehlt explizit DTW für diesen Use Case

3. **Confidence-Penalty für Teilmuster**
   - Vollständiges Muster (20/20 Bars): 100% Confidence
   - Teilmuster (15/20 Bars): 75% Confidence
   - Formel: `confidence = (bars_available / bars_required) * similarity_score`

4. **UI-Indikator für Teilmuster**
   - "Pattern Formation in Progress: 75% complete"
   - Real-time Update bei jeder neuen Kerze

**Lösung:**
- Erweitere `extract_current_pattern()` für variable Längen
- Implementiere DTW für Partial Matching
- UI-Toggle "Show Partial Patterns"

---

## 4. Weitere Spec-Gaps

### 4.1 DTW-Algorithmus (MEDIUM PRIORITY)

**Spec-Empfehlung:** DTW als Goldstandard
**Aktuelle Implementierung:** Cosine-Similarity

**Vergleich:**

| Feature | Cosine-Similarity | DTW |
|---------|------------------|-----|
| Geschwindigkeit | ⚡ Sehr schnell (O(n)) | ⚠️ Langsamer (O(n²)) |
| Zeitliche Verschiebung | ❌ Ignoriert | ✅ Berücksichtigt |
| Skalierbarkeit | ✅ Gut (Qdrant-optimiert) | ⚠️ Begrenzt (CPU-intensiv) |
| Robustheit | ⚠️ Sensitiv bei Phase-Shifts | ✅ Robust |

**Lösung:**
- Hybrid-Approach:
  1. **Pre-Filter mit Cosine-Similarity** (schnell, auf Qdrant)
  2. **DTW-Refinement** auf Top-100 Matches (genauer)

```python
async def search_with_dtw_refinement(pattern, limit=10):
    # Step 1: Fast pre-filtering
    candidates = await db.search_similar(
        pattern,
        limit=100,  # 10x mehr Kandidaten
        score_threshold=0.5
    )

    # Step 2: DTW refinement
    dtw_scores = []
    for candidate in candidates:
        dtw_distance = dtw.distance(
            pattern.close_prices,
            candidate.close_prices
        )
        dtw_scores.append((candidate, 1 / (1 + dtw_distance)))

    # Step 3: Return top matches by DTW
    sorted_matches = sorted(dtw_scores, key=lambda x: x[1], reverse=True)
    return sorted_matches[:limit]
```

### 4.2 Heikin-Ashi-Smoothing (MEDIUM PRIORITY)

**Implementierung:**
```python
def apply_heikin_ashi(bars):
    """Transform OHLC to Heikin-Ashi for noise reduction."""
    ha_bars = []
    prev_ha_open = bars[0].open
    prev_ha_close = bars[0].close

    for bar in bars:
        ha_close = (bar.open + bar.high + bar.low + bar.close) / 4
        ha_open = (prev_ha_open + prev_ha_close) / 2
        ha_high = max(bar.high, ha_open, ha_close)
        ha_low = min(bar.low, ha_open, ha_close)

        ha_bars.append(HistoricalBar(
            timestamp=bar.timestamp,
            open=ha_open,
            high=ha_high,
            low=ha_low,
            close=ha_close,
            volume=bar.volume
        ))

        prev_ha_open = ha_open
        prev_ha_close = ha_close

    return ha_bars
```

**Integration:**
- Option in `PatternAnalysisSettings`: "Apply Heikin-Ashi Smoothing"
- Automatisch anwenden für Timeframes < 5 Minuten

### 4.3 Multi-Timeframe-Confirmation (LOW PRIORITY)

**Spec-Empfehlung:**
> "Pattern auf 15min identifizieren → Bestätigung auf 5min → Entry auf 1min"

**Implementierung:**
```python
async def analyze_with_multi_timeframe_confirmation(bars_1min):
    # Step 1: Resample to 15min
    bars_15min = resample_bars(bars_1min, '15min')

    # Step 2: Find patterns on 15min
    patterns_15min = await pattern_service.analyze_signal(
        bars_15min, symbol, '15min'
    )

    if patterns_15min.similar_patterns_count < 10:
        return "No strong pattern on 15min"

    # Step 3: Confirm on 5min
    bars_5min = resample_bars(bars_1min, '5min')
    patterns_5min = await pattern_service.analyze_signal(
        bars_5min, symbol, '5min'
    )

    if patterns_5min.win_rate < 0.6:
        return "Pattern not confirmed on 5min"

    # Step 4: Generate entry signal on 1min
    entry_signal = await pattern_service.analyze_signal(
        bars_1min, symbol, '1min'
    )

    return entry_signal
```

---

## 5. Priorisierung & Roadmap

### Phase 1: Live-Daten (2-3 Tage)

**Ziel:** Pattern-DB automatisch aktualisieren

**Schritte:**
1. Implementiere `PatternUpdateWorker` (Background Thread)
2. Listener für neue Chart-Daten (Event-Bus)
3. Incremental Pattern Insertion in Qdrant
4. UI-Button "🔄 Refresh Pattern Database"

**Erwartetes Ergebnis:**
- ✅ Pattern-DB immer aktuell (max. 1 Stunde alt)
- ✅ Keine manuellen `build_patterns_quick.py` Runs nötig

### Phase 2: Zeitrahmen-Konvertierung (1-2 Tage)

**Ziel:** Benutzer kann Analyse-Timeframe wählen

**Schritte:**
1. Implementiere `TimeframeConverter.resample_bars()`
2. UI-Dropdown "Target Timeframe" in `PatternAnalysisSettings`
3. Integration in `PatternService.analyze_signal()`

**Erwartetes Ergebnis:**
- ✅ Analyse auf 1min, 5min, 15min, 1h möglich
- ✅ Automatische Umrechnung aus 1min-Daten

### Phase 3: Teilmustererkennung (2-3 Tage)

**Ziel:** Erkennung aktuell bildender Muster

**Schritte:**
1. Erweitere `extract_current_pattern()` für variable Längen
2. DTW-basiertes Partial Matching
3. UI-Toggle "Show Partial Patterns"
4. Real-time Update bei neuer Kerze

**Erwartetes Ergebnis:**
- ✅ "Pattern Formation: 75% complete" Indikator
- ✅ Live-Warnungen bei Pattern-Completion

### Phase 4: DTW-Refinement (2-3 Tage)

**Ziel:** Bessere Match-Qualität

**Schritte:**
1. Installiere `dtaidistance` Library
2. Implementiere Hybrid-Approach (Cosine Pre-Filter + DTW Refinement)
3. Benchmark: Cosine vs. DTW vs. Hybrid

**Erwartetes Ergebnis:**
- ✅ 10-15% bessere Pattern-Matches
- ✅ Robust gegen Phase-Shifts

### Phase 5: Heikin-Ashi + Multi-Timeframe (Optional, 2-3 Tage)

**Ziel:** Noise Reduction + Confirmation

**Schritte:**
1. Heikin-Ashi-Transformation in `extractor.py`
2. Multi-Timeframe-Confirmation-Logic
3. UI-Checkboxen "Apply Smoothing", "Multi-TF Confirmation"

**Erwartetes Ergebnis:**
- ✅ Bessere SNR für 1min-Patterns
- ✅ Höhere Win Rate durch Confirmation

---

## 6. Benchmark-Vergleich

### Aktuelle Implementierung vs. Spec

| Feature | Implementierung | Spezifikation | Gap |
|---------|----------------|---------------|-----|
| **Pattern-Extraktion** | ✅ Sliding Window | ✅ Sliding Window | ✅ Match |
| **Normalisierung** | ✅ Relative % | ✅ 0-1 Range | ⚠️ Different Scale |
| **Ähnlichkeitsmetrik** | ⚠️ Cosine | ✅ DTW | ❌ Gap |
| **Datenglättung** | ❌ Keine | ✅ Heikin-Ashi + EMA | ❌ Gap |
| **Timeframe-Support** | ⚠️ Statisch | ✅ Dynamisch | ❌ Gap |
| **Live-Updates** | ❌ Manuell | ✅ Automatisch | ❌ Gap |
| **Teilmustererkennung** | ❌ Keine | ✅ DTW Partial | ❌ Gap |
| **Multi-TF-Confirmation** | ❌ Keine | ✅ 15min→5min→1min | ❌ Gap |
| **Confidence-Scoring** | ⚠️ Direkt | ✅ Sigmoid + Bonuses | ⚠️ Partial Gap |
| **Backtesting-Phasen** | ❌ Keine | ✅ 3 Phasen | ❌ Gap |

**Gesamtbewertung:**
- ✅ **Vollständig umgesetzt:** 2/10 (20%)
- ⚠️ **Teilweise umgesetzt:** 3/10 (30%)
- ❌ **Nicht umgesetzt:** 5/10 (50%)

---

## 7. Empfohlene Architektur-Änderungen

### 7.1 Live-Update-Architektur

```
┌─────────────────────┐
│  ChartDataListener  │  ← Event: New Bar Received
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  PatternUpdate      │  ← Background Worker
│  Worker             │     (QThread oder asyncio Task)
└──────────┬──────────┘
           │
           ├──────────────────────────┐
           ▼                          ▼
┌──────────────────┐      ┌──────────────────┐
│  PatternExtractor│      │  Qdrant Client   │
│  .extract_patterns│      │  .insert_batch   │
└──────────────────┘      └──────────────────┘
```

**Pseudo-Code:**
```python
class PatternUpdateWorker(QThread):
    def __init__(self, event_bus):
        super().__init__()
        self.event_bus = event_bus
        self.event_bus.subscribe('chart.new_bar', self.on_new_bar)

    async def on_new_bar(self, event):
        symbol = event['symbol']
        timeframe = event['timeframe']
        new_bar = event['bar']

        # Get recent bars (window_size + outcome_bars)
        recent_bars = await self.get_recent_bars(symbol, timeframe, count=25)

        # Extract new patterns
        patterns = list(self.extractor.extract_patterns(
            recent_bars, symbol, timeframe
        ))

        # Insert into Qdrant
        if patterns:
            await self.db.insert_patterns_batch(patterns)
            logger.info(f"Inserted {len(patterns)} new patterns for {symbol}")
```

### 7.2 TimeframeConverter Service

```python
class TimeframeConverter:
    """Converts OHLC bars between timeframes."""

    @staticmethod
    def resample(bars: list[HistoricalBar],
                 target_tf: str) -> list[HistoricalBar]:
        """
        Resample bars to target timeframe.

        Args:
            bars: List of 1-min bars
            target_tf: '5min', '15min', '1h'

        Returns:
            Resampled bars
        """
        df = pd.DataFrame([{
            'timestamp': b.timestamp,
            'open': b.open,
            'high': b.high,
            'low': b.low,
            'close': b.close,
            'volume': b.volume
        } for b in bars])

        df.set_index('timestamp', inplace=True)

        resampled = df.resample(target_tf).agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }).dropna()

        return [
            HistoricalBar(
                timestamp=idx,
                open=row['open'],
                high=row['high'],
                low=row['low'],
                close=row['close'],
                volume=row['volume']
            )
            for idx, row in resampled.iterrows()
        ]
```

### 7.3 Partial Pattern Matcher

```python
class PartialPatternMatcher:
    """Matches incomplete patterns using DTW."""

    def __init__(self, db: TradingPatternDB):
        self.db = db

    async def match_partial(self,
                           current_bars: list[HistoricalBar],
                           min_completion: float = 0.75,
                           dtw_window: int = 5):
        """
        Match partial pattern with historical patterns.

        Args:
            current_bars: Current (incomplete) bars
            min_completion: Minimum % of pattern required (0.75 = 15/20 bars)
            dtw_window: DTW warping window size

        Returns:
            List of (pattern, confidence) tuples
        """
        # Extract partial pattern
        partial_pattern = self.extractor.extract_partial_pattern(
            current_bars,
            min_bars=int(self.extractor.window_size * min_completion)
        )

        # Get candidates from Qdrant (cosine pre-filter)
        candidates = await self.db.search_similar(
            partial_pattern,
            limit=100,
            score_threshold=0.5
        )

        # DTW refinement
        dtw_matches = []
        for candidate in candidates:
            # Truncate candidate to same length as partial
            candidate_truncated = candidate.close_prices[:len(current_bars)]

            # Calculate DTW distance
            distance = dtw.distance(
                partial_pattern.close_prices,
                candidate_truncated,
                window=dtw_window
            )

            # Convert distance to confidence
            confidence = 1 / (1 + distance) * (len(current_bars) / self.extractor.window_size)

            dtw_matches.append((candidate, confidence))

        # Sort by confidence
        return sorted(dtw_matches, key=lambda x: x[1], reverse=True)[:10]
```

---

## 8. Fazit

### Zusammenfassung

Die aktuelle Implementierung ist eine **solide Grundlage**, aber benötigt **kritische Erweiterungen**, um den Anforderungen der Spezifikation gerecht zu werden:

**Stärken:**
- ✅ Gut strukturierte Architektur (Service Layer, Pattern Extraction, Qdrant-Integration)
- ✅ Funktionierende UI mit Progress-Tracking
- ✅ Robuste Pattern-Extraktion mit Outcome-Labeling
- ✅ Skalierbare Qdrant-basierte Ähnlichkeitssuche

**Schwächen:**
- ❌ **Statische Pattern-DB** (keine Live-Updates)
- ❌ **Fehlende Teilmustererkennung** (kritisch für Live-Trading)
- ❌ **Keine Multi-Timeframe-Support** (Spec empfiehlt 15min → 5min → 1min)
- ⚠️ **Cosine statt DTW** (weniger robust bei Phase-Shifts)
- ❌ **Keine Datenglättung** (Heikin-Ashi für 1min-Patterns)

### Empfehlung

**Schrittweise Umsetzung gemäß Roadmap (Phase 1-5):**

1. **Phase 1 (KRITISCH):** Live-Daten-Updates → Macht Pattern-DB nutzbar für Live-Trading
2. **Phase 2 (WICHTIG):** Zeitrahmen-Konvertierung → Erfüllt User-Anforderung "1min → alle Timeframes"
3. **Phase 3 (WICHTIG):** Teilmustererkennung → Ermöglicht frühzeitige Signal-Detection
4. **Phase 4 (NICE-TO-HAVE):** DTW-Refinement → Verbessert Match-Qualität
5. **Phase 5 (OPTIONAL):** Heikin-Ashi + Multi-TF → Noise Reduction & Confirmation

**Geschätzte Gesamtaufwand:** 9-14 Arbeitstage (mit Testing & Dokumentation)

---

## Anhang: Verwendete Dateien

### Implementierung (Gelesen)
1. `src/core/pattern_db/extractor.py` (309 Zeilen)
2. `src/core/pattern_db/embedder.py` (217 Zeilen)
3. `src/core/pattern_db/qdrant_client.py` (487 Zeilen)
4. `src/ui/widgets/pattern_recognition_widget.py` (481 Zeilen)
5. `build_patterns_quick.py` (142 Zeilen)

### Spezifikation (Referenz)
1. `01_Projectplan/01_bisher nicht umgesetzt/Chartmuster_Erkennung/mustererkennung_komplett.md` (1,131 Zeilen)

**Gesamt analysierte LOC:** ~2,767 Zeilen
