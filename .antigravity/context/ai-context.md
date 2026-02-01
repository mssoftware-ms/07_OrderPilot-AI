# AI Context Packet

**Project:** 07_OrderPilot-AI
**Stack:** PYQT6
**Generated:** 2026-02-01T13:15:27.365269+00:00

---

## Das Grundgesetz (Rules)

```
# ⚖️ Das Grundgesetz der Code-Integrität

§1 [Planung]: Erst Plan (3-7 Schritte), dann Code.
§2 [Search]: Erst `rg`/`grep`, dann Änderung. Keine Bauchentscheidungen.
§3 [Atomic]: Patches müssen klein und einzeln testbar sein.
§4 [Kommunikation]: Max. 5 Fragen. Annahmen explizit markieren.
§5 [QA]: Kein Merge ohne `scripts/ai-verify.sh` Durchlauf (§8).
§6 [Safety]: Keine Secrets, keine destruktiven Aktionen ohne Erlaubnis.
§7 [Hierarchie]: Orchestrator plant, Dev codet, QA prüft.
```

---

## ai_docs/architecture.md

# 🏗️ OrderPilot-AI Architektur

## Grundprinzipien

### 1. Signal-Slot Prinzip
- **UI rechnet NIE selbst** – alle Berechnungen in Services/Core
- UI reagiert nur auf Signale und zeigt Daten an
- Keine Business-Logik in Widgets

### 2. Schichtenarchitektur
```
┌─────────────────────────────────────────┐
│  UI Layer (src/ui/)                     │
│  - Widgets, Dialogs, Windows            │
│  - Reagiert auf Signale                 │
├─────────────────────────────────────────┤
│  Core Layer (src/core/)                 │
│  - TradingBot, CEL Engine, Strategies   │
│  - Business Logic, Berechnungen         │
├─────────────────────────────────────────┤
│  Broker Layer (src/brokers/)            │
│  - Alpaca, Bitunix Adapter              │
│  - API-Calls, Streaming                 │
├─────────────────────────────────────────┤
│  Data Layer                             │
│  - HistoryManager, MarketData           │
│  - Caching, Persistence                 │
└─────────────────────────────────────────┘
```

### 3. Mixin-Pattern
Große Klassen werden in Mixins aufgeteilt:
- `ChartWindow` nutzt: `PanelsMixin`, `EventBusMixin`, `StateMixin`, etc.
- Jede Mixin-Datei hat EIN Verantwortungsbereich

### 4. Composition over Inheritance
- `ChartWindow` delegiert an Helper-Klassen:
  - `ChartWindowSetup` - Initialisierung
  - `ChartWindowHandlers` - Event-Handler
  - `ChartWindowLifecycle` - Cleanup

## Datenflüsse

### Live-Preis Updates
```
WebSocket → MarketDataStream → price_updated Signal → UI Labels
```

### Bot-Execution
```
CEL Expression → CEL Engine → Entry/Exit Signal → Order Service → Broker API
```

## Wichtige Singleton-Services
- `HistoryManager` - Zentrale Datenverwaltung
- `EventBus` - Globale Event-Distribution
- `SettingsManager` - Konfiguration


## ai_docs/naming_conventions.md

# 📝 Naming Conventions

## UI-Elemente (objectName)

| Typ      | Prefix  | Beispiel                              |
| -------- | ------- | ------------------------------------- |
| Button   | `btn_`  | `btn_start_bot`, `btn_close_position` |
| Label    | `lbl_`  | `lbl_current_price`, `lbl_pnl`        |
| LineEdit | `txt_`  | `txt_symbol`, `txt_quantity`          |
| ComboBox | `cmb_`  | `cmb_timeframe`, `cmb_strategy`       |
| CheckBox | `chk_`  | `chk_trailing_stop`, `chk_auto_close` |
| SpinBox  | `spn_`  | `spn_stop_loss`, `spn_take_profit`    |
| GroupBox | `grp_`  | `grp_position`, `grp_order_settings`  |
| Tab      | `tab_`  | `tab_trading`, `tab_backtest`         |
| Dock     | `dock_` | `dock_watchlist`, `dock_activity_log` |

## Widget-Hierarchie für F12 Inspector
```
{window}_{tab}_{group}_{element}
Beispiel: chart_window.trading_tab.position_group.lbl_pnl
```

## Python-Klassen

| Typ     | Pattern                 | Beispiel                          |
| ------- | ----------------------- | --------------------------------- |
| Mixin   | `*Mixin`                | `PanelsMixin`, `EventBusMixin`    |
| Widget  | `*Widget`               | `TradingWidget`, `ChartWidget`    |
| Dialog  | `*Dialog`               | `SettingsDialog`, `OrderDialog`   |
| Window  | `*Window`               | `ChartWindow`, `TradingBotWindow` |
| Service | `*Service` / `*Manager` | `OrderService`, `HistoryManager`  |

## Signale
```python
# Pattern: {action}_{object}
price_updated = pyqtSignal(float)
position_opened = pyqtSignal(dict)
order_filled = pyqtSignal(str, float)
```

## Dateien
- Mixins: `*_mixin.py`
- Setup-Helper: `*_setup.py`
- Handlers: `*_handlers.py`


## ai_docs/pitfalls.md

# ⚠️ Bekannte Pitfalls & Patterns

## 1. Race Conditions bei UI-Updates

**Problem:** Mehrere Stellen setzen dasselbe Label → Flackern, inkonsistente Werte

**Lösung:**
- EIN zentraler Signal-Handler pro UI-Element
- Alle Updates über diesen Handler routen

```python
# FALSCH (Race Condition)
self.lbl_price.setText(str(price_from_stream))
self.lbl_price.setText(str(price_from_calculation))

# RICHTIG (Zentralisiert)
self.price_updated.connect(self._on_price_update)
def _on_price_update(self, price: float):
    self.lbl_price.setText(f"${price:,.2f}")
```

## 2. Event-Loop Blocking

**Problem:** Lange Berechnungen blockieren UI

**Lösung:**
- `QThread` oder `asyncio` für langlaufende Operationen
- `QTimer.singleShot()` für verzögerte Updates

## 3. Doppelte Initialisierung

**Problem:** Widget wird zweimal erstellt

**Prüfen:**
- Suche nach mehreren `__init__` Aufrufen
- Prüfe Mixin-Reihenfolge (MRO)

## 4. Timezone-Chaos

**Problem:** Chart zeigt falsche Zeit

**Regel:**
- Intern: IMMER UTC Unix-Timestamps
- Display: Erst bei Anzeige in Lokalzeit konvertieren
- Niemals: Lokale Zeit in Berechnungen verwenden

## 5. Alpaca API Gotchas

- Paper vs Live: Unterschiedliche Base-URLs
- Rate Limits: Max 200 requests/min
- Streaming: Reconnect-Logik erforderlich

