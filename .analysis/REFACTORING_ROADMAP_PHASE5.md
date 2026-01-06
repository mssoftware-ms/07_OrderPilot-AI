# Refactoring Roadmap - Phase 5+

**Datum:** 2026-01-06
**Status:** PLANUNG
**Scope:** Mittelfristiges Refactoring-Programm

---

## Executive Summary

Nach erfolgreicher Phase 3B & 4B verbleiben:

| Kategorie | Anzahl | Status |
|-----------|--------|--------|
| 🔴 **Critical (CC > 20)** | **1** | Dokumentiert |
| ⚠️  **Warnings (CC 11-20)** | **117** | Zu priorisieren |
| ℹ️  **Moderate (CC 6-10)** | **441** | Optional |

**Ziel:** Systematische Reduktion von Warnings (CC 11-20) auf <50

---

## Phase 5A: Top-Priority Critical Function

### ⚠️ `_show_evaluation_popup` (CC=26)

**Datei:** `src/chart_chat/chart_chat_actions_mixin.py:231`

**Status:** ✅ Detaillierter Plan erstellt
- **Dokument:** `.analysis/REFACTORING_PLAN_EVALUATION_DIALOG.md`
- **Aufwand:** 6-8 Stunden
- **Strategie:** Vollständige Klassen-Extraktion → `EvaluationDialog`
- **ROI:** HOCH (große Wartbarkeitsverbesserung)

**Empfehlung:**
- ✅ **Durchführen** - Separate Task, dedizierter Zeitslot
- 📅 **Timing:** Nach User-Freigabe
- 🎯 **Ziel:** CC 26 → 3 (-88%)

---

## Phase 5B: High-Priority Warnings (CC=20)

### Top 6 Funktionen mit CC=20

| # | Funktion | Datei | Zeile | Kategorie |
|---|----------|-------|-------|-----------|
| 1 | `calculate_bb` | core/indicators/volatility.py | 28 | Indicators |
| 2 | `select_strategy` | core/tradingbot/strategy_selector.py | 133 | Trading Bot |
| 3 | `_validate_product` | derivatives/ko_finder/adapter/normalizer.py | 153 | KO Finder |
| 4 | `_convert_macd_data_to_chart_format` | ui/widgets/chart_mixins/indicator_mixin.py | 143 | UI/Chart |
| 5 | `_check_stops_on_candle_close` | ui/widgets/chart_window_mixins/bot_callbacks_candle_mixin.py | 82 | Trading Bot |
| 6 | `_update_current_position_display` | ui/widgets/chart_window_mixins/bot_panels_mixin.py | 220 | UI/Bot |

### Empfehlung:

**Priority 1:** Trading Bot Core Logic (2, 5)
- `select_strategy` - Kern der Strategie-Auswahl
- `_check_stops_on_candle_close` - Kritisch für Stop-Loss-Verwaltung
- **ROI:** SEHR HOCH (Fehler hier = Geldverlust!)

**Priority 2:** Indicators (1, 4)
- `calculate_bb` - Bollinger Bands Berechnung
- `_convert_macd_data_to_chart_format` - MACD Visualisierung
- **ROI:** MITTEL (Performance + Korrektheit)

**Priority 3:** UI & Others (3, 6)
- **ROI:** NIEDRIG (hauptsächlich Wartbarkeit)

---

## Phase 5C: Medium-Priority Warnings (CC=17-19)

### CC=19 (4 Funktionen)

| Funktion | Datei | Kategorie |
|----------|-------|-----------|
| `from_variable_string` | chart_chat/chart_markings.py:61 | Parsing |
| `detect_regime` | core/ai_analysis/regime.py:19 | AI Analysis |
| `combine_signals` | core/strategy/engine.py:321 | Strategy Engine |
| `calculate_metrics` | core/tradingbot/strategy_evaluator.py:69 | Trading Bot |

**Empfehlung:**
- **`calculate_metrics`** bereits teilweise refactored in Phase 3B!
  - Prüfen, ob weitere Optimierung möglich
- **`combine_signals`** - Kritisch für Signal-Aggregation
- **`detect_regime`** - AI-basierte Markt-Regime-Erkennung

### CC=18 (3 Funktionen)

| Funktion | Datei | Kategorie |
|----------|-------|-----------|
| `run` | chart_chat/chart_chat_worker.py:52 | Worker Thread |
| `_load_ui_settings` | ui/dialogs/pattern_db_settings_mixin.py:34 | UI Settings |
| `_update_signals_pnl` | ui/widgets/chart_window_mixins/bot_display_signals_mixin.py:13 | UI/Bot Display |

### CC=17 (5 Funktionen)

*(Siehe vollständige Liste oben)*

**Empfehlung:**
- Fokus auf **Trading Bot** und **Strategy Engine** Funktionen
- UI-Funktionen später (niedrigere Priorität)

---

## Phase 5D: Remaining Warnings (CC=11-16)

**Gesamt:** 100 Funktionen

### Top-Kategorien:

1. **UI/Chart Widgets** (~40 Funktionen)
   - Meist UI-Logik, Display-Updates
   - **ROI:** NIEDRIG (hauptsächlich Wartbarkeit)

2. **Trading Bot Logic** (~25 Funktionen)
   - Position Management, Signale, Stops
   - **ROI:** HOCH (Fehler = Geldverlust!)

3. **Strategy Engine** (~15 Funktionen)
   - Signal-Generierung, Kombinationen
   - **ROI:** HOCH (Kern-Logik)

4. **Market Data / Indicators** (~10 Funktionen)
   - Daten-Verarbeitung, Berechnungen
   - **ROI:** MITTEL (Performance + Korrektheit)

5. **Others** (~10 Funktionen)
   - Diverse Module
   - **ROI:** VARIABEL

---

## Priorisierte Roadmap

### Phase 5 (Kurzfristig, 1-2 Wochen)

**Ziel:** Top 10 Critical/High-Priority Warnings refactoren

1. ✅ **`_show_evaluation_popup`** (CC=26) - Bereits geplant
2. 🎯 **`select_strategy`** (CC=20) - Trading Bot Kern
3. 🎯 **`_check_stops_on_candle_close`** (CC=20) - Stop-Loss Management
4. 🎯 **`combine_signals`** (CC=19) - Signal-Aggregation
5. 🎯 **`calculate_bb`** (CC=20) - Bollinger Bands
6. 🎯 **`detect_regime`** (CC=19) - Regime-Erkennung

**Aufwand:** ~8-12 Stunden
**Erwartete CC-Reduktion:** ~60-80 Punkte gesamt
**ROI:** SEHR HOCH

### Phase 6 (Mittelfristig, 1 Monat)

**Ziel:** Weitere 20-30 Warnings refactoren

- **Fokus:** Trading Bot & Strategy Engine (CC 16-19)
- **Methode:** Extract Method, Guard Clauses
- **Aufwand:** ~20-30 Stunden

### Phase 7 (Langfristig, 3 Monate)

**Ziel:** Warnings <50, alle Critical <10

- **Fokus:** Systematische Durchforstung aller Warnings
- **Methode:** Batch-Refactoring nach Modul
- **Aufwand:** ~40-60 Stunden

---

## Refactoring-Patterns (Empfohlen)

### 1. Extract Method Pattern
**Anwendung:** >90% der Fälle
**Vorteil:** Einfach, sicher, testbar

### 2. Guard Clauses
**Anwendung:** Validation-heavy Funktionen
**Vorteil:** Reduziert Verschachtelung drastisch

### 3. Strategy Pattern
**Anwendung:** if-elif-elif Chains (z.B. `select_strategy`)
**Vorteil:** Erweiterbar, testbar

### 4. Template Method
**Anwendung:** Funktionen mit klarer Struktur
**Vorteil:** Lesbarkeit, Wiederverwendung

### 5. Dispatch Dictionary
**Anwendung:** Type-basierte Verzweigungen
**Vorteil:** Höchste CC-Reduktion (-90%+)

---

## Guidelines & Best Practices

### Vor jedem Refactoring:

1. ✅ **Funktion lesen und verstehen**
   - Was tut sie?
   - Welche Verantwortlichkeiten?
   - Welche Tests existieren?

2. ✅ **Tests schreiben/erweitern**
   - Unit-Tests für Kern-Logik
   - Integration-Tests für kritische Pfade
   - Coverage >70%

3. ✅ **Pattern auswählen**
   - Extract Method (default)
   - Guard Clauses (bei vielen Validierungen)
   - Dispatch/Strategy (bei langen if-elif)

4. ✅ **Klein anfangen**
   - Ein Pattern pro Refactoring
   - Commits nach jedem Schritt
   - Tests laufen lassen

### Nach jedem Refactoring:

1. ✅ **Verification**
   - Syntax-Tests
   - Import-Tests
   - Unit-Tests (100% bestanden)
   - Integration-Tests (kritische Pfade)

2. ✅ **Metrics prüfen**
   - CC-Reduktion messen
   - LOC-Änderung prüfen
   - Dokumentieren

3. ✅ **Commit**
   - Klare Commit-Message
   - CC-Reduktion erwähnen
   - Pattern dokumentieren

---

## Risk Assessment

### Low-Risk Refactorings:
- UI-Display Funktionen
- Logging, Formatting
- Data-Transformationen

### Medium-Risk Refactorings:
- Indicator-Berechnungen
- Chart-Visualisierung
- Settings-Management

### High-Risk Refactorings:
- **Trading Bot Logic** (Stop-Loss, Position Management)
- **Strategy Selection**
- **Signal Generation/Combination**

**Mitigation für High-Risk:**
1. 🧪 **Umfangreiche Tests schreiben VORHER**
2. 🔄 **Paper-Trading Tests nach Refactoring**
3. 📊 **Backtests vergleichen (vor/nach)**
4. 👥 **Code-Review einholen**
5. 🎯 **Feature-Flags nutzen** (alte Implementierung behalten)

---

## Metrics & KPIs

### Ziele (nächste 3 Monate):

| Metrik | Aktuell | Ziel | Fortschritt |
|--------|---------|------|-------------|
| Critical (CC>20) | 1 | 0 | 🟡 In Arbeit |
| Warnings (CC 11-20) | 117 | <50 | 🔴 TODO |
| Moderate (CC 6-10) | 441 | <350 | 🔴 TODO |
| Durchschnitt CC | ~7.5 | <6.0 | 🟡 In Arbeit |

### Tracking:

- **Wöchentlich:** Radon-Scan laufen lassen
- **Monatlich:** Fortschritts-Report erstellen
- **Quarterly:** Review & Priorisierung anpassen

---

## Tooling & Automation

### CI/CD Integration (Empfohlen):

```yaml
# .github/workflows/code-quality.yml
name: Code Quality

on: [push, pull_request]

jobs:
  complexity:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Install dependencies
        run: pip install radon
      - name: Check complexity
        run: |
          radon cc src/ -s -a --total-average -j > complexity.json
          # Fail if new functions with CC>20
          python scripts/check_complexity.py
```

### Pre-Commit Hook (Optional):

```bash
#!/bin/bash
# .git/hooks/pre-commit

# Check complexity of changed files
for file in $(git diff --cached --name-only --diff-filter=AM | grep "\.py$"); do
    if [ -f "$file" ]; then
        radon cc "$file" -s -n C | grep -q "C\|D\|E\|F" && echo "❌ $file has CC>15" && exit 1
    fi
done
```

---

## Resources & Documentation

### Internal Docs:
- `.analysis/REFACTORING_FINAL_REPORT_PHASE3B.md` - Lessons Learned
- `.analysis/REFACTORING_PLAN_EVALUATION_DIALOG.md` - Class Extraction Guide
- `.analysis/REFACTORING_NOTES_REMAINING.md` - Known Issues

### External References:
- [Refactoring Guru - Patterns](https://refactoring.guru/refactoring/catalog)
- [Radon Documentation](https://radon.readthedocs.io/)
- [Python Best Practices](https://docs.python-guide.org/)

---

## Next Steps

### Immediate (Diese Woche):
1. ✅ **User-Freigabe** für `_show_evaluation_popup` Refactoring
2. 📋 **Issue erstellen** für Top 6 CC=20 Funktionen
3. 🧪 **Test-Coverage prüfen** für High-Risk Funktionen

### Short-Term (Nächste 2 Wochen):
1. 🔧 **Refactor `select_strategy`** (CC=20)
2. 🔧 **Refactor `_check_stops_on_candle_close`** (CC=20)
3. 📊 **Progress Report** erstellen

### Mid-Term (Nächster Monat):
1. 🎯 **Phase 6 starten** - 20-30 Warnings
2. 🧪 **Test-Coverage erhöhen** auf >80%
3. 🔄 **CI/CD Integration** für Complexity Checks

---

## Conclusion

Das Projekt hat durch Phase 3B & 4B **dramatische Verbesserungen** erfahren:
- **Nur noch 1 Critical** (war 8)
- **Durchschnitt CC-Reduktion: -79%**

**Aber:** Es verbleiben **117 Warnings (CC 11-20)**, die systematisch angegangen werden sollten.

**Empfehlung:**
1. ✅ **`_show_evaluation_popup`** refactoren (separate Task)
2. 🎯 **Top 10 Warnings** in Phase 5 (1-2 Wochen)
3. 📈 **Kontinuierliche Verbesserung** in Phases 6-7 (3 Monate)

**Fokus:** Trading Bot & Strategy Engine (höchster ROI)

---

**Status:** ✅ PLANUNG ABGESCHLOSSEN
**Nächster Schritt:** User-Priorisierung & Freigabe

