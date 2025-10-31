# F1 – Datenbank (SQLite)

> **Projekt:** Automatisierte Trading-Anwendung (Windows 11, Python)
> **Stand:** 2025-10-30 13:07
> **Leitplanken:** Broker **Trade Republic (inoffiziell, privat)** + **IBKR** (offiziell); Live-Daten via Broker-Streams; **1‑Sekunden**-Zeitraster; **Limit/Stop(-Limit)**; **manuelle Freigabe default**; DSGVO; **OpenAI‑Integration** (Responses API mit Structured Outputs; optional Assistants/Realtime).

## Ziele
- Persistenz für Bars/Orders/Trades/Alerts/Config; **KI‑Cache/Telemetry**

## Deliverables
- Schema + Indizes; Batch‑Writer; PRAGMA‑Tuning; KI‑Tabellen

## Checkliste
- [ ] **01. Schema: bars, orders, trades, alerts, config**
- [ ] **02. **KI‑Tabellen**: ai_cache(key, result, ttl, cost, model); ai_telemetry(ts, feature, tokens, cost, latency)**
- [ ] **03. Batch‑Writer (Queue), WAL, PRAGMA Settings**
- [ ] **04. Migrations‑Stub (Timescale später)**
- [ ] **05. Tests: Integrität/Performance**

## Abnahme-Kriterien
- [ ] Durchsatz stabil; KI‑Cache/Telemetry funktionieren
