# B3 – Historie‑Provider (Placeholder)

> **Projekt:** Automatisierte Trading-Anwendung (Windows 11, Python)
> **Stand:** 2025-10-30 13:07
> **Leitplanken:** Broker **Trade Republic (inoffiziell, privat)** + **IBKR** (offiziell); Live-Daten via Broker-Streams; **1‑Sekunden**-Zeitraster; **Limit/Stop(-Limit)**; **manuelle Freigabe default**; DSGVO; **OpenAI‑Integration** (Responses API mit Structured Outputs; optional Assistants/Realtime).

## Ziele
- Spätere AV/Finnhub/IBKR History ohne Codebruch; KI‑Zusammenfassungen vorbereiten

## Deliverables
- History‑Interface; Rolling‑Cache; KI‑Summary‑Hook

## Abhängigkeiten
- B1
- B2
- H2
- H3

## Checkliste
- [ ] **01. Interface: get_historical(symbol, timeframe, from, to)**
- [ ] **02. Rolling‑Cache: lokale DB; Gap‑Handling**
- [ ] **03. **KI‑Hook**: `summarize_history_gaps` (Schema) – erzeugt knappe Hinweise im UI**

## Abnahme-Kriterien
- [ ] Mock‑Provider getestet; KI‑Summary optional/abschaltbar
