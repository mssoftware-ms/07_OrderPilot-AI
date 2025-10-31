# H2 – Prompt‑Library & Structured Outputs

> **Projekt:** Automatisierte Trading-Anwendung (Windows 11, Python)
> **Stand:** 2025-10-30 13:07
> **Leitplanken:** Broker **Trade Republic (inoffiziell, privat)** + **IBKR** (offiziell); Live-Daten via Broker-Streams; **1‑Sekunden**-Zeitraster; **Limit/Stop(-Limit)**; **manuelle Freigabe default**; DSGVO; **OpenAI‑Integration** (Responses API mit Structured Outputs; optional Assistants/Realtime).

## Ziele
- Versionierte Prompts; JSON‑Schemas; Templating

## Deliverables
- Ordner: /src/prompts + /src/schemas; pydantic‑Modelle

## Abhängigkeiten
- H1

## Checkliste
- [ ] **01. Prompts: strategy_explain, alert_triage, backtest_review, risk_guard**
- [ ] **02. Schemas: AnalysisResult, AlertDecision, BacktestSummary, RiskCheck**
- [ ] **03. Templating (jinja2); Placeholders; Variable Binding**
- [ ] **04. Regression‑Tests (Fixtures, Seeds)**

## Abnahme-Kriterien
- [ ] Alle KI‑Flows nutzen gültige Schemas; Versionen dokumentiert
