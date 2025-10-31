# A2 – Trade Republic Adapter (inoffiziell)

> **Projekt:** Automatisierte Trading-Anwendung (Windows 11, Python)
> **Stand:** 2025-10-30 13:07
> **Leitplanken:** Broker **Trade Republic (inoffiziell, privat)** + **IBKR** (offiziell); Live-Daten via Broker-Streams; **1‑Sekunden**-Zeitraster; **Limit/Stop(-Limit)**; **manuelle Freigabe default**; DSGVO; **OpenAI‑Integration** (Responses API mit Structured Outputs; optional Assistants/Realtime).

## Ziele
- Schneller Live‑Start über TR; stabile Streams/Orders; defensiv gegen API‑Änderungen

## Deliverables
- Login/Session; Subscribe/Unsubscribe; Order‑Flow; Reconnect/Backoff; Throttling

## Abhängigkeiten
- A1

## Checkliste
- [ ] **01. Credentials sicher hinterlegen (Windows Credential Manager)**
- [ ] **02. WebSocket‑Client: Connect/Heartbeat/Backoff; Schema‑Robustheit**
- [ ] **03. ISIN<->Symbol Mapping; Börsenplatz LSX/gettex konfigurierbar**
- [ ] **04. Order‑Ablauf mit Idempotenz‑Keys (Retry‑sicher)**
- [ ] **05. Fehlerfälle: Auth‑Fail, Device‑Kollision, Payload‑Change → Soft‑Fail + Warnbanner**
- [ ] **06. Throttling Limits durchsetzen**
- [ ] **07. **KI‑Telemetry‑Tags** in Logs (Kosten/Latenz wenn KI‑Hooks genutzt)**
- [ ] **08. Integration‑Tests (Mock‑Server)**

## Abnahme-Kriterien
- [ ] Stabile Streams/Orders; Warn‑Banner für Inoffiziell; KI‑Telemetry im Log
