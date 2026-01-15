# Engine Settings - Entry/Exit Variablen

## Übersicht

Diese Dokumentation listet alle Variablen aus den Engine Settings Tabs auf, die Einfluss auf Entry- und Exit-Punkte haben.

**Gesamt: ~85+ Variablen** in 6 Hauptkategorien

---

## 1. Entry Score Settings

### 1.1 Entry Score Weights (Gewichtungen)

Die Gewichtungen beeinflussen, wie stark jede Komponente zum Gesamt-Entry-Score beiträgt. **Summe muss 1.0 (100%) ergeben.**

| Variable | Typ | Min | Max | Default | Beschreibung |
|----------|-----|-----|-----|---------|--------------|
| `weight_trend_alignment` | float | 0.0 | 1.0 | 0.25 | EMA-Stack Trend-Alignment Gewichtung |
| `weight_rsi` | float | 0.0 | 1.0 | 0.15 | RSI Momentum Gewichtung |
| `weight_macd` | float | 0.0 | 1.0 | 0.20 | MACD Crossover Gewichtung |
| `weight_adx` | float | 0.0 | 1.0 | 0.15 | ADX Trendstärke Gewichtung |
| `weight_volatility` | float | 0.0 | 1.0 | 0.10 | ATR/BB Volatilität Gewichtung |
| `weight_volume` | float | 0.0 | 1.0 | 0.15 | Volumen-Bestätigung Gewichtung |

### 1.2 Entry Score Thresholds

| Variable | Typ | Min | Max | Default | Beschreibung |
|----------|-----|-----|-----|---------|--------------|
| `min_score_for_entry` | float | 0.1 | 0.9 | 0.50 | Minimum Score für gültiges Entry-Signal |
| `boost_threshold` | float | 0.6 | 1.0 | 0.75 | Score ab dem Boost angewendet wird |

### 1.3 Entry Score Gates (Boolean Filter)

Gates können Entries komplett blockieren, unabhängig vom Score.

| Variable | Typ | Default | Beschreibung |
|----------|-----|---------|--------------|
| `gate_block_in_chop` | bool | True | Entry bei Seitwärtsbewegung (Chop) blockieren |
| `gate_block_against_strong_trend` | bool | True | Entry gegen starken Trend blockieren |
| `gate_allow_counter_trend_sfp` | bool | False | SFP Counter-Trend trotzdem erlauben |

### 1.4 Entry Score Modifiers

| Variable | Typ | Min | Max | Default | Beschreibung |
|----------|-----|-----|-----|---------|--------------|
| `boost_modifier` | float | 0.0 | 0.5 | 0.10 | Score-Boost bei sehr guten Bedingungen |
| `chop_penalty` | float | 0.0 | 0.5 | 0.15 | Score-Abzug bei Chop-Markt |
| `volatile_penalty` | float | 0.0 | 0.5 | 0.10 | Score-Abzug bei extremer Volatilität |

---

## 2. Trigger/Exit Settings

### 2.1 Breakout Trigger

| Variable | Typ | Min | Max | Default | Beschreibung |
|----------|-----|-----|-----|---------|--------------|
| `breakout_enabled` | bool | - | - | True | Breakout-Trigger aktivieren |
| `breakout_volume_mult` | float | 1.0 | 5.0 | 1.5 | Mindest-Volumen-Multiplikator für Breakout |
| `breakout_close_threshold` | float | 0.1 | 2.0 | 0.5 | % über Level für gültigen Close-Breakout |

### 2.2 Pullback Trigger

| Variable | Typ | Min | Max | Default | Beschreibung |
|----------|-----|-----|-----|---------|--------------|
| `pullback_enabled` | bool | - | - | True | Pullback-Trigger aktivieren |
| `pullback_max_distance` | float | 0.5 | 3.0 | 1.0 | Max ATR-Entfernung vom Level |
| `pullback_rejection_wick` | float | 0.1 | 1.0 | 0.3 | Min Wick-Rejection in ATR |

### 2.3 SFP (Sweep/Fake/Push) Trigger

| Variable | Typ | Min | Max | Default | Beschreibung |
|----------|-----|-----|-----|---------|--------------|
| `sfp_enabled` | bool | - | - | True | SFP-Trigger aktivieren |
| `sfp_wick_body_ratio` | float | 0.5 | 5.0 | 2.0 | Min Wick-zu-Body Verhältnis |
| `sfp_penetration` | float | 0.0 | 1.0 | 0.3 | Penetration des Levels in % |

### 2.4 Stop-Loss Settings

| Variable | Typ | Min | Max | Default | Beschreibung |
|----------|-----|-----|-----|---------|--------------|
| `sl_type` | enum | - | - | "ATR" | SL-Typ: ATR, Percent, Structure |
| `sl_atr_multiplier` | float | 0.5 | 5.0 | 1.5 | ATR-Multiplikator für SL |
| `sl_percent` | float | 0.1 | 10.0 | 1.0 | Fester Prozent-SL |
| `sl_structure_buffer` | float | 0.1 | 1.0 | 0.2 | Buffer unter/über Structure in ATR |

### 2.5 Take-Profit Settings

| Variable | Typ | Min | Max | Default | Beschreibung |
|----------|-----|-----|-----|---------|--------------|
| `tp_rr_ratio` | float | 1.0 | 10.0 | 2.0 | Risk-Reward Ratio für TP |
| `tp_atr_multiplier` | float | 1.0 | 10.0 | 3.0 | ATR-Multiplikator für TP |
| `tp_use_level` | bool | - | - | True | Nächstes Level als TP verwenden |

### 2.6 Trailing Stop Settings

| Variable | Typ | Min | Max | Default | Beschreibung |
|----------|-----|-----|-----|---------|--------------|
| `trailing_enabled` | bool | - | - | True | Trailing-Stop aktivieren |
| `trailing_activation` | float | 0.5 | 5.0 | 1.0 | Aktivierung ab X × Risk im Profit |
| `trailing_distance` | float | 0.3 | 2.0 | 0.5 | Trailing-Distanz in ATR |
| `trailing_step` | float | 0.1 | 1.0 | 0.2 | Step-Size für Trailing in ATR |
| `trailing_move_to_be` | bool | - | - | True | SL auf Break-Even verschieben |

### 2.7 Time-Based Exit

| Variable | Typ | Min | Max | Default | Beschreibung |
|----------|-----|-----|-----|---------|--------------|
| `time_exit_enabled` | bool | - | - | False | Zeit-basierter Exit aktivieren |
| `max_hold_hours` | int | 1 | 168 | 24 | Maximale Haltezeit in Stunden |

### 2.8 Partial Take-Profit

| Variable | Typ | Min | Max | Default | Beschreibung |
|----------|-----|-----|-----|---------|--------------|
| `partial_tp_enabled` | bool | - | - | False | Partial TP aktivieren |
| `partial_tp1_r` | float | 0.5 | 3.0 | 1.0 | TP1 bei X × Risk |
| `partial_tp1_size` | int | 10 | 90 | 50 | TP1 Positionsgröße (%) |
| `partial_move_sl_after_tp1` | bool | - | - | True | SL nach TP1 auf Entry verschieben |

---

## 3. Leverage Settings

### 3.1 Leverage Tier Limits

| Variable | Typ | Min | Max | Default | Beschreibung |
|----------|-----|-----|-----|---------|--------------|
| `leverage_tier_1` | int | 1 | 50 | 5 | Max Leverage Tier 1 (niedriger Score) |
| `leverage_tier_2` | int | 1 | 50 | 10 | Max Leverage Tier 2 |
| `leverage_tier_3` | int | 1 | 50 | 15 | Max Leverage Tier 3 |
| `leverage_tier_4` | int | 1 | 50 | 20 | Max Leverage Tier 4 (hoher Score) |

### 3.2 Regime Leverage Multipliers

| Variable | Typ | Min | Max | Default | Beschreibung |
|----------|-----|-----|-----|---------|--------------|
| `regime_mult_strong_trend` | float | 0.5 | 1.5 | 1.0 | Multiplikator bei starkem Trend |
| `regime_mult_weak_trend` | float | 0.5 | 1.5 | 0.8 | Multiplikator bei schwachem Trend |
| `regime_mult_neutral` | float | 0.5 | 1.5 | 0.7 | Multiplikator bei neutralem Markt |
| `regime_mult_chop` | float | 0.5 | 1.5 | 0.5 | Multiplikator bei Chop |
| `regime_mult_volatile` | float | 0.5 | 1.5 | 0.6 | Multiplikator bei hoher Volatilität |

### 3.3 Safety Settings

| Variable | Typ | Min | Max | Default | Beschreibung |
|----------|-----|-----|-----|---------|--------------|
| `min_liquidation_distance` | float | 1.0 | 20.0 | 5.0 | Min Abstand zur Liquidation (%) |
| `sl_before_liquidation` | bool | - | - | True | SL muss vor Liquidationspreis sein |
| `auto_reduce_leverage` | bool | - | - | True | Leverage automatisch reduzieren |

### 3.4 Account Risk Limits

| Variable | Typ | Min | Max | Default | Beschreibung |
|----------|-----|-----|-----|---------|--------------|
| `max_position_risk_pct` | float | 0.5 | 10.0 | 2.0 | Max Risiko pro Position (%) |
| `max_daily_exposure_pct` | float | 5.0 | 100.0 | 20.0 | Max tägliche Exposure (%) |
| `max_concurrent_positions` | int | 1 | 10 | 3 | Max gleichzeitige Positionen |

---

## 4. Level Settings

### 4.1 Swing Detection

| Variable | Typ | Min | Max | Default | Beschreibung |
|----------|-----|-----|-----|---------|--------------|
| `swing_lookback` | int | 3 | 50 | 10 | Lookback-Periode für Swing-Erkennung |
| `min_touches` | int | 1 | 10 | 2 | Min Touches für gültiges Level |

### 4.2 Zone Width

| Variable | Typ | Min | Max | Default | Beschreibung |
|----------|-----|-----|-----|---------|--------------|
| `zone_atr_multiplier` | float | 0.1 | 2.0 | 0.5 | Zone-Breite als ATR-Multiplikator |
| `zone_min_pct` | float | 0.01 | 1.0 | 0.1 | Minimum Zone-Breite (%) |
| `zone_max_pct` | float | 0.5 | 5.0 | 1.0 | Maximum Zone-Breite (%) |

### 4.3 Level Filtering

| Variable | Typ | Min | Max | Default | Beschreibung |
|----------|-----|-----|-----|---------|--------------|
| `max_levels` | int | 5 | 50 | 20 | Max Anzahl aktiver Levels |
| `proximity_merge_pct` | float | 0.1 | 2.0 | 0.5 | Levels innerhalb X% zusammenführen |
| `strong_threshold` | float | 0.5 | 1.0 | 0.7 | Schwelle für "starkes" Level |
| `key_threshold` | float | 0.7 | 1.0 | 0.9 | Schwelle für "Key" Level |

### 4.4 Pivot Points

| Variable | Typ | Default | Beschreibung |
|----------|-----|---------|--------------|
| `include_pivots` | bool | True | Pivot Points einbeziehen |
| `pivot_type` | enum | "Standard" | Pivot-Typ: Standard, Fibonacci, Woodie, Camarilla |

### 4.5 Historical Levels

| Variable | Typ | Min | Max | Default | Beschreibung |
|----------|-----|-----|-----|---------|--------------|
| `include_daily_levels` | bool | - | - | True | Daily High/Low einbeziehen |
| `daily_lookback` | int | 1 | 30 | 5 | Daily Lookback-Tage |
| `include_weekly_levels` | bool | - | - | True | Weekly High/Low einbeziehen |
| `weekly_lookback` | int | 1 | 12 | 4 | Weekly Lookback-Wochen |

---

## 5. LLM Validation Settings

### 5.1 General Settings

| Variable | Typ | Min | Max | Default | Beschreibung |
|----------|-----|-----|-----|---------|--------------|
| `llm_enabled` | bool | - | - | False | LLM-Validierung aktivieren |
| `llm_fallback_to_technical` | bool | - | - | True | Fallback auf technische Analyse bei Fehler |
| `llm_timeout` | int | 5 | 120 | 30 | Timeout für LLM-Anfrage (Sekunden) |

### 5.2 Routing Thresholds

| Variable | Typ | Min | Max | Default | Beschreibung |
|----------|-----|-----|-----|---------|--------------|
| `quick_approve_threshold` | float | 0.5 | 1.0 | 0.75 | Quick-Check Approval ab Score |
| `quick_to_deep_threshold` | float | 0.3 | 0.8 | 0.50 | Quick zu Deep-Check ab Score |
| `deep_approve_threshold` | float | 0.4 | 1.0 | 0.60 | Deep-Check Approval ab Score |
| `deep_veto_threshold` | float | 0.2 | 0.6 | 0.30 | Deep-Check Veto unter Score |

### 5.3 Score Modifiers

| Variable | Typ | Min | Max | Default | Beschreibung |
|----------|-----|-----|-----|---------|--------------|
| `llm_boost_modifier` | float | 0.0 | 0.5 | 0.10 | Score-Boost bei LLM-Approval |
| `llm_caution_modifier` | float | -0.5 | 0.0 | -0.10 | Score-Reduktion bei LLM-Warnung |

### 5.4 Prompt Settings

| Variable | Typ | Min | Max | Default | Beschreibung |
|----------|-----|-----|-----|---------|--------------|
| `prompt_include_levels` | bool | - | - | True | Level-Informationen im Prompt |
| `prompt_include_indicators` | bool | - | - | True | Indikator-Werte im Prompt |
| `prompt_max_candles` | int | 0 | 50 | 20 | Max Kerzen im Prompt |
| `prompt_max_tokens` | int | 500 | 5000 | 2000 | Max Tokens für LLM-Antwort |

---

## 6. Risk Management Settings

### 6.1 Trade Risk

| Variable | Typ | Min | Max | Default | Beschreibung |
|----------|-----|-----|-----|---------|--------------|
| `risk_per_trade_pct` | float | 0.1 | 10.0 | 1.0 | Risiko pro Trade (% vom Kapital) |
| `base_leverage` | int | 1 | 50 | 5 | Basis-Leverage |
| `max_leverage` | int | 1 | 125 | 20 | Maximum Leverage |

### 6.2 Daily Limits

| Variable | Typ | Min | Max | Default | Beschreibung |
|----------|-----|-----|-----|---------|--------------|
| `max_daily_loss_pct` | float | 1.0 | 20.0 | 5.0 | Max Tagesverlust (%) |
| `max_daily_trades` | int | 1 | 50 | 10 | Max Trades pro Tag |

---

## Zusammenfassung nach Kategorien

| Kategorie | Anzahl Variablen | Einfluss auf |
|-----------|------------------|--------------|
| Entry Score | 15 | Entry-Entscheidung, Signal-Qualität |
| Trigger/Exit | 26 | Entry-Trigger, Exit-Strategie |
| Leverage | 14 | Positionsgröße, Risiko |
| Level | 15 | Level-Erkennung, Zone-Breite |
| LLM Validation | 12 | AI-Validierung, Score-Modifikation |
| Risk Management | 6 | Position Sizing, Daily Limits |
| **GESAMT** | **88** | - |

---

## Quelldateien

- `src/ui/widgets/settings/entry_score_settings_widget.py`
- `src/ui/widgets/settings/entry_score_ui_weights.py`
- `src/ui/widgets/settings/entry_score_ui_gates.py`
- `src/ui/widgets/settings/entry_score_ui_thresholds.py`
- `src/ui/widgets/settings/trigger_exit_settings_widget.py`
- `src/ui/widgets/settings/trigger_exit_settings_ui_groups.py`
- `src/ui/widgets/settings/leverage_settings_widget.py`
- `src/ui/widgets/settings/level_settings_widget.py`
- `src/ui/widgets/settings/llm_validation_settings_widget.py`
- `src/core/trading_bot/risk_manager.py`

---

*Dokument erstellt: 2026-01-09*
