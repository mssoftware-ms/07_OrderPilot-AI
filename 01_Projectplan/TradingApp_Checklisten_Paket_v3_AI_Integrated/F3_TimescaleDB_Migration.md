# F3 – TimescaleDB (optional)

> **Projekt:** Automatisierte Trading-Anwendung (Windows 11, Python)
> **Stand:** 2025-10-30 13:07
> **Leitplanken:** Broker **Trade Republic (inoffiziell, privat)** + **IBKR** (offiziell); Live-Daten via Broker-Streams; **1‑Sekunden**-Zeitraster; **Limit/Stop(-Limit)**; **manuelle Freigabe default**; DSGVO; **OpenAI‑Integration** (Responses API mit Structured Outputs; optional Assistants/Realtime).

## Ziele
- Skalierung; schnellere Zeitreihen‑Queries; KI‑Telemetry‑Rollups

## Deliverables
- Docker‑Compose; Hypertables; Migration SQLite→Timescale

## Abhängigkeiten
- F1

## Checkliste
- [ ] **01. Setup Compose; Auth/SSL**
- [ ] **02. Migration ETL‑Skript (bars/orders/trades/alerts/**ai_telemetry**)**
- [ ] **03. Hypertables; Retention/Compression Policies**

## Abnahme-Kriterien
- [ ] Query‑Speedup belegt; Rollups für KI‑Kosten
