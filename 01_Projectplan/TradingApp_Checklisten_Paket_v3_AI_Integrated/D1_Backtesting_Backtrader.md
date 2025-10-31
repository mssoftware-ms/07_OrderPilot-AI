# D1 – Backtesting (Backtrader)

> **Projekt:** Automatisierte Trading-Anwendung (Windows 11, Python)
> **Stand:** 2025-10-30 13:07
> **Leitplanken:** Broker **Trade Republic (inoffiziell, privat)** + **IBKR** (offiziell); Live-Daten via Broker-Streams; **1‑Sekunden**-Zeitraster; **Limit/Stop(-Limit)**; **manuelle Freigabe default**; DSGVO; **OpenAI‑Integration** (Responses API mit Structured Outputs; optional Assistants/Realtime).

## Ziele
- Reproduzierbarkeit live/backtest; KPIs; **KI‑Reviewer**

## Deliverables
- Feed‑Adapter; Fees/Slippage; KPIs/Charts; KI‑Zusammenfassung

## Abhängigkeiten
- C2
- F1
- H2
- H3
- H5

## Checkliste
- [ ] **01. Feed: DB/CSV→Backtrader; Parameter‑Binding**
- [ ] **02. Kostenmodelle: TR €1 flat; IBKR min/tiers; Slippage 1‑3 Ticks**
- [ ] **03. KPIs: Sharpe/Sortino/MaxDD/WinRate/Expectancy/R‑Multiple**
- [ ] **04. Charts: Trades/Equity‑Curve; Export CSV/HTML**
- [ ] **05. **KI‑Backtest‑Review**: `summarize_backtest(results)->BacktestSummary` (Schema)**
- [ ] **06. Unit/Integration‑Tests; deterministische Seeds**

## Abnahme-Kriterien
- [ ] KPIs konsistent; KI‑Review erzeugt nutzbare Hinweise; Export funktioniert
