# OrderPilot-AI Architektur

## Schichtenmodell

```
┌─────────────────────────────────────────────────────────────┐
│                        UI Layer                             │
│  src/ui/app.py ── TradingApplication (QMainWindow)          │
│  src/ui/widgets/ ── Charts, Dialogs, Panels                 │
│  src/ui/dialogs/ ── Modale Dialoge                          │
└─────────────────────────┬───────────────────────────────────┘
                          │ ruft auf
┌─────────────────────────▼───────────────────────────────────┐
│                     Service Layer                           │
│  src/core/market_data/ ── HistoryManager, Provider, Errors  │
│  src/core/strategy/ ── Engine, Compiler, Evaluation         │
│  src/core/trading/ ── Order-Execution (TODO)                │
└─────────────────────────┬───────────────────────────────────┘
                          │ verwendet
┌─────────────────────────▼───────────────────────────────────┐
│                    Broker Adapter                           │
│  src/brokers/alpaca/ ── REST + Streaming Clients            │
│  src/brokers/ibkr/ ── Interactive Brokers (optional)        │
└─────────────────────────────────────────────────────────────┘

## Event-Bus Architektur

Der zentrale Event-Bus (src/common/event_bus.py) verbindet alle Komponenten:

```
Publisher                    Event-Bus                    Subscriber
─────────                    ─────────                    ──────────
AlpacaStreamClient  ──────▶  MARKET_TICK  ──────▶  EmbeddedTradingViewChart
                             MARKET_BAR   ──────▶  IndicatorMixin
                             ORDER_UPDATE ──────▶  PositionsPanel
```

### Event-Typen
- `MARKET_TICK` - Echtzeit-Preisupdate (Trades)
- `MARKET_BAR` - Komplettierte Kerze
- `ORDER_UPDATE` - Orderstatusänderung
- `POSITION_UPDATE` - Positionsänderung
- `ACCOUNT_UPDATE` - Kontostand-Änderung

## Datenfluss: Chart laden

```
1. User klickt "Load Chart"
   │
2. EmbeddedTradingViewChart.load_symbol(symbol)
   │
3. HistoryManager.fetch_data(DataRequest)
   │
4. Provider auswählen (Alpaca/Yahoo/Database)
   │
5. Daten in DataFrame konvertieren
   │
6. EmbeddedTradingViewChart.load_data(df)
   │
7. JavaScript chartAPI.setData() aufrufen
```

## Mixin-Pattern

Große Klassen sind in Mixins aufgeteilt für bessere Wartbarkeit:

### EmbeddedTradingViewChart (src/ui/widgets/embedded_tradingview_chart.py)
```
EmbeddedTradingViewChart
├── ToolbarMixin      - UI-Toolbar (Symbol, Timeframe, Buttons)
├── IndicatorMixin    - Technische Indikatoren (SMA, RSI, etc.)
├── StreamingMixin    - Live-Daten (WebSocket-Events)
├── DataLoadingMixin  - Datenladen (load_data, load_symbol)
└── ChartStateMixin   - Zustandsverwaltung (visible range, panes)
```

### ChartWindow (src/ui/widgets/chart_window.py)
```
ChartWindow
├── PanelsMixin       - Tab-Panels (Strategy, Backtest, etc.)
├── BacktestMixin     - Backtest-Ausführung
├── EventBusMixin     - Event-Bus Integration
└── StateMixin        - State Save/Restore
```

### EntryAnalyzerPopup (src/ui/dialogs/entry_analyzer/entry_analyzer_popup.py)
```
EntryAnalyzerPopup
├── BacktestMixin     - Backtest-Setup, Regime-Analyse, Regime-Set Erstellung
├── IndicatorsMixin   - Indikator-Optimierung + Presets
├── AnalysisMixin     - Visible Range + Validation
└── AIMixin           - AI Copilot + Pattern Recognition
```

### TradingApplication (src/ui/app.py)
```
TradingApplication
├── MenuMixin         - Menüleiste
├── ToolbarMixin      - Haupttoolbar
└── BrokerMixin       - Broker-Verbindung
```

## Workspace Manager Pattern (UI Refactoring 2026-01)

Das UI wurde refaktorisiert zum **Workspace Manager Pattern**:

### Architektur-Übersicht

```
┌─────────────────────────────────────────────────────────────┐
│              TradingApplication (Workspace Manager)          │
│  Compact Control Panel (400x600) - Minimiert in Taskbar     │
│  ├── Broker-Auswahl + Connect/Disconnect                    │
│  ├── WatchlistWidget (zentral)                              │
│  └── Menübar für globale Aktionen                           │
└─────────────────────────┬───────────────────────────────────┘
                          │ öffnet/verwaltet
┌─────────────────────────▼───────────────────────────────────┐
│              ChartWindow (Primary Interface)                 │
│  Standalone QMainWindow - Multi-Monitor fähig               │
│  ├── Toolbar mit Broker Mirror Controls                     │
│  ├── Chart Widget (TradingView)                             │
│  ├── Watchlist Dock (shared Model)                          │
│  ├── Activity Log Dock (symbol-gefiltert)                   │
│  └── Context Menu (Settings, Docks, Workspace)              │
└─────────────────────────────────────────────────────────────┘
```

### Singleton Services

Zentralisierte, thread-sichere Services für geteilte Zustände:

```
┌─────────────────────────────────────────────────────────────┐
│                     BrokerService                            │
│  src/core/broker/broker_service.py                          │
├─────────────────────────────────────────────────────────────┤
│  - Singleton: get_broker_service()                          │
│  - Thread-safe: asyncio.Lock für connect/disconnect         │
│  - Events: MARKET_CONNECTED / MARKET_DISCONNECTED           │
│  - Unterstützt: Mock, IBKR, TR, Alpaca, Bitunix            │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                     WatchlistModel                           │
│  src/ui/models/watchlist_model.py                           │
├─────────────────────────────────────────────────────────────┤
│  - Singleton: WatchlistModel.instance()                     │
│  - QAbstractTableModel für Qt Model-View Pattern            │
│  - Automatische UI-Synchronisation via dataChanged          │
│  - Signals: symbol_added, symbol_removed, symbols_changed   │
│  - Persistenz: save_to_settings() / load_from_settings()    │
└─────────────────────────────────────────────────────────────┘
```

### Event-Bus mit Filter-Support

```python
# Subscription mit optionalem Filter (Phase 0 Enhancement)
event_bus.subscribe(
    EventType.ORDER_FILLED,
    handler=self._on_order_filled,
    filter=lambda e: e.data.get("symbol") == self.symbol
)
```

### ChartWindow Enhanced Features

```
ChartWindow
├── Broker Mirror Controls  - Connect/Disconnect Buttons in Toolbar
├── Watchlist Dock          - Rechts angedockt, shared WatchlistModel
├── Activity Log Dock       - Unten angedockt, symbol-gefiltert
├── Context Menu            - Rechtsklick: Settings, Docks, Workspace
├── Keyboard Shortcuts      - Ctrl+, (Settings), Ctrl+Shift+W (Workspace)
└── Enhanced Session State  - Speichert/lädt:
    ├── Window Geometry
    ├── Dock Visibility (Watchlist, Activity Log)
    ├── Active Timeframe + Period
    └── Crosshair Sync Status
```

### Session Persistence Flow

```
┌─────────────────┐    save_enhanced_session_state()   ┌─────────────────┐
│  ChartWindow    │ ─────────────────────────────────▶ │   QSettings     │
│  closes         │                                     │   (Registry)    │
└─────────────────┘                                     └─────────────────┘
                                                               │
┌─────────────────┐    _restore_enhanced_session_state() ◀─────┘
│  ChartWindow    │ ◀──────────────────────────────────────────
│  opens          │    restore_after_state_load()
└─────────────────┘
```

## Provider-Pattern

Datenquellen sind als Provider abstrahiert:

```
HistoricalDataProvider (Abstract Base)
├── AlpacaProvider         - Alpaca Stock API
├── AlpacaCryptoProvider   - Alpaca Crypto API
├── BitunixProvider        - Bitunix Futures API (NEW)
├── YahooFinanceProvider   - yfinance
├── AlphaVantageProvider   - Alpha Vantage API
├── FinnhubProvider        - Finnhub API
├── IBKRHistoricalProvider - Interactive Brokers
└── DatabaseProvider       - Lokale SQLite DB
```

## Derivatives Module (KO-Finder)

Das Derivatives-Modul ermöglicht die Suche nach Knock-Out Produkten.
**Einzige Datenquelle: Onvista** (keine Alternativen erlaubt).

### Architektur (Ports & Adapters)

```
┌─────────────────────────────────────────────────────────────┐
│                       UI Layer                               │
│  KOFilterPanel ── Filter-Controls (Hebel, Spread, etc.)     │
│  KOResultPanel ── Ergebnis-Tabellen (Long/Short Tabs)       │
│  KOFinderMixin ── ChartWindow Integration                    │
└─────────────────────────┬───────────────────────────────────┘
                          │ ruft auf
┌─────────────────────────▼───────────────────────────────────┐
│                   KOFinderService                            │
│  Orchestrierung: Fetch → Parse → Filter → Rank → Cache      │
└─────────────────────────┬───────────────────────────────────┘
                          │ verwendet
┌─────────────────────────▼───────────────────────────────────┐
│                  Engine Components                           │
│  HardFilters ── Ausschluss (Hebel, Spread, KO-Abstand)      │
│  RankingEngine ── Score-Berechnung (deterministisch)        │
│  CacheManager ── Stale-While-Revalidate                     │
└─────────────────────────┬───────────────────────────────────┘
                          │ ruft auf
┌─────────────────────────▼───────────────────────────────────┐
│                  Onvista Adapter                             │
│  OnvistaURLBuilder ── URL-Generierung                       │
│  OnvistaFetcher ── HTTP + Rate-Limit + Circuit-Breaker      │
│  OnvistaParser ── HTML → Models (Header-basiert)            │
│  OnvistaNormalizer ── Zahlen, Plausibilität, Flags          │
└─────────────────────────────────────────────────────────────┘
```

### Datenfluss: KO-Finder Refresh

```
1. User klickt "Aktualisieren"
   │
2. KOFinderMixin._on_ko_refresh()
   │
3. KOFinderService.search(underlying, config)
   │
4. Parallel: OnvistaFetcher.fetch(long_url), fetch(short_url)
   │
5. OnvistaParser.parse(html, direction)
   │
6. OnvistaNormalizer.normalize_products(products)
   │
7. HardFilters.apply(products) → Ausschluss
   │
8. RankingEngine.rank(products, top_n) → Score + Sort
   │
9. SearchResponse → UI Update
```

### Modulstruktur (max 600 LOC/Datei)

```
src/derivatives/ko_finder/
├── __init__.py              # Public API
├── models.py                # KnockoutProduct, Quote, SearchResponse
├── config.py                # KOFilterConfig + QSettings
├── constants.py             # Issuer-IDs, URLs, Defaults
├── service.py               # KOFinderService (Orchestrierung)
├── adapter/
│   ├── url_builder.py       # URL-Generierung
│   ├── fetcher.py           # HTTP-Client + Rate-Limit
│   ├── parser.py            # HTML → Models
│   └── normalizer.py        # Daten-Bereinigung
└── engine/
    ├── filters.py           # HardFilters
    ├── ranking.py           # RankingEngine + Score
    └── cache.py             # CacheManager + SWR
```

### UI Integration

```
ChartWindow
├── BotPanelsMixin
├── KOFinderMixin      [NEU] ← KO-Finder Tab
├── PanelsMixin        ← Registriert Tab
├── EventBusMixin
└── StateMixin

src/ui/widgets/ko_finder/
├── table_model.py     # QAbstractTableModel
├── filter_panel.py    # Filter-Controls
└── result_panel.py    # Tabellen + Meta-Info
```

## Chart-Marking Modul

Das Chart-Marking-Modul (`src/chart_marking/`) bietet einheitliche Chart-Markierungsfunktionen.

### Architektur

```
┌─────────────────────────────────────────────────────────────┐
│                    EmbeddedTradingViewChart                  │
│               + ChartMarkingMixin                            │
└─────────────────────────┬───────────────────────────────────┘
                          │ verwendet
┌─────────────────────────▼───────────────────────────────────┐
│                  Manager-Komponenten                         │
│  EntryMarkerManager  - Entry Pfeile (Long/Short)            │
│  StructureMarkerManager - BoS/CHoCH/MSB Marker              │
│  ZoneManager         - Support/Resistance Zonen             │
│  StopLossLineManager - Stop-Loss/TP Linien                  │
└─────────────────────────┬───────────────────────────────────┘
                          │ ruft auf
┌─────────────────────────▼───────────────────────────────────┐
│                  JavaScript Chart API                        │
│  window.chartAPI.addTradeMarkers()                          │
│  window.chartAPI.addZone() / clearZones()                   │
│  window.chartAPI.addHorizontalLine()                        │
└─────────────────────────────────────────────────────────────┘
```

### Modulstruktur

```
src/chart_marking/
├── __init__.py              # Public API + Exports
├── models.py                # Datenmodelle (EntryMarker, Zone, etc.)
├── constants.py             # Farben, Styles, Größen
│
├── markers/
│   ├── entry_markers.py     # Entry-Pfeile (Long/Short)
│   └── structure_markers.py # BoS/CHoCH/MSB Marker
│
├── zones/
│   ├── zone_primitive_js.py # JavaScript für Rechteck-Rendering
│   └── support_resistance.py # Zone-Management
│
├── lines/
│   └── stop_loss_line.py    # SL/TP/Entry Linien
│
├── mixin/
│   └── chart_marking_mixin.py # Haupt-Mixin für Chart-Widget
│
└── multi_chart/             # Multi-Chart/Multi-Monitor
    ├── layout_manager.py    # Layout-Presets + Persistenz
    ├── crosshair_sync.py    # Crosshair-Synchronisation
    └── multi_monitor_manager.py # Fenster-Verwaltung
```

### Multi-Chart Funktionalität

```
┌─────────────────────────────────────────────────────────────┐
│                  MultiMonitorChartManager                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  LayoutManager                                              │
│  ├── save_layout() - Layout speichern                       │
│  ├── load_layout() - Layout laden                           │
│  ├── list_layouts() - Alle Layouts auflisten                │
│  └── capture_current_layout() - Fenster erfassen            │
│                                                             │
│  CrosshairSyncManager                                       │
│  ├── register_window() - Chart registrieren                 │
│  ├── on_crosshair_move() - Sync an andere Charts            │
│  └── set_enabled() - Sync ein/aus                           │
│                                                             │
│  Window Management                                          │
│  ├── open_chart() - Neues Fenster öffnen                    │
│  ├── apply_layout() - Layout anwenden                       │
│  └── tile_on_monitor() - Fenster anordnen                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Datenmodelle

```python
# Entry Marker
EntryMarker(id, timestamp, price, direction, text, score)

# Support/Resistance Zone
Zone(id, zone_type, start_time, end_time, top_price, bottom_price, opacity)

# Structure Break
StructureBreakMarker(id, timestamp, price, break_type, direction)

# Stop-Loss Line
StopLossLine(id, price, entry_price, direction, show_risk)

# Multi-Chart Layout
MultiChartLayout(id, name, charts: List[ChartConfig], sync_crosshair)
ChartConfig(symbol, timeframe, monitor, position)
```

### JavaScript Integration

Zone-Primitives werden via `get_chart_html_template()` in das Chart injiziert:

```javascript
// Zone API
window.chartAPI.addZone(id, startTime, endTime, topPrice, bottomPrice, fillColor, borderColor, label)
window.chartAPI.updateZone(id, startTime, endTime, topPrice, bottomPrice)
window.chartAPI.removeZone(id)
window.chartAPI.clearZones()

// Marker API (v5)
window.chartAPI.addTradeMarkers(markers)
window.chartAPI.clearMarkers()

// Line API
window.chartAPI.addHorizontalLine(price, color, label, lineStyle, id)
```

## Chart Analysis Chatbot

Das Chart-Chat-Modul (`src/chart_chat/`) bietet KI-gestützte Chart-Analyse und Konversation.

### Architektur

```
┌─────────────────────────────────────────────────────────────┐
│                    ChartWindow                               │
│                + ChartChatMixin                              │
└─────────────────────────┬───────────────────────────────────┘
                          │ erstellt
┌─────────────────────────▼───────────────────────────────────┐
│                  ChartChatWidget (QDockWidget)               │
│  - Chat Display (Markdown)                                  │
│  - Quick Actions (Trend, Support, Entry)                    │
│  - Input Field + Send                                       │
│  - Export / Clear History                                   │
└─────────────────────────┬───────────────────────────────────┘
                          │ verwendet
┌─────────────────────────▼───────────────────────────────────┐
│                  ChartChatService                            │
│  - Conversation Management                                  │
│  - History Persistence (pro Fenster: Symbol + Timeframe)    │
│  - Chart Context Extraction                                 │
└─────────────────────────┬───────────────────────────────────┘
                          │ orchestriert
┌─────────────────────────▼───────────────────────────────────┐
│                  Service Components                          │
│  ChartContextBuilder - OHLCV + Indicators extrahieren       │
│  ChartAnalyzer - KI-Aufrufe für Analyse + Q&A               │
│  HistoryStore - JSON-Persistenz (FIFO, max 50 msgs)         │
└─────────────────────────┬───────────────────────────────────┘
                          │ verwendet
┌─────────────────────────▼───────────────────────────────────┐
│                  AI Provider (AIProviderFactory)             │
│  OpenAIProvider / AnthropicProvider / GeminiProvider        │
└─────────────────────────────────────────────────────────────┘
```

### Modulstruktur

```
src/chart_chat/
├── __init__.py              # Public API + Exports
├── models.py                # ChatMessage, ChartAnalysisResult, etc.
├── prompts.py               # System Prompts, Templates
├── context_builder.py       # ChartContext, ChartContextBuilder
├── history_store.py         # HistoryStore (JSON Persistenz)
├── analyzer.py              # ChartAnalyzer (KI-Aufrufe)
├── chat_service.py          # ChartChatService (Orchestrierung)
├── widget.py                # ChartChatWidget (QDockWidget)
└── mixin.py                 # ChartChatMixin (Integration)
```

### Datenfluss: Chat-Anfrage

```
1. User stellt Frage im Chat Widget
   │
2. ChartChatService.ask_question(question)
   │
3. ChartContextBuilder.build_context()
   │  - Extrahiert OHLCV aus chart.data
   │  - Berechnet aktive Indikatoren (RSI, MACD, BB, etc.)
   │  - Ermittelt Trend, Volatilität, Volume-Trend
   │
4. ChartAnalyzer.answer_question(question, context, history)
   │  - Formatiert Prompt mit Kontext + Historie
   │  - Ruft AI Provider auf
   │
5. QuickAnswerResult → Widget zeigt Antwort
   │
6. HistoryStore.save_history() → JSON Persistenz
```

### Datenfluss: Vollständige Analyse

```
1. User klickt "Vollständige Analyse"
   │
2. ChartChatService.analyze_chart()
   │
3. ChartContextBuilder.build_context(lookback=100)
   │
4. ChartAnalyzer.analyze_chart(context)
   │  - System Prompt für technische Analyse
   │  - Strukturierte JSON-Ausgabe
   │
5. ChartAnalysisResult (Pydantic Model)
   │  - trend_direction, trend_strength
   │  - support_levels, resistance_levels
   │  - recommendation (action, confidence, reasoning)
   │  - risk_assessment (stop_loss, take_profit, R:R)
   │  - patterns_identified
   │
6. result.to_markdown() → Widget Anzeige
```

### History Persistenz

```
Speicherort: ~/.orderpilot/chat_history/
Dateiformat: {symbol}_{timeframe}.json

Beispiel: BTC_USD_1H.json
{
  "symbol": "BTC/USD",
  "timeframe": "1H",
  "updated_at": "2025-01-15T14:30:00",
  "messages": [
    {"role": "user", "content": "...", "timestamp": "..."},
    {"role": "assistant", "content": "...", "timestamp": "..."}
  ]
}

FIFO: Max 50 Nachrichten pro Chart
```

### Datenmodelle

```python
# Chat Message
ChatMessage(id, role, content, timestamp, metadata)

# Analysis Result
ChartAnalysisResult(
    trend_direction: TrendDirection,    # bullish/bearish/neutral
    trend_strength: SignalStrength,     # strong/moderate/weak
    support_levels: List[SupportResistanceLevel],
    resistance_levels: List[SupportResistanceLevel],
    recommendation: EntryExitRecommendation,
    risk_assessment: RiskAssessment,
    patterns_identified: List[PatternInfo],
    indicator_summary: str,
    overall_sentiment: str,
    confidence_score: float             # 0.0-1.0
)

# Quick Answer
QuickAnswerResult(answer, confidence, follow_up_suggestions)
```

### UI Integration

```
ChartWindow
├── BotPanelsMixin
├── KOFinderMixin
├── StrategySimulatorMixin
├── PanelsMixin
├── EventBusMixin
├── StateMixin
├── ChartChatMixin      [NEU] ← Chart Chat Widget
└── QMainWindow

Features:
- Dockbar rechts am Chart
- Quick Actions: Trend, Support, Entry, Risiken
- Vollständige Analyse mit Markdown-Output
- Chat-Export als Markdown
- Automatisches History-Loading bei Symbol-Wechsel
```

## AI Market Analysis Module

Das AI Analysis Modul (`src/core/ai_analysis/`) bietet eine tiefgehende Marktstrukturanalyse als Popup.
Es ist **isoliert vom Trading** (Read-Only) und fokussiert auf Setup-Erkennung.

### Architektur

```
┌─────────────────────────────────────────────────────────────┐
│                    AIAnalysisWindow (Popup)                  │
│                + src/ui/ai_analysis_window.py                │
└─────────────────────────┬───────────────────────────────────┘
                          │ ruft auf
┌─────────────────────────▼───────────────────────────────────┐
│                   AIAnalysisEngine                           │
│  Orchestrator: Data → Validator → Regime → Features → LLM   │
└─────────────────────────┬───────────────────────────────────┘
                          │ verwendet
┌─────────────────────────▼───────────────────────────────────┐
│                  Core Components                             │
│  DataValidator - Pre-Flight Checks (Lag, Bad Ticks)         │
│  RegimeDetector - Deterministische Marktphasen (Bull/Bear)  │
│  FeatureEngineer - Technische Features (RSI, Struct, Pivots)│
│  PromptComposer - JSON-Prompt Generierung                   │
│  OpenAIClient - Async API Wrapper (mit Retries)             │
└─────────────────────────────────────────────────────────────┘
```

### Datenfluss

```
1. User klickt "AI Analyse" im Chart
   │
2. AIAnalysisWindow.start_analysis()
   │
3. DataValidator.validate_data(df) → Check Lag/Volume
   │
4. RegimeDetector.detect_regime(df) → "STRONG_TREND_BULL"
   │
5. FeatureEngineer.extract_features(df) → RSI State, Pivots
   │
6. PromptComposer.compose_prompt(input_json)
   │
7. OpenAIClient.analyze(prompt) → LLM
   │
8. AIAnalysisOutput (JSON) → UI Anzeige
```

## Analysis & AI Modules

### Visible Chart Analyzer (`src/analysis/visible_chart/`)
- **Analyzer**: Orchestriert die Analyse des sichtbaren Chartbereichs.
- **Background Runner**: Führt Analysen im Hintergrund durch (Full & Incremental).
- **Optimization**: `src/analysis/indicator_optimization/` für Parameter-Optimierung.
    - `candidate_space.py`: Definiert Parameter-Bereiche.
    - `optimizer.py`: Fast Random Search Optimizer.
- **Entry Signals**: `src/analysis/entry_signals/` (Core Logic).

### AI Copilot (`src/analysis/visible_chart/entry_copilot.py`)
- KI-gestützte Analyse von Signalen.
- Generierung von Trading-Empfehlungen.

## Verzeichnisstruktur

```
src/
├── analysis/             # Analyse-Module [NEU]
│   ├── visible_chart/    # Live-Analyse des sichtbaren Bereichs
│   ├── indicator_optimization/ # Parameter-Optimierung
│   ├── entry_signals/    # Core Signal Logic
│   └── regime/           # Markterkennung
├── brokers/              # Deprecated - wird migriert
├── common/               # Shared Utilities
│   ├── event_bus.py      # Globaler Event-Bus
│   ├── logging_setup.py  # Logging-Konfiguration
│   └── security.py       # API-Key Verwaltung
├── core/                 # Business Logic
│   ├── market_data/      # Marktdaten
│   │   ├── history_provider.py
│   │   ├── alpaca_stream.py
│   │   ├── bitunix_stream.py           # NEW - Bitunix WebSocket
│   │   ├── stream_client.py
│   │   └── providers/    # Datenquellen
│   │       ├── alpaca_stock_provider.py
│   │       ├── bitunix_provider.py     # NEW - Bitunix REST API
│   │       ├── yahoo_provider.py
│   │       └── ...
│   ├── broker/           # Broker Trading Adapters
│   │   ├── base.py       # BrokerAdapter (Abstract Base)
│   │   ├── alpaca_adapter.py
│   │   ├── bitunix_adapter.py          # NEW - Bitunix Trading API
│   │   └── broker_types.py
│   ├── strategy/         # Strategien
│   │   ├── engine.py     # Strategie-Engine
│   │   ├── compiler.py   # DSL-Compiler
│   │   └── strategies/   # Strategie-Implementierungen
│   └── tradingbot/       # Automatisierter Trading Bot [NEU]
│       ├── config.py           # BotConfig, RiskConfig, LLMPolicyConfig
│       ├── models.py           # DTOs (FeatureVector, Signal, Position, etc.)
│       ├── state_machine.py    # Bot State Machine (7 States, 18 Triggers)
│       ├── bot_controller.py   # Main Controller
│       ├── feature_engine.py   # Feature Calculation (IndicatorEngine Integration)
│       ├── regime_engine.py    # Regime Classification (Trend/Range + Volatility)
│       ├── no_trade_filter.py  # Trade Filtering (Vol, Volume, Time, Risk)
│       ├── strategy_catalog.py # Pre-built Strategy Definitions (8 Strategies)
│       ├── strategy_evaluator.py # Walk-Forward Analysis + Metrics
│       ├── strategy_selector.py  # Daily Strategy Selection
│       ├── entry_exit_engine.py  # Entry Scoring, Exit Signals, Trailing Stops
│       ├── execution.py          # Position Sizing, Risk Manager, Paper Executor
│       ├── llm_integration.py    # OpenAI Integration mit Guardrails
│       ├── backtest_harness.py   # Reproduzierbarer Backtest + Release Gate
│       └── bot_tests.py          # Unit/Integration/Chaos Tests
├── derivatives/          # Derivate-Module [NEU]
│   └── ko_finder/        # KO-Finder (Onvista-only)
│       ├── models.py     # KnockoutProduct, Quote, SearchResponse
│       ├── config.py     # KOFilterConfig
│       ├── constants.py  # Issuer-IDs, URLs
│       ├── service.py    # KOFinderService
│       ├── adapter/      # Onvista-Adapter
│       │   ├── url_builder.py
│       │   ├── fetcher.py
│       │   ├── parser.py
│       │   └── normalizer.py
│       └── engine/       # Filter, Ranking, Cache
│           ├── filters.py
│           ├── ranking.py
│           └── cache.py
├── chart_marking/        # Chart-Markierungen
│   ├── models.py         # Datenmodelle
│   ├── constants.py      # Farben, Styles
│   ├── markers/          # Entry/Structure Marker
│   ├── zones/            # Support/Resistance Zonen
│   ├── lines/            # Stop-Loss/TP Linien
│   ├── mixin/            # ChartMarkingMixin
│   └── multi_chart/      # Multi-Monitor Support
│       ├── layout_manager.py
│       ├── crosshair_sync.py
│       └── multi_monitor_manager.py
├── chart_chat/           # KI Chart-Analyse Chatbot [NEU]
│   ├── models.py         # ChatMessage, ChartAnalysisResult
│   ├── prompts.py        # System Prompts, Templates
│   ├── context_builder.py # Chart Context Extraktion
│   ├── history_store.py  # JSON Persistenz (pro Fenster)
│   ├── analyzer.py       # KI-Aufrufe
│   ├── chat_service.py   # Orchestrierung
│   ├── widget.py         # QDockWidget UI
│   ├── chart_chat_worker.py
│   ├── chart_chat_ui_mixin.py
│   ├── chart_chat_history_mixin.py
│   ├── chart_chat_actions_mixin.py
│   ├── chart_chat_export_mixin.py
│   ├── chart_chat_events_mixin.py
│   └── mixin.py          # ChartChatMixin
├── ai/                   # AI Services
│   ├── openai_service.py # OpenAI Integration
│   ├── openai_service_client_mixin.py
│   ├── openai_service_analysis_mixin.py
│   └── openai_service_prompt_mixin.py
│   └── anthropic_service.py
└── ui/                   # User Interface
    ├── app.py            # Hauptfenster
    ├── app_components/   # App-Mixins
    │   ├── app_ui_mixin.py
    │   ├── app_events_mixin.py
    │   ├── app_timers_mixin.py
    │   ├── app_settings_mixin.py
    │   ├── app_chart_mixin.py
    │   ├── app_broker_events_mixin.py
    │   ├── app_refresh_mixin.py
    │   └── app_lifecycle_mixin.py
    ├── app_console_utils.py
    ├── app_logging.py
    ├── app_resources.py
    ├── app_startup_window.py
    ├── widgets/          # Wiederverwendbare Widgets
    │   ├── embedded_tradingview_chart.py
    │   ├── embedded_tradingview_bridge.py
    │   ├── embedded_tradingview_chart_ui_mixin.py
    │   ├── embedded_tradingview_chart_marking_mixin.py
    │   ├── embedded_tradingview_chart_js_mixin.py
    │   ├── embedded_tradingview_chart_view_mixin.py
    │   ├── embedded_tradingview_chart_loading_mixin.py
    │   ├── embedded_tradingview_chart_events_mixin.py
    │   ├── chart_mixins/ # Chart-Mixins
    │   └── chart_window_mixins/
    │       ├── bot_display_manager.py
    │       ├── bot_display_selection_mixin.py
    │       ├── bot_display_position_mixin.py
    │       ├── bot_display_signals_mixin.py
    │       ├── bot_display_logging_mixin.py
    │       ├── bot_display_metrics_mixin.py
    │       ├── bot_ui_panels.py
    │       ├── bot_ui_control_mixin.py
    │       ├── bot_ui_strategy_mixin.py
    │       ├── bot_ui_signals_mixin.py
    │       ├── bot_ui_ki_logs_mixin.py
    │       ├── bot_position_persistence.py
    │       ├── bot_position_persistence_storage_mixin.py
    │       ├── bot_position_persistence_restore_mixin.py
    │       ├── bot_position_persistence_pnl_mixin.py
    │       ├── bot_position_persistence_context_mixin.py
    │       ├── bot_position_persistence_chart_mixin.py
    │       ├── bot_callbacks.py
    │       ├── bot_callbacks_lifecycle_mixin.py
    │       ├── bot_callbacks_signal_mixin.py
    │       ├── bot_callbacks_log_order_mixin.py
    │       └── bot_callbacks_candle_mixin.py
    │       ├── strategy_simulator_mixin.py
    │       ├── strategy_simulator_ui_mixin.py
    │       ├── strategy_simulator_params_mixin.py
    │       ├── strategy_simulator_run_mixin.py
    │       ├── strategy_simulator_results_mixin.py
    │       └── strategy_simulator_worker.py
    └── dialogs/          # Modale Dialoge
        ├── pattern_db_dialog.py
        ├── pattern_db_ui_mixin.py
        ├── pattern_db_settings_mixin.py
        ├── pattern_db_docker_mixin.py
        ├── pattern_db_build_mixin.py
        ├── pattern_db_log_mixin.py
        ├── pattern_db_search_mixin.py
        └── pattern_db_lifecycle_mixin.py
```

## Tradingbot-Architektur [NEU]

### State Machine

```
FLAT ────▶ SIGNAL ────▶ ENTERED ────▶ MANAGE ────▶ EXITED
  │           │            │            │            │
  │           └──expire────┘            │            │
  │                        │            │            │
  └────────────────────────┴────────────┴────────────┘
                              (reset/candle_close)

  + PAUSED (manual pause)
  + ERROR (error handling)
```

### Bot-Datenfluss

```
1. MARKET_BAR Event (Candle Close)
   │
2. BotController.on_bar(bar)
   │
3. FeatureEngine → FeatureVector
   │
4. RegimeEngine → RegimeState (Trend/Range + Vol)
   │
5. State-abhängige Verarbeitung:
   ├── FLAT → Entry-Scoring → Signal?
   ├── SIGNAL → Confirm/Expire → Entry Order?
   └── MANAGE → Trailing Stop → Exit Signal?
   │
6. BotDecision → Event-Bus / Callbacks
```

### Trailing Stop Varianten

1. **PCT (Prozent-basiert)**: Fester Abstand in % vom Höchst-/Tiefstpreis
2. **ATR (Volatilitäts-basiert)**: ATR-Multiple, angepasst an Regime
3. **SWING (Struktur-basiert)**: Bollinger Bands als Support/Resistance

### Data Pipeline (Feature & Regime Engines)

```
FeatureEngine                         RegimeEngine
─────────────                         ────────────
┌─────────────┐                       ┌─────────────┐
│ OHLCV Data  │                       │FeatureVector│
└──────┬──────┘                       └──────┬──────┘
       │                                     │
       ▼                                     ▼
┌─────────────────┐                   ┌─────────────────┐
│ IndicatorEngine │                   │ ADX/DI Analysis │
│ (SMA,EMA,RSI,   │                   │ ATR% Analysis   │
│  MACD,BB,ATR,   │                   │ BB Width Check  │
│  ADX,Stoch,etc.)│                   └────────┬────────┘
└────────┬────────┘                            │
         │                                     ▼
         ▼                              ┌─────────────┐
  ┌─────────────────┐                   │ RegimeState │
  │  FeatureVector  │                   │ - regime    │
  │  - indicators   │                   │ - volatility│
  │  - derived      │                   │ - confidence│
  │  - normalized   │                   └─────────────┘
  └─────────────────┘
```

### No-Trade Filter

```
┌─────────────────────────────────────────────────────┐
│                  NoTradeFilter                       │
├─────────────────────────────────────────────────────┤
│ Layer 1: Volatility     │ ATR%, Extreme Vol Regime  │
│ Layer 2: Liquidity      │ Volume Ratio < threshold  │
│ Layer 3: Time           │ NASDAQ RTH, First/Last min│
│ Layer 4: Risk Limits    │ Max trades, Loss limits   │
│ Layer 5: Technical      │ RSI extremes              │
│ Layer 6: Regime Change  │ Trend flip, Vol spike     │
└─────────────────────────────────────────────────────┘
```

### Daily Strategy Selection

```
┌─────────────────────────────────────────────────────────────┐
│                    StrategyCatalog                          │
│  8 Pre-built Strategies:                                    │
│  ├── trend_following_conservative                           │
│  ├── trend_following_aggressive                             │
│  ├── mean_reversion_bb                                      │
│  ├── mean_reversion_rsi                                     │
│  ├── breakout_volatility                                    │
│  ├── breakout_momentum                                      │
│  ├── momentum_macd                                          │
│  └── scalping_range                                         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   StrategyEvaluator                         │
│  Walk-Forward Analysis:                                     │
│  ├── Rolling/Anchored Windows                               │
│  ├── In-Sample Training (30 days default)                   │
│  ├── Out-of-Sample Testing (7 days default)                 │
│  └── Robustness Gate: min_trades, profit_factor, max_dd     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   StrategySelector                          │
│  Daily Selection:                                           │
│  ├── Filter by applicable regime                            │
│  ├── Rank by composite score                                │
│  ├── Lock selection for day (optional intraday switch)      │
│  └── Persist selection snapshots                            │
└─────────────────────────────────────────────────────────────┘
```

### Entry/Exit Engine

```
┌─────────────────────────────────────────────────────────────┐
│                    EntryExitEngine                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  EntryScorer                                                │
│  ├── 7 Score Components (0-100):                            │
│  │   ├── trend_alignment (MA direction)                     │
│  │   ├── momentum_rsi (RSI divergence)                      │
│  │   ├── momentum_macd (MACD histogram)                     │
│  │   ├── trend_strength (ADX)                               │
│  │   ├── mean_reversion (BB %B)                             │
│  │   ├── volume_confirmation (Volume Ratio)                 │
│  │   └── regime_match (Strategy fit)                        │
│  └── Configurable weights per component                     │
│                                                             │
│  ExitSignalChecker                                          │
│  ├── RSI Extreme Exit                                       │
│  ├── MACD Cross Against Position                            │
│  ├── Trend Break (MA Cross)                                 │
│  ├── Volatility Spike Exit                                  │
│  ├── Regime Flip Exit                                       │
│  └── Time Stop (max bars held)                              │
│                                                             │
│  TrailingStopManager                                        │
│  ├── PCT Mode (percentage-based)                            │
│  ├── ATR Mode (volatility-based, regime-adjusted)           │
│  └── SWING Mode (BB support/resistance)                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Execution Layer

```
┌─────────────────────────────────────────────────────────────┐
│                    OrderExecutor                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  PositionSizer                                              │
│  ├── Fixed Fractional (% of account per trade)              │
│  ├── ATR-Based (volatility-adjusted sizing)                 │
│  └── Constraints: MAX_RISK, MAX_POSITION_SIZE               │
│                                                             │
│  RiskManager                                                │
│  ├── Daily Limits: trades/day, daily_loss_pct              │
│  ├── Position Limits: max_concurrent_positions              │
│  ├── Loss Streak Cooldown (auto-pause after N losses)       │
│  └── can_trade() → (allowed, blocking_reasons)              │
│                                                             │
│  ExecutionGuardrails                                        │
│  ├── Max/Min Order Value                                    │
│  ├── Rate Limiting (per minute)                             │
│  ├── Stop-Loss Required for Entries                         │
│  └── Duplicate Signal Prevention                            │
│                                                             │
│  PaperExecutor                                              │
│  ├── Slippage Simulation                                    │
│  ├── Fill Probability                                       │
│  ├── Fee Calculation                                        │
│  └── Order Tracking                                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### KI-Integration (optional)

```
KIMode.NO_KI   → Rein regelbasiert
KIMode.LOW_KI  → Daily Strategy Selection (1 Call/Tag)
KIMode.FULL_KI → Daily + Intraday Events

LLM Response → JSON Schema Validation → Fallback auf Regelwerk
```

```
┌─────────────────────────────────────────────────────────────┐
│                    LLMIntegration                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  LLMPromptBuilder                                           │
│  ├── DAILY_STRATEGY_TEMPLATE                                │
│  ├── TRADE_DECISION_TEMPLATE                                │
│  └── Structured features (no free-form text)                │
│                                                             │
│  LLMResponseValidator                                       │
│  ├── Pydantic Schema Validation                             │
│  ├── Auto-Repair (action, confidence, reason_codes)         │
│  └── get_fallback_response() für sichere Defaults           │
│                                                             │
│  Call Policy                                                │
│  ├── Daily: Max 1 Strategy Selection Call                   │
│  ├── Intraday: RegimeFlip, ExitCandidate, SignalChange      │
│  └── Budget: max_daily_calls, daily_budget_usd              │
│                                                             │
│  Safety & Audit                                             │
│  ├── Rate Limiting (per minute)                             │
│  ├── Consecutive Error Backoff                              │
│  ├── Prompt/Response Hashing                                │
│  └── Full Audit Trail (LLMCallRecord)                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### UI Bot Integration

```
┌─────────────────────────────────────────────────────────────┐
│                    ChartWindow + BotPanelsMixin             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  BotOverlayMixin (Chart)                                    │
│  ├── Entry Markers (Candidate/Confirmed)                    │
│  ├── Stop Lines (Initial/Trailing)                          │
│  └── Debug HUD (State, Regime, Strategy, KI-Mode)           │
│                                                             │
│  Bot Tabs (Bottom Panel)                                    │
│  ├── Bot Control (Start/Stop, Settings)                     │
│  ├── Daily Strategy (Active, Scores, Walk-Forward)          │
│  ├── Signals & Trades (Position, Signals, Stop History)     │
│  └── KI Logs (Status, Calls, Cost, Audit)                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Backtest & QA

```
┌─────────────────────────────────────────────────────────────┐
│                    BacktestHarness                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  BacktestConfig                                             │
│  ├── Deterministic Seed (from config hash or explicit)      │
│  ├── Date Range (start_date, end_date)                      │
│  ├── Simulation Params (slippage, commission, fees)         │
│  └── Output Options (trades, equity curve, decisions)       │
│                                                             │
│  BacktestSimulator                                          │
│  ├── Slippage Simulation (random within range)              │
│  ├── Fill Probability (configurable)                        │
│  ├── Fee Calculation (per side)                             │
│  └── Order Execution Simulation                             │
│                                                             │
│  BacktestResult                                             │
│  ├── trades: List[BacktestTrade]                            │
│  ├── metrics: PerformanceMetrics                            │
│  ├── equity_curve: pd.DataFrame                             │
│  ├── decisions: List[BotDecision] (optional)                │
│  └── config_snapshot: dict                                  │
│                                                             │
│  Event-by-Event Processing                                  │
│  ├── _initialize_bot() - Setup with config                  │
│  ├── _process_bar() - Single bar through bot logic          │
│  └── _finalize_trades() - Close open positions              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    ReleaseGate                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Paper → Live Validation Thresholds:                        │
│  ├── min_trades: 30 (minimum sample size)                   │
│  ├── min_win_rate: 0.40 (40%)                               │
│  ├── min_profit_factor: 1.2                                 │
│  ├── max_drawdown: 0.15 (15%)                               │
│  └── min_sharpe: 0.8                                        │
│                                                             │
│  check(result) → (passed: bool, failures: List[str])        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Simulator Strategy Parameters

```
src/core/simulator/
├── strategy_params.py           # Public API (helpers + re-exports)
├── strategy_params_base.py      # StrategyName, ParameterDefinition, StrategyParameterConfig
├── strategy_params_registry.py  # STRATEGY_PARAMETER_REGISTRY (definitions)
├── simulation_signals.py        # Signal generator + wrappers
├── simulation_signal_utils.py   # Common indicators (RSI/OBV/ATR helpers)
├── simulation_signals_breakout.py
├── simulation_signals_momentum.py
├── simulation_signals_mean_reversion.py
├── simulation_signals_trend_following.py
├── simulation_signals_scalping.py
├── simulation_signals_bollinger_squeeze.py
├── simulation_signals_trend_pullback.py
├── simulation_signals_opening_range.py
└── simulation_signals_regime_hybrid.py
```

### Test Suite

```
┌─────────────────────────────────────────────────────────────┐
│                    BotTestSuite                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  BotUnitTests (Isolated Component Tests)                    │
│  ├── test_feature_normalization                             │
│  ├── test_trailing_state_never_loosen (Invariant)           │
│  ├── test_regime_detection                                  │
│  ├── test_entry_scoring                                     │
│  └── test_position_sizing                                   │
│                                                             │
│  BotIntegrationTests (Multi-Component Tests)                │
│  ├── test_full_trade_cycle (Entry → Manage → Exit)          │
│  ├── test_no_ki_stability (100 bars without LLM)            │
│  └── test_trailing_modes (PCT, ATR, SWING)                  │
│                                                             │
│  ChaosTests (Failure/Edge Case Tests)                       │
│  ├── test_missing_data_handling (NaN, gaps)                 │
│  ├── test_invalid_prices (negative, zero)                   │
│  ├── test_extreme_volatility (ATR spikes)                   │
│  ├── test_llm_failure (timeout, invalid JSON)               │
│  └── test_partial_fills (order execution edge cases)        │
│                                                             │
│  run_all_tests() → Dict[str, TestSuiteResult]               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Wichtige Interfaces

### DataRequest (src/core/market_data/types.py)
```python
@dataclass
class DataRequest:
    symbol: str
    start_date: datetime
    end_date: datetime
    timeframe: Timeframe
    asset_class: AssetClass
    source: Optional[DataSource] = None
```

### Bar (src/core/market_data/types.py)
```python
@dataclass
class Bar:
    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int
```

## Sicherheitshinweise

1. **Paper-Trading Default**: Alle neuen Features nutzen Paper-Umgebung
2. **API-Keys**: Nur in .env, nie im Code
3. **Order-Logik**: Jede Änderung erfordert Tests
4. **Live-Trading**: Nur mit expliziter User-Anweisung

## Tradingbot Status

**Stand: 2025-12-16 - 100% Implementiert**

Der automatisierte Tradingbot ist vollständig implementiert mit:
- ✅ State Machine (7 States, 18 Triggers)
- ✅ Feature & Regime Engine (14+ Indikatoren)
- ✅ Daily Strategy Selection (8 Strategien, Walk-Forward)
- ✅ Entry/Exit Engine (Entry Scoring, 3 Trailing-Modi)
- ✅ Execution Layer (Paper + Live, Risk Management)
- ✅ LLM Integration (OpenAI, 3 KI-Modi, Guardrails)
- ✅ UI Integration (4 neue Tabs, Chart Overlay)
- ✅ Backtest Harness (reproduzierbar, Release Gate)
- ✅ Test Suite (Unit, Integration, Chaos Tests)

**Quickstart:**
```python
from src.core.tradingbot import BotController, FullBotConfig, MarketType

# Konfiguration erstellen
config = FullBotConfig.create_default("BTC/USD", MarketType.CRYPTO)

# Bot starten
bot = BotController(config)
await bot.start()
```

**Beispiel-Konfigurationen:** `config/bot_configs/`

## CEL Rule Engine System [NEU]

Das **CEL (Common Expression Language) Rule Engine System** ermöglicht deklarative, JSON-basierte Trading-Regeln für den automatisierten Bot. Es ersetzt hardcoded Logik durch flexible, wiederverwendbare RulePacks.

### Architektur-Übersicht

```
┌─────────────────────────────────────────────────────────────┐
│                    JSON RulePack Files                       │
│              (03_JSON/RulePacks/*.json)                      │
└─────────────────────────┬───────────────────────────────────┘
                          │ validate & load
┌─────────────────────────▼───────────────────────────────────┐
│                  Phase 1: JSON Schema Foundation            │
│  - SchemaValidator: JSON Schema Draft 2020-12               │
│  - RulePack Pydantic Models (v2)                            │
│  - RulePackLoader: JSON → validated RulePack                │
└─────────────────────────┬───────────────────────────────────┘
                          │ compile expressions
┌─────────────────────────▼───────────────────────────────────┐
│                  Phase 2: CEL Engine Core                   │
│  - CELEngine: Expression compiler + evaluator (celpy)       │
│  - RuleContextBuilder: FeatureVector → CEL context          │
│  - Custom Functions: pctl(), isnull(), nz(), coalesce()     │
│  - Expression Caching: ~100x faster repeated evaluations    │
└─────────────────────────┬───────────────────────────────────┘
                          │ orchestrate execution
┌─────────────────────────▼───────────────────────────────────┐
│                  Phase 3: RulePack Executor                 │
│  - RulePackExecutor: Correct execution order                │
│  - ExecutionResult: ALLOW/BLOCK/EXIT/UPDATE_STOP            │
│  - Rule Profiling: Trigger counts, evaluation stats         │
│  - Monotonic Stop Enforcement (LONG: max, SHORT: min)       │
└─────────────────────────┬───────────────────────────────────┘
                          │ integrate with bot
┌─────────────────────────▼───────────────────────────────────┐
│                  Phase 4: BotController Integration         │
│  - load_rulepack(): Load RulePack JSON                      │
│  - _evaluate_rules(): Execute pack_types at decision points │
│  - Integration Points:                                      │
│    ├── Entry (FLAT state): risk + entry packs              │
│    ├── Exit (MANAGE state): exit pack                      │
│    └── Stop Update (MANAGE state): update_stop pack        │
└─────────────────────────────────────────────────────────────┘
```

### 4-Phasen Implementierung

#### Phase 1: JSON Schema Foundation (KOMPLETT)

**Deliverables:**
- JSON Schema Specification (`src/core/tradingbot/cel/schema/rulepack.schema.json`)
- Pydantic v2 Models (`src/core/tradingbot/cel/models.py`)
- SchemaValidator mit JSON Schema Draft 2020-12
- RulePackLoader: JSON → Python objects

**Datenmodelle:**
```python
# RulePack - Top-Level Container
RulePack(
    rules_version: str,
    engine: str,                    # "CEL"
    packs: List[Pack]
)

# Pack - Logical Grouping (risk, entry, exit, update_stop)
Pack(
    pack_type: str,                 # "risk" | "entry" | "exit" | "update_stop"
    rules: List[Rule],
    description: Optional[str]
)

# Rule - Single CEL Expression
Rule(
    id: str,                        # Unique identifier
    name: str,                      # Human-readable name
    expression: str,                # CEL expression
    severity: str,                  # "block" | "warn" | "exit" | "update_stop"
    message: str,                   # User-facing message
    enabled: bool = True
)
```

**Test Coverage:** 27 Tests (100% schema validation coverage)

#### Phase 2: CEL Engine Core (KOMPLETT)

**Deliverables:**
- CELEngine: Expression compiler + evaluator (`src/core/tradingbot/cel/engine.py`)
- RuleContextBuilder: FeatureVector → CEL context (`src/core/tradingbot/cel/context.py`)
- Custom CEL Functions (pctl, isnull, nz, coalesce)
- Expression Caching: LRU cache für wiederholte Evaluationen

**CEL Context Structure:**
```python
{
    # Indicators (13 total)
    "rsi14": {"value": 28.5, "period": 14, "indicator": "rsi"},
    "macd12_26_9": {
        "value": 0.5,
        "signal": 0.3,
        "histogram": 0.2,
        "fast": 12,
        "slow": 26,
        "smooth": 9
    },
    "adx14": {"value": 32.0, "period": 14},
    "atr14": {"value": 1.5, "period": 14},
    # ... weitere Indikatoren

    # Trade State (optional - nur bei offener Position)
    "trade": {
        "side": "LONG",
        "entry_price": 100.0,
        "current_price": 101.0,
        "profit_pct": 1.0,
        "bars_held": 3
    },

    # Configuration
    "cfg": {
        "capital": 10000.0,
        "max_position_size": 0.02,
        "max_risk_per_trade": 0.01
    },

    # Market Context
    "symbol": "BTC/USD",
    "timeframe": "5m"
}
```

**Custom Functions:**
- `pctl(values, percentile)` - Percentile calculation
- `isnull(value)` - NULL check
- `nz(value, default)` - NULL coalescing
- `coalesce(value1, value2, ...)` - First non-NULL value

**Performance:** ~100x faster with expression caching (0.02ms vs 2ms per eval)

**Test Coverage:** 30 Tests (engine, context, functions, caching)

#### Phase 3: RulePack Executor (KOMPLETT)

**Deliverables:**
- RulePackExecutor: Orchestrates pack evaluation
- ExecutionResult enum: ALLOW, BLOCK, EXIT, UPDATE_STOP
- ExecutionSummary: Aggregated results with metadata
- Rule Profiling: Track evaluations/triggers per rule
- Monotonic Stop Enforcement

**Execution Order (kritisch):**
```
1. exit pack          → If triggered, EXIT immediately
2. update_stop pack   → If triggered, UPDATE_STOP (then continue)
3. risk pack          → If blocked, BLOCK entry
4. entry pack         → If blocked, BLOCK entry
5. Final Decision     → ALLOW if all passed
```

**ExecutionResult States:**
```python
class ExecutionResult(str, Enum):
    ALLOW = "allow"           # All checks passed
    BLOCK = "block"           # Entry blocked by risk/entry pack
    EXIT = "exit"             # Position exit triggered
    UPDATE_STOP = "update_stop"  # Trailing stop update
```

**Monotonic Stop Enforcement:**
```python
def enforce_monotonic_stop(
    trade_direction: str,      # "LONG" | "SHORT"
    current_stop: float,
    new_stop: float
) -> float:
    """
    Ensures stops only move in safe direction:
    - LONG: Stops only move UP (use max)
    - SHORT: Stops only move DOWN (use min)
    """
    if trade_direction == "LONG":
        return max(current_stop, new_stop)  # Never lower stop
    else:  # SHORT
        return min(current_stop, new_stop)  # Never raise stop
```

**Rule Profiling:**
```python
executor.get_rule_stats() → {
    "risk_max_position": {
        "evaluations": 150,
        "triggers": 12,
        "last_triggered": "2025-01-15T14:30:00",
        "avg_eval_time_ms": 0.023
    }
}
```

**Test Coverage:** 24 Tests (execution order, monotonic stops, profiling)

#### Phase 4: BotController Integration (KOMPLETT)

**Deliverables:**
- `BotController.load_rulepack()` - Load RulePack from JSON
- `BotController._evaluate_rules()` - Execute pack_types at decision points
- Entry Integration: FLAT state (risk + entry packs)
- Exit Integration: MANAGE state (exit pack)
- Stop Update Integration: MANAGE state (update_stop pack)
- Rule Profiling API

**Integration Points:**

```
BotController Integration Points:
────────────────────────────────

1. Entry Check (bot_state_handlers_flat.py:65-82)
   └─► State: FLAT
   └─► Trigger: After score calculation, before signal creation
   └─► Packs: ["risk", "entry"]
   └─► Action: BLOCK entry if rules fail

2. Exit Check (bot_state_handlers_manage.py:60-77)
   └─► State: MANAGE
   └─► Trigger: After stop-hit check, before standard exits
   └─► Packs: ["exit"]
   └─► Action: EXIT position if exit rule triggers

3. Stop Update (bot_state_handlers_manage.py:84-128)
   └─► State: MANAGE
   └─► Trigger: Before trailing stop update
   └─► Packs: ["update_stop"]
   └─► Action: UPDATE stop with monotonic enforcement
```

**API Methods:**

```python
# Load RulePack
bot.load_rulepack("03_JSON/RulePacks/default_rules.json")
→ Returns: bool (True on success)

# Evaluate Rules (internal)
allowed, reason, summary = bot._evaluate_rules(
    features=current_features,
    pack_types=["risk", "entry"]
)
→ Returns: (
    allowed: bool,
    reason: str,
    summary: ExecutionSummary | None
)

# Rule Profiling
stats = bot.get_rule_stats()
→ Returns: Dict[str, RuleStats]

top_rules = bot.get_most_triggered_rules(top_n=10)
→ Returns: List[(rule_id, trigger_count)]

bot.clear_rule_stats()
```

**Test Coverage:** 13 Integration Tests

### Datenfluss: Entry Decision mit CEL

```
┌─────────────────────────────────────────────────────────────┐
│  1. MARKET_BAR Event → BotController.on_bar()               │
└───────────────────────┬─────────────────────────────────────┘
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  2. FeatureEngine → FeatureVector (13 indicators)           │
└───────────────────────┬─────────────────────────────────────┘
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  3. State: FLAT → process_flat()                            │
└───────────────────────┬─────────────────────────────────────┘
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  4. EntryScorer.calculate_score() → (long_score, short_score)|
└───────────────────────┬─────────────────────────────────────┘
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  5. _select_entry_signal() → (side, score)                  │
└───────────────────────┬─────────────────────────────────────┘
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  6. CEL Integration: _evaluate_rules(features, ["risk", "entry"])|
│     ├── RuleContextBuilder.build(features, trade, config)   │
│     ├── RulePackExecutor.execute(rulepack, context)         │
│     └── Returns: (allowed, reason, summary)                 │
└───────────────────────┬─────────────────────────────────────┘
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  7. Decision:                                               │
│     IF allowed:                                             │
│        → Create Signal                                      │
│        → Transition to SIGNAL state                         │
│     ELSE:                                                   │
│        → Log block reason                                   │
│        → BotDecision(NO_TRADE, BLOCKED_BY_CEL_RULES)        │
└─────────────────────────────────────────────────────────────┘
```

### Datenfluss: Exit Decision mit CEL

```
┌─────────────────────────────────────────────────────────────┐
│  1. State: MANAGE → process_manage()                        │
└───────────────────────┬─────────────────────────────────────┘
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  2. Check Stop Hit (using candle extremes)                  │
│     IF stop_hit: → EXIT immediately                         │
└───────────────────────┬─────────────────────────────────────┘
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  3. CEL Integration: _evaluate_rules(features, ["exit"])    │
│     ├── Context includes trade state (side, entry, profit)  │
│     ├── RulePackExecutor.execute()                          │
│     └── Returns: (allowed, reason, summary)                 │
└───────────────────────┬─────────────────────────────────────┘
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  4. Decision:                                               │
│     IF exit rule triggered:                                 │
│        → Log exit reason                                    │
│        → handle_exit_signal(exit_signal="CEL_RULE_EXIT")    │
│     ELSE:                                                   │
│        → Continue to standard exit checks                   │
└─────────────────────────────────────────────────────────────┘
```

### Datenfluss: Stop Update mit CEL

```
┌─────────────────────────────────────────────────────────────┐
│  1. State: MANAGE → process_manage() (after exit checks)    │
└───────────────────────┬─────────────────────────────────────┘
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  2. CEL Integration: _evaluate_rules(features, ["update_stop"])|
└───────────────────────┬─────────────────────────────────────┘
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  3. IF update_stop rule triggered:                          │
│     ├── _calculate_rule_based_stop(features) → new_stop     │
│     ├── enforce_monotonic_stop(direction, current, new)     │
│     └── Update position.stop_loss if changed                │
└───────────────────────┬─────────────────────────────────────┘
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  4. ELSE (no CEL trigger):                                  │
│     └── Fallback to standard trailing stop update          │
└─────────────────────────────────────────────────────────────┘
```

### RulePack JSON Example

```json
{
  "rules_version": "1.0.0",
  "engine": "CEL",
  "packs": [
    {
      "pack_type": "risk",
      "description": "Risk management rules",
      "rules": [
        {
          "id": "risk_max_position",
          "name": "Max Position Size Check",
          "expression": "cfg.max_position_size <= 0.2",
          "severity": "block",
          "message": "Position size exceeds 20% limit"
        }
      ]
    },
    {
      "pack_type": "entry",
      "description": "Entry validation rules",
      "rules": [
        {
          "id": "entry_rsi_oversold",
          "name": "RSI Oversold with Strong Trend",
          "expression": "rsi14.value < 30 && adx14.value > 25",
          "severity": "warn",
          "message": "RSI oversold with strong trend - favorable entry"
        }
      ]
    },
    {
      "pack_type": "exit",
      "description": "Exit trigger rules",
      "rules": [
        {
          "id": "exit_rsi_overbought",
          "name": "RSI Overbought Exit",
          "expression": "rsi14.value > 70",
          "severity": "exit",
          "message": "RSI overbought - exit position"
        }
      ]
    },
    {
      "pack_type": "update_stop",
      "description": "Trailing stop update rules",
      "rules": [
        {
          "id": "stop_trail_profit",
          "name": "Trail Stop in Profit",
          "expression": "trade != null && trade.profit_pct > 2.0",
          "severity": "update_stop",
          "message": "Trailing stop update (profit > 2%)"
        }
      ]
    }
  ]
}
```

### Verzeichnisstruktur

```
src/core/tradingbot/cel/
├── __init__.py                 # Public API exports
├── models.py                   # Pydantic Models (RulePack, Pack, Rule)
├── engine.py                   # CELEngine (compiler + evaluator)
├── context.py                  # RuleContextBuilder
├── executor.py                 # RulePackExecutor + ExecutionResult
├── loader.py                   # RulePackLoader
├── schema/
│   └── rulepack.schema.json    # JSON Schema Draft 2020-12
└── tests/
    ├── test_schema_validator.py         # 27 Tests
    ├── test_cel_engine.py                # 30 Tests
    ├── test_rulepack_executor.py         # 24 Tests
    └── test_bot_controller_cel_integration.py  # 13 Tests
```

### CEL Expression Beispiele

**Indikator-Checks:**
```javascript
// RSI oversold
rsi14.value < 30

// MACD bullish cross
macd12_26_9.histogram > 0 && macd12_26_9.value > macd12_26_9.signal

// ADX strong trend
adx14.value > 25

// Bollinger Band squeeze
bb20_2.width < pctl(bb20_2.width, 20)  // Width in lower 20th percentile
```

**Position-Checks:**
```javascript
// Trade in profit
trade != null && trade.profit_pct > 1.0

// Held too long
trade.bars_held > 50

// Stop distance check
(trade.current_price - trade.entry_price) / trade.entry_price > 0.02
```

**Risk-Checks:**
```javascript
// Max position size
cfg.max_position_size <= 0.2

// Max risk per trade
cfg.max_risk_per_trade <= 0.02

// Capital check
cfg.capital >= 1000.0
```

**Combined Logic:**
```javascript
// Entry: RSI oversold + strong trend + bullish MACD
rsi14.value < 30 && adx14.value > 25 && macd12_26_9.histogram > 0

// Exit: RSI overbought OR profit > 5% OR held > 100 bars
rsi14.value > 70 || trade.profit_pct > 5.0 || trade.bars_held > 100
```

### Performance Metriken

**Expression Evaluation:**
- Uncached: ~2ms pro Expression
- Cached (LRU): ~0.02ms pro Expression (~100x speedup)
- Context Building: ~0.5ms (13 Indikatoren)

**RulePack Execution:**
- 4 Packs (10 Rules total): ~1-2ms ohne Cache
- 4 Packs (10 Rules total): ~0.1ms mit Cache

**Memory Footprint:**
- RulePack JSON: ~5-15KB
- Compiled Expressions (Cached): ~50KB für 50 Rules
- Context Object: ~2KB

### Integration mit bestehenden Systemen

**Feature Engine:**
```python
# FeatureEngine liefert alle 13 Indikatoren
features = feature_engine.process_bar(bar)

# RuleContextBuilder konvertiert zu CEL Context
context = RuleContextBuilder.build(features, trade, config)
```

**Regime Engine:**
```python
# Regime kann in Custom Context hinzugefügt werden
regime = regime_engine.classify(features)

context_override = {
    "regime": {
        "type": regime.regime.value,      # "TREND_UP"
        "volatility": regime.volatility.value  # "NORMAL"
    }
}

allowed, reason, summary = bot._evaluate_rules(
    features, ["entry"], context_override=context_override
)
```

**Strategy Catalog:**
- RulePacks können pro Strategy definiert werden
- Strategy-spezifische Regeln über context_override

### Sicherheit & Guardrails

**JSON Schema Validation:**
- Alle RulePacks werden gegen JSON Schema validiert
- Pydantic v2 für Typ-Sicherheit zur Laufzeit

**CEL Sandboxing:**
- CEL ist eine sichere Expression Language (kein arbitrary code execution)
- Kein Dateisystem-Zugriff, kein Netzwerk-Zugriff
- Nur definierte Funktionen verfügbar

**Monotonic Stop Enforcement:**
- Verhindert versehentliches "Lockern" von Stops
- LONG: Stops bewegen sich nur nach oben
- SHORT: Stops bewegen sich nur nach unten

**Fallback bei fehlenden RulePacks:**
- Wenn kein RulePack geladen: `_evaluate_rules()` gibt `(True, "", None)` zurück
- Bot funktioniert weiter mit hardcoded Logik

### Erweiterbarkeit

**Neue Pack Types:**
- Einfach neue `pack_type` in JSON definieren
- RulePackExecutor unterstützt beliebige Pack-Typen
- Execution-Order kann angepasst werden

**Custom CEL Functions:**
- Neue Funktionen via `celpy` Environment registrieren
- Beispiel: `volatility_rank()`, `sector_strength()`, etc.

**Multi-Timeframe Context:**
- Context kann um Daten aus höheren Timeframes erweitert werden
- Beispiel: H1 Features im M5 Bot

### Workflow: Neue RulePack erstellen

```
1. JSON Schema Entwurf
   ├── 03_JSON/RulePacks/my_rules.json
   └── Packs definieren: risk, entry, exit, update_stop

2. Validierung
   ├── RulePackLoader.load("my_rules.json")
   └── SchemaValidator prüft gegen rulepack.schema.json

3. Bot Integration
   ├── bot.load_rulepack("03_JSON/RulePacks/my_rules.json")
   └── RulePack wird bei Entry/Exit/Stop evaluiert

4. Testing
   ├── Manual: Bot in Backtest laufen lassen
   ├── Profiling: bot.get_rule_stats() prüfen
   └── Iteration: Regeln basierend auf Trigger-Häufigkeit anpassen
```

### Status & Roadmap

**✅ Phase 1-4: KOMPLETT (Stand: 2025-01-20)**
- 94 Tests (81 Unit + 13 Integration)
- ~5,300 LOC implementiert
- 3 Integration Points im BotController
- Vollständige Dokumentation

**⏳ Optional Phase 5 (Zukunft):**
- Rule Versioning & Migration Tools
- Visual RulePack Editor (UI)
- Rule Templates Library
- A/B Testing Framework für RulePacks
- Multi-Strategy RulePack Orchestration
