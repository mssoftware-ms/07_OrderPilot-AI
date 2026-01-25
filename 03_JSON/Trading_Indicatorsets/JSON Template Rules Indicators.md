# JSON Template Rules – Indicator Sets v2.0

Referenz für Indicator-Only Configs (Entry/Exit Long/Short), angelehnt an Regime v2.

- `schema_version`: **2.0.0**
- `metadata`: `{ author, created_at, updated_at?, tags?, notes?, trading_style? }`
- `indicators`: **Pflicht**, Liste von Objekten
  - `name`: string (z. B. `TREND_SUPERTREND_FAST`)
  - `type`: string (enum ähnlich Regime: EMA, SMA, ADX, RSI, ATR, BB, MACD, STOCH, SUPERTREND, CCI, VWAP, OBV)
  - `params`: Liste (max. 10)
    - `name`: string
    - `value`: number
    - `range`: `{ min, max, step }` (optional; wird in UI befüllt/überschrieben)
- Optional: `optimization_results`: Array mit gespeicherten Ergebnissen (wie Regime v2)
  - `timestamp`, `score`, `trial_number`, `applied`, `indicators` (gleiche Struktur wie oben)
- Backtest-Meta (optional): `backtest` `{ source: "live|historical", symbol, timeframe, bars_used }`

Pfad-Empfehlung: `03_JSON/Trading_Indicatorsets/*.json`  
Export-Ziel: `03_JSON/Trading_Indicatorsets/exports/indicator_sets_{symbol}_{timeframe}.json`

Validierung: SchemaVersion prüfen, `indicators` ≥ 1, jede `params` ≤ 10, `step > 0` falls angegeben.
