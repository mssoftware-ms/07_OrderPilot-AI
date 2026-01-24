# ⚡ Performance-Optimierung für Regime-Optimierung

## Problem: Kombinatorische Explosion

### Stufe 1: Regime-Erkennung
| Parameter | Range | Werte |
|-----------|-------|-------|
| ADX Period | 10-18 (Step 2) | 5 |
| ADX Threshold | 20-30 (Step 2) | 6 |
| SMA Fast | 20-50 (Step 10) | 4 |
| SMA Slow | 100-200 (Step 25) | 5 |
| RSI Period | 9-21 (Step 3) | 5 |
| RSI Sideways Low | 35-45 (Step 5) | 3 |
| RSI Sideways High | 55-65 (Step 5) | 3 |
| BB Period | 15-25 (Step 5) | 3 |
| BB Width Percentile | 0.15-0.25 (Step 0.05) | 3 |
| **TOTAL** | | **5×6×4×5×5×3×3×3×3 = 303,750** |

### Stufe 2: Indikator-Optimierung (pro Regime)
| Indikator | Parameter | Kombinationen |
|-----------|-----------|---------------|
| RSI | period × threshold_low × threshold_high | ~500 |
| MACD | fast × slow × signal | ~200 |
| STOCH | k × d × threshold | ~300 |
| BB | period × std_dev | ~50 |
| ATR | period × multiplier | ~100 |
| EMA | period | ~20 |
| CCI | period × threshold | ~150 |
| **Pro Signal-Type** | | **~1,320** |
| **× 4 Signal-Types** | | **~5,280** |
| **× 3 Regimes** | | **~15,840** |

**Grid Search Gesamtzeit:** 303,750 + 15,840 = **~320,000 Evaluationen**
Bei 100ms pro Evaluation = **~9 Stunden!**

---

## Lösung: 5 kombinierte Strategien

### Strategie 1: Bayesian Optimization (TPE)

TPE (Tree-structured Parzen Estimator) lernt aus vergangenen Trials und fokussiert auf vielversprechende Regionen.

```python
import optuna
from optuna.samplers import TPESampler

def create_regime_study():
    sampler = TPESampler(
        n_startup_trials=20,      # Zufällige Exploration am Anfang
        multivariate=True,        # Berücksichtigt Parameter-Korrelationen
        group=True,               # Gruppiert verwandte Parameter
        seed=42
    )
    
    study = optuna.create_study(
        direction="maximize",
        sampler=sampler,
        storage="sqlite:///optuna_regime.db",
        study_name="regime_optimization"
    )
    return study
```

**Speedup:** ~2,000x (303,750 → 150 Trials)

### Strategie 2: Sequential Parameter Optimization

Optimiere Parameter in Phasen statt alle gleichzeitig:

```python
SEQUENTIAL_PHASES = [
    {
        "name": "adx",
        "params": ["adx_period", "adx_threshold"],
        "trials": 40,
        "description": "Trendstärke-Erkennung optimieren"
    },
    {
        "name": "sma", 
        "params": ["sma_fast_period", "sma_slow_period"],
        "trials": 35,
        "description": "Trendrichtung mit besten ADX-Werten"
    },
    {
        "name": "rsi",
        "params": ["rsi_period", "rsi_sideways_low", "rsi_sideways_high"],
        "trials": 45,
        "description": "Sideways-Erkennung"
    },
    {
        "name": "bb",
        "params": ["bb_period", "bb_width_percentile"],
        "trials": 30,
        "description": "Volatilitäts-Filter"
    }
]
# Total: 150 Trials statt 303,750
```

**Speedup:** ~2,000x

### Strategie 3: Hyperband Pruning (Early Stopping)

Teste auf Daten-Subsets und eliminiere schlechte Kandidaten früh:

```python
from optuna.pruners import HyperbandPruner

pruner = HyperbandPruner(
    min_resource=1,        # Minimum 10% der Daten
    max_resource=100,      # Maximum 100% der Daten
    reduction_factor=3     # Reduziere um Faktor 3 pro Runde
)

def objective_with_pruning(trial):
    params = suggest_params(trial)
    
    # Multi-Fidelity: Teste auf Subsets
    for fidelity in [10, 25, 50, 100]:  # Prozent der Daten
        subset_size = int(len(df) * fidelity / 100)
        score = evaluate_regime(df.iloc[:subset_size], params)
        
        trial.report(score, step=fidelity)
        
        if trial.should_prune():
            raise optuna.TrialPruned()
    
    return score
```

**Speedup:** ~10x zusätzlich

### Strategie 4: Parameter Importance Analysis

Identifiziere wichtige Parameter und fixiere unwichtige:

```python
# Nach 50 Trials analysieren
importance = optuna.importance.get_param_importances(study)

# Beispiel-Ergebnis:
# adx_threshold: 0.35 (WICHTIG)
# sma_slow_period: 0.22 (WICHTIG)
# rsi_period: 0.18 (MITTEL)
# bb_width_percentile: 0.08 (UNWICHTIG → auf Default fixieren)
# bb_period: 0.05 (UNWICHTIG → auf Default fixieren)

# Unwichtige Parameter fixieren
FIXED_PARAMS = {
    "bb_period": 20,
    "bb_width_percentile": 0.20
}
```

**Speedup:** ~2-5x zusätzlich

### Strategie 5: Coarse-to-Fine Optimization

Erst grob, dann fein:

```python
# Phase 1: Grobe Suche
COARSE_RANGES = {
    "adx_period": {"min": 10, "max": 18, "step": 4},      # 3 Werte
    "adx_threshold": {"min": 20, "max": 30, "step": 5},   # 3 Werte
}

# Phase 2: Feine Suche um beste Werte
best_adx_period = 14  # Aus Phase 1
FINE_RANGES = {
    "adx_period": {"min": 12, "max": 16, "step": 1},     # ±2 um besten Wert
}
```

---

## Empfohlene Konfiguration

### Optimization Modes

| Mode | Trials | Zeit | Use Case |
|------|--------|------|----------|
| `quick` | 50 | ~30s | Schnelltest |
| `standard` | 150 | ~2min | Normale Nutzung |
| `thorough` | 300 | ~5min | Finale Optimierung |
| `exhaustive` | 500 | ~10min | Maximale Genauigkeit |

### JSON-Konfiguration

```json
{
  "optimization_config": {
    "mode": "standard",
    "method": "tpe_multivariate",
    "max_trials": 150,
    "n_startup_trials": 20,
    "early_stopping": {
      "enabled": true,
      "pruner": "hyperband",
      "min_fidelity": 0.1,
      "reduction_factor": 3
    },
    "sequential_phases": {
      "enabled": true,
      "phases": [
        {"name": "adx", "params": ["adx_period", "adx_threshold"], "trials": 40},
        {"name": "sma", "params": ["sma_fast_period", "sma_slow_period"], "trials": 35},
        {"name": "rsi", "params": ["rsi_period", "rsi_sideways_low", "rsi_sideways_high"], "trials": 45},
        {"name": "bb", "params": ["bb_period", "bb_width_percentile"], "trials": 30}
      ]
    },
    "parallel": {
      "n_jobs": -1,
      "storage": "sqlite:///optuna_regime.db"
    }
  }
}
```

---

## Implementierung

### RegimeOptimizer mit Optuna

```python
import optuna
from optuna.samplers import TPESampler
from optuna.pruners import HyperbandPruner

class RegimeOptimizer:
    def __init__(self, df: pd.DataFrame, config: dict):
        self.df = df
        self.config = config
        self.study = None
    
    def create_study(self) -> optuna.Study:
        """Erstelle Optuna Study mit optimalen Settings."""
        sampler = TPESampler(
            n_startup_trials=self.config.get("n_startup_trials", 20),
            multivariate=True,
            group=True,
            seed=42
        )
        
        pruner = HyperbandPruner(
            min_resource=1,
            max_resource=100,
            reduction_factor=3
        )
        
        self.study = optuna.create_study(
            direction="maximize",
            sampler=sampler,
            pruner=pruner,
            storage=self.config.get("storage", "sqlite:///optuna.db"),
            study_name=f"regime_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        return self.study
    
    def objective(self, trial: optuna.Trial) -> float:
        """Objective Function für Regime-Optimierung."""
        # Parameter Suggestions
        params = {
            "adx_period": trial.suggest_int("adx_period", 10, 18, step=2),
            "adx_threshold": trial.suggest_int("adx_threshold", 20, 30),
            "sma_fast_period": trial.suggest_int("sma_fast_period", 20, 50, step=10),
            "sma_slow_period": trial.suggest_int("sma_slow_period", 100, 200, step=25),
            "rsi_period": trial.suggest_int("rsi_period", 9, 21, step=3),
            "rsi_sideways_low": trial.suggest_int("rsi_sideways_low", 35, 45, step=5),
            "rsi_sideways_high": trial.suggest_int("rsi_sideways_high", 55, 65, step=5),
            "bb_period": trial.suggest_int("bb_period", 15, 25, step=5),
            "bb_width_percentile": trial.suggest_float("bb_width_percentile", 0.15, 0.25, step=0.05)
        }
        
        # Constraint: SMA Slow > SMA Fast
        if params["sma_slow_period"] <= params["sma_fast_period"]:
            return float("-inf")
        
        # Constraint: RSI High > RSI Low
        if params["rsi_sideways_high"] <= params["rsi_sideways_low"]:
            return float("-inf")
        
        # Multi-Fidelity Evaluation
        for fidelity in [10, 25, 50, 100]:
            subset_size = int(len(self.df) * fidelity / 100)
            score = self._evaluate(self.df.iloc[:subset_size], params)
            
            trial.report(score, step=fidelity)
            
            if trial.should_prune():
                raise optuna.TrialPruned()
        
        return score
    
    def _evaluate(self, df: pd.DataFrame, params: dict) -> float:
        """Evaluiere Regime-Klassifikation."""
        # Indikatoren berechnen
        df = self._calculate_indicators(df, params)
        
        # Regime klassifizieren
        regimes = self._classify_regimes(df, params)
        
        # Score berechnen (F1-gewichtet)
        f1_bull = self._calculate_f1(regimes, "BULL")
        f1_bear = self._calculate_f1(regimes, "BEAR")
        f1_sideways = self._calculate_f1(regimes, "SIDEWAYS")
        stability = self._calculate_stability(regimes)
        
        # Composite Score (Bear wichtiger)
        score = (
            0.30 * f1_bear +      # Bear-Erkennung priorisiert
            0.25 * f1_bull +
            0.20 * f1_sideways +
            0.25 * stability
        ) * 100
        
        return score
    
    def optimize(self, n_trials: int = 150) -> dict:
        """Führe Optimierung durch."""
        if self.study is None:
            self.create_study()
        
        self.study.optimize(
            self.objective,
            n_trials=n_trials,
            n_jobs=self.config.get("n_jobs", -1),
            show_progress_bar=True
        )
        
        return {
            "best_params": self.study.best_params,
            "best_score": self.study.best_value,
            "n_trials": len(self.study.trials),
            "n_pruned": len([t for t in self.study.trials if t.state == optuna.trial.TrialState.PRUNED])
        }
```

---

## Erwartete Speedups

| Strategie | Baseline | Optimiert | Speedup |
|-----------|----------|-----------|---------|
| TPE Sampler | 303,750 | 150 | **2,025x** |
| + Hyperband | 150 | 100 | **1.5x** |
| + Sequential | 100 | 80 | **1.25x** |
| **GESAMT** | 303,750 | ~80-150 | **2,000-3,800x** |

**Praktisch:** 9 Stunden → **2-5 Minuten**

---

## Installation

```bash
pip install optuna optuna-dashboard
```

## Visualisierung

```bash
# Optuna Dashboard starten
optuna-dashboard sqlite:///optuna_regime.db
```

---

## Referenzen

- [Optuna Documentation](https://optuna.readthedocs.io/)
- [TPE Algorithm Paper](https://papers.nips.cc/paper/4443-algorithms-for-hyper-parameter-optimization)
- [Hyperband Paper](https://arxiv.org/abs/1603.06560)
