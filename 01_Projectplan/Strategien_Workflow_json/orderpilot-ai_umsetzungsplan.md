# OrderPilot-AI – Umsetzungsplan (Checkliste & Tracking)

> Vorlage/Struktur basiert auf deiner bereitgestellten Checkliste. fileciteturn1file0  
> Ziel: OrderPilot-AI als robuste, deterministische Trading-Software (Entry Designer + Trading Bot) mit StrategySpec/Workflow, Exchange-Integration (Bitunix Futures), Virtual Orders, Idempotency, Strategy Library und Regime Interface.

**Start:** 2026-01-17  
**Gesamtfortschritt:** 0%

---

## 🛠️ CODE-QUALITÄTS-STANDARDS (vor jedem Task lesen!)

### ✅ ERFORDERLICH für jeden Task:
1. Vollständige Implementation (keine TODOs/Platzhalter)
2. Error Handling für alle kritischen Pfade (Netzwerk/Exchange/Parsing/IO)
3. Input Validation (JSON, Konfig, API-Responses)
4. Type Hints vollständig
5. Docstrings für öffentliche APIs
6. Logging mit sinnvollen Log-Leveln + strukturierte Logs (JSON)
7. Tests (Unit + Integration) für neue Features
8. Clean Code (alten Code entfernen, keine Dead Paths)

### ❌ VERBOTEN:
1. Platzhalter-Code (`TODO`, `pass`, Dummy Returns)
2. Silent Failures (`except: pass`)
3. Hardcoded Secrets (API Keys etc.)
4. Nicht-deterministische Backtests (Lookahead, Random ohne Seed)
5. Ungesicherte Order-Duplikate (keine Idempotency Keys)
6. Mehrere aktive Stops gleichzeitig (Policy-Verstoß)
7. UI ohne Funktionslogik (falls UI-Komponenten angefasst werden)

### 🔍 BEFORE MARKING COMPLETE:
- [ ] Feature läuft in Paper und Backtest konsistent
- [ ] Keine TODOs
- [ ] Validator/Guards aktiv
- [ ] Tests grün (CI)
- [ ] Logging/Tracing nachvollziehbar
- [ ] Rate-Limits & Retries geprüft
- [ ] Exchange-Simulation deckt Edge-Cases ab

---

## 📊 Status-Legende
- ⬜ Offen / Nicht begonnen
- 🔄 In Arbeit
- ✅ Abgeschlossen
- ❌ Fehler / Blockiert
- ⭐ Übersprungen / Nicht benötigt

---

## 🛠️ TRACKING-FORMAT (PFLICHT)

### Erfolgreicher Task
```markdown
- [ ] **1.2.3 Task Name**
  Status: ✅ Abgeschlossen (YYYY-MM-DD HH:MM) → *Was wurde implementiert*
  Code: `pfad/datei.py:zeilen`
  Tests: `tests/test_x.py:TestClass`
  Nachweis: Screenshot/Log-Ausgabe/Backtest-Report
```

### Fehlgeschlagener Task
```markdown
- [ ] **1.2.3 Task Name**
  Status: ❌ Fehler (YYYY-MM-DD HH:MM) → *Fehlerbeschreibung*
  Fehler: `Exakte Error Message`
  Ursache: ...
  Lösung: ...
  Retry: Geplant für YYYY-MM-DD HH:MM
```

---

# Phase 0: Vorbereitung & Setup (Woche 1)

- [ ] **0.1 Repo & Branch-Strategie**
  Status: ⬜ → main/dev + feature branches, PR-Checks
- [ ] **0.2 Python Tooling**
  Status: ⬜ → pyproject.toml, ruff, mypy, pytest, pre-commit
- [ ] **0.3 Projektstruktur**
  Status: ⬜ → Module: `entry_designer/`, `trading_bot/`, `shared/`
- [ ] **0.4 Konfig & Secrets**
  Status: ⬜ → `.env.example`, config loader, keine Secrets im Repo
- [ ] **0.5 CI Pipeline**
  Status: ⬜ → Unit + Integration Tests, Lint, Typecheck
- [ ] **0.6 Logging/Observability Baseline**
  Status: ⬜ → strukturierte Logs, Correlation IDs, log rotation

---

# Phase 1: Shared-Core Foundation (Woche 1–2)

## 1.1 Shared Domain Model
- [ ] **1.1.1 Canonical Types**
  Status: ⬜ → Candle, Trade, Position, Order, Fill, Fees, Slippage
- [ ] **1.1.2 Money/Precision Layer**
  Status: ⬜ → Decimal/quantize, symbol-specific precision
- [ ] **1.1.3 Timeframe Utilities**
  Status: ⬜ → Parse/format (`5m`), alignment, timezone

## 1.2 StrategySpec & WorkflowSpec (JSON)
- [ ] **1.2.1 JSON Schema Draft 2020-12 – Strategy**
  Status: ⬜ → schema file + validator wrapper
- [ ] **1.2.2 JSON Schema Draft 2020-12 – Workflow**
  Status: ⬜ → schema file + validator wrapper
- [ ] **1.2.3 Zusatz-Validatoren (Business Rules)**
  Status: ⬜ → DAG check, unsafe DSL, margin isolated, single stop
- [ ] **1.2.4 Fehlercodes & Diagnostics**
  Status: ⬜ → standardisierte Codes, user-friendly messages
- [ ] **1.2.5 Migration Framework**
  Status: ⬜ → `schema_version` routing + migrations (v0→v1)

## 1.3 Condition DSL Engine (Whitelist)
- [ ] **1.3.1 Parser + AST**
  Status: ⬜ → supports `op/args`, nested all/any/not
- [ ] **1.3.2 Evaluator (Bar-close)**
  Status: ⬜ → deterministic, no future reads
- [ ] **1.3.3 Safety Guard**
  Status: ⬜ → denylist unknown ops, limit recursion depth
- [ ] **1.3.4 DSL Test Suite**
  Status: ⬜ → cross/slope/window cases

---

# Phase 2: Indicators Engine (Woche 2–3)

## 2.1 Indicator Registry (Builtin)
- [ ] **2.1.1 Builtin Indicators MVP**
  Status: ⬜ → RSI, SMA, EMA, MACD, ATR, BB, ADX
- [ ] **2.1.2 Multi-Output Indicators**
  Status: ⬜ → MACD outputs `macd/signal/hist`
- [ ] **2.1.3 Warmup Handling**
  Status: ⬜ → warmup bars from spec, missing data policy

## 2.2 Plugin Indicators
- [ ] **2.2.1 Plugin Loader**
  Status: ⬜ → import by entrypoint, version checks
- [ ] **2.2.2 Plugin Sandbox Policy**
  Status: ⬜ → allowed_packages, signature optional
- [ ] **2.2.3 Plugin Contract Tests**
  Status: ⬜ → compatibility: inputs/outputs/params

## 2.3 DAG Execution
- [ ] **2.3.1 Build DAG from indicators[]**
  Status: ⬜ → topological sort, cycle detection
- [ ] **2.3.2 Compute Graph per Bar**
  Status: ⬜ → caching, incremental update
- [ ] **2.3.3 Performance Benchmarks**
  Status: ⬜ → 5m BTC multi-year, target < X ms/bar

---

# Phase 3: Backtesting & Optimizer (Entry Designer) (Woche 3–5)

## 3.1 Backtest Engine Core
- [ ] **3.1.1 Determinism Profiles**
  Status: ⬜ → strict_candle_close, hybrid_intrabar (HL)
- [ ] **3.1.2 Fill Model**
  Status: ⬜ → close/next_open/trigger_price
- [ ] **3.1.3 Fees/Slippage Integration**
  Status: ⬜ → costs profile resolver + overrides
- [ ] **3.1.4 Risk & Position Sizing**
  Status: ⬜ → fixed_notional, fixed_contracts, risk_percent
- [ ] **3.1.5 PnL Accounting**
  Status: ⬜ → realized/unrealized, funding placeholder optional

## 3.2 Virtual Orders Simulation
- [ ] **3.2.1 Single Active Stop Simulation**
  Status: ⬜ → replace semantics, trailing, breakeven
- [ ] **3.2.2 TP/SL Priority Rules (hybrid)**
  Status: ⬜ → deterministic ordering
- [ ] **3.2.3 Partial Exits Simulation**
  Status: ⬜ → scale_out portions + remaining sizing

## 3.3 Optimizer Integration
- [ ] **3.3.1 Search Space Binding**
  Status: ⬜ → map spec params to optimizer knobs
- [ ] **3.3.2 Objective & Constraints**
  Status: ⬜ → sharpe, net, dd, min trades
- [ ] **3.3.3 Regime-Aware Tuning**
  Status: ⬜ → split dataset by regime tags

## 3.4 Backtest Reporting
- [ ] **3.4.1 Metrics Pack**
  Status: ⬜ → winrate, PF, DD, trade stats, exposure
- [ ] **3.4.2 Reproducibility Report**
  Status: ⬜ → config hash, data hash, spec hash
- [ ] **3.4.3 Export Format**
  Status: ⬜ → JSON report + optional HTML

---

# Phase 4: Live/Paper Trading Bot (Woche 5–7)

## 4.1 Bot Runtime Core
- [ ] **4.1.1 Event Loop (Bar Close Driven)**
  Status: ⬜ → scheduler for timeframe alignment
- [ ] **4.1.2 State Store**
  Status: ⬜ → persisted positions, stops, workflow state
- [ ] **4.1.3 Strategy Loader**
  Status: ⬜ → read spec, validate, prepare DAG+DSL

## 4.2 Exchange Integration – Bitunix Futures
- [ ] **4.2.1 REST Client**
  Status: ⬜ → auth, time sync, retries, rate-limit
- [ ] **4.2.2 WebSocket Client**
  Status: ⬜ → order updates, fills, positions
- [ ] **4.2.3 Normalized OMS Adapter**
  Status: ⬜ → place/cancel/replace, client order ids
- [ ] **4.2.4 Isolated Margin Enforcement**
  Status: ⬜ → preflight checks, reject if not isolated
- [ ] **4.2.5 Leverage Policy**
  Status: ⬜ → set leverage safely, verify post-set

## 4.3 Idempotency & Partial Fills
- [ ] **4.3.1 order_intent_id Generation**
  Status: ⬜ → stable per action, dedupe window
- [ ] **4.3.2 Partial Fill Handler**
  Status: ⬜ → update remaining qty, adjust stops
- [ ] **4.3.3 Exactly-Once Effects (App-level)**
  Status: ⬜ → event de-dupe + persistent checkpoints

---

# Phase 5: Virtual Orders (Live) & Safety (Woche 7–8)

## 5.1 Virtual Stop/TP/Trailing Engine
- [ ] **5.1.1 Stop Engine State Model**
  Status: ⬜ → exactly 1 active stop
- [ ] **5.1.2 Trigger Detection**
  Status: ⬜ → bar-close + optional intrabar (HL/ticks)
- [ ] **5.1.3 Execution Locks**
  Status: ⬜ → prevent double exit orders
- [ ] **5.1.4 Fail-safe Native Stop (optional)**
  Status: ⬜ → disconnect fallback if supported

## 5.2 Disconnect/Reconnect Recovery
- [ ] **5.2.1 Reconciliation Routine**
  Status: ⬜ → reconcile open orders/positions
- [ ] **5.2.2 Emergency Exit Policy**
  Status: ⬜ → if state inconsistent, flatten safely
- [ ] **5.2.3 Audit Trail**
  Status: ⬜ → append-only ledger of intents & outcomes

---

# Phase 6: ExecutionWorkflow Engine (Woche 8–9)

- [ ] **6.1 WorkflowSpec Validator**
  Status: ⬜ → schema + business validation
- [ ] **6.2 Event Bus**
  Status: ⬜ → on_bar_close, on_entry_filled, on_profit_threshold
- [ ] **6.3 Rule Evaluator**
  Status: ⬜ → priority ordering, cooldown, once_per_position
- [ ] **6.4 Actions Implementation**
  Status: ⬜ → replace_stop_loss, enable_trailing_stop, scale_out
- [ ] **6.5 Idempotency in Workflow**
  Status: ⬜ → idempotency_key support + dedupe
- [ ] **6.6 Workflow Tests**
  Status: ⬜ → deterministic replay of event sequences

---

# Phase 7: Strategy Library & Regime Interface (Woche 9–10)

## 7.1 Strategy Library
- [ ] **7.1.1 Library Index**
  Status: ⬜ → list, search, tags, versions
- [ ] **7.1.2 Sign/Verify (optional)**
  Status: ⬜ → sha256 + optional ed25519
- [ ] **7.1.3 Compatibility Gate**
  Status: ⬜ → compat check per bot version
- [ ] **7.1.4 Hot-Swap Policy**
  Status: ⬜ → swap only flat / controlled transition

## 7.2 Regime Detection Interface
- [ ] **7.2.1 Regime Event Contract**
  Status: ⬜ → state update input to bot
- [ ] **7.2.2 Optimizer Regime Annotation**
  Status: ⬜ → store regime label + confidence
- [ ] **7.2.3 Strategy Selection Logic**
  Status: ⬜ → mapping regime → strategy candidate set

---

# Phase 8: Production Hardening (Woche 10–12)

- [ ] **8.1 Security**
  Status: ⬜ → config validation, secret handling, plugin allowlist
- [ ] **8.2 Performance**
  Status: ⬜ → load tests, latency budgets, memory budgets
- [ ] **8.3 Monitoring**
  Status: ⬜ → metrics (orders, fills, rejects, lag), alerts
- [ ] **8.4 Fault Injection**
  Status: ⬜ → simulate disconnects, rejects, partial fills
- [ ] **8.5 Documentation**
  Status: ⬜ → operator guide + troubleshooting
- [ ] **8.6 Release Checklist**
  Status: ⬜ → paper soak test, staged rollout, rollback plan

---

## 🔥 Kritische Pfade
1. Shared-Core (Schemas/Validator/DSL) → Indicator DAG → Backtest determinism
2. OMS/Idempotency → Virtual Orders → Recovery (Disconnect/Reconnect)
3. Workflow Engine → Strategy Library/Hot-swap → Regime Interface

## Risiken & Mitigation
- **Exchange Limits / Semantik-Abweichungen:** Adapter + Virtual Orders + Fail-safe Stops
- **Datenlücken:** missing_data_policy + Reconciliation + Circuit Breaker
- **Overtrading bei 5m:** cooldown + max_entries_per_day + daily loss limit
- **Lookahead-Bias:** strict mode default + lookahead_guard tests

