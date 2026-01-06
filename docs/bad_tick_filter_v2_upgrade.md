# Bad Tick Filter v2.0 - Upgrade zur Hampel-Filterung

**Datum:** 2026-01-06
**Status:** ✅ Implementiert, bereit für Test
**Problem:** Bad Ticks trotz v1.0 Filter immer noch sichtbar im Live-Chart
**Lösung:** Hampel-Filter mit Volumen-Bestätigung (aus RTF-Dokument)

---

## 🔥 Das Problem mit v1.0

**Deine Beobachtung:** "immer noch bad ticks vorhanden"

**Warum v1.0 NICHT funktionierte:**
```python
# v1.0 (alt) - Einfache Prozent-Abweichung
if abs(close - moving_average) / moving_average > 0.05:  # 5% Abweichung
    bad_tick = True  # ❌ Problem: Entfernt ALLE Spikes!
```

**Das Problem:**
- Crypto-Märkte sind volatil (BTC kann 5% in Minuten fallen)
- Einfache Prozent-Filter unterscheiden NICHT zwischen:
  - **Bad Tick** (technischer Fehler, kein Volumen)
  - **Flash Crash** (echter Market Move, hohes Volumen)
- Resultat: Filter war entweder zu streng (entfernt echte Moves) oder zu lasch (lässt Bad Ticks durch)

---

## ✅ Die Lösung: Hampel-Filter v2.0

**Quelle:** "Handbuch für Algorithmische Datenintegrität und KI.rtf"

### Die kritische Erkenntnis:

```python
is_bad_tick = is_price_outlier & (~is_high_volume)

# Ein Bad Tick ist: Preis-Outlier OHNE hohes Volumen
# Ein Flash Crash ist: Preis-Outlier MIT hohem Volumen → KEEP!
```

### Wie der Hampel-Filter funktioniert:

1. **Outlier-Erkennung mit MAD (Median Absolute Deviation)**
   - Statt Moving Average → Rolling Median (robuster gegen Outliers)
   - Statt Standard Deviation → MAD (nicht von Outliers beeinflusst)
   - Modified Z-Score: `mod_z = 0.6745 * (deviation / mad)`
   - Outlier = `mod_z > 3.5`

2. **Volumen-Bestätigung**
   - Rolling Median Volumen berechnen
   - High Volume Event = `volume > (median_volume * 10.0)`
   - Wenn Volumen 10x höher als Median → echter Market Move!

3. **Bad Tick Logik**
   ```python
   # Schritt 1: Ist der Preis ein Outlier?
   is_price_outlier = detect_outliers_mad(df, 'close')

   # Schritt 2: Ist das Volumen extrem hoch?
   vol_median = df['volume'].rolling(window=15).median()
   is_high_volume = df['volume'] > (vol_median * 10.0)

   # Schritt 3: Bad Tick = Outlier OHNE High Volume
   is_bad_tick = is_price_outlier & (~is_high_volume)

   # Resultat:
   # - Preis-Spike MIT hohem Volumen = Flash Crash → KEEP! ✅
   # - Preis-Spike OHNE hohes Volumen = Bad Tick → REMOVE! ❌
   ```

---

## 📝 Implementierte Änderungen

### 1. Neue Klasse in `src/analysis/data_cleaning.py`

```python
class HampelBadTickDetector:
    """Advanced bad tick detector using Hampel Filter with Volume Confirmation."""

    def __init__(
        self,
        window: int = 15,          # 15-Bar Rolling Window
        threshold: float = 3.5,    # MAD-Threshold für Outliers
        vol_filter_mult: float = 10.0  # Volumen-Multiplikator
    ):
        ...

    def detect_outliers_mad(self, df, col='close') -> pd.Series:
        """MAD-basierte Outlier-Erkennung."""
        rolling_median = df[col].rolling(window=self.window).median()
        deviation = np.abs(df[col] - rolling_median)
        mad = deviation.rolling(window=self.window).median()
        mod_z = 0.6745 * (deviation / mad)
        return mod_z > self.threshold

    def detect_bad_ticks(self, df) -> pd.Series:
        """Bad Tick = Outlier WITHOUT High Volume."""
        is_price_outlier = self.detect_outliers_mad(df, 'close')
        vol_median = df['volume'].rolling(window=self.window).median()
        is_high_volume = df['volume'] > (vol_median * self.vol_filter_mult)
        is_bad_tick = is_price_outlier & (~is_high_volume)
        return is_bad_tick
```

### 2. Alle 3 Datenquellen aktualisiert

**Live-Streaming:** `src/core/market_data/alpaca_crypto_stream.py`
```python
detector = HampelBadTickDetector(
    window=15,
    threshold=3.5,
    vol_filter_mult=10.0,
)
self._bad_tick_filter = StreamBadTickFilter(detector, window_size=100)
```

**Database:** `src/core/market_data/providers/database_provider.py`
```python
self.bad_tick_detector = HampelBadTickDetector(
    window=15,
    threshold=3.5,
    vol_filter_mult=10.0,
)
```

**API:** `src/core/market_data/alpaca_crypto_provider.py`
```python
self.bad_tick_detector = HampelBadTickDetector(
    window=15,
    threshold=3.5,
    vol_filter_mult=10.0,
)
```

### 3. Dokumentation aktualisiert

- `docs/bad_tick_filter_deployment.md` → v2.0
- Changelog mit v1.0 vs v2.0 Vergleich
- Erklärung warum v1.0 nicht funktionierte

---

## 🧪 Testen

### Schritt 1: App neu starten (WICHTIG!)

```bash
# 1. Alle Python-Prozesse beenden
# 2. App komplett neu starten
# 3. Chart laden (BTC/USD, 1min, Live)
```

### Schritt 2: Logs prüfen

Beim App-Start solltest du sehen:
```
🛡️  Hampel Filter with Volume Confirmation initialized (window=15, threshold=3.5, vol_mult=10x)
```

Im Live-Betrieb (wenn Bad Tick erkannt wird):
```
🚫 BAD TICK REJECTED: Price spike detected | BTC/USD @ 2026-01-06 19:00:00 | O:94000 H:1000 L:900 C:950
🔍 Hampel Filter: 1 bad ticks detected (outliers: 1, high-vol events: 0, bad ticks: 1)
```

### Schritt 3: Chart beobachten

- **Erwartetes Resultat:** Keine extreme Spikes mehr (wie $94k → $0.01)
- **Aber:** Echte Flash Crashes MIT hohem Volumen sollten SICHTBAR bleiben!

---

## 📊 Beispiele

### ✅ Szenario 1: Bad Tick (wird entfernt)

```
Timestamp: 2026-01-06 19:05:00
Open: 94500
High: 1000  ← ❌ Unrealistisch
Low: 900    ← ❌ Unrealistisch
Close: 950  ← ❌ Unrealistisch
Volume: 100 BTC (Median: 50 BTC)

→ is_price_outlier = True (Close weicht massiv ab)
→ is_high_volume = False (100 < 500)
→ is_bad_tick = True → REMOVE ❌
```

### ✅ Szenario 2: Flash Crash (wird behalten)

```
Timestamp: 2026-01-06 19:06:00
Open: 94500
High: 94500
Low: 80000  ← Flash Crash!
Close: 82000
Volume: 1000 BTC (Median: 50 BTC) ← ⚠️ Extrem hoch!

→ is_price_outlier = True (Close weicht massiv ab)
→ is_high_volume = True (1000 > 500)
→ is_bad_tick = False → KEEP ✅ (echter Market Event!)
```

---

## 🎯 Parameter-Tuning (falls nötig)

### Falls zu viele Bars gefiltert werden:

```python
# In allen 3 Dateien ändern:
HampelBadTickDetector(
    window=15,
    threshold=4.0,  # Von 3.5 auf 4.0 erhöhen (weniger streng)
    vol_filter_mult=8.0,  # Von 10 auf 8 senken (mehr High-Vol Events)
)
```

### Falls immer noch Bad Ticks durchkommen:

```python
# In allen 3 Dateien ändern:
HampelBadTickDetector(
    window=20,  # Mehr Kontext (20 statt 15)
    threshold=3.0,  # Strenger (3.0 statt 3.5)
    vol_filter_mult=15.0,  # Strenger Volume-Check (15x statt 10x)
)
```

---

## 🔧 Troubleshooting

### Problem: Filter funktioniert nicht

**Lösung:**
1. App **komplett** neu starten (alle Python-Prozesse beenden)
2. Logs prüfen: `grep "Hampel Filter" logs/orderpilot.log`
3. Sicherstellen dass v2.0 verwendet wird (nicht v1.0)

### Problem: Zu viele Bars werden entfernt

**Ursache:** Threshold zu niedrig oder vol_filter_mult zu hoch

**Lösung:**
```python
threshold=4.5,  # Erhöhen (4.5 oder 5.0 für volatile Märkte)
vol_filter_mult=8.0,  # Senken (mehr Events als "high volume" akzeptieren)
```

### Problem: Chart zeigt keine Daten

**Ursache:** Alle Bars wurden gefiltert (zu aggressiv)

**Lösung:** Filter temporär komplett deaktivieren:
```python
# In alpaca_crypto_stream.py:
# Kommentiere die Filter-Initialisierung aus und teste
```

---

## ✅ Erwartetes Ergebnis

Nach App-Neustart sollten:
- ✅ Keine extreme Bad Ticks mehr sichtbar sein ($94k → $0.01)
- ✅ Echte Flash Crashes MIT hohem Volumen SICHTBAR bleiben
- ✅ Logs zeigen gefilterte Bad Ticks
- ✅ Chart ist stabil und realistisch

---

**Nächster Schritt:** App neu starten und testen! 🚀
