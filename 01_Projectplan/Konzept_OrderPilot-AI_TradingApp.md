# Konzept: **OrderPilot‑AI** – Automatisierte Trading‑Anwendung in Python
> **Stand:** 2025-10-30 14:33 · **Zielplattform:** Windows 11 (Desktop, PyQt6) · **Programmiersprache:** Python 3.11  
> **Kernausrichtung:** Kleinanleger‑freundlich, niedrige Fixkosten, manuelle Freigabe als Default, KI‑Assistenz (Structured Outputs), hybride Broker‑Anbindung (Trade Republic* / IBKR).

\* **Hinweis:** Trade Republic bietet keine offizielle öffentliche API für Drittentwickler. Eine produktive Anbindung stützt sich i. d. R. auf **inoffizielle/private** Mechanismen (riskant/instabil/ToS‑abhängig). **IBKR** stellt eine **offizielle** API (TWS/Gateway) bereit und ist daher der verlässliche Primärpfad für Live/Paper‑Trading.


---

## 1) Executive Summary
OrderPilot‑AI ist eine modulare Desktop‑Trading‑App mit:
- **Live‑Datenstream** über Broker (präferiert IBKR; TR optional/inoffiziell), **1‑Sekunden‑Bars** mit Glättung.
- **Regelbasierten Strategien** (RSI, MACD, SMA/EMA, Bollinger, ATR) + **KI‑Analyse** (Erklärung, Kontraindikatoren, Gebührenhinweis) vor Order‑Freigabe.
- **Manueller Freigabe** als Standard (Automatik optional), **Watchlist & Alarme** mit KI‑Triage, **Backtesting** (Backtrader) mit KI‑Review.
- **Sicherem Key‑Handling**, **Rate‑Limit/Budget‑Kontrolle**, **Audit‑Logs** und **DSGVO‑sensibler** Datenminimalisierung.

Referenzen: **IBKR TWS API** (offiziell) citeturn0search0turn0search3turn0search20, **Backtrader** (Backtests & Live/IBKR) citeturn0search24turn0search12turn0search1, **TA‑Lib** (Indikatoren) citeturn0search22turn0search10, **OpenAI Structured Outputs (Responses API)** citeturn0search8.

---

## 2) Produktziele & Nicht‑Ziele
**Ziele**
1. Günstige, robuste Infrastruktur für Kleinanleger (Gebühren ~1 €/Trade, niedrige Grundkosten).  
2. **Transparenter, kontrollierbarer** Handelsfluss – Nutzer behält die Entscheidungshoheit.  
3. Schnelles Backtesting → Strategietuning → kontrolliertes Live‑Rollout (Paper → Live).

**Nicht‑Ziele**
- Kein Hochfrequenzhandel/HFT.  
- Keine Performance‑Versprechen oder „Signalverkauf“ (Compliance).

---

## 3) Anforderungen & getroffene Grundentscheidungen
- **Broker‑Modell:** **Hybrid** – **IBKR (offiziell, primär)** + **Trade Republic (inoffiziell, sekundär)**. citeturn0search0turn0search20  
- **Handel zuerst über:** **Trade Republic** (manuell freigegeben); paralleler **IBKR Paper‑Account** für Absicherung.  
- **Ordertypen:** **Limit, Stop, Stop‑Limit** (DAY/GTC).  
- **Marktdaten:** **Broker‑Stream** (IBKR/TWS; TR wenn möglich). citeturn0search0  
- **Zeitbasis:** **1‑Sekunde** (frei parametrierbar).  
- **UI:** **PyQt6** Desktop; Themes **Dark (Orange/Dark)** & **Light**.  
- **Indikatoren/Analyse:** **TA‑Lib** / `pandas`. citeturn0search22  
- **Backtesting:** **Backtrader** (inkl. IBKR‑Integration). citeturn0search12  
- **KI:** **OpenAI Responses API – Structured Outputs** (Schema‑validiert); Assistants/Realtime optional. citeturn0search8  
- **Persistenz:** **SQLite** (lokal) + optionale TimescaleDB‑Migration.  
- **Security/Compliance:** Key‑Vault (Windows Credential Manager), Data Minimization, Audit‑Logs, Rate‑Limit/Budget.

---

## 4) Architekturübersicht
### 4.1 Schichten
- **UI‑Layer (PyQt6)**: Dashboard, Chart‑View (Plotly/QWebEngine), Order‑Freigabe‑Dialog, Watchlist/Alarme, Backtest‑UI.  
- **Service‑Layer**: Strategy/Indicator Engine, Execution Engine, Market‑Data Streams, Backtest Runner, Alerting.  
- **Adapters**: `BrokerAdapter` (IBKR/TWS; TR privat), MarketData Feeds.  
- **AI‑Service**: `OpenAIService` (Responses API, Structured Outputs, Caching, Telemetrie). citeturn0search8  
- **Persistence/Infra**: SQLite (Bars/Orders/Trades/Alerts/AI‑Cache/Telemetry), Logs (JSON), Config/Profiles.

### 4.2 Datenströme (vereinfacht)
Broker‑Stream → Resampling (1 s, Glättung) → Indicator Engine → Strategy → **KI‑Post‑Signal‑Analyse** → **Order‑Freigabe‑Dialog** (manuell) → Execution/Broker.  
Alarme: Events → **KI‑Triage (Ranking/Begründung)** → Benachrichtigung.  
Backtests: Resultate → **KI‑Review** (KPIs‑Zusammenfassung & Tuning‑Hinweise).

**Backtrader** deckt Backtests und optional Live‑Trading (IBKR) ab. citeturn0search24

---

## 5) Module (Epics → Kernbausteine)
- **A – Broker & Execution**
  - *A1* BrokerAdapter‑Interface (einheitliche Order‑API, Fees/Rate‑Limits, AI‑Pre‑Check‑Hook).  
  - *A2* Trade Republic Adapter (*inoffiziell; robust gegen Payload‑Änderungen; Warnbanner*).  
  - *A3* IBKR Adapter (TWS/Gateway; Paper/Live; Derivate‑Support). citeturn0search0  
  - *A4* Execution Engine (Queue/Retry, manuelle Freigabe, Audit‑Log, Kill‑Switch).
- **B – Marktdaten**
  - *B1* Stream‑Client (IBKR/TWS, TR wenn möglich). citeturn0search0  
  - *B2* Resampling & Noise‑Reduction (Median/MA, deterministisch).  
  - *B3* Historie‑Provider (Placeholder; später IBKR/AV/Finnhub).
- **C – Strategie & Analyse**
  - *C1* Indicator Engine (TA‑Lib/Pandas). citeturn0search22  
  - *C2* Strategy Engine (Regeln, ATR‑Stops, Cooldowns) + **KI‑Post‑Signal‑Hook**.  
  - *C3* ML‑Hook (optional, spätere Modelle).
- **D – Backtesting**
  - *D1* Backtrader‑Runner + KPIs + **KI‑Review**. citeturn0search24
- **E – UI/UX**
  - *E1* Dashboard & Status (inkl. **KI‑Kosten/Latenz‑Tile**).  
  - *E2* Chart‑View (Plotly/QWebEngine; Live‑Layer; **KI‑Overlays**).  
  - *E3* Strategiekonfigurator (Schemas, Presets, **KI‑Param‑Vorschläge**).  
  - *E4* **Order‑Freigabe‑Dialog** (Begründung/Kontraindikatoren/Gebührenhinweis – **Structured Output**). citeturn0search8  
  - *E5* Watchlist & Alarme (**KI‑Triage/Ranking**).  
  - *E6* Backtest‑UI (Vergleiche, Export, **KI‑Zusammenfassung**).
- **F – Persistence & Logging**
  - *F1* SQLite (Bars/Orders/Trades/Alerts/**ai_cache**, **ai_telemetry**).  
  - *F2* Logs (JSON, Rotation, **KI‑Felder**).  
  - *F3* TimescaleDB (optional; Hypertables/Rollups).
- **G – Security & Compliance**
  - *G1* Config & Secrets (Profiles, **Windows Credential Manager**).  
  - *G2* Rechte & Schutz (Limits, Kill‑Switch, Warnungen).  
  - *G3* ToS/AGB‑Guard (TR‑Hinweis, Throttling).
- **H – KI‑Module**
  - *H0* Überblick/Feature‑Flags/Telemetry  
  - *H1* OpenAIService & Clients (Responses/Assistants/Realtime*)  
  - *H2* Prompt‑Library & JSON‑Schemas  
  - *H3* KI in Strategie/Alarm/Backtest  
  - *H4* Safety/Privacy/Compliance  
  - *H5* Kostenkontrolle/Rate‑Limits

---

## 6) Technologie‑Bausteine
- **IBKR TWS/Gateway API** (offiziell; Python‑Bindings, Testbeds; Paper‑Trading) – *primär für Live*. citeturn0search3  
- **Backtrader** – Backtests, Live‑Feeds/Trading (IBKR). citeturn0search24  
- **TA‑Lib** – 150+ Indikatoren; Windows‑Installer/Conda verfügbar. citeturn0search22turn0search10  
- **OpenAI Responses API (Structured Outputs)** – Schema‑validierte Antworten; stabil für UI‑Flows. citeturn0search8  
- **Plotly + PyQt6‑WebEngine** – interaktive Charts im Desktop‑UI.  
- **JSON‑Schema** – Validierung aller KI‑Outputs (strict).

---

## 7) Kosten‑ & Betriebsannahmen (Richtwerte)
- **IBKR**: Paper‑Trading kostenlos; API offiziell dokumentiert (TWS/Gateway). citeturn0search23  
- **OpenAI**: Nutzung **mini/flagship** je nach Pfad, Budgetgrenzen/Telemetry. **Structured Outputs** reduzieren Integrationsfehler. citeturn0search8  
- **Lokal (Desktop)**: Keine Cloud‑Hosting‑Pflicht; TimescaleDB optional.

---

## 8) Sicherheit, Stabilität & Compliance
- **Key‑Handling:** Windows Credential Manager; keine Klartext‑Secrets.  
- **Data Minimization:** Nur notwendige Felder an die KI senden; keine personenbezogenen Daten.  
- **Rate‑Limits/Budget:** Exponential Backoff + Jitter; Token/Kosten‑Dashboard; Monatslimits.  
- **Audit‑Logs:** Jede KI‑Interaktion mit `model/tokens/cost/promptVersion/schema` protokollieren.  
- **IBKR‑Stabilität:** Offizielle API/Testbeds, Paper→Live‑Pfad, Monitoring/Debug‑Guides. citeturn0search21  
- **TR‑Hinweis:** Inoffizielle Nutzung → ToS‑Risiko; klar sichtbar im UI kennzeichnen.

---

## 9) UI‑Design (Dark/Light)
- **Dark (Orange/Dark):** Hintergrund #0F1115, Primär #F29F05, Text #EAECEF.  
- **Light:** Hintergrund #F7F8FA, Primär #E07B00, Text #0F1115.  
- **Charting:** Candles/Overlays + **KI‑Annotations** (dezente Flags/Tooltips).  
- **Threading:** Keine GUI‑Operationen außerhalb des Main‑Threads; Worker (QThread/QThreadPool) + Signals/Slots. *(Backtrader‑Live‑Betrieb erfordert getrennte I/O‑Threads).* citeturn0search12

---

## 10) Roadmap (8 Wochen, Beispiel)
- **M1 (W1–2):** Core‑Skeleton, Event‑Bus, Config/Profiles, Logging, SQLite‑Schema, **OpenAIService‑Stub**, Prompt/Schemas (Stub).  
- **M2 (W3–4):** IBKR‑Stream + Execution (manuelle Freigabe), Chart‑View (1 s), Indikator‑Basis, **KI‑Order‑Erklärung**, **Alert‑Triage (Pilot)**.  
- **M3 (W5–6):** Backtesting (Backtrader), KPIs, Watchlist/Alarme, **KI‑Backtest‑Review**, Kosten‑Dashboard.  
- **M4 (W7–8):** IBKR‑Optionen/Derivate, Risk‑Controls, Reconnect/Backpressure, **Assistants/Realtime (optional)**.

---

## 11) Abnahmekriterien (Auszug)
- Einheitliche Order‑API (Limit/Stop/Stop‑Limit, DAY/GTC).  
- 1‑Sekunden‑Bars stabil (Resampling/Glättung reproduzierbar).  
- **KI‑Outputs sind schema‑validiert** (Order‑Dialog/Alarme/Backtests). citeturn0search8  
- Backtests reproduzierbar (Backtrader), Paper→Live ohne Code‑Drift. citeturn0search24

---

## 12) Quellen (Auswahl)
- **IBKR API (TWS/Gateway & Campus):** Einführungen, Testbeds, Paper→Live‑Leitfäden. citeturn0search0turn0search3turn0search21  
- **Backtrader – Docs & Live/IBKR:** Quickstart, Live‑Trading, IB‑Integration. citeturn0search24turn0search12  
- **TA‑Lib – Python/Windows:** PyPI & offizielle Installer. citeturn0search22turn0search10  
- **OpenAI – Structured Outputs (Responses API):** Grundlagen & Beispiele. citeturn0search8
