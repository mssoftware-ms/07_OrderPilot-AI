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
