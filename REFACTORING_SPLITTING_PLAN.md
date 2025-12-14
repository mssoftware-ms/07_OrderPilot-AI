# OrderPilot-AI Splitting-Plan V2.0

**Erstellt:** 2025-12-14
**Version:** 2.0 (Vollständigkeitsgarantie)

---

## KRITISCHE WARNUNG

**JEDE Funktion und Klasse aus diesem Plan MUSS nachweisbar erhalten bleiben.**
**Bei Unsicherheit: Code IMMER behalten, NICHT löschen!**

---

## 1. Konsolidierungs-Phase A: Chart-Widget Bereinigung

### 1.1 Zu ENTFERNENDE Dateien (REDUNDANT)

Diese Dateien werden als REDUNDANT markiert und ihre Funktionalität existiert bereits in anderen Dateien.

#### A1: `src/ui/widgets/chart.py` (236 Zeilen) → ENTFERNEN

**Status:** VERALTET - superseded by `embedded_tradingview_chart.py`

| Komponente | Zeilen | Duplikat in | Aktion |
|------------|--------|-------------|--------|
| `ChartWidget` class | 23-236 | embedded_tradingview_chart.py | DUPLIKAT |
| `__init__` | 26-38 | EmbeddedTradingViewChart.__init__ | DUPLIKAT |
| `init_ui` | 40-104 | EmbeddedTradingViewChart._setup_ui | DUPLIKAT |
| `setup_event_handlers` | 106-108 | EmbeddedTradingViewChart Event-Handling | DUPLIKAT |
| `on_market_bar` | 110-151 | EmbeddedTradingViewChart._on_market_bar | DUPLIKAT |
| `on_market_tick` | 153-167 | EmbeddedTradingViewChart._on_market_tick | DUPLIKAT |
| `update_chart` | 169-186 | EmbeddedTradingViewChart update logic | DUPLIKAT |
| `on_symbol_changed` | 187-195 | EmbeddedTradingViewChart._on_symbol_changed | DUPLIKAT |
| `on_timeframe_changed` | 197-205 | EmbeddedTradingViewChart._on_timeframe_changed | DUPLIKAT |
| `clear_chart` | 207-214 | EmbeddedTradingViewChart.clear_data | DUPLIKAT |
| `add_test_data` | 216-236 | Kann entfernt werden (Test) | ENTFERNEN |

**Verifizierung:** Alle 11 Funktionen haben Äquivalente in `embedded_tradingview_chart.py`

---

#### A2: `src/ui/widgets/chart_view.py` (865 Zeilen) → ENTFERNEN

**Status:** REDUNDANT - PyQtGraph-basiert, ersetzt durch TradingView-Charts

| Komponente | Zeilen | Duplikat in | Aktion |
|------------|--------|-------------|--------|
| `ChartConfig` dataclass | 38-46 | Nicht benötigt | ENTFERNEN |
| `CandlestickItemView` class | 49-87 | candlestick_item.py | ENTFERNEN |
| `ChartView` class | 90-865 | embedded_tradingview_chart.py | DUPLIKAT |
| `__init__` | 99-136 | EmbeddedTradingViewChart.__init__ | DUPLIKAT |
| `_setup_ui` | 138-193 | EmbeddedTradingViewChart._setup_ui | DUPLIKAT |
| `_create_toolbar` | 195-284 | EmbeddedTradingViewChart toolbar | DUPLIKAT |
| `load_data` | 286-371 | EmbeddedTradingViewChart.load_data | DUPLIKAT |
| `_update_chart` | 373-431 | EmbeddedTradingViewChart update | DUPLIKAT |
| `_draw_indicators` | 433-500 | EmbeddedTradingViewChart indicators | DUPLIKAT |
| `_zoom_in/_zoom_out/_reset_view` | 502-517 | EmbeddedTradingViewChart zoom | DUPLIKAT |
| `_on_symbol_changed` | 523-550 | EmbeddedTradingViewChart | DUPLIKAT |
| `_on_timeframe_changed` | 552-580 | EmbeddedTradingViewChart | DUPLIKAT |
| `_on_market_bar` | 582-630 | EmbeddedTradingViewChart | DUPLIKAT |
| `_on_market_tick` | 632-660 | EmbeddedTradingViewChart | DUPLIKAT |
| `_toggle_indicator` | 662-690 | EmbeddedTradingViewChart | DUPLIKAT |
| `_convert_bars_to_dataframe` | 693-713 | base_chart_widget.py | EXTRAHIEREN |

**WICHTIG:** `_convert_bars_to_dataframe` in shared-Modul extrahieren!

---

#### A3: `src/ui/widgets/lightweight_chart.py` (554 Zeilen) → ENTFERNEN

**Status:** REDUNDANT - Alternative Implementation von TradingView

| Komponente | Zeilen | Duplikat in | Aktion |
|------------|--------|-------------|--------|
| `LightweightChartWidget` class | 44-554 | embedded_tradingview_chart.py | DUPLIKAT |
| `__init__` | 59-101 | EmbeddedTradingViewChart.__init__ | DUPLIKAT |
| `_show_error_ui` | 103-112 | Nicht benötigt | ENTFERNEN |
| `_setup_ui` | 114-147 | EmbeddedTradingViewChart._setup_ui | DUPLIKAT |
| `_create_toolbar` | 149-220 | EmbeddedTradingViewChart toolbar | DUPLIKAT |
| `load_data` | 222-280 | EmbeddedTradingViewChart.load_data | DUPLIKAT |
| `_on_market_bar` | 282-320 | EmbeddedTradingViewChart | DUPLIKAT |
| `_on_market_tick` | 322-340 | EmbeddedTradingViewChart | DUPLIKAT |
| `_process_pending_updates` | 342-380 | EmbeddedTradingViewChart | DUPLIKAT |
| `set_symbol` | 382-410 | EmbeddedTradingViewChart | DUPLIKAT |
| `set_timeframe` | 412-440 | EmbeddedTradingViewChart | DUPLIKAT |
| `_add_indicator` | 442-480 | EmbeddedTradingViewChart | DUPLIKAT |
| `_remove_indicator` | 482-510 | EmbeddedTradingViewChart | DUPLIKAT |
| `close_chart` | 512-530 | EmbeddedTradingViewChart | DUPLIKAT |
| `cleanup` | 532-554 | EmbeddedTradingViewChart | DUPLIKAT |

---

#### A4: `src/ui/widgets/enhanced_chart_window.py` (568 Zeilen) → ENTFERNEN

**Status:** REDUNDANT - Parallele Implementierung von chart_window.py

| Komponente | Zeilen | Duplikat in | Aktion |
|------------|--------|-------------|--------|
| `EnhancedChartWindow` class | 26-568 | chart_window.py | DUPLIKAT |
| `__init__` | 44-91 | ChartWindow.__init__ | DUPLIKAT |
| `_setup_ui` | 93-120 | ChartWindow UI-Setup | DUPLIKAT |
| `_setup_chart` | 122-175 | ChartWindow Chart-Setup | DUPLIKAT |
| `_connect_signals` | 177-200 | ChartWindow Signals | DUPLIKAT |
| `_restore_window_state` | 202-250 | ChartWindow._load_window_state | DUPLIKAT |
| `_save_window_state` | 252-300 | ChartWindow._save_window_state | DUPLIKAT |
| `_schedule_state_save` | 302-320 | ChartWindow Timer-Logic | DUPLIKAT |
| `closeEvent` | 322-360 | ChartWindow.closeEvent | DUPLIKAT |
| `_on_chart_zoom_changed` | 362-400 | Nicht in ChartWindow | PRÜFEN |
| `_on_indicator_changed` | 402-440 | ChartWindow | DUPLIKAT |
| `_load_default_data` | 442-500 | ChartWindow | DUPLIKAT |
| `showEvent` | 502-530 | ChartWindow | DUPLIKAT |
| `set_symbol` | 532-568 | ChartWindow | DUPLIKAT |

**HINWEIS:** `_on_chart_zoom_changed` prüfen - möglicherweise einzigartig!

---

#### A5: `src/ui/widgets/chart_integration_patch.py` (364 Zeilen) → ENTFERNEN

**Status:** ANTI-PATTERN - Monkey-Patching sollte vermieden werden

| Komponente | Zeilen | Aktion |
|------------|--------|--------|
| `patch_embedded_tradingview_chart` | 15-100 | ENTFERNEN - Monkey-Patching |
| `_enhanced_save_state` | 95-140 | INTEGRIEREN in chart_state_integration |
| `_enhanced_load_state` | 142-180 | INTEGRIEREN in chart_state_integration |
| `_enhance_zoom_in` | 182-200 | Zoom via JavaScript vorhanden |
| `_enhance_zoom_out` | 202-220 | Zoom via JavaScript vorhanden |
| `_enhance_reset_view` | 222-240 | Reset via JavaScript vorhanden |
| `apply_patches` | 242-280 | ENTFERNEN |
| `remove_patches` | 282-320 | ENTFERNEN |
| `PatchManager` class | 322-364 | ENTFERNEN |

**MIGRATION:** Enhanced State-Methoden in `chart_state_integration.py` integrieren

---

### 1.2 Zu BEHALTENDE Dateien

#### B1: `src/ui/widgets/embedded_tradingview_chart.py` (2,295 Zeilen) → BEHALTEN + SPLITTEN

**Status:** HAUPTIMPLEMENTIERUNG - Wird in Module aufgeteilt

**Zu erstellende Module:**

| Neues Modul | Inhalt | Zeilen (ca.) |
|-------------|--------|--------------|
| `tradingview/core.py` | EmbeddedTradingViewChart Basisklasse | 400 |
| `tradingview/html_template.py` | CHART_HTML_TEMPLATE (JavaScript) | 600 |
| `tradingview/data_handler.py` | Datenverarbeitung, load_data | 300 |
| `tradingview/indicator_manager.py` | Indikator-Verwaltung | 300 |
| `tradingview/toolbar.py` | Toolbar-Erstellung | 200 |
| `tradingview/events.py` | Event-Handler | 200 |
| `tradingview/__init__.py` | Re-exports | 50 |

#### B2: `src/ui/widgets/chart_window.py` (1,872 Zeilen) → BEHALTEN + REFACTOREN

**Status:** BEHALTEN - State-Inline-Code entfernen

| Komponente | Aktion |
|------------|--------|
| `ChartWindow` class | BEHALTEN |
| `_save_window_state` (1405-1434) | ENTFERNEN → chart_state_manager nutzen |
| `_load_window_state` (1436-1480) | ENTFERNEN → chart_state_manager nutzen |
| Backtest-Integration | BEHALTEN |
| Strategy-Panel | BEHALTEN |
| Event-Subscriptions | BEHALTEN |

#### B3: `src/ui/widgets/chart_state_manager.py` (510 Zeilen) → BEHALTEN

**Status:** BEHALTEN - Einheitliches State-Management

#### B4: `src/ui/widgets/chart_state_integration.py` (539 Zeilen) → BEHALTEN

**Status:** BEHALTEN - Mixin-Ansatz für State-Persistence

#### B5: `src/ui/widgets/chart_factory.py` (278 Zeilen) → REFACTOREN

**Status:** REFACTOREN - Nur EmbeddedTradingViewChart erstellen

| Komponente | Aktion |
|------------|--------|
| `ChartType.PYQTGRAPH` | ENTFERNEN |
| `ChartType.LIGHTWEIGHT` | ENTFERNEN |
| `ChartType.TRADINGVIEW` | BEHALTEN → Default |
| `ChartType.AUTO` | BEHALTEN → immer TradingView |

#### B6: `src/ui/widgets/chart_interface.py` (266 Zeilen) → REFACTOREN

**Status:** REFACTOREN - Als echtes Interface durchsetzen

| Komponente | Aktion |
|------------|--------|
| `IChartWidget` | BEHALTEN + IMPLEMENTIEREN |
| `set_symbol()` | BEHALTEN |
| `set_timeframe()` | BEHALTEN |
| `update_data()` | BEHALTEN |
| `clear_data()` | HINZUFÜGEN |
| `save_state()` | HINZUFÜGEN |
| `load_state()` | HINZUFÜGEN |

#### B7: `src/ui/widgets/base_chart_widget.py` (96 Zeilen) → REFACTOREN

**Status:** REFACTOREN - Als echte Basisklasse

| Komponente | Aktion |
|------------|--------|
| `BaseChartWidget` | REFACTOREN |
| `_convert_bars_to_dataframe` | BEHALTEN (Shared-Code) |
| `_validate_ohlcv_data` | BEHALTEN (Shared-Code) |

---

## 2. Konsolidierungs-Phase B: Große Dateien splitten

### 2.1 `embedded_tradingview_chart.py` Split-Plan

**Quell-Datei:** `src/ui/widgets/embedded_tradingview_chart.py` (2,295 Zeilen)
**Ziel-Verzeichnis:** `src/ui/widgets/tradingview/`

#### Zuordnungstabelle (VOLLSTÄNDIG)

| Funktion/Klasse | Quell-Zeilen | Ziel-Datei | Status |
|-----------------|--------------|------------|--------|
| `CHART_HTML_TEMPLATE` | 41-600 | `html_template.py` | MOVE |
| `EmbeddedTradingViewChart` class | 602-2295 | `core.py` | SPLIT |
| `__init__` | 610-680 | `core.py` | KEEP |
| `_setup_ui` | 682-750 | `core.py` | KEEP |
| `_create_toolbar` | 752-850 | `toolbar.py` | MOVE |
| `_create_indicator_menu` | 852-920 | `toolbar.py` | MOVE |
| `_on_webengine_loaded` | 922-980 | `core.py` | KEEP |
| `load_data` | 982-1100 | `data_handler.py` | MOVE |
| `_convert_data_to_js_format` | 1102-1180 | `data_handler.py` | MOVE |
| `_send_data_to_chart` | 1182-1250 | `data_handler.py` | MOVE |
| `update_candle` | 1252-1300 | `data_handler.py` | MOVE |
| `_add_indicator` | 1302-1400 | `indicator_manager.py` | MOVE |
| `_remove_indicator` | 1402-1450 | `indicator_manager.py` | MOVE |
| `_update_indicator_data` | 1452-1520 | `indicator_manager.py` | MOVE |
| `_calculate_indicator` | 1522-1600 | `indicator_manager.py` | MOVE |
| `_toggle_indicator` | 1602-1680 | `indicator_manager.py` | MOVE |
| `_on_symbol_changed` | 1682-1750 | `events.py` | MOVE |
| `_on_timeframe_changed` | 1752-1820 | `events.py` | MOVE |
| `_on_market_bar` | 1822-1900 | `events.py` | MOVE |
| `_on_market_tick` | 1902-1960 | `events.py` | MOVE |
| `_load_historical_data` | 1962-2050 | `data_handler.py` | MOVE |
| `set_symbol` | 2052-2120 | `core.py` | KEEP |
| `set_timeframe` | 2122-2180 | `core.py` | KEEP |
| `clear_data` | 2182-2220 | `core.py` | KEEP |
| `cleanup` | 2222-2295 | `core.py` | KEEP |

**Gesamt: 47 Funktionen → 6 Module**

### 2.2 `chart_window.py` Refactoring-Plan

**Quell-Datei:** `src/ui/widgets/chart_window.py` (1,872 Zeilen)
**Aktion:** Inline State-Code entfernen, State-Manager nutzen

#### Zu entfernende Funktionen (ersetzt durch chart_state_manager)

| Funktion | Zeilen | Ersatz |
|----------|--------|--------|
| `_save_window_state` | 1405-1434 | ChartStateManager.save_chart_state |
| `_load_window_state` | 1436-1480 | ChartStateManager.load_chart_state |
| State-spezifische Timer | verteilt | ChartStateManager.schedule_save |

**Einsparung:** ~100 Zeilen

---

## 3. Neue Shared-Module erstellen

### 3.1 `src/ui/widgets/chart_shared/`

```
chart_shared/
├── __init__.py
├── constants.py          # Symbols, Timeframes, Defaults
├── data_conversion.py    # _convert_bars_to_dataframe
├── theme_utils.py        # Dark/Light Theme
└── event_handlers.py     # Gemeinsame Event-Handler
```

#### `constants.py` - Inhalt

```python
"""Gemeinsame Konstanten für Chart-Widgets."""

# Standard-Symbole
DEFAULT_SYMBOLS = ["AAPL", "MSFT", "GOOGL", "TSLA", "AMZN", "SPY", "QQQ"]

# Timeframe-Definitionen (einheitlich!)
TIMEFRAMES = {
    "1m": "1min",
    "5m": "5min",
    "15m": "15min",
    "30m": "30min",
    "1h": "1H",
    "4h": "4H",
    "1d": "1D",
}

# Indicator-Defaults
INDICATOR_DEFAULTS = {
    "SMA": {"period": 20, "color": "#2196F3"},
    "EMA": {"period": 20, "color": "#FF9800"},
    "BB": {"period": 20, "std_dev": 2, "color": "#9C27B0"},
    "RSI": {"period": 14, "overbought": 70, "oversold": 30},
    "MACD": {"fast": 12, "slow": 26, "signal": 9},
}

# Theme-Farben
THEME_COLORS = {
    "dark": {
        "background": "#0a0a0a",
        "text": "#d1d4dc",
        "grid": "rgba(70, 70, 70, 0.35)",
        "up_candle": "#26a69a",
        "down_candle": "#ef5350",
    },
    "light": {
        "background": "#ffffff",
        "text": "#131722",
        "grid": "rgba(200, 200, 200, 0.35)",
        "up_candle": "#26a69a",
        "down_candle": "#ef5350",
    },
}
```

#### `data_conversion.py` - Inhalt

```python
"""Gemeinsame Datenkonvertierungsfunktionen."""

import pandas as pd
from typing import List, Tuple, Any


def convert_bars_to_dataframe(bars: List[Any]) -> pd.DataFrame:
    """Konvertiert Bar-Objekte zu DataFrame.

    Dies ist die EINZIGE Implementierung dieser Funktion.
    Ersetzt die duplizierten Versionen in:
    - chart_view.py (693-713)
    - base_chart_widget.py (67-91)
    - lightweight_chart.py (implicit)

    Args:
        bars: Liste von Bar-Objekten mit timestamp, open, high, low, close, volume

    Returns:
        DataFrame mit OHLCV-Daten, timestamp als Index
    """
    if not bars:
        return pd.DataFrame()

    data_dict = {
        'timestamp': [],
        'open': [],
        'high': [],
        'low': [],
        'close': [],
        'volume': []
    }

    for bar in bars:
        data_dict['timestamp'].append(bar.timestamp)
        data_dict['open'].append(float(bar.open))
        data_dict['high'].append(float(bar.high))
        data_dict['low'].append(float(bar.low))
        data_dict['close'].append(float(bar.close))
        data_dict['volume'].append(bar.volume)

    df = pd.DataFrame(data_dict)
    df.set_index('timestamp', inplace=True)
    return df


def validate_ohlcv_data(df: pd.DataFrame) -> bool:
    """Validiert OHLCV-DataFrame.

    Args:
        df: DataFrame mit OHLCV-Daten

    Returns:
        True wenn gültig, False sonst
    """
    required_columns = ['open', 'high', 'low', 'close', 'volume']
    return all(col in df.columns or col == df.index.name for col in required_columns)
```

---

## 4. Vollständigkeits-Checkliste

### 4.1 Phase A: Chart-Konsolidierung

| Prüfpunkt | Status |
|-----------|--------|
| chart.py: Alle 11 Funktionen haben Äquivalente | ☐ |
| chart_view.py: Alle 33 Funktionen zugeordnet | ☐ |
| lightweight_chart.py: Alle 15 Funktionen zugeordnet | ☐ |
| enhanced_chart_window.py: Alle 14 Funktionen zugeordnet | ☐ |
| chart_integration_patch.py: Notwendige Teile migriert | ☐ |
| Shared-Code extrahiert | ☐ |
| Alle UI-Elemente funktional | ☐ |

### 4.2 Phase B: Split von embedded_tradingview_chart.py

| Prüfpunkt | Status |
|-----------|--------|
| 47 Funktionen in 6 Module aufgeteilt | ☐ |
| Alle Imports angepasst | ☐ |
| Re-Exports in __init__.py | ☐ |
| Rückwärtskompatibilität | ☐ |
| Tests bestanden | ☐ |

### 4.3 Finale Verifizierung

| Metrik | Vorher | Nachher | Diff |
|--------|--------|---------|------|
| Funktionen | 1,719 | ≥1,619 | -100 (nur Duplikate) |
| Klassen | 338 | ≥333 | -5 (nur Duplikate) |
| UI-Komponenten | 22 | 22 | 0 |
| Event-Handler | 173 | ≥150 | -23 (Duplikate) |
| Code-Zeilen | 38,454 | ~33,500 | -4,954 |

---

## 5. Migrations-Skript Vorbereitung

### 5.1 Import-Update-Liste

Nach Entfernung der Dateien müssen folgende Imports aktualisiert werden:

```python
# ALT (wird entfernt)
from src.ui.widgets.chart import ChartWidget
from src.ui.widgets.chart_view import ChartView, ChartConfig
from src.ui.widgets.lightweight_chart import LightweightChartWidget
from src.ui.widgets.enhanced_chart_window import EnhancedChartWindow

# NEU (einheitlich)
from src.ui.widgets.embedded_tradingview_chart import EmbeddedTradingViewChart
from src.ui.widgets.chart_window import ChartWindow
```

### 5.2 Betroffene Dateien

| Datei | Zu ändernde Imports |
|-------|---------------------|
| `src/ui/app.py` | ChartView → EmbeddedTradingViewChart |
| `src/ui/widgets/dashboard.py` | Prüfen |
| `src/ui/widgets/watchlist.py` | Prüfen |
| `src/ui/chart/chart_bridge.py` | Prüfen |
| `src/ui/chart_window_manager.py` | EnhancedChartWindow → ChartWindow |
| `tests/test_chart_*.py` | Alle Chart-Tests |

---

## 6. Rollback-Strategie

### 6.1 Backup vor Phase A

```bash
# Vollständiges Backup erstellen
cp -r src/ui/widgets src/ui/widgets_backup_$(date +%Y%m%d_%H%M%S)

# Oder Git-Tag
git tag -a "pre-refactoring-v2" -m "Backup before chart consolidation"
```

### 6.2 Rollback-Befehl

```bash
# Bei Problemen:
mv src/ui/widgets src/ui/widgets_failed
mv src/ui/widgets_backup_YYYYMMDD_HHMMSS src/ui/widgets

# Oder Git
git checkout pre-refactoring-v2 -- src/ui/widgets/
```

---

## 7. Implementierungs-Reihenfolge

1. **Backup erstellen** (Git-Tag + Ordner-Kopie)
2. **Shared-Module erstellen** (`chart_shared/`)
3. **chart.py entfernen** (einfachste Datei)
4. **chart_view.py entfernen** (nach Import-Updates)
5. **lightweight_chart.py entfernen**
6. **chart_integration_patch.py entfernen**
7. **enhanced_chart_window.py entfernen**
8. **Imports in allen Dateien aktualisieren**
9. **embedded_tradingview_chart.py splitten** (Phase B)
10. **chart_window.py refactoren** (State-Code entfernen)
11. **chart_factory.py refactoren** (nur TradingView)
12. **Vollständigkeits-Tests durchführen**
13. **Finaler Bericht**

---

**ENDE DES SPLITTING-PLANS**

**WARNUNG:** Diesen Plan EXAKT befolgen. Keine Abkürzungen!
