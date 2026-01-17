# OrderPilot-AI – StrategySpec & ExecutionWorkflow Spezifikation (v1.0)

> Zweck: Ein **gemeinsames, versioniertes JSON-Protokoll**, das im **Entry Designer (Backtest/Optimierung)** und im **Trading Bot (Live/Paper)** **identisch und deterministisch** interpretiert wird.  
> Fokus: **BTCUSDT Futures, 5m**, **Isolated Margin zwingend**, **max. 1 aktiver Stop-Loss** (Replace/Ablöse-Regel).  
> Erweiterung: Optionaler **ExecutionWorkflow** als „Automation Layer“ (Event-getrieben), ohne die StrategySpec zu verschmutzen.

---

## 1) Architektur-Überblick (Stichpunkte)

### Kernprinzip: StrategySpec vs. ExecutionWorkflow
- **StrategySpec (Core / Shared)**
  - beschreibt **Signal-Logik & statische Handelsparameter**: Indikatoren, Entry/Exit, Risk, Kostenreferenzen, Datenanforderungen.
  - ist **vollständig deterministisch** im Backtest und identisch interpretierbar im Live-Bot.
  - ist **erweiterbar ohne Breaking Changes** (schema_version + Migration).
- **ExecutionWorkflow (Bot Extension / Optional)**
  - beschreibt **Event-getriebene Automationen**: z. B. Trailing erst nach Profit+Momentum aktivieren, Stop ersetzen, Teilverkäufe.
  - darf StrategySpec **nur referenzieren**, nicht verändern.
  - erzwingt Policies (z. B. `single_active_stop`) und Idempotenz-Regeln.

### Determinismus
- Default: **strict_candle_close**
  - Signale **nur** bei Bar-Close.
  - Indikatorwerte basieren nur auf `t <= close` (kein Lookahead).
  - Exits durch SL/TP werden in diesem Profil **auf Bar-Close** verarbeitet (konservativ, deterministisch).
- Optional: **hybrid_intrabar**
  - Exits (SL/TP/Trailing) können **intrabar** triggern (z. B. mit High/Low der Kerze oder Tick-/Sub-Bar-Daten).
  - Erfordert **klar definierte Fill-Prioritäten** (z. B. SL vor TP) und **einheitliche Simulation** für Backtest und Live.
  - Empfehlung: hybrid nur aktivieren, wenn Live-Engine **denselben Trigger-Mechanismus** nutzt (z. B. Tickfeed oder 1m Subbars).

### Exchange-Limitierungen & Virtual Orders
- Ziel: korrekte Semantik auch ohne native Stop-/OCO-/Trailing-Orders.
- **Bot-managed / virtuelle Orders**:
  - Stop-Loss / Take-Profit / Trailing werden als **interner Zustand** geführt.
  - Ausführung über **Market-Order** (oder aggressive Limit-Order) beim Trigger.
- **Safety-Layer (Fail-Safe)**
  - Optionaler „Weit-Stop“ als native Exchange-Order (falls verfügbar) als **Disconnect-Fallback**.
  - Bei Reconnect: **State-Reconciliation** (Position, offene Orders, letzter Trigger-Stand) und ggf. Not-Exit.
- **Race Conditions / Requotes**
  - Trigger → `order_intent_id` erzeugen → nur **ein** Exit-Intent pro Position/Trigger.
  - Anti-Duplikate durch `execution_id`/`order_intent_id` + idempotente Handlers.
  - Slippage-/Spread-Guards: definierte `max_slippage_bps` + „circuit breaker“ bei abnormalem Markt.

### Single Active Stop-Loss Policy
- Zu jeder Zeit gilt: **genau 1 aktiver Stop**.
- Jede Änderung erfolgt ausschließlich via **Replace/Ablöse**:
  - `replace_stop_loss(...)`
  - `enable_trailing_stop(...)` (impliziert Replace)
  - `set_breakeven_stop(...)` (impliziert Replace)
- Validator und Workflow-Engine verhindern parallele Stop-Setups.

### Strategy Library & Hot-Swap
- Mehrere StrategySpecs können in einer Library versioniert, getestet, signiert und selektiert werden.
- Hot-Swap nur unter klaren Regeln:
  - **Standard:** Strategy-Wechsel nur in „flat“ (keine offene Position) oder über definierte Transition-Policy.
  - Regime-basierte Auswahl (Trend/Range/Volatilität) über externes Regime-Interface (siehe unten).

### Regime Detection Interface
- Regime-Erkennung ist **separat** (KI/Optimierer/Statistik-Modul).
- StrategySpec bekommt nur:
  - deklarative **Regime-Tags** (wo sie passt),
  - optional **Regime-Annotation** von Optimizer,
  - keine gemischte Logik im Kern.

### Partial Fills & Idempotency (Execution-Engineer-Sicht)
- Jede Aktion erzeugt einen **Intent**:
  - `order_intent_id` (clientOrderId)
  - `execution_id` (interne Ausführungs-Kette)
- Events sind **at-least-once** zu behandeln:
  - doppelte Events dürfen keine doppelte Order auslösen.
- Partial fills führen zu Zuständen:
  - `PARTIAL` → ggf. Restmenge managen (cancel/replace) gemäß Execution-Policy.
  - Stops/TP werden **auf Remaining Qty** angepasst.

---

## 2) Konkretes Datenmodell (StrategySpec v1.0)

### Top-Level
- `meta` *(required)*
- `market` *(required)*
- `determinism` *(required)*
- `data_requirements` *(optional)*
- `indicators` *(required)*
- `entry` *(required)*
- `exit` *(required)*
- `risk` *(required)*
- `execution` *(required)*
- `costs` *(optional)*
- `optimization` *(optional)*
- `regime` *(optional)*
- `security` *(optional)*

### meta
- `schema_version` *(string, required)* – z. B. `"1.0"`
- `id` *(string, required)* – stabiler Identifier
- `name` *(string, required)*
- `tags` *(string[], optional)*
- `created_at` *(string ISO-8601, optional)*
- `author` *(string, optional)*
- `compat` *(object, optional)* – z. B. `{ "entry_designer": ">=1.3", "trading_bot": ">=2.0" }`
- `signature` *(object, optional)* – Signatur/Hash der Datei (Library/Trust)
  - `algo` *(string)* e.g. `"ed25519"` / `"sha256"`
  - `value` *(string)*
  - `signed_at` *(date-time, optional)*

### market
- `exchange` *(string, required)* – `"bitunix"` (lowercase empfohlen)
- `symbol` *(string, required)* – `"BTCUSDT"`
- `product` *(string, required)* – `"futures"`
- `margin_mode` *(string, required)* – **const `"isolated"`**
- `leverage` *(number, optional)* – z. B. `20`
- `timeframe` *(string, required)* – z. B. `"5m"`
- `timezone` *(string, optional, default `"UTC"`)*
- `candle_alignment` *(string, optional, default `"exchange"`)* – `"exchange"|"utc"`

### determinism
- `profile` *(string, required)* – `"strict_candle_close"` | `"hybrid_intrabar"`
- `intrabar_source` *(string, optional)* – `"hl"` (High/Low) | `"ticks"` | `"subbars"`
- `fill_model` *(string, optional)* – `"next_open"` | `"close"` | `"trigger_price"`
- `intrabar_priority` *(string[], optional)* – Reihenfolge, z. B. `["stop_loss","take_profit"]`
- `lookahead_guard` *(boolean, optional, default true)* – harte Prüfung in Backtest

### data_requirements
- `warmup_bars` *(int, optional, default 0)*
- `indicator_timeframes` *(string[], optional)*
- `missing_data_policy` *(string, optional, default "skip")* – `"skip"|"carry_forward"|"fail"`

### indicators (Registry + Plugin-fähig + DAG)
Listenelement `indicator`:
- `id` *(string, required)* – Referenzname innerhalb StrategySpec
- `type` *(string, required)* – z. B. `"RSI"`, `"SMA"`, `"MACD"`, **oder Plugin-Typ**
- `provider` *(string, optional, default "builtin")* – `"builtin"` | `"plugin"`
- `plugin` *(object, required wenn provider="plugin")*
  - `package` *(string, required)* – z. B. `"orderpilot_indicators"`
  - `entrypoint` *(string, required)* – z. B. `"my_pkg.rsi:RSIIndicator"`
  - `version` *(string, optional)* – SemVer
- `params` *(object, optional)* – Indikatorparameter
- `inputs` *(string[], optional, default ["close"])* – `"open"|"high"|"low"|"close"|"volume"|<indicator_id>|<indicator_id>.<output>`
- `outputs` *(string[], optional)* – falls Multi-Output (z. B. MACD: `"macd","signal","hist"`)
- `timeframe` *(string, optional, default market.timeframe)*
- **Constraint:** DAG ohne Zyklen (Validator: `cyclic_indicator_graph`).

### conditions – sichere DSL als strukturierte Objekte
Bedingungstypen sind **whitelist**-validierbar:
- Vergleich: `> >= < <= == !=`
- Cross: `crosses_above`, `crosses_below`
- Window: `highest`, `lowest`, `sma`, `ema` (als Funktionen)
- State: `increasing`, `decreasing`, `slope_gt`, `slope_lt`
- Kombinatorik: `all`, `any` (verschachtelt), `not`

Condition-Objekt (Basis):
- `op` *(string, required)* – Operator oder Funktion
- `args` *(array, required)* – Argumente: Literale, Series-Refs, Sub-Expressions
- `id` *(string, optional)* – für Debug/Tracing
- `comment` *(string, optional)*

Series-Ref:
- als string, z. B. `"close"`, `"rsi14"`, `"macd.hist"`

Beispiele:
- RSI < 30: `{ "op": "<", "args": ["rsi14", 30] }`
- Cross: `{ "op": "crosses_above", "args": ["close", "ma50"] }`
- Rising momentum: `{ "op": "increasing", "args": ["macd.hist", 3] }`

### entry
- `direction` *(string, required)* – `"long"|"short"|"both"`
- `filters` *(condition[], optional)* – harte Filter (AND)
- `signals` *(object, required)*
  - `mode` *(string, required)* – `"all"` | `"scoring"`
  - `conditions` *(array, required)*
    - bei mode="all": condition[]
    - bei mode="scoring": `{ condition: <cond>, weight: number }[]`
  - `min_score` *(number, optional)* – nur bei scoring
- `cooldown` *(object, optional)*
  - `after_exit_bars` *(int, default 0)*
- `max_entries_per_day` *(int, optional)* – Fokus 5m/daytrading

### exit
- `stop_loss` *(object, optional)*
  - `type` *(string, required)* – `"percent"|"atr"|"price"`
  - `value` *(number, required)*
- `take_profit` *(object, optional)*
  - `type` *(string, required)* – `"percent"|"atr"|"price"`
  - `value` *(number, required)*
- `trailing` *(object, optional)* – nur aktiv, wenn eingeschaltet
  - `type` *(string, required)* – `"percent"|"atr"`
  - `value` *(number, required)* – distance oder multiplier
  - `activate_when` *(object, optional)* – wenn du es **im Core** aktivieren willst
    - `profit_pct_gte` *(number, optional)*
- `breakeven` *(object, optional)*
  - `profit_pct_gte` *(number, required)*
- `partial_exits` *(array, optional)*
  - `{ "profit_pct_gte": number, "portion": number }`
- `exit_conditions` *(condition[], optional)* – Indikator-/Signal-Exits

**Constraint:** `execution.stop_loss_policy == "single_active_stop"` und Exit-Konfiguration darf nicht zu „mehrfachen parallelen Stops“ führen (Validator: `multiple_active_stops`).

### risk
- `risk_per_trade` *(number, required)* – Anteil vom Equity, z. B. `0.01`
- `position_sizing` *(object, required)*
  - `type` *(string, required)* – `"fixed_contracts"|"fixed_notional"|"risk_percent"`
  - `value` *(number, required)*
- `max_positions` *(int, required, default 1)*
- `max_leverage` *(number, optional)* – Safety
- `daily_loss_limit_pct` *(number, optional)* – Circuit breaker
- `cooldown_after_loss_bars` *(int, optional)*

### execution
- `mode` *(string, required)* – `"paper"|"live"`
- `order_preference` *(object, required)*
  - `entry` *(string, required)* – `"market"|"limit"`
  - `exit` *(string, required)* – `"market"|"limit"`
  - `time_in_force` *(string, optional)* – `"GTC"|"IOC"|"FOK"`
- `retry_policy` *(object, optional)*
  - `max_retries` *(int, default 2)*
  - `backoff_ms` *(int, default 250)*
- `safety` *(object, required)*
  - `stop_loss_policy` *(string, required, const "single_active_stop")*
  - `max_slippage_bps` *(int, optional)*
  - `max_spread_bps` *(int, optional)*
  - `circuit_breaker` *(object, optional)*
    - `halt_on_disconnect` *(bool, default true)*
    - `halt_on_order_rejects` *(int, default 3)*
- `idempotency` *(object, required)*
  - `client_order_id_mode` *(string, default "order_intent_id")*
  - `dedupe_window_ms` *(int, default 30000)*

### costs
- `fee_profile_id` *(string, required wenn costs gesetzt)* – Referenz auf vorhandenes Gebührenmodell
- `slippage_profile_id` *(string, optional)*
- `overrides` *(object, optional)* – z. B. `{ "taker_fee_bps": 4 }`

### optimization
- `enabled` *(bool, default false)*
- `engine` *(string, optional)* – `"optuna"`
- `search_space` *(object, optional)* – Parameter-Ranges
- `objective` *(object, optional)* – Ziel(e)
- `constraints` *(object, optional)* – z. B. max DD, min trades
- `regime_aware` *(object, optional)* – Tuning per Regime

### regime
- `tags` *(string[], optional)* – z. B. `["range","trend_up"]`
- `volatility_levels` *(string[], optional)* – `["low","normal","high"]`
- `annotation` *(object, optional)* – Output eines Regime-Detectors, ohne Logik zu ändern

### security
- `allowed_plugins` *(string[], optional)* – Whitelist für Plugin-Packages
- `blocked_fields` *(string[], optional)* – um riskante Felder zu sperren
- `require_signature` *(bool, default false)*

---

## 3) ExecutionWorkflow Datenmodell (WorkflowSpec v1.0)

Top-Level:
- `meta` *(required)*: schema_version, id, strategy_id, name
- `policies` *(required)*: stop_loss_policy
- `rules` *(required)*: Liste von Event-Regeln

### meta
- `schema_version` *(string, required)* – `"1.0"`
- `id` *(string, required)*
- `name` *(string, required)*
- `strategy_id` *(string, required)*
- `created_at` *(date-time, optional)*
- `author` *(string, optional)*

### policies
- `stop_loss_policy` *(string, required, const "single_active_stop")*

### rules[]
- `id` *(string, required)*
- `event` *(string, required)* – Whitelist:
  - `on_bar_close`
  - `on_entry_filled`
  - `on_profit_threshold`
  - `on_indicator_state_change`
  - `on_disconnect`
  - `on_reconnect`
  - `on_order_update`
- `when` *(condition, optional)* – zusätzliche Bedingung (DSL, wie StrategySpec)
- `cooldown_ms` *(int, optional)* – um Flapping zu verhindern
- `once_per_position` *(bool, optional, default false)*
- `priority` *(int, optional, default 100)* – kleiner = früher
- `actions` *(array, required)* – Aktionen (idempotent)

### actions[] (Whitelist)
- `place_order`
- `close_position`
- `replace_stop_loss` (**Ablöse**)
- `set_take_profit`
- `enable_trailing_stop` (**Ablöse**)
- `scale_out`
- `emit_log`
- `set_state` / `clear_state` (optional für State Machine Lite)

Action-Objekt:
- `type` *(string, required)*
- `params` *(object, required)*
- `idempotency_key` *(string, optional)* – wenn gesetzt, muss Bot deduplizieren

**Konfliktregel:** Jede Action, die Stop setzt, muss Replace sein. Mehrere Stop-Actions in derselben Tick/Bar werden nach `priority` abgearbeitet, aber es darf am Ende **nur ein Stop** aktiv sein.

---

## 4) JSON Schemas (Draft 2020-12)

> Hinweis: JSON Schema validiert Struktur/Typen. Logische Constraints (DAG-Zyklen, unsafe DSL, multiple stops) kommen zusätzlich als Validator-Pass im Code.

### 4.1 StrategySpec Schema (kompakt)
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://orderpilot-ai/schemas/strategy-spec-1.0.json",
  "type": "object",
  "additionalProperties": false,
  "required": ["meta", "market", "determinism", "indicators", "entry", "exit", "risk", "execution"],
  "properties": {
    "meta": {
      "type": "object",
      "additionalProperties": false,
      "required": ["schema_version", "id", "name"],
      "properties": {
        "schema_version": { "type": "string", "const": "1.0" },
        "id": { "type": "string", "minLength": 1 },
        "name": { "type": "string", "minLength": 1 },
        "tags": { "type": "array", "items": { "type": "string" } },
        "created_at": { "type": "string", "format": "date-time" },
        "author": { "type": "string" },
        "compat": { "type": "object" },
        "signature": { "type": "object" }
      }
    },
    "market": {
      "type": "object",
      "additionalProperties": false,
      "required": ["exchange", "symbol", "product", "margin_mode", "timeframe"],
      "properties": {
        "exchange": { "type": "string" },
        "symbol": { "type": "string" },
        "product": { "type": "string", "enum": ["futures"] },
        "margin_mode": { "type": "string", "const": "isolated" },
        "leverage": { "type": "number", "minimum": 1 },
        "timeframe": { "type": "string", "pattern": "^[0-9]+(m|h|d)$" },
        "timezone": { "type": "string", "default": "UTC" },
        "candle_alignment": { "type": "string", "enum": ["exchange", "utc"], "default": "exchange" }
      }
    },
    "determinism": {
      "type": "object",
      "additionalProperties": false,
      "required": ["profile"],
      "properties": {
        "profile": { "type": "string", "enum": ["strict_candle_close", "hybrid_intrabar"] },
        "intrabar_source": { "type": "string", "enum": ["hl", "ticks", "subbars"] },
        "fill_model": { "type": "string", "enum": ["next_open", "close", "trigger_price"] },
        "intrabar_priority": { "type": "array", "items": { "type": "string" } },
        "lookahead_guard": { "type": "boolean", "default": true }
      }
    },
    "data_requirements": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "warmup_bars": { "type": "integer", "minimum": 0, "default": 0 },
        "indicator_timeframes": { "type": "array", "items": { "type": "string" } },
        "missing_data_policy": { "type": "string", "enum": ["skip", "carry_forward", "fail"], "default": "skip" }
      }
    },
    "indicators": {
      "type": "array",
      "minItems": 1,
      "items": { "$ref": "#/$defs/indicator" }
    },
    "entry": {
      "type": "object",
      "additionalProperties": false,
      "required": ["direction", "signals"],
      "properties": {
        "direction": { "type": "string", "enum": ["long", "short", "both"] },
        "filters": { "type": "array", "items": { "$ref": "#/$defs/expr" } },
        "signals": {
          "type": "object",
          "additionalProperties": false,
          "required": ["mode", "conditions"],
          "properties": {
            "mode": { "type": "string", "enum": ["all", "scoring"] },
            "conditions": { "type": "array" },
            "min_score": { "type": "number" }
          }
        },
        "cooldown": {
          "type": "object",
          "additionalProperties": false,
          "properties": { "after_exit_bars": { "type": "integer", "minimum": 0, "default": 0 } }
        },
        "max_entries_per_day": { "type": "integer", "minimum": 1 }
      }
    },
    "exit": {
      "type": "object",
      "additionalProperties": false,
      "required": [],
      "properties": {
        "stop_loss": { "$ref": "#/$defs/price_rule" },
        "take_profit": { "$ref": "#/$defs/price_rule" },
        "trailing": {
          "type": "object",
          "additionalProperties": false,
          "required": ["type", "value"],
          "properties": {
            "type": { "type": "string", "enum": ["percent", "atr"] },
            "value": { "type": "number", "exclusiveMinimum": 0 },
            "activate_when": {
              "type": "object",
              "additionalProperties": false,
              "properties": { "profit_pct_gte": { "type": "number" } }
            }
          }
        },
        "breakeven": {
          "type": "object",
          "additionalProperties": false,
          "required": ["profit_pct_gte"],
          "properties": { "profit_pct_gte": { "type": "number", "exclusiveMinimum": 0 } }
        },
        "partial_exits": {
          "type": "array",
          "items": {
            "type": "object",
            "additionalProperties": false,
            "required": ["profit_pct_gte", "portion"],
            "properties": {
              "profit_pct_gte": { "type": "number" },
              "portion": { "type": "number", "exclusiveMinimum": 0, "maximum": 1 }
            }
          }
        },
        "exit_conditions": { "type": "array", "items": { "$ref": "#/$defs/expr" } }
      }
    },
    "risk": {
      "type": "object",
      "additionalProperties": false,
      "required": ["risk_per_trade", "position_sizing", "max_positions"],
      "properties": {
        "risk_per_trade": { "type": "number", "exclusiveMinimum": 0, "maximum": 1 },
        "position_sizing": {
          "type": "object",
          "additionalProperties": false,
          "required": ["type", "value"],
          "properties": {
            "type": { "type": "string", "enum": ["fixed_contracts", "fixed_notional", "risk_percent"] },
            "value": { "type": "number", "exclusiveMinimum": 0 }
          }
        },
        "max_positions": { "type": "integer", "minimum": 1, "default": 1 },
        "max_leverage": { "type": "number", "minimum": 1 },
        "daily_loss_limit_pct": { "type": "number", "minimum": 0, "maximum": 1 },
        "cooldown_after_loss_bars": { "type": "integer", "minimum": 0 }
      }
    },
    "execution": {
      "type": "object",
      "additionalProperties": false,
      "required": ["mode", "order_preference", "safety", "idempotency"],
      "properties": {
        "mode": { "type": "string", "enum": ["paper", "live"] },
        "order_preference": {
          "type": "object",
          "additionalProperties": false,
          "required": ["entry", "exit"],
          "properties": {
            "entry": { "type": "string", "enum": ["market", "limit"] },
            "exit": { "type": "string", "enum": ["market", "limit"] },
            "time_in_force": { "type": "string", "enum": ["GTC", "IOC", "FOK"] }
          }
        },
        "retry_policy": {
          "type": "object",
          "additionalProperties": false,
          "properties": {
            "max_retries": { "type": "integer", "minimum": 0, "default": 2 },
            "backoff_ms": { "type": "integer", "minimum": 0, "default": 250 }
          }
        },
        "safety": {
          "type": "object",
          "additionalProperties": false,
          "required": ["stop_loss_policy"],
          "properties": {
            "stop_loss_policy": { "type": "string", "const": "single_active_stop" },
            "max_slippage_bps": { "type": "integer", "minimum": 0 },
            "max_spread_bps": { "type": "integer", "minimum": 0 },
            "circuit_breaker": { "type": "object", "additionalProperties": false }
          }
        },
        "idempotency": {
          "type": "object",
          "additionalProperties": false,
          "properties": {
            "client_order_id_mode": { "type": "string", "default": "order_intent_id" },
            "dedupe_window_ms": { "type": "integer", "minimum": 0, "default": 30000 }
          }
        }
      }
    },
    "costs": {
      "type": "object",
      "additionalProperties": false,
      "required": ["fee_profile_id"],
      "properties": {
        "fee_profile_id": { "type": "string" },
        "slippage_profile_id": { "type": "string" },
        "overrides": { "type": "object" }
      }
    },
    "optimization": { "type": "object" },
    "regime": { "type": "object" },
    "security": { "type": "object" }
  },
  "$defs": {
    "indicator": {
      "type": "object",
      "additionalProperties": false,
      "required": ["id", "type"],
      "properties": {
        "id": { "type": "string", "minLength": 1 },
        "type": { "type": "string", "minLength": 1 },
        "provider": { "type": "string", "enum": ["builtin", "plugin"], "default": "builtin" },
        "plugin": {
          "type": "object",
          "additionalProperties": false,
          "properties": {
            "package": { "type": "string" },
            "entrypoint": { "type": "string" },
            "version": { "type": "string" }
          },
          "required": ["package", "entrypoint"]
        },
        "params": { "type": "object" },
        "inputs": { "type": "array", "items": { "type": "string" } },
        "outputs": { "type": "array", "items": { "type": "string" } },
        "timeframe": { "type": "string" }
      },
      "allOf": [
        {
          "if": { "properties": { "provider": { "const": "plugin" } } },
          "then": { "required": ["plugin"] }
        }
      ]
    },
    "expr": {
      "type": "object",
      "additionalProperties": false,
      "required": ["op", "args"],
      "properties": {
        "op": { "type": "string" },
        "args": { "type": "array" },
        "id": { "type": "string" },
        "comment": { "type": "string" }
      }
    },
    "price_rule": {
      "type": "object",
      "additionalProperties": false,
      "required": ["type", "value"],
      "properties": {
        "type": { "type": "string", "enum": ["percent", "atr", "price"] },
        "value": { "type": "number" }
      }
    }
  }
}
```

### 4.2 WorkflowSpec Schema (kompakt)
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://orderpilot-ai/schemas/workflow-spec-1.0.json",
  "type": "object",
  "additionalProperties": false,
  "required": ["meta", "policies", "rules"],
  "properties": {
    "meta": {
      "type": "object",
      "additionalProperties": false,
      "required": ["schema_version", "id", "name", "strategy_id"],
      "properties": {
        "schema_version": { "type": "string", "const": "1.0" },
        "id": { "type": "string" },
        "name": { "type": "string" },
        "strategy_id": { "type": "string" },
        "created_at": { "type": "string", "format": "date-time" },
        "author": { "type": "string" }
      }
    },
    "policies": {
      "type": "object",
      "additionalProperties": false,
      "required": ["stop_loss_policy"],
      "properties": {
        "stop_loss_policy": { "type": "string", "const": "single_active_stop" }
      }
    },
    "rules": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": ["id", "event", "actions"],
        "properties": {
          "id": { "type": "string" },
          "event": {
            "type": "string",
            "enum": [
              "on_bar_close",
              "on_entry_filled",
              "on_profit_threshold",
              "on_indicator_state_change",
              "on_disconnect",
              "on_reconnect",
              "on_order_update"
            ]
          },
          "when": { "$ref": "https://orderpilot-ai/schemas/strategy-spec-1.0.json#/$defs/expr" },
          "cooldown_ms": { "type": "integer", "minimum": 0 },
          "once_per_position": { "type": "boolean", "default": false },
          "priority": { "type": "integer", "default": 100 },
          "actions": {
            "type": "array",
            "minItems": 1,
            "items": {
              "type": "object",
              "additionalProperties": false,
              "required": ["type", "params"],
              "properties": {
                "type": {
                  "type": "string",
                  "enum": [
                    "place_order",
                    "close_position",
                    "replace_stop_loss",
                    "set_take_profit",
                    "enable_trailing_stop",
                    "scale_out",
                    "emit_log",
                    "set_state",
                    "clear_state"
                  ]
                },
                "params": { "type": "object" },
                "idempotency_key": { "type": "string" }
              }
            }
          }
        }
      }
    }
  }
}
```

---

## 5) Beispiele (komplette JSON-Dateien)

### Beispiel 1: RSI + MA Filter, SL/TP (BTCUSDT Futures 5m, strict candle close)
```json
{
  "meta": {
    "schema_version": "1.0",
    "id": "rsi_ma_5m_v1",
    "name": "RSI(14) Oversold + SMA(50) Filter",
    "tags": ["scalping", "mean_reversion", "5m", "btc"],
    "created_at": "2026-01-17T00:00:00Z",
    "author": "Maik"
  },
  "market": {
    "exchange": "bitunix",
    "symbol": "BTCUSDT",
    "product": "futures",
    "margin_mode": "isolated",
    "leverage": 10,
    "timeframe": "5m",
    "timezone": "UTC",
    "candle_alignment": "exchange"
  },
  "determinism": {
    "profile": "strict_candle_close",
    "fill_model": "close",
    "lookahead_guard": true
  },
  "data_requirements": {
    "warmup_bars": 60,
    "missing_data_policy": "skip"
  },
  "indicators": [
    {
      "id": "rsi14",
      "type": "RSI",
      "provider": "builtin",
      "params": { "period": 14 },
      "inputs": ["close"]
    },
    {
      "id": "sma50",
      "type": "SMA",
      "provider": "builtin",
      "params": { "period": 50 },
      "inputs": ["close"]
    }
  ],
  "entry": {
    "direction": "long",
    "filters": [
      { "op": ">", "args": ["close", "sma50"], "id": "trend_filter" }
    ],
    "signals": {
      "mode": "all",
      "conditions": [
        { "op": "<", "args": ["rsi14", 30], "id": "rsi_oversold" }
      ]
    },
    "cooldown": { "after_exit_bars": 0 },
    "max_entries_per_day": 100
  },
  "exit": {
    "stop_loss": { "type": "percent", "value": 0.12 },
    "take_profit": { "type": "percent", "value": 0.25 }
  },
  "risk": {
    "risk_per_trade": 0.01,
    "position_sizing": { "type": "risk_percent", "value": 0.01 },
    "max_positions": 1,
    "daily_loss_limit_pct": 0.05
  },
  "execution": {
    "mode": "paper",
    "order_preference": { "entry": "market", "exit": "market", "time_in_force": "IOC" },
    "retry_policy": { "max_retries": 2, "backoff_ms": 250 },
    "safety": {
      "stop_loss_policy": "single_active_stop",
      "max_slippage_bps": 15,
      "max_spread_bps": 20,
      "circuit_breaker": { "halt_on_disconnect": true, "halt_on_order_rejects": 3 }
    },
    "idempotency": { "client_order_id_mode": "order_intent_id", "dedupe_window_ms": 30000 }
  },
  "costs": {
    "fee_profile_id": "bitunix_futures_default",
    "slippage_profile_id": "scalping_5m_default"
  }
}
```

### Beispiel 2: Workflow – nach Entry + Momentum + Profit → Trailing aktivieren (Replace-Stop-Policy)
**StrategySpec (Core):**
```json
{
  "meta": {
    "schema_version": "1.0",
    "id": "mom_trail_5m_v1",
    "name": "Momentum Entry + Workflow Trailing",
    "tags": ["scalping", "momentum", "5m", "btc"],
    "created_at": "2026-01-17T00:00:00Z",
    "author": "Maik"
  },
  "market": {
    "exchange": "bitunix",
    "symbol": "BTCUSDT",
    "product": "futures",
    "margin_mode": "isolated",
    "leverage": 20,
    "timeframe": "5m",
    "timezone": "UTC",
    "candle_alignment": "exchange"
  },
  "determinism": {
    "profile": "strict_candle_close",
    "fill_model": "close",
    "lookahead_guard": true
  },
  "data_requirements": { "warmup_bars": 120, "missing_data_policy": "skip" },
  "indicators": [
    {
      "id": "sma20",
      "type": "SMA",
      "provider": "builtin",
      "params": { "period": 20 },
      "inputs": ["close"]
    },
    {
      "id": "macd",
      "type": "MACD",
      "provider": "builtin",
      "params": { "fast": 12, "slow": 26, "signal": 9 },
      "inputs": ["close"],
      "outputs": ["macd", "signal", "hist"]
    }
  ],
  "entry": {
    "direction": "both",
    "signals": {
      "mode": "scoring",
      "conditions": [
        { "condition": { "op": "crosses_above", "args": ["close", "sma20"], "id": "cross_up" }, "weight": 1.0 },
        { "condition": { "op": "crosses_below", "args": ["close", "sma20"], "id": "cross_dn" }, "weight": 1.0 }
      ],
      "min_score": 1.0
    }
  },
  "exit": {
    "stop_loss": { "type": "percent", "value": 0.12 }
  },
  "risk": {
    "risk_per_trade": 0.01,
    "position_sizing": { "type": "risk_percent", "value": 0.01 },
    "max_positions": 1
  },
  "execution": {
    "mode": "live",
    "order_preference": { "entry": "market", "exit": "market", "time_in_force": "IOC" },
    "safety": { "stop_loss_policy": "single_active_stop", "max_slippage_bps": 20, "max_spread_bps": 30 },
    "idempotency": { "client_order_id_mode": "order_intent_id", "dedupe_window_ms": 30000 }
  },
  "costs": { "fee_profile_id": "bitunix_futures_default" },
  "regime": { "tags": ["trend_up", "trend_down"] }
}
```

**WorkflowSpec (Automation Layer):**
```json
{
  "meta": {
    "schema_version": "1.0",
    "id": "mom_trail_5m_wf_v1",
    "name": "Enable trailing when profit>=0.25% and MACD hist increasing",
    "strategy_id": "mom_trail_5m_v1",
    "created_at": "2026-01-17T00:00:00Z",
    "author": "Maik"
  },
  "policies": {
    "stop_loss_policy": "single_active_stop"
  },
  "rules": [
    {
      "id": "enable_trailing_after_profit",
      "event": "on_bar_close",
      "priority": 10,
      "once_per_position": true,
      "when": {
        "op": "all",
        "args": [
          { "op": ">=", "args": ["position_profit_pct", 0.25] },
          { "op": "increasing", "args": ["macd.hist", 3] }
        ]
      },
      "actions": [
        {
          "type": "enable_trailing_stop",
          "idempotency_key": "trail_enable_once",
          "params": { "type": "percent", "value": 0.10 }
        },
        {
          "type": "emit_log",
          "params": { "level": "info", "message": "Trailing aktiviert (Replace SL)" }
        }
      ]
    },
    {
      "id": "trail_update_each_close",
      "event": "on_bar_close",
      "priority": 50,
      "when": { "op": "==", "args": ["state.trailing_active", true] },
      "actions": [
        {
          "type": "replace_stop_loss",
          "params": { "mode": "trailing_engine_update" }
        }
      ]
    }
  ]
}
```

> In diesem Workflow wird der Stop stets via Replace verwaltet. Der Bot führt Trailing als internen Zustand und setzt/ersetzt den einzigen Stop entsprechend.

---

## 6) Migrations-Notiz (alt → neu)

Dein altes Format (Beispiel `strategies.json`) ist „regelzentriert“ (entry_rules/exit_rules, weights, thresholds). Mapping:

1. **meta**
   - alt `name` → neu `meta.name`
   - alt `description` → neu `meta.tags` oder optional `meta.description` (wenn du es ergänzen willst)
   - alt `strategy_type`, `regimes`, `volatility_levels` → neu `meta.tags` und/oder `regime.tags`/`regime.volatility_levels`

2. **Entry Scoring**
   - alt `entry_rules[]` → neu `entry.signals.mode="scoring"` und `conditions[]` mit `{condition, weight}`
   - alt `entry_threshold` / `min_entry_score` → neu `entry.signals.min_score`

3. **Exit**
   - alt `stop_loss_pct` → neu `exit.stop_loss: {type:"percent", value:<...>}`
   - alt `exit_rules`:
     - `rule_type="profit"` → neu `exit.take_profit`
     - `rule_type="trailing"` → neu `exit.trailing` oder Workflow-Aktion `enable_trailing_stop`
     - `rule_type="indicator"` → neu `exit.exit_conditions` oder Workflow `on_indicator_state_change`

4. **Indikatoren**
   - alt `indicator` Strings → neu `indicators[]` mit `id` + `type` (+ params).
   - Falls du heute Indikatoren nur per Namen nutzt (z. B. `"rsi_14"`), dann:
     - `id="rsi14"`, `type="RSI"`, `params:{period:14}`.
   - Custom/Composite: `provider="plugin"` + `plugin.entrypoint`.

5. **Costs**
   - alt (implizit im Code) → neu `costs.fee_profile_id` / `slippage_profile_id` als Referenz.

6. **Validierung**
   - Schema-Validierung + Zusatzchecks: `unknown_indicator_id`, `cyclic_indicator_graph`, `unsafe_expression`, `multiple_active_stops`, `invalid_margin_mode`.

---

## Fehlercodes (Empfehlung)
- `invalid_schema`
- `invalid_margin_mode`
- `invalid_timeframe`
- `unknown_indicator_id`
- `cyclic_indicator_graph`
- `unsafe_expression`
- `multiple_active_stops`
- `invalid_cost_profile`
- `invalid_action_params`
- `strategy_mismatch`
- `idempotency_violation`
