# Aggressive Hampel Filter Parameters

Wenn der Hampel-Filter mit Standard-Parametern Bad Ticks nicht entfernt, verwende diese aggressiveren Einstellungen:

## Problem-Analyse

Die Bad Ticks im Chart zeigen:
1. **Extreme Spikes nach oben** (von ~$95k auf weit über Chart-Bereich)
2. **Hohe rote Kerzen** (unrealistische Preisbewegungen)

Diese sollten DEFINITIV als Bad Ticks erkannt werden!

## Mögliche Ursachen

1. **Filter wird nicht verwendet** (alte Version läuft noch)
2. **Threshold zu hoch** (3.5 ist zu lenient für extreme Spikes)
3. **Volume ist zu hoch** (Bad Ticks werden als "high volume events" fehlinterpretiert)
4. **Window zu klein** (15 Bars reichen nicht für Kontext)

## Lösung 1: EXTREME Parameter

Ändere in **ALLEN 3 Dateien**:
- `src/core/market_data/alpaca_crypto_stream.py`
- `src/core/market_data/providers/database_provider.py`
- `src/core/market_data/alpaca_crypto_provider.py`

```python
detector = HampelBadTickDetector(
    window=20,  # Mehr Kontext (20 statt 15)
    threshold=2.0,  # VIEL strenger (2.0 statt 3.5)
    vol_filter_mult=50.0,  # VIEL höhere Volume-Anforderung (50x statt 10x)
)
```

**Erklärung:**
- `threshold=2.0`: Erkennt bereits kleinere Abweichungen als Outlier
- `vol_filter_mult=50.0`: Nur wenn Volumen 50x höher als Median ist, wird es als "echter Crash" akzeptiert
- `window=20`: Mehr historischer Kontext für bessere MAD-Berechnung

## Lösung 2: OHLC-Only Mode (Fallback)

Falls auch das nicht hilft, verwende einen SIMPLEN OHLC-Filter ohne MAD:

```python
# In allen 3 Dateien, vor dem HampelBadTickDetector:

# TEMPORARY FIX: Use simple OHLC + extreme price filter
class SimpleAggressiveFilter:
    """Ultra-aggressive bad tick filter as fallback."""

    def detect_bad_ticks(self, df):
        bad = pd.Series(False, index=df.index)

        # 1. OHLC consistency
        bad |= df['high'] < df['low']
        bad |= (df['open'] < df['low']) | (df['open'] > df['high'])
        bad |= (df['close'] < df['low']) | (df['close'] > df['high'])

        # 2. Zero/negative prices
        for col in ['open', 'high', 'low', 'close']:
            bad |= df[col] <= 0

        # 3. EXTREME price deviation (>20% from previous bar)
        prev_close = df['close'].shift(1)
        deviation_pct = ((df['close'] - prev_close) / prev_close * 100).abs()
        bad |= deviation_pct > 20.0  # >20% change = bad tick

        return bad

# Use this instead:
self.bad_tick_detector = SimpleAggressiveFilter()
```

## Lösung 3: Debug-Output aktivieren

Füge temporär Debug-Output hinzu um zu sehen WAS der Filter sieht:

In `alpaca_crypto_stream.py`, Zeile ~302 (in `_on_bar`):

```python
# BEFORE filter check, add this:
logger.error(f"🔍 INCOMING BAR: {bar.symbol} @ {bar.timestamp} | O:{bar.open} H:{bar.high} L:{bar.low} C:{bar.close} V:{bar.volume}")

# Then the existing filter:
is_valid, rejection_reason = self._bad_tick_filter.filter_bar(bar_dict)
if not is_valid:
    logger.error(f"🚫 BAD TICK REJECTED: {rejection_reason}")
    self.metrics.messages_dropped += 1
    return
else:
    logger.error(f"✅ BAR ACCEPTED")  # ADD THIS to see what passes through
```

Dann in den Logs sehen wir:
- Welche Bars ankommen
- Welche gefiltert werden
- Welche durchgelassen werden

---

## Sofort-Test

Erstelle Test-Datei um zu prüfen ob extreme Spikes erkannt werden:

```python
# test_extreme_spike.py
import pandas as pd
from src.analysis.data_cleaning import HampelBadTickDetector

# Simulate extreme spike like in your chart
data = {
    'timestamp': pd.date_range('2026-01-06 19:00', periods=100, freq='1min'),
    'open': [95000] * 100,
    'high': [95500] * 50 + [1000000] + [95500] * 49,  # EXTREME spike
    'low': [94500] * 100,
    'close': [95000] * 100,
    'volume': [50] * 100,
}
df = pd.DataFrame(data)

# Test with current parameters
detector = HampelBadTickDetector(window=15, threshold=3.5, vol_filter_mult=10.0)
bad_mask = detector.detect_bad_ticks(df)

print(f"Bad ticks detected: {bad_mask.sum()}")
print(f"Spike at index 50 detected? {bad_mask.iloc[50]}")

if not bad_mask.iloc[50]:
    print("❌ CURRENT PARAMETERS DON'T WORK!")
    print("Trying aggressive parameters...")

    detector_aggressive = HampelBadTickDetector(window=20, threshold=2.0, vol_filter_mult=50.0)
    bad_mask_aggressive = detector_aggressive.detect_bad_ticks(df)

    print(f"Aggressive: Bad ticks detected: {bad_mask_aggressive.sum()}")
    print(f"Aggressive: Spike at index 50 detected? {bad_mask_aggressive.iloc[50]}")
```

**Run it:**
```bash
PYTHONPATH=/mnt/d/03_GIT/02_Python/07_OrderPilot-AI python test_extreme_spike.py
```

---

## Checkliste für dich:

- [ ] **App komplett neu gestartet?** (alle Python-Prozesse beendet)
- [ ] **Logs prüfen:** `bash scripts/check_filter_status.sh`
- [ ] **Welche Filter-Version läuft?** (Hampel v2.0 oder alter v1.0?)
- [ ] **Werden Bad Ticks rejected?** (Logs zeigen "BAD TICK REJECTED"?)
- [ ] **Test-Script laufen lassen:** `python test_extreme_spike.py`

**Sende mir bitte:**
1. Output von `bash scripts/check_filter_status.sh`
2. Die letzten 50 Zeilen aus `logs/orderpilot.log`

Dann kann ich genau sehen was das Problem ist!
