# H3 – KI in Strategie, Alarme & Backtests

> **Projekt:** Automatisierte Trading-Anwendung (Windows 11, Python)
> **Stand:** 2025-10-30 13:07
> **Leitplanken:** Broker **Trade Republic (inoffiziell, privat)** + **IBKR** (offiziell); Live-Daten via Broker-Streams; **1‑Sekunden**-Zeitraster; **Limit/Stop(-Limit)**; **manuelle Freigabe default**; DSGVO; **OpenAI‑Integration** (Responses API mit Structured Outputs; optional Assistants/Realtime).

## Ziele
- Assistive Analysen; User behält Kontrolle

## Deliverables
- Hooks: post_signal_analysis; alert_explain_and_rank; summarize_backtest

## Abhängigkeiten
- H2
- C2
- E4
- E5
- D1

## Checkliste
- [ ] **01. Strategy‑Hook implementieren (C2)**
- [ ] **02. Order‑Dialog Panel (E4) anbinden**
- [ ] **03. Alarm‑Triage (E5) anbinden**
- [ ] **04. Backtest‑Review (D1) anbinden**

## Abnahme-Kriterien
- [ ] Hooks funktionieren in allen Pfaden; abschaltbar
