# Advanced Backtesting Features - Projektplan

> **Datum:** 2026-01-24
> **Datenquelle:** `\data\orderpilot_historical.db`
> **Datenmenge:** 365 Tage × 1min Kerzen → 105.120 5min Kerzen
> **Status:** Planung

---

## Übersicht

Mit 105.000+ Kerzen haben wir genug Daten für professionelle Backtesting-Methoden, die in der Industrie Standard sind. Dieser Plan beschreibt drei Hauptfeatures:

1. **Walk-Forward-Analyse** - Robustheitsprüfung der Optimierung
2. **Marktphasen-Analyse** - Regime-spezifische Performance
3. **Out-of-Sample Validierung** - Overfitting-Erkennung

---

## 1. Walk-Forward-Analyse (WFA)

### 1.1 Konzept

Walk-Forward ist der Goldstandard für Strategie-Validierung. Anstatt auf allen Daten zu optimieren (Overfitting-Gefahr), wird iterativ optimiert und getestet:

```
|-------- IN-SAMPLE (Training) --------|--- OUT-OF-SAMPLE (Test) ---|
|        Optimierung hier              |    Validierung hier        |

Fenster 1: [████████████████████████████][░░░░░░░░]
Fenster 2:        [████████████████████████████][░░░░░░░░]
Fenster 3:               [████████████████████████████][░░░░░░░░]
           ────────────────────────────────────────────────────────►
                                Zeit
```

### 1.2 Parameter

| Parameter | Empfehlung | Beschreibung |
|-----------|------------|--------------|
| In-Sample Länge | 60-90 Tage | Optimierungsfenster |
| Out-of-Sample Länge | 15-30 Tage | Testfenster |
| Schritt-Größe | 15-30 Tage | Verschiebung pro Iteration |
| Mindest-Fenster | 200 Kerzen | Warmup-Periode |

### 1.3 Implementierungsplan

```python
# Pseudocode Walk-Forward Engine

class WalkForwardAnalyzer:
    def __init__(self, data: pd.DataFrame):
        self.data = data
        self.in_sample_days = 60
        self.out_sample_days = 15
        self.step_days = 15

    def run(self) -> WalkForwardResult:
        results = []

        for window in self._generate_windows():
            # 1. Optimiere auf In-Sample
            optimizer = RegimeOptimizer(window.in_sample_data)
            best_params = optimizer.optimize()

            # 2. Teste auf Out-of-Sample (OHNE Optimierung!)
            oos_score = self._evaluate(window.out_sample_data, best_params)

            results.append({
                "window": window.id,
                "in_sample_score": best_params.score,
                "out_sample_score": oos_score,
                "params": best_params,
                "period": window.date_range
            })

        return WalkForwardResult(results)
```

### 1.4 Metriken

- **Walk-Forward Efficiency (WFE):** `OOS_Score / IS_Score`
  - WFE > 0.5 = Gut
  - WFE > 0.7 = Sehr gut
  - WFE < 0.3 = Overfitting-Warnung

- **Konsistenz:** Standardabweichung der OOS-Scores
- **Robustheit:** Wie oft ist OOS-Score > Schwellenwert?

### 1.5 UI-Integration

```
┌─────────────────────────────────────────────────────────────┐
│ Walk-Forward Analyse                                        │
├─────────────────────────────────────────────────────────────┤
│ In-Sample Tage:  [60 ▼]    Out-of-Sample Tage: [15 ▼]      │
│ Schritt-Größe:   [15 ▼]    Trials pro Fenster: [50 ▼]      │
│                                                             │
│ [▶ Start Walk-Forward]                                      │
├─────────────────────────────────────────────────────────────┤
│ Fenster │ Zeitraum          │ IS-Score │ OOS-Score │ WFE   │
│---------|-------------------|----------|-----------|-------|
│    1    │ Jan-Feb → Mär     │   82.3   │   71.2    │ 0.87  │
│    2    │ Feb-Mär → Apr     │   79.1   │   68.5    │ 0.87  │
│    3    │ Mär-Apr → Mai     │   85.2   │   52.1    │ 0.61  │
│   ...   │                   │          │           │       │
├─────────────────────────────────────────────────────────────┤
│ Gesamt WFE: 0.72 ✅  │  Konsistenz: 8.3  │  Robustheit: 85% │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Marktphasen-Analyse (Bull/Bear/Sideways)

### 2.1 Konzept

Verschiedene Marktphasen erfordern unterschiedliche Parameter. Wir analysieren die Performance pro Phase separat:

```
2025-01 ──────────────────────────────────────────── 2026-01
        │ BULL  │ SIDEWAYS │  BEAR  │ RECOVERY │ BULL │
        └───────┴──────────┴────────┴──────────┴──────┘
```

### 2.2 Phasen-Erkennung

**Automatische Erkennung basierend auf:**
- SMA(50) vs SMA(200) Crossover
- ADX > 25 (Trending) vs ADX < 20 (Sideways)
- Preis-Performance über 30 Tage

**Manuelle Annotation:**
- Bekannte Events (z.B. Bitcoin ETF Approval, Fed Meetings)
- Nachträglich identifizierte Phasen

### 2.3 Implementierungsplan

```python
class MarketPhaseAnalyzer:
    def __init__(self, data: pd.DataFrame):
        self.data = data

    def detect_phases(self) -> list[MarketPhase]:
        """Automatische Phasen-Erkennung."""
        phases = []

        # Berechne Indikatoren
        sma50 = self.data['close'].rolling(50).mean()
        sma200 = self.data['close'].rolling(200).mean()
        adx = calculate_adx(self.data, 14)

        # Klassifiziere jeden Abschnitt
        for segment in self._segment_data():
            if adx.mean() < 20:
                phase_type = "SIDEWAYS"
            elif sma50.iloc[-1] > sma200.iloc[-1]:
                phase_type = "BULL"
            else:
                phase_type = "BEAR"

            phases.append(MarketPhase(
                start=segment.start,
                end=segment.end,
                type=phase_type,
                confidence=self._calculate_confidence(segment)
            ))

        return phases

    def analyze_per_phase(self, params: RegimeParams) -> dict:
        """Performance pro Marktphase analysieren."""
        results = {}

        for phase in self.phases:
            phase_data = self.data[phase.start:phase.end]
            score = evaluate_regime(phase_data, params)

            results[phase.type] = {
                "score": score,
                "trades": count_trades(phase_data, params),
                "win_rate": calculate_win_rate(phase_data, params),
                "duration_days": (phase.end - phase.start).days
            }

        return results
```

### 2.4 UI-Integration

```
┌─────────────────────────────────────────────────────────────┐
│ Marktphasen-Analyse                                         │
├─────────────────────────────────────────────────────────────┤
│ [▶ Phasen erkennen]  [✏ Manuell bearbeiten]                │
├─────────────────────────────────────────────────────────────┤
│ Erkannte Phasen:                                            │
│ ┌─────────┬──────────────────┬────────┬─────────┐          │
│ │  Phase  │     Zeitraum     │  Tage  │ Kerzen  │          │
│ ├─────────┼──────────────────┼────────┼─────────┤          │
│ │  BULL   │ 2025-01 - 2025-03│   62   │  17,856 │          │
│ │ SIDEWAYS│ 2025-03 - 2025-05│   58   │  16,704 │          │
│ │  BEAR   │ 2025-05 - 2025-08│   91   │  26,208 │          │
│ │  BULL   │ 2025-08 - 2026-01│  154   │  44,352 │          │
│ └─────────┴──────────────────┴────────┴─────────┘          │
├─────────────────────────────────────────────────────────────┤
│ Performance pro Phase (aktuelle Parameter):                 │
│ ┌─────────┬────────┬──────────┬───────────┐                │
│ │  Phase  │ Score  │ Win Rate │  Trades   │                │
│ ├─────────┼────────┼──────────┼───────────┤                │
│ │  BULL   │  78.5  │   62.3%  │    127    │                │
│ │ SIDEWAYS│  45.2  │   48.1%  │     89    │ ⚠️ Schwach    │
│ │  BEAR   │  71.8  │   58.7%  │    156    │                │
│ └─────────┴────────┴──────────┴───────────┘                │
│                                                             │
│ [▶ Optimierung pro Phase starten]                          │
└─────────────────────────────────────────────────────────────┘
```

### 2.5 Phasen-spezifische Optimierung

Option: Separate Parameter-Sets pro Marktphase optimieren:

```json
{
  "regime_params": {
    "BULL": {
      "adx_threshold": 22,
      "rsi_period": 12,
      "sma_fast": 20,
      "sma_slow": 100
    },
    "BEAR": {
      "adx_threshold": 28,
      "rsi_period": 16,
      "sma_fast": 30,
      "sma_slow": 150
    },
    "SIDEWAYS": {
      "adx_threshold": 18,
      "rsi_period": 14,
      "sma_fast": 10,
      "sma_slow": 50
    }
  }
}
```

---

## 3. Out-of-Sample (OOS) Validierung

### 3.1 Konzept

Einfachste Form der Validierung: Daten aufteilen in Training und Test.

```
|============ 70% TRAINING ============|==== 30% TEST ====|
        Optimierung hier                Niemals anfassen!
```

### 3.2 Aufteilungs-Strategien

| Strategie | Training | Test | Verwendung |
|-----------|----------|------|------------|
| 70/30 Split | 255 Tage | 110 Tage | Standard |
| 80/20 Split | 292 Tage | 73 Tage | Mehr Training |
| Zeitbasiert | Bis Datum X | Ab Datum X | Realistische Simulation |

### 3.3 Implementierungsplan

```python
class OutOfSampleValidator:
    def __init__(self, data: pd.DataFrame, split_ratio: float = 0.7):
        self.split_idx = int(len(data) * split_ratio)
        self.train_data = data.iloc[:self.split_idx]
        self.test_data = data.iloc[self.split_idx:]

    def validate(self) -> ValidationResult:
        # 1. Optimiere NUR auf Training
        optimizer = RegimeOptimizer(self.train_data)
        best_params = optimizer.optimize()
        train_score = best_params.score

        # 2. Evaluiere auf Test (KEINE Optimierung!)
        test_score = evaluate_regime(self.test_data, best_params)

        # 3. Berechne Overfitting-Metriken
        degradation = (train_score - test_score) / train_score

        return ValidationResult(
            train_score=train_score,
            test_score=test_score,
            degradation_pct=degradation * 100,
            is_overfit=degradation > 0.3,  # >30% Degradation = Overfitting
            params=best_params
        )
```

### 3.4 Overfitting-Erkennung

| Degradation | Bewertung | Aktion |
|-------------|-----------|--------|
| < 10% | Excellent | Parameter verwenden |
| 10-20% | Gut | Akzeptabel |
| 20-30% | Grenzwertig | Vorsicht, weniger Trials |
| > 30% | Overfitting | Parameter verwerfen! |

### 3.5 UI-Integration

```
┌─────────────────────────────────────────────────────────────┐
│ Out-of-Sample Validierung                                   │
├─────────────────────────────────────────────────────────────┤
│ Split: [70% ▼] Training  │  [30% ▼] Test                   │
│                                                             │
│ Training: 2025-01-01 bis 2025-09-20 (73.584 Kerzen)        │
│ Test:     2025-09-20 bis 2026-01-01 (31.536 Kerzen)        │
│                                                             │
│ [▶ Validierung starten]                                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   Training Score:  82.5                                     │
│   Test Score:      71.3                                     │
│   ─────────────────────                                     │
│   Degradation:     13.6% ✅ Gut                             │
│                                                             │
│   ┌────────────────────────────────────────┐               │
│   │ ████████████████████████████░░░░░░░░░░ │ Train: 82.5   │
│   │ ███████████████████████░░░░░░░░░░░░░░░ │ Test:  71.3   │
│   └────────────────────────────────────────┘               │
│                                                             │
│   Bewertung: Parameter sind robust, minimales Overfitting   │
│                                                             │
│ [💾 Parameter anwenden]  [📊 Details anzeigen]              │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. Implementierungs-Roadmap

### Phase 1: Grundlagen (1-2 Wochen)

- [ ] Daten-Splitter Utility erstellen
- [ ] `WalkForwardWindow` Datenklasse
- [ ] `MarketPhase` Datenklasse
- [ ] `ValidationResult` Datenklasse
- [ ] Basis-Evaluierungsfunktion (Score ohne Optimierung)

### Phase 2: Out-of-Sample Validierung (1 Woche)

- [ ] `OutOfSampleValidator` Klasse
- [ ] UI-Tab "OOS Validierung" in Entry Analyzer
- [ ] Degradation-Berechnung und Visualisierung
- [ ] Export der Validierungsergebnisse

### Phase 3: Marktphasen-Analyse (1-2 Wochen)

- [ ] `MarketPhaseAnalyzer` Klasse
- [ ] Automatische Phasen-Erkennung (ADX/SMA basiert)
- [ ] UI für Phasen-Übersicht
- [ ] Performance-pro-Phase Tabelle
- [ ] Manuelle Phasen-Annotation (optional)

### Phase 4: Walk-Forward-Analyse (2-3 Wochen)

- [ ] `WalkForwardAnalyzer` Klasse
- [ ] Fenster-Generator
- [ ] Parallele Optimierung pro Fenster (optional)
- [ ] WFE und Konsistenz-Metriken
- [ ] UI-Tab "Walk-Forward"
- [ ] Ergebnis-Export (CSV/JSON)

### Phase 5: Integration & Reporting (1 Woche)

- [ ] Kombinierte Analyse (WF + Phasen + OOS)
- [ ] PDF-Report Generator
- [ ] Empfehlungs-Engine ("Welche Parameter sind am robustesten?")
- [ ] Vergleich verschiedener Optimierungs-Runs

---

## 5. Technische Anforderungen

### 5.1 Performance

Mit 105.000 Kerzen und mehreren Analyse-Fenstern:

- Walk-Forward mit 10 Fenstern × 50 Trials = 500 Optimierungen
- Geschätzte Zeit: 5-15 Minuten (je nach Hardware)
- **Empfehlung:** Threading/Multiprocessing für Fenster

### 5.2 Speicher

- ~105.000 Kerzen × 6 Spalten × 8 Bytes = ~5 MB RAM
- Plus Indikatoren: ~20 MB RAM
- Gesamt pro Fenster: ~25-50 MB
- **Kein Problem für moderne Systeme**

### 5.3 Datenbank-Schema (für Ergebnisse)

```sql
CREATE TABLE walk_forward_results (
    id INTEGER PRIMARY KEY,
    run_timestamp DATETIME,
    window_id INTEGER,
    in_sample_start DATE,
    in_sample_end DATE,
    out_sample_start DATE,
    out_sample_end DATE,
    in_sample_score REAL,
    out_sample_score REAL,
    wfe REAL,
    params_json TEXT
);

CREATE TABLE market_phases (
    id INTEGER PRIMARY KEY,
    phase_type TEXT,  -- BULL, BEAR, SIDEWAYS
    start_date DATE,
    end_date DATE,
    confidence REAL,
    is_manual BOOLEAN
);
```

---

## 6. Erwartete Ergebnisse

Nach Implementierung dieser Features:

1. **Bessere Parameter-Auswahl**
   - Nur Parameter verwenden, die OOS-Validierung bestehen
   - Walk-Forward zeigt Konsistenz über Zeit

2. **Marktphasen-Awareness**
   - Wissen, in welchen Phasen die Strategie funktioniert
   - Optional: Phasen-spezifische Parameter

3. **Overfitting-Prävention**
   - Klare Metriken für Überanpassung
   - Automatische Warnungen bei Degradation > 30%

4. **Professionelles Reporting**
   - Industrie-Standard Backtesting-Methoden
   - Nachvollziehbare Ergebnisse für Dokumentation

---

## 7. Referenzen

- Pardo, R. (2008). "The Evaluation and Optimization of Trading Strategies"
- Walk-Forward Optimization: https://www.investopedia.com/terms/w/walk-forward-testing.asp
- Out-of-Sample Testing: https://www.quantconnect.com/tutorials/strategy-library/out-of-sample-testing

---

*Erstellt: 2026-01-24*
*Projekt: OrderPilot-AI Entry Analyzer*
