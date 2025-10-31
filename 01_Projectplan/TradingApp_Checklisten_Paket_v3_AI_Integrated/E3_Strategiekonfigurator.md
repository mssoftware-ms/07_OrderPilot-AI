# E3 – Strategiekonfigurator

> **Projekt:** Automatisierte Trading-Anwendung (Windows 11, Python)
> **Stand:** 2025-10-30 13:07
> **Leitplanken:** Broker **Trade Republic (inoffiziell, privat)** + **IBKR** (offiziell); Live-Daten via Broker-Streams; **1‑Sekunden**-Zeitraster; **Limit/Stop(-Limit)**; **manuelle Freigabe default**; DSGVO; **OpenAI‑Integration** (Responses API mit Structured Outputs; optional Assistants/Realtime).

## Ziele
- Aktivieren/Parametrisieren von Strategien/Indikatoren; **KI‑Preset‑Vorschläge**

## Deliverables
- Form‑Schemas; Validierung; Presets; KI‑Autosuggest

## Abhängigkeiten
- C2
- H2
- H3

## Checkliste
- [ ] **01. Form‑Generator aus pydantic‑Schemas**
- [ ] **02. Preset Save/Load; Profile‑Defaults**
- [ ] **03. **KI‑Vorschläge**: Parameter‑Hints aus Backtest‑Reviews**
- [ ] **04. Live‑Validierung & Inline‑Hilfen**

## Abnahme-Kriterien
- [ ] Param‑Änderungen ohne Neustart; KI‑Vorschläge nachvollziehbar
