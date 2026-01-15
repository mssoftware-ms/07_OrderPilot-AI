# Backtest-Templates (Bitunix BTC Perp) – Entry + SL + Exit/TP (2 Szenarien)

Stand: 2026-01-09

Diese Vorlage ist so aufgebaut, dass du **nicht** in eine Grid-Explosion läufst, aber trotzdem die **entscheidenden Freiheitsgrade** testest:
- **Entry-Qualität** (Score + Trigger)
- **Stop-Loss** (robust, volatilitätsbasiert)
- **Exit/TP** (Trailing + TP-Mechanik)

> Leitidee: Für Trendfollowing ist **Stop/Trailing** wichtiger als „noch ein Indikator“. ATR-basierte Stops sind dafür der Standard, weil sie sich an Volatilität anpassen.

---

## Szenario 1: Trendfollowing – konservativ (Überleben + große Moves mitnehmen)

| Block | Fix (konstant) | Zu testende Variablen (Kombinationen) | Empfehlung / Begründung |
|---|---|---|---|
| **Entry-Score (Gates)** | `gate_block_in_chop=True`  `gate_block_against_strong_trend=True`  `gate_allow_counter_trend_sfp=False` | *(nicht variieren im ersten Lauf)* | Chop filtern und keine Counter-Trend-„SFP-Ausnahmen“. Das reduziert schlechte Trades. |
| **Entry-Score (Weights)** | Weight-Preset **W1** (Trend/ADX-lastig) ODER **W0** (Default) | `weight_*` **nur als Preset-Auswahl**: `{W0, W1}` | Weights **nicht** voll optimieren → Overfitting-Risiko. Nur 2 Presets testen. |
| **Entry-Score (Threshold)** | — | `min_score_for_entry ∈ {0.60, 0.65, 0.70}` | Konservativ = nur hohe Signalqualität. |
| **Entry-Trigger** | `breakout_enabled=True` `pullback_enabled=True` `sfp_enabled=False` | `breakout_volume_mult ∈ {1.5, 2.0}`  `breakout_close_threshold ∈ {0.4, 0.8}`  `pullback_max_distance ∈ {1.0, 1.6}`  `pullback_rejection_wick ∈ {0.3, 0.5}` | Breakout + Pullback deckt Trend-Continuation sauber ab; SFP aus. |
| **Stop-Loss** | `sl_type="ATR"` | `sl_atr_multiplier ∈ {1.6, 2.0, 2.4}` | Mehr „Luft“ für Trend-Atmung (weniger Noise-Stops). |
| **Take Profit (TP)** | `tp_use_level=True` | `tp_atr_multiplier ∈ {2.0, 2.5, 3.0}` *(oder alternativ `tp_rr_ratio ∈ {2.0, 2.5, 3.0}`)* | TP nicht zu knapp setzen; Level-TP verhindert „zu früh raus“. |
| **Trailing Stop (mitwandern)** | `trailing_enabled=True` `trailing_move_to_be=True` | `trailing_activation ∈ {1.0, 1.5, 2.0}`  `trailing_distance ∈ {0.6, 0.9, 1.2}`  `trailing_step ∈ {0.15, 0.25, 0.35}` | Erst ab Profit aktivieren (Activation), dann mit ATR-Distanz nachziehen. |
| **Risk/Leverage (Safety)** | `min_liquidation_distance` **hart erzwingen** | `risk_per_trade_pct ∈ {0.25, 0.50, 0.75, 1.00}`  `base_leverage ∈ {3, 5, 8}`  `max_leverage ∈ {10, 15}` | Bei 100€: kleines Risiko pro Trade und Leverage nur so hoch, dass Liquidation weit genug weg bleibt. |

**Weight-Presets (Summe = 1.0):**
- **W0 (Default)**: `trend=0.25, rsi=0.15, macd=0.20, adx=0.15, volatility=0.10, volume=0.15`
- **W1 (Trend/ADX-heavy)**: `trend=0.35, rsi=0.10, macd=0.15, adx=0.20, volatility=0.10, volume=0.10`

---

## Szenario 2: Trendfollowing – aggressiv (früher rein, schneller absichern)

| Block | Fix (konstant) | Zu testende Variablen (Kombinationen) | Empfehlung / Begründung |
|---|---|---|---|
| **Entry-Score (Gates)** | `gate_block_in_chop=True`  `gate_block_against_strong_trend=True`  `gate_allow_counter_trend_sfp=True` | *(nicht variieren im ersten Lauf)* | Chop weiter filtern, aber SFP als „aggressiver Re-Entry/Stop-Run“-Trigger zulassen. |
| **Entry-Score (Weights)** | Weight-Preset **W0** (Default) ODER **W2** (Momentum-lastiger) | Preset-Auswahl: `{W0, W2}` | Aggressiv = etwas mehr Momentum/Volatility. |
| **Entry-Score (Threshold)** | — | `min_score_for_entry ∈ {0.45, 0.55, 0.65}` | Niedrigerer Threshold = mehr Trades (aber mehr Fehler). |
| **Entry-Trigger** | `breakout_enabled=True` `sfp_enabled=True` `pullback_enabled=optional` | `breakout_volume_mult ∈ {1.2, 1.6}`  `breakout_close_threshold ∈ {0.3, 0.6}`  `sfp_wick_body_ratio ∈ {1.5, 2.5, 3.5}`  `sfp_penetration ∈ {0.2, 0.35, 0.5}`  *(optional)* `pullback_max_distance ∈ {0.8, 1.2}` | Früherer Entry über Breakout/SFP, aber trotzdem parametrisch begrenzen. |
| **Stop-Loss** | `sl_type="ATR"` *(optional 2. Pass: `"Percent"`)* | `sl_atr_multiplier ∈ {1.0, 1.3, 1.6}` *(optional: `sl_percent ∈ {0.4, 0.6, 0.8}`)* | Enger SL = höhere Stop-Rate. Nur sinnvoll, wenn Trailing/BE gut sitzt. |
| **Take Profit (TP)** | `tp_use_level=False` *(oder True, falls Levels gut sind)* | `tp_atr_multiplier ∈ {1.5, 2.0, 2.5}` *(oder `tp_rr_ratio ∈ {1.5, 2.0, 2.5}`)* | Aggressiv: kleinerer TP + Trailing macht den Rest. |
| **Trailing Stop (mitwandern)** | `trailing_enabled=True` `trailing_move_to_be=True` | `trailing_activation ∈ {0.6, 0.9, 1.2}`  `trailing_distance ∈ {0.4, 0.6, 0.8}`  `trailing_step ∈ {0.10, 0.20, 0.30}` | Früh aktivieren, enger nachziehen. |
| **Risk/Leverage (Safety)** | `min_liquidation_distance` **hart erzwingen** | `risk_per_trade_pct ∈ {0.25, 0.40, 0.60, 0.80}`  `base_leverage ∈ {5, 8, 12}`  `max_leverage ∈ {15, 20}` | Aggressiv heißt nicht „All-in“: Risiko bleibt klein, sonst sind Fees/Slippage tödlich. |

**Weight-Presets (Summe = 1.0):**
- **W0 (Default)**: `trend=0.25, rsi=0.15, macd=0.20, adx=0.15, volatility=0.10, volume=0.15`
- **W2 (Momentum/Volatility)**: `trend=0.25, rsi=0.20, macd=0.20, adx=0.10, volatility=0.15, volume=0.10`

---

## Empfohlene Test-Kombinationen (ohne OOM)

### A) “Grid Essential” (schnell, reproduzierbar)
Pro Szenario **nur** diese 5 Kernhebel kombinieren (alles andere fix):
- `min_score_for_entry` (3 Werte)
- `sl_atr_multiplier` (3 Werte)
- `tp_atr_multiplier` (3 Werte)
- `trailing_activation` (3 Werte)
- `trailing_distance` (3 Werte)

➡️ **3^5 = 243 Läufe pro Szenario** (machbar, keine Speicherkatastrophe)

Optional als separater Block danach:
- Risk/Leverage (z. B. 3×4×2 = 24 Läufe) **mit fixiertem** besten Entry/Exit-Set.

### B) “Random Search” (besserer ROI als große Grids)
Statt mehr Dimensionen in ein Grid zu pressen:
- **300–600 Iterationen pro Szenario**
- kontinuierliche Parameterbereiche samplen (gleichmäßig oder log-uniform, je nach Parameter)

Warum: Random Search findet gute Regionen schneller als Grid, wenn viele Parameter nur schwach wichtig sind.

---

## Parameter-Namen (zu deiner Codebasis passend)
Diese Variablen entsprechen deinen Dokumentationen:
- Batch-Parameter (17 Stück): u. a. `weight_*`, `gate_*`, `min_score_for_entry`, `tp_atr_multiplier`, `sl_atr_multiplier`, `risk_per_trade_pct`, `base_leverage`, `max_leverage`
- Engine Entry/Exit: u. a. `breakout_*`, `pullback_*`, `sfp_*`, `sl_type`, `tp_use_level`, `trailing_*`, `partial_tp_*`, `time_exit_*`, `min_liquidation_distance`

---

## Quellen (nur zur Einordnung, nicht als “Regel”)
- ADX > ~25 wird häufig als „starker Trend“ interpretiert; darunter eher weak/range.  
- ATR-basierte Stops/Trailing sind Standard, weil sie Volatilität adaptieren.  
- Random Search ist typischerweise effizienter als Grid Search bei vielen Hyperparametern.

