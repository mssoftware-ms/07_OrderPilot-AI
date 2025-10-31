# E5 – Watchlist & Alarme

> **Projekt:** Automatisierte Trading-Anwendung (Windows 11, Python)
> **Stand:** 2025-10-30 13:07
> **Leitplanken:** Broker **Trade Republic (inoffiziell, privat)** + **IBKR** (offiziell); Live-Daten via Broker-Streams; **1‑Sekunden**-Zeitraster; **Limit/Stop(-Limit)**; **manuelle Freigabe default**; DSGVO; **OpenAI‑Integration** (Responses API mit Structured Outputs; optional Assistants/Realtime).

## Ziele
- Preis‑ und Indikator‑Trigger; **KI‑Triage**; Benachrichtigung

## Deliverables
- Watchlist‑Repo; Alarm‑DSL; Tray/Popup/Ton; KI‑Ranking

## Abhängigkeiten
- B1
- C1
- F1
- H2
- H3
- H5

## Checkliste
- [ ] **01. Watchlist (DB), Tags/Filter**
- [ ] **02. Alarm‑DSL (Symbol, Bedingung, Wert, Dauer)**
- [ ] **03. **KI‑Triage**: `alert_explain_and_rank(event)->AlertDecision` (Schema)**
- [ ] **04. Benachrichtigung + Snooze/Auto‑Reset**

## Abnahme-Kriterien
- [ ] Zero‑Miss; False‑Positives reduziert; Ranking plausibel
