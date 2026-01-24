# ✅ Checkliste: Orderpilot Entry Analyzer → 2-Stufen Regime-Optimierung

**Start:** 2026-01-24  
**Letzte Aktualisierung:** 2026-01-24  
**Gesamtfortschritt:** 0% (0/72 Tasks)

---

## 📋 **PROJEKT-KONTEXT**

### **Ausgangslage (IST-Zustand):**
- Entry Analyzer hat 3 Tabs: **Setup**, **Parameter Presets**, **Results**
- Regime-Erkennung und Indikator-Optimierung in einem Schritt
- Config-Pfad: `03_JSON\Entry_Analyzer\Regime\entry_analyzer_regime.json`

### **Ziel (SOLL-Zustand): 2-Stufen Sequentieller Workflow**

```
┌─────────────────────────────────────────────────────────────────────────┐
│  STUFE 1: Regime-Optimierung                                            │
│  • Indikatoren: ADX, SMA_Fast, SMA_Slow, RSI, BB Width                 │
│  • Klassifikation: ADX+SMA basiert (NICHT RSI/MACD!)                   │
│  • Speichern: optimized_regime_BTCUSDT_5m.json                          │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│  STUFE 2: Indikator-Set-Optimierung (PRO REGIME SEPARAT!)               │
│  • Indikatoren: RSI, MACD, STOCH, BB, ATR, EMA, CCI (7 Stück)          │
│  • Pro Regime: Entry-Long, Entry-Short, Exit-Long, Exit-Short          │
│  • Speichern: indicator_sets_BULL/BEAR/SIDEWAYS_BTCUSDT_5m.json        │
└─────────────────────────────────────────────────────────────────────────┘
```

### **⚠️ KRITISCHE REGELN**

```
┌─────────────────────────────────────────────────────────────────────────┐
│  STUFE-1 INDIKATOREN (Regime-Erkennung):                               │
│  ✓ ADX, SMA_Fast, SMA_Slow, RSI, BB Width                              │
│  ✗ NICHT: MACD (das ist Stufe 2!)                                      │
├─────────────────────────────────────────────────────────────────────────┤
│  REGIME-KLASSIFIKATION:                                                 │
│  BULL:     ADX > threshold AND Close > SMA_Fast AND SMA_Fast > SMA_Slow│
│  BEAR:     ADX > threshold AND Close < SMA_Fast AND SMA_Fast < SMA_Slow│
│  SIDEWAYS: ADX < threshold AND BB_Width < percentile AND RSI 40-60     │
├─────────────────────────────────────────────────────────────────────────┤
│  STUFE-2 INDIKATOREN (Entry/Exit):                                     │
│  ✓ RSI, MACD, STOCH, BB, ATR, EMA, CCI (7 Stück)                       │
├─────────────────────────────────────────────────────────────────────────┤
│  PERFORMANCE: KEIN Grid Search! → Optuna TPE (2000x schneller)         │
└─────────────────────────────────────────────────────────────────────────┘
```

### **Regime-Mapping & Farben**

| Regime | Farbe | Hex Code |
|--------|-------|----------|
| **BULL** | Grün | `#26a69a` |
| **BEAR** | Rot | `#ef5350` |
| **SIDEWAYS** | Grau | `#9e9e9e` |

---

## 📊 Status-Legende
- ⬜ Offen | 🔄 In Arbeit | ✅ Abgeschlossen | ❌ Fehler

---

## Phase 0: Analyse & Vorbereitung (4 Stunden)

- [ ] **0.1 Bestehenden Code analysieren**  
  Status: ⬜ → *Entry Analyzer Tabs, RegimeOptimizationThread*
- [ ] **0.2 Abhängigkeiten dokumentieren**  
  Status: ⬜ → *Welche Klassen nutzen die alten Tabs?*
- [ ] **0.3 JSON-Schemas validieren**  
  Status: ⬜ → *4 neue Schemas gegen ConditionEvaluator testen*
- [ ] **0.4 Datenbasis für Tests vorbereiten**  
  Status: ⬜ → *Sample-Daten mit bekannten Regime-Perioden*

---

## Phase 0.5: Performance-Optimierung Setup (2 Stunden) ⚡ NEU

- [ ] **0.5.1 Optuna installieren**  
  Status: ⬜ → `pip install optuna optuna-dashboard`
- [ ] **0.5.2 TPESampler konfigurieren**  
  Status: ⬜ → `multivariate=True, n_startup_trials=20`
- [ ] **0.5.3 HyperbandPruner einrichten**  
  Status: ⬜ → `min_resource=1, max_resource=100, reduction_factor=3`
- [ ] **0.5.4 SQLite Storage für Optuna**  
  Status: ⬜ → `sqlite:///optuna_regime.db`

```python
# Referenz-Code für Phase 0.5
import optuna
from optuna.samplers import TPESampler
from optuna.pruners import HyperbandPruner

sampler = TPESampler(n_startup_trials=20, multivariate=True, seed=42)
pruner = HyperbandPruner(min_resource=1, max_resource=100, reduction_factor=3)
study = optuna.create_study(direction="maximize", sampler=sampler, pruner=pruner)
```

---

## Phase 1: Stufe-1 Core Classes (10 Stunden)

### 1.1 RegimeOptimizer Klasse (6 Stunden)
- [ ] **1.1.1 RegimeOptimizer erstellen**  
  Status: ⬜ → *Datei: src/core/regime_optimizer.py*
- [ ] **1.1.2 TPE Optimization Implementation**  
  Status: ⬜ → *Optuna statt Grid Search!*
- [ ] **1.1.3 Korrekte Indikatoren: ADX, SMA_Fast, SMA_Slow, RSI, BB Width**  
  Status: ⬜ → *NICHT MACD!*
- [ ] **1.1.4 Korrekte Regime-Klassifikation**  
  Status: ⬜ → *ADX+SMA basiert, nicht RSI/MACD*
- [ ] **1.1.5 Composite Score Berechnung**  
  Status: ⬜ → *F1-Bull (25%), F1-Bear (30%), F1-Sideways (20%), Stability (25%)*
- [ ] **1.1.6 Bar-Indices pro Regime speichern**  
  Status: ⬜ → *Welche Bars gehören zu BULL/BEAR/SIDEWAYS (für Stufe 2)*

### 1.2 RegimeResultsManager Klasse (4 Stunden)
- [ ] **1.2.1 RegimeResultsManager erstellen**  
  Status: ⬜ → *Datei: src/core/regime_results_manager.py*
- [ ] **1.2.2 Sortierung & Ranking**  
  Status: ⬜ → *Nach Score sortieren, Ränge vergeben*
- [ ] **1.2.3 Export regime_optimization_results.json**  
  Status: ⬜ → *Alle Ergebnisse speichern*
- [ ] **1.2.4 Export optimized_regime.json**  
  Status: ⬜ → *Gewählte Config mit Bar-Indices exportieren*

---

## Phase 2: Stufe-2 Core Classes (12 Stunden)

### 2.1 IndicatorSetOptimizer Klasse (8 Stunden)
- [ ] **2.1.1 IndicatorSetOptimizer erstellen**  
  Status: ⬜ → *Datei: src/core/indicator_set_optimizer.py*
- [ ] **2.1.2 Regime-Filter Implementation**  
  Status: ⬜ → *Nur Bars des ausgewählten Regimes verwenden*
- [ ] **2.1.3 Alle 7 Indikatoren: RSI, MACD, STOCH, BB, ATR, EMA, CCI**  
  Status: ⬜ → *Nicht nur 5!*
- [ ] **2.1.4 TPE Optimization pro Indikator**  
  Status: ⬜ → *40 trials pro Indikator*
- [ ] **2.1.5 Signal-Backtest: Entry-Long**  
  Status: ⬜ → *Trades simulieren, Metriken berechnen*
- [ ] **2.1.6 Signal-Backtest: Entry-Short**  
  Status: ⬜ → *Trades simulieren, Metriken berechnen*
- [ ] **2.1.7 Signal-Backtest: Exit-Long**  
  Status: ⬜ → *Exit-Timing bewerten*
- [ ] **2.1.8 Signal-Backtest: Exit-Short**  
  Status: ⬜ → *Exit-Timing bewerten*
- [ ] **2.1.9 Metriken-Berechnung**  
  Status: ⬜ → *Win Rate, Profit Factor, Sharpe, Drawdown, Expectancy*
- [ ] **2.1.10 Condition Generator**  
  Status: ⬜ → *left/op/right Format für ConditionEvaluator*

### 2.2 IndicatorResultsManager Klasse (4 Stunden)
- [ ] **2.2.1 IndicatorResultsManager erstellen**  
  Status: ⬜ → *Datei: src/core/indicator_results_manager.py*
- [ ] **2.2.2 Ergebnisse pro Signal-Typ sortieren**  
  Status: ⬜ → *4 Listen: Entry-Long, Entry-Short, Exit-Long, Exit-Short*
- [ ] **2.2.3 Export indicator_optimization_results.json**  
  Status: ⬜ → *Pro Regime eine Datei*
- [ ] **2.2.4 Export indicator_sets.json**  
  Status: ⬜ → *Beste Sets pro Regime exportieren*

---

## Phase 3: UI-Widget Implementation (20 Stunden)

### 3.1 Stufe-1 UI: Regime-Optimierung (8 Stunden)
- [ ] **3.1.1 Tab "Regime Setup"**  
  Status: ⬜ → *Parameter-Ranges, Auto/Manual Toggle, Kombinationen-Counter*
- [ ] **3.1.2 Tab "Regime Optimization"**  
  Status: ⬜ → *Start/Stop, Progress, Live Top-5 Table*
- [ ] **3.1.3 Tab "Regime Results"**  
  Status: ⬜ → *Full Table, Auswahl, Export, "Apply & Continue" Button*
- [ ] **3.1.4 RegimeOptimizationWorker Thread**  
  Status: ⬜ → *QThread mit progress, result_ready, finished Signals*
- [ ] **3.1.5 Chart-Integration: Regime-Perioden anzeigen**  
  Status: ⬜ → *BULL=#26a69a, BEAR=#ef5350, SIDEWAYS=#9e9e9e*

### 3.2 Stufe-2 UI: Indikator-Optimierung (12 Stunden)
- [ ] **3.2.1 Tab "Indicator Setup"**  
  Status: ⬜ → *Regime-Dropdown, Indikator-Auswahl, Parameter-Ranges*
- [ ] **3.2.2 Signal-Type Selector**  
  Status: ⬜ → *Checkboxes: Entry-Long, Entry-Short, Exit-Long, Exit-Short*
- [ ] **3.2.3 Tab "Indicator Optimization"**  
  Status: ⬜ → *Pro Regime: Start/Stop, Progress, Live Results*
- [ ] **3.2.4 Tab "Indicator Results"**  
  Status: ⬜ → *Regime-Dropdown, 4 Sub-Tabellen, Export*
- [ ] **3.2.5 IndicatorOptimizationWorker Thread**  
  Status: ⬜ → *QThread für Indikator-Tests*
- [ ] **3.2.6 Ergebnistabelle mit Score-Sortierung**  
  Status: ⬜ → *Sortierung nach Score pro Signal-Type*
- [ ] **3.2.7 Selection & Export pro Regime**  
  Status: ⬜ → *Auswahl → indicator_sets_BULL/BEAR/SIDEWAYS.json*
- [ ] **3.2.8 Chart-Integration: Gewählte Regime hervorheben**  
  Status: ⬜ → *Bei Indikator-Test nur Regime-Bars färben*

---

## Phase 4: Integration & Migration (8 Stunden)

### 4.1 Alte Tabs entfernen (3 Stunden)
- [ ] **4.1.1 entry_analyzer_setup_tab.py LÖSCHEN**  
  Status: ⬜ → *Komplett entfernen*
- [ ] **4.1.2 entry_analyzer_presets_tab.py LÖSCHEN**  
  Status: ⬜ → *Komplett entfernen*
- [ ] **4.1.3 entry_analyzer_results_tab.py LÖSCHEN**  
  Status: ⬜ → *Komplett entfernen*
- [ ] **4.1.4 Alte RegimeOptimizationThread entfernen**  
  Status: ⬜ → *Durch neue Worker ersetzen*
- [ ] **4.1.5 Imports bereinigen**  
  Status: ⬜ → *Ungenutzte Imports entfernen*

### 4.2 Neue Tabs integrieren (3 Stunden)
- [ ] **4.2.1 MainWindow: 4 neue Tabs registrieren**  
  Status: ⬜ → *Regime Setup, Regime Results, Indicator Setup, Indicator Results*
- [ ] **4.2.2 Signal-Verbindungen herstellen**  
  Status: ⬜ → *Regime Results → Indicator Setup Übergang*
- [ ] **4.2.3 Datei-Pfade konfigurieren**  
  Status: ⬜ → *STUFE_1_Regime/, STUFE_2_Indicators/BULL|BEAR|SIDEWAYS/*

### 4.3 Chart-Integration (2 Stunden)
- [ ] **4.3.1 _draw_regime_lines() aktualisieren**  
  Status: ⬜ → *3 Farben: BULL, BEAR, SIDEWAYS*
- [ ] **4.3.2 Regime-Perioden aus JSON laden**  
  Status: ⬜ → *regime_periods Array verwenden*

---

## Phase 5: Testing & Cleanup (10 Stunden)

### 5.1 Unit Tests (6 Stunden)
- [ ] **5.1.1 RegimeOptimizer Tests**  
  Status: ⬜ → *TPE, Score Calculation, Korrekte Indikatoren*
- [ ] **5.1.2 Test: Korrekte Klassifikationslogik**  
  Status: ⬜ → *BULL=Close>SMA_Fast>SMA_Slow, nicht RSI/MACD*
- [ ] **5.1.3 IndicatorSetOptimizer Tests**  
  Status: ⬜ → *Regime-Filter, Backtest, 4 Signal-Types, 7 Indikatoren*
- [ ] **5.1.4 RegimeResultsManager Tests**  
  Status: ⬜ → *Sorting, Export*
- [ ] **5.1.5 IndicatorResultsManager Tests**  
  Status: ⬜ → *Pro-Regime Export*
- [ ] **5.1.6 JSON Schema Validation Tests**  
  Status: ⬜ → *Alle 4 Schemas gegen Beispiele*

### 5.2 Integration Tests (2 Stunden)
- [ ] **5.2.1 End-to-End Stufe 1**  
  Status: ⬜ → *Daten laden → Regime optimieren → Export*
- [ ] **5.2.2 End-to-End Stufe 2**  
  Status: ⬜ → *Regime laden → Indikator optimieren → 3 Exports*

### 5.3 Final Cleanup (2 Stunden)
- [ ] **5.3.1 Dead Code Scan**  
  Status: ⬜ → *vulture src/*
- [ ] **5.3.2 Import-Bereinigung**  
  Status: ⬜ → *autoflake + isort*
- [ ] **5.3.3 Code-Formatierung**  
  Status: ⬜ → *black + flake8*
- [ ] **5.3.4 Alte Regime-Namen entfernen**  
  Status: ⬜ → *STRONG_TREND_BULL → BULL, etc.*

---

## 📈 Fortschritts-Tracking

### Gesamt-Statistik
- **Total Tasks:** 72
- **Abgeschlossen:** 0 (0%)
- **In Arbeit:** 0 (0%)
- **Offen:** 72 (100%)

### Phase-Statistik
| Phase | Tasks | Abgeschlossen | Fortschritt |
|-------|-------|---------------|-------------|
| Phase 0 | 4 | 0 | ⬜ 0% |
| Phase 0.5 | 4 | 0 | ⬜ 0% |
| Phase 1 | 10 | 0 | ⬜ 0% |
| Phase 2 | 14 | 0 | ⬜ 0% |
| Phase 3 | 18 | 0 | ⬜ 0% |
| Phase 4 | 11 | 0 | ⬜ 0% |
| Phase 5 | 11 | 0 | ⬜ 0% |

### Zeitschätzung
- **Geschätzte Gesamtzeit:** 66-74 Stunden (2-3 Wochen)

---

## 📁 Datei-Struktur (Ziel)

```
03_JSON/Entry_Analyzer/Regime/
├── schemas/
│   ├── regime_optimization_results.schema.json
│   ├── optimized_regime_config.schema.json
│   ├── indicator_optimization_results.schema.json
│   └── optimized_indicator_sets.schema.json
│
├── STUFE_1_Regime/
│   ├── regime_optimization_results_BTCUSDT_5m.json
│   └── optimized_regime_BTCUSDT_5m.json
│
└── STUFE_2_Indicators/
    ├── BULL/
    │   ├── indicator_optimization_results_BULL_BTCUSDT_5m.json
    │   └── indicator_sets_BULL_BTCUSDT_5m.json
    ├── BEAR/
    │   ├── indicator_optimization_results_BEAR_BTCUSDT_5m.json
    │   └── indicator_sets_BEAR_BTCUSDT_5m.json
    └── SIDEWAYS/
        ├── indicator_optimization_results_SIDEWAYS_BTCUSDT_5m.json
        └── indicator_sets_SIDEWAYS_BTCUSDT_5m.json
```

---

## 📄 Referenz-Dokumente

1. **README_JSON_FORMATE.md** - Workflow-Diagramm
2. **PERFORMANCE_OPTIMIERUNG.md** - TPE/Optuna Best Practices
3. **PROMPT_Claude_CLI_Regime_Optimierung.md** - Implementierungs-Anleitung
4. **schemas/*.schema.json** - 4 JSON-Schemas
5. **examples/** - Beispiel-JSONs für beide Stufen

---

**Letzte Aktualisierung:** 2026-01-24
