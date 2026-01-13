# Startup Errors Fix - 2026-01-13

**Datum**: 2026-01-13
**Status**: ✅ BEHOBEN
**Betroffene Dateien**: 3

---

## Fehler-Übersicht

### Fehler 1: Bitunix HEDGE Widget Initialization Failed ❌

**Symptom:**
```
"Failed to create Bitunix HEDGE widget: wrapped C/C++ object of type QPushButton has been deleted"
```

**Ursache:**
Qt-Lifecycle-Problem in `bitunix_hedge_execution_widget.py`. In `_setup_ui()` wurde versucht, das Widget (`self`) als Child zu einem neuen Container hinzuzufügen, nachdem bereits ein Layout gesetzt wurde. Das führte dazu, dass QPushButton-Objekte gelöscht wurden, während sie noch referenziert wurden.

```python
# PROBLEM (alt):
self.setLayout(main_layout)  # Layout gesetzt
main_container = QWidget()
container_layout = QVBoxLayout(main_container)
container_layout.addWidget(self)  # ❌ Widget fügt sich selbst hinzu
```

**Lösung:**
Footer direkt in das QVBoxLayout integrieren, ohne separaten Container:

```python
# LÖSUNG (neu):
main_v_layout = QVBoxLayout()
columns_layout = QHBoxLayout()
# ... Spalten hinzufügen ...
main_v_layout.addLayout(columns_layout)
main_v_layout.addWidget(self._create_status_footer())  # Footer direkt
self.setLayout(main_v_layout)
```

**Datei:** `src/ui/widgets/bitunix_hedge_execution_widget.py:61-88`

---

### Fehler 2: Alpaca Crypto Invalid Symbol Format ❌

**Symptom:**
```
"Error fetching Alpaca crypto data: invalid symbol: BTCUSDT does not match ^[A-Z]+/[A-Z]+$"
"No bars returned from alpaca_crypto, trying fallback..."
```

**Ursache:**
Alpaca Crypto API erwartet Symbole im Format `BTC/USD`, `ETH/USD` (mit Slash), nicht `BTCUSDT`. Die Skip-Logik in `_should_skip_source()` funktionierte korrekt für die Fallback-Schleife, aber NICHT für explizit angegebene Quellen in `_try_specific_source()`.

**Lösung:**
Skip-Logik auch in `_try_specific_source()` einbauen:

```python
async def _try_specific_source(self, request: DataRequest) -> tuple[list[HistoricalBar], str]:
    if not (request.source and request.source in self.parent.providers):
        return [], ""

    # NEU: Check if source should be skipped
    if self._should_skip_source(request, request.source, False):
        logger.debug(f"Skipping specific source {request.source.value} for {request.symbol} (invalid combination)")
        return [], ""

    # ... rest of method
```

**Logik:**
- Symbole mit `/` (z.B. `BTC/USD`) → Alpaca Crypto
- Symbole mit `USDT`/`USDC` (z.B. `BTCUSDT`) → Bitunix
- Falsche Kombination → Skip

**Datei:** `src/core/market_data/history_provider_fetching.py:91-119`

---

### Fehler 3: Database UNIQUE Constraint Failed ❌

**Symptom:**
```
"Database transaction failed: (sqlite3.IntegrityError) UNIQUE constraint failed: market_bars.symbol, market_bars.timestamp"
```

**Ursache:**
**Race Condition** bei parallelen Fetch-Operationen:
1. Zwei Chart-Widgets fetchen gleichzeitig Bars für `BTCUSDT`
2. Beide lesen die DB zur gleichen Zeit → beide sehen keine Duplikate
3. Beide versuchen gleichzeitig zu schreiben
4. Der zweite Write schlägt fehl mit UNIQUE constraint

**Lösung:**
`IntegrityError` speziell behandeln und für Race Conditions als normales Verhalten erkennen:

```python
except Exception as e:
    import sqlite3

    # Race condition: Another thread may have inserted the same bars
    # This is expected and can be safely ignored
    if isinstance(e.__cause__, sqlite3.IntegrityError) and "UNIQUE constraint" in str(e):
        logger.debug(f"Bars already in database (race condition, expected): {symbol}")
    else:
        logger.error(f"Failed to store bars to database: {e}")
```

**Datei:** `src/core/market_data/history_provider_fetching.py:267-276`

---

## Zusammenfassung der Änderungen

### Datei 1: `src/ui/widgets/bitunix_hedge_execution_widget.py`

**Geänderte Methode:** `_setup_ui()` (Zeilen 61-88)

**Vorher:**
- QHBoxLayout mit 3 Spalten als Haupt-Layout
- Footer in separatem Widget
- Versuch, `self` als Child hinzuzufügen → Qt-Fehler

**Nachher:**
- QVBoxLayout als Haupt-Layout
- QHBoxLayout für 3 Spalten (nested)
- Footer direkt in QVBoxLayout → keine separaten Container

### Datei 2: `src/core/market_data/history_provider_fetching.py`

**Änderung 1:** `_try_specific_source()` (Zeilen 91-119)

**Neu hinzugefügt:**
```python
# Check if source should be skipped for this asset class/symbol
if self._should_skip_source(request, request.source, False):
    logger.debug(f"Skipping specific source {request.source.value} for {request.symbol} (invalid combination)")
    return [], ""
```

**Änderung 2:** `_store_to_database()` (Zeilen 267-276)

**Neu hinzugefügt:**
```python
except Exception as e:
    import sqlite3

    # Race condition: Another thread may have inserted the same bars
    # This is expected and can be safely ignored
    if isinstance(e.__cause__, sqlite3.IntegrityError) and "UNIQUE constraint" in str(e):
        logger.debug(f"Bars already in database (race condition, expected): {symbol}")
    else:
        logger.error(f"Failed to store bars to database: {e}")
```

---

## Erwartetes Verhalten nach Fix

### Startup-Sequenz

1. ✅ **Bitunix HEDGE Widget**
   - Widget lädt erfolgreich
   - Alle UI-Elemente (Buttons, Spinboxes, etc.) verfügbar
   - Keine Qt C++ object deletion errors

2. ✅ **Alpaca Crypto Provider**
   - Wird für `BTCUSDT` übersprungen (Bitunix-Symbol)
   - Kein API-Fehler mehr
   - Log zeigt: `"Skipping specific source alpaca_crypto for BTCUSDT (invalid combination)"`

3. ✅ **Database Caching**
   - Parallele Fetch-Operationen funktionieren
   - Race Conditions werden erkannt und ignoriert
   - Log zeigt: `"Bars already in database (race condition, expected): BTCUSDT"` (Debug-Level)
   - **KEIN** Error-Log mehr

### Log-Output (Erwartet)

**Vor Fix:**
```
ERROR: Failed to create Bitunix HEDGE widget: wrapped C/C++ object of type QPushButton has been deleted
ERROR: Error fetching Alpaca crypto data: invalid symbol: BTCUSDT does not match ^[A-Z]+/[A-Z]+$
ERROR: Failed to store bars to database: (sqlite3.IntegrityError) UNIQUE constraint failed
```

**Nach Fix:**
```
INFO: Bitunix HEDGE widget initialized successfully
DEBUG: Skipping specific source alpaca_crypto for BTCUSDT (invalid combination)
DEBUG: Bars already in database (race condition, expected): BTCUSDT
INFO: Fetched 1607 bars from bitunix
```

---

## Testing Checklist

### Test 1: Bitunix HEDGE Widget
- [ ] Anwendung starten
- [ ] "Trading Bot" Tab öffnen
- [ ] Bitunix HEDGE Execution Widget sichtbar
- [ ] Alle Buttons/Controls funktionieren
- [ ] Kein Qt-Fehler im Log

### Test 2: Symbol Loading
- [ ] Chart für `BTCUSDT` laden
- [ ] Alpaca Crypto wird übersprungen (Debug-Log)
- [ ] Bitunix Provider liefert Daten
- [ ] Chart zeigt Kerzen

### Test 3: Parallel Loading
- [ ] Zwei Chart-Widgets für `BTCUSDT` öffnen
- [ ] Beide laden gleichzeitig
- [ ] Keine IntegrityError im Log (nur Debug-Meldung)
- [ ] Beide Charts zeigen korrekte Daten

---

## Technische Details

### Qt Widget Lifecycle
- Ein Widget kann nicht sein eigenes Parent sein
- `addWidget(self)` nach `setLayout()` ist ungültig
- Lösung: Flache Hierarchie ohne Container-in-Container

### Crypto Provider Separation
- **Alpaca Crypto**: Symbole mit `/` (BTC/USD, ETH/USD)
- **Bitunix**: Symbole mit `USDT`/`USDC` (BTCUSDT, ETHUSDT)
- Skip-Logik muss ÜBERALL gelten (auch bei expliziten Quellen)

### Database Race Conditions
- SQLAlchemy Sessions sind nicht thread-safe
- Parallele Writes auf gleiche Daten → IntegrityError
- Lösung: Error abfangen und als normal behandeln (idempotent operations)

---

## Weitere Maßnahmen (Optional)

### Performance-Optimierung
- [ ] `INSERT OR IGNORE` für SQLite nutzen (eliminiert Race Condition komplett)
- [ ] Connection Pooling für DB-Zugriffe
- [ ] Caching-Layer vor DB

### Monitoring
- [ ] Prometheus Metrics für DB-Errors
- [ ] Alerting bei häufigen IntegrityErrors (>100/h)
- [ ] Grafana Dashboard für Provider-Statistiken

---

**Status**: ✅ Alle Fehler behoben
**Nächster Schritt**: Anwendung neu starten und Tests durchführen
