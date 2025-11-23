# OrderPilot-AI – Detaillierte Codeanalyse

## 1. Projektüberblick
- **Zielsetzung:** OrderPilot-AI ist eine Desktop-Handelsplattform mit KI-gestützter Orderprüfung, mehrstufigem Risikomanagement und PyQt6-Oberfläche. Kernflüsse: Echtzeitmarktdaten → Indikatoren → Strategien → KI-Validierung → Orderausführung → Überwachung.
- **Architektur:** Klare Schichten für Infrastruktur (`src/common`), Konfiguration (`src/config`), KI-Dienste (`src/ai`), Datenversorgung (`src/core/market_data`), Indikatoren & Strategien (`src/core/indicators`/`strategy`), Broker & Execution (`src/core/broker`/`execution`), Persistenz (`src/database`) und UI (`src/ui`). Tests liegen in `tests/`.
- **Einstieg & Laufzeit:** `main.py` delegiert an `start_orderpilot.py`, das Banner, Logging, Abhängigkeits-Checks und Datenbank-Setup startet, bevor `ui/app.py:main()` die asynchrone PyQt/QEventLoop-Anwendung hochzieht.

## 2. Eingesetzte Python-Bibliotheken
Die wichtigsten Abhängigkeiten aus `requirements.txt` und `dev-requirements.txt` gruppiert nach Aufgabenbereich:

| Kategorie | Bibliotheken | Zweck im Projekt |
| --- | --- | --- |
| Async & Infrastruktur | `aiohttp`, `websockets`, `blinker`, `tenacity`, `python-json-logger`, `pytz`, `PyYAML`, `keyring`, `cryptography`, `jsonschema` | HTTP/WebSocket-Kommunikation, Event-Bus, Retry-Strategien, strukturierte Logs, Zeitzonen, YAML-Konfig, Credential- & Verschlüsselungs-Utilities, Schema-Validierung.
| Daten & Analytics | `numpy`, `pandas`, `pandas-ta`/`pandas_ta`, `matplotlib` | Numerik, OHLCV-Verarbeitung, technische Indikatoren (TA-Lib-Ersatz), Chart-Ausgabe.
| Trading & Marktdaten | `alpaca-py`, `ibapi`, `backtrader`, `alpaca.data.*`, `websockets` | Broker- und Marktdatenzugriff (Alpaca, IBKR), Backtests via Backtrader, Realtime-Streams.
| Persistenz & Modellierung | `SQLAlchemy`, `pydantic`, `pydantic-settings`, `PyYAML` | ORM für Orders/MarketBars, Validierung von Settings/Profilen, YAML-Konfigs. (Hinweis: Duplicate Pins `pydantic-settings` vs. `pydantic_settings`.)
| Benutzeroberfläche | `PyQt6`, `pyqtgraph`, `qasync` | Desktop-GUI, Charting, Async-Integration in Qt-Eventloop.
| KI & Automatisierung | `openai` | Strukturierte KI-Ausgaben für Order-, Signal-, Backtest- und Alert-Analysen.
| Logging & Sicherheit | `python-json-logger`, `cryptography`, `keyring` | JSON-Audit-Logs, Verschlüsselung via Fernet, Credential-Speicher.
| Tests & Tooling | `pytest`, `pytest-qt`, `ruff`, `mypy`, `types-PyYAML`, `types-requests`, `sphinx`, `furo` | Automatisierte Tests (inkl. UI), Linting, Typprüfung und Dokumentation.

> Hinweis: `pandas-ta` und `pandas_ta` sowie `pydantic-settings` und `pydantic_settings` sind doppelt gelistet; Konsolidierung reduziert Build-Zeit und Konflikte.

## 3. Modulübersicht – Funktionen & Aufgaben

### 3.1 Bootstrap & Konfiguration
- `main.py` / `start_orderpilot.py`: CLI-Argumente, Banner, Logging (`setup_logging`), Dependency-Check, DB-Init (`check_database`), Setzen von `TRADING_ENV`/Profil-Variablen, Start von `ui.app.main()`.
- `src/config/loader.py`: Pydantic-basierte Settings (`AppSettings`, `ProfileConfig`) für Broker, Markt, Backtests, UI usw. `ConfigManager` lädt/speichert YAML-Profile (`config/profiles/*.yaml`), verwaltet Secrets via `keyring`, exportiert Profile und pflegt Watchlists.
- `systemvariablen.py` & `.env`-Handling (falls vorhanden) interagieren mit dem Konfig-Manager für Laufzeitparameter.

### 3.2 Infrastruktur (`src/common`)
- `event_bus.py`: `EventType`-Enum deckt Application-, UI-, Markt-, Strategie-, Order-, Alert-, AI- und Backtest-Events ab. `EventBus.emit/subscribe/unsubscribe/get_history` liefert ein blinker-basiertes Publish/Subscribe-Rückgrat; globaler `event_bus` + Convenience-Signale (`app_event` etc.).
- `logging_setup.py`: JSON-Logging inkl. `AITelemetryFilter`, `TradingJsonFormatter`, Rotations-Handler (App/Audit/AI). Utility-Calls `log_order_action` und `log_ai_request` bringen strukturierte Metadaten in Audit- bzw. Telemetrie-Logs.
- `performance.py`: `PerformanceMonitor` trackt Latenzen/Counters, liefert `monitor_performance` & `log_performance` Dekoratoren sowie `performance_monitor.report()` für Diagnosen.
- `security.py`: Sicherheits-Enums (`SecurityLevel`, `SecurityAction`), `SecurityContext`, `EncryptionManager` (PBKDF2 + Fernet), Keyring-Integration, Event/Audit-Emissionen (z.B. bei Kill-Switch). Ideal für Handling sensibler Orderdaten.

### 3.3 KI-Layer (`src/ai`)
- `openai_service.py`: 
  - `OpenAIService.structured_completion()` orchestriert Schema-validierte ChatCompletions (JSON-Schema via `jsonschema.validate`, Tenacity Retries, `CostTracker`/`CacheManager`).
  - Spezialisierte Methoden `analyze_order`, `triage_alert`, `review_backtest`, `analyze_signal` erzeugen strukturierte `OrderAnalysis`, `AlertTriageResult`, `BacktestReview`, `StrategySignalAnalysis` (alle `pydantic`-Modelle).
  - `CostTracker` berechnet tokenbasierte Kosten und erzwingt Monatsbudgets; `CacheManager` (in Datei definiert) reduziert Tokenverbrauch via Prompt-Hashing.
- `prompts.py`: `PromptTemplates` für Order-, Alert-, Backtest-, Signal- und Risiko-Analysen plus JSON-Schemas und `PromptBuilder`/`SchemaValidator` für Versionierung und Validierung.
- `ai/__init__.py`: Exportiert Modelle/Funktionen, damit andere Layer nur `from src.ai import get_openai_service` verwenden müssen.

### 3.4 Markt- & Datenversorgung (`src/core/market_data`)
- `history_provider.py`: 
  - `DataSource`, `Timeframe`, `HistoricalBar`, `DataRequest` beschreiben Abrufparameter.
  - `HistoricalDataProvider` Template-Methode mit optionalem Cache; konkrete Provider (IBKR, Alpaca, AlphaVantage, Finnhub, Yahoo, Database) implementieren `_fetch_data_from_source` & `is_available`.
  - `HistoryManager` verwaltet Provider-Prioritäten je Profil, cached Bars in SQL via `get_db_manager`, liefert `fetch_data`, `get_latest_price`, `start_realtime_stream` (Priorität: Alpaca WS → AlphaVantage Polling) und `stop_realtime_stream`.
- `stream_client.py`: Abstrakter Echtzeit-Client mit `StreamMetrics`, `MarketTick`, Backpressure/Buffering, Subscriptions, Lags und Event-Emission (`EventType.MARKET_DATA_TICK`).
- `alpaca_stream.py` & `alpha_vantage_stream.py`: Konkrete Streamer – Alpaca via WebSocket (`StockDataStream`), Alpha Vantage via Polling. Beide feuern Verbindungs-/Tick-Events und integrieren Latenz-Metriken.
- `resampler.py`: `MarketDataResampler` + Filter (Median, Moving Average, Kalman) erzeugen 1s-Bars und feuern `EventType.MARKET_BAR`-Events, sodass Strategien glatte Daten erhalten.

### 3.5 Indikatoren & Strategien
- `src/core/indicators/engine.py`: `IndicatorEngine.calculate()` orchestriert TA-Berechnung mit optionaler TA-Lib/Pandas-TA-Fallback-Logik, Caching und Event-Emission. `IndicatorConfig` + `IndicatorType` decken Trend/Momentum/Volatilität/Volumen/Custom-Indikatoren.
- `src/core/strategy/engine.py`: 
  - `StrategyConfig/State/Signal` definieren Parameter & Laufzeitstatus.
  - Konkrete Klassen `TrendFollowingStrategy`, `MeanReversionStrategy`, `MomentumStrategy`, `BreakoutStrategy`, `ScalpingStrategy` implementieren `evaluate()` (nutzen Indikatoren, Positionstracking).
  - `StrategyEngine` verwaltet Strategien (`create_strategy`, `enable/disable`), führt `evaluate_all` asynchron aus, bündelt Signale (`combine_signals`), konvertiert Signale in `OrderRequest` (`signal_to_order`) und liefert Stats (`get_strategy_stats`).

### 3.6 Broker & Execution
- `src/core/broker/base.py`: 
  - Kern-Datenmodelle (`OrderRequest`, `OrderResponse`, `Position`, `Balance`, `FeeModel`) nutzen `pydantic`-Validierung (z.B. Pflicht-Limitpreis für Limit-Orders).
  - `AIAnalysisRequest/Result` und `TokenBucketRateLimiter` integrieren KI-Feedback + API-Ratenkontrolle.
  - `BrokerAdapter` implementiert Template-Methoden für `connect`, `place_order`, `cancel_order`, Positions-/Balance-Fetching und AI-Hooks.
- Konkrete Adapter: `mock_broker.py` (Simulation mit Cash, Fills, Gebühren), `ibkr_adapter.py`, `trade_republic_adapter.py` (nicht im Detail gezeigt, aber strukturell identisch).
- `src/core/execution/engine.py`: `ExecutionEngine` pflegt `ExecutionTask`-Queues, Prioritäten, manuelle Freigaben, Daily-Loss/Drawdown-Grenzen sowie eine Kill-Switch-State-Machine (`activate_kill_switch`). Events (APP_START/APP_ERROR) informieren den Bus; Datenbank-Integration speichert Orders.

### 3.7 Backtesting
- `src/core/backtesting/backtrader_integration.py`: `BacktestConfig`/`BacktestResult` definieren Parameter & Kennzahlen. `OrderPilotStrategy` Wrapped-Strategie nutzt Backtrader-Callbacks `notify_order`, `notify_trade`, `next()` (async) und `IndicatorEngine`. Ergebnisse enthalten Equity-Kurven, Trade-Logs und optional Benchmark.

### 3.8 Persistenz & Datenbank (`src/database`)
- `models.py`: SQLAlchemy-Modelle für `MarketBar`, `Order`, `Execution`, `Position`, `Alert`, `Strategy`, `AITelemetry`, `AICache`, `AuditLog`, `SystemMetrics` inkl. Enums (`OrderStatus`, `OrderType`, `TimeInForce`, `AlertPriority`). Enthält Constraints, Indizes und JSON-Felder für KI-Analysen.
- `database.py`: `DatabaseManager` kapselt Engine-Setup (SQLite default, optional PostgreSQL/Timescale), `initialize`, `session` Kontextmanager, Wartungsfunktionen (`backup`, `vacuum`, `cleanup_old_data`, `get_table_stats`). `initialize_database`/`get_db_manager` stellen globale Instanz bereit.

### 3.9 Benutzeroberfläche (`src/ui`)
- `app.py`: `TradingApplication(QMainWindow)` orchestriert Broker-Verbindungen (`connect_broker`), Orderdialoge, Timer, Event-Handler, Theme-Wechsel, Status-Bar, Dock-Widgets und asynchrone Init (`asyncio.create_task(initialize_services)`). Signale wie `broker_connected`/`order_placed` koppeln UI-Komponenten an Back-End-Ereignisse. `main()` richtet Logging, `QApplication`, `qasync.QEventLoop` ein und startet das Fenster.
- Dialoge (`dialogs/`): `OrderDialog`, `SettingsDialog`, `BacktestDialog` kapseln Benutzerinteraktionen (Ordereingabe, Konfig, Backtests) inkl. Validierungen.
- Widgets (`widgets/`): 
  - `DashboardWidget`, `PerformanceDashboard`, `WatchlistWidget`, `OrdersWidget`, `PositionsWidget`, `IndicatorsWidget`, `AlertsWidget` stellen spezialisierte Ansichten dar.
  - `chart_window_manager.py` + `EmbeddedTradingViewChart`, `pyqtgraph`-basierte Komponenten rendern Charts; `themes.py` & `icons.py` kümmern sich um Look & Feel.

### 3.10 Tests & Hilfsskripte
- `tests/`: Pytest-Suites für Kernbereiche (`test_event_bus`, `test_security`, `test_execution_engine`, `test_broker_adapter`, `test_config`, `test_database`, `test_performance`, `test_integration`, `test_skeleton`). `pytest-qt` deckt GUI-Aspekte ab.
- Skripte (`comprehensive_system_test.py`, `check_db_data.py`, `fix_imports.py`) liefern Diagnose-, Maintenance- und Refactoring-Helfer.

## 4. Typische Funktionsketten
1. **Realtime Trading Flow**
   1. `HistoryManager.start_realtime_stream()` wählt Alpaca/Alpha-Vantage Provider → `StreamClient.process_tick()` erzeugt `MarketTick` → `event_bus` feuert `MARKET_DATA_TICK`.
   2. `MarketDataResampler` + `IndicatorEngine.calculate()` aktualisieren technische Werte, die `StrategyEngine.evaluate_all()` in Signale übersetzt.
   3. `StrategyEngine.signal_to_order()` → `ExecutionEngine.submit_order()` (inkl. optionalem `AIAnalysisRequest` via `OpenAIService.analyze_order`).
   4. `ExecutionEngine` validiert Limits (manuelle Approval Hooks), nutzt `BrokerAdapter.place_order()` zur tatsächlichen Ausführung (Mock/IBKR/TradeRepublic). Ergebnis-Events aktualisieren DB (`DatabaseManager`) und UI-Widgets (Orders/Positions/Dashboard).

2. **Backtest Flow**
   - `BacktestDialog` sammelt Parameter → `BacktestConfig` + `HistoryManager.fetch_data()` → `OrderPilotStrategy` (Backtrader) simuliert Trades → `BacktestResult` liefert Kennzahlen, optional `OpenAIService.review_backtest()` zieht eine KI-Bewertung nach.

3. **Alert & Sicherheit**
   - Alerts (z.B. Stop-Loss, Disconnect) feuern `EventType.ALERT_TRIGGERED`, `AlertsWidget` zeigt Details, `security.log` vermerkt Aktionen (`SecurityAction.ALERT`). Kill-Switch-Aufruf (`ExecutionEngine.activate_kill_switch`) setzt Status via Event-Bus & UI-Hinweis.

4. **Konfig-Änderungen**
   - `ConfigManager.save_profile()` schreibt YAML, `event_bus` erhält `CONFIG_CHANGED`, wodurch UI/Einstellungen/Services (z.B. neue Provider) reinitialisiert werden können.

## 5. Hinweise & Beobachtungen
- Doppelte Requirements (`pandas-ta` vs. `pandas_ta`, `pydantic-settings` vs. `pydantic_settings`, `python-json-logger` vs. `python_json_logger`) sollten konsolidiert werden.
- `HistoryManager` nutzt viele Provider-Klassen; Credential-Handling hängt von `keyring`. Für Nicht-Windows-Umgebungen muss ein alternatives Secret-Backend konfiguriert werden.
- Das Event-System ist zentral – Subscription-Übersicht (wer hört auf welche Events) sollte dokumentiert bleiben, um unbeabsichtigte Race Conditions zu vermeiden.
- `ExecutionEngine` kombiniert Async (Queue) mit DB-Zugriff; Sicherstellen, dass `get_db_manager()` vor Start initialisiert wird (z.B. beim UI-Setup).
- PyQt + `qasync` erfordern, dass alle `asyncio`-Tasks über den Qt-Loop laufen; UI-Widgets sollten lange Operationen stets auslagern (z.B. `asyncio.create_task`).

