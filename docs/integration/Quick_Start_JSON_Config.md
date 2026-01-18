# Quick Start: Regime-Based JSON Configuration

**Zielgruppe:** Entwickler, die schnell mit dem neuen JSON-Config-System starten wollen

---

## 1. Grundkonzepte (5 Minuten)

### Was ist neu?

**Vorher:**
```python
# Hardcoded Strategy Selection
catalog = StrategyCatalog()
strategy = catalog.get_strategy("trend_following_conservative")
```

**Jetzt:**
```python
# JSON-basierte Konfiguration
config_loader = ConfigLoader(SCHEMA_PATH)
config = config_loader.load_config("my_config.json")

# Automatisches Regime-Detection + Routing
active_regimes = regime_detector.detect(indicator_values)
strategy_set = router.select(active_regimes)
```

### Die 5 Kernkomponenten

1. **Indicators** - Technische Indikatoren (RSI, MACD, ...) auf verschiedenen Timeframes
2. **Regimes** - Marktphasen (Trend, Range, Low-Volume) mit Aktivierungsbedingungen
3. **Strategies** - Handelsstrategien mit Entry/Exit/Risk
4. **Strategy Sets** - Strategiebündel mit Parameter-Overrides
5. **Routing** - Regime → Strategy-Set Zuordnung

---

## 2. Minimales Beispiel (10 Minuten)

Erstelle eine Datei `simple_config.json`:

```json
{
  "schema_version": "1.0",
  "metadata": {
    "author": "me",
    "created_at": "2026-01-18T10:00:00Z",
    "notes": "Simple trend following setup"
  },

  "indicators": [
    {
      "id": "rsi14",
      "type": "RSI",
      "params": { "period": 14 },
      "timeframe": "1h"
    },
    {
      "id": "adx14",
      "type": "ADX",
      "params": { "period": 14 },
      "timeframe": "1h"
    }
  ],

  "regimes": [
    {
      "id": "trending",
      "name": "Trending Market",
      "conditions": {
        "all": [
          {
            "left": { "indicator_id": "adx14", "field": "value" },
            "op": "gt",
            "right": { "value": 25 }
          }
        ]
      }
    }
  ],

  "strategies": [
    {
      "id": "trend_follow",
      "name": "Simple Trend Following",
      "entry": {
        "all": [
          {
            "left": { "indicator_id": "adx14", "field": "value" },
            "op": "gt",
            "right": { "value": 25 }
          },
          {
            "left": { "indicator_id": "rsi14", "field": "value" },
            "op": "gt",
            "right": { "value": 60 }
          }
        ]
      },
      "exit": {
        "any": [
          {
            "left": { "indicator_id": "rsi14", "field": "value" },
            "op": "lt",
            "right": { "value": 40 }
          }
        ]
      },
      "risk": {
        "stop_loss_pct": 2.0,
        "take_profit_pct": 5.0
      }
    }
  ],

  "strategy_sets": [
    {
      "id": "set_trend",
      "name": "Trending Strategies",
      "strategies": [
        { "strategy_id": "trend_follow" }
      ]
    }
  ],

  "routing": [
    {
      "strategy_set_id": "set_trend",
      "match": {
        "all_of": ["trending"]
      }
    }
  ]
}
```

**Verwendung:**
```python
from pathlib import Path
from src.core.tradingbot.config.loader import ConfigLoader
from src.core.tradingbot.bot_controller import BotController

# Load config
config_path = Path("simple_config.json")
bot = BotController(config_path=config_path)

# Bot verwendet jetzt die JSON-Config
```

---

## 3. Multi-Timeframe Setup (15 Minuten)

**Ziel:** Nutze Indikatoren auf mehreren Zeitrahmen für robustere Signale

```json
{
  "indicators": [
    {
      "id": "adx14_1h",
      "type": "ADX",
      "params": { "period": 14 },
      "timeframe": "1h"
    },
    {
      "id": "adx14_4h",
      "type": "ADX",
      "params": { "period": 14 },
      "timeframe": "4h"
    },
    {
      "id": "adx14_1d",
      "type": "ADX",
      "params": { "period": 14 },
      "timeframe": "1d"
    }
  ],

  "regimes": [
    {
      "id": "strong_trend",
      "name": "Strong Trend (Multi-Timeframe Confirmed)",
      "conditions": {
        "all": [
          {
            "left": { "indicator_id": "adx14_1h", "field": "value" },
            "op": "gt",
            "right": { "value": 25 }
          },
          {
            "left": { "indicator_id": "adx14_4h", "field": "value" },
            "op": "gt",
            "right": { "value": 25 }
          },
          {
            "left": { "indicator_id": "adx14_1d", "field": "value" },
            "op": "gt",
            "right": { "value": 20 }
          }
        ]
      }
    }
  ]
}
```

**Vorteil:** Trend muss auf 3 Zeitrahmen bestätigt sein → weniger Fehlsignale

---

## 4. Regime-Scopes für Entry/Exit (20 Minuten)

**Konzept:** Verschiedene Regimes für Entry und Exit - können gleichzeitig aktiv sein

```json
{
  "regimes": [
    {
      "id": "entry_trend",
      "name": "Entry Regime - Strong Trend",
      "scope": "entry",
      "conditions": {
        "all": [
          {
            "left": { "indicator_id": "adx14_1h", "field": "value" },
            "op": "gt",
            "right": { "value": 30 }
          }
        ]
      }
    },
    {
      "id": "exit_low_vol",
      "name": "Exit Regime - Low Volume",
      "scope": "exit",
      "conditions": {
        "all": [
          {
            "left": { "indicator_id": "vol_ratio", "field": "value" },
            "op": "lt",
            "right": { "value": 0.5 }
          }
        ]
      }
    },
    {
      "id": "exit_trend_weakening",
      "name": "Exit Regime - Trend Weakening",
      "scope": "exit",
      "conditions": {
        "all": [
          {
            "left": { "indicator_id": "adx14_1h", "field": "value" },
            "op": "lt",
            "right": { "value": 20 }
          }
        ]
      }
    }
  ],

  "routing": [
    {
      "strategy_set_id": "set_trend_normal",
      "match": {
        "all_of": ["entry_trend"],
        "none_of": ["exit_low_vol", "exit_trend_weakening"]
      }
    },
    {
      "strategy_set_id": "set_trend_exit_mode",
      "match": {
        "all_of": ["entry_trend"],
        "any_of": ["exit_low_vol", "exit_trend_weakening"]
      }
    }
  ]
}
```

**Erklärung:**
- `entry_trend` ist aktiv → Signale für neue Trades
- `exit_low_vol` wird aktiv → Wechsel zu `set_trend_exit_mode` (engere Stops)
- **Beide Regimes gleichzeitig aktiv!**

---

## 5. Parameter-Overrides (25 Minuten)

**Konzept:** Passe Strategie-Parameter an Marktphase an, ohne Duplikate

### Basis-Strategie
```json
{
  "strategies": [
    {
      "id": "trend_follow",
      "name": "Trend Following",
      "risk": {
        "stop_loss_pct": 2.0,
        "take_profit_pct": 5.0,
        "trailing_mode": "atr",
        "trailing_multiplier": 2.0
      }
    }
  ]
}
```

### Strategy Set mit Override (aggressive Version)
```json
{
  "strategy_sets": [
    {
      "id": "set_trend_aggressive",
      "name": "Trend - Aggressive Mode",
      "strategies": [
        {
          "strategy_id": "trend_follow",
          "strategy_overrides": {
            "risk": {
              "stop_loss_pct": 3.0,
              "take_profit_pct": 8.0,
              "trailing_multiplier": 1.5
            }
          }
        }
      ],
      "indicator_overrides": [
        {
          "indicator_id": "rsi14_1h",
          "params": { "period": 21 }
        }
      ]
    }
  ]
}
```

**Ergebnis:**
- Im Set `set_trend_aggressive`:
  - Stop-Loss: 3% statt 2%
  - Take-Profit: 8% statt 5%
  - RSI-Periode: 21 statt 14
- Keine Duplikation der Strategie!

---

## 6. Condition Operatoren (10 Minuten)

### Verfügbare Operatoren

#### `gt` (Greater Than)
```json
{
  "left": { "indicator_id": "rsi14", "field": "value" },
  "op": "gt",
  "right": { "value": 70 }
}
```

#### `lt` (Less Than)
```json
{
  "left": { "indicator_id": "adx14", "field": "value" },
  "op": "lt",
  "right": { "value": 20 }
}
```

#### `eq` (Equal)
```json
{
  "left": { "indicator_id": "stoch_k", "field": "value" },
  "op": "eq",
  "right": { "value": 50 }
}
```

#### `between` (Range)
```json
{
  "left": { "indicator_id": "rsi14", "field": "value" },
  "op": "between",
  "right": { "min": 40, "max": 60 }
}
```

#### Indikator vs. Indikator
```json
{
  "left": { "indicator_id": "sma20", "field": "value" },
  "op": "gt",
  "right": { "indicator_id": "sma50", "field": "value" }
}
```

### Logische Verknüpfungen

#### `all` (UND)
```json
{
  "all": [
    { "left": {...}, "op": "gt", "right": {...} },
    { "left": {...}, "op": "lt", "right": {...} }
  ]
}
```

#### `any` (ODER)
```json
{
  "any": [
    { "left": {...}, "op": "gt", "right": {...} },
    { "left": {...}, "op": "lt", "right": {...} }
  ]
}
```

---

## 7. Validierung & Debugging (15 Minuten)

### JSON Schema Validierung
```python
from src.core.tradingbot.config.loader import ConfigLoader
from pathlib import Path

loader = ConfigLoader(SCHEMA_PATH)

try:
    config = loader.load_config(Path("my_config.json"))
    print("✓ Config is valid")
except Exception as e:
    print(f"✗ Validation failed: {e}")
```

### Debugging Tool
```python
def debug_config(config_path: Path):
    """Debug-Tool für Config-Dateien."""
    loader = ConfigLoader(SCHEMA_PATH)
    config = loader.load_config(config_path)

    print("=== Indicators ===")
    for ind in config.indicators:
        print(f"  {ind.id}: {ind.type} ({ind.timeframe or 'default'})")

    print("\n=== Regimes ===")
    for regime in config.regimes:
        print(f"  {regime.id}: {regime.name} (scope: {regime.scope or 'global'})")

    print("\n=== Strategies ===")
    for strategy in config.strategies:
        print(f"  {strategy.id}: {strategy.name}")

    print("\n=== Strategy Sets ===")
    for strategy_set in config.strategy_sets:
        print(f"  {strategy_set.id}: {len(strategy_set.strategies)} strategies")

    print("\n=== Routing ===")
    for rule in config.routing:
        match = rule.match
        print(f"  {rule.strategy_set_id}:")
        if match.all_of:
            print(f"    all_of: {match.all_of}")
        if match.any_of:
            print(f"    any_of: {match.any_of}")
        if match.none_of:
            print(f"    none_of: {match.none_of}")

# Usage
debug_config(Path("my_config.json"))
```

**Output:**
```
=== Indicators ===
  rsi14_1h: RSI (1h)
  adx14_1h: ADX (1h)
  adx14_4h: ADX (4h)

=== Regimes ===
  trend: Trending Market (scope: global)
  low_vol: Low Volume (scope: exit)

=== Strategies ===
  trend_follow: Trend Following

=== Strategy Sets ===
  set_trend: 1 strategies

=== Routing ===
  set_trend:
    all_of: ['trend']
    none_of: ['low_vol']
```

---

## 8. Migration bestehender Strategien (30 Minuten)

### Automatische Migration
```bash
# Hardcoded Strategien → JSON exportieren
python tools/migrate_to_regime_json.py

# Output: 03_JSON/Trading_Bot/configs/migrated_config.json
```

### Manuelle Anpassung
```python
# Vorher (hardcoded)
class TrendFollowingConservative:
    name = "trend_following_conservative"
    entry_rules = [
        EntryRule(name="ma_alignment", indicator="sma_alignment", ...),
        EntryRule(name="adx_strength", indicator="adx", threshold=25, ...)
    ]
    exit_rules = [...]
    stop_loss_pct = 2.5

# Nachher (JSON)
{
  "id": "trend_following_conservative",
  "name": "Conservative Trend Following",
  "entry": {
    "all": [
      {
        "left": { "indicator_id": "sma20", "field": "value" },
        "op": "gt",
        "right": { "indicator_id": "sma50", "field": "value" }
      },
      {
        "left": { "indicator_id": "adx14", "field": "value" },
        "op": "gt",
        "right": { "value": 25 }
      }
    ]
  },
  "exit": {...},
  "risk": {
    "stop_loss_pct": 2.5,
    "take_profit_pct": 6.25
  }
}
```

---

## 9. Best Practices (10 Minuten)

### DO ✅

1. **Verwende sprechende IDs**
   ```json
   "id": "rsi14_1h"  // ✅ Good
   "id": "ind1"      // ❌ Bad
   ```

2. **Nutze Multi-Timeframe für robuste Signale**
   ```json
   // Trend auf 1h UND 4h bestätigt
   "all": [
     { "indicator_id": "adx14_1h", "op": "gt", "right": {"value": 25} },
     { "indicator_id": "adx14_4h", "op": "gt", "right": {"value": 25} }
   ]
   ```

3. **Nutze Scopes für Entry/Exit**
   ```json
   { "id": "entry_trend", "scope": "entry", ... },
   { "id": "exit_vol_dry", "scope": "exit", ... }
   ```

4. **Kommentiere komplexe Bedingungen**
   ```json
   {
     "notes": "Trend nur aktiv wenn ADX > 25 auf 3 Timeframes"
   }
   ```

5. **Verwende Parameter-Overrides statt Duplikate**
   ```json
   // ✅ Override
   { "strategy_id": "trend_follow", "strategy_overrides": {...} }

   // ❌ Duplikat
   { "id": "trend_follow_v2", ... }
   ```

### DON'T ❌

1. **Keine Magic Numbers ohne Kontext**
   ```json
   // ❌
   { "value": 1.234567 }

   // ✅
   { "value": 1.5, "notes": "1.5x ATR trailing stop" }
   ```

2. **Keine zirkulären Referenzen**
   ```json
   // ❌ Indikator A referenziert Indikator B, B referenziert A
   ```

3. **Keine zu komplexen Bedingungen**
   ```json
   // ❌ Zu viele verschachtelte all/any
   "all": [
     "any": [
       "all": [...]
     ]
   ]

   // ✅ Teile in separate Regimes auf
   ```

---

## 10. Troubleshooting (15 Minuten)

### Problem: "Indicator not found"
```
ValueError: Indicator rsi14.value not found
```

**Lösung:**
```json
// Prüfe: Existiert der Indikator?
{
  "indicators": [
    { "id": "rsi14", "type": "RSI", ... }  // ✅ ID stimmt
  ]
}

// Prüfe: Referenz korrekt?
{
  "left": { "indicator_id": "rsi14", "field": "value" }  // ✅ Korrekt
}
```

### Problem: "No strategy set matched"
```
WARNING: No strategy set matched, using default
```

**Lösung:**
```python
# Debug: Welche Regimes sind aktiv?
active_regimes = regime_detector.detect_active_regimes(indicator_values)
print([r.id for r in active_regimes])  # ['trend', 'low_vol']

# Prüfe: Passt Routing?
{
  "routing": [
    {
      "strategy_set_id": "set_trend",
      "match": {
        "all_of": ["trend"],
        "none_of": ["low_vol"]  // ❌ low_vol ist aktiv → kein Match!
      }
    }
  ]
}
```

### Problem: JSON Schema Validation Error
```
SchemaValidationError: 'stop_loss_pct' is a required property
```

**Lösung:**
```json
// Fehlt ein required field?
{
  "risk": {
    "stop_loss_pct": 2.0  // ✅ Required field hinzugefügt
  }
}
```

---

## 11. Nächste Schritte

1. **Erstelle deine erste Config** - Nutze Beispiel aus Abschnitt 2
2. **Validiere mit Schema** - `python tools/validate_config.py`
3. **Teste im Paper-Trading** - Bot mit JSON-Config starten
4. **Erweitere schrittweise** - Multi-Timeframe, Scopes, Overrides
5. **Optimiere Parameter** - AI Analysis für Backtests

---

**Ressourcen:**
- Vollständiger Plan: `docs/integration/RegimeBasedJSON_Integration_Plan.md`
- JSON Schema: `src/core/tradingbot/config/schema.json`
- Beispiel-Configs: `03_JSON/Trading_Bot/templates/`
- Migration Tool: `tools/migrate_to_regime_json.py`

---

**Happy Coding! 🚀**
