# A3 – IBKR Adapter (offiziell)

> **Projekt:** Automatisierte Trading-Anwendung (Windows 11, Python)
> **Stand:** 2025-10-30 13:07
> **Leitplanken:** Broker **Trade Republic (inoffiziell, privat)** + **IBKR** (offiziell); Live-Daten via Broker-Streams; **1‑Sekunden**-Zeitraster; **Limit/Stop(-Limit)**; **manuelle Freigabe default**; DSGVO; **OpenAI‑Integration** (Responses API mit Structured Outputs; optional Assistants/Realtime).

## Ziele
- TWS/Gateway‑Anbindung; Derivate‑Support; Paper‑Trading

## Deliverables
- Contracts (Stocks/ETFs/Options/Futures); MarketData Stream/Snapshot; Fehlercode‑Mapping

## Abhängigkeiten
- A1

## Checkliste
- [ ] **01. TWS/Gateway Verbindung (ClientId/Ports) + Healthcheck**
- [ ] **02. Contract‑Validatoren (Symbol/SecType/Exchange/Currency)**
- [ ] **03. Order‑API (Limit/Stop/Stop‑Limit; DAY/GTC)**
- [ ] **04. MarketData: Streaming + Snapshot Fallback**
- [ ] **05. Paper‑Profile & Sandbox‑Config**
- [ ] **06. Retry/Backoff; Fehlermapping konsistent**
- [ ] **07. **KI‑Hooks** kompatibel (gleiche Signatur wie A1)**
- [ ] **08. Integration‑Tests soweit möglich**

## Abnahme-Kriterien
- [ ] Paper‑Trades OK; Derivate korrekt; KI‑Hook passt zu A1
