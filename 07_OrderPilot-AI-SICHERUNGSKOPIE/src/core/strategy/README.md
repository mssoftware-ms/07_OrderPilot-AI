# Strategy Module

## Übersicht

Dieses Modul enthält die Strategie-Engine für Backtesting und Live-Trading.

## Hauptkomponenten

### StrategyEngine (`engine.py`)
- Führt Strategien auf historischen Daten aus
- Berechnet Performance-Metriken
- Unterstützt Optimierung

### StrategyCompiler (`compiler.py`)
- Kompiliert DSL-basierte Strategiedefinitionen
- Validiert Strategie-Syntax

### Strategies (`strategies/`)
- `TrendFollowingStrategy` - Trendfolge (SMA-Crossover)
- `MeanReversionStrategy` - Mean-Reversion (Bollinger Bands)
- `MomentumStrategy` - Momentum-basiert (RSI)
- `BreakoutStrategy` - Ausbruchsstrategien
- `ScalpingStrategy` - Kurzfrist-Trading

## Verwendung

```python
from src.core.strategy.engine import StrategyEngine
from src.core.strategy.strategies import TrendFollowingStrategy

engine = StrategyEngine()
strategy = TrendFollowingStrategy(fast_period=10, slow_period=20)
results = engine.run_backtest(strategy, data)
```

## Neue Strategie erstellen

1. Datei in `strategies/` erstellen
2. Von `BaseStrategy` erben
3. `generate_signals()` implementieren
4. In `strategies/__init__.py` exportieren
