# OrderPilot-AI Architektur-Umbau: ChartWindow als Hauptfenster

**Datum:** 2026-01-21
**Aktualisiert:** 2026-01-21 (Best-Practice Review)
**Status:** ✅ PLAN FERTIG - Bereit für Implementation
**Ziel:** Hauptfenster eliminieren, ChartWindow wird primäres Fenster

---

## Executive Summary

Der Benutzer möchte die App-Architektur grundlegend ändern: Das bisherige Hauptfenster (`TradingApplication`) soll entfernt oder versteckt werden, stattdessen soll das `ChartWindow` beim Start direkt angezeigt werden.

**Zu übernehmende Funktionen aus Hauptfenster:**
1. ✅ Watchlist (mit letztem Symbol, Doppelklick für Wechsel)
2. ✅ Settings Dialog
3. ✅ Market Data Provider Auswahl

---

## Web-Recherche: Best Practices für Trading-App-Architekturen

### Trend 1: Unified Cloud Architecture mit flexibler Frontend-Präsentation
- **Quelle:** [WalletInvestor - Multi-Device Trading Platforms](https://walletinvestor.com/magazine/7-best-seamless-multi-device-options-trading-platforms-for-2026-unlock-professional-gains-anywhere)
- Single Backend, Multiple Frontend Views
- Plattform behandelt Web/Desktop/Mobile als "verschiedene Fenster zum gleichen Cloud-Engine"
- **Relevanz:** Unterstützt flexible Window-Architektur

### Trend 2: Multi-Monitor Support ist essentiell
- **Quelle:** [QuantVPS - Trade Execution Software](https://www.quantvps.com/blog/best-trade-execution-software)
- Chart-Engine verarbeitet große Datenmengen über mehrere Monitore
- Kritisch für Trader mit vielen Positionen
- **Relevanz:** Multi-Chart-Management muss erhalten bleiben

### Trend 3: Modular Architecture bevorzugt
- **Quelle:** [A-Team - Trading Platforms](https://a-teaminsight.com/blog/leading-platforms-and-frameworks-to-support-trading-application-development/)
- EP3 kombiniert Matching, Surveillance, Risk in modularer Architektur
- Erweiterbare APIs
- **Relevanz:** Unterstützt Komponenten-basierte Struktur

### Trend 4: Workspace Management statt einzelner Fenster
- **Quelle:** [TradingTechnologies - Multi-Window Workspaces](https://library.tradingtechnologies.com/trade/ttw-managing-multiwindow-workspaces-in-trade.html)
- "Add and switch between multiple windows in a single workspace"
- **Relevanz:** Könnte Hauptfenster als "Workspace Manager" rechtfertigen

### Trend 5: UX Best Practices für Trading UIs
- **Quelle:** [Devexperts - Trading UI Design](https://devexperts.com/blog/ui/)
- **Multi-Panel Layouts:** Mehr als 2 Content Panels
- **Flexible Workspaces:** Split screens, multi-monitor, floating windows, tab-free containers
- **Customization:** Plattformen passen sich an spezifische Assets/Methoden an
- **Warnung:** Frühe Plattformen nutzten zu viele verschachtelte Fenster/Tabs
- **Migration:** Hin zu user-friendly Ansatz (Simplicity bei erhaltener Power)
- **Navigation:** Quick-jump Controls bei vielen Komponenten
- **Relevanz:** **Single Chart Window mit integrierten Komponenten entspricht modernem Trend**

### PyQt6 Best Practices (2024/2025)
- **Quelle:** Web-Recherche PyQt6 Patterns
- **QDockWidget** für flexible Docking-Panels ✅
- **Eigenständige Fenster** statt MDI für Multi-Monitor-Support ✅
- **Model-View-Separation** für shared Data (WatchlistModel) ✅
- **Singleton-Services** für zentrale Ressourcen (BrokerService) ✅
- **Event-Driven Architecture** mit Filtering auf Bus-Ebene ✅

**Quellen:**
- [7 Best Seamless Multi-Device Options Trading Platforms for 2026](https://walletinvestor.com/magazine/7-best-seamless-multi-device-options-trading-platforms-for-2026-unlock-professional-gains-anywhere)
- [Designing User Interface in Trading Software](https://devexperts.com/blog/ui/)
- [The 10 best trading platform design examples](https://merge.rocks/blog/the-10-best-trading-platform-design-examples-in-2024)
- [TradingView Platform UX Design](https://rondesignlab.com/cases/tradingview-platform-for-traders)
- [Managing multi-window workspaces](https://library.tradingtechnologies.com/trade/ttw-managing-multiwindow-workspaces-in-trade.html)
- [PyQt6 QDockWidget](https://doc.qt.io/qt-6/qdockwidget.html)
- [PyQt6 Model-View Architecture](https://pythonguis.com/tutorials/modelview-architecture/)

---

## USER-ENTSCHEIDUNGEN ✅

Alle 6 kritischen Fragen geklärt:

1. **Architektur-Strategie:** ✅ **Option 3** (Workspace Manager)
   - Hauptfenster bleibt als kompakte Control-Leiste
   - ChartWindow für Charts
   - Aufwand: Mittel (10-15h)

2. **Zentrale Trading-Tabs:** ✅ **Option A** (Komplett entfernen)
   - Dashboard, Positions, Orders, Performance, Indicators, Alerts werden NICHT übernommen
   - Fokus 100% auf Chart-Trading

3. **Broker & Trading Mode:** ✅ **Option A** (In ChartWindow Toolbar)
   - Zusätzliche Buttons in ChartWindow Toolbar Row 1
   - Immer sichtbar, schneller Zugriff

4. **Multi-Chart Management:** ✅ **Option A** (Doppelklick öffnet neues Fenster)
   - ChartWindowManager + MultiMonitorChartManager bleiben
   - Jeder Doppelklick in Watchlist öffnet neues ChartWindow

5. **Activity Log:** ✅ **Option B** (Bottom Dock in ChartWindow)
   - Activity Log wird Bottom Dock Widget in jedem ChartWindow
   - Togglebar, zeigt Chart-spezifische Events

6. **Menu Bar:** ✅ **Option C** (Im Workspace Manager / Hauptfenster)
   - Hauptfenster behält vollständige Menu Bar
   - ChartWindow hat Context-Menu für wichtigste Actions
   - Zentralisiert

---

## ZIEL-ARCHITEKTUR

### Architektur-Diagramm (Best Practice)

```
┌─────────────────────────────────────────────────────────────────────┐
│                        SINGLETON SERVICES                            │
├─────────────────────────────────────────────────────────────────────┤
│  BrokerService          WatchlistModel         EventBus             │
│  (Singleton)            (QAbstractListModel)   (mit Symbol-Filter)  │
│       │                       │                      │              │
│       ▼                       ▼                      ▼              │
│  ┌─────────┐            ┌─────────┐           ┌─────────┐          │
│  │ connect │            │ symbols │           │subscribe│          │
│  │disconnect│           │ add/rem │           │  emit   │          │
│  └────┬────┘            └────┬────┘           └────┬────┘          │
│       │                      │                     │                │
└───────┼──────────────────────┼─────────────────────┼────────────────┘
        │                      │                     │
        ▼                      ▼                     ▼
┌───────────────────────────────────────────────────────────────────┐
│                    WORKSPACE MANAGER (Hauptfenster)                │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ Menu Bar: File | View | Charts | Trading | Tools | Help      │ │
│  ├──────────────────────────────────────────────────────────────┤ │
│  │ Toolbar: [Connect] [Broker▼] [Mode▼] [Provider▼] [Status]    │ │
│  ├──────────────────────────────────────────────────────────────┤ │
│  │                                                              │ │
│  │               WATCHLIST (Central Widget)                     │ │
│  │        ┌────────────────────────────────────┐               │ │
│  │        │  Symbol    Price   Change   ...    │               │ │
│  │        │  AAPL      189.50  +1.2%          │  ◄─┐           │ │
│  │        │  BTCUSDT   90150   -0.5%          │    │ Shared    │ │
│  │        │  SPY       478.20  +0.8%          │    │ Model     │ │
│  │        └────────────────────────────────────┘    │           │ │
│  │               ▲ Double-Click = Open ChartWindow  │           │ │
│  ├──────────────────────────────────────────────────┼───────────┤ │
│  │ Status Bar: Time | Market | Account             │           │ │
│  └──────────────────────────────────────────────────┘           │ │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼ Opens
┌───────────────────────────────────────────────────────────────────┐
│                    CHART WINDOW (pro Symbol)                       │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ Toolbar Row 1: [Connect] [Broker▼] [Mode Badge] | TF | ...   │ │
│  │                    ▲ Mirror Controls (Events only)           │ │
│  ├──────────────────────────────────────────────────────────────┤ │
│  │ Toolbar Row 2: [Live] [Regime] [Mark] [AI] [Bot] [Levels]    │ │
│  ├──────────┬───────────────────────────────────────┬───────────┤ │
│  │ Left Dock│                                       │Right Dock │ │
│  │ Watchlist│         CHART (Central)               │  AI Chat  │ │
│  │ (shared  │                                       │           │ │
│  │  model)  │     ┌─────────────────────────┐      │           │ │
│  │          │     │  [Candlestick Chart]    │      │           │ │
│  │          │     │                         │      │           │ │
│  │          │     └─────────────────────────┘      │           │ │
│  ├──────────┴───────────────────────────────────────┴───────────┤ │
│  │ Bottom Dock: ACTIVITY LOG (toggleable, symbol-filtered)      │ │
│  ├──────────────────────────────────────────────────────────────┤ │
│  │ Context Menu (Right-Click): Settings | Close All | Show WS   │ │
│  └──────────────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────────┘
```

### Workspace Manager (Kompaktes Hauptfenster)

**Neue Rolle:** Zentrale Control-Leiste, kein Trading-Tab-Widget mehr

```
TradingApplication (Workspace Manager)
├── Menu Bar (vollständig)
│   ├── File: Settings, Exit
│   ├── View: Theme
│   ├── Charts: New Chart, Layouts, Sync, Tile All, Close All
│   ├── Trading: Connect/Disconnect, Backtest, AI Analysis, Optimization
│   ├── Tools: Chart Analysis, AI Monitor, Pattern DB, Console, Reset
│   └── Help: About
├── Toolbar (1 Zeile, kompakt)
│   ├── Connect/Disconnect Button (PRIMARY - owns BrokerService)
│   ├── Broker Selector (Combo)
│   ├── Trading Mode (Backtest/Paper/Live)
│   ├── Market Data Provider (Combo)
│   └── Status Indicators
├── Central Widget: WATCHLIST (Hauptfokus)
│   └── WatchlistWidget (mit SHARED WatchlistModel)
├── NO MORE TABS (Dashboard/Positions/Orders entfernt)
├── Status Bar: Time, Market Status, Account Info
└── Chart Management
    ├── ChartWindowManager (Multi-Chart Tracking)
    └── MultiMonitorChartManager (Layout Management)
```

**Größe:** Kompakt, z.B. 400px breit × 600px hoch (anpassbar)

**Position:** Links auf Hauptmonitor (oder user-defined)

**Verhalten:**
- Immer sichtbar (kann minimiert werden)
- Watchlist-Doppelklick → öffnet ChartWindow für Symbol
- Broker/Mode/Provider zentral für alle Charts
- Menu steuert alle ChartWindows (Sync, Tile, Close All)

---

### ChartWindow (Pro Symbol)

**Erweiterte Rolle:** Standalone Trading-Interface mit integrierten Controls

```
ChartWindow (pro Symbol)
├── Toolbar Row 1 (ERWEITERT)
│   ├── Connect/Disconnect Button (MIRROR - emits Events only)
│   ├── Broker Selector (MIRROR - emits Events only)
│   ├── Trading Mode Badge (READ-ONLY)
│   ├── Separator
│   ├── Timeframe Selector
│   ├── Period Selector
│   ├── Indicators Menu
│   ├── Load/Refresh/Zoom Actions
│   └── Market Data Provider (MIRROR)
├── Toolbar Row 2 (unverändert)
│   ├── Live Stream, Regime, Marking, AI Chat, Bot, Levels, Context
│   └── Market Status Label
├── Central: EmbeddedTradingViewChart
├── Left Dock: WATCHLIST (SHARED Model)
│   └── WatchlistWidget (Doppelklick öffnet weiteres ChartWindow)
├── Right Dock: Chat Widget
├── Bottom Dock: ACTIVITY LOG (Symbol-gefiltert auf Bus-Ebene)
│   └── ActivityLogWidget (nur Events für dieses Symbol)
├── Dockable: Bitunix Trading Widget
├── Standalone: Trading Bot Window
├── Context Menu (Rechtsklick):
│   ├── Settings
│   ├── Alle Charts schließen
│   └── Workspace Manager anzeigen
└── NO MENU BAR (alle Menu-Funktionen via Workspace Manager)
```

**Verhalten:**
- Eigenständiges Fenster pro Symbol
- Broker/Mode Controls sind **Mirror Controls** (emittieren nur Events)
- Watchlist nutzt **gemeinsames WatchlistModel** (Singleton)
- Activity Log hat **Symbol-Filter auf Bus-Ebene** (performant)
- Context Menu für schnellen Zugriff auf Settings

---

## SINGLETON SERVICES (NEU)

### BrokerService Pattern

```python
# src/core/broker/broker_service.py
class BrokerService:
    """Singleton für zentrale Broker-Verwaltung."""
    
    _instance: Optional['BrokerService'] = None
    
    @classmethod
    def instance(cls) -> 'BrokerService':
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self):
        self._broker: Optional[BrokerAdapter] = None
        self._connection_lock = asyncio.Lock()
    
    async def connect(self, broker_type: str) -> bool:
        """Thread-safe connect. Nur EINE aktive Verbindung."""
        async with self._connection_lock:
            if self._broker and self._broker.connected:
                return True  # Already connected
            
            # Create and connect broker
            self._broker = self._create_broker(broker_type)
            success = await self._broker.connect()
            
            if success:
                event_bus.emit(Event(EventType.BROKER_CONNECTED, {...}))
            return success
    
    async def disconnect(self) -> None:
        async with self._connection_lock:
            if self._broker:
                await self._broker.disconnect()
                event_bus.emit(Event(EventType.BROKER_DISCONNECTED, {...}))

# Usage in ChartWindow (Mirror Control):
class ChartWindowToolbar:
    def _on_connect_clicked(self):
        # Emit event, let BrokerService handle it
        event_bus.emit(Event(EventType.BROKER_CONNECT_REQUESTED, {
            "broker_type": self.broker_combo.currentText()
        }))
```

### WatchlistModel Pattern

```python
# src/ui/models/watchlist_model.py
class WatchlistModel(QAbstractListModel):
    """Singleton Model für Watchlist-Daten."""
    
    _instance: Optional['WatchlistModel'] = None
    
    @classmethod
    def instance(cls) -> 'WatchlistModel':
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self):
        super().__init__()
        self._symbols: list[WatchlistItem] = []
    
    def add_symbol(self, symbol: str) -> None:
        self.beginInsertRows(...)
        self._symbols.append(WatchlistItem(symbol))
        self.endInsertRows()
        # Qt Model signals automatically notify all views!
    
    def remove_symbol(self, symbol: str) -> None:
        ...

# Usage in any Widget:
class WatchlistWidget(QListView):
    def __init__(self):
        super().__init__()
        self.setModel(WatchlistModel.instance())  # SHARED!
```

### Event Bus mit Symbol-Filter

```python
# src/common/event_bus.py
class EventBus:
    def subscribe(
        self,
        event_type: EventType,
        handler: Callable,
        filter: Optional[Callable[[Event], bool]] = None  # NEU
    ) -> None:
        """Subscribe with optional filter (evaluated BEFORE handler call)."""
        self._subscribers[event_type].append((handler, filter))
    
    def emit(self, event: Event) -> None:
        for handler, filter_fn in self._subscribers[event.type]:
            if filter_fn is None or filter_fn(event):
                handler(event)

# Usage in ChartWindow Activity Log:
class ActivityLogWidget:
    def _subscribe_events(self):
        event_bus.subscribe(
            EventType.TRADE_EXECUTED,
            self._log_trade,
            filter=lambda e: e.data.get("symbol") == self.symbol  # Filter auf Bus-Ebene!
        )
```

---

## DETAILLIERTER IMPLEMENTIERUNGSPLAN

### Phase 0: Singleton Services erstellen (2-3h) [NEU]

**Dateien:**
- `src/core/broker/broker_service.py` (NEU)
- `src/ui/models/watchlist_model.py` (NEU)
- `src/common/event_bus.py` (erweitern)

**Änderungen:**

1. **BrokerService Singleton erstellen**
   - Zentrale Broker-Verwaltung
   - Thread-safeConnect/Disconnect
   - Emittiert BROKER_CONNECTED/DISCONNECTED

2. **WatchlistModel Singleton erstellen**
   - QAbstractListModel für Qt Model-View
   - add_symbol/remove_symbol mit Signals
   - Automatische View-Updates

3. **EventBus Filter-Support hinzufügen**
   - subscribe() mit optionalem filter Parameter
   - Filter wird VOR Handler-Aufruf geprüft
   - Skaliert besser bei vielen Subscribern

**Verifikation:**
- BrokerService.instance() gibt immer gleiche Instanz
- WatchlistModel.instance() gibt immer gleiche Instanz
- Event-Filter funktioniert korrekt

---

### Phase 1: Workspace Manager Umbau (4-5h)

**Dateien:** `src/ui/app.py`, `src/ui/app_components/app_ui_mixin.py`, `src/ui/app_components/toolbar_mixin.py`

**Änderungen:**

1. **AppUIMixin - Central Widget vereinfachen**
   - Entfernen: 6-Tab Widget (Dashboard, Positions, Orders, Performance, Indicators, Alerts)
   - Setzen: WatchlistWidget als zentrales Widget
   - WatchlistWidget nutzt **WatchlistModel.instance()**
   - Entfernen: Watchlist Dock (ist jetzt zentral)
   - Entfernen: Activity Log Dock (geht zu ChartWindow)

2. **ToolbarMixin - Auf 1 Zeile reduzieren**
   - Entfernen: Row 2 komplett
   - Behalten: Row 1 (Connect, Broker, Mode, Provider, Status)
   - Connect-Button ruft **BrokerService.instance().connect()** auf

3. **Fenster-Größe anpassen**
   - Default: 400x600px statt 1200x800px
   - Minimum: 300x400px

**Verifikation:**
- Hauptfenster startet kompakt mit Watchlist zentral
- Toolbar hat nur 1 Zeile
- Menu Bar vollständig vorhanden
- Keine Tabs mehr sichtbar

---

### Phase 2: ChartWindow Toolbar Erweiterung (3-4h)

**Datei:** `src/ui/widgets/chart_mixins/toolbar_mixin.py`

**Änderungen:**

1. **Toolbar Row 1 erweitern mit Broker Controls (MIRROR)**
   - Connect/Disconnect Button (checkable) - **emittiert nur Events**
   - Broker Selector ComboBox - **emittiert nur Events**
   - Trading Mode Badge (Read-Only Label)
   - Market Data Provider ComboBox

2. **Event Bus Synchronisation**
   - Subscribe: BROKER_CONNECTED, BROKER_DISCONNECTED, TRADING_MODE_CHANGED
   - Emit: BROKER_CONNECT_REQUESTED, BROKER_DISCONNECT_REQUESTED
   - **NICHT direkt BrokerService aufrufen** (nur Events!)

3. **Responsive Toolbar (Optional)**
   - Bei Platzmangel: Overflow-Items in "..." Menu
   - Oder: 2 Sub-Rows (1a: Broker, 1b: Timeframe)

**Verifikation:**
- Toolbar Row 1 zeigt Broker Controls
- Connect-Button synchronisiert mit Workspace via Events
- Mode Badge zeigt aktuellen Modus
- Provider Combo funktioniert

---

### Phase 3: ChartWindow Watchlist Integration (2-3h)

**Datei:** `src/ui/widgets/chart_window_setup.py`

**Änderungen:**

1. **Left Dock Widget erstellen mit SHARED Model**
   - WatchlistWidget Instanz
   - `self.watchlist.setModel(WatchlistModel.instance())` ← SHARED!
   - Doppelklick öffnet NEUES ChartWindow
   - Toolbar Toggle Button

2. **Keine manuelle Event-Synchronisation nötig!**
   - Qt Model-View synchronisiert automatisch
   - Optional: Event-Bus für nicht-Qt-Komponenten

3. **Persistence**
   - Speichern: Dock Visibility Status
   - Laden: Beim ChartWindow Start

**Verifikation:**
- Watchlist als Left Dock sichtbar
- Doppelklick öffnet neues ChartWindow
- Watchlist-Daten synchronisiert **automatisch** (Model-View)
- Toggle Button funktioniert

---

### Phase 4: ChartWindow Activity Log Integration (1-2h)

**Datei:** `src/ui/widgets/chart_window_setup.py`

**Änderungen:**

1. **Bottom Dock Widget erstellen**
   - ActivityLogWidget Instanz (Chart-spezifisch)
   - Default versteckt
   - Toolbar Toggle Button

2. **Symbol-Filtering auf Bus-Ebene (PERFORMANT)**
   ```python
   event_bus.subscribe(
       EventType.TRADE_EXECUTED,
       self._log_trade,
       filter=lambda e: e.data.get("symbol") == self.symbol
   )
   ```
   - Filter im Event-Bus, nicht im Handler
   - Skaliert gut bei vielen Charts

**Verifikation:**
- Activity Log als Bottom Dock
- Default versteckt, togglebar
- Zeigt nur relevante Events (symbol-gefiltert)
- Persistence funktioniert

---

### Phase 5: ChartWindow Context Menu (1h) [NEU]

**Datei:** `src/ui/widgets/chart_window_setup.py`

**Änderungen:**

1. **Context Menu erstellen**
   - Rechtsklick auf Chart öffnet Menu
   - Actions: Settings, Alle Charts schließen, Workspace anzeigen

2. **Keyboard Shortcuts**
   - `Ctrl+,` für Settings (überall)
   - `Ctrl+Shift+W` für Workspace anzeigen

**Verifikation:**
- Rechtsklick öffnet Context Menu
- Settings öffnet Settings Dialog
- Workspace Manager wird angezeigt/fokussiert

---

### Phase 6: Startup Flow anpassen (2-3h)

**Dateien:** `start_orderpilot.py`, `src/ui/app_components/app_lifecycle_mixin.py`

**Änderungen:**

1. **Startup Sequence**
   - Workspace Manager zeigen (400x600px)
   - KEIN auto-open ChartWindow

2. **Session Persistence (ERWEITERT)**
   - Speichern:
     - Liste offener Symbole
     - Fenster-Geometrie (Position, Größe) via `saveGeometry()`
     - Dock-States via `saveState()`
     - Aktiver Timeframe/Period
     - Sync-Status (Crosshairs)
   - Laden: Bei Start wiederherstellen

**Verifikation:**
- App startet mit Workspace Manager
- Watchlist sofort bedienbar
- Kein automatisches ChartWindow
- Session-Restore funktional (inkl. Geometry!)

---

### Phase 7: Multi-Chart Synchronisation (1-2h)

**Keine Code-Änderungen nötig!** Bestehende Infrastruktur funktioniert:

- ChartWindowManager
- MultiMonitorChartManager
- Menu-Funktionen (Sync, Tile, Close All)

**Einzige Änderung:** Watchlist-Doppelklick öffnet IMMER neues ChartWindow

**Verifikation:**
- Mehrere ChartWindows parallel
- Sync Crosshairs funktioniert
- Tile All Charts funktioniert
- Close All Charts funktioniert

---

## KRITISCHE DATEIEN

| Datei | Änderungen | Aufwand | Risiko |
|-------|-----------|---------|--------|
| `src/core/broker/broker_service.py` | **NEU** - Singleton | 1.5h | Mittel |
| `src/ui/models/watchlist_model.py` | **NEU** - Singleton Model | 1h | Niedrig |
| `src/common/event_bus.py` | Filter-Support | 0.5h | Niedrig |
| `src/ui/app_components/app_ui_mixin.py` | Tabs entfernen, Watchlist zentral | 1h | Niedrig |
| `src/ui/app_components/toolbar_mixin.py` | Row 2 entfernen | 0.5h | Niedrig |
| `src/ui/widgets/chart_mixins/toolbar_mixin.py` | Broker Controls (Mirror) | 2h | Mittel |
| `src/ui/widgets/chart_window_setup.py` | Watchlist + Activity Log + Context Menu | 3h | Mittel |
| `src/ui/app_components/app_lifecycle_mixin.py` | Session Persistence erweitert | 1h | Niedrig |
| `start_orderpilot.py` | Startup Flow anpassen | 0.5h | Niedrig |

**Gesamt:** 11-12h (ohne Testing)

---

## RISIKEN & LÖSUNGEN

### 1. ~~Toolbar Row 1 Platzmangel~~ (⚠️ Mittel) → ✅ GELÖST
**Lösung:** Responsive Toolbar mit Overflow-Menu ODER 2 Sub-Rows

### 2. ~~WatchlistWidget Synchronisation~~ (⚠️ Mittel) → ✅ GELÖST
**Lösung:** **Shared WatchlistModel** (Qt Model-View Pattern) - automatische Sync!

### 3. ~~Activity Log Performance~~ (⚠️ Niedrig) → ✅ GELÖST
**Lösung:** **Symbol-Filter auf Bus-Ebene** - kein Handler-Call für irrelevante Events

### 4. ~~Broker-State Synchronisation~~ (⚠️ Hoch) → ✅ GELÖST
**Lösung:** **BrokerService Singleton** mit Lock. ChartWindows emittieren nur Events, keine direkten Calls.

### 5. Menu-Zugriff bei minimiertem Workspace (⚠️ Niedrig) → ✅ GELÖST
**Lösung:** **Context Menu** in ChartWindow + Keyboard Shortcuts

### 6. Session Persistence unvollständig (⚠️ Niedrig) → ✅ GELÖST
**Lösung:** Erweiterte Persistence mit Geometry, DockState, Timeframe, Sync-Status

---

## VERIFIKATIONSPLAN

### Test-Suites

1. **Singleton Services:**
   - BrokerService.instance() immer gleiche Instanz
   - WatchlistModel.instance() immer gleiche Instanz
   - Event-Filter funktioniert korrekt

2. **Startup Flow:** Workspace Manager zeigt sich kompakt

3. **Chart Opening:** Doppelklick öffnet ChartWindow mit allen Features

4. **Multi-Chart:** Mehrere Charts parallel, Sync funktioniert

5. **Broker Controls (Mirror):**
   - ChartWindow Connect-Button emittiert Event
   - BrokerService verarbeitet Event
   - Alle ChartWindows aktualisieren Status

6. **Watchlist Sync:**
   - Symbol in Workspace hinzufügen
   - Automatisch in allen ChartWindows sichtbar (Model-View)

7. **Activity Log:** Chart-spezifisches Logging (Filter auf Bus-Ebene)

8. **Session Restore:**
   - Charts werden wiederhergestellt
   - Geometrie korrekt
   - DockStates korrekt
   - Timeframes korrekt

9. **Context Menu:** Settings, Close All, Show Workspace funktionieren

10. **Menu-Funktionen:** Alle Menu-Items funktionieren

---

## GESCHÄTZTE AUFWÄNDE

| Kategorie | Stunden |
|-----------|---------|
| Phase 0: Singleton Services | 2-3h |
| Phase 1: Workspace Manager | 4-5h |
| Phase 2: ChartWindow Toolbar | 3-4h |
| Phase 3: Watchlist Integration | 2-3h |
| Phase 4: Activity Log | 1-2h |
| Phase 5: Context Menu | 1h |
| Phase 6: Startup/Session | 2-3h |
| Phase 7: Multi-Chart | 1-2h |
| **Implementation Gesamt** | **16-23h** |
| Testing & Bugfixing | 6-10h |
| Dokumentation | 1h |
| **GESAMT** | **23-34h** |

**Empfehlung:** 28-30 Stunden (konservativ)

**Timeline (8h/Tag):**
- Tag 1: Phase 0-1 (Singleton Services + Workspace Manager)
- Tag 2: Phase 2-3 (ChartWindow Toolbar + Watchlist)
- Tag 3: Phase 4-6 (Activity Log + Context Menu + Startup)
- Tag 4: Phase 7 + Testing + Bugfixing

---

## NÄCHSTE SCHRITTE

1. ✅ Plan fertig (inkl. Best-Practice-Review)
2. ⏳ Phase 0 starten: Singleton Services erstellen
3. Nach jeder Phase: Testen und committen
4. Nach allen Phasen: Vollständiger Integrationstest

---

## ÄNDERUNGSHISTORIE

| Datum | Änderung |
|-------|----------|
| 2026-01-21 | Initialer Plan erstellt |
| 2026-01-21 | **Best-Practice-Review:** |
|            | + Phase 0: Singleton Services (BrokerService, WatchlistModel) |
|            | + Phase 5: Context Menu für ChartWindow |
|            | + Event-Bus Filter-Support |
|            | + Erweiterte Session Persistence |
|            | + Architektur-Diagramm mit Service-Layer |
|            | + Zeitschätzung aktualisiert (23-34h) |

---

**Status:** ✅ BEREIT FÜR IMPLEMENTATION (Best-Practice-Enhanced)
