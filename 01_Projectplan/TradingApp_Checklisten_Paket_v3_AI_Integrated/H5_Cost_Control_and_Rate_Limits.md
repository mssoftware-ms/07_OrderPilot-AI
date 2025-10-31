# H5 – Kostenkontrolle & Rate‑Limits

> **Projekt:** Automatisierte Trading-Anwendung (Windows 11, Python)
> **Stand:** 2025-10-30 13:07
> **Leitplanken:** Broker **Trade Republic (inoffiziell, privat)** + **IBKR** (offiziell); Live-Daten via Broker-Streams; **1‑Sekunden**-Zeitraster; **Limit/Stop(-Limit)**; **manuelle Freigabe default**; DSGVO; **OpenAI‑Integration** (Responses API mit Structured Outputs; optional Assistants/Realtime).

## Ziele
- Budget‑Sicherheit; adaptive Modellwahl; keine Nutzer‑Fehler trotz 429

## Deliverables
- Budget‑Limits pro Profil; Token‑/Kosten‑Monitor; Backoff/Queueing

## Abhängigkeiten
- H1
- E1
- F1

## Checkliste
- [ ] **01. Budget‑Config: Monatsgrenzen + Warn/Block**
- [ ] **02. Token/Kosten‑Anzeige im Dashboard (E1)**
- [ ] **03. Adaptive Modelle: mini default, Flagship nur bei Bedarf**
- [ ] **04. Retry/Backoff/Jitter; Queueing; Idempotenz**
- [ ] **05. Cache (Hitrate‑Monitoring)**

## Abnahme-Kriterien
- [ ] Budget eingehalten; 429/5xx robust abgefedert
