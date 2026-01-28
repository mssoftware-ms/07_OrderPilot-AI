# JSON Entry System - Integration Tests

**Version:** 1.0
**Date:** 2026-01-28
**Author:** Claude Code

---

## 📋 Test-Übersicht

Diese Dokumentation beschreibt manuelle Ende-zu-Ende Tests für das JSON Entry System. Die Tests sollten in der angegebenen Reihenfolge durchgeführt werden.

**Voraussetzungen:**
- ✅ Trading Bot läuft (UI gestartet)
- ✅ Chart mit Symbol geöffnet (z.B. BTCUSDT)
- ✅ HistoryManager verfügbar
- ✅ Beispiel-JSONs erstellt

---

## Test 1: UI Button Verfügbarkeit

**Ziel:** Prüfen ob "Start Bot (JSON Entry)" Button vorhanden ist

### Schritte

1. Öffne Trading Bot Tab
2. Prüfe ob beide Buttons vorhanden sind:
   - ✅ "▶ Start Bot" (blau)
   - ✅ "▶ Start Bot (JSON Entry)" (blau)
   - ✅ "⏸ Stop Bot" (rot, disabled)

### Erwartetes Ergebnis

- [ ] Beide Start-Buttons sind sichtbar
- [ ] Buttons haben unterschiedliche Tooltips
- [ ] "Start Bot (JSON Entry)" Tooltip zeigt JSON Entry Info

**Status:** ⬜ Not Started | ✅ Passed | ❌ Failed

---

## Test 2: Simple Entry (nur Regime JSON)

**Ziel:** JSON Entry mit einfacher Expression ohne Indicator JSON

### Vorbereitung

Erstelle `test_simple.json`:
```json
{
  "schema_version": "2.0.0",
  "metadata": {
    "name": "Test Simple Entry"
  },
  "indicators": {
    "rsi14": {"type": "RSI", "period": 14}
  },
  "regimes": {},
  "entry_expression": "rsi < 35"
}
```

### Schritte

1. Klicke "▶ Start Bot (JSON Entry)"
2. Wähle `test_simple.json` aus
3. Klicke "No" bei Indicator JSON Dialog
4. Prüfe Log-Meldungen
5. Prüfe UI State

### Erwartetes Ergebnis

**Log:**
```
✅ Regime JSON: test_simple.json
📝 Entry Expression: rsi < 35
✅ JSON Entry Scorer bereit
   Compiled Expression: True
✅ Bot gestartet! JSON Entry Pipeline läuft.
```

**UI:**
- [ ] "Start Bot" Button disabled
- [ ] "Start Bot (JSON Entry)" Button disabled
- [ ] "Stop Bot" Button enabled
- [ ] Pipeline läuft (Log-Updates jede Sekunde)

**Status:** ⬜ Not Started | ✅ Passed | ❌ Failed

**Notizen:**
```
[Platz für Notizen]
```

---

## Test 3: Entry mit Regime + Indicator JSON

**Ziel:** Beide JSON-Dateien laden und kombinieren

### Vorbereitung

Verwende existierende Dateien:
- Regime JSON: `03_JSON/Entry_Analyzer/Regime/260128_example_json_entry.json`
- Indicator JSON: `tests/core/tradingbot/fixtures/test_indicators.json`

### Schritte

1. Klicke "▶ Start Bot (JSON Entry)"
2. Wähle `260128_example_json_entry.json`
3. Klicke "Yes" bei Indicator JSON Dialog
4. Wähle `test_indicators.json`
5. Prüfe Log-Meldungen

### Erwartetes Ergebnis

**Log:**
```
✅ Regime JSON: 260128_example_json_entry.json
✅ Indicator JSON: test_indicators.json
📝 Entry Expression: rsi < 35 && adx > 25 && macd_hist > 0...
✅ JSON Entry Scorer bereit
✅ Bot gestartet! JSON Entry Pipeline läuft.
```

**Behavior:**
- [ ] Beide JSON-Dateien werden geladen
- [ ] Indicators werden kombiniert (4 total: rsi14, adx14, macd, bb)
- [ ] Entry Expression aus Regime JSON verwendet

**Status:** ⬜ Not Started | ✅ Passed | ❌ Failed

**Notizen:**
```
[Platz für Notizen]
```

---

## Test 4: Entry Expression Compilation Fehler

**Ziel:** Fehlerbehandlung bei ungültiger CEL Syntax

### Vorbereitung

Erstelle `test_invalid.json`:
```json
{
  "schema_version": "2.0.0",
  "metadata": {
    "name": "Test Invalid Expression"
  },
  "indicators": {},
  "regimes": {},
  "entry_expression": "invalid syntax here &&& ||"
}
```

### Schritte

1. Klicke "▶ Start Bot (JSON Entry)"
2. Wähle `test_invalid.json`
3. Prüfe Fehlermeldung

### Erwartetes Ergebnis

**Dialog:**
- [ ] Error Dialog erscheint
- [ ] Meldung: "CEL Expression compilation failed"
- [ ] Bot startet NICHT

**Log:**
```
❌ Fehler beim Starten: CEL Expression compilation failed
```

**Status:** ⬜ Not Started | ✅ Passed | ❌ Failed

**Notizen:**
```
[Platz für Notizen]
```

---

## Test 5: File Not Found (Regime JSON)

**Ziel:** Fehlerbehandlung wenn JSON-Datei nicht existiert

### Schritte

1. Klicke "▶ Start Bot (JSON Entry)"
2. Wähle non-existierende Datei (oder Cancel)
3. Prüfe Fehlermeldung

### Erwartetes Ergebnis

**Log:**
```
❌ Abgebrochen - keine Regime JSON ausgewählt
```
ODER
```
❌ Datei nicht gefunden: nonexistent.json
```

**Dialog:**
- [ ] Error Dialog mit FileNotFoundError

**Status:** ⬜ Not Started | ✅ Passed | ❌ Failed

**Notizen:**
```
[Platz für Notizen]
```

---

## Test 6: Stop Bot (Cleanup)

**Ziel:** Prüfen ob JSON Entry Scorer korrekt deaktiviert wird

### Schritte

1. Starte Bot mit JSON Entry (wie Test 2)
2. Warte 5-10 Sekunden (Pipeline läuft)
3. Klicke "⏸ Stop Bot"
4. Prüfe Log-Meldungen
5. Prüfe UI State

### Erwartetes Ergebnis

**Log:**
```
⏹ Stoppe Trading Bot...
   JSON Entry Scorer deaktiviert
✅ Bot gestoppt! Pipeline wurde angehalten.
```

**UI:**
- [ ] "Start Bot" Button enabled
- [ ] "Start Bot (JSON Entry)" Button enabled
- [ ] "Stop Bot" Button disabled
- [ ] Pipeline stoppt (keine Log-Updates mehr)

**Status:** ⬜ Not Started | ✅ Passed | ❌ Failed

**Notizen:**
```
[Platz für Notizen]
```

---

## Test 7: Pipeline Integration (JSON Entry aktiv)

**Ziel:** Prüfen ob Pipeline JSON Entry Scorer verwendet

### Vorbereitung

Erstelle `test_pipeline.json`:
```json
{
  "schema_version": "2.0.0",
  "metadata": {
    "name": "Test Pipeline"
  },
  "indicators": {
    "rsi14": {"type": "RSI", "period": 14}
  },
  "regimes": {},
  "entry_expression": "rsi < 30"
}
```

### Schritte

1. Starte Bot mit `test_pipeline.json`
2. Aktiviere Debug-Logging (falls verfügbar)
3. Warte auf neuen Bar (1 Minute bei 1m Timeframe)
4. Prüfe Pipeline-Logs

### Erwartetes Ergebnis

**Pipeline Logs:**
```
Using JSON Entry Scorer (CEL-based)
JSON Entry [long]: True (score=1.00, reasons=['JSON_CEL_ENTRY', ...])
```
ODER
```
Using JSON Entry Scorer (CEL-based)
JSON Entry [long]: False (score=0.00, reasons=[])
```

**Behavior:**
- [ ] Pipeline verwendet JsonEntryScorer statt EntryScoreEngine
- [ ] Entry Score wird korrekt berechnet
- [ ] Reason Codes werden generiert

**Status:** ⬜ Not Started | ✅ Passed | ❌ Failed

**Notizen:**
```
[Platz für Notizen]
```

---

## Test 8: SL/TP/Trailing aus UI (nicht JSON)

**Ziel:** Prüfen ob SL/TP aus UI-Feldern verwendet wird

### Schritte

1. Setze UI-Felder:
   - Initial SL: 2.0%
   - Initial TP: 4.0%
   - Trailing Stop: Enabled
2. Starte Bot mit JSON Entry
3. Warte auf Entry Signal
4. Prüfe ob SL/TP aus UI verwendet werden

### Erwartetes Ergebnis

**Log beim Start:**
```
✅ Bot gestartet! JSON Entry Pipeline läuft.
   SL: 2.0% | TP: 4.0% | Trailing: Ja
```

**Bei Entry Signal:**
- [ ] Stop Loss = Entry Price * (1 - 0.02) für Long
- [ ] Take Profit = Entry Price * (1 + 0.04) für Long
- [ ] Trailing Stop aktiviert wenn TP-Schwelle erreicht

**Status:** ⬜ Not Started | ✅ Passed | ❌ Failed

**Notizen:**
```
[Platz für Notizen]
```

---

## Test 9: Parallel Start (Standard vs. JSON)

**Ziel:** Prüfen ob beide Entry-Modi unabhängig funktionieren

### Schritte

1. Starte Bot mit "Start Bot" (Standard)
2. Warte 30 Sekunden
3. Stoppe Bot
4. Starte Bot mit "Start Bot (JSON Entry)"
5. Warte 30 Sekunden
6. Vergleiche Entry-Signale

### Erwartetes Ergebnis

**Standard Entry:**
- [ ] EntryScoreEngine wird verwendet
- [ ] 7-Komponenten Score
- [ ] Component Breakdown im Log

**JSON Entry:**
- [ ] JsonEntryScorer wird verwendet
- [ ] CEL Expression Evaluation
- [ ] Reason Codes im Log

**Behavior:**
- [ ] Unterschiedliche Entry-Signale (je nach Expression)
- [ ] Beide Modi funktionieren unabhängig
- [ ] Kein Konflikt zwischen Modi

**Status:** ⬜ Not Started | ✅ Passed | ❌ Failed

**Notizen:**
```
[Platz für Notizen]
```

---

## Test 10: Validation Warnings

**Ziel:** Prüfen ob Config-Validierung korrekt funktioniert

### Vorbereitung

Erstelle `test_warnings.json`:
```json
{
  "schema_version": "2.0.0",
  "metadata": {
    "name": "Test Warnings"
  },
  "indicators": {
    "rsi14": {"type": "RSI", "period": 14},
    "macd": {"type": "MACD", "fast": 12, "slow": 26, "signal": 9}
  },
  "regimes": {},
  "entry_expression": "rsi < 30"
}
```

### Schritte

1. Starte Bot mit `test_warnings.json`
2. Prüfe Validierungs-Warnings im Log

### Erwartetes Ergebnis

**Log:**
```
⚠️ Validierungs-Warnungen:
   - Indicators nicht in Entry Expression verwendet: macd
```

**Behavior:**
- [ ] Warnings werden angezeigt
- [ ] Bot startet trotzdem (Warnings sind nicht fatal)
- [ ] macd Indicator wird als ungenutzt erkannt

**Status:** ⬜ Not Started | ✅ Passed | ❌ Failed

**Notizen:**
```
[Platz für Notizen]
```

---

## Test 11: Complex Expression (Multiple Conditions)

**Ziel:** Prüfen ob komplexe CEL Expressions funktionieren

### Vorbereitung

Verwende `260128_example_json_entry.json` (bereits erstellt):
```json
{
  "entry_expression": "rsi < 35 && adx > 25 && macd_hist > 0 && (regime == 'EXTREME_BULL' || regime == 'TREND_UP')"
}
```

### Schritte

1. Starte Bot mit `260128_example_json_entry.json`
2. Warte auf mehrere Bars
3. Prüfe Entry-Signale

### Erwartetes Ergebnis

**Entry Signal nur wenn:**
- [ ] RSI < 35 (Oversold)
- [ ] ADX > 25 (Strong Trend)
- [ ] MACD Histogram > 0 (Bullish)
- [ ] Regime ist EXTREME_BULL ODER TREND_UP

**Reason Codes:**
```
JSON Entry [long]: True (score=1.00, reasons=['JSON_CEL_ENTRY', 'RSI_OVERSOLD', 'STRONG_TREND', 'MACD_BULLISH', 'TREND_REGIME'])
```

**Status:** ⬜ Not Started | ✅ Passed | ❌ Failed

**Notizen:**
```
[Platz für Notizen]
```

---

## Test 12: Performance (CEL Evaluation < 5ms)

**Ziel:** Prüfen ob CEL Evaluation schnell genug ist

### Schritte

1. Starte Bot mit JSON Entry
2. Aktiviere Performance-Logging (falls verfügbar)
3. Messe Zeit für Entry Score Phase
4. Prüfe ob < 5ms pro Bar

### Erwartetes Ergebnis

**Performance:**
- [ ] CEL Compilation einmalig beim Start (< 100ms)
- [ ] CEL Evaluation pro Bar < 5ms
- [ ] Kein Performance-Overhead vs. Standard Entry

**Behavior:**
- [ ] Pipeline läuft smooth (1x pro Sekunde bei neuem Bar)
- [ ] Keine Verzögerungen oder Lag

**Status:** ⬜ Not Started | ✅ Passed | ❌ Failed

**Notizen:**
```
[Platz für Notizen]
```

---

## 📊 Test-Zusammenfassung

| Test | Status | Notizen |
|------|--------|---------|
| Test 1: UI Button Verfügbarkeit | ⬜ | |
| Test 2: Simple Entry | ⬜ | |
| Test 3: Regime + Indicator JSON | ⬜ | |
| Test 4: Expression Compilation Fehler | ⬜ | |
| Test 5: File Not Found | ⬜ | |
| Test 6: Stop Bot (Cleanup) | ⬜ | |
| Test 7: Pipeline Integration | ⬜ | |
| Test 8: SL/TP aus UI | ⬜ | |
| Test 9: Parallel Start | ⬜ | |
| Test 10: Validation Warnings | ⬜ | |
| Test 11: Complex Expression | ⬜ | |
| Test 12: Performance | ⬜ | |

**Gesamt:** 0/12 Passed

---

## 🐛 Bug Reports

Falls Bugs gefunden werden, bitte dokumentieren:

### Bug Template

```markdown
**Bug ID:** [Nummer]
**Test:** [Test Name]
**Severity:** Critical | High | Medium | Low
**Description:** [Kurze Beschreibung]
**Steps to Reproduce:**
1. ...
2. ...
3. ...
**Expected Result:** [Was sollte passieren]
**Actual Result:** [Was ist passiert]
**Logs/Screenshots:** [Anhängen]
**Environment:**
- OS: Windows 11 / Linux
- Python: 3.12.3
- Version: [Git Commit Hash]
```

---

## ✅ Acceptance Criteria

Das JSON Entry System ist produktionsbereit wenn:

- [ ] Alle 12 Tests bestanden (PASSED)
- [ ] Keine Critical/High Bugs
- [ ] Performance-Ziel erreicht (< 5ms CEL Evaluation)
- [ ] Dokumentation vollständig
- [ ] Unit Tests bestanden (38/38)

---

**Version:** 1.0
**Last Updated:** 2026-01-28
**Tester:** [Name eintragen]
**Test Date:** [Datum eintragen]
**Test Duration:** [Dauer eintragen]

