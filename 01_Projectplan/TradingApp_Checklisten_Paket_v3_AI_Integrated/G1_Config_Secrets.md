# G1 – Config & Secrets (Profiles)

> **Projekt:** Automatisierte Trading-Anwendung (Windows 11, Python)
> **Stand:** 2025-10-30 13:07
> **Leitplanken:** Broker **Trade Republic (inoffiziell, privat)** + **IBKR** (offiziell); Live-Daten via Broker-Streams; **1‑Sekunden**-Zeitraster; **Limit/Stop(-Limit)**; **manuelle Freigabe default**; DSGVO; **OpenAI‑Integration** (Responses API mit Structured Outputs; optional Assistants/Realtime).

## Ziele
- Profiles (paper/live); **OpenAI‑Keys sicher**; Limits/Timeouts

## Deliverables
- .env Defaults; Credential Manager; GUI‑Editor; Doppel‑Bestätigung live

## Abhängigkeiten
- H5

## Checkliste
- [ ] **01. .env unsensibel; Validierungen**
- [ ] **02. Secrets: Windows Credential Manager; niemals Klartext**
- [ ] **03. GUI‑Editor für Profile (Model‑Defaults, Budget‑Limits, Timeouts)**
- [ ] **04. Live‑Profil: Doppel‑Bestätigung; roter Rahmen/Badge**

## Abnahme-Kriterien
- [ ] Keys sicher; Profile vollständig; Budget‑Limits greifen
