# 📚 Regime-Based JSON Strategy System - Dokumentation

**Projekt:** OrderPilot-AI - JSON Strategy Migration
**Version:** 2.0
**Erstellt:** 2026-01-18
**Basis:** `01_Projectplan/Strategien_Workflow_json/json Format Strategien Indikatoren.md`

---

## 🎯 Überblick

Diese Dokumentation beschreibt die Migration von **hardcodierten Trading-Strategien** zu einem **Regime-basierten JSON-Konfigurationssystem**.

### Kernkonzepte

1. **Multi-Timeframe Indikatoren** - Indikatoren auf verschiedenen Zeitrahmen (1h, 4h, 1d)
2. **Regime Detection** - Automatische Marktphasen-Erkennung (Trend, Range, Low-Volume)
3. **Strategy Sets** - Strategiebündel mit Parameter-Overrides
4. **Dynamic Routing** - Regime → Strategy-Set Zuordnung
5. **Condition System** - Flexible Bedingungslogik (gt, lt, eq, between mit all/any)

---

## 📂 Dokumentationsstruktur

| Dokument | Beschreibung | Zielgruppe | Größe |
|----------|--------------|------------|-------|
| **[RegimeBasedJSON_Integration_Plan.md](RegimeBasedJSON_Integration_Plan.md)** | Vollständiger technischer Integrationsplan | Entwickler, Architekten | 38 KB |
| **[Quick_Start_JSON_Config.md](Quick_Start_JSON_Config.md)** | Schnelleinstieg & Beispiele | Entwickler (Quick Start) | 15 KB |
| **[CHECKLISTE_RegimeBasedJSON_Implementation.md](CHECKLISTE_RegimeBasedJSON_Implementation.md)** | Detaillierte Implementierungs-Checkliste | Projektmanager, Entwickler | 18 KB |

**Gesamt:** 71 KB, 2.651 Zeilen Dokumentation

---

## 🚀 Wo anfangen?

### Für Entwickler (Hands-On)
1. ✅ **Lesen:** [Quick_Start_JSON_Config.md](Quick_Start_JSON_Config.md) (Abschnitt 1-3)
2. ✅ **Minimal-Beispiel:** Kopiere JSON aus Abschnitt 2
3. ✅ **Validieren:** `python tools/validate_config.py`
4. ✅ **Testen:** Bot mit JSON-Config starten

### Für Projektplanung
1. ✅ **Lesen:** [RegimeBasedJSON_Integration_Plan.md](RegimeBasedJSON_Integration_Plan.md)
2. ✅ **Review:** Architektur, Phasen, Risiken
3. ✅ **Tracking:** [CHECKLISTE_RegimeBasedJSON_Implementation.md](CHECKLISTE_RegimeBasedJSON_Implementation.md)
4. ✅ **Timeline:** 5-6 Wochen, 140 Stunden

### Für schnellen Überblick
1. ✅ **Executive Summary:** [RegimeBasedJSON_Integration_Plan.md - Abschnitt 1](RegimeBasedJSON_Integration_Plan.md#📋-executive-summary)
2. ✅ **Beispiele:** [Quick_Start_JSON_Config.md - Abschnitt 2-5](Quick_Start_JSON_Config.md#2-minimales-beispiel-10-minuten)

---

## 📖 Inhaltsübersicht

### RegimeBasedJSON_Integration_Plan.md

**Abschnitte:**
1. **Executive Summary** - Projektziel, Status Quo, Ziel-Architektur
2. **JSON Schema - Komponenten** - Indicators, Regimes, Strategies, Strategy Sets, Routing
3. **Implementierungsplan** - 7 Phasen, detaillierte Tasks
4. **Verzeichnisstruktur** - 03_JSON Organisation
5. **Migration-Strategie** - Schritt-für-Schritt Anleitung
6. **Deliverables & Meilensteine** - Wöchentliche Ziele
7. **Testing-Strategie** - Unit & Integration Tests
8. **Rollout Plan** - Alpha, Beta, Production

**Highlights:**
- ✅ Vollständige Pydantic Models mit Code-Beispielen
- ✅ ConditionEvaluator Implementation (200+ LOC)
- ✅ RegimeDetector Implementation (150+ LOC)
- ✅ StrategyRouter & Executor (250+ LOC)
- ✅ Migration Tool (200+ LOC)

---

### Quick_Start_JSON_Config.md

**Abschnitte:**
1. **Grundkonzepte** (5 Min) - Was ist neu?
2. **Minimales Beispiel** (10 Min) - Erste JSON-Config
3. **Multi-Timeframe Setup** (15 Min) - Robuste Signale
4. **Regime-Scopes** (20 Min) - Entry/Exit-Regimes
5. **Parameter-Overrides** (25 Min) - Anpassung ohne Duplikate
6. **Condition Operatoren** (10 Min) - gt, lt, eq, between
7. **Validierung & Debugging** (15 Min) - Tools & Tipps
8. **Migration** (30 Min) - Hardcoded → JSON
9. **Best Practices** (10 Min) - DO's & DON'Ts
10. **Troubleshooting** (15 Min) - Häufige Fehler

**Highlights:**
- ✅ 10 praxisnahe Beispiele
- ✅ Copy-Paste-ready JSON-Snippets
- ✅ Debug-Tool mit Output-Beispielen
- ✅ Migration Schritt-für-Schritt

---

### CHECKLISTE_RegimeBasedJSON_Implementation.md

**Aufbau:**
- **Code-Qualitäts-Standards** - Was vor jedem Task beachten
- **Status-Legende** - Tracking-Symbole
- **Tracking-Format** - Beispiele für erfolgreiche/fehlgeschlagene Tasks
- **7 Phasen** - 98 Tasks insgesamt
- **Fortschritts-Tracking** - Statistiken, Zeitschätzung
- **Kritische Pfade** - Abhängigkeiten
- **Risiken & Mitigationen** - 6 identifizierte Risiken
- **Qualitätsziele** - Performance & Coverage Targets
- **Review Checkpoints** - Wöchentliche Reviews

**Highlights:**
- ✅ 98 detaillierte Tasks
- ✅ 140 Stunden geschätzt
- ✅ Code-Qualitäts-Checkliste vor jedem Task
- ✅ Tracking-Format-Beispiele
- ✅ Wöchentliche Review-Checkpoints

---

## 🔧 Implementierungsphasen

| Phase | Dauer | Tasks | Fokus |
|-------|-------|-------|-------|
| **Phase 0: Vorbereitung** | 0.5 Tag | 5 | Setup, Backup, Git |
| **Phase 1: Core Infrastructure** | 1.5 Wochen | 20 | JSON Schema, Pydantic, ConfigLoader |
| **Phase 2: Condition Evaluator** | 1 Woche | 15 | Condition Logic, Regime Detection |
| **Phase 3: Strategy Routing** | 1 Woche | 13 | Router, Executor, Overrides |
| **Phase 4: Bot Integration** | 1 Woche | 15 | BotController, Multi-Timeframe |
| **Phase 5: Migration & Testing** | 1 Woche | 18 | Migration Tool, Tests |
| **Phase 6: AI Analysis** | 1 Woche | 8 | Backtest, Optimizer |
| **Phase 7: Production** | 1 Woche | 14 | UI, Docs, Polish |

**Gesamt:** 5-6 Wochen, 140 Stunden

---

## 📊 Beispiel: JSON Config

**Minimal-Config:**
```json
{
  "schema_version": "1.0",
  "indicators": [
    { "id": "rsi14", "type": "RSI", "params": { "period": 14 } }
  ],
  "regimes": [
    {
      "id": "trending",
      "name": "Trending Market",
      "conditions": {
        "all": [
          {
            "left": { "indicator_id": "rsi14", "field": "value" },
            "op": "gt",
            "right": { "value": 60 }
          }
        ]
      }
    }
  ],
  "strategies": [ ... ],
  "strategy_sets": [ ... ],
  "routing": [ ... ]
}
```

**Vollständige Beispiele:**
- `Quick_Start_JSON_Config.md` Abschnitt 2-5
- `01_Projectplan/Strategien_Workflow_json/json Format Strategien Indikatoren.md` (Beispiel A & B)

---

## 🧪 Testing

### Unit Tests (85% Coverage Target)
- ✅ Pydantic Models
- ✅ ConfigLoader (Valid/Invalid JSON)
- ✅ ConditionEvaluator (alle Operatoren)
- ✅ RegimeDetector (Multi-Regime)
- ✅ StrategyRouter (Matching-Logic)
- ✅ StrategySetExecutor (Overrides)

### Integration Tests
- ✅ Full Routing Flow (Regime → Strategy → Execution)
- ✅ Multi-Timeframe Calculation
- ✅ Override Mechanism
- ✅ Fallback to Hardcoded

### Performance Tests
- ✅ Config Load: < 100ms
- ✅ Regime Detection: < 20ms
- ✅ Strategy Routing: < 10ms
- ✅ Multi-TF Calculation: < 50ms

---

## ⚠️ Wichtige Hinweise

### Kritische Punkte
1. **JSON Schema muss korrekt sein** - Alle Komponenten basieren darauf
2. **Multi-Regime Support** - Mehrere Regimes gleichzeitig aktiv
3. **Override State Management** - Indicator State nach Execution wiederherstellen
4. **Migration vollständig** - Alle 9 Strategien müssen migriert werden
5. **Backward Compatibility** - Fallback zu hardcoded muss funktionieren

### Risiken
| Risiko | Mitigation |
|--------|-----------|
| Schema-Design fehlerhaft | 2 Reviewer vor Finalisierung |
| Multi-TF Performance | Aggressive Caching |
| Override Bugs | Immutable Indicator Objects |
| Migration Errors | Jede Strategie einzeln validieren |
| User Complexity | UI Wizard + Templates |

---

## 🎯 Success Metrics

- **Validierung:** 100% aller JSON Configs validieren
- **Performance:** < 50ms für Regime-Detection + Routing
- **Test Coverage:** > 85%
- **Backward Compatibility:** 100% (Fallback zu hardcoded)
- **Migration Success:** 100% aller Strategien migriert

---

## 📞 Support & Nächste Schritte

### Nächste Schritte
1. ✅ **Review** - Alle 3 Dokumente durchlesen
2. ✅ **Planung** - Timeline & Ressourcen festlegen
3. ✅ **Kickoff** - Phase 0 starten (Vorbereitung)
4. ✅ **Implementation** - Checkliste abarbeiten
5. ✅ **Testing** - Continuous Testing ab Phase 1

### Bei Fragen
- **Technisch:** Siehe [RegimeBasedJSON_Integration_Plan.md](RegimeBasedJSON_Integration_Plan.md)
- **Quick Help:** Siehe [Quick_Start_JSON_Config.md](Quick_Start_JSON_Config.md)
- **Progress:** Siehe [CHECKLISTE_RegimeBasedJSON_Implementation.md](CHECKLISTE_RegimeBasedJSON_Implementation.md)

---

## 📁 Dateipfade

### Dokumentation
```
docs/integration/
├── README.md                                          # Diese Datei
├── RegimeBasedJSON_Integration_Plan.md               # Hauptplan
├── Quick_Start_JSON_Config.md                        # Quick Start
└── CHECKLISTE_RegimeBasedJSON_Implementation.md      # Checkliste
```

### Basis-Projektplan
```
01_Projectplan/Strategien_Workflow_json/
└── json Format Strategien Indikatoren.md              # Original Schema
```

### Ziel-Verzeichnisse (werden erstellt)
```
03_JSON/
├── Trading_Bot/
│   ├── configs/          # Production Configs
│   └── templates/        # Config Templates
└── AI_Analyse/
    ├── configs/          # Test Configs
    ├── results/          # Backtest Results
    └── optimization/     # Parameter Optimization
```

---

**Status:** ✅ Dokumentation Complete
**Last Updated:** 2026-01-18
**Erstellt von:** Claude Code (Sonnet 4.5)
