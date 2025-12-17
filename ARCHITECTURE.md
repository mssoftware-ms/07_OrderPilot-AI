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
├── ai/                   # AI Services
│   ├── openai_service.py # OpenAI Integration
│   └── anthropic_service.py
└── ui/                   # User Interface
    ├── app.py            # Hauptfenster
    ├── app_components/   # App-Mixins
    ├── widgets/          # Wiederverwendbare Widgets
    │   ├── chart_mixins/ # Chart-Mixins
    │   └── chart_window_mixins/
    └── dialogs/          # Modale Dialoge
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
