# CE-Editor: Regime Entry JSON-Editor Dokumentation

## Übersicht

Der Regime Entry JSON-Editor im CE-Editor ermöglicht die Konfiguration von Regime-Einstiegen durch eine strukturierte JSON-Datei. Diese Datei definiert, welche Entry Points unter welchen Bedingungen Trades auslösen.

## JSON-Struktur

### Hauptformat

```json
{
  "regimes": [
    {
      "name": "Regime Name",
      "description": "Beschreibung des Regimes",
      "entries": [
        {
          "entry_point_id": "unique_entry_id",
          "enabled": true,
          "parameters": {
            // Spezifische Parameter für diesen Entry Point
          }
        }
      ]
    }
  ]
}
```

### Detaillierte Struktur

#### 1. Regime-Level

```json
{
  "regimes": [
    {
      "name": "Trend Following",              // Eindeutiger Name des Regimes
      "description": "Trend-basierte Strategie mit mehreren Entry Points",
      "active": true,                          // Ist dieses Regime aktiv?
      "priority": 1,                           // Priorität bei Konflikten (1 = höchste)
      "market_condition": "trending",          // Optional: Marktzustand
      "entries": [...]                         // Array von Entry Point Konfigurationen
    }
  ]
}
```

**Regime-Felder:**
- `name`: Eindeutiger Name des Regimes (string, erforderlich)
- `description`: Beschreibung der Strategie (string, optional)
- `active`: Aktivierungsstatus (boolean, default: true)
- `priority`: Priorität bei mehreren Regimes (integer, optional)
- `market_condition`: Zugeordneter Marktzustand (string, optional)
- `entries`: Array von Entry Point Definitionen (array, erforderlich)

#### 2. Entry-Level

```json
{
  "entry_point_id": "breakout_entry_1",      // Referenz zur Cell-Definition
  "enabled": true,                            // Ist dieser Entry Point aktiv?
  "weight": 1.0,                              // Gewichtung im Regime (0.0-1.0)
  "direction": "long",                        // Trade-Richtung: "long", "short", "both"
  "parameters": {
    // Entry-spezifische Parameter
    "stop_loss_pct": 2.0,
    "take_profit_pct": 6.0,
    "position_size_pct": 10.0
  },
  "filters": {
    // Optionale Filter
    "min_volume": 1000000,
    "time_filter": {
      "start": "09:30",
      "end": "16:00"
    }
  },
  "risk_management": {
    // Risk Management Regeln
    "max_risk_per_trade": 2.0,
    "max_portfolio_risk": 10.0
  }
}
```

**Entry-Felder:**
- `entry_point_id`: ID des Entry Points aus Cell (string, erforderlich)
- `enabled`: Aktivierungsstatus dieses Entries (boolean, default: true)
- `weight`: Gewichtung im Regime (float, 0.0-1.0, default: 1.0)
- `direction`: Trade-Richtung (enum: "long"|"short"|"both", default: "both")
- `parameters`: Entry-spezifische Parameter (object, optional)
- `filters`: Zusätzliche Filter (object, optional)
- `risk_management`: Risk Management Konfiguration (object, optional)

### Beispiel: Vollständige Konfiguration

```json
{
  "version": "1.0",
  "last_modified": "2024-01-30T10:00:00Z",
  "regimes": [
    {
      "name": "Trend Following Aggressive",
      "description": "Aggressives Trend-Following mit Breakouts und Pullbacks",
      "active": true,
      "priority": 1,
      "market_condition": "strong_trend",
      "entries": [
        {
          "entry_point_id": "breakout_entry",
          "enabled": true,
          "weight": 1.0,
          "direction": "both",
          "parameters": {
            "breakout_threshold": 0.5,
            "confirmation_bars": 2,
            "stop_loss_pct": 2.0,
            "take_profit_pct": 6.0,
            "position_size_pct": 10.0
          },
          "filters": {
            "min_volume": 1000000,
            "min_volatility": 0.02,
            "time_filter": {
              "start": "09:45",
              "end": "15:30"
            }
          },
          "risk_management": {
            "max_risk_per_trade": 2.0,
            "max_portfolio_risk": 10.0,
            "max_correlation": 0.7
          }
        },
        {
          "entry_point_id": "pullback_entry",
          "enabled": true,
          "weight": 0.8,
          "direction": "long",
          "parameters": {
            "pullback_depth": 0.382,
            "fib_level": "382",
            "stop_loss_pct": 1.5,
            "take_profit_pct": 4.5,
            "position_size_pct": 8.0
          },
          "filters": {
            "min_volume": 800000,
            "trend_strength_min": 0.6
          },
          "risk_management": {
            "max_risk_per_trade": 1.5,
            "trailing_stop": true,
            "trailing_stop_pct": 1.0
          }
        }
      ]
    },
    {
      "name": "Mean Reversion",
      "description": "Mean Reversion Strategie für Range-Markets",
      "active": true,
      "priority": 2,
      "market_condition": "ranging",
      "entries": [
        {
          "entry_point_id": "oversold_bounce",
          "enabled": true,
          "weight": 1.0,
          "direction": "long",
          "parameters": {
            "rsi_threshold": 30,
            "bb_position": "lower",
            "stop_loss_pct": 1.0,
            "take_profit_pct": 2.0,
            "position_size_pct": 5.0
          },
          "filters": {
            "max_volatility": 0.03,
            "range_bound": true
          },
          "risk_management": {
            "max_risk_per_trade": 1.0,
            "max_positions": 5
          }
        }
      ]
    }
  ],
  "global_settings": {
    "max_concurrent_entries": 3,
    "default_stop_loss_pct": 2.0,
    "default_take_profit_pct": 4.0,
    "default_position_size_pct": 5.0
  }
}
```

## Import-Funktion

### Import aus Datei

Der CE-Editor unterstützt das Importieren von Regime-Konfigurationen aus externen JSON-Dateien.

**Siehe:** [Regime JSON Import Guide](./ce-regime-json-import.md) für detaillierte Import-Anweisungen.

**Kurz-Übersicht:**

1. **Datei vorbereiten**: JSON-Datei mit korrekter Struktur erstellen
2. **Import im Editor**: 
   - "Import" Button im Regime Editor
   - Datei auswählen
   - Validierung durchführen
3. **Merge-Optionen**:
   - `replace`: Überschreibt bestehende Regimes
   - `merge`: Fügt neue Regimes hinzu
   - `update`: Aktualisiert nur vorhandene IDs

### Export-Funktion

Bestehende Konfigurationen können exportiert werden:

```python
# Export aktuelle Konfiguration
editor.export_regime_config(filepath="my_regimes.json")
```

## Validierung

### Automatische Validierung

Der Editor validiert automatisch:

1. **Struktur-Validierung**:
   - JSON-Syntax
   - Erforderliche Felder
   - Datentypen

2. **Referenz-Validierung**:
   - `entry_point_id` existiert in Cell
   - Referenzierte Entry Points sind definiert

3. **Werte-Validierung**:
   - Prozentsätze im gültigen Bereich (0-100)
   - Zeiten im korrekten Format (HH:MM)
   - Weights zwischen 0.0 und 1.0

4. **Logik-Validierung**:
   - Stop Loss < Take Profit
   - Position Size nicht über 100%
   - Keine widersprüchlichen Filter

### Fehlerbehandlung

Validierungsfehler werden kategorisiert:

```json
{
  "validation_errors": [
    {
      "type": "missing_field",
      "location": "regimes[0].entries[1]",
      "field": "entry_point_id",
      "message": "Required field 'entry_point_id' is missing"
    },
    {
      "type": "invalid_reference",
      "location": "regimes[0].entries[0].entry_point_id",
      "value": "unknown_entry",
      "message": "Entry point 'unknown_entry' not found in Cell definitions"
    },
    {
      "type": "value_out_of_range",
      "location": "regimes[0].entries[0].parameters.position_size_pct",
      "value": 150,
      "message": "Position size 150% exceeds maximum of 100%"
    }
  ]
}
```

## Best Practices

### 1. Namenskonvention

```json
{
  "entry_point_id": "strategy_condition_direction_variant",
  // Beispiele:
  // "breakout_strong_long_v1"
  // "pullback_fib382_both_v2"
  // "meanrev_rsi_long_v1"
}
```

### 2. Modulare Regimes

Halte Regimes fokussiert:
- Ein Regime = Eine Strategie
- Verwende Priority für Multi-Regime-Setups
- Separate Regimes für verschiedene Marktbedingungen

### 3. Parameter-Organisation

```json
{
  "parameters": {
    // Gruppierung nach Funktion
    "entry": {
      "threshold": 0.5,
      "confirmation_bars": 2
    },
    "exit": {
      "stop_loss_pct": 2.0,
      "take_profit_pct": 6.0
    },
    "sizing": {
      "position_size_pct": 10.0,
      "max_leverage": 1.0
    }
  }
}
```

### 4. Versionierung

```json
{
  "version": "1.2.3",
  "last_modified": "2024-01-30T10:00:00Z",
  "author": "Maik",
  "changelog": [
    {
      "version": "1.2.3",
      "date": "2024-01-30",
      "changes": "Added volume filter to breakout entry"
    }
  ]
}
```

### 5. Dokumentation

Kommentiere komplexe Logik:

```json
{
  "entry_point_id": "custom_breakout",
  "description": "Breakout mit Volumen-Bestätigung und ATR-Filter",
  "parameters": {
    "breakout_threshold": 0.5,
    // Threshold ist % über Resistance
    "volume_multiple": 1.5,
    // 1.5x average volume erforderlich
    "atr_multiple": 1.2
    // Volatility muss mindestens 1.2x ATR sein
  }
}
```

## Schema-Referenz

### JSON Schema (v1.0)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["regimes"],
  "properties": {
    "version": {"type": "string"},
    "last_modified": {"type": "string", "format": "date-time"},
    "regimes": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["name", "entries"],
        "properties": {
          "name": {"type": "string"},
          "description": {"type": "string"},
          "active": {"type": "boolean"},
          "priority": {"type": "integer", "minimum": 1},
          "market_condition": {"type": "string"},
          "entries": {
            "type": "array",
            "items": {
              "type": "object",
              "required": ["entry_point_id"],
              "properties": {
                "entry_point_id": {"type": "string"},
                "enabled": {"type": "boolean"},
                "weight": {"type": "number", "minimum": 0, "maximum": 1},
                "direction": {"enum": ["long", "short", "both"]},
                "parameters": {"type": "object"},
                "filters": {"type": "object"},
                "risk_management": {"type": "object"}
              }
            }
          }
        }
      }
    },
    "global_settings": {"type": "object"}
  }
}
```

## Fehlerbehandlung & Troubleshooting

### Häufige Fehler

**1. Entry Point nicht gefunden**
```
Error: Entry point 'my_entry' not found in Cell definitions
```
→ Stelle sicher, dass der Entry Point in Cell definiert ist

**2. Ungültige JSON-Syntax**
```
Error: Unexpected token } at position 145
```
→ Prüfe JSON-Syntax mit einem Validator

**3. Fehlende erforderliche Felder**
```
Error: Required field 'entry_point_id' missing in entry
```
→ Füge alle erforderlichen Felder hinzu

**4. Werte außerhalb des Bereichs**
```
Error: position_size_pct must be between 0 and 100
```
→ Korrigiere die Parameterwerte

### Debug-Modus

Aktiviere Debug-Logging für detaillierte Informationen:

```python
editor.set_debug_mode(True)
editor.load_regime_config("my_config.json")
# Zeigt detaillierte Validierungs- und Lade-Informationen
```

## Siehe auch

- [Regime JSON Import Guide](./ce-regime-json-import.md) - Detaillierte Import-Anweisungen
- [Entry Point Definition in Cell](./cell-entry-point-definition.md) - Cell Entry Point Syntax
- [Trade Execution Flow](./trade-execution-flow.md) - Kompletter Ablaufplan
- [Trade Execution Diagram](./trade-execution-diagram.md) - Visuelles Ablaufdiagramm

## Changelog

### Version 1.0.0 (2024-01-30)
- Initiale Dokumentation
- JSON-Schema v1.0
- Import/Export Funktionalität
- Validierungs-Engine
