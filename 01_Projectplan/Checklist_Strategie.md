# ✅ Checkliste: OrderPilot-AI – Strategie-, Skript-Engine & KI-Integration

**Projekt:** 07_OrderPilot-AI  
**Repo:** D:\03_Git\02_Python\07_OrderPilot-AI  
**Start:** 2025-11-22  
**Letzte Aktualisierung:** 2025-11-22  
**Scope:** Strategie-Engine, Skriptsprache, KI (GPT-4.1), Risk-Layer, Backtest/Paper/Live – **Orderausführung im Detail später**

---

## 🛠 CODE-QUALITÄTS-STANDARDS (für OrderPilot-AI)

### ✅ Pflichtregeln

1. **Vor Implementierung prüfen**
   - [ ] Vor jeder neuen Funktion/Klasse: **Suche im Projekt**, ob Ähnliches existiert  
         (VS Code „Go to Symbol“, Projektweite Suche).
   - [ ] Wenn ja → **wiederverwenden/erweitern**, NICHT duplizieren.

2. **Keine doppelten & toten Codes**
   - [ ] Kein Copy&Paste von Logik (DRY).  
   - [ ] Ungenutzte Funktionen/Module löschen (Git ist das Archiv).:contentReference[oaicite:1]{index=1}  

3. **Modulgröße**
   - [ ] Keine `.py` > **500 Zeilen** produktiver Code.  
   - [ ] Falls größer → Modul in logisch saubere Teile splitten  
         (z. B. `app_ui.py`, `app_controllers.py`, `app_state.py`).

4. **Tests für jede Funktion**
   - [ ] Jede neue „logische“ Funktion (kein reiner Getter/Setter) bekommt **mind. 1 Unit-Test**,  
         Lokation: `tests/…`.
   - [ ] Edge-Cases & Fehlerpfade abdecken (z. B. leere Daten, API-Fehler).

5. **Type Hints & Docstrings**
   - [ ] Alle öffentlichen Funktionen/Klassen: vollständige Type Hints.
   - [ ] Kurz-Docstring: Zweck, Parameter, Rückgabe, mögliche Exceptions.

6. **Error Handling & Logging**
   - [ ] Kein `except: pass`.  
   - [ ] Für kritische Pfade (Daten, Orders, KI): Logging + sinnvolle Fehlermeldung.:contentReference[oaicite:2]{index=2}  

7. **Trennung Definition / Ausführung**
   - [ ] In `src/` nur Module mit Definitionen.  
   - [ ] Einstiegspunkte: `main_*.py` im Root (oder `src/orderpilot/main.py`) mit  
     `if __name__ == "__main__":`.

8. **Nur getesteter Code in „Live-Pfad“**
   - [ ] Keine Änderungen an Backtest/Paper/Live-Routen ohne passende Tests.
   - [ ] PR/Commit erst nach: Tests ✅ + Linting ✅.

### ❌ Verboten

- Platzhalter (`# TODO später`, `return "Not implemented"` im Live-Pfad)  
- Auskommentierte Legacy-Funktionen als „Archiv“  
- Magic Numbers ohne Konfig (Risikoprozente, Schwellen)  
- Direktes Arbeiten mit API-Keys im Code (nur `.env`/Config)

---

## 📁 Ziel-Ordnerstruktur (OrderPilot-AI)

Unter `src/`:

- `src/orderpilot/core/` – Basistypen, Events, Config
- `src/orderpilot/marketdata/` – Alpaca-Adapter, Aggregation
- `src/orderpilot/strategies/` – Strategie-/Skript-Engine
- `src/orderpilot/risk/` – Risk-Layer
- `src/orderpilot/orders/` – Order-Routing (später vertiefen)
- `src/orderpilot/backtest/` – Backtesting-Engine
- `src/orderpilot/llm/` – GPT-4.1-Anbindung, Prompts, Adapter
- `src/orderpilot/monitoring/` – Logging, Metriken, einfache Views
- `src/ui/` – Qt/GUI (bestehende `app.py` aufsplitten falls >500 Zeilen)

---

## PHASE 0 – Aufräumen & Basis vorbereiten

### 0.1 Struktur & Standards im Repo verankern

- [ ] **0.1.1 Zielstruktur anlegen**
  - Ordner unter `src/orderpilot/…` anlegen (siehe oben).
  - `__init__.py` in allen Paket-Ordnern.

- [ ] **0.1.2 Bestehende Module sichten**
  - `src/ui/app.py` und andere große Dateien auflisten.
  - Prüfen, welche Logik Richtung Strategie/Trading geht → NOTIEREN.

- [ ] **0.1.3 Prüfen auf Duplikate & toten Code**
  - Projektweite Suche nach doppelten Hilfsfunktionen.
  - Alte, ungenutzte Funktionen/Module identifizieren und zur Löschung markieren.

- [ ] **0.1.4 Test-Infrastruktur**
  - Sicherstellen: `tests/`-Ordner vorhanden.
  - `pytest` konfiguriert, ein erster Test läuft (Smoke-Test).

---

## PHASE 1 – Core-Datenmodelle & Event-Pipeline

### 1.1 Domain-Modelle für OrderPilot-AI

- [ ] **1.1.1 Basistypen in `src/orderpilot/core/models.py`**
  - `Candle`, `Signal`, `OrderRequest`, `OrderStatus`, `Position`, `PortfolioState`.

- [ ] **1.1.2 Events & Message-Envelope**
  - Datei: `src/orderpilot/core/events.py`
  - Einheitliches Event-Schema: `type`, `timestamp`, `payload`, `source`, `correlation_id`.

- [ ] **1.1.3 In-Memory-Event-Bus**
  - Datei: `src/orderpilot/core/event_bus.py`
  - Publisher/Subscriber-API, Topics: `MARKET_DATA`, `SIGNAL`, `ORDER`, `POSITION`, `LLM`.

### 1.2 Marktdaten (Alpaca) an Event-Bus hängen

- [ ] **1.2.1 Alpaca-Adapter refaktorieren**
  - Datei: `src/orderpilot/marketdata/alpaca_adapter.py`
  - Nur noch: Verbindungsaufbau, Raw-Daten → `Candle`.

- [ ] **1.2.2 Candle-Events publizieren**
  - 1m-Candles: `MARKET_DATA` Events mit `Candle`-Payload.

- [ ] **1.2.3 Aggregation 5m/15m**
  - Datei: `src/orderpilot/marketdata/aggregator.py`
  - Aus 1m → 5m/15m bauen, neue Events emittieren.

- [ ] **1.2.4 Latenz-Messung**
  - Messung „Serverzeit vs. Empfangszeit“ pro Candle loggen.

---

## PHASE 2 – Strategie- / Skript-Engine

### 2.1 Strategie-Interface & Registry

- [ ] **2.1.1 Strategy-Baseclass**
  - Datei: `src/orderpilot/strategies/base.py`
  - Methoden: `on_candle`, `on_position_update`, `generate_signals`.

- [ ] **2.1.2 Strategie-Registry**
  - Datei: `src/orderpilot/strategies/registry.py`
  - Mapping `strategy_id` → Strategy-Klasse, Laden aus Config.

### 2.2 Skript-Layer (einfache DSL / Python-Skripte)

- [ ] **2.2.1 Dateibasierte Strategien**
  - Ordner: `strategies/scripts/` im Repo.
  - Ein Skript = eine Strategie-Definition (Python oder minimale DSL).

- [ ] **2.2.2 Sandbox für Skripte**
  - Datei: `src/orderpilot/strategies/sandbox.py`
  - Eingeschränkter Namespace, Zeitlimit.

- [ ] **2.2.3 MA-Crossover als Referenzstrategie**
  - Datei: `src/orderpilot/strategies/ma_crossover.py`
  - Nutzt Basis-API, liefert klare `Signal`-Objekte.

### 2.3 Engine-Lifecycle

- [ ] **2.3.1 Strategy-Runner**
  - Datei: `src/orderpilot/strategies/runner.py`
  - Abonniert `MARKET_DATA`, ruft `strategy.on_candle`, publiziert `SIGNAL`.

- [ ] **2.3.2 Multi-Strategie-Support**
  - Mehrere Strategy-Instanzen pro Symbol/Timeframe möglich.
  - Konfiguration in z. B. `config/strategies.yaml`.

---

## PHASE 3 – Backtesting

### 3.1 Backtest-Core

- [ ] **3.1.1 Backtest-Datenquelle**
  - Datei: `src/orderpilot/backtest/data_loader.py`
  - CSV/Parquet/Alpaca-History → `Candle`-Sequenz.

- [ ] **3.1.2 Backtest-Engine**
  - Datei: `src/orderpilot/backtest/engine.py`
  - Spielt Candles über Event-Bus ein, nutzt existierende Strategy-/Risk-Pipeline.

### 3.2 KPIs & Reports

- [ ] **3.2.1 Trade-/Equity-Tracking**
  - Datei: `src/orderpilot/backtest/tracking.py`
  - Sammlt Trades, Equity-Kurve, Drawdown.

- [ ] **3.2.2 KPI-Berechnung**
  - Winrate, Profit-Faktor, Max Drawdown, Sharpe/Sortino.

---

## PHASE 4 – Risk-Management-Layer

### 4.1 Zentraler Risk-Layer

- [ ] **4.1.1 Risk-Modul**
  - Datei: `src/orderpilot/risk/engine.py`
  - Subscriber für `SIGNAL`, Publisher für `ORDER_REQUEST`.

- [ ] **4.1.2 Regeln: Risiko pro Trade**
  - Konfig: `config/risk.yaml`
  - Berechnung Positionsgröße per Strategy/Symbol.

- [ ] **4.1.3 Tagesverlust & Max-Exposure**
  - Tracking Tages-PnL, offene Positionen.
  - Blockiert neue Orders bei Grenzübertritt.

### 4.2 Kill-Switch & Fail-Safes

- [ ] **4.2.1 Manueller Kill-Switch**
  - API/CLI, die Flag `trading_enabled=False` setzt.

- [ ] **4.2.2 Automatischer Kill-Switch**
  - Trigger bei: Datenfeed-Ausfall, KI-Ausfall, Broker-Errors, Überschreitung Tagesverlust.

---

## PHASE 5 – Order-Layer (nur minimal für den Flow)

- [ ] **5.1.1 Order-Interface**
  - Datei: `src/orderpilot/orders/interface.py`
  - `submit_order(request)`, `cancel_order(id)`, `sync_positions()`.

- [ ] **5.1.2 Paper-Adapter**
  - Datei: `src/orderpilot/orders/alpaca_paper.py`
  - Umsetzung für Alpaca-Paper, Rückgabe `OrderStatus`-Events.

---

## PHASE 6 – KI-Modul (GPT-4.1)

### 6.1 LLM-Adapter & Modelle

- [ ] **6.1.1 OpenAI-Client**
  - Datei: `src/orderpilot/llm/openai_client.py`
  - GPT-4.1 „trading-advisor“; Timeout/Retry.

- [ ] **6.1.2 Request-/Response-Modelle**
  - Datei: `src/orderpilot/llm/models.py`
  - `LLMRequest` (komprimierte Marktdaten + Strategie-Signal + Risiko-Kontext),  
    `LLMResponse` (action, confidence, reasoning).

### 6.2 Prompt-Design

- [ ] **6.2.1 Advisor-Prompt**
  - Datei: `src/orderpilot/llm/prompts.py`
  - Template: „Strategie X schlägt Entry bei Preis Y vor, Marktkontext …, Risiko … → Empfehlung?“

- [ ] **6.2.2 Autonomer Prompt (später aktivierbar)**
  - Klar definierte Constraints: darf **niemals** Risk-Limits überschreiten (wird trotzdem vom Risk-Layer geprüft).

### 6.3 Integration in den Flow

- [ ] **6.3.1 LLM-Decision-Node**
  - Datei: `src/orderpilot/llm/router.py`
  - Flow: `SIGNAL` → optional LLM → `Risk-Engine`.

- [ ] **6.3.2 Fallback-Logik**
  - Wenn LLM nicht antwortet:  
    - Entweder Strategie-Signal unverändert weitergeben  
    - oder Signal verwerfen (Konfig-Flag).

- [ ] **6.3.3 Reasoning-Logging**
  - Speicherung von `LLMResponse.reasoning` in z. B. `logs/llm_decisions.log`.

---

## PHASE 7 – Workflows & Modi (Backtest / Paper / Live)

- [ ] **7.1.1 Modus-Flag in Config**
  - `mode = backtest|paper|live` in `config/app.yaml`.

- [ ] **7.1.2 CLI/Runner für Backtest**
  - Datei: `main_backtest.py`
  - Parameter: Strategie, Zeitraum, Symbole → Backtest-Report.

- [ ] **7.1.3 CLI/Runner für Paper**
  - Datei: `main_paper.py`
  - Live-Daten, Paper-Orders, volle Logs.

- [ ] **7.1.4 Live-Runner (nur wenn ready)**
  - Datei: `main_live.py`
  - Nutzt **exakt gleichen Flow** wie Paper, nur anderer Order-Adapter.

---

## PHASE 8 – Monitoring & UI-Anbindung

- [ ] **8.1.1 Zentrale Logging-Konfiguration**
  - Datei: `src/orderpilot/monitoring/logging_config.py`
  - Channels: `trading`, `risk`, `llm`, `infra`, `backtest`.

- [ ] **8.1.2 Metrik-Sammlung**
  - Datei: `src/orderpilot/monitoring/metrics.py`
  - Tages-PnL, aktuelle Positionen, LLM-Latenz.

- [ ] **8.1.3 UI-Hooks in `src/ui/`**
  - Strategiestatus, PnL, aktive Signale im bestehenden Qt-UI anzeigen  
    (z. B. eigene Panel-Klasse `StrategyMonitorWidget`).

---

## 🔄 Ablaufdiagramm (angepasst auf OrderPilot-AI)

```mermaid
flowchart LR
    MD[marketdata/alpaca_adapter.py] -->|Candle-Events| STRAT[strategies/runner.py]
    STRAT -->|Signal| LLM[llm/router.py]
    STRAT -->|Signal (direkt)| RISK[risk/engine.py]
    LLM -->|verfeinertes Signal + Reasoning| RISK
    RISK -->|OrderRequest| ORD[orders/alpaca_paper.py]
    ORD -->|OrderStatus/Positions| POS[core/models: Position]
    POS --> STRAT
    MD --> MON[monitoring/*]
    STRAT --> MON
    LLM --> MON
    RISK --> MON
    ORD --> MON
    BACK[backtest/engine.py] --> STRAT
    BACK --> RISK
    BACK --> MON
