# C3 – ML‑Hook (optional)

> **Projekt:** Automatisierte Trading-Anwendung (Windows 11, Python)
> **Stand:** 2025-10-30 13:07
> **Leitplanken:** Broker **Trade Republic (inoffiziell, privat)** + **IBKR** (offiziell); Live-Daten via Broker-Streams; **1‑Sekunden**-Zeitraster; **Limit/Stop(-Limit)**; **manuelle Freigabe default**; DSGVO; **OpenAI‑Integration** (Responses API mit Structured Outputs; optional Assistants/Realtime).

## Ziele
- Spätere ML‑Modelle zuschaltbar; koexistiert mit Regeln/KI‑Analysen

## Deliverables
- Feature‑Pipeline (aus C1); Model‑Registry (JSON)

## Abhängigkeiten
- C2
- H2

## Checkliste
- [ ] **01. Feature‑Extraktion (Fenster/Lags)**
- [ ] **02. Score‑Threshold; Ensemble mit Regeln**
- [ ] **03. Registry (Version, Pfad, Hyperparams)**
- [ ] **04. Offline‑Evaluierung vs. Backtests**

## Abnahme-Kriterien
- [ ] ML Off by default; sauberes Toggle
