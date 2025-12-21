# Splitting-Plan: 600 LOC Regel

**Datum:** 2025-12-14
**Regel:** Keine Codedatei darf mehr als 600 Zeilen produktiven Code haben!

---

## Übersicht der zu splittenden Dateien

| Datei | Total LOC | Produktiv LOC | Funktionen | Klassen | Splitting-Faktor |
|-------|-----------|---------------|------------|---------|------------------|
| embedded_tradingview_chart.py | 2,295 | 1,637 | 58 | 1 | ÷3 |
| history_provider.py | 1,892 | 1,114 | 54 | 9 | ÷2 |
| chart_window.py | 1,872 | 1,154 | 51 | 1 | ÷2 |
| app.py | 1,478 | 980 | 42 | 1 | ÷2 |
| engine.py | 956 | 625 | 29 | 12 | ÷1.5 |

---

## 1. embedded_tradingview_chart.py (1,637 LOC → 3-4 Module)

### Analyse der Code-Bereiche

```
Zeilen 1-597:     CHART_HTML_TEMPLATE (JavaScript/HTML)
Zeilen 600-903:   EmbeddedTradingViewChart.__init__, _setup_ui, _create_toolbar
Zeilen 904-1100:  JS-Ausführung, Page-Load, State-Management
Zeilen 1101-1423: Data-Loading, Indicator-Konfiguration, Panel-Erstellung
Zeilen 1424-1691: Indicator-Updates (full + real-time)
Zeilen 1692-2296: Event-Handler, Symbol-Loading, Streaming
```

### Splitting-Plan

```
VORHER: embedded_tradingview_chart.py (1,637 LOC)

NACHHER:
src/ui/widgets/chart/
├── __init__.py                          (~30 LOC)
│   └── Re-exports: EmbeddedTradingViewChart
│
├── embedded_tradingview_chart.py        (~450 LOC)
│   └── EmbeddedTradingViewChart (Hauptklasse)
│       - __init__
│       - _setup_ui
│       - _create_toolbar
│       - load_data
│       - Event-Handler-Verbindungen
│
├── chart_js_template.py                 (~600 LOC)
│   └── CHART_HTML_TEMPLATE (JavaScript/HTML String)
│       - Chart-Initialisierung
│       - chartAPI-Objekt
│       - Panel-Management
│
├── chart_indicators.py                  (~400 LOC)
│   └── ChartIndicatorMixin
│       - _get_indicator_configs
│       - _update_indicators
│       - _update_indicators_realtime
│       - _create_overlay_indicator
│       - _create_oscillator_panel
│       - _convert_*_data_to_chart_format
│
└── chart_streaming.py                   (~300 LOC)
    └── ChartStreamingMixin
        - _toggle_live_stream
        - _start_live_stream
        - _stop_live_stream
        - _on_market_bar
        - _on_market_tick
        - load_symbol

SUMME: ~1,780 LOC (inkl. Imports/Re-exports)
FUNKTIONEN: 58 (identisch!) ✅
```

---

## 2. history_provider.py (1,114 LOC → 2-3 Module)

### Analyse der Code-Bereiche

```
Zeilen 1-80:      Imports, Enums, DataRequest Dataclass
Zeilen 81-200:    HistoricalDataProvider (Basisklasse)
Zeilen 201-350:   IBKRHistoricalProvider
Zeilen 351-500:   AlphaVantageProvider
Zeilen 501-650:   YahooFinanceProvider
Zeilen 651-800:   FinnhubProvider
Zeilen 801-1100:  AlpacaProvider, AlpacaCryptoProvider
Zeilen 1101-1300: DatabaseProvider
Zeilen 1301-1892: HistoryManager (Hauptklasse)
```

### Splitting-Plan

```
VORHER: history_provider.py (1,114 LOC)

NACHHER:
src/core/market_data/
├── __init__.py                          (existiert, erweitern)
│   └── Re-exports aller Provider
│
├── history_provider.py                  (~400 LOC)
│   └── HistoryManager (Hauptklasse)
│       - fetch_data
│       - register_provider
│       - get_available_sources
│       - Streaming-Start/Stop
│
├── types.py                             (~100 LOC)
│   └── DataRequest, Timeframe, DataSource Enums
│       (teilweise bereits existiert)
│
├── providers/
│   ├── __init__.py                      (~50 LOC)
│   │   └── Re-exports aller Provider
│   │
│   ├── base.py                          (~150 LOC)
│   │   └── HistoricalDataProvider (ABC)
│   │
│   ├── alpaca_provider.py               (~300 LOC)
│   │   └── AlpacaProvider, AlpacaCryptoProvider
│   │
│   ├── yahoo_provider.py                (~150 LOC)
│   │   └── YahooFinanceProvider
│   │
│   ├── database_provider.py             (~150 LOC)
│   │   └── DatabaseProvider
│   │
│   └── other_providers.py               (~200 LOC)
│       └── IBKRHistoricalProvider
│       └── AlphaVantageProvider
│       └── FinnhubProvider

SUMME: ~1,500 LOC (inkl. Imports/Re-exports)
FUNKTIONEN: 54 (identisch!) ✅
```

---

## 3. chart_window.py (1,154 LOC → 2-3 Module)

### Analyse der Code-Bereiche

```
Zeilen 1-150:     Imports, ChartWindow.__init__
Zeilen 151-400:   UI-Setup (_setup_ui, _create_bottom_tabs)
Zeilen 401-700:   Strategy-Tab (_create_strategy_tab, Strategy-Handler)
Zeilen 701-1000:  Backtest-Tab (_create_backtest_tab, Backtest-Handler)
Zeilen 1001-1300: Optimization-Tab, State-Management
Zeilen 1301-1872: Event-Handler, closeEvent, Load/Save State
```

### Splitting-Plan

```
VORHER: chart_window.py (1,154 LOC)

NACHHER:
src/ui/widgets/
├── chart_window.py                      (~450 LOC)
│   └── ChartWindow
│       - __init__
│       - _setup_ui
│       - _create_bottom_tabs (delegiert zu Mixin)
│       - closeEvent
│       - State Load/Save
│
├── chart_window_tabs/
│   ├── __init__.py                      (~30 LOC)
│   │   └── Re-exports
│   │
│   ├── strategy_tab.py                  (~300 LOC)
│   │   └── StrategyTabMixin
│   │       - _create_strategy_tab
│   │       - _on_strategy_*
│   │       - Strategy-Logik
│   │
│   ├── backtest_tab.py                  (~300 LOC)
│   │   └── BacktestTabMixin
│   │       - _create_backtest_tab
│   │       - _on_backtest_*
│   │       - Backtest-Logik
│   │
│   └── optimization_tab.py              (~200 LOC)
│       └── OptimizationTabMixin
│           - _create_optimization_tab
│           - Optimization-Logik

SUMME: ~1,280 LOC (inkl. Imports/Re-exports)
FUNKTIONEN: 51 (identisch!) ✅
```

---

## 4. app.py (980 LOC → 2-3 Module)

### Analyse der Code-Bereiche

```
Zeilen 1-70:      Imports
Zeilen 71-140:    TradingApplication.__init__
Zeilen 141-230:   create_menu_bar
Zeilen 231-395:   create_toolbar (sehr lang!)
Zeilen 396-475:   create_central_widget, create_dock_widgets, create_status_bar
Zeilen 476-625:   Event-Setup, Theme, Settings
Zeilen 626-860:   Trading Mode, Broker Connect/Disconnect
Zeilen 861-1050:  Dialog-Shows, Market-Data
Zeilen 1051-1200: Chart-Popup, Watchlist
Zeilen 1201-1450: Data-Provider, Refresh, Close-Event
Zeilen 1451-1479: main()
```

### Splitting-Plan

```
VORHER: app.py (980 LOC)

NACHHER:
src/ui/
├── app.py                               (~400 LOC)
│   └── TradingApplication
│       - __init__
│       - init_ui (delegiert)
│       - setup_timers
│       - closeEvent
│       - main()
│
├── app_components/
│   ├── __init__.py                      (~30 LOC)
│   │   └── Re-exports
│   │
│   ├── menu_builder.py                  (~150 LOC)
│   │   └── MenuBarBuilder
│   │       - create_menu_bar
│   │       - create_file_menu
│   │       - create_view_menu
│   │       - create_trading_menu
│   │
│   ├── toolbar_builder.py               (~250 LOC)
│   │   └── ToolbarBuilder
│   │       - create_toolbar
│   │       - _create_broker_selector
│   │       - _create_trading_mode_selector
│   │       - _create_data_provider_selector
│   │
│   └── broker_handlers.py               (~200 LOC)
│       └── BrokerHandlersMixin
│           - connect_broker
│           - disconnect_broker
│           - _on_trading_mode_changed

SUMME: ~1,030 LOC (inkl. Imports/Re-exports)
FUNKTIONEN: 42 (identisch!) ✅
```

---

## 5. engine.py (625 LOC → 2 Module)

### Analyse der Code-Bereiche

```
Zeilen 1-25:      Imports
Zeilen 26-90:     Enums (SignalType, StrategyType), Dataclasses
Zeilen 91-207:    BaseStrategy (ABC)
Zeilen 208-319:   TrendFollowingStrategy
Zeilen 320-430:   MeanReversionStrategy
Zeilen 431-524:   MomentumStrategy
Zeilen 525-617:   BreakoutStrategy
Zeilen 618-715:   ScalpingStrategy
Zeilen 716-957:   StrategyEngine
```

### Splitting-Plan

```
VORHER: engine.py (625 LOC)

NACHHER:
src/core/strategy/
├── engine.py                            (~350 LOC)
│   └── SignalType, StrategyType (Enums)
│   └── Signal, StrategyConfig, StrategyState (Dataclasses)
│   └── BaseStrategy (ABC)
│   └── StrategyEngine
│       - create_strategy
│       - evaluate_all
│       - combine_signals
│       - signal_to_order
│
├── strategies/
│   ├── __init__.py                      (~50 LOC)
│   │   └── Re-exports aller Strategien
│   │
│   ├── trend_following.py               (~120 LOC)
│   │   └── TrendFollowingStrategy
│   │
│   ├── mean_reversion.py                (~120 LOC)
│   │   └── MeanReversionStrategy
│   │
│   ├── momentum.py                      (~100 LOC)
│   │   └── MomentumStrategy
│   │
│   ├── breakout.py                      (~100 LOC)
│   │   └── BreakoutStrategy
│   │
│   └── scalping.py                      (~100 LOC)
│       └── ScalpingStrategy

SUMME: ~940 LOC (inkl. Imports/Re-exports)
FUNKTIONEN: 29 (identisch!) ✅
```

---

## Implementierungs-Reihenfolge

1. **engine.py** (einfachstes Splitting, wenig Abhängigkeiten)
2. **history_provider.py** (klare Provider-Trennung)
3. **app.py** (UI-Builder-Extraktion)
4. **chart_window.py** (Tab-Extraktion)
5. **embedded_tradingview_chart.py** (komplexestes Splitting)

---

## Abhängigkeiten und Import-Updates

Nach jedem Splitting müssen folgende Imports aktualisiert werden:

### engine.py Splitting:
- `src/core/backtesting/backtrader_integration.py`
- `src/ui/widgets/chart_window.py`

### history_provider.py Splitting:
- `src/ui/app.py`
- `src/ui/widgets/embedded_tradingview_chart.py`
- `src/ui/widgets/chart_window.py`

### app.py Splitting:
- Keine externen Abhängigkeiten (nur interne Imports)

### chart_window.py Splitting:
- `src/ui/chart_window_manager.py`
- `examples/chart_state_persistence_demo.py`

### embedded_tradingview_chart.py Splitting:
- `src/ui/app.py`
- `src/ui/widgets/chart_window.py`
- `src/ui/widgets/chart_factory.py`

---

## Verifikations-Checkliste

Nach jedem Splitting:

- [ ] AST-Syntax-Check aller neuen Dateien
- [ ] Import-Check: Keine fehlenden Imports
- [ ] Funktionen-Count: Identisch wie vorher
- [ ] Re-Exports in `__init__.py` funktionieren
- [ ] Keine zirkulären Imports
- [ ] Produktive LOC pro Datei < 600

---

**Erstellt von:** Claude Code (Refactoring Phase 2)
**Status:** Bereit zur Implementierung
