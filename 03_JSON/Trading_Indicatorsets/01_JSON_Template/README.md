# Indicator Set JSON Template (v1.0.0)

Ort: `03_JSON/Trading_Indicatorsets/01_JSON_Template/indicator_set_template.json`

Zweck: Speichert die besten Indikator-Kombinationen pro Signaltyp (Entry/Exit Long/Short) aus der Indicator Optimization V2.

## Struktur
```json
{
  "schema_version": "1.0.0",
  "metadata": {
    "author": "...",
    "created_at": "ISO-8601",
    "updated_at": "ISO-8601",
    "symbol": "BTCUSDT",
    "timeframe": "5m",
    "source": "indicator_optimization_v2",
    "mode": "best_per_indicator",
    "notes": "free text"
  },
  "signal_sets": [
    {
      "signal_type": "entry_long",
      "indicators": [
        {
          "name": "RSI",
          "params": [
            { "name": "period", "value": 14, "range": { "min": 10, "max": 20, "step": 2 } },
            { "name": "oversold", "value": 35, "range": { "min": 25, "max": 40, "step": 5 } },
            { "name": "overbought", "value": 65, "range": { "min": 60, "max": 75, "step": 5 } }
          ],
          "score": 72.5,
          "win_rate": 0.58,
          "profit_factor": 1.35
        }
      ]
    }
  ]
}
```

### Felder
- `schema_version`: immer `"1.0.0"`.
- `metadata`: Pflicht; enthält Quelle, Symbol, Timeframe, Modus (`best_per_indicator` oder `global_best`).
- `signal_sets[*].signal_type`: `"entry_long" | "entry_short" | "exit_long" | "exit_short"`.
- `indicators[*]`: bestes Ergebnis pro Indikator für diesen Signaltyp.
  - `params[*].value`: gewählter Wert.
  - `params[*].range`: optional, dokumentiert Suchraum (min/max/step).
  - `score`, `win_rate`, `profit_factor`: Kennzahlen des besten Laufs.

## Nutzung mit der UI
- Modus **Pro Indikator** erzeugt ein „Best per Indicator“-Set (ein Eintrag je Indikator).
- Modus **Global** liefert weiter das Gesamt-Bestresultat, kann aber ebenfalls in dieses Format exportiert werden (dann nur ein Indikator).
- Export-Ziel: `03_JSON/Trading_Indicatorsets/...` (nicht in Templates schreiben).

## Validierung
Noch kein dediziertes Schema; verwende Pydantic/JSON-Schema nach Bedarf. Stelle sicher, dass `schema_version` gesetzt ist und `signal_sets` nicht leer ist.
