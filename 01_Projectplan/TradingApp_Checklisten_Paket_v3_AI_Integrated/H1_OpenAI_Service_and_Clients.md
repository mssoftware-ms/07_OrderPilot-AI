# H1 – OpenAIService & Clients

> **Projekt:** Automatisierte Trading-Anwendung (Windows 11, Python)
> **Stand:** 2025-10-30 13:07
> **Leitplanken:** Broker **Trade Republic (inoffiziell, privat)** + **IBKR** (offiziell); Live-Daten via Broker-Streams; **1‑Sekunden**-Zeitraster; **Limit/Stop(-Limit)**; **manuelle Freigabe default**; DSGVO; **OpenAI‑Integration** (Responses API mit Structured Outputs; optional Assistants/Realtime).

## Ziele
- Responses API (Structured Outputs); Assistants (optional); Realtime (optional)

## Deliverables
- Klassen: OpenAIService, ResponsesClient, AssistantsClient (optional), RealtimeClient (Stub)

## Abhängigkeiten
- H0

## Checkliste
- [ ] **01. ResponsesClient: Schema‑Pflicht; Streaming optional; Idempotenz‑IDs**
- [ ] **02. AssistantsClient: Tool‑Hook (später)**
- [ ] **03. RealtimeClient Stub (WebSocket)**
- [ ] **04. Timeouts/Retry (exponential backoff); Jitter**
- [ ] **05. Unit‑Tests: 429/5xx/Timeouts; Schema‑Invalid**

## Abnahme-Kriterien
- [ ] Schema‑validierte Outputs; Fehlerpfade stabil
