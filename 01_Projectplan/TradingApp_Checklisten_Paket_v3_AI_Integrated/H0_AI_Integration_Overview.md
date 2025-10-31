# H0 – KI‑Integration: Überblick & Schnittstellen

> **Projekt:** Automatisierte Trading-Anwendung (Windows 11, Python)
> **Stand:** 2025-10-30 13:07
> **Leitplanken:** Broker **Trade Republic (inoffiziell, privat)** + **IBKR** (offiziell); Live-Daten via Broker-Streams; **1‑Sekunden**-Zeitraster; **Limit/Stop(-Limit)**; **manuelle Freigabe default**; DSGVO; **OpenAI‑Integration** (Responses API mit Structured Outputs; optional Assistants/Realtime).

## Ziele
- Kontextsensitive KI‑Analysen; robuste Service‑Schicht; DSGVO

## Deliverables
- OpenAIService; Routing/Caching; Telemetrie; Feature‑Flags

## Checkliste
- [ ] **01. Architekturdiagramm OpenAIService ↔ Strategy/Alerts/Backtest/UI**
- [ ] **02. Config‑Keys: OPENAI_API_KEY im Credential Manager**
- [ ] **03. Model‑Registry & Defaults per Profil**
- [ ] **04. Cache (Kontext‑Hash) + TTL**
- [ ] **05. Telemetry: Tokens, Latenz, Kosten, Fehlerraten**
- [ ] **06. Circuit‑Breaker/Retry/Timeout‑Politik**

## Abnahme-Kriterien
- [ ] Service isoliert; Abschaltbar; Telemetrie sichtbar
