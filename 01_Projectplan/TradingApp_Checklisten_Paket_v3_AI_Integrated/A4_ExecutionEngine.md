# A4 – ExecutionEngine

> **Projekt:** Automatisierte Trading-Anwendung (Windows 11, Python)
> **Stand:** 2025-10-30 13:07
> **Leitplanken:** Broker **Trade Republic (inoffiziell, privat)** + **IBKR** (offiziell); Live-Daten via Broker-Streams; **1‑Sekunden**-Zeitraster; **Limit/Stop(-Limit)**; **manuelle Freigabe default**; DSGVO; **OpenAI‑Integration** (Responses API mit Structured Outputs; optional Assistants/Realtime).

## Ziele
- Signal→Order Pipeline; **manuelle Freigabe Default**; Risk‑Controls; KI‑gestützte Begründungen

## Deliverables
- Queue/Retry/Prio; Freigabedialog mit Gebühren/Slippage/Stops; Audit‑Log

## Abhängigkeiten
- A1
- A2/A3
- H0
- H1
- H2
- H3
- H5

## Checkliste
- [ ] **01. Execution‑Queue: Priorität, Idempotenz, Retry‑Politik**
- [ ] **02. Order‑Freigabedialog (2‑stufig): Fees/Slippage/Stops/TIF + **KI‑Erklärung** (Schema `AnalysisResult`)**
- [ ] **03. Auto/Manuell pro Strategie; MaxRisk/DayLimits/Position‑Caps**
- [ ] **04. Audit‑Log (JSON) inkl. KI‑Felder: model, tokens, cost, decision**
- [ ] **05. Kill‑Switch (Hotkey + UI); Red‑State in UI**
- [ ] **06. Unit/Integration‑Tests mit Sim‑Broker; Mock‑KI für deterministische Tests**

## Abnahme-Kriterien
- [ ] Kein UI‑Blocken; KI‑Erklärung erscheint konsistent; Risk‑Controls greifen sofort
