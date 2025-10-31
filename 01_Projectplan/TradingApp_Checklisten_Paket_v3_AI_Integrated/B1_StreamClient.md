# B1 – Stream‑Client (TR/IBKR)

> **Projekt:** Automatisierte Trading-Anwendung (Windows 11, Python)
> **Stand:** 2025-10-30 13:07
> **Leitplanken:** Broker **Trade Republic (inoffiziell, privat)** + **IBKR** (offiziell); Live-Daten via Broker-Streams; **1‑Sekunden**-Zeitraster; **Limit/Stop(-Limit)**; **manuelle Freigabe default**; DSGVO; **OpenAI‑Integration** (Responses API mit Structured Outputs; optional Assistants/Realtime).

## Ziele
- Live‑Kurse via Broker‑Streams; Latenz/Lag sichtbar; Backpressure

## Deliverables
- WebSocket/Streaming; Watchlist‑Subscriptions; Status‑Metriken

## Checkliste
- [ ] **01. TR Topics/ISIN; IBKR Level1 Stream; dynamische Sub/Unsub via Watchlist**
- [ ] **02. Heartbeat/Backoff/Resubscribe; Drop‑Detection**
- [ ] **03. Lag/Latenz‑Metriken im Dashboard (E1)**
- [ ] **04. Burst‑Handling (Batches) ohne UI‑Blockade**
- [ ] **05. **KI‑Kosten‑Overlay** optional im Dashboard (wenn KI Features aktiv)**
- [ ] **06. Tests mit Fake‑Feeds/Bursts**

## Abnahme-Kriterien
- [ ] 1s‑Updates stabil; Resubscribe funktioniert; Metriken korrekt
