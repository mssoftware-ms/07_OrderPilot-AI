# Data Quality Fixes - OrderPilot-AI

## Problem 1: Fallback zu anderen Providern trotz expliziter Provider-Auswahl

### Symptom
- User wählt explizit "Bitunix" als Provider
- System versucht trotzdem Alpaca Crypto als Fallback
- Fehlermeldung: `"invalid symbol: BTCUSDT does not match ^[A-Z]+/[A-Z]+$"`

### Root Cause
- Alpaca Crypto erwartet Symbol-Format `BTC/USD` (mit Slash)
- Bitunix nutzt Format `BTCUSDT` (ohne Slash)
- `history_provider_fetching.py` hatte Fallback-Logik auch bei expliziter Provider-Wahl

### Fix
**Datei:** `src/core/market_data/history_provider_fetching.py`

1. **Kein Fallback bei expliziter Provider-Wahl:**
   ```python
   # CRITICAL FIX: If specific source is requested, ONLY try that source (no fallback)
   if request.source:
       bars, source_used = await self._try_specific_source(request)
       if bars:
           return bars, source_used
       # No fallback - user explicitly requested this source
       logger.error(f"Failed to get data from requested source {request.source.value}")
       return [], "none"
   ```

2. **Error Dialogs für User Feedback:**
   - Neue Datei: `src/ui/dialogs/error_dialog.py`
   - Zeigt Popup bei Provider-Fehlern
   - User sieht sofort, was schiefgelaufen ist

### Testing
```bash
# 1. Wähle Bitunix als Provider
# 2. Lade BTCUSDT
# 3. Erwartung: Nur Bitunix wird versucht, kein Fallback zu Alpaca
```

---

## Problem 2: Kerzen ohne Körper/Docht im Chart (1min/5min Timeframes)

### Symptom
- Charts zeigen Kerzen ohne Körper (Open = Close)
- Kerzen ohne Docht (High = Open/Close, Low = Open/Close)
- Besonders auffällig in 1min und 5min Charts

### Root Cause Analysis

#### Schritt 1: Datenbank-Analyse
```sql
-- Prüfung auf OHLC-Inkonsistenzen
SELECT COUNT(*) FROM market_bars
WHERE symbol = 'BTCUSDT'
  AND (high < open OR high < close OR low > open OR low > close);
-- Ergebnis: 22 fehlerhafte Bars
```

#### Schritt 2: Detailanalyse
```python
# Beispiel fehlerhafte Kerze:
# O=95289.10, H=95289.00, L=95245.50, C=95245.60
# Problem: High (95289.00) < Open (95289.10)
# Abweichung: 0.10 (Rundungsfehler von Bitunix API)
```

#### Schritt 3: Lightweight-Charts Validierung
Recherche in [TradingView Lightweight-Charts Issues](https://github.com/tradingview/lightweight-charts/issues):
- Lightweight-Charts erwartet: `high >= max(open, close)` und `low <= min(open, close)`
- Verletzung dieser Regel → Kerze wird nicht korrekt gerendert
- Siehe: [Candles have disappeared](https://www.tradingview.com/support/solutions/43000472764-candles-have-disappeared-from-the-chart/)

### Fix

**1. Prävention: Bitunix Provider OHLC Validation**

**Datei:** `src/core/market_data/providers/bitunix_provider.py`

```python
def _parse_klines(self, data: dict, symbol: str) -> list[HistoricalBar]:
    # Parse OHLC values
    o = Decimal(str(kline['open']))
    h = Decimal(str(kline['high']))
    l = Decimal(str(kline['low']))
    c = Decimal(str(kline['close']))

    # CRITICAL FIX: Validate and correct OHLC consistency
    corrected_high = max(o, h, c)
    corrected_low = min(o, l, c)

    if h != corrected_high or l != corrected_low:
        logger.debug(f"OHLC validation fix: {symbol} @ {timestamp}")

    bar = HistoricalBar(
        timestamp=timestamp,
        open=o,
        high=corrected_high,  # ✅ Use validated high
        low=corrected_low,    # ✅ Use validated low
        close=c,
        volume=volume,
        source="bitunix"
    )
```

**Effekt:** Alle neuen Daten von Bitunix werden automatisch validiert und korrigiert.

**2. Reparatur: Datenbank-Fix Tool**

**Datei:** `tools/fix_ohlc_database.py`

```bash
# Dry Run (zeigt Probleme ohne zu ändern)
python tools/fix_ohlc_database.py --dry-run --symbol BTCUSDT

# Apply Fix (erstellt Backup und korrigiert)
python tools/fix_ohlc_database.py --apply --symbol BTCUSDT

# Fix für alle Symbole
python tools/fix_ohlc_database.py --apply
```

**Beispiel Output:**
```
Found 22 bars with OHLC inconsistencies:

2026-01-17 04:30:00 | BTCUSDT | high < open (95289.00 < 95289.10)
  Before: O=95289.10 H=95289.00 L=95245.50 C=95245.60
  After:  O=95289.10 H=95289.10 L=95245.50 C=95245.60

✅ Backup created: data/orderpilot_backup_20260117_143022.db
✅ Fixed 22 bars!
```

### Testing

**Test 1: Neue Daten (Bitunix Provider)**
```bash
# 1. Lösche alte BTCUSDT Daten aus DB
# 2. Lade BTCUSDT neu von Bitunix
# 3. Prüfe: python tools/fix_ohlc_database.py --dry-run --symbol BTCUSDT
# Erwartung: "No OHLC inconsistencies found!"
```

**Test 2: Chart Rendering**
```bash
# 1. Öffne Chart für BTCUSDT
# 2. Wähle 1min Timeframe
# 3. Prüfe: Alle Kerzen haben Körper UND Docht (sofern Preisbewegung vorhanden)
```

**Test 3: Bestehende Daten (Datenbank-Fix)**
```bash
# 1. Vor Fix: python tools/fix_ohlc_database.py --dry-run --symbol BTCUSDT
# 2. Apply: python tools/fix_ohlc_database.py --apply --symbol BTCUSDT
# 3. Nach Fix: python tools/fix_ohlc_database.py --dry-run --symbol BTCUSDT
# Erwartung: "No OHLC inconsistencies found!"
```

---

## Zusammenfassung

### Was wurde gefixt?

1. **Provider Fallback deaktiviert** wenn User explizit einen Provider wählt
2. **Error Dialogs** zeigen User sofort, wenn etwas schiefgeht
3. **OHLC Validation** in Bitunix Provider verhindert fehlerhafte Daten
4. **Database Fix Tool** repariert bestehende fehlerhafte Daten

### Welche Dateien wurden geändert?

- ✅ `src/core/market_data/history_provider_fetching.py` - Kein Fallback bei expliziter Wahl
- ✅ `src/ui/dialogs/error_dialog.py` - Neue Error Dialog Helper
- ✅ `src/core/market_data/providers/bitunix_provider.py` - OHLC Validation
- ✅ `tools/fix_ohlc_database.py` - Database Fix Tool

### Migration Path

1. **Sofort:** Bitunix Provider validiert alle neuen Daten automatisch
2. **Optional:** Bestehende DB-Daten mit `tools/fix_ohlc_database.py --apply` reparieren
3. **Monitoring:** Logs zeigen `"Fixed X OHLC inconsistencies"` wenn Korrekturen vorgenommen wurden

---

## Sources

- [Lightweight-Charts: Candles disappeared](https://www.tradingview.com/support/solutions/43000472764-candles-have-disappeared-from-the-chart/)
- [Lightweight-Charts: OHLC Data Validation](https://tradingview.github.io/lightweight-charts/docs/release-notes)
- [Lightweight-Charts Issues: Missing candles](https://github.com/tradingview/lightweight-charts/issues/1288)
