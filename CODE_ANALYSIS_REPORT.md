# OrderPilot-AI Code-Qualitäts-Analyse
**Datum:** 2025-11-23
**Analysierte Dateien:** 57 Python-Dateien
**Gesamtzeilen:** 21.467 LOC (13.998 SLOC)
**Analysewerkzeuge:** vulture 2.14, radon 6.0.1

---

## Executive Summary

Diese Analyse identifiziert systematisch toten Code, Redundanzen und Komplexitäts-Hotspots in der OrderPilot-AI Codebasis. Die Ergebnisse dienen als Grundlage für eine kontrollierte Code-Bereinigung.

### Hauptbefunde

- **25 tote/ungenutzte Imports und Variablen** (hohe Konfidenz)
- **1 kritische Komplexitäts-Hotspot** (F-Grade, Komplexität 62)
- **3 hochkomplexe Funktionen** (D/E-Grade, Komplexität 22-36)
- **33 komplexe Funktionen** (C-Grade, Komplexität 11-19)
- **Signifikante Code-Duplikation** zwischen Chart-Widgets
- **5 ungenutzte Strategy-Klassen** (nur in Backtesting verwendet)

### Priorisierung

1. **KRITISCH:** EmbeddedTradingViewChart._update_indicators (Komplexität 62)
2. **HOCH:** Tote Imports entfernen (25 Fälle)
3. **MITTEL:** ChartView.load_symbol refactoring (Komplexität 36)
4. **MITTEL:** Code-Duplikation in Chart-Widgets reduzieren
5. **NIEDRIG:** Ungenutzte Exception-Handler-Variablen bereinigen

---

## 1. Dead Code (Toter Code)

### 1.1 Verifizierte Dead Imports (90-100% Konfidenz)

#### Unused Imports

| Datei | Import | Zeile | Konfidenz |
|-------|--------|-------|-----------|
| `src/ui/app.py` | `ChartView` | 58 | 90% |
| `src/ui/widgets/embedded_tradingview_chart.py` | `QUrl` | 14 | 90% |
| `src/ui/widgets/embedded_tradingview_chart.py` | `QWebChannel` | 29 | 90% |
| `src/ui/widgets/lightweight_chart.py` | `QWebChannel` | 26 | 90% |
| `src/core/backtesting/backtrader_integration.py` | `btfeeds` | 20 | 90% |
| `src/core/backtesting/backtrader_integration.py` | `mdates` | 609 | 90% |
| `src/core/broker/alpaca_adapter.py` | `GetOrdersRequest` | 12 | 90% |

**Total: 7 ungenutzte Imports**

### 1.2 Unused Variables (100% Konfidenz)

#### Exception Handler Variables (Low Priority)

Diese Variablen werden in `except` Blöcken definiert, aber nicht verwendet:

| Datei | Variablen | Zeile |
|-------|-----------|-------|
| `src/ai/openai_service.py` | `exc_type, exc_val, exc_tb` | 345 |
| `src/common/performance.py` | `exc_type, exc_val, exc_tb` | 269 |

**Hinweis:** Häufiges Pattern in Exception Handling - können durch `_` ersetzt werden.

#### IBKR Callback Parameters (Medium Priority)

Ungenutzte Parameter in IBKR Adapter Callbacks:

| Datei | Variablen | Zeilen |
|-------|-----------|--------|
| `src/core/broker/ibkr_adapter.py` | `permId, remaining` | 78 |
| `src/core/broker/ibkr_adapter.py` | `clientId, lastFillPrice, parentId` | 79 |
| `src/core/broker/ibkr_adapter.py` | `mktCapPrice, whyHeld` | 80 |
| `src/core/broker/ibkr_adapter.py` | `attrib` | 117 |

**Hinweis:** API-Callback-Signaturen - Parameter können mit `_` prefix markiert werden.

#### Database Callback Parameters

| Datei | Variable | Zeile |
|-------|----------|-------|
| `src/database/database.py` | `connection_record` | 59 |

#### UI Widget Variables

| Datei | Variable | Zeile | Kontext |
|-------|----------|-------|---------|
| `src/ui/widgets/chart_view.py` | `frac, orthoRange` | 131 | ViewBox Callback |
| `src/ui/widgets/embedded_tradingview_chart.py` | `checked` | 477 | Indicator Action |

**Total: 18 ungenutzte Variablen**

---

## 2. Komplexitäts-Analyse

### 2.1 Kritische Komplexitäts-Hotspots

#### F-Grade: Unmittelbar handlungsbedürftig

| Datei | Funktion | Komplexität | Grade |
|-------|----------|-------------|-------|
| `src/ui/widgets/embedded_tradingview_chart.py` | `_update_indicators` (Line 692) | **62** | **F** |

**Details:**
- **Problem:** Mega-Methode mit 62 Verzweigungen
- **Risiko:** Extrem schwer zu testen und zu warten
- **Empfehlung:** In separate Funktionen aufteilen:
  - `_update_overlay_indicators()` für SMA/EMA/BB
  - `_update_oscillator_indicators()` für RSI/MACD/STOCH/ATR/ADX/CCI/MFI
  - `_calculate_indicator()` für Shared Logic
  - `_render_indicator()` für Chart-Rendering

#### E-Grade: Dringend empfohlen

| Datei | Funktion | Komplexität | Grade |
|-------|----------|-------------|-------|
| `src/ui/widgets/chart_view.py` | `load_symbol` (Line 652) | **36** | **E** |

**Details:**
- **Problem:** Komplexe Symbol-Lade-Logik mit vielen Pfaden
- **Risiko:** Fehleranfällig bei Änderungen
- **Empfehlung:** State Machine Pattern oder separate Methoden für:
  - Datenvalidierung
  - Chart-Initialisierung
  - Indikator-Setup
  - Fehlerbehandlung

#### D-Grade: Empfohlen

| Datei | Funktion | Komplexität | Grade |
|-------|----------|-------------|-------|
| `src/core/market_data/history_provider.py` | `YahooFinanceProvider.fetch_bars` (Line 629) | **22** | **D** |

**Details:**
- **Problem:** Komplexe Fallback-Logik für Datenabruf
- **Risiko:** Schwer zu debuggen bei Provider-Problemen
- **Empfehlung:** Separate Methoden für verschiedene Timeframes

### 2.2 C-Grade Funktionen (11-19 Komplexität)

**Gesamt: 33 Funktionen**

Auswahl der kritischsten:

| Datei | Funktion | Komplexität |
|-------|----------|-------------|
| `src/core/strategy/engine.py` | `combine_signals` (819) | 19 |
| `src/ui/app.py` | `closeEvent` (1030) | 19 |
| `src/ui/widgets/performance_dashboard.py` | `_calculate_metrics` (609) | 17 |
| `src/ui/widgets/embedded_tradingview_chart.py` | `load_symbol` (1268) | 17 |
| `src/core/broker/alpaca_adapter.py` | `_place_order_impl` (167) | 15 |
| `src/ui/dialogs/settings_dialog.py` | `save_settings` (423) | 15 |
| `src/ui/widgets/chart_view.py` | `_update_chart` (366) | 14 |

**Durchschnittliche Komplexität aller C-Grade Funktionen:** 15.9

---

## 3. Code-Duplikation

### 3.1 Type-2 Clones (Strukturelle Duplikate)

#### Chart Widget Indicator Logic

**Betroffene Dateien:**
- `src/ui/widgets/embedded_tradingview_chart.py:_update_indicators()` (Lines 692-753)
- `src/ui/widgets/lightweight_chart.py:_update_indicators()` (Lines 319-374)

**Duplikations-Grad:** ~70% (strukturell ähnlich)

**Gemeinsame Pattern:**
```python
# Beide implementieren ähnliche Logik:
1. Check if indicator button is checked
2. Create IndicatorConfig
3. Calculate indicator via indicator_engine
4. Convert to chart-specific format
5. Add/remove series based on state
```

**Unterschiede:**
- Embedded TradingView: JavaScript-basiertes Rendering (komplexer)
- Lightweight Chart: Python-API-basiertes Rendering

**Empfehlung:** Shared Base Class oder Strategy Pattern für Indikator-Management

#### Symbol Loading Logic

**Betroffene Dateien:**
- `src/ui/widgets/embedded_tradingview_chart.py:load_symbol()` (Line 1268)
- `src/ui/widgets/chart_view.py:load_symbol()` (Line 652)
- `src/ui/widgets/lightweight_chart.py:load_symbol()` (Line 467)

**Duplikations-Grad:** ~50-60%

**Gemeinsame Pattern:**
1. History Manager Datenabruf
2. DataFrame Validierung
3. Indikator-Engine Initialisierung
4. Chart-Update

**Empfehlung:** Abstract Base Class `BaseChartWidget` mit shared `load_symbol()` Template Method

### 3.2 Strategy Pattern Duplication

**Betroffene Dateien:**
- `src/core/strategy/engine.py`

**5 Strategy-Klassen mit ähnlicher Struktur:**
1. `TrendFollowingStrategy` (Line 208, Komplexität 14)
2. `MeanReversionStrategy` (Line 321, Komplexität 15)
3. `MomentumStrategy` (Line 432, Komplexität 14)
4. `BreakoutStrategy` (Line 526, Komplexität 13)
5. `ScalpingStrategy` (Line 619, Komplexität 13)

**Problem:** Jede Strategy hat fast identische Struktur:
- `__init__()` mit State-Initialisierung
- `reset()` Methode
- `evaluate()` Methode mit Indikator-Berechnung
- Signal-Generierung

**Nutzung:** Nur in `src/core/backtesting/backtrader_integration.py` referenziert

**Empfehlung:**
- Template Method Pattern für gemeinsame Logik
- **ODER:** Prüfen ob diese Strategien aktuell überhaupt verwendet werden (scheinen nicht im Main App aktiv)

---

## 4. Architektur-Beobachtungen

### 4.1 Große Dateien (>1000 LOC)

| Datei | LOC | SLOC | Kommentare |
|-------|-----|------|------------|
| `src/core/market_data/history_provider.py` | 1664 | 1090 | 67 |
| `src/ui/widgets/embedded_tradingview_chart.py` | 1410 | 1033 | 149 |
| `src/core/indicators/engine.py` | 1191 | 928 | 81 |
| `src/ui/app.py` | 1132 | 735 | 128 |
| `src/core/strategy/engine.py` | 957 | 648 | 54 |

**Empfehlung:**
- `history_provider.py` könnte in separate Provider-Klassen pro Datenquelle aufgeteilt werden
- `embedded_tradingview_chart.py` sollte Indikator-Logik auslagern

### 4.2 Kommentar-Statistiken

**Gesamtprojekt:**
- Kommentare/LOC: 8%
- Kommentare/SLOC: 12%
- Kommentare+Multi/LOC: 15%

**Best Documented:**
- `src/database/models.py`: 27% (Kommentare/SLOC)
- `src/ui/chart_window_manager.py`: 34% (Kommentare+Multi/LOC)
- `src/ui/widgets/chart_window.py`: 25% (Kommentare/SLOC)

**Under Documented:**
- `src/ui/themes.py`: 0% (Kommentare/LOC)
- `src/ai/prompts.py`: 2% (Kommentare/LOC)
- `src/ui/widgets/indicators.py`: 4% (Kommentare/SLOC)

---

## 5. Ungenutzte/Isolierte Komponenten

### 5.1 Strategie-Klassen (Vermutlich ungenutzt)

**Location:** `src/core/strategy/engine.py`

Die folgenden 5 komplexen Strategy-Klassen sind nur in der Engine definiert und werden nur vom Backtesting-Modul referenziert:

1. `TrendFollowingStrategy` (208 LOC, Komplexität 14)
2. `MeanReversionStrategy` (111 LOC, Komplexität 15)
3. `MomentumStrategy` (94 LOC, Komplexität 14)
4. `BreakoutStrategy` (93 LOC, Komplexität 13)
5. `ScalpingStrategy` (98 LOC, Komplexität 13)

**Status:** Nicht in `src/ui/app.py` importiert oder instanziiert

**Empfehlung:**
- **OPTION 1:** Falls nicht aktiv genutzt → In separate `experimental/` oder `legacy/` Ordner verschieben
- **OPTION 2:** Vollständig entfernen und nur bei Bedarf aus Git-Historie wiederherstellen
- **OPTION 3:** In Main App integrieren falls Funktionalität erwünscht

**Geschätzte LOC für Entfernung:** ~500-600 Zeilen

### 5.2 Broker Adapters

**Definiert in `src/core/broker/`:**
- `alpaca_adapter.py` (494 LOC) - **AKTIV VERWENDET** in app.py
- `ibkr_adapter.py` (532 LOC) - **AKTIV VERWENDET** in app.py
- `trade_republic_adapter.py` (491 LOC) - **AKTIV VERWENDET** in app.py
- `mock_broker.py` (304 LOC) - **AKTIV VERWENDET** in app.py

**Status:** Alle Adapter werden in `app.py` importiert und sind aktiv

---

## 6. Code Smells

### 6.1 Long Method (>50 LOC)

| Datei | Methode | LOC | Komplexität |
|-------|---------|-----|-------------|
| `src/ui/widgets/embedded_tradingview_chart.py` | `_update_indicators` | ~80 | 62 |
| `src/ui/widgets/chart_view.py` | `load_symbol` | ~100 | 36 |
| `src/core/market_data/history_provider.py` | `fetch_bars` (Yahoo) | ~70 | 22 |

### 6.2 Large Class

| Datei | Klasse | LOC | Methoden |
|-------|--------|-----|----------|
| `HistoryManager` | `history_provider.py` | ~600 | 15+ |
| `EmbeddedTradingViewChart` | `embedded_tradingview_chart.py` | ~1300 | 30+ |
| `IndicatorEngine` | `indicators/engine.py` | ~1100 | 20+ |

**Empfehlung:** God Object Anti-Pattern - Klassen haben zu viele Verantwortlichkeiten

### 6.3 Long Parameter List

**Wenige Fälle gefunden** - Projekt nutzt größtenteils Config-Objekte (Good Practice)

### 6.4 Primitive Obsession

**Beobachtet in:** Strategy Engine - viele String-basierte Enum-Vergleiche
**Empfehlung:** Bereits teilweise durch `StrategyType(Enum)` gelöst

---

## 7. Priorisierte Action Items

### Priority 1: KRITISCH (Sofort)

1. **Refactor `EmbeddedTradingViewChart._update_indicators()`**
   - **Datei:** `src/ui/widgets/embedded_tradingview_chart.py:692`
   - **Komplexität:** 62 → Ziel: <10 pro Methode
   - **Aufwand:** 4-6 Stunden
   - **Risiko:** Hoch (viele Chart-Features betroffen)
   - **Tests:** Manuelle Chart-Tests für alle Indikatoren erforderlich

### Priority 2: HOCH (Diese Woche)

2. **Tote Imports entfernen**
   - **Dateien:** 7 Dateien betroffen
   - **Aufwand:** 30 Minuten
   - **Risiko:** Minimal
   - **Tests:** `pytest` sollte ausreichen

3. **Refactor `ChartView.load_symbol()`**
   - **Datei:** `src/ui/widgets/chart_view.py:652`
   - **Komplexität:** 36 → Ziel: <15
   - **Aufwand:** 2-3 Stunden
   - **Risiko:** Mittel

### Priority 3: MITTEL (Nächste 2 Wochen)

4. **Chart Widget Code-Duplikation reduzieren**
   - **Dateien:** `embedded_tradingview_chart.py`, `lightweight_chart.py`, `chart_view.py`
   - **Aufwand:** 6-8 Stunden
   - **Risiko:** Mittel-Hoch (Refactoring über 3 Chart-Implementierungen)
   - **Empfehlung:** Abstract Base Class erstellen

5. **Strategy Classes evaluieren**
   - **Dateien:** `src/core/strategy/engine.py`
   - **Aufwand:** 1-2 Stunden (Analyse) + 2-4 Stunden (Entfernung oder Integration)
   - **Risiko:** Niedrig (wenn nicht verwendet)
   - **Empfehlung:** Mit Product Owner klären ob Features erwünscht

### Priority 4: NIEDRIG (Nächster Monat)

6. **Ungenutzte Exception-Handler-Variablen bereinigen**
   - **Dateien:** `openai_service.py`, `performance.py`, `ibkr_adapter.py`, etc.
   - **Aufwand:** 1 Stunde
   - **Risiko:** Minimal

7. **Große Dateien aufteilen**
   - **Dateien:** `history_provider.py`, `indicators/engine.py`
   - **Aufwand:** 8-12 Stunden pro Datei
   - **Risiko:** Hoch (umfassende Tests erforderlich)

---

## 8. Metrics Summary

### Codebase Overview
- **Total Files:** 57
- **Total LOC:** 21,467
- **Total SLOC:** 13,998
- **Average File Size:** 377 LOC
- **Largest File:** `history_provider.py` (1,664 LOC)

### Complexity Distribution
- **F-Grade (>50):** 1 function (0.3%)
- **E-Grade (30-50):** 1 function (0.3%)
- **D-Grade (20-30):** 1 function (0.3%)
- **C-Grade (10-20):** 33 functions (9.7%)
- **A-B Grade (<10):** ~300+ functions (90%)

### Dead Code
- **Unused Imports:** 7
- **Unused Variables:** 18
- **Unused Classes:** 5 (Strategies - zu verifizieren)

### Code Quality Indicators
- **Average Cyclomatic Complexity:** 15.9 (C-Grade functions)
- **Comment Coverage:** 15% (LOC+Multi)
- **Logical LOC:** 50.7% of total LOC

---

## 9. Risiko-Bewertung für Bereinigung

### Geringes Risiko (Kann sofort durchgeführt werden)
- ✅ Tote Imports entfernen
- ✅ Ungenutzte Exception-Handler-Variablen mit `_` ersetzen
- ✅ Unused IBKR Callback-Parameter mit `_` prefix markieren

### Mittleres Risiko (Tests erforderlich)
- ⚠️ Strategy-Klassen entfernen (falls ungenutzt)
- ⚠️ `ChartView.load_symbol()` refactoring
- ⚠️ `YahooFinanceProvider.fetch_bars()` vereinfachen

### Hohes Risiko (Umfassende Tests und Planung erforderlich)
- 🔴 `EmbeddedTradingViewChart._update_indicators()` refactoring
- 🔴 Chart Widget Code-Duplikation reduzieren
- 🔴 Große Dateien aufteilen

---

## 10. Empfohlene Nächste Schritte

1. **Review Meeting:** Dieser Report mit Team durchgehen
2. **Priority 1 Items bestätigen:** Fokus auf kritische Komplexitäts-Hotspots
3. **Strategie-Klassen klären:** Product Owner fragen ob Features benötigt werden
4. **Quick Wins umsetzen:** Tote Imports entfernen (30 Min Aufwand)
5. **Test-Coverage erhöhen:** Vor großen Refactorings
6. **Schrittweise Bereinigung:** Ein Modul nach dem anderen

---

## Anhang A: Analyse-Kommandos

```bash
# Dead Code Analysis
vulture src/ --min-confidence 80 --sort-by-size

# Complexity Analysis
radon cc src/ -a -s -n C  # Cyclomatic Complexity
radon mi src/ -s -n C     # Maintainability Index

# Raw Metrics
radon raw src/ -s

# Find duplicates (manual inspection)
grep -r "def load_symbol" src/ui/widgets/
grep -r "def _update_indicators" src/ui/widgets/
```

---

**WICHTIG:** Dies ist eine ANALYSE - keine Änderungen wurden am Code vorgenommen. Alle Löschungen oder Refactorings bedürfen expliziter Freigabe nach Review dieses Reports.
