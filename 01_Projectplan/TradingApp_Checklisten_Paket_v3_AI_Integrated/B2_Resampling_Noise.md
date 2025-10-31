# B2 – Resampling & Noise‑Reduction

> **Projekt:** Automatisierte Trading-Anwendung (Windows 11, Python)
> **Stand:** 2025-10-30 13:07
> **Leitplanken:** Broker **Trade Republic (inoffiziell, privat)** + **IBKR** (offiziell); Live-Daten via Broker-Streams; **1‑Sekunden**-Zeitraster; **Limit/Stop(-Limit)**; **manuelle Freigabe default**; DSGVO; **OpenAI‑Integration** (Responses API mit Structured Outputs; optional Assistants/Realtime).

## Ziele
- 1‑Sekunden‑Bars; parametrierbare Median/MA‑Glättung; deterministisch

## Deliverables
- Aggregator: Ticks→Bars; Filter: Median/MA; Param‑UI

## Abhängigkeiten
- B1

## Checkliste
- [ ] **01. OHLCV Aggregator für 1s/5s/10s/1m… (konfigurierbar)**
- [ ] **02. Noise‑Filter: Median/MA, Fenster dynamisch**
- [ ] **03. Latenz/Throughput messen; Backpressure Schutz**
- [ ] **04. **KI‑Signal‑Annotation** Schnittstelle: markiere Bars mit KI‑Hinweisen (z. B. anomale Spikes)**
- [ ] **05. Unit‑Tests (Off‑by‑One/Zeitzonen/Teilbörsentage)**

## Abnahme-Kriterien
- [ ] Deterministische Bars; Filter latenzeffizient; KI‑Annotations optional
