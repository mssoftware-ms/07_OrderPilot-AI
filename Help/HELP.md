# OrderPilot-AI - Backtesting Hilfe

Diese Anleitung erklärt Schritt für Schritt, wie du Backtests ausführst und eigene Konfigurationsvarianten erstellst.

---

## Inhaltsverzeichnis

1. [Schnellstart](#1-schnellstart)
2. [Verfügbare Templates](#2-verfügbare-templates)
3. [Backtest ausführen](#3-backtest-ausführen)
4. [Eigene Varianten erstellen](#4-eigene-varianten-erstellen)
5. [Parameter-Referenz](#5-parameter-referenz)
6. [Tipps & Best Practices](#6-tipps--best-practices)

---

## 1. Schnellstart

### Voraussetzungen

- Python 3.10+
- Alle Dependencies installiert (`pip install -r requirements.txt`)
- Historische Daten vorhanden

### Schnellster Weg zum ersten Backtest

```bash
# 1. Template kopieren
cp config/backtest_templates/base_trendfollowing.json config/backtest_templates/mein_test.json

# 2. App starten
python main.py

# 3. Im Bitunix Trading Tab -> Backtest Tab -> Template auswählen -> Start
```

---

## 2. Verfügbare Templates

### Basis-Templates (zum Erweitern)

| Template | Strategie | Timeframe | Beschreibung |
|----------|-----------|-----------|--------------|
| `base_trendfollowing.json` | Trend-Following | 5m | EMA/ADX-basiert, für Trendmärkte |
| `base_scalping.json` | Scalping | 1m | Schnelle Entries, enge Stops |
| `base_mean_reversion.json` | Mean Reversion | 15m | Range-Trading, RSI-basiert |

### Spezialisierte Templates (fertig konfiguriert)

| Template | Basis | Besonderheit |
|----------|-------|--------------|
| `trendfollowing_conservative.json` | base_trendfollowing | Hohe Score-Threshold, breites SL |
| `trendfollowing_aggressive.json` | base_trendfollowing | Frühere Entries, SFP aktiviert |
| `scalping_micro_100eur.json` | base_scalping | Für 100€ Micro-Account optimiert |

---

## 3. Backtest ausführen

### Methode 1: Über die UI

1. **App starten**: `python main.py`
2. **Bitunix Trading Tab** öffnen
3. **Backtest Tab** auswählen
4. **Template** aus Dropdown wählen
5. **Zeitraum** einstellen (Start/End Datum)
6. **Start** klicken

### Methode 2: Über Python-Code

```python
import asyncio
from pathlib import Path
from src.core.backtesting.config_loader import load_config
from src.core.backtesting.batch_runner_v2 import BatchRunnerV2

async def run_backtest():
    # Template laden
    runner = BatchRunnerV2.from_template("trendfollowing_conservative")

    # Progress anzeigen
    runner.set_progress_callback(lambda pct, msg: print(f"{pct}%: {msg}"))

    # Ausführen
    summary = await runner.run()

    # Ergebnisse
    print(f"Beste Variante: {summary.best_run.parameters}")
    print(f"Expectancy: {summary.best_run.metrics.expectancy}")
    print(f"Win Rate: {summary.best_run.metrics.win_rate:.1%}")

asyncio.run(run_backtest())
```

### Methode 3: Einzelner Backtest (ohne Grid)

```python
from src.core.backtesting.backtest_runner import BacktestRunner
from src.core.backtesting.config import BacktestConfig

config = BacktestConfig(
    name="Mein Test",
    risk_per_trade_pct=1.0,
    base_leverage=5,
    sl_atr_multiplier=1.5,
    tp_atr_multiplier=2.0,
)

runner = BacktestRunner(config)
result = await runner.run()
print(result.metrics)
```

---

## 4. Eigene Varianten erstellen

### Methode 1: Extends (Empfohlen)

Erstelle eine neue Datei, die von einem Basis-Template erbt:

```json
{
  "$schema": "../schemas/backtest_config_v2.schema.json",
  "version": "2.0.0",
  "extends": "base_trendfollowing.json",

  "meta": {
    "name": "Meine Trendfollowing Variante",
    "description": "Konservativer mit höherem Score-Threshold",
    "tags": ["custom", "trendfollowing", "btc"]
  },

  "overrides": {
    "entry_score.thresholds.min_score_for_entry.value": 0.70,
    "exit_management.stop_loss.atr_multiplier.value": 2.0,
    "exit_management.take_profit.atr_multiplier.value": 3.0,
    "risk_leverage.base_leverage.value": 3,
    "risk_leverage.risk_per_trade_pct.value": 0.5
  }
}
```

**Speichern als**: `config/backtest_templates/meine_variante.json`

### Methode 2: Vollständige Kopie

1. Kopiere ein Basis-Template:
   ```bash
   cp config/backtest_templates/base_trendfollowing.json \
      config/backtest_templates/meine_strategie.json
   ```

2. Bearbeite die Datei und ändere die gewünschten Werte

### Methode 3: Programmatisch mit Overrides

```python
from src.core.backtesting.batch_runner_v2 import BatchRunnerV2

runner = BatchRunnerV2.from_template(
    "base_scalping",
    overrides={
        "entry_score.thresholds.min_score_for_entry.value": 0.60,
        "exit_management.stop_loss.atr_multiplier.value": 1.5,
        "risk_leverage.base_leverage.value": 10,
        "execution_simulation.initial_capital": 200.0,
    }
)

summary = await runner.run()
```

---

## 5. Parameter-Referenz

### Entry Score Parameter

| Parameter | Pfad | Beschreibung | Empfohlener Bereich |
|-----------|------|--------------|---------------------|
| Min Score | `entry_score.thresholds.min_score_for_entry` | Mindest-Score für Entry | 0.45 - 0.70 |
| Block in Chop | `entry_score.gates.block_in_chop` | Keine Trades bei ADX < 20 | true/false |
| Weight Preset | `entry_score.weights.use_preset` | Indikator-Gewichtung | W0, W1, W2 |

**Weight Presets**:
- **W0** (Default): Ausgewogen
- **W1** (Trend-heavy): Mehr Gewicht auf Trend/ADX
- **W2** (Momentum-heavy): Mehr Gewicht auf RSI/Volatility

### Exit Management Parameter

| Parameter | Pfad | Beschreibung | Empfohlener Bereich |
|-----------|------|--------------|---------------------|
| SL ATR Mult | `exit_management.stop_loss.atr_multiplier` | Stop-Loss als ATR-Vielfaches | 1.0 - 2.5 |
| TP ATR Mult | `exit_management.take_profit.atr_multiplier` | Take-Profit als ATR-Vielfaches | 1.5 - 4.0 |
| Trailing Activation | `exit_management.trailing_stop.activation_atr` | Ab wann Trailing startet | 0.5 - 2.0 |
| Trailing Distance | `exit_management.trailing_stop.distance_atr` | Trailing-Abstand | 0.3 - 1.2 |

### Risk/Leverage Parameter

| Parameter | Pfad | Beschreibung | Empfohlener Bereich |
|-----------|------|--------------|---------------------|
| Risk per Trade | `risk_leverage.risk_per_trade_pct` | Risiko pro Trade in % | 0.25 - 2.0 |
| Base Leverage | `risk_leverage.base_leverage` | Basis-Hebel | 3 - 20 |
| Max Leverage | `risk_leverage.max_leverage` | Maximaler Hebel | 10 - 50 |
| Min Liquidation Dist | `risk_leverage.min_liquidation_distance_pct` | Sicherheitsabstand | 4.0 - 10.0 |

### Optimierbare Parameter aktivieren

Um einen Parameter zu optimieren, setze `optimize: true` und definiere `range`:

```json
{
  "exit_management": {
    "stop_loss": {
      "atr_multiplier": {
        "value": 1.5,
        "optimize": true,
        "range": [1.0, 1.3, 1.5, 1.8, 2.0]
      }
    }
  }
}
```

---

## 6. Tipps & Best Practices

### Grid-Größe kontrollieren

Prüfe vor dem Start, wie viele Kombinationen getestet werden:

```python
from src.core.backtesting.config_loader import load_config, count_grid_combinations

config = load_config("config/backtest_templates/meine_variante.json")
count = count_grid_combinations(config)
print(f"Grid-Kombinationen: {count}")

# Empfehlung:
# < 500: Grid Search OK
# 500-5000: Random Search verwenden
# > 5000: Parameter reduzieren oder Random Search
```

### Parameter-Priorität (nach Impact)

1. **Höchste Priorität** (optimieren):
   - `sl_atr_multiplier`
   - `tp_atr_multiplier`
   - `trailing_activation_atr`
   - `trailing_distance_atr`

2. **Mittlere Priorität** (testen):
   - `min_score_for_entry`
   - `base_leverage`
   - `risk_per_trade_pct`

3. **Niedrige Priorität** (fixieren):
   - Weight-Presets (W0/W1/W2 als Ganzes)
   - Entry Gates
   - Indicator-Parameter

### Overfitting vermeiden

1. **Weights NICHT einzeln optimieren** - Verwende Presets (W0, W1, W2)
2. **Parameter-Gruppen** für logische Paare:
   ```json
   {
     "parameter_groups": [
       {
         "name": "sl_tp_pair",
         "parameters": [
           "exit_management.stop_loss.atr_multiplier.value",
           "exit_management.take_profit.atr_multiplier.value"
         ],
         "combinations": [
           [1.0, 1.5],
           [1.5, 2.0],
           [2.0, 3.0]
         ]
       }
     ]
   }
   ```
3. **Walk-Forward aktivieren** für Out-of-Sample Validierung
4. **min_trades Constraint** hoch setzen (>50)

### Micro-Account (100€) Besonderheiten

- **Fee-Impact beachten**: Bei 0.06% Taker-Fee und kleinen Positionen können Fees 30-75% des Profits auffressen
- **Höherer Leverage nötig**: 15-25x, aber `min_liquidation_distance` einhalten
- **Template verwenden**: `scalping_micro_100eur.json` ist bereits optimiert

### Beispiel: Konservative Strategie erstellen

```json
{
  "extends": "base_trendfollowing.json",
  "meta": {
    "name": "Ultra Konservativ",
    "description": "Nur beste Setups, breites SL, niedriges Risiko"
  },
  "overrides": {
    "entry_score.thresholds.min_score_for_entry.value": 0.75,
    "entry_score.gates.block_in_chop": true,
    "entry_score.gates.allow_counter_trend_sfp": false,
    "exit_management.stop_loss.atr_multiplier.value": 2.5,
    "exit_management.take_profit.atr_multiplier.value": 3.5,
    "risk_leverage.risk_per_trade_pct.value": 0.25,
    "risk_leverage.base_leverage.value": 3,
    "constraints.min_trades": 20,
    "constraints.max_drawdown_pct": 15
  }
}
```

### Beispiel: Aggressive Scalping Strategie

```json
{
  "extends": "base_scalping.json",
  "meta": {
    "name": "Aggressive Scalper",
    "description": "Viele Trades, schnelle Exits"
  },
  "overrides": {
    "entry_score.thresholds.min_score_for_entry.value": 0.45,
    "entry_score.gates.allow_counter_trend_sfp": true,
    "entry_triggers.sfp.enabled": true,
    "exit_management.stop_loss.atr_multiplier.value": 1.0,
    "exit_management.take_profit.atr_multiplier.value": 1.5,
    "exit_management.trailing_stop.activation_atr.value": 0.5,
    "exit_management.time_stop.enabled": true,
    "exit_management.time_stop.max_holding_minutes": 60,
    "risk_leverage.base_leverage.value": 15,
    "constraints.min_trades": 100
  }
}
```

---

## Weitere Dokumentation

- **Migration Guide**: `docs/BACKTEST_CONFIG_V2_MIGRATION.md`
- **Architektur**: `ARCHITECTURE.md`
- **Quickstart**: `QUICKSTART.md`
- **JSON Schema**: `config/schemas/backtest_config_v2.schema.json`

---

## Fehlerbehebung

### "Keine Trades gefunden"

- `min_score_for_entry` zu hoch? Versuche 0.50
- Zeitraum zu kurz? Mindestens 30 Tage
- Gates zu strikt? `block_in_chop` temporär deaktivieren

### "Grid zu groß"

- Reduziere `range` Arrays auf 3-4 Werte
- Verwende `optimization.method: "random"` mit `max_iterations: 500`
- Fixiere Low-Impact Parameter

### "Schlechte Performance"

- SL zu eng? Versuche höheren ATR-Multiplikator
- TP zu weit? Risk:Reward prüfen (1:1.5 bis 1:2 ist typisch für Scalping)
- Leverage zu hoch? Liquidationsrisiko prüfen

---

*Erstellt für OrderPilot-AI v2.0*
