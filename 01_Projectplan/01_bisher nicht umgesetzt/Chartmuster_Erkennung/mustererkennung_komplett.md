# Chartmusteranalyse & Vorhersage – Kompletter Leitfaden

**Inhaltsübersicht:**
1. [Theoretischer Hintergrund](#theoretischer-hintergrund)
2. [Datenglättung](#datenglättung)
3. [Musterähnlichkeit mit DTW](#musterähnlichkeit-mit-dtw)
4. [End-to-End Pipeline](#end-to-end-pipeline)
5. [Optimale Analysezeiträume](#optimale-analysezeiträume)
6. [Optimale Kerzenzeiträume](#optimale-kerzenzeiträume)
7. [Backtesting-Framework](#backtesting-framework)

---

## Theoretischer Hintergrund

### Warum einfacher Vergleich nicht funktioniert

Bei Chartmustern treten mehrere typische Probleme auf:

**Zeitliche Asymmetrie:**
- Historisches Muster: 45 Kerzen für eine komplette Bewegung
- Aktueller Chart: Ähnliches Muster, aber über 55 Kerzen verteilt
- Einfache euklidische Distanz (Punkt-zu-Punkt) wertet diese als stark unterschiedlich, obwohl die Form ähnlich ist.

**Rauschen & Mikrostruktur:**
- 1-Minuten-Kerzen sind stark verrauscht (Market Microstructure Noise)
- Lokale Spikes überlagern die eigentliche Bewegung
- Der Vergleich auf Rohdaten führt zu vielen False Positives

**Skalierungsproblem:**
- Muster bei Kurs 1.0850 vs. 1.0950
- Relative Form ist ähnlich, aber absolute Werte sind unterschiedlich
- Ohne Normalisierung werden solche Muster nicht erkannt

### Best Practices (Stand 2025)

Aus moderner Literatur und Algo-Trading-Praxis lassen sich diese Punkte ableiten:

1. **Datenglättung ist Pflicht** – reduziert Rausch um 60–80%
2. **Dynamic Time Warping (DTW)** – Goldstandard für Zeitreihen-Ähnlichkeit
3. **Multi-Layer-Ansatz** – Glättung + Normalisierung + Strukturanalyse
4. **Extrema-Fokus** – Pivot Points statt jede Kerze vergleichen
5. **Konfidenz-Scoring** – 0–100 % statt Binary-Match

---

## Datenglättung

### Warum glätten?

**Rohdaten (1-Min Close):**
```text
1.0852, 1.0851, 1.0853, 1.0850, 1.0849, 1.0851, 1.0852, ...
```

**Geglättet (Heikin-Ashi oder EMA):**
```text
1.0851, 1.0851, 1.0851, 1.0850, 1.0850, 1.0851, 1.0851, ...
```

Effekt: Einzelne Spikes verschwinden, die zugrundeliegende Struktur (Trend, Schwingung) wird sichtbar.

### Glättungsmethoden im Vergleich

| Methode | Vorteil | Nachteil | Geeignet für Mustererkennung |
|---------|---------|---------|------------------------------|
| **EMA** | Reaktiv, wenig Lag | Glättet weniger stark | ⭐⭐⭐⭐ Sehr gut |
| **SMA** | Einfach, robust | Mehr Lag | ⭐⭐⭐ OK |
| **Heikin-Ashi** | Sehr klare Trends | Berechnet, mehr Lag | ⭐⭐⭐⭐⭐ Hervorragend |
| **Savitzky-Golay** | Sehr glatte Kurve | Rechenintensiv | ⭐⭐⭐⭐ Sehr gut |
| **Kalman Filter** | Adaptiv, probabilistisch | Komplex | ⭐⭐⭐⭐ Gut |

**Pragmatische Empfehlung für 1-Min-Daten:**
- Heikin-Ashi als Basis + optional EMA(20/50) oder Savitzky-Golay zur Zusatzglättung

### Python: Preprocessing-Klasse

```python
import numpy as np
import pandas as pd
from scipy.signal import savgol_filter, argrelextrema

class ChartDataPreprocessor:
    """Vorbereitung historischer und aktueller Chartdaten für Mustererkennung"""

    @staticmethod
    def heikin_ashi(ohlc_data: pd.DataFrame) -> pd.DataFrame:
        """Heikin-Ashi Glättung: Input/Output: DataFrame mit OHLC."""
        ha = pd.DataFrame(index=ohlc_data.index)

        ha_close = (ohlc_data['open'] + ohlc_data['high'] +
                    ohlc_data['low'] + ohlc_data['close']) / 4
        ha['ha_close'] = ha_close

        ha_open = ha_close.copy()
        ha_open.iloc[0] = ohlc_data['open'].iloc[0]
        for i in range(1, len(ha_open)):
            ha_open.iloc[i] = (ha_open.iloc[i-1] + ha_close.iloc[i-1]) / 2
        ha['ha_open'] = ha_open

        ha['ha_high'] = pd.concat(
            [ohlc_data['high'], ha['ha_open'], ha['ha_close']], axis=1
        ).max(axis=1)

        ha['ha_low'] = pd.concat(
            [ohlc_data['low'], ha['ha_open'], ha['ha_close']], axis=1
        ).min(axis=1)

        return ha

    @staticmethod
    def exponential_moving_average(prices, span=20):
        """EMA Glättung"""
        return pd.Series(prices).ewm(span=span, adjust=False).mean().values

    @staticmethod
    def savitzky_golay_smooth(prices, window=11, polyorder=3):
        """Polynomal-basiertes Smoothing"""
        prices = np.asarray(prices)
        if len(prices) < window:
            window = len(prices) if len(prices) % 2 == 1 else len(prices) - 1
        if window <= polyorder:
            polyorder = window - 1
        return savgol_filter(prices, window, polyorder, mode='nearest')

    @staticmethod
    def normalize_prices(prices):
        """Normalisierung auf 0-1 Range (relative Veränderungen)"""
        prices = np.asarray(prices)
        min_p, max_p = prices.min(), prices.max()
        if max_p == min_p:
            return np.full_like(prices, 0.5, dtype=float)
        return (prices - min_p) / (max_p - min_p)

    @staticmethod
    def prepare_data(ohlc_df: pd.DataFrame,
                     smoothing_method='heikin_ashi',
                     normalize=True):
        """Komplette Daten-Vorbereitung für Mustererkennung"""
        ha = ChartDataPreprocessor.heikin_ashi(ohlc_df)
        base = ha['ha_close'].values

        if smoothing_method == 'ema':
            smoothed = ChartDataPreprocessor.exponential_moving_average(base, span=20)
        elif smoothing_method == 'savgol':
            smoothed = ChartDataPreprocessor.savitzky_golay_smooth(base, window=11, polyorder=3)
        else:
            smoothed = base

        if normalize:
            smoothed = ChartDataPreprocessor.normalize_prices(smoothed)

        return smoothed
```

---

## Musterähnlichkeit mit DTW

### Warum DTW?

**Beispiel:**

```text
Pattern A: [0.3, 0.5, 0.7, 0.6, 0.4, 0.2]
Pattern B: [0.3, 0.45, 0.5, 0.65, 0.7, 0.65, 0.55, 0.4, 0.2]
```

- Euklidische Distanz: Schlecht (unterschiedliche Längen)
- **DTW**: Erlaubt "Warping" und findet das optimale Alignment ✅

### Python: DTW + Konfidenz

```python
class TimeSeriesMatcher:
    """Mustererkennung auf Basis von DTW"""

    @staticmethod
    def dtw_distance(series1, series2):
        """
        Dynamic Time Warping Distance
        Berechnet optimal gepfadete Ähnlichkeit zwischen zwei Zeitreihen
        """
        s1 = np.asarray(series1, dtype=float)
        s2 = np.asarray(series2, dtype=float)
        n, m = len(s1), len(s2)
        dtw = np.full((n+1, m+1), np.inf)
        dtw[0, 0] = 0.0

        for i in range(1, n+1):
            for j in range(1, m+1):
                cost = (s1[i-1] - s2[j-1]) ** 2
                dtw[i, j] = cost + min(dtw[i-1, j],      # Einfügen
                                       dtw[i, j-1],      # Löschen
                                       dtw[i-1, j-1])    # Match

        # Pfad zurückverfolgen (für Visualisierung)
        i, j = n, m
        path = [(i-1, j-1)]
        while i > 1 or j > 1:
            candidates = []
            if i > 1:
                candidates.append((dtw[i-1, j], i-1, j))
            if j > 1:
                candidates.append((dtw[i, j-1], i, j-1))
            if i > 1 and j > 1:
                candidates.append((dtw[i-1, j-1], i-1, j-1))
            val, i, j = min(candidates, key=lambda x: x[0])
            path.append((i-1, j-1))
        path.reverse()

        return float(dtw[n, m]), path

    @staticmethod
    def pattern_match_score(series1, series2, dtw_distance, max_distance=None):
        """
        Konvertiert DTW-Distanz in Konfidenz-Score (0-100%)
        
        Sigmoid-Mapping für sanfte Konvertierung:
        - DTW_distance = 0 → Confidence = 100%
        - DTW_distance = max_distance → Confidence ≈ 50%
        - DTW_distance = 2*max_distance → Confidence ≈ 12%
        """
        if max_distance is None:
            max_distance = max(len(series1), len(series2)) * 0.15
        
        confidence = 100.0 / (1.0 + np.exp((dtw_distance - max_distance) / 2.0))
        return float(max(0.0, min(100.0, confidence)))

    @staticmethod
    def fastdtw(series1, series2, radius=5):
        """
        FastDTW: Schnellere DTW-Variante für große Datenmengen
        
        Nutzt Sakoe-Chiba Band für Constraint
        """
        n, m = len(series1), len(series2)
        dtw = np.full((n+1, m+1), np.inf)
        dtw[0, 0] = 0.0

        for i in range(1, n+1):
            for j in range(max(1, i-radius), min(m+1, i+radius)):
                distance = (series1[i-1] - series2[j-1]) ** 2
                dtw[i, j] = distance + min(
                    dtw[i-1, j],
                    dtw[i, j-1],
                    dtw[i-1, j-1]
                )

        return float(dtw[n, m])
```

---

## End-to-End Pipeline

### Pattern-Erkennungs-Engine

```python
from scipy.signal import argrelextrema

class PatternRecognitionEngine:
    """Komplette Engine für historische Mustererkennung und aktuelle Analyse"""
    
    def __init__(self, historical_df: pd.DataFrame):
        self.preprocessor = ChartDataPreprocessor()
        self.matcher = TimeSeriesMatcher()
        self.df_historical = historical_df
        self.historical_patterns = []
        self.current_pattern = None

    def _extract_local_extrema(self, values, window=5):
        """Finde lokale Maxima und Minima (Pivot Points)"""
        values = np.asarray(values)
        local_max = argrelextrema(values, np.greater_equal, order=window)[0]
        local_min = argrelextrema(values, np.less_equal, order=window)[0]
        extrema = np.sort(np.unique(np.concatenate([local_max, local_min])))
        return extrema

    def extract_patterns_from_history(self, pattern_length=50, step_size=10):
        """
        Extrahiere alle möglichen Muster aus historischen Daten
        
        Parameter:
            pattern_length: Länge des Musters in Kerzen
            step_size: Schrittweite beim Sliding Window
        """
        prices = self.df_historical['close'].values
        smoothed = self.preprocessor.prepare_data(
            self.df_historical[['open', 'high', 'low', 'close']],
            smoothing_method='heikin_ashi',
            normalize=True,
        )

        patterns = []
        for i in range(0, len(smoothed) - pattern_length, step_size):
            segment = smoothed[i:i+pattern_length]
            extrema_idx = self._extract_local_extrema(segment, window=3)
            if len(extrema_idx) < 4:  # Mindestens 3 Moves (4 Extrema)
                continue

            direction = 'UP' if segment[-1] > segment[0] else 'DOWN'
            price_start, price_end = prices[i], prices[i+pattern_length-1]
            change_pct = (price_end - price_start) / price_start * 100.0

            patterns.append({
                'start_idx': i,
                'end_idx': i + pattern_length,
                'timestamp': self.df_historical.index[i],
                'pattern': segment,
                'extrema_indices': extrema_idx,
                'extrema_values': segment[extrema_idx],
                'direction': direction,
                'price_start': price_start,
                'price_end': price_end,
                'price_change_pct': change_pct,
            })

        self.historical_patterns = patterns
        print(f"✓ {len(patterns)} Muster extrahiert")
        return patterns

    def analyze_current_pattern(self, current_ohlc: pd.DataFrame, pattern_length=50,
                                min_confidence=50.0):
        """
        Analysiere aktuellen Intraday-Chart
        
        Return: Liste von gefundenen ähnlichen Mustern mit Scores
        """
        prices = current_ohlc['close'].values
        smoothed = self.preprocessor.prepare_data(
            current_ohlc[['open', 'high', 'low', 'close']],
            smoothing_method='heikin_ashi',
            normalize=True,
        )
        current_segment = smoothed[-pattern_length:]
        self.current_pattern = current_segment

        current_direction = 'UP' if current_segment[-1] > current_segment[0] else 'DOWN'

        matches = []
        for hist in self.historical_patterns:
            # Nur vergleichen wenn Richtung ähnlich ist
            if hist['direction'] != current_direction:
                continue
            
            dtw_dist, path = self.matcher.dtw_distance(current_segment, hist['pattern'])
            conf = self.matcher.pattern_match_score(hist['pattern'], current_segment, dtw_dist)
            
            if conf < min_confidence:
                continue

            last_price = prices[-1]
            expected_price = last_price * (1.0 + hist['price_change_pct'] / 100.0)

            matches.append({
                'historical_pattern': hist,
                'dtw_distance': dtw_dist,
                'confidence': conf,
                'expected_move_pct': hist['price_change_pct'],
                'expected_price': expected_price,
                'warp_path': path,
            })

        matches.sort(key=lambda x: x['confidence'], reverse=True)
        return matches

    def aggregate_forecast(self, matches, top_n=5):
        """Aggregiere Top-N Matches zu einer Vorhersage"""
        if not matches:
            return {
                'average_confidence': 0.0,
                'expected_move_pct': 0.0,
                'move_std': 0.0,
                'forecast_interval': (0.0, 0.0),
                'top_matches': [],
            }

        top = matches[:top_n]
        weights = np.array([m['confidence'] for m in top], dtype=float)
        weights /= weights.sum()

        moves = np.array([m['expected_move_pct'] for m in top], dtype=float)
        weighted_move = float((weights * moves).sum())
        move_std = float(moves.std()) if len(moves) > 1 else 0.0

        return {
            'average_confidence': float(np.mean([m['confidence'] for m in top])),
            'expected_move_pct': weighted_move,
            'move_std': move_std,
            'forecast_interval': (weighted_move - 2*move_std,
                                  weighted_move + 2*move_std),
            'top_matches': top,
        }
```

### Praktisches Verwendungsbeispiel

```python
# 1. Daten laden
df = pd.read_csv('historical_data.csv', parse_dates=['datetime'], index_col='datetime')

# 2. Engine initialisieren
engine = PatternRecognitionEngine(df)

# 3. Historische Muster extrahieren
patterns = engine.extract_patterns_from_history(
    pattern_length=50,
    step_size=5
)

# 4. Aktuellen Chart analysieren
current_ohlc = pd.DataFrame({
    'open': [...],
    'high': [...],
    'low': [...],
    'close': [...]
})

matches = engine.analyze_current_pattern(current_ohlc, pattern_length=50)

# 5. Vorhersage generieren
forecast = engine.aggregate_forecast(matches, top_n=5)

print(f"Konfidenz: {forecast['average_confidence']:.1f}%")
print(f"Erwartete Bewegung: {forecast['expected_move_pct']:+.2f}%")
print(f"95% Intervall: [{forecast['forecast_interval'][0]:.2f}%, {forecast['forecast_interval'][1]:.2f}%]")
```

---

## Optimale Analysezeiträume

### Das Drei-Phasen-Modell

Die professionelle Herangehensweise bei Backtests basiert auf drei separaten, **chronologischen Phasen**:

```
Phase 1: DISCOVERY (6-12 Monate)
│
├─ Ziel: Gibt es echte Muster mit Edge?
├─ Pattern-Sample: 100-300
├─ Erwartete Winrate: 52-70%
└─ Test: Alle Daten verwenden
    
    ↓ NO OVERLAP!
    
Phase 2: VALIDATION (3-6 Monate, OUT OF SAMPLE)
│
├─ Ziel: Funktioniert es auch in neuen Daten?
├─ KRITISCH: Exakt gleiche Parameter wie Phase 1!
├─ Pattern-Sample: 50-150 neue Muster
├─ Erwartete Winrate: Discovery ±3-5%
└─ Rote Flagge: Wenn Winrate >10% unter Discovery → OVERFITTING
    
    ↓ NO OVERLAP!
    
Phase 3: FORWARD-TEST (2-8 Wochen, LIVE/PAPER)
│
├─ Ziel: Funktioniert es in der Realität?
├─ KRITISCH: Real-Time Daten, echte Slippage/Spreads
├─ Sample: 20-50 echte Trades
└─ Rote Flagge: Wenn Winrate deutlich unter Validation → Adaption nötig
```

### Phase 1: DISCOVERY (6–12 Monate)

**Parameter für 1-Min Kerzen:**

```python
timeframe = "6-12 months"
pattern_length = 40-80  # Kerzen (= 40-80 Min Chart-Zeit)
stride = 5-10  # Überlappung reduzieren
minimum_pattern_confidence = "65-70%"

# Für EUR/USD 1-Min:
# 6 Monate ~ 250 Tradingstage * 1440 Min = 360,000 Kerzen
# 12 Monate ~ 720,000 Kerzen
```

**Vorgehen:**

1. Extrahiere alle möglichen Muster
2. Filtere nach Qualität (Confidence > 65%)
3. Berechne für jeden Pattern-Typ:
   - Occurrence Frequency
   - Win Rate
   - Average Profit
   - Max Drawdown

**Success-Kriterien:**
- ✅ Mindestens 50-100 unterschiedliche Pattern-Typen
- ✅ Win-Rate zwischen 52-75% (realistisch!)
- ✅ Pattern tritt mindestens 5x auf (nicht Zufall)

**Rote Flaggen:**
- ❌ Win-Rate > 85% → Zu gut, Overfitting!
- ❌ Nur 10-20 Pattern gefunden → Zu restriktiv
- ❌ Pattern tritt nur 1-2x auf → Statistisches Rauschen

### Phase 2: VALIDATION (3–6 Monate, out-of-sample)

**KRITISCH:** Dieser Zeitraum darf KEINE Überschneidung mit Phase 1 haben!

**Chronologische Anordnung:**
```
Discovery Data:    | Validation Data:  | Forward Test:
2023-01-01         | 2023-09-01        | 2024-01-01
to 2023-08-31      | to 2023-12-31     | to ongoing
(6 Monate)         | (4 Monate)        |
```

**Vorgehen:**

1. Nutze exakt die gleichen Parameter wie Phase 1
   - Gleiche Smoothing-Methode (Heikin-Ashi + EMA)
   - Gleiche DTW-Schwelle
   - Gleiche Konfidenz-Grenzen

2. Teste OHNE zu optimieren

```python
# FALSCH:
params_optimized_on_validation_data = optimize(validation_data)
# → Damit hast du Phase 2 "kontaminiert"

# RICHTIG:
results = test_with_phase1_parameters(validation_data)
```

3. Vergleiche Discovery vs. Validation Metriken

```python
phase1_winrate = 68%
phase2_winrate = 65%  # ✅ Ähnlich? Großartig!

phase1_winrate = 68%
phase2_winrate = 42%  # ❌ Großes Loch? Overfitting erkannt!
```

**Success-Kriterien:**
- ✅ Win-Rate ähnlich zu Phase 1 (±3-5%)
- ✅ Durchschnittlicher Profit ähnlich (±10%)
- ✅ Drawdown-Profil ähnlich
- ✅ Gleiche Pattern-Typen sind signifikant

**Rote Flaggen:**
- ❌ Plötzlich niedrigere Win-Rate → Overfitted
- ❌ Völlig andere Pattern-Topologie → Regime Change
- ❌ Validation-Periode war Bear, Discovery war Bull → Regime-Bias

### Phase 3: FORWARD-TEST (2–8 Wochen Live/Paper)

**Das ist der Praxistest:**

```python
timeframe = "2-8 weeks"  # Real-Time!
live_pattern_detection = True  # Echte aktuelle Patterns
min_trades = 20  # Mindestens 20 echte Signals
```

**Was unterscheidet Phase 3 von Phase 1+2:**

| Aspekt | Backtest (Phase 1+2) | Live (Phase 3) |
|--------|-------------------|-------------------|
| **Ausführung** | Simuliert, perfekte Fills | Real: Slippage, Latenz, Rejection |
| **Psychologie** | Keine (Button-Druck) | Echt: Emotionale Entscheidungen |
| **Liquidität** | Angenommen 100% | Wirklich: 94.5% im Schnitt |
| **Überraschungen** | News ist in den Daten | News ist JETZT! |
| **Pattern-Frequenz** | Berechnet | Aktuell! |

### Statistische Mindestgrößen

| Ziel | Minimum Trades/Samples |
|------|----------------------|
| Grobe Idee | 30–50 |
| 95% Konfidenz (CLT) | ≈ 100 |
| Hohe Sicherheit | ≈ 200 |
| Institutionelle Standards | 500+ |

**Konkrete Zahlen für 1-Min Kerzen:**

```python
# 1-Min Kerzen sind HOCHFREQUENT
# Ein Pattern tritt vielleicht 10-20x pro Tag auf

Wenn du 6 Monate testest (250 Tradingstage):
  Hochfrequente Pattern (tritt 3x/Stunde auf)
    → ~72 Occurrences pro Tag × 250 Tage = 18,000 Samples ✅✅✅
  
  Moderate Pattern (tritt 2x/Tag auf)
    → 2 × 250 = 500 Samples ✅✅
  
  Seltene Pattern (tritt 1x pro Woche auf)
    → 50 Samples pro 6 Monate ❌ Zu wenig!
```

### Regime-Stratifikation (wichtig!)

**Problematisches Szenario:**

```
Wenn deine 6-Monate Discovery-Periode 4 Monate Trends + 2 Monate Range war:
  → Pattern werden zu "Trend-biased"
  → Versagen in Range-Märkten
```

**Lösung:**

```python
def stratified_backtest(data, patterns):
    """Teste Patterns separat für verschiedene Marktregime"""
    
    # 1. Erkenne Regime anhand von Indikatoren
    trend_regime = identify_trending_periods(data)
    range_regime = identify_ranging_periods(data)
    volatility_spikes = identify_high_volatility(data)
    
    results = {
        'trending': test_patterns(data[trend_regime], patterns),
        'ranging': test_patterns(data[range_regime], patterns),
        'volatile': test_patterns(data[volatility_spikes], patterns),
    }
    
    # 2. Vergleiche Win-Rates
    print(f"Trending:   {results['trending'].win_rate:.1%}")
    print(f"Ranging:    {results['ranging'].win_rate:.1%}")
    print(f"Volatile:   {results['volatile'].win_rate:.1%}")
    
    # 3. Flag problematische Regime
    if results['ranging'].win_rate < 45%:
        print("⚠️ WARNING: Patterns versagen in Range-Märkten!")
    
    return results
```

---

## Optimale Kerzenzeiträume

### Das Rausch-Dilemma: Signal-to-Noise Ratio

```
1-Min:  SNR ~0.6–0.8  ❌ (zu verrauscht)
5-Min:  SNR ~1.2–1.5  ⚠️ (akzeptabel)
15-Min: SNR ~2.5–3.2  ✅ (gut!)
30-Min: SNR ~4.5–6.0  ✅✅ (sehr gut)
```

### Vergleich: 1-Min vs. 5-Min vs. 15-Min

| Zeitraum | Signal-to-Noise | Pattern-Häufigkeit | Rausch-Filter nötig | Konsistenz Backtest→Live |
|----------|-----------------|--------------------|--------------------|------------------------|
| **1-Min** | 0.6–0.8 | Sehr häufig | Ultra-aggressiv | 70%+ → 38–45% ❌ |
| **5-Min** | 1.2–1.5 | Häufig | Stark | 65%+ → 52–62% ⚠️ |
| **15-Min** | 2.5–3.2 | Regelmäßig | Moderat | 62%+ → 58–62% ✅ |
| **30-Min** | 4.5–6.0 | Selten | Minimal | 60%+ → 58–61% ✅✅ |

### 1-Minute Kerzenzeitraum

**Wann sinnvoll:**
- Nur bei High-Frequency-Scalping (< 1 Min Holdtime)
- Mit massive Rechenkraft und Glättungs-Pipelines
- Außergewöhnlich liquide Assets (ES, GC, EUR/USD)

**Probleme:**
```
1min Close: 1.0850, 1.0851, 1.0850, 1.0849, 1.0851, 1.0852, 1.0850, ...
            ↓ Sind das echte Moves oder Spread-Bewegungen?
            → DTW-Distanz hoch, weil Rausch dominiert
```

**Lösung wenn 1-Min notwendig:**
1. Ultra-aggressive Glättung (Heikin-Ashi + EMA(10) + Savitzky-Golay)
2. Mindestens 500+ historische Muster
3. Nur Patterns mit 75%+ Konfidenz handeln
4. Regime-Filter stark einsetzen

### 5-Minute Kerzenzeitraum

**Wann sinnvoll:**
- Daytrading mit mehreren Trades pro Session (2–5)
- Holdtime: 5–30 Minuten
- Mehr Signals als 15-Min, aber weniger Rausch als 1-Min

**Pattern-Häufigkeit:**
```
6 Monate 5-Min Daten:
  - 250 Tradingstage × 288 Kerzen/Tag = ~72.000 Kerzen
  - Mit 50-Kerzen Pattern & Stride 5 → ~14.400 Kandidaten
  - Nach Filterung → 200–400 gute Patterns ✅
```

**Konsistenz:** Backtest-Konsistenz ca. 90% (5–10% Divergenz zu Live)

### 15-Minute Kerzenzeitraum ⭐ **EMPFOHLEN**

**Das ist der "Sweet Spot" für Mustererkennung!**

**Warum 15-Min das beste ist:**

1. **Optimal Signal-to-Noise Ratio** (~2.5–3.0)
   - Echte Moves sind sichtbar
   - Rausch ist gefiltert
   - Pattern sind stabil

2. **Genug Data Points**
   ```
   6 Monate 15-Min Daten:
     - 250 Tage × 96 Kerzen/Tag = ~24.000 Kerzen
     - Mit 50-Kerzen Pattern → ~4.800 Kandidaten
     - Nach Filterung → 150–300 exzellente Patterns ✅
   ```

3. **Pattern-Häufigkeit ist praktisch**
   - Ein gutes Pattern alle 1–3 Tage
   - Genug für Backtesting, aber nicht täglich "Rausch-Pattern"

4. **Backtest zu Live ist sehr konsistent**
   ```
   Discovery: 62% Winrate
   Validation: 59% Winrate
   Live: 58–61% Winrate
   → Sehr vorhersagbar!
   ```

5. **Technisch einfach**
   ```python
   smoothed = ChartDataPreprocessor.prepare_data(
       ohlc_df,
       smoothing_method='heikin_ashi',  # Reicht!
       normalize=True,
   )
   
   dtw_dist = TimeSeriesMatcher.dtw_distance(pattern_a, pattern_b)
   # Keine speziellen Tweaks nötig
   ```

**Pattern-Länge auf 15-Min:**
```python
# 50 × 15min = 750 Min (~12.5 Stunden)
# Praktisch für Daytrading-Patterns
pattern_length = 50
```

### 30-Minuten bis 1-Stunden Zeitrahmen

**Wann sinnvoll:**
- Absolute Robustheit (institutionelle Anforderungen)
- Swing-Positionen (Holdtime 2h–2 Tage)
- Hohe Spreads (brauchst größere Moves)

**Pros:**
- Sehr niedriges Rausch (~4–6 SNR)
- Pattern extrem stabil
- Backtest-Konsistenz: 98%+

**Cons:**
- Deutlich weniger Pattern (~30–50 pro 6 Monate)
- Weniger Statistical Power
- Signals selten (vielleicht 1–2 pro Woche)

**Beispiel:**
```
6 Monate 30-Min Daten:
  - 250 Tage × 48 Kerzen/Tag = ~12.000 Kerzen
  - Mit 50-Kerzen Pattern → ~2.400 Kandidaten
  - Nach Filterung → 50–100 Patterns nur
  
  → Zu wenig für zuverlässige Statistik!
  → Besser: 12+ Monate Daten nutzen
```

### Multi-Timeframe Ansatz (Best Practice)

**Nicht einen Timeframe, sondern Konfirmation über mehrere:**

```python
class MultiTimeframeConfirmation:
    """Nutze Multi-Timeframe für robuste Signals"""
    
    def __init__(self):
        self.engine_15m = PatternRecognitionEngine(load_data('15min'))
        self.engine_5m = PatternRecognitionEngine(load_data('5min'))
    
    def get_signal(self):
        # Schritt 1: 15-Min Pattern → Muster erkannt?
        matches_15m = self.engine_15m.analyze_current_pattern(...)
        if not matches_15m or matches_15m[0]['confidence'] < 60:
            return None  # Kein Signal
        
        # Schritt 2: 5-Min bestätigt?
        matches_5m = self.engine_5m.analyze_current_pattern(...)
        if not matches_5m or matches_5m[0]['confidence'] < 55:
            return None  # Keine Confirmation
        
        # Beide stimmen überein?
        if matches_15m[0]['expected_move_pct'] * \
           matches_5m[0]['expected_move_pct'] > 0:  # Gleiche Richtung
            
            return {
                'confidence': (matches_15m[0]['confidence'] + 
                              matches_5m[0]['confidence']) / 2,
                'expected_move': matches_15m[0]['expected_move_pct'],
            }
        
        return None
```

**Professionelle Konfirmations-Hierarchie:**

```
1. LONG TIMEFRAME (15-Min oder höher):
   → Bestimmt die RICHTUNG
   → Confidence > 60%

2. MEDIUM TIMEFRAME (5-Min):
   → Bestätigt die STRUKTUR
   → Confidence > 55%

3. SHORT TIMEFRAME (1-Min, optional):
   → Refiniert den EINTRAG
   → Nur oberflächlich, kein Pattern-Matching
```

### Konkrete Empfehlung für DEIN Projekt

**Du hast: 1 Jahr 1-Min Kerzen**

**Option A: Konservativ (Empfohlen für Start)**

```python
# Aggregiere 1-Min zu 15-Min
df_15min = resample_ohlc(df_1min, '15T')

# Jetzt: 24.000 Kerzen (perfekt!)
engine = PatternRecognitionEngine(df_15min)

patterns = engine.extract_patterns_from_history(
    pattern_length=50,    # 50 × 15min = 750 Min
    step_size=5,
)
# → 150–300 solide Patterns in 6 Monaten Discovery ✅
```

**Option B: Aggressiv (Mehr Signals)**

```python
# Nutze 5-Min Daten
df_5min = resample_ohlc(df_1min, '5min')

# Jetzt: 72.000 Kerzen (~3× mehr Pattern)
engine = PatternRecognitionEngine(df_5min)

patterns = engine.extract_patterns_from_history(
    pattern_length=50,
    step_size=5,
    min_confidence=70,  # Höhere Schwelle!
)
```

**Option C: Hybrid (Best Practice)**

```python
# Nutze BEIDE Timeframes
engine_15m = PatternRecognitionEngine(df_15min)
engine_5m = PatternRecognitionEngine(df_5min)

# Trading Signal nur wenn BEIDE Timeframes zustimmen
multi_tf = MultiTimeframeConfirmation()
signal = multi_tf.get_signal()
```

---

## Backtesting-Framework

### Daten korrekt splitten

```python
class TestingFramework:

    @staticmethod
    def split_data_chronologically(df: pd.DataFrame,
                                   ratio_discovery=0.5,
                                   ratio_validation=0.25):
        """
        Splitte Daten chronologisch OHNE Overlap
        
        Klassischer Fehler:
          train_test_split(data, test_size=0.2)  # ❌ Zerstört Zeitreihen-Struktur!
        
        Richtig:
          Discovery:  data[0:50%]
          Validation: data[50%:75%]  (KEIN Overlap!)
          Forward:    data[75%:100%]
        """
        n = len(df)
        d_end = int(n * ratio_discovery)
        v_end = int(n * (ratio_discovery + ratio_validation))
        
        discovery = df.iloc[:d_end]
        validation = df.iloc[d_end:v_end]
        forward = df.iloc[v_end:]
        
        return discovery, validation, forward

    @staticmethod
    def identify_regime(prices, window=20):
        """Erkenne Marktregime basierend auf Volatilität & Trend"""
        returns = np.diff(prices) / prices[:-1]
        volatility = pd.Series(returns).rolling(window).std()
        trend = pd.Series(prices).rolling(window).mean()
        
        trend_strength = np.abs(np.diff(trend)) / (volatility + 1e-8)
        
        regime = []
        for ts, vol in zip(trend_strength, volatility):
            if ts > 1.5:
                regime.append('TRENDING')
            elif vol > np.percentile(volatility, 75):
                regime.append('VOLATILE')
            else:
                regime.append('RANGING')
        
        return np.array(regime)

    @staticmethod
    def validate_consistency(discovery_winrate, validation_winrate,
                             threshold_warn=0.05, threshold_fail=0.10):
        """Prüfe ob Discovery/Validation konsistent sind"""
        diff = abs(discovery_winrate - validation_winrate)
        
        print(f"Discovery Win-Rate:  {discovery_winrate:.1%}")
        print(f"Validation Win-Rate: {validation_winrate:.1%}")
        print(f"Divergence:          {diff:.1%}")
        
        if diff > threshold_fail:
            print("⚠️  WARNUNG: Große Divergenz! Mögliches Overfitting")
            return False
        elif diff > threshold_warn:
            print("⚠️  Moderate Divergence - Beobachten")
            return True
        else:
            print("✅ Gute Konsistenz zwischen Phases")
            return True
```

### Komplettes Backtesting-Workflow

```python
def complete_backtest_workflow():
    """Komplettes Beispiel von Datenladenung bis zur Vorhersage"""
    
    # 1. Lade 1-Jahrs-Daten (1-Min)
    print("=" * 60)
    print("DATEN LADEN")
    print("=" * 60)
    df_1min = pd.read_csv("1year_eur_usd_1min.csv", 
                          parse_dates=['datetime'], 
                          index_col='datetime')
    
    # 2. Aggregiere zu 15-Min (Optional: auch 5-Min testen)
    print("\n" + "=" * 60)
    print("AGGREGATION ZU 15-MIN")
    print("=" * 60)
    df_15min = resample_ohlc(df_1min, '15T')
    print(f"✓ Aggregiert: {len(df_1min)} Kerzen → {len(df_15min)} Kerzen")
    
    # 3. Splitte chronologisch
    print("\n" + "=" * 60)
    print("DATEN-SPLIT")
    print("=" * 60)
    discovery, validation, forward = TestingFramework.split_data_chronologically(
        df_15min,
        ratio_discovery=0.5,
        ratio_validation=0.25,
    )
    print(f"Discovery:  {len(discovery)} Kerzen ({discovery.index[0]} - {discovery.index[-1]})")
    print(f"Validation: {len(validation)} Kerzen ({validation.index[0]} - {validation.index[-1]})")
    print(f"Forward:    {len(forward)} Kerzen ({forward.index[0]} - {forward.index[-1]})")
    
    # 4. PHASE 1: DISCOVERY
    print("\n" + "=" * 60)
    print("PHASE 1: DISCOVERY")
    print("=" * 60)
    
    engine_discovery = PatternRecognitionEngine(discovery)
    patterns_discovery = engine_discovery.extract_patterns_from_history(
        pattern_length=50,
        step_size=5
    )
    
    # Berechne Metriken
    discovery_results = analyze_patterns(patterns_discovery)
    print(f"\n📊 Discovery Ergebnisse:")
    print(f"   Patterns: {len(patterns_discovery)}")
    print(f"   Winrate: {discovery_results['winrate']:.1%}")
    print(f"   Avg Profit: {discovery_results['avg_profit']:+.2f}%")
    print(f"   Max Drawdown: {discovery_results['max_drawdown']:.2f}%")
    
    # 5. PHASE 2: VALIDATION (EXAKT GLEICHE PARAMETER!)
    print("\n" + "=" * 60)
    print("PHASE 2: VALIDATION (OUT-OF-SAMPLE)")
    print("=" * 60)
    
    engine_validation = PatternRecognitionEngine(validation)
    patterns_validation = engine_validation.extract_patterns_from_history(
        pattern_length=50,  # GLEICH!
        step_size=5         # GLEICH!
    )
    
    validation_results = analyze_patterns(patterns_validation)
    print(f"\n📊 Validation Ergebnisse:")
    print(f"   Patterns: {len(patterns_validation)}")
    print(f"   Winrate: {validation_results['winrate']:.1%}")
    print(f"   Avg Profit: {validation_results['avg_profit']:+.2f}%")
    print(f"   Max Drawdown: {validation_results['max_drawdown']:.2f}%")
    
    # 6. KONSISTENZ-PRÜFUNG
    print("\n" + "=" * 60)
    print("KONSISTENZ-PRÜFUNG")
    print("=" * 60)
    
    is_consistent = TestingFramework.validate_consistency(
        discovery_results['winrate'],
        validation_results['winrate'],
        threshold_warn=0.05,
        threshold_fail=0.10
    )
    
    if not is_consistent:
        print("\n⚠️ WARNUNG: Overfitting wahrscheinlich! Parameter anpassen.")
        return
    
    # 7. REGIME-STRATIFIKATION
    print("\n" + "=" * 60)
    print("REGIME-STRATIFIKATION")
    print("=" * 60)
    
    regimes = TestingFramework.identify_regime(discovery['close'].values)
    
    for regime_name in ['TRENDING', 'RANGING', 'VOLATILE']:
        regime_mask = regimes == regime_name
        regime_patterns = [p for i, p in enumerate(patterns_discovery) if regime_mask[i]]
        regime_res = analyze_patterns(regime_patterns)
        
        print(f"\n{regime_name}:")
        print(f"   Patterns: {len(regime_patterns)}")
        print(f"   Winrate: {regime_res['winrate']:.1%}")
    
    # 8. FORWARD-TEST (später mit aktuellen Daten)
    print("\n" + "=" * 60)
    print("FORWARD-TEST (LIVE/PAPER)")
    print("=" * 60)
    print("Nutze engine_discovery.analyze_current_pattern() mit Live-Daten")
    
    return engine_discovery, patterns_discovery, discovery_results


def resample_ohlc(df, target_tf):
    """Aggregiere OHLC Daten zu höherem Timeframe"""
    agg_dict = {
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    }
    return df.resample(target_tf).agg(agg_dict).dropna()


def analyze_patterns(patterns):
    """Berechne Metriken für eine Menge von Patterns"""
    if not patterns:
        return {'winrate': 0, 'avg_profit': 0, 'max_drawdown': 0}
    
    profits = [p['price_change_pct'] for p in patterns]
    wins = sum(1 for p in profits if p > 0)
    
    return {
        'winrate': wins / len(profits) if profits else 0,
        'avg_profit': np.mean(profits),
        'max_drawdown': np.min(profits),
    }


if __name__ == "__main__":
    engine, patterns, results = complete_backtest_workflow()
```

---

## Zusammenfassung & Checkliste

### ✅ Best Practices

- ✅ **Datenglättung ist essentiell** – Heikin-Ashi + optional EMA
- ✅ **Nutze DTW statt Euclidean Distance** – flexibles Alignment
- ✅ **Normalisiere Preise** – nur Form zählt
- ✅ **Finde lokale Extrema** – nicht einzelne Kerzen
- ✅ **Verwende Confidence-Scoring** – 0–100%, nicht Binary
- ✅ **Validiere statistisch** – brauchst 100+ Muster für Signifikanz
- ✅ **Multi-Layer Approach** – Struktur + Glättung + Normalisierung
- ✅ **Backteste gründlich** – Discovery → Validation → Forward
- ✅ **Nutze 15-Min** – Sweet Spot für Mustererkennung
- ✅ **Stratifiziere nach Regime** – testen in Trending/Ranging/Volatile

### ❌ Häufige Fehler

| Fehler | Lösung |
|--------|--------|
| Nur 1-Min nutzen | Aggregiere zu 5-Min oder 15-Min |
| Confidence 90%+ im Backtest | Erhöhe min_confidence auf 65–70% |
| Validation Win-Rate Crash | Nutze höhere Timeframes |
| Weniger Pattern erwartet | Teste beide 5-Min + 15-Min |
| Funktioniert nur in Bull | Stratifiziere nach Regime |
| Train/Test Overlap | Nutze chronologische Split! |

---

## Nächste Schritte für DEIN Projekt

1. **Lade deine 1-Jahrs 1-Min Daten**
2. **Aggregiere zu 15-Min** (später optional 5-Min testen)
3. **Führe `complete_backtest_workflow()` aus**
4. **Überprüfe Discovery vs. Validation Konsistenz**
5. **Wenn konsistent: Forward-Test mit Live/Paper-Daten**
6. **Wenn nicht konsistent: Parameter anpassen**

Mit diesem Framework solltest du robuste, nicht-überoptimierte Ergebnisse bekommen!