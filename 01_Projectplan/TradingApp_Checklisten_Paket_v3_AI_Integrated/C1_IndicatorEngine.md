# C1 – Indicator Engine (TA‑Lib/pandas_ta)

> **Projekt:** Automatisierte Trading-Anwendung (Windows 11, Python)
> **Stand:** 2025-10-30 13:07
> **Leitplanken:** Broker **Trade Republic (inoffiziell, privat)** + **IBKR** (offiziell); Live-Daten via Broker-Streams; **1‑Sekunden**-Zeitraster; **Limit/Stop(-Limit)**; **manuelle Freigabe default**; DSGVO; **OpenAI‑Integration** (Responses API mit Structured Outputs; optional Assistants/Realtime).

## Ziele
- RSI/MACD/SMA/EMA/Bollinger/ATR; performant; konfigurierbar; KI‑Kontextbereitstellung

## Deliverables
- TA‑Lib Wrapper + Fallback; Param‑Schemas; Caching

## Abhängigkeiten
- B2
- H2

## Checkliste
- [ ] **01. Einheitliche API je Indikator; Validation via pydantic**
- [ ] **02. Nur aktive Indikatoren berechnen; Caching je Symbol/TF/Params**
- [ ] **03. **KI‑Context Exporter**: kompaktes JSON der relevanten Indikatorwerte für Order‑Dialog/Backtests**
- [ ] **04. Unit‑Tests: Referenzwerte, Randfälle (NaNs, kurze Fenster)**

## Abnahme-Kriterien
- [ ] <50ms/Bar Standard‑Set; KI‑Kontext verfügbar
