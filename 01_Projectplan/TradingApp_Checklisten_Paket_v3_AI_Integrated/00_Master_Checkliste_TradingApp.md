# 00 – Master-Checkliste (Module & Meilensteine, inkl. KI)

> **Projekt:** Automatisierte Trading-Anwendung (Windows 11, Python)
> **Stand:** 2025-10-30 13:07
> **Leitplanken:** Broker **Trade Republic (inoffiziell, privat)** + **IBKR** (offiziell); Live-Daten via Broker-Streams; **1‑Sekunden**-Zeitraster; **Limit/Stop(-Limit)**; **manuelle Freigabe default**; DSGVO; **OpenAI‑Integration** (Responses API mit Structured Outputs; optional Assistants/Realtime).


## Module (Epics → Module)
- [ ] A1 BrokerAdapter Interface
- [ ] A2 Trade Republic Adapter (inoffiziell, privat)
- [ ] A3 IBKR Adapter (offiziell)
- [ ] A4 ExecutionEngine
- [ ] B1 Stream-Client (TR/IBKR)
- [ ] B2 Resampling & Noise-Reduction
- [ ] B3 Historie-Provider (Placeholder)
- [ ] C1 Indicator Engine (TA-Lib/pandas_ta)
- [ ] C2 Strategy Engine (regelbasiert)
- [ ] C3 ML-Hook (optional)
- [ ] D1 Backtesting (Backtrader)
- [ ] E1 Dashboard & Status
- [ ] E2 Chart-View (Plotly + PyQtGraph)
- [ ] E3 Strategiekonfigurator
- [ ] E4 Order-Freigabe-Dialog
- [ ] E5 Watchlist & Alarme
- [ ] E6 Backtest-UI
- [ ] E_Themes Dark (Orange/Dark) & Light
- [ ] F1 Datenbank (SQLite)
- [ ] F2 Logs (JSON)
- [ ] F3 TimescaleDB Migration (optional)
- [ ] G1 Config & Secrets (Profiles)
- [ ] G2 Rechte & Schutzmechanismen
- [ ] G3 ToS/AGB-Guard
- [ ] H0 AI-Integration Überblick & Schnittstellen
- [ ] H1 OpenAIService & Clients
- [ ] H2 Prompt-Library & Structured Outputs
- [ ] H3 KI in Strategie/Alarme/Backtests
- [ ] H4 Safety/Privacy/Compliance
- [ ] H5 Kostenkontrolle & Rate-Limits

## Meilensteine
- [ ] **M1 (W1–2):** Core-Skeleton, Event-Bus, Config/Profiles, Logging, DB-Schema (SQLite), **OpenAIService (Stub)**, **Prompt/Schemas (Stub)**
- [ ] **M2 (W3–4):** TR-Stream + Execution (manuelle Freigabe), Chart-View 1s, Indikatoren-Basis, **KI im Order-Dialog (Erklärung)**, **Alert‑Triage (Pilot)**
- [ ] **M3 (W5–6):** Backtesting (Backtrader), KPIs, Watchlist/Alarme, **Backtest‑Reviewer (KI)**, Kostenmonitor
- [ ] **M4 (W7–8):** IBKR-Adapter (Paper), Risk-Controls, Reconnect/Backpressure, **Assistants‑Tools (optional)**
- [ ] **M5 (W9+):** Historie-Provider, Timescale, ML-Hook, Realtime (optional)

## Abnahme-Kriterien (global)
- [ ] Einheitliche Order-API (Limit/Stop/Stop-Limit, DAY/GTC) implementiert
- [ ] 1‑Sekunden‑Bars stabil (Resampling + Glättung parametrierbar)
- [ ] KI‑Funktionen per Feature‑Flag deaktivierbar; **Structured Outputs** strikt validiert
- [ ] Backtests reproduzierbar; gleiche Strategy‑Artefakte live/backtest
- [ ] UI in **Dark (Orange/Dark)** und **Light** vollständig nutzbar
