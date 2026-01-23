# Claude-CLI Prompt: Orderpilot 2-Stufen Regime-Optimierung

## Sofort ausführbarer Prompt

```
Du bist ein Senior Python-Entwickler und implementierst ein 2-Stufen Regime-Optimierungssystem für den Orderpilot-AI Trading Bot.

## PROJEKT-KONTEXT: 2-STUFEN SEQUENTIELLER WORKFLOW

### STUFE 1: Regime-Optimierung
- Parameter-Varianten testen (ADX Period/Threshold, RSI Period)
- Einstellbar: Auto-Modus (System wählt Ranges) oder Manual (Benutzer definiert)
- Beste Kombination für BULL/BEAR/SIDEWAYS Erkennung finden
- Speichern: 
  • regime_optimization_results_BTCUSDT_5m.json (alle Ergebnisse)
  • optimized_regime_BTCUSDT_5m.json (gewählte Config mit Bar-Indices)
- Chart zeigt Regime-Perioden mit Farben an

### STUFE 2: Indikator-Set-Optimierung (PRO REGIME SEPARAT!)
- Für JEDES Regime (BULL, BEAR, SIDEWAYS) SEPARAT optimieren
- NUR die Bars des jeweiligen Regimes verwenden!
- 4 Durchläufe pro Regime: Entry-Long, Entry-Short, Exit-Long, Exit-Short
- Indikatoren testen: RSI, MACD, STOCH, BB, EMA (mit vielen Parameter-Varianten)
- Einstellbar: Auto (maximale Varianten) oder Manual (feste Anzahl)
- Speichern PRO REGIME:
  • indicator_optimization_results_BULL_BTCUSDT_5m.json (alle Ergebnisse)
  • indicator_sets_BULL_BTCUSDT_5m.json (beste Entry/Exit Sets)
  • (analog für BEAR und SIDEWAYS)

## REGIME-MAPPING & FARBEN

| Regime | Farbe | Hex Code |
|--------|-------|----------|
| BULL | Grün | #26a69a |
| BEAR | Rot | #ef5350 |
| SIDEWAYS | Grau | #9e9e9e |

## DATEI-STRUKTUR

```
03_JSON/Entry_Analyzer/Regime/
├── STUFE_1_Regime/
│   ├── regime_optimization_results_*.json
│   └── optimized_regime_*.json
└── STUFE_2_Indicators/
    ├── BULL/
    │   ├── indicator_optimization_results_BULL_*.json
    │   └── indicator_sets_BULL_*.json
    ├── BEAR/
    │   └── ...
    └── SIDEWAYS/
        └── ...
```

## KRITISCHE ANWEISUNG: CODE-BEREINIGUNG

⚠️ NACH JEDER IMPLEMENTIERUNGSPHASE:
1. ALTER CODE MUSS VOLLSTÄNDIG ENTFERNT WERDEN
2. KEINE auskommentierten Funktionen/Klassen
3. KEINE "old_*" oder "_backup" Dateien
4. KEINE unbenutzten Imports
5. Alte Regime-Namen (STRONG_TREND_BULL, etc.) KOMPLETT durch BULL/BEAR/SIDEWAYS ersetzen

## IMPLEMENTATION

### Phase 1: Stufe-1 Core Classes
Erstelle in src/core/:
1. regime_optimizer.py
   - Grid-Search mit Auto/Manual Modus
   - Composite Score: F1-Bull (25%), F1-Bear (30%), F1-Sideways (20%), Stability (25%)
   - Bar-Indices pro Regime speichern (für Stufe 2)
2. regime_results_manager.py
   - Export: regime_optimization_results.json + optimized_regime.json

### Phase 2: Stufe-2 Core Classes
1. indicator_set_optimizer.py
   - Regime-Filter: Nur Bars des ausgewählten Regimes verwenden!
   - 4 Signal-Types: Entry-Long, Entry-Short, Exit-Long, Exit-Short
   - Metriken: Win Rate, Profit Factor, Sharpe, Drawdown
2. indicator_results_manager.py
   - Export pro Regime: indicator_sets_BULL/BEAR/SIDEWAYS.json

### Phase 3: UI-Widgets
Stufe-1 Tabs:
- "Regime Setup" - Parameter-Ranges, Auto/Manual Toggle
- "Regime Results" - Ergebnistabelle, "Apply & Continue" Button

Stufe-2 Tabs:
- "Indicator Setup" - Regime-Dropdown, Indikator-Auswahl
- "Indicator Results" - Pro Regime: 4 Sub-Tabellen, Export

### Phase 4: Integration
1. LÖSCHE alte Tabs komplett
2. Chart: 3 Farben (BULL=#26a69a, BEAR=#ef5350, SIDEWAYS=#9e9e9e)

## QUALITÄTSSTANDARDS

✅ ERFORDERLICH:
- Vollständige Implementation
- Error Handling
- Type Hints
- Docstrings
- Unit Tests

❌ VERBOTEN:
- # TODO
- # def old_function():
- except: pass
- Alte Regime-Namen

## ARBEITSWEISE

1. Lies CHECKLISTE_Regime_Optimierung_Refactoring.md
2. Arbeite Phase für Phase ab
3. Nach jeder Phase: Code-Bereinigung!
4. Dokumentiere gelöschten Code

Beginne mit Phase 0: Analyse & Vorbereitung.
```

---

## Kurzprompt

```
Implementiere 2-Stufen Regime-Optimierung für Orderpilot-AI:

STUFE 1: Regime-Erkennung optimieren → optimized_regime.json (mit Bar-Indices)
STUFE 2: Pro Regime (BULL/BEAR/SIDEWAYS) separat Indikatoren optimieren
         → indicator_sets_BULL.json, indicator_sets_BEAR.json, indicator_sets_SIDEWAYS.json

WICHTIG: In Stufe 2 NUR die Bars des jeweiligen Regimes verwenden!

Farben: BULL=#26a69a, BEAR=#ef5350, SIDEWAYS=#9e9e9e

Nach jeder Phase ALTER CODE KOMPLETT LÖSCHEN.

Lies: CHECKLISTE_Regime_Optimierung_Refactoring.md, README_JSON_FORMATE.md
```

---

## Phasen-spezifische Prompts

### Phase 1 starten (Stufe-1 Core):
```
Implementiere Phase 1: Stufe-1 Core Classes

Erstelle:
1. src/core/regime_optimizer.py
   - grid_search() mit Auto/Manual Modus
   - classify_regime() → BULL, BEAR, SIDEWAYS
   - composite_score() → F1-Bull (25%), F1-Bear (30%), F1-Sideways (20%), Stability (25%)
   - get_regime_bar_indices() → Dict mit Arrays der Bar-Indices pro Regime

2. src/core/regime_results_manager.py
   - sort_results()
   - export_optimization_results() → regime_optimization_results.json
   - export_regime_config() → optimized_regime.json (mit bar_indices!)

Nutze schemas/regime_optimization_results.schema.json und optimized_regime_config.schema.json
```

### Phase 2 starten (Stufe-2 Core):
```
Implementiere Phase 2: Stufe-2 Core Classes

Erstelle:
1. src/core/indicator_set_optimizer.py
   - load_regime_config() → Bar-Indices laden
   - filter_bars_for_regime(regime: str) → Nur BULL/BEAR/SIDEWAYS Bars!
   - optimize_signal(signal_type: str, regime: str) → Entry-Long/Short, Exit-Long/Short
   - backtest_indicator() → Win Rate, Profit Factor, Sharpe
   - generate_conditions() → left/op/right Format

2. src/core/indicator_results_manager.py
   - export_per_regime() → indicator_sets_BULL.json, indicator_sets_BEAR.json, indicator_sets_SIDEWAYS.json

KRITISCH: Stufe 2 muss die Bar-Indices aus Stufe 1 verwenden!
```

### Phase 3 starten (UI):
```
Implementiere Phase 3: UI-Widgets

Stufe-1 Tabs:
1. RegimeSetupTab
   - Parameter SpinBoxes (ADX Period/Threshold, RSI Period)
   - Auto/Manual ComboBox
   - Kombinationen-Counter
   - "Start Optimization" Button

2. RegimeResultsTab
   - QTableWidget mit Rank, Score, Params, F1-Scores
   - Sortierung nach Score
   - "Apply & Continue to Indicator Optimization" Button → Speichert Config, wechselt Tab

Stufe-2 Tabs:
3. IndicatorSetupTab
   - Regime ComboBox (BULL/BEAR/SIDEWAYS oder "Alle")
   - Indikator Checkboxes (RSI, MACD, STOCH, BB, EMA)
   - Signal-Type Checkboxes (Entry-Long, Entry-Short, Exit-Long, Exit-Short)
   - "Start Optimization" Button

4. IndicatorResultsTab
   - Regime Dropdown
   - 4 QTableWidgets (Entry-Long, Entry-Short, Exit-Long, Exit-Short)
   - Auswahl pro Signal-Type
   - "Export Selected" Button → indicator_sets_BULL/BEAR/SIDEWAYS.json
```

### Phase 4 starten (Integration):
```
Implementiere Phase 4: Integration & Migration

1. LÖSCHE alte Dateien:
   - src/ui/tabs/entry_analyzer_setup_tab.py
   - src/ui/tabs/entry_analyzer_presets_tab.py
   - src/ui/tabs/entry_analyzer_results_tab.py

2. Aktualisiere MainWindow:
   - 4 neue Tabs registrieren
   - Signal-Verbindungen: Regime Results → Indicator Setup

3. Chart-Integration:
   - _draw_regime_lines() aktualisieren
   - 3 Farben: BULL=#26a69a, BEAR=#ef5350, SIDEWAYS=#9e9e9e
   - regime_periods Array aus JSON verwenden

WICHTIG: Alter Code wird GELÖSCHT, nicht auskommentiert!
```
