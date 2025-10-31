# A1 – BrokerAdapter Interface (gemeinsame Order‑API)

> **Projekt:** Automatisierte Trading-Anwendung (Windows 11, Python)
> **Stand:** 2025-10-30 13:07
> **Leitplanken:** Broker **Trade Republic (inoffiziell, privat)** + **IBKR** (offiziell); Live-Daten via Broker-Streams; **1‑Sekunden**-Zeitraster; **Limit/Stop(-Limit)**; **manuelle Freigabe default**; DSGVO; **OpenAI‑Integration** (Responses API mit Structured Outputs; optional Assistants/Realtime).

## Ziele
- Einheitliche Schnittstelle TR/IBKR; Normierung Ordertypen/TIF/Fees; KI‑Hooks definieren

## Deliverables
- ABC + Fehlermodell; Fee‑Engine; Rate‑Limiter/Kill‑Switch; **AI‑Hook-Points** (z. B. Risk‑Explain)

## Checkliste
- [ ] **01. Projektstruktur: src/core/broker/****
- [ ] **02. Typisierte Datamodelle (pydantic): Order, OrderStatus, Position, Balance, FeeModel**
- [ ] **03. ABC: BrokerAdapter – place/cancel/positions/balances/status**
- [ ] **04. Fehlermodell: Exceptions mit Codes; Mapping TR/IBKR‑Spezifika**
- [ ] **05. Ordertypen/TIF Mapping (Market/Limit/Stop/Stop‑Limit; DAY/GTC)**
- [ ] **06. Fee‑Engine: TR flat ~€1; IBKR parameterisierbar**
- [ ] **07. Rate‑Limiter (Token‑Bucket) + globaler Kill‑Switch‑Hook**
- [ ] **08. **KI‑Hooks**: `before_place_order_ai_check(order, context)->AnalysisResult` (Schema)**
- [ ] **09. Unit‑Tests: Contracts, Fees, Validierungen, AI‑Hook‑Stubs**

## Abnahme-Kriterien
- [ ] Contracts stabil; AI‑Hook vorhanden/abschaltbar; Docs & Type‑Hints vollständig
