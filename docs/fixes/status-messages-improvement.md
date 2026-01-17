# Status Messages Improvement - Download UI

## Problem

User sieht während des Downloads keine Statusmeldungen im Label unter der Progress Bar:
- Keine Info über Datenbank-Initialisierung
- Keine Info über Löschen alter Daten
- Keine Info über Download-Fortschritt

## Fix

### 1. Worker Status Messages (mit Emojis)

**Datei:** `src/ui/workers/historical_download_worker.py`

| Progress | Status Message | Beschreibung |
|----------|----------------|--------------|
| 5% | 📂 Initializing database... | Datenbank wird vorbereitet |
| 8% | ✅ Database ready | Datenbank bereit |
| 10% | 🔧 Creating bitunix provider... | Provider wird erstellt |
| 15% | 🌐 Using public Bitunix API... | Bestätigung: Public API |
| 20% | 📊 Preparing download for BTCUSDT... | Download-Vorbereitung |
| 20% | 🚀 Starting download for BTCUSDT... | Download startet |

### 2. Manager Deletion Messages

**Datei:** `src/core/market_data/bitunix_historical_data_manager.py`

| Status Message | Wann | Beschreibung |
|----------------|------|--------------|
| 🗑️ Deleting existing data for BTCUSDT... | Vor Delete | Löschvorgang startet |
| ✅ Deleted 802 old bars, starting download... | Nach Delete (Daten vorhanden) | X Bars gelöscht |
| ✅ No old data found, starting fresh download... | Nach Delete (keine Daten) | Fresh Download |

### 3. Download Progress Messages

**Während des Downloads** (vom BitunixProvider):

```
BTCUSDT: Batch 1: 200 Bars geladen, aktuell bei 17.01.2026 14:20
BTCUSDT: Batch 10: 2,000 Bars geladen, aktuell bei 16.01.2026 08:45
BTCUSDT: Batch 100: 20,000 Bars geladen, aktuell bei 10.01.2026 16:30
...
BTCUSDT: Batch 2629: 525,600 Bars geladen, aktuell bei 18.01.2025 00:00
```

### 4. OHLC Validation Messages

| Progress | Status Message | Beschreibung |
|----------|----------------|--------------|
| 92% | 🔍 Validating OHLC data quality... | Validation startet |
| 95% | ✅ Fixed 22 OHLC inconsistencies | Fehler gefunden & korrigiert |
| 95% | ✅ All OHLC data valid | Keine Fehler gefunden |

### 5. Completion Messages

| Progress | Status Message | Beschreibung |
|----------|----------------|--------------|
| 98% | 🎉 Finalizing... | Fast fertig |
| 100% | ✅ Download complete! | Abgeschlossen |

---

## Vollständiger Ablauf

### Szenario: 365 Tage, 1min, BTCUSDT (mit alten Daten in DB)

**Progress Bar & Status Label:**

```
[  5%] 📂 Initializing database...
[  8%] ✅ Database ready
[ 10%] 🔧 Creating bitunix provider...
[ 15%] 🌐 Using public Bitunix API (no keys required)...
[ 20%] 📊 Preparing download for BTCUSDT...
[ 20%] 🚀 Starting download for BTCUSDT...
[ 20%] 🗑️ Deleting existing data for BTCUSDT...
[ 20%] ✅ Deleted 802 old bars, starting download...
[ 21%] BTCUSDT: Batch 1: 200 Bars geladen, aktuell bei 17.01.2026 14:20
[ 22%] BTCUSDT: Batch 100: 20,000 Bars geladen, aktuell bei 15.01.2026 08:45
[ 33%] BTCUSDT: Batch 500: 100,000 Bars geladen, aktuell bei 28.12.2025 16:30
[ 46%] BTCUSDT: Batch 1000: 200,000 Bars geladen, aktuell bei 10.11.2025 09:15
...
[ 90%] BTCUSDT: Batch 2629: 525,600 Bars geladen, aktuell bei 18.01.2025 00:00
[ 92%] 🔍 Validating OHLC data quality...
[ 95%] ✅ Fixed 22 OHLC inconsistencies
[ 98%] 🎉 Finalizing...
[100%] ✅ Download complete!
```

**Erfolgs-Dialog:**
```
Downloaded 525,600 bars for 1 symbol(s)
✅ Auto-fixed 22 OHLC inconsistencies
```

---

## Geänderte Dateien

| Datei | Änderung | Beschreibung |
|-------|----------|--------------|
| `src/ui/workers/historical_download_worker.py` | ✅ ERWEITERT | + Emojis, + mehr Status-Updates |
| `src/core/market_data/bitunix_historical_data_manager.py` | ✅ ERWEITERT | + Delete-Messages mit Count |
| `src/core/market_data/bitunix_historical_data_db.py` | ✅ ERWEITERT | Delete gibt jetzt Count zurück |

---

## Code-Änderungen im Detail

### Worker Messages

```python
# Vorher
self.progress.emit(5, "Initializing database...")
self.progress.emit(10, "Creating bitunix provider...")

# Nachher
self.progress.emit(5, "📂 Initializing database...")
self.progress.emit(8, "✅ Database ready")
self.progress.emit(10, "🔧 Creating bitunix provider...")
self.progress.emit(15, "🌐 Using public Bitunix API...")
self.progress.emit(20, "📊 Preparing download for BTCUSDT...")
```

### Manager Deletion

```python
# Vorher
await self._db_handler.delete_symbol_data(db_symbol)
logger.info(f"Deleted data for {db_symbol}")

# Nachher
if progress_callback:
    progress_callback(0, 0, f"🗑️ Deleting existing data for {symbol}...")

deleted_count = await self._db_handler.delete_symbol_data(db_symbol)

if progress_callback:
    if deleted_count > 0:
        progress_callback(0, 0, f"✅ Deleted {deleted_count:,} old bars, starting download...")
    else:
        progress_callback(0, 0, f"✅ No old data found, starting fresh download...")
```

### Database Return Value

```python
# Vorher
async def delete_symbol_data(self, db_symbol: str) -> None:
    await self.db.run_in_executor(...)

# Nachher
async def delete_symbol_data(self, db_symbol: str) -> int:
    return await self.db.run_in_executor(...)
    # Returns: Number of bars deleted
```

---

## Testing

**Test 1: Fresh Download (keine alten Daten)**
1. Neue Datenbank oder neues Symbol
2. Starte Download
3. **Erwartung:** `✅ No old data found, starting fresh download...`

**Test 2: Update Download (mit alten Daten)**
1. Symbol bereits in DB (z.B. 802 Bars)
2. Starte Download erneut
3. **Erwartung:** `✅ Deleted 802 old bars, starting download...`

**Test 3: Status Label Updates**
1. Beobachte Status-Label während Download
2. **Erwartung:**
   - Emojis sichtbar ✅
   - Messages ändern sich kontinuierlich ✅
   - Batch-Nummer wird aktualisiert ✅
   - Datum des aktuellen Batches sichtbar ✅

---

## Vorher / Nachher

### Vorher ❌
```
[  5%] Initializing database...
[ 10%] Creating provider...
[ 20%] Downloading...
[ 20%] (keine weiteren Updates)
...
(User weiß nicht was passiert)
```

### Nachher ✅
```
[  5%] 📂 Initializing database...
[  8%] ✅ Database ready
[ 10%] 🔧 Creating bitunix provider...
[ 15%] 🌐 Using public Bitunix API...
[ 20%] 📊 Preparing download for BTCUSDT...
[ 20%] 🚀 Starting download for BTCUSDT...
[ 20%] 🗑️ Deleting existing data for BTCUSDT...
[ 20%] ✅ Deleted 802 old bars, starting download...
[ 21%] BTCUSDT: Batch 1: 200 Bars geladen...
[ 22%] BTCUSDT: Batch 100: 20,000 Bars geladen...
...
[ 92%] 🔍 Validating OHLC data quality...
[ 95%] ✅ Fixed 22 OHLC inconsistencies
[100%] ✅ Download complete!
```

---

**Status:** ✅ Implementiert in Version 2025-01-17
