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
│  src/core/market_data/ ── HistoryManager, Provider          │
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

### TradingApplication (src/ui/app.py)
```
TradingApplication
├── MenuMixin         - Menüleiste
├── ToolbarMixin      - Haupttoolbar
└── BrokerMixin       - Broker-Verbindung
```

## Provider-Pattern

Datenquellen sind als Provider abstrahiert:

```
HistoricalDataProvider (Abstract Base)
├── AlpacaProvider         - Alpaca Stock API
├── AlpacaCryptoProvider   - Alpaca Crypto API
├── YahooFinanceProvider   - yfinance
├── AlphaVantageProvider   - Alpha Vantage API
├── FinnhubProvider        - Finnhub API
├── IBKRHistoricalProvider - Interactive Brokers
└── DatabaseProvider       - Lokale SQLite DB
```

## Verzeichnisstruktur

```
src/
├── brokers/              # Broker-Adapter
│   └── alpaca/           # Alpaca-spezifisch
│       ├── client.py     # REST-Client
│       ├── streaming.py  # WebSocket-Client
│       └── models.py     # DTOs
├── common/               # Shared Utilities
│   ├── event_bus.py      # Globaler Event-Bus
│   ├── logging_setup.py  # Logging-Konfiguration
│   └── security.py       # API-Key Verwaltung
├── core/                 # Business Logic
│   ├── market_data/      # Marktdaten
│   │   ├── history_provider.py
│   │   └── providers/    # Datenquellen
│   └── strategy/         # Strategien
│       ├── engine.py     # Strategie-Engine
│       ├── compiler.py   # DSL-Compiler
│       └── strategies/   # Strategie-Implementierungen
└── ui/                   # User Interface
    ├── app.py            # Hauptfenster
    ├── app_components/   # App-Mixins
    ├── widgets/          # Wiederverwendbare Widgets
    │   ├── chart_mixins/ # Chart-Mixins
    │   └── chart_window_mixins/
    └── dialogs/          # Modale Dialoge
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
