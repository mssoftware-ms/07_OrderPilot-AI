# C2 – Strategy Engine (regelbasiert)

> **Projekt:** Automatisierte Trading-Anwendung (Windows 11, Python)
> **Stand:** 2025-10-30 13:07
> **Leitplanken:** Broker **Trade Republic (inoffiziell, privat)** + **IBKR** (offiziell); Live-Daten via Broker-Streams; **1‑Sekunden**-Zeitraster; **Limit/Stop(-Limit)**; **manuelle Freigabe default**; DSGVO; **OpenAI‑Integration** (Responses API mit Structured Outputs; optional Assistants/Realtime).

## Ziele
- Mehrere Strategien; Priorisierung/Ensembling; Sizing %; ATR‑Stops; KI‑Nachanalyse

## Deliverables
- Strategy‑Baseclass; Konfliktauflösung; Cooldowns; KI‑Hooks

## Abhängigkeiten
- C1
- B2
- A4
- H2
- H3

## Checkliste
- [ ] **01. Strategy‑API: on_bar()/generate_signal()**
- [ ] **02. Sizing: % vom Kapital; Caps; Min/Max pro Trade**
- [ ] **03. Stops/TP: Trailing ATR + Mindest‑R**
- [ ] **04. Konfliktlösung deterministisch; Cooldowns**
- [ ] **05. **Post‑Signal KI‑Hook**: `post_signal_analysis(context)->AnalysisResult`**
- [ ] **06. Unit‑Tests: Signalmatrizen; deterministische Seeds für KI‑Mocks**

## Abnahme-Kriterien
- [ ] Live/Backtest gleiche Ergebnisse; KI‑Nachanalyse eingebunden/abschaltbar
