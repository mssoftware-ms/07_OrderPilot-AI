# Download Progress Bar & Timeframe Fix

## Problem 1: Progress Bar bleibt bei 20% stehen

### Symptom
- Progress Bar springt auf 5% (Database init)
- Springt auf 10% (Provider init)
- Springt auf 20% (Start download)
- **Bleibt dann bei 20% stehen während des gesamten Downloads**

### Root Cause

**Datei:** `src/ui/workers/historical_download_worker.py`

Der `make_progress_callback()` verwendete nur einen **konstanten** `base_pct` Wert:

```python
# ❌ VORHER (FALSCH)
def make_progress_callback(sym: str, base_pct: int):
    def callback(batch_num: int, total_bars: int, status_msg: str):
        # base_pct bleibt KONSTANT!
        self.progress.emit(base_pct, f"{sym}: {status_msg}")
    return callback
```

**Problem:**
- `base_pct` = 20 (fix)
- `batch_num` wurde ignoriert
- Keine Berechnung basierend auf geschätzten Batches

### Fix

**Neue Implementierung:**

```python
# ✅ NACHHER (KORREKT)
# 1. Berechne geschätzte Batches basierend auf Timeframe
bars_per_day = {
    "1min": 1440,
    "5min": 288,
    "15min": 96,
    "1h": 24,
    "4h": 6,
    "1d": 1,
}
bpd = bars_per_day.get(self.timeframe, 1440)
total_bars_estimated = self.days * bpd
estimated_batches = max(1, (total_bars_estimated // 200) + 1)  # 200 bars per batch

# 2. Progress-Callback mit echter Berechnung
def make_progress_callback(sym: str, start_pct: int, pct_range: int, est_batches: int):
    def callback(batch_num: int, total_bars: int, status_msg: str):
        # Berechne Progress basierend auf batch_num
        batch_progress = min(99, int((batch_num / est_batches) * pct_range))
        current_pct = start_pct + batch_progress
        self.progress.emit(current_pct, f"{sym}: {status_msg}")
    return callback
```

**Formel:**
```
current_pct = start_pct + (batch_num / estimated_batches) * pct_range

Beispiel (365 Tage, 1min):
- estimated_batches = (365 * 1440 / 200) + 1 = 2,629
- start_pct = 20
- pct_range = 70
- batch_num = 1,000
  → current_pct = 20 + (1000 / 2629) * 70 = 46.6%
```

### Neue Progress-Schritte

| Phase | Progress | Beschreibung |
|-------|----------|--------------|
| Database Init | 5% | Datenbank initialisieren |
| Provider Init | 10-15% | Provider erstellen |
| Download Start | 20% | Download starten |
| **Batch Download** | **20-90%** | **Jeder Batch aktualisiert Progress** |
| OHLC Validation | 95% | Automatische Validierung |
| Complete | 100% | Fertig |

**Beispiel-Log:**
```
📊 Download estimates: 525,600 bars, ~2,629 batches
BTCUSDT: Batch 1: 200 Bars geladen, aktuell bei 17.01.2026 14:20    [20%]
BTCUSDT: Batch 100: 20,000 Bars geladen, aktuell bei 15.01.2026 08:45  [22%]
BTCUSDT: Batch 500: 100,000 Bars geladen, aktuell bei 28.12.2025 16:30 [33%]
BTCUSDT: Batch 1000: 200,000 Bars geladen, aktuell bei 10.11.2025 09:15 [46%]
...
BTCUSDT: Batch 2629: 525,600 Bars geladen, aktuell bei 18.01.2025 00:00 [90%]
Validating OHLC data quality...                                          [95%]
✅ Auto-fixed 22 OHLC inconsistencies                                    [100%]
```

---

## Problem 2: Timeframe-Quelle unklar

### Symptom
User vermutet, dass Download die Timeframe-Einstellung vom **Chart-Fenster** nimmt statt vom **Settings-Dialog**.

### Analyse

**Code-Trace:**

1. **Settings Dialog** (`settings_tabs_bitunix.py:241`):
   ```python
   timeframe = self.parent.bitunix_dl_timeframe.currentText()
   # ✅ Kommt vom QComboBox im Settings-Tab
   ```

2. **Worker Creation** (`settings_tabs_bitunix.py:245-249`):
   ```python
   self._bitunix_download_worker = HistoricalDownloadWorker(
       provider_type="bitunix",
       symbols=[symbol],
       days=days,
       timeframe=timeframe,  # ✅ Wird korrekt übergeben
       mode=mode,
       enable_bad_tick_filter=enable_filter,
   )
   ```

3. **Worker Init** (`historical_download_worker.py:31`):
   ```python
   self.timeframe = timeframe  # ✅ Wird gespeichert
   ```

**Ergebnis:** Code ist korrekt - Timeframe kommt vom Settings-Dialog.

### Fix: Debug-Logging hinzugefügt

Um sicherzustellen und dem User Transparenz zu geben, wurden **detaillierte Logs** hinzugefügt:

```python
logger.info("=" * 80)
logger.info("🚀 DOWNLOAD WORKER STARTED")
logger.info("=" * 80)
logger.info(f"📊 Provider:        {self.provider_type}")
logger.info(f"📊 Symbols:         {', '.join(self.symbols)}")
logger.info(f"📊 Timeframe STR:   '{self.timeframe}' (from Settings UI)")
logger.info(f"📊 Days back:       {self.days}")
logger.info(f"📊 Mode:            {self.mode}")
logger.info(f"📊 Bad tick filter: {self.enable_bad_tick_filter}")
logger.info("=" * 80)

# Map to enum
tf = timeframe_map.get(self.timeframe, Timeframe.MINUTE_1)

logger.info(f"📊 Timeframe ENUM:  {tf.value} (mapped from '{self.timeframe}')")
if self.timeframe not in timeframe_map:
    logger.warning(f"⚠️ Unknown timeframe '{self.timeframe}', defaulting to 1min!")
logger.info("=" * 80)
```

**Beispiel-Output:**
```
================================================================================
🚀 DOWNLOAD WORKER STARTED
================================================================================
📊 Provider:        bitunix
📊 Symbols:         BTCUSDT
📊 Timeframe STR:   '1min' (from Settings UI)
📊 Days back:       365
📊 Mode:            download
📊 Bad tick filter: True
================================================================================
📊 Timeframe ENUM:  1min (mapped from '1min')
================================================================================
```

### Zusätzliche Logs im Bitunix-Download

```python
logger.info(f"📥 Starting full download for {symbol}")
logger.info(f"   Timeframe: {self.timeframe} → {timeframe.value}")
logger.info(f"   Days back: {self.days}")
logger.info(f"   Estimated batches: ~{estimated_batches:,}")
```

---

## Testing

### Test 1: Progress Bar (1min, 7 Tage)

1. Settings → Bitunix
2. Symbol: BTCUSDT
3. Period: 7 days
4. Timeframe: **1min**
5. Click "Download Full History"

**Erwartung:**
```
[  5%] Initializing database...
[ 10%] Using public Bitunix API...
[ 20%] Downloading BTCUSDT...
[ 21%] BTCUSDT: Batch 1: 200 Bars geladen...
[ 22%] BTCUSDT: Batch 10: 2,000 Bars geladen...
...
[ 89%] BTCUSDT: Batch 50: 10,080 Bars geladen...
[ 95%] Validating OHLC data quality...
[100%] Download complete!
```

**Estimated Batches:**
- 7 days × 1440 bars/day = 10,080 bars
- 10,080 / 200 = 51 batches

### Test 2: Progress Bar (5min, 365 Tage)

**Erwartung:**
```
Estimated batches: ~526
Progress: 20% → 25% → 35% → 50% → 70% → 90% → 95% → 100%
```

### Test 3: Timeframe-Logging

**Check Logs:**
```
📊 Timeframe STR:   '1min' (from Settings UI)
📊 Timeframe ENUM:  1min (mapped from '1min')
   Timeframe: 1min → 1min
```

**Falls Timeframe falsch:**
```
📊 Timeframe STR:   '5min' (from Settings UI)
⚠️ Chart zeigt aber 1min Daten!
→ User hat falsche Einstellung im Settings-Tab
```

---

## Zusammenfassung

### ✅ Problem 1: Progress Bar - GELÖST

**Vorher:**
- Progress bei 20% stehen geblieben
- Keine Feedback während Download
- User weiß nicht wie lange es dauert

**Nachher:**
- Berechnet `estimated_batches` präzise
- Progress aktualisiert sich kontinuierlich (20-90%)
- User sieht aktuellen Fortschritt und Batch-Nummer

### ✅ Problem 2: Timeframe - VERIFIZIERT

**Analyse:**
- Code ist korrekt, Timeframe kommt vom Settings-Dialog
- **Keine Änderung nötig**

**Verbesserung:**
- Detaillierte Logs zeigen Timeframe-Quelle
- User kann im Log verifizieren welcher Timeframe verwendet wird

---

## Geänderte Dateien

| Datei | Änderung |
|-------|----------|
| `src/ui/workers/historical_download_worker.py` | ✅ Progress-Berechnung, Debug-Logs |
| `docs/fixes/download-progress-fix.md` | ✅ Diese Dokumentation |

---

**Status:** ✅ Implementiert in Version 2025-01-17
