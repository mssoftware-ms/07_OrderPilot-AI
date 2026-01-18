# Umsetzungsplan: CEL Rule Engine & Erweiterte Marktanalyse

**Erstellt:** 2026-01-18
**Status:** Analyse & Planung
**Version:** 1.0

---

## Executive Summary

Dieser Plan integriert zwei Hauptanforderungen in die bestehende OrderPilot-AI Trading-Plattform:

1. **CEL-basierte Rule Engine** für flexible Trading-Regeln (no_trade, entry, exit, update_stop, risk)
2. **Erweiterte Marktanalyse** mit Regime-Klassifikation (R0-R5), Indikator-Optimierung, und Scoring-System

**Kritische Erkenntnis:** Sehr viel Infrastruktur ist **bereits vorhanden**:
- ✅ JSON-basiertes Config-System (ConfigLoader, RegimeDetector, StrategyRouter)
- ✅ Backtesting-Engine mit Regime-Tracking
- ✅ FeatureEngine mit Standard-Indikatoren
- ✅ Integration-Tests für Regime-basierte Workflows

**Hauptaufgaben:**
1. **CEL-Integration** in bestehendes Condition-Evaluation-System
2. **Regime-Engine Erweiterung** von 3 auf 6 Regime (R0-R5) mit Orderflow
3. **Indikator-Katalog** & **Scoring-Pipeline** für 0-100 Bewertungen
4. **Marktanalyse.json** Schema-Implementierung
5. **UI-Integration** für Regime-Visualisierung und Indikator-Optimierung

---

## 1. Überschneidungsanalyse: Bestehend vs. Neu

### 1.1 Regime-Klassifikation

| Feature | Bestand (`regime_engine.py`) | Neu (CEL_Rules_Doku + Projektzusammenfassung) |
|---------|------------------------------|-----------------------------------------------|
| **Regime-Typen** | 3 (TREND_UP, TREND_DOWN, RANGE) | 6 (R0-R5: Neutral, Trend, Range, Breakout, High-Vol, Orderflow) |
| **Volatilität** | ✅ 4 Stufen (LOW, NORMAL, HIGH, EXTREME) | ✅ Ähnlich (ATR%, BBWidth) |
| **Indikatoren** | ADX, ATR%, BBWidth | ADX, CHOP, Ichimoku, TTM Squeeze, OBI, BBWidth, ATRP |
| **Anti-Flap** | ❌ Nicht vorhanden | ✅ confirm_bars, cooldown_bars, min_segment_bars |
| **Richtung** | ±DI für Trend | ±DI, Ichimoku, Donchian, OBI |
| **Confidence** | ✅ regime_confidence | ✅ Kompatibel |

**Fazit:** Regime-Engine muss **erweitert, nicht ersetzt** werden.

---

### 1.2 Condition Evaluation

| Feature | Bestand (`config/evaluator.py`) | Neu (CEL Rules) |
|---------|----------------------------------|------------------|
| **Sprache** | Pydantic-Modelle + Python-Conditions | CEL-Expressions (String-basiert) |
| **Operatoren** | gt, lt, eq, between | gt, lt, eq, between + in, ternary, functions |
| **Logik** | all (AND), any (OR) | && (AND), \|\| (OR), ! (NOT) |
| **Lookback** | ❌ Nicht direkt | ✅ lag(x,n), x[-n] |
| **Functions** | ❌ Nur Operatoren | ✅ pctl, sma, ema, crossover, isnull, nz |
| **Safety** | Python-Runtime | CEL-Sandbox (non-Turing complete) |

**Fazit:** CEL kann als **Backend-Engine für Evaluator** dienen, JSON-Schema bleibt Schnittstelle.

---

### 1.3 Backtesting

| Feature | Bestand (`backtesting/engine.py`) | Neu (Projektzusammenfassung) |
|---------|-----------------------------------|------------------------------|
| **Multi-Timeframe** | ✅ Resampling + Forward-Fill | ✅ Kompatibel |
| **Regime-Tracking** | ✅ regime_history mit timestamps | ✅ Segmente mit Start/End + Features |
| **Indikator-Berechnung** | ✅ pandas_ta (RSI, SMA, ADX, MACD) | ✅ Erweitern für Ichimoku, CHOP, Aroon, OBI |
| **Scoring** | ❌ Nur Profit Factor, Win Rate, Sharpe (TODO) | ✅ 0-100 Percentile-Rank über mehrere Metriken |
| **Regime-Segmente** | ❌ Nur History-Array | ✅ Segment-Features (range_pct, atrp, bbwidth, obi) |
| **Einzelindikator-Tests** | ❌ Nur Strategy-Combos | ✅ Entry-Track, Exit-Track, Regime-Track isoliert |

**Fazit:** Backtest-Engine braucht **Erweiterung für Scoring & Segmentierung**, Basis ist solide.

---

### 1.4 Feature-Berechnung

| Feature | Bestand (`feature_engine.py`) | Neu (Indikator-Katalog) |
|---------|-------------------------------|-------------------------|
| **Overlay** | SMA, EMA, BB | + Ichimoku, Supertrend, Parabolic SAR, Donchian, Keltner, Pivot, VWAP |
| **Panel** | RSI, MACD, ADX, Stoch, CCI, MFI, ATR | + CHOP, Aroon, Vortex, Hurst |
| **Orderflow** | ❌ Nicht vorhanden | OBI, Spread (bps), Depth Bid/Ask |
| **Perzentile** | ❌ Nicht vorhanden | pctl(x, p, window) |

**Fazit:** Feature-Engine gut erweiterbar, **neue Indikatoren + Orderflow hinzufügen**.

---

### 1.5 JSON-Config-System

| Feature | Bestand (`config/`) | Neu (RulePack JSON + Marktanalyse.json) |
|---------|---------------------|----------------------------------------|
| **Schema** | ✅ TradingBotConfig (Pydantic) | ✅ RulePack + Marktanalyse (JSON Schema Draft 2020-12) |
| **Indicators** | ✅ id, type, params, timeframe | ✅ Kompatibel |
| **Regimes** | ✅ id, name, conditions | ✅ Erweitern für R0-R5 + when/direction_expr |
| **Strategies** | ✅ entry/exit conditions, risk | ✅ Kompatibel |
| **Routing** | ✅ all_of, any_of, none_of | ✅ Kompatibel |
| **Rules** | ❌ Nicht vorhanden | ✅ RulePack mit severity (block, exit, update_stop) |
| **Segments** | ❌ Nicht vorhanden | ✅ Marktanalyse.json mit Segmenten + Features |
| **Indicator Runs** | ❌ Nicht vorhanden | ✅ Scores pro Indikator-Parameterset + Regime |

**Fazit:** Config-System ist **bereits sehr gut**, braucht nur **Erweiterung für Rules + Marktanalyse**.

---

## 2. Architektur-Entscheidungen (ADRs)

### ADR-001: CEL als Evaluation-Backend

**Entscheidung:** CEL-Python (celpy) wird als Backend-Engine für `ConditionEvaluator` integriert, **nicht als Ersatz** des JSON-Schemas.

**Rationale:**
1. **Safety:** CEL ist non-Turing complete, keine while-Loops, kein Memory Leak Risk
2. **Performance:** Compilation-Pattern mit Caching (Microsecond-Evaluation)
3. **Flexibilität:** Custom Functions (pctl, crossover, lag) für Trading-Use-Cases
4. **Gradual Migration:** JSON-Schema bleibt, CEL ist optionales Backend

**Architektur:**
```python
# Alte Condition (Pydantic)
{
  "type": "condition",
  "indicator": "rsi_14",
  "operator": "gt",
  "value": 50
}

# Neue CEL-Expression (in JSON eingebettet)
{
  "type": "cel_expression",
  "expr": "rsi_14 > 50 && volume > pctl(volume, 20, 288)"
}

# Beide werden von ConditionEvaluator unterstützt:
class ConditionEvaluator:
    def __init__(self):
        self.cel_env = celpy.Environment()  # NEU
        self.cel_cache = {}                  # Compiled expressions

    def evaluate(self, condition, context):
        if condition.type == "cel_expression":
            return self._eval_cel(condition.expr, context)
        else:
            return self._eval_pydantic(condition)  # Bestehende Logik
```

**Trade-offs:**
- ✅ Keine Breaking Changes für bestehende Configs
- ✅ Schrittweise Migration möglich
- ❌ Zwei Evaluation-Pfade (Komplexität)

**Mitigation:** Tests für beide Pfade, klare Doku welcher wann verwendet wird.

---

### ADR-002: Regime-Engine Hybrid-Ansatz

**Entscheidung:** Regime-Engine wird **erweitert** um R0-R5 Taxonomie, aber **existierende 3-Regime-API bleibt** für Backward Compatibility.

**Architektur:**
```python
class RegimeEngine:
    # Alte API (bleibt)
    def classify(self, features: FeatureVector) -> RegimeState:
        """Simple 3-regime classification (TREND_UP/DOWN/RANGE)."""
        ...

    # Neue API (erweitert)
    def classify_extended(self, features: FeatureVector) -> ExtendedRegimeState:
        """R0-R5 classification with orderflow, breakout, etc."""
        regime_id = self._composite_regime_detection(features)
        direction = self._detect_direction(features, regime_id)
        return ExtendedRegimeState(
            regime_id=regime_id,       # R0-R5
            direction=direction,       # UP, DOWN, NONE
            volatility=...,
            confidence=...,
            features={                  # Segment-Features
                'atrp': ...,
                'range_pct': ...,
                'bbwidth': ...,
                'obi': ...
            }
        )

    def _composite_regime_detection(self, features):
        # Priority-based logic:
        if features.obi and abs(features.obi) > percentile(features.obi, 90):
            return RegimeID.R5  # Orderflow
        if features.squeeze_on or features.bbwidth < percentile(..., 20):
            return RegimeID.R3  # Breakout Setup
        if features.atrp > percentile(..., 80):
            return RegimeID.R4  # High Volatility
        if features.adx > 25 or features.chop < 38.2:
            return RegimeID.R1  # Trend
        if features.adx < 20 or features.chop > 61.8:
            return RegimeID.R2  # Range
        return RegimeID.R0  # Neutral
```

**Trade-offs:**
- ✅ Bestehende Strategien brechen nicht
- ✅ Neue Strategies können Extended nutzen
- ❌ Zwei Regime-Systeme parallel (Komplexität)

**Mitigation:** Klare Doku, Tests für beide APIs.

---

### ADR-003: Indikator-Katalog als YAML

**Entscheidung:** Indikator-Definitionen werden in **YAML-Datei** mit Metadaten gepflegt, nicht hardcoded.

**Struktur:**
```yaml
# config/indicators/catalog.yaml
indicators:
  - id: adx
    type: panel
    family: trend_strength
    roles: [regime, entry, exit]
    best_regimes: [R1, R0, R2]
    grid:
      "5m":
        length: [7, 10, 14, 20]
      "1D":
        length: [10, 14, 20, 28]

  - id: supertrend
    type: overlay
    family: trend_following
    roles: [regime, entry, exit]
    best_regimes: [R1, R3]
    grid:
      "5m":
        atr_len: [7, 10, 14]
        mult: [2.0, 2.5, 3.0, 4.0]
```

**Vorteile:**
- ✅ Single Source of Truth
- ✅ Einfach erweiterbar (kein Code-Change)
- ✅ Grid-Search für Optimization direkt im Katalog
- ✅ Metadaten (roles, best_regimes) für intelligentes Routing

---

### ADR-004: Marktanalyse.json als Persistenz-Format

**Entscheidung:** Ergebnisse der Entry-Analyzer-Runs werden in **Marktanalyse.json** gespeichert, nicht in Datenbank.

**Rationale:**
1. **Portabilität:** JSON kann versioniert (Git), geteilt, archiviert werden
2. **Schema-Validation:** JSON Schema Draft 2020-12 für Typsicherheit
3. **Human-Readable:** Analysen können manuell reviewed werden
4. **Einfachheit:** Keine DB-Migrations, kein ORM-Overhead

**Schema (Auszug):**
```json
{
  "meta": {
    "symbol": "BTCUSDT",
    "exchange": "bitunix",
    "timeframes": ["5m", "1D"],
    "start_date": "2024-01-01T00:00:00Z",
    "end_date": "2024-12-31T23:59:59Z",
    "generator": "OrderPilot-AI Entry Analyzer",
    "version": "1.0.0"
  },
  "regime_engine": {
    "classifier": "composite_v1",
    "rules": [...],
    "anti_flap": {
      "confirm_bars": 3,
      "cooldown_bars": 5,
      "min_segment_bars": 10
    }
  },
  "segments": [
    {
      "id": "seg_001",
      "start_idx": 0,
      "end_idx": 287,
      "regime": "R1",
      "direction": "UP",
      "features": {
        "range_pct": 1.85,
        "atrp": 0.60,
        "bbwidth": 0.024,
        "squeeze_on": false,
        "obi": null
      }
    }
  ],
  "indicator_runs": [
    {
      "id": "run_001",
      "indicator": "rsi",
      "params": {"period": 14},
      "timeframe": "5m",
      "regime": "R1",
      "track": "entry",
      "metrics": {
        "profit_factor": 1.85,
        "expectancy": 0.012,
        "sortino": 1.42,
        "max_dd": -0.08,
        "win_rate": 0.58
      },
      "score": 72.3
    }
  ],
  "regime_set": {
    "R1": {
      "entries": [
        {
          "indicator": "rsi",
          "params": {"period": 14},
          "weight": 0.35,
          "score": 72.3
        },
        {
          "indicator": "macd",
          "params": {"fast": 12, "slow": 26, "signal": 9},
          "weight": 0.40,
          "score": 78.1
        }
      ],
      "exits": [...]
    }
  }
}
```

---

### ADR-005: Scoring mit Percentile-Rank

**Entscheidung:** Scores werden als **Percentile-Rank (0-100)** über alle Kandidaten berechnet, nicht als absolute Werte.

**Rationale:**
1. **Normalisierung:** Verschiedene Metriken (Profit Factor, Sharpe, Max DD) werden vergleichbar
2. **Regime-spezifisch:** Jedes Regime hat eigene Score-Verteilung
3. **Robustheit:** Outlier haben weniger Impact als bei Normalisierung auf Min/Max

**Formel:**
```python
def percentile_rank_score(metric_value, all_values):
    """
    Returns score 0-100 where 100 = best (highest percentile).
    For "smaller is better" metrics (e.g. Max DD), invert.
    """
    rank = sum(1 for v in all_values if v < metric_value)
    return 100 * rank / len(all_values)

# Composite Score (weighted)
composite_score = (
    0.30 * percentile_rank(profit_factor, ...) +
    0.25 * percentile_rank(expectancy, ...) +
    0.20 * percentile_rank(sortino, ...) +
    0.15 * (100 - percentile_rank(max_dd, ...)) +  # Invert (smaller better)
    0.10 * percentile_rank(win_rate, ...)
)
```

---

## 3. Implementierungsplan (7 Phasen)

### Phase 0: Setup & Dependencies (1-2 Tage)

**Ziel:** Entwicklungsumgebung vorbereiten, Dependencies installieren

**Tasks:**
1. **Python CEL installieren**
   ```bash
   pip install cel-python  # oder python-cel (Rust-backed)
   ```
2. **YAML-Parser** (für Indikator-Katalog)
   ```bash
   pip install pyyaml
   ```
3. **Zusätzliche Indikatoren** (falls nicht in pandas_ta)
   ```bash
   pip install ta-lib  # Optional für Ichimoku, Aroon, VWAP
   ```
4. **JSON Schema Validator**
   ```bash
   pip install jsonschema
   ```

**Deliverables:**
- Updated `requirements.txt` / `pyproject.toml`
- Environment-Tests (CEL imports, YAML loads)

**Risiken:**
- ta-lib kann schwierig zu installieren sein (C-Dependencies) → Alternative: pandas_ta hat meiste Indikatoren

---

### Phase 1: CEL-Integration in ConditionEvaluator (3-4 Tage)

**Ziel:** CEL als optionales Backend für Condition-Evaluation

**Tasks:**
1. **CEL-Environment Setup** (`src/core/tradingbot/config/cel_engine.py`)
   ```python
   from celpy import Environment, Runner

   class CELEngine:
       def __init__(self):
           self.env = Environment()
           self.cache = {}

       def compile(self, expr: str):
           if expr not in self.cache:
               ast = self.env.compile(expr)
               self.cache[expr] = self.env.program(ast)
           return self.cache[expr]

       def evaluate(self, expr: str, context: dict):
           program = self.compile(expr)
           runner = Runner(program)
           return runner.evaluate(context)
   ```

2. **Custom Functions registrieren**
   ```python
   # Percentile
   def pctl(series, p, window):
       return np.percentile(series[-window:], p)

   # Crossover
   def crossover(a, b):
       return a[-2] < b[-2] and a[-1] > b[-1]

   # isnull, nz, coalesce
   def isnull(x):
       return x is None or pd.isna(x)

   self.env.add_function('pctl', pctl)
   self.env.add_function('crossover', crossover)
   self.env.add_function('isnull', isnull)
   ```

3. **ConditionEvaluator erweitern**
   ```python
   class ConditionEvaluator:
       def __init__(self, ...):
           self.cel_engine = CELEngine()  # NEU

       def evaluate(self, condition, context):
           if hasattr(condition, 'cel_expr'):
               # Neue CEL-Expression
               return self.cel_engine.evaluate(condition.cel_expr, context)
           else:
               # Bestehende Pydantic-Condition
               return self._eval_pydantic(condition, context)
   ```

4. **Pydantic-Modell erweitern**
   ```python
   # In schema_types.py
   class Condition(BaseModel):
       # Bestehende Felder
       type: Literal["condition", "cel_expression"]
       indicator: str | None = None
       operator: str | None = None
       value: float | None = None

       # NEU
       cel_expr: str | None = None  # Wenn type == "cel_expression"
   ```

5. **Unit-Tests**
   - Test einfache CEL-Expressions: `rsi_14 > 50`
   - Test komplexe: `volume > pctl(volume, 20, 288) && atrp < 0.2`
   - Test Custom Functions: `crossover(sma_fast, sma_slow)`
   - Test Error-Handling: Syntax-Fehler, Missing Context-Keys

**Deliverables:**
- `src/core/tradingbot/config/cel_engine.py`
- Modified `src/core/tradingbot/config/evaluator.py`
- Updated `src/backtesting/schema_types.py` (Pydantic Models)
- `tests/unit/test_cel_engine.py` (20+ Tests)

**Akzeptanzkriterien:**
- ✅ CEL-Expressions evaluieren korrekt
- ✅ Custom Functions (pctl, crossover) funktionieren
- ✅ Compilation-Caching funktioniert (Performance)
- ✅ Fehlerhafte Expressions werfen Exception mit klarer Fehlermeldung
- ✅ Bestehende Pydantic-Conditions weiterhin funktionsfähig

---

### Phase 2: Regime-Engine Erweiterung (R0-R5) (5-6 Tage)

**Ziel:** RegimeEngine um R0-R5 Taxonomie erweitern, Anti-Flap-Logik

**Tasks:**
1. **Neue Enum-Definitionen** (`src/core/tradingbot/models.py`)
   ```python
   class RegimeID(str, Enum):
       R0 = "R0"  # Neutral
       R1 = "R1"  # Trend
       R2 = "R2"  # Range
       R3 = "R3"  # Breakout
       R4 = "R4"  # High Volatility
       R5 = "R5"  # Orderflow

   class Direction(str, Enum):
       UP = "UP"
       DOWN = "DOWN"
       NONE = "NONE"

   @dataclass
   class ExtendedRegimeState:
       regime_id: RegimeID
       direction: Direction
       volatility: VolatilityLevel
       confidence: float
       features: dict[str, float | None]  # atrp, range_pct, bbwidth, obi, etc.
   ```

2. **Composite Regime Detection** (`src/core/tradingbot/regime_engine.py`)
   ```python
   def classify_extended(self, features: FeatureVector) -> ExtendedRegimeState:
       # 1. Berechne Segment-Features
       segment_features = self._calc_segment_features(features)

       # 2. Priority-basierte Regime-Detektion
       regime_id = self._composite_detect(segment_features)

       # 3. Richtung bestimmen
       direction = self._detect_direction(segment_features, regime_id)

       # 4. Confidence berechnen
       confidence = self._calc_confidence(segment_features, regime_id)

       return ExtendedRegimeState(
           regime_id=regime_id,
           direction=direction,
           volatility=self._classify_volatility(features),
           confidence=confidence,
           features=segment_features
       )

   def _composite_detect(self, features: dict) -> RegimeID:
       # Priority 1: Orderflow
       if features.get('obi') and abs(features['obi']) > features.get('obi_pctl_90', 0.7):
           return RegimeID.R5

       # Priority 2: Breakout Setup
       if features.get('squeeze_on') or features.get('bbwidth_pctl', 50) < 20:
           return RegimeID.R3

       # Priority 3: High Volatility
       if features.get('atrp_pctl', 50) > 80 or features.get('bbwidth_pctl', 50) > 80:
           return RegimeID.R4

       # Priority 4: Trend
       if features.get('adx', 0) > 25 or features.get('chop', 50) < 38.2:
           return RegimeID.R1

       # Priority 5: Range
       if features.get('adx', 0) < 20 or features.get('chop', 50) > 61.8:
           return RegimeID.R2

       # Default: Neutral
       return RegimeID.R0
   ```

3. **Segment-Features berechnen**
   ```python
   def _calc_segment_features(self, features: FeatureVector) -> dict:
       return {
           'atrp': features.atr_14 / features.close * 100 if features.atr_14 else None,
           'bbwidth': features.bb_width,  # Schon in FeatureVector
           'range_pct': self._calc_range_pct(features),  # HH-LL über N Bars
           'squeeze_on': self._is_squeeze_on(features),
           'obi': features.obi if hasattr(features, 'obi') else None,
           'adx': features.adx,
           'chop': features.chop if hasattr(features, 'chop') else None,
           # Perzentile (brauchen Historien-Fenster)
           'atrp_pctl': ...,
           'bbwidth_pctl': ...,
           'obi_pctl_90': ...
       }
   ```

4. **Anti-Flap-Logik**
   ```python
   class RegimeTracker:
       def __init__(self, confirm_bars=3, cooldown_bars=5, min_segment_bars=10):
           self.confirm_bars = confirm_bars
           self.cooldown_bars = cooldown_bars
           self.min_segment_bars = min_segment_bars
           self.current_regime = RegimeID.R0
           self.pending_regime = None
           self.confirm_count = 0
           self.bars_since_change = 0

       def update(self, detected_regime: RegimeID) -> tuple[RegimeID, bool]:
           """
           Returns: (active_regime, regime_changed)
           """
           if detected_regime == self.current_regime:
               self.confirm_count = 0
               self.pending_regime = None
               self.bars_since_change += 1
               return self.current_regime, False

           # Cooldown aktiv?
           if self.bars_since_change < self.cooldown_bars:
               return self.current_regime, False

           # Min-Segment-Länge erreicht?
           if self.bars_since_change < self.min_segment_bars:
               return self.current_regime, False

           # Neues Regime pending?
           if detected_regime != self.pending_regime:
               self.pending_regime = detected_regime
               self.confirm_count = 1
               return self.current_regime, False

           # Confirm-Counter erhöhen
           self.confirm_count += 1
           if self.confirm_count >= self.confirm_bars:
               # Regime-Wechsel!
               old_regime = self.current_regime
               self.current_regime = detected_regime
               self.pending_regime = None
               self.confirm_count = 0
               self.bars_since_change = 0
               return self.current_regime, True

           return self.current_regime, False
   ```

5. **FeatureEngine erweitern** für neue Indikatoren
   ```python
   # In feature_engine.py
   def _build_indicator_configs(self):
       configs = [
           # Bestehende...

           # NEU: CHOP
           IndicatorConfig(
               indicator_type=IndicatorType.CHOP,
               params={'period': 14},
               cache_results=True
           ),

           # NEU: Ichimoku
           IndicatorConfig(
               indicator_type=IndicatorType.ICHIMOKU,
               params={'tenkan': 9, 'kijun': 26, 'senkou_b': 52},
               cache_results=True
           ),

           # ... weitere
       ]
   ```

6. **Unit-Tests**
   - Test Regime-Detektion für jedes R0-R5
   - Test Anti-Flap (confirm_bars funktioniert)
   - Test Segment-Features (range_pct, atrp korrekt)
   - Test Richtungserkennung (UP/DOWN/NONE)

**Deliverables:**
- Modified `src/core/tradingbot/regime_engine.py`
- Modified `src/core/tradingbot/models.py`
- Modified `src/core/tradingbot/feature_engine.py`
- `src/core/tradingbot/regime_tracker.py` (neu)
- `tests/unit/test_regime_engine_extended.py`

**Akzeptanzkriterien:**
- ✅ Alle 6 Regimes (R0-R5) werden korrekt detektiert
- ✅ Anti-Flap verhindert Regime-Flapping
- ✅ Segment-Features (atrp, bbwidth, range_pct) korrekt berechnet
- ✅ Backward Compatibility: `classify()` (alte API) funktioniert weiterhin

---

### Phase 3: Indikator-Katalog & Grid-Search (4-5 Tage)

**Ziel:** YAML-basierter Indikator-Katalog, Grid-Search für Parameter-Optimization

**Tasks:**
1. **Katalog-YAML erstellen** (`config/indicators/catalog.yaml`)
   ```yaml
   indicators:
     - id: adx
       type: panel
       family: trend_strength
       roles: [regime, entry, exit]
       best_regimes: [R1, R0, R2]
       params_default:
         length: 14
       grid:
         "5m":
           length: [7, 10, 14, 20]
         "1D":
           length: [10, 14, 20, 28]

     - id: rsi
       type: panel
       family: momentum
       roles: [entry, exit]
       best_regimes: [R1, R2]
       params_default:
         period: 14
       grid:
         "5m":
           period: [10, 12, 14, 16, 20]
         "1D":
           period: [10, 14, 20]

     # ... weitere ~30 Indikatoren
   ```

2. **Katalog-Loader** (`src/core/tradingbot/indicator_catalog.py`)
   ```python
   import yaml
   from pathlib import Path

   class IndicatorCatalog:
       def __init__(self, catalog_path: str | None = None):
           if catalog_path is None:
               catalog_path = Path(__file__).parent.parent.parent / "config/indicators/catalog.yaml"

           with open(catalog_path) as f:
               self.data = yaml.safe_load(f)

           self.indicators = {ind['id']: ind for ind in self.data['indicators']}

       def get_indicator(self, ind_id: str) -> dict:
           return self.indicators.get(ind_id)

       def get_by_role(self, role: str) -> list[dict]:
           return [ind for ind in self.indicators.values() if role in ind.get('roles', [])]

       def get_by_regime(self, regime: str) -> list[dict]:
           return [ind for ind in self.indicators.values() if regime in ind.get('best_regimes', [])]

       def get_param_grid(self, ind_id: str, timeframe: str) -> dict:
           ind = self.get_indicator(ind_id)
           if not ind:
               return {}
           return ind.get('grid', {}).get(timeframe, {})

       def generate_param_combinations(self, ind_id: str, timeframe: str) -> list[dict]:
           """Generate all parameter combinations for grid search."""
           grid = self.get_param_grid(ind_id, timeframe)
           if not grid:
               return [self.get_indicator(ind_id).get('params_default', {})]

           import itertools
           keys = list(grid.keys())
           values = [grid[k] for k in keys]
           combos = list(itertools.product(*values))
           return [dict(zip(keys, combo)) for combo in combos]
   ```

3. **Grid-Search Runner** (`src/core/tradingbot/indicator_optimizer.py`)
   ```python
   class IndicatorOptimizer:
       def __init__(self, catalog: IndicatorCatalog, backtest_engine: BacktestEngine):
           self.catalog = catalog
           self.backtest_engine = backtest_engine

       def optimize_indicator(
           self,
           ind_id: str,
           timeframe: str,
           symbol: str,
           start_date,
           end_date,
           regime_filter: str | None = None,
           track: Literal["entry", "exit", "regime"] = "entry"
       ) -> list[dict]:
           """
           Run grid-search for indicator across all parameter combinations.
           Returns list of results sorted by score.
           """
           results = []
           combos = self.catalog.generate_param_combinations(ind_id, timeframe)

           for params in combos:
               # Create single-indicator config
               config = self._create_single_indicator_config(
                   ind_id, params, timeframe, track, regime_filter
               )

               # Run backtest
               bt_results = self.backtest_engine.run(config, symbol, start_date, end_date)

               # Calculate metrics
               metrics = self._calculate_metrics(bt_results)

               # Calculate score
               score = self._calculate_score(metrics)

               results.append({
                   'indicator': ind_id,
                   'params': params,
                   'regime': regime_filter,
                   'track': track,
                   'metrics': metrics,
                   'score': score
               })

           return sorted(results, key=lambda x: x['score'], reverse=True)

       def _create_single_indicator_config(self, ind_id, params, timeframe, track, regime_filter):
           """
           Create JSON config for single-indicator test.
           Entry Track: Candidate entry + baseline exit
           Exit Track: Baseline entry + candidate exit
           """
           if track == "entry":
               # Entry from indicator, exit from baseline (e.g. Chandelier)
               entry_conditions = self._indicator_to_entry_conditions(ind_id, params)
               exit_conditions = self._baseline_exit_conditions()
           elif track == "exit":
               # Entry from baseline, exit from indicator
               entry_conditions = self._baseline_entry_conditions()
               exit_conditions = self._indicator_to_exit_conditions(ind_id, params)
           else:  # regime
               # Test regime quality
               ...

           return TradingBotConfig(
               indicators=[...],
               regimes=[...],
               strategies=[...],
               routing=[...]
           )
   ```

4. **Baseline-Strategien definieren**
   ```python
   def _baseline_exit_conditions(self) -> dict:
       """Chandelier Exit (ATR-based trailing stop)."""
       return {
           "type": "cel_expression",
           "expr": "close < chandelier_stop"
       }

   def _baseline_entry_conditions(self) -> dict:
       """Simple SMA Crossover."""
       return {
           "type": "cel_expression",
           "expr": "crossover(sma_fast, sma_slow)"
       }
   ```

5. **Unit-Tests**
   - Test Katalog-Loader (YAML parsen)
   - Test Grid-Generation (korrekte Kombinationen)
   - Test Optimization-Runner (Mock-Backtest)

**Deliverables:**
- `config/indicators/catalog.yaml`
- `src/core/tradingbot/indicator_catalog.py`
- `src/core/tradingbot/indicator_optimizer.py`
- `tests/unit/test_indicator_catalog.py`
- `tests/integration/test_indicator_optimizer.py`

**Akzeptanzkriterien:**
- ✅ Katalog mit mindestens 20 Indikatoren
- ✅ Grid-Search generiert korrekte Kombinationen
- ✅ Optimizer läuft durch und liefert Scores

---

### Phase 4: Scoring-Pipeline (0-100 System) (3-4 Tage)

**Ziel:** Percentile-basiertes Scoring für Indikatoren und Regime-Klassifizierer

**Tasks:**
1. **Metriken-Berechnung** (`src/core/tradingbot/metrics.py`)
   ```python
   from dataclasses import dataclass

   @dataclass
   class TradeMetrics:
       # Profitability
       profit_factor: float
       expectancy: float
       total_return: float

       # Risk-Adjusted
       sharpe: float
       sortino: float
       calmar: float

       # Drawdown
       max_dd: float
       avg_dd: float

       # Win Stats
       win_rate: float
       avg_win: float
       avg_loss: float

       # Trade Stats
       total_trades: int
       avg_trade_duration: float

   class MetricsCalculator:
       @staticmethod
       def calculate(trades: list[Trade], initial_capital: float) -> TradeMetrics:
           wins = [t for t in trades if t.pnl > 0]
           losses = [t for t in trades if t.pnl <= 0]

           gross_profit = sum(t.pnl for t in wins)
           gross_loss = abs(sum(t.pnl for t in losses))

           profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
           expectancy = (gross_profit - gross_loss) / len(trades) if trades else 0

           # Sharpe/Sortino (braucht equity curve)
           equity_curve = MetricsCalculator._build_equity_curve(trades, initial_capital)
           returns = np.diff(equity_curve) / equity_curve[:-1]
           sharpe = np.mean(returns) / np.std(returns) * np.sqrt(252) if len(returns) > 0 else 0

           downside_returns = returns[returns < 0]
           sortino = (np.mean(returns) / np.std(downside_returns) * np.sqrt(252)
                      if len(downside_returns) > 0 else 0)

           # Max Drawdown
           max_dd = MetricsCalculator._calculate_max_drawdown(equity_curve)

           return TradeMetrics(
               profit_factor=profit_factor,
               expectancy=expectancy,
               total_return=(equity_curve[-1] - initial_capital) / initial_capital,
               sharpe=sharpe,
               sortino=sortino,
               calmar=0,  # TODO
               max_dd=max_dd,
               avg_dd=0,  # TODO
               win_rate=len(wins) / len(trades) if trades else 0,
               avg_win=gross_profit / len(wins) if wins else 0,
               avg_loss=gross_loss / len(losses) if losses else 0,
               total_trades=len(trades),
               avg_trade_duration=0  # TODO
           )
   ```

2. **Percentile-Rank Scorer** (`src/core/tradingbot/scoring.py`)
   ```python
   class PercentileScorer:
       @staticmethod
       def percentile_rank(value: float, all_values: list[float], smaller_is_better=False) -> float:
           """
           Returns percentile rank (0-100).
           100 = best (highest percentile for "bigger is better" metrics).
           """
           if not all_values:
               return 50.0  # Neutral

           rank = sum(1 for v in all_values if v < value)
           percentile = 100 * rank / len(all_values)

           if smaller_is_better:
               return 100 - percentile
           return percentile

       @staticmethod
       def calculate_composite_score(
           metrics: TradeMetrics,
           all_metrics: list[TradeMetrics],
           weights: dict[str, float] | None = None
       ) -> float:
           """
           Calculate weighted composite score from multiple metrics.
           """
           if weights is None:
               weights = {
                   'profit_factor': 0.25,
                   'expectancy': 0.25,
                   'sortino': 0.20,
                   'max_dd': 0.20,  # Invert
                   'win_rate': 0.10
               }

           all_pf = [m.profit_factor for m in all_metrics]
           all_exp = [m.expectancy for m in all_metrics]
           all_sortino = [m.sortino for m in all_metrics]
           all_max_dd = [m.max_dd for m in all_metrics]
           all_wr = [m.win_rate for m in all_metrics]

           score = (
               weights['profit_factor'] * PercentileScorer.percentile_rank(metrics.profit_factor, all_pf) +
               weights['expectancy'] * PercentileScorer.percentile_rank(metrics.expectancy, all_exp) +
               weights['sortino'] * PercentileScorer.percentile_rank(metrics.sortino, all_sortino) +
               weights['max_dd'] * PercentileScorer.percentile_rank(metrics.max_dd, all_max_dd, smaller_is_better=True) +
               weights['win_rate'] * PercentileScorer.percentile_rank(metrics.win_rate, all_wr)
           )

           return score
   ```

3. **Regime-Quality Scorer** (für Regime-Klassifizierer)
   ```python
   from sklearn.metrics import balanced_accuracy_score, f1_score, matthews_corrcoef

   class RegimeQualityScorer:
       @staticmethod
       def calculate_quality_score(
           detected_regimes: list[str],
           reference_regimes: list[str],
           all_results: list[tuple[list[str], list[str]]]  # Für Percentile
       ) -> float:
           """
           Calculate regime quality score (0-100).
           Metrics: Balanced Accuracy, Macro-F1, MCC, Regime-Churn
           """
           # Balanced Accuracy
           bal_acc = balanced_accuracy_score(reference_regimes, detected_regimes)

           # Macro-F1
           macro_f1 = f1_score(reference_regimes, detected_regimes, average='macro')

           # Matthews Correlation Coefficient
           mcc = matthews_corrcoef(reference_regimes, detected_regimes)

           # Regime-Churn-Penalty (switches per bar)
           churn = sum(1 for i in range(1, len(detected_regimes)) if detected_regimes[i] != detected_regimes[i-1])
           churn_rate = churn / len(detected_regimes)

           # Composite (weighted)
           base_score = (
               0.35 * bal_acc +
               0.35 * macro_f1 +
               0.20 * (mcc + 1) / 2 +  # Normalize MCC (-1..1) to (0..1)
               0.10 * (1 - churn_rate)  # Less churn is better
           ) * 100

           # Percentile-Rank über alle Klassifizierer
           all_base_scores = [
               RegimeQualityScorer._calc_base_score(det, ref)
               for det, ref in all_results
           ]

           return PercentileScorer.percentile_rank(base_score, all_base_scores)
   ```

4. **Integration in Optimizer**
   ```python
   # In indicator_optimizer.py
   def optimize_indicator(self, ...):
       results = []

       for params in combos:
           bt_results = self.backtest_engine.run(...)

           # Calculate metrics
           metrics = MetricsCalculator.calculate(bt_results['trades'], initial_capital)

           results.append({
               'indicator': ind_id,
               'params': params,
               'metrics': metrics
           })

       # Calculate scores after collecting all results
       all_metrics = [r['metrics'] for r in results]
       for r in results:
           r['score'] = PercentileScorer.calculate_composite_score(
               r['metrics'], all_metrics
           )

       return sorted(results, key=lambda x: x['score'], reverse=True)
   ```

5. **Unit-Tests**
   - Test Metriken-Berechnung (Profit Factor, Sharpe, etc.)
   - Test Percentile-Rank (edge cases: leer, single value)
   - Test Composite-Score (verschiedene Gewichtungen)
   - Test Regime-Quality-Score

**Deliverables:**
- `src/core/tradingbot/metrics.py`
- `src/core/tradingbot/scoring.py`
- Modified `src/core/tradingbot/indicator_optimizer.py`
- `tests/unit/test_metrics.py`
- `tests/unit/test_scoring.py`

**Akzeptanzkriterien:**
- ✅ Metriken korrekt berechnet (validiert gegen Beispieldaten)
- ✅ Scores liegen immer zwischen 0-100
- ✅ Percentile-Rank korrekt (Edge-Cases)

---

### Phase 5: Marktanalyse.json Schema & Writer (3-4 Tage)

**Ziel:** JSON Schema + Writer für Marktanalyse-Ergebnisse

**Tasks:**
1. **JSON Schema definieren** (`config/schemas/marktanalyse_schema.json`)
   ```json
   {
     "$schema": "https://json-schema.org/draft/2020-12/schema",
     "$id": "https://orderpilot-ai.local/marktanalyse.schema.json",
     "title": "Marktanalyse",
     "type": "object",
     "required": ["meta", "regime_engine", "segments", "indicator_runs"],
     "properties": {
       "meta": {
         "type": "object",
         "required": ["symbol", "exchange", "timeframes", "start_date", "end_date"],
         "properties": {
           "symbol": {"type": "string"},
           "exchange": {"type": "string"},
           "timeframes": {
             "type": "array",
             "items": {"type": "string"}
           },
           "start_date": {"type": "string", "format": "date-time"},
           "end_date": {"type": "string", "format": "date-time"},
           "generator": {"type": "string"},
           "version": {"type": "string"}
         }
       },
       "regime_engine": {
         "type": "object",
         "properties": {
           "classifier": {"type": "string"},
           "rules": {"type": "array"},
           "anti_flap": {
             "type": "object",
             "properties": {
               "confirm_bars": {"type": "integer"},
               "cooldown_bars": {"type": "integer"},
               "min_segment_bars": {"type": "integer"}
             }
           }
         }
       },
       "segments": {
         "type": "array",
         "items": {
           "type": "object",
           "required": ["id", "start_idx", "end_idx", "regime", "direction", "features"],
           "properties": {
             "id": {"type": "string"},
             "start_idx": {"type": "integer"},
             "end_idx": {"type": "integer"},
             "regime": {"type": "string", "enum": ["R0", "R1", "R2", "R3", "R4", "R5"]},
             "direction": {"type": "string", "enum": ["UP", "DOWN", "NONE"]},
             "features": {
               "type": "object",
               "properties": {
                 "range_pct": {"type": "number"},
                 "atrp": {"type": "number"},
                 "bbwidth": {"type": "number"},
                 "squeeze_on": {"type": "boolean"},
                 "obi": {"type": ["number", "null"]}
               }
             }
           }
         }
       },
       "indicator_runs": {
         "type": "array",
         "items": {
           "type": "object",
           "required": ["id", "indicator", "params", "timeframe", "regime", "track", "metrics", "score"],
           "properties": {
             "id": {"type": "string"},
             "indicator": {"type": "string"},
             "params": {"type": "object"},
             "timeframe": {"type": "string"},
             "regime": {"type": "string"},
             "track": {"type": "string", "enum": ["entry", "exit", "regime"]},
             "metrics": {
               "type": "object",
               "properties": {
                 "profit_factor": {"type": "number"},
                 "expectancy": {"type": "number"},
                 "sortino": {"type": "number"},
                 "max_dd": {"type": "number"},
                 "win_rate": {"type": "number"}
               }
             },
             "score": {"type": "number", "minimum": 0, "maximum": 100}
           }
         }
       },
       "regime_set": {
         "type": "object",
         "patternProperties": {
           "^R[0-5]$": {
             "type": "object",
             "properties": {
               "entries": {
                 "type": "array",
                 "items": {
                   "type": "object",
                   "properties": {
                     "indicator": {"type": "string"},
                     "params": {"type": "object"},
                     "weight": {"type": "number"},
                     "score": {"type": "number"}
                   }
                 }
               },
               "exits": {"type": "array"}
             }
           }
         }
       }
     }
   }
   ```

2. **Marktanalyse-Writer** (`src/core/tradingbot/marktanalyse_writer.py`)
   ```python
   import json
   from jsonschema import validate
   from pathlib import Path

   class MarktanalyseWriter:
       def __init__(self, schema_path: str | None = None):
           if schema_path is None:
               schema_path = Path(__file__).parent.parent.parent / "config/schemas/marktanalyse_schema.json"

           with open(schema_path) as f:
               self.schema = json.load(f)

       def write(
           self,
           output_path: str,
           meta: dict,
           regime_engine_config: dict,
           segments: list[dict],
           indicator_runs: list[dict],
           regime_set: dict
       ):
           """
           Write Marktanalyse.json with validation.
           """
           data = {
               "meta": meta,
               "regime_engine": regime_engine_config,
               "segments": segments,
               "indicator_runs": indicator_runs,
               "regime_set": regime_set
           }

           # Validate
           validate(instance=data, schema=self.schema)

           # Write
           with open(output_path, 'w') as f:
               json.dump(data, f, indent=2)
   ```

3. **Integration in Entry Analyzer**
   ```python
   # In entry_analyzer_popup.py (nach Backtest-Run)
   def _on_backtest_finished(self, results):
       # ... existing results display ...

       # Create Marktanalyse.json
       writer = MarktanalyseWriter()

       meta = {
           "symbol": self.symbol,
           "exchange": "bitunix",
           "timeframes": ["5m"],
           "start_date": self.start_date.isoformat(),
           "end_date": self.end_date.isoformat(),
           "generator": "OrderPilot-AI Entry Analyzer v1.0",
           "version": "1.0.0"
       }

       segments = self._convert_regime_history_to_segments(results['regime_history'])
       indicator_runs = results.get('indicator_runs', [])
       regime_set = results.get('regime_set', {})

       output_path = Path(self.config_file).parent / f"marktanalyse_{self.symbol}_{self.start_date}.json"
       writer.write(output_path, meta, {}, segments, indicator_runs, regime_set)

       QMessageBox.information(self, "Analyse gespeichert", f"Marktanalyse gespeichert: {output_path}")
   ```

4. **Unit-Tests**
   - Test Schema-Validation (gültige/ungültige Strukturen)
   - Test Writer (korrekte JSON-Generierung)

**Deliverables:**
- `config/schemas/marktanalyse_schema.json`
- `src/core/tradingbot/marktanalyse_writer.py`
- Modified `src/ui/dialogs/entry_analyzer_popup.py`
- `tests/unit/test_marktanalyse_writer.py`

**Akzeptanzkriterien:**
- ✅ Schema validiert korrekte Strukturen
- ✅ Writer wirft bei ungültigen Daten Exception
- ✅ JSON kann von Entry Analyzer exportiert werden

---

### Phase 6: RulePack-System Integration (3-4 Tage)

**Ziel:** RulePack.json für Trading-Regeln (no_trade, entry, exit, update_stop, risk)

**Tasks:**
1. **RulePack JSON Schema** (`config/schemas/rulepack_schema.json`)
   ```json
   {
     "$schema": "https://json-schema.org/draft/2020-12/schema",
     "$id": "https://orderpilot-ai.local/rulepack.schema.json",
     "title": "RulePack",
     "type": "object",
     "required": ["rules_version", "engine", "packs"],
     "properties": {
       "rules_version": {"type": "string"},
       "engine": {"type": "string", "enum": ["CEL"]},
       "packs": {
         "type": "array",
         "items": {
           "type": "object",
           "required": ["pack_id", "enabled", "rules"],
           "properties": {
             "pack_id": {"type": "string"},
             "enabled": {"type": "boolean"},
             "rules": {
               "type": "array",
               "items": {
                 "type": "object",
                 "required": ["id", "severity", "expr"],
                 "properties": {
                   "id": {"type": "string"},
                   "severity": {"type": "string", "enum": ["block", "exit", "update_stop"]},
                   "expr": {"type": "string"},
                   "result_type": {"type": "string"}
                 }
               }
             }
           }
         }
       }
     }
   }
   ```

2. **RulePack-Loader** (`src/core/tradingbot/rulepack_loader.py`)
   ```python
   from jsonschema import validate

   class RulePackLoader:
       def __init__(self, cel_engine: CELEngine):
           self.cel_engine = cel_engine

       def load(self, rulepack_path: str) -> dict:
           with open(rulepack_path) as f:
               data = json.load(f)

           # Validate
           validate(instance=data, schema=self._load_schema())

           # Compile CEL expressions
           for pack in data['packs']:
               for rule in pack['rules']:
                   self.cel_engine.compile(rule['expr'])  # Pre-compile

           return data
   ```

3. **Rule-Executor** (`src/core/tradingbot/rule_executor.py`)
   ```python
   class RuleExecutor:
       def __init__(self, rulepack: dict, cel_engine: CELEngine):
           self.rulepack = rulepack
           self.cel_engine = cel_engine

       def evaluate_pack(self, pack_id: str, context: dict) -> list[dict]:
           """
           Evaluate all rules in a pack.
           Returns list of triggered rules.
           """
           pack = next((p for p in self.rulepack['packs'] if p['pack_id'] == pack_id), None)
           if not pack or not pack['enabled']:
               return []

           triggered = []
           for rule in pack['rules']:
               try:
                   result = self.cel_engine.evaluate(rule['expr'], context)
                   if result:
                       triggered.append(rule)
               except Exception as e:
                   logger.error(f"Rule {rule['id']} evaluation failed: {e}")

           return triggered

       def should_block_trade(self, context: dict) -> tuple[bool, str | None]:
           """
           Check no_trade and entry rules.
           Returns (should_block, reason).
           """
           # no_trade pack (highest priority)
           no_trade_triggers = self.evaluate_pack('no_trade', context)
           if no_trade_triggers:
               return True, f"No-Trade Rule: {no_trade_triggers[0]['id']}"

           # entry pack (gates)
           entry_triggers = self.evaluate_pack('entry', context)
           if entry_triggers:
               return True, f"Entry Gate: {entry_triggers[0]['id']}"

           return False, None

       def should_exit_trade(self, context: dict) -> tuple[bool, str | None]:
           """
           Check exit rules.
           """
           exit_triggers = self.evaluate_pack('exit', context)
           if exit_triggers:
               return True, exit_triggers[0]['id']

           return False, None

       def calculate_new_stop(self, context: dict) -> float | None:
           """
           Check update_stop rules, return new stop (monotonic).
           """
           stop_triggers = self.evaluate_pack('update_stop', context)
           if not stop_triggers:
               return None

           # Rules should return stop price (or null)
           new_stops = []
           for rule in stop_triggers:
               try:
                   result = self.cel_engine.evaluate(rule['expr'], context)
                   if result is not None:
                       new_stops.append(result)
               except Exception as e:
                   logger.error(f"Stop calculation failed for {rule['id']}: {e}")

           if not new_stops:
               return None

           # Monotonic: Long = max, Short = min
           side = context['trade']['side']
           if side == 'long':
               return max(new_stops)
           else:
               return min(new_stops)
   ```

4. **Default RulePack erstellen** (`config/rulepacks/default.json`)
   ```json
   {
     "rules_version": "1.0.0",
     "engine": "CEL",
     "packs": [
       {
         "pack_id": "no_trade",
         "enabled": true,
         "rules": [
           {
             "id": "NT_LOW_VOL_AND_LOW_VOLATILITY",
             "severity": "block",
             "expr": "volume < pctl(volume, cfg.min_volume_pctl, cfg.min_volume_window) && atrp < cfg.min_atrp_pct"
           },
           {
             "id": "NT_TOO_WILD",
             "severity": "block",
             "expr": "atrp > cfg.max_atrp_pct"
           }
         ]
       },
       {
         "pack_id": "exit",
         "enabled": true,
         "rules": [
           {
             "id": "EX_STOP_HIT",
             "severity": "exit",
             "expr": "trade.side == \"long\" ? trade.current_price <= trade.stop_price : trade.current_price >= trade.stop_price"
           }
         ]
       },
       {
         "pack_id": "update_stop",
         "enabled": true,
         "rules": [
           {
             "id": "US_BREAK_EVEN_LOCK",
             "severity": "update_stop",
             "result_type": "number_or_null",
             "expr": "trade.pnl_pct >= trade.tr_lock_pct ? (trade.side == \"long\" ? max(trade.stop_price, trade.entry_price) : min(trade.stop_price, trade.entry_price)) : null"
           }
         ]
       }
     ]
   }
   ```

5. **Integration in BotController** (live trading)
   ```python
   # In bot_controller.py
   class BotController:
       def __init__(self, ...):
           self.rule_executor = RuleExecutor(
               rulepack=RulePackLoader(self.cel_engine).load("config/rulepacks/default.json"),
               cel_engine=self.cel_engine
           )

       def _on_new_bar(self, bar_data):
           features = self.feature_engine.calculate_features(...)

           # Build context for rules
           context = self._build_rule_context(features)

           # Check no-trade / entry gates
           should_block, reason = self.rule_executor.should_block_trade(context)
           if should_block:
               logger.info(f"Trade blocked: {reason}")
               return

           # ... normal entry logic ...

           # If in trade, check exit + stop updates
           if self.active_trade:
               should_exit, exit_reason = self.rule_executor.should_exit_trade(context)
               if should_exit:
                   self._close_trade(exit_reason)
                   return

               new_stop = self.rule_executor.calculate_new_stop(context)
               if new_stop:
                   self._update_stop_loss(new_stop)
   ```

6. **Unit-Tests**
   - Test RulePack-Loader (gültige/ungültige Packs)
   - Test RuleExecutor (verschiedene Packs)
   - Test Monotonic Stop-Logic (Long/Short)

**Deliverables:**
- `config/schemas/rulepack_schema.json`
- `config/rulepacks/default.json`
- `src/core/tradingbot/rulepack_loader.py`
- `src/core/tradingbot/rule_executor.py`
- Modified `src/core/tradingbot/bot_controller.py`
- `tests/unit/test_rulepack.py`

**Akzeptanzkriterien:**
- ✅ RulePack lädt und validiert korrekt
- ✅ Rules evaluieren mit CEL-Context
- ✅ Monotonic Stop-Logic funktioniert

---

### Phase 7: UI-Integration & Visualisierung (5-6 Tage)

**Ziel:** Entry Analyzer mit Regime-Visualisierung, Indikator-Optimization UI

**Tasks:**
1. **Backtest-Button Verdrahtung** (bereits existiert, nur konnektieren)
   ```python
   # In entry_analyzer_popup.py
   def __init__(self, parent=None):
       # ... existing UI setup ...

       # Connect Run Backtest Button
       self.run_backtest_btn.clicked.connect(self._on_run_backtest_clicked)

   def _on_run_backtest_clicked(self):
       # Validate inputs
       config_path = self.json_file_input.text()
       symbol = self.symbol_combo.currentText()
       start_date = self.start_date_edit.date().toPyDate()
       end_date = self.end_date_edit.date().toPyDate()
       capital = self.capital_spin.value()

       # Load JSON Config
       config = ConfigLoader().load_config(config_path)

       # Run Backtest in Background Thread
       self.backtest_thread = BacktestThread(config, symbol, start_date, end_date, capital)
       self.backtest_thread.finished.connect(self._on_backtest_finished)
       self.backtest_thread.progress.connect(self._update_progress_bar)
       self.backtest_thread.start()
   ```

2. **BacktestThread erstellen**
   ```python
   # src/ui/threads/backtest_thread.py
   from PyQt6.QtCore import QThread, pyqtSignal

   class BacktestThread(QThread):
       finished = pyqtSignal(dict)
       progress = pyqtSignal(int, str)

       def __init__(self, config, symbol, start_date, end_date, capital):
           super().__init__()
           self.config = config
           self.symbol = symbol
           self.start_date = start_date
           self.end_date = end_date
           self.capital = capital

       def run(self):
           engine = BacktestEngine()
           results = engine.run(
               self.config,
               self.symbol,
               self.start_date,
               self.end_date,
               self.capital
           )
           self.finished.emit(results)
   ```

3. **Regime-Visualisierung im Chart**
   ```python
   # src/ui/widgets/chart_window_mixins/regime_visualization_mixin.py
   import pyqtgraph as pg

   class RegimeVisualizationMixin:
       def __init__(self):
           self.regime_lines = []
           self.regime_colors = {
               'R0': '#9e9e9e',    # Gray
               'R1': '#26a69a',    # Green
               'R2': '#ffa726',    # Orange
               'R3': '#ab47bc',    # Purple
               'R4': '#ef5350',    # Red
               'R5': '#42a5f5'     # Blue
           }

       def draw_regime_boundaries(self, regime_history: list[dict]):
           self.clear_regime_lines()

           for change in regime_history:
               timestamp = change['timestamp']
               regime_ids = change['regime_ids']

               # Convert timestamp to x-coordinate
               x_pos = self._timestamp_to_x(timestamp)

               # Get color (use first regime if multiple)
               regime_id = regime_ids[0] if regime_ids else 'R0'
               color = self.regime_colors.get(regime_id, '#9e9e9e')

               # Draw vertical line
               line = pg.InfiniteLine(
                   pos=x_pos,
                   angle=90,
                   pen=pg.mkPen(color=color, width=2, style=Qt.PenStyle.DashLine),
                   label=regime_id,
                   labelOpts={'position': 0.95, 'color': color}
               )

               self.chart_widget.addItem(line)
               self.regime_lines.append(line)

       def clear_regime_lines(self):
           for line in self.regime_lines:
               self.chart_widget.removeItem(line)
           self.regime_lines.clear()
   ```

4. **Indikator-Optimization Tab**
   ```python
   # In entry_analyzer_popup.py
   def _setup_indicator_optimization_tab(self, tab):
       layout = QVBoxLayout(tab)

       # Indicator Selection Group
       indicator_group = QGroupBox("Indikator-Auswahl")
       indicator_layout = QVBoxLayout(indicator_group)

       self.indicator_checkboxes = {}
       catalog = IndicatorCatalog()
       for ind in catalog.indicators.values():
           cb = QCheckBox(f"{ind['id']} ({', '.join(ind.get('roles', []))})")
           cb.setChecked(True)
           self.indicator_checkboxes[ind['id']] = cb
           indicator_layout.addWidget(cb)

       layout.addWidget(indicator_group)

       # Regime Filter
       regime_group = QGroupBox("Regime-Filter")
       regime_layout = QHBoxLayout(regime_group)

       self.regime_filter_combo = QComboBox()
       self.regime_filter_combo.addItems(["Alle", "R0", "R1", "R2", "R3", "R4", "R5"])
       regime_layout.addWidget(QLabel("Regime:"))
       regime_layout.addWidget(self.regime_filter_combo)

       layout.addWidget(regime_group)

       # Optimize Button
       self.optimize_btn = QPushButton("🚀 Optimierung starten")
       self.optimize_btn.clicked.connect(self._on_optimize_clicked)
       layout.addWidget(self.optimize_btn)

       # Results Table
       self.optimization_results_table = QTableWidget()
       self.optimization_results_table.setColumnCount(7)
       self.optimization_results_table.setHorizontalHeaderLabels([
           "Indikator", "Parameter", "Regime", "Track", "Score", "Win Rate", "Profit Factor"
       ])
       layout.addWidget(self.optimization_results_table)

   def _on_optimize_clicked(self):
       # Get selected indicators
       selected = [ind_id for ind_id, cb in self.indicator_checkboxes.items() if cb.isChecked()]

       # Get regime filter
       regime = self.regime_filter_combo.currentText()
       regime_filter = None if regime == "Alle" else regime

       # Run optimization in background
       self.optimization_thread = IndicatorOptimizationThread(
           selected, regime_filter, self.symbol, self.start_date, self.end_date
       )
       self.optimization_thread.finished.connect(self._on_optimization_finished)
       self.optimization_thread.start()
   ```

5. **IndicatorOptimizationThread**
   ```python
   # src/ui/threads/indicator_optimization_thread.py
   class IndicatorOptimizationThread(QThread):
       finished = pyqtSignal(list)
       progress = pyqtSignal(int, str)

       def run(self):
           optimizer = IndicatorOptimizer(IndicatorCatalog(), BacktestEngine())

           results = []
           for ind_id in self.selected_indicators:
               ind_results = optimizer.optimize_indicator(
                   ind_id,
                   self.timeframe,
                   self.symbol,
                   self.start_date,
                   self.end_date,
                   regime_filter=self.regime_filter
               )
               results.extend(ind_results)

           self.finished.emit(results)
   ```

6. **Unit-Tests + Integration-Tests**
   - Test Regime-Visualisierung (Linien korrekt gezeichnet)
   - Test Optimization-Thread (Mock-Backtest)
   - Test UI-Workflow (Button-Clicks, Threads)

**Deliverables:**
- Modified `src/ui/dialogs/entry_analyzer_popup.py`
- `src/ui/threads/backtest_thread.py`
- `src/ui/threads/indicator_optimization_thread.py`
- `src/ui/widgets/chart_window_mixins/regime_visualization_mixin.py`
- `tests/integration/test_entry_analyzer_ui.py`

**Akzeptanzkriterien:**
- ✅ Backtest-Button läuft durch
- ✅ Regime-Linien im Chart sichtbar
- ✅ Optimization-Tab funktioniert
- ✅ Ergebnisse in Marktanalyse.json exportierbar

---

## 4. Risiken & Mitigation

### Risiko 1: CEL-Performance bei komplexen Expressions

**Problem:** CEL-Evaluation könnte bei Echtzeit-Bar-Updates langsam sein (> 10ms)

**Mitigation:**
1. **Compilation-Caching:** Alle Expressions einmal kompilieren, dann nur evaluieren
2. **Profiling:** Performance-Tests mit realistischen Workloads (1000+ Bars/s)
3. **Alternative:** Falls celpy zu langsam, Wechsel zu `python-cel` (Rust-backed, Microsecond-Evaluation)

**Test:**
```python
# Performance-Benchmark
import time

cel_engine = CELEngine()
expr = "volume > pctl(volume, 20, 288) && atrp < 0.2 && rsi_14 > 50"
context = {...}

# Warmup
cel_engine.evaluate(expr, context)

# Benchmark
start = time.perf_counter()
for _ in range(10000):
    cel_engine.evaluate(expr, context)
end = time.perf_counter()

avg_time = (end - start) / 10000
assert avg_time < 0.001, f"CEL too slow: {avg_time*1000:.2f}ms"
```

---

### Risiko 2: Orderflow-Daten (OBI) nicht verfügbar

**Problem:** Bitunix API liefert möglicherweise keine Orderbuch-Daten für R5-Regime

**Mitigation:**
1. **Graceful Degradation:** Wenn `obi` = null, R5 wird nie detektiert (failsafe)
2. **Alternative Datenquelle:** Binance oder andere Exchanges mit Orderbook-API
3. **Fallback:** R5 optional, System funktioniert auch mit R0-R4

**Implementation:**
```python
# In composite_detect
if features.get('obi') is not None and abs(features['obi']) > ...:
    return RegimeID.R5
# Falls obi=null, wird diese Bedingung nie True
```

---

### Risiko 3: Grid-Search Laufzeit (zu langsam)

**Problem:** Optimization über 30 Indikatoren x 5-10 Parameter-Kombinationen = 150+ Backtests (Stunden)

**Mitigation:**
1. **Parallel-Processing:** `multiprocessing.Pool` für Backtest-Runs
2. **Caching:** Indikator-Berechnungen cachen (pandas_ta hat bereits Caching)
3. **Sampling:** Statt Grid-Search, Random-Search mit Top-K (schneller)
4. **Incremental:** Nur geänderte Indikatoren neu testen

**Implementation:**
```python
from multiprocessing import Pool

def optimize_indicator_parallel(self, ind_ids, ...):
    with Pool(processes=4) as pool:
        results = pool.starmap(
            self._optimize_single,
            [(ind_id, ...) for ind_id in ind_ids]
        )
    return results
```

---

### Risiko 4: Schema-Breaking Changes

**Problem:** Änderungen an Marktanalyse.json oder RulePack.json brechen alte Dateien

**Mitigation:**
1. **Versionierung:** `schema_version` in JSON, Backward-Compatibility-Layer
2. **Migration-Scripts:** Tools für Schema-Upgrades
3. **Deprecation-Warnings:** Alte Felder als deprecated markieren, später entfernen

**Implementation:**
```python
# In MarktanalyseWriter
def write(self, ...):
    if meta.get('version', '1.0.0') < '1.1.0':
        # Migrate old format
        ...
```

---

### Risiko 5: UI-Thread-Blocking

**Problem:** Lange-laufende Backtests blockieren UI (Freeze)

**Mitigation:**
1. **QThread:** Alle Backtests/Optimizations in separaten Threads
2. **Progress-Signals:** Emit Progress-Updates für UI-Feedback
3. **Cancel-Button:** Nutzer kann Runs abbrechen

**Implementation:**
```python
# In BacktestThread
def run(self):
    for i, bar in enumerate(data):
        # ... processing ...

        if i % 100 == 0:
            self.progress.emit(int(i / len(data) * 100), f"Bar {i}/{len(data)}")

        if self.isInterruptionRequested():
            return  # Cancel
```

---

## 5. Zeitschätzung & Priorisierung

### Gesamt-Aufwand: **25-32 Arbeitstage** (5-6 Wochen bei Vollzeit)

| Phase | Aufwand | Priorität | Dependencies |
|-------|---------|-----------|--------------|
| **Phase 0: Setup** | 1-2 Tage | P0 (Kritisch) | Keine |
| **Phase 1: CEL** | 3-4 Tage | P1 (Hoch) | Phase 0 |
| **Phase 2: Regime R0-R5** | 5-6 Tage | P1 (Hoch) | Phase 0 |
| **Phase 3: Katalog & Grid** | 4-5 Tage | P2 (Mittel) | Phase 2 |
| **Phase 4: Scoring** | 3-4 Tage | P2 (Mittel) | Phase 3 |
| **Phase 5: Marktanalyse.json** | 3-4 Tage | P2 (Mittel) | Phase 4 |
| **Phase 6: RulePack** | 3-4 Tage | P3 (Niedrig) | Phase 1 |
| **Phase 7: UI** | 5-6 Tage | P1 (Hoch) | Phase 2, 3, 5 |

**Empfohlene Reihenfolge:**
1. **Phase 0** → **Phase 2** (Regime-Engine zuerst, da Basis für alles)
2. **Phase 1** (CEL parallel zu Phase 2 möglich)
3. **Phase 3** → **Phase 4** → **Phase 5** (Sequentiell, bauen aufeinander auf)
4. **Phase 7** (UI am Ende, wenn Backend stabil)
5. **Phase 6** (RulePack optional, kann später kommen)

---

## 6. Nächste Schritte

### Sofort (nächste 24h):
1. **User-Feedback einholen:**
   - Priorisierung bestätigen (P1 zuerst?)
   - Orderflow (R5) wirklich benötigt? (Wenn nicht, spart Zeit)
   - UI-Design für Optimization-Tab besprechen

2. **Environment-Setup:**
   ```bash
   pip install cel-python pyyaml jsonschema
   pytest --version  # Sicherstellen dass Tests laufen
   ```

### Woche 1 (Tag 1-5):
- **Phase 0: Setup** (Tag 1)
- **Phase 2: Regime-Engine R0-R5** (Tag 2-5)
  - Start mit Regime-Detektion-Tests
  - Anti-Flap-Logik implementieren
  - Segment-Features berechnen

### Woche 2 (Tag 6-10):
- **Phase 1: CEL-Integration** (Tag 6-9)
  - CEL-Engine + Custom Functions
  - ConditionEvaluator erweitern
  - Tests für CEL-Expressions
- **Phase 7: UI-Basics** (Tag 10)
  - Backtest-Button verdrahten
  - Regime-Visualisierung Proof-of-Concept

### Woche 3 (Tag 11-15):
- **Phase 3: Indikator-Katalog** (Tag 11-13)
  - YAML-Katalog mit 20+ Indikatoren
  - Grid-Search-Runner
- **Phase 4: Scoring** (Tag 14-15)
  - Percentile-Scorer
  - Metriken-Berechnung

### Woche 4 (Tag 16-20):
- **Phase 5: Marktanalyse.json** (Tag 16-18)
  - Schema + Writer
  - Integration in Entry Analyzer
- **Phase 7: UI-Completion** (Tag 19-20)
  - Optimization-Tab
  - Ergebnis-Export

### Optional (Woche 5+):
- **Phase 6: RulePack-System** (Tag 21-24)
  - Nur wenn Live-Trading-Regeln benötigt
  - Sonst: Backlog für später

---

## 7. Erfolgskriterien

Am Ende der Implementation sollte Folgendes funktionieren:

### ✅ Backtest-Workflow
1. **Entry Analyzer öffnen** → Backtest Setup Tab
2. **JSON-Config auswählen** (oder neu erstellen)
3. **"Run Backtest" klicken**
4. **Regime-Grenzen im Chart** sichtbar (farbcodiert R0-R5)
5. **Backtest Results Tab** zeigt Performance-Metriken

### ✅ Indikator-Optimization
1. **Optimization Tab öffnen**
2. **Indikatoren auswählen** (z.B. RSI, MACD, ADX)
3. **Regime-Filter setzen** (z.B. nur R1 Trend)
4. **"Optimize" klicken**
5. **Ergebnisse sortiert nach Score (0-100)**
6. **Top-3 Indikatoren pro Regime anzeigen**

### ✅ Marktanalyse-Export
1. **Nach Backtest/Optimization**
2. **"Export Marktanalyse" Button**
3. **Marktanalyse.json gespeichert** mit:
   - Segmenten (Regime-Grenzen + Features)
   - Indicator-Runs (Scores pro Parameter)
   - Regime-Set (Top-N Indikatoren + Gewichte)

### ✅ Live-Trading-Integration (Optional Phase 6)
1. **BotController lädt RulePack.json**
2. **No-Trade-Rules blocken schlechte Setups**
3. **Exit-Rules triggern Ausstiege**
4. **Update-Stop-Rules passen SL an** (Trailing, Break-Even)

---

## 8. Anhang: Code-Beispiele

### A1: Vollständiges CEL-Context-Beispiel

```python
# RuleContext für CEL-Evaluation
context = {
    # Markt/Regime
    "tf": "5m",
    "regime": "R1",
    "direction": "UP",

    # OHLCV
    "open": 95250.0,
    "high": 95410.0,
    "low": 95120.0,
    "close": 95159.70,
    "volume": 1234.56,

    # Indikatoren
    "atrp": 0.60,
    "bbwidth": 0.024,
    "range_pct": 1.85,
    "squeeze_on": False,
    "spread_bps": 2.1,
    "depth_bid": 125.0,
    "depth_ask": 132.0,
    "obi": None,

    # Trade-State (wenn Trade offen)
    "trade": {
        "id": "E:50",
        "strategy": "trend_following_conservative",
        "side": "long",
        "entry_price": 95336.14,
        "current_price": 95159.70,
        "stop_price": 95171.63,
        "sl_pct": 0.17,
        "tr_pct": 1.00,
        "tra_pct": 0.50,
        "tr_lock_pct": 0.50,
        "pnl_pct": -0.18,
        "pnl_usdt": -0.18,
        "fees_pct": 0.080,
        "fees_usdt": 2.40,
        "invest_usdt": 100.00,
        "leverage": 20,
        "age_sec": 87,
        "bars_in_trade": 4,
        "is_open": True
    },

    # Config
    "cfg": {
        "min_volume_pctl": 20,
        "min_volume_window": 288,
        "min_atrp_pct": 0.20,
        "max_atrp_pct": 2.50,
        "max_spread_bps": 8.0,
        "min_depth": 60.0,
        "max_leverage": 50,
        "max_fees_pct": 0.15,
        "min_obi": 0.60,
        "min_range_pct": 0.60,
        "no_trade_regimes": ["R0"]
    }
}
```

### A2: Beispiel-Regime-Set-Output

```json
{
  "regime_set": {
    "R1": {
      "entries": [
        {
          "indicator": "supertrend",
          "params": {"atr_len": 10, "mult": 2.5},
          "weight": 0.35,
          "score": 82.4,
          "role": "entry"
        },
        {
          "indicator": "macd",
          "params": {"fast": 12, "slow": 26, "signal": 9},
          "weight": 0.40,
          "score": 78.1,
          "role": "entry"
        },
        {
          "indicator": "rsi",
          "params": {"period": 14},
          "weight": 0.25,
          "score": 72.3,
          "role": "entry"
        }
      ],
      "exits": [
        {
          "indicator": "chandelier",
          "params": {"atr_len": 14, "mult": 3.0},
          "weight": 0.60,
          "score": 85.2,
          "role": "exit"
        },
        {
          "indicator": "atr_trail",
          "params": {"atr_len": 14, "mult": 2.0},
          "weight": 0.40,
          "score": 79.8,
          "role": "exit"
        }
      ]
    },
    "R2": {
      "entries": [
        {
          "indicator": "rsi",
          "params": {"period": 14},
          "weight": 0.45,
          "score": 76.5,
          "role": "entry"
        },
        {
          "indicator": "bb",
          "params": {"period": 20, "std": 2.0},
          "weight": 0.35,
          "score": 71.2,
          "role": "entry"
        },
        {
          "indicator": "stoch",
          "params": {"k": 14, "d": 3},
          "weight": 0.20,
          "score": 68.9,
          "role": "entry"
        }
      ],
      "exits": [...]
    }
  }
}
```

---

## 9. Zusammenfassung

Dieser Umsetzungsplan integriert **CEL-basierte Rule-Engine** und **erweiterte Marktanalyse** in OrderPilot-AI durch:

1. **CEL-Integration** als flexibles Backend für Trading-Regeln
2. **Regime-Engine Erweiterung** von 3 auf 6 Regime (R0-R5)
3. **YAML-basierter Indikator-Katalog** für strukturierte Metadaten
4. **Grid-Search & Scoring-Pipeline** für 0-100 Bewertungen
5. **Marktanalyse.json** als portable Persistenz
6. **RulePack-System** für no_trade, entry, exit, update_stop, risk
7. **UI-Integration** mit Regime-Visualisierung und Optimization-Tab

**Bestehende Infrastruktur nutzen:**
- JSON-Config-System (ConfigLoader, RegimeDetector, StrategyRouter) bleibt
- Backtest-Engine wird erweitert, nicht ersetzt
- FeatureEngine bekommt neue Indikatoren
- Entry Analyzer UI wird erweitert (nicht neu gebaut)

**Zeitrahmen:** 5-6 Wochen Vollzeit (25-32 Tage), schrittweise umsetzbar

**Risiko-Mitigation:** Performance-Tests, Parallel-Processing, Graceful Degradation, Schema-Versionierung

**Nächster Schritt:** User-Feedback einholen und mit **Phase 0 + Phase 2** starten.
