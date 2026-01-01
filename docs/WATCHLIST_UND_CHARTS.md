

# Watchlist & Charts - Anleitung

Vollständige Anleitung zur Verwendung der Watchlist und Charts in OrderPilot-AI.

## Übersicht

Die **Watchlist** ermöglicht es dir:
- Symbole/Indizes zu überwachen
- Echtzeit-Preise zu sehen
- Schnell Charts zu öffnen
- Direkt Orders zu platzieren

Die **Charts** zeigen dir:
- Historische Preisdaten
- Technische Indikatoren (RSI, MACD)
- Echtzeit-Updates
- Verschiedene Zeitrahmen

## Watchlist verwenden

### 1. Symbole hinzufügen

#### In der UI

1. **Öffne die App**: `python start_orderpilot.py`
2. **Siehst du links die Watchlist**
3. **Symbol hinzufügen**:
   - Gib ein Symbol ein (z.B. "AAPL")
   - Klicke auf "+" oder drücke Enter

#### Quick-Add Buttons

- **Indices**: QQQ, DIA, SPY, IWM, VTI
- **Tech**: AAPL, MSFT, GOOGL, AMZN, META, NVDA, TSLA
- **Clear**: Alle Symbole entfernen

#### Mit dem Management-Tool

```bash
# Tool starten
python tools/manage_watchlist.py

# Symbole hinzufügen
>>> add AAPL
>>> add MSFT
>>> add QQQ

# Preset laden
>>> preset indices    # Fügt QQQ, DIA, SPY, IWM, VTI hinzu
>>> preset tech       # Fügt Tech-Aktien hinzu

# Watchlist anzeigen
>>> list

# Speichern
>>> save

# Beenden
>>> quit
```

### 2. Verfügbare Presets

| Preset | Beschreibung | Symbole |
|--------|--------------|---------|
| **indices** | Major US-Indizes | QQQ, DIA, SPY, IWM, VTI |
| **tech** | Tech-Giganten | AAPL, MSFT, GOOGL, AMZN, META, NVDA, TSLA |
| **finance** | Finanz-Sektor | JPM, BAC, WFC, GS, MS, C |
| **energy** | Energie-Sektor | XOM, CVX, COP, SLB, EOG |
| **crypto_related** | Crypto-Stocks | COIN, MARA, RIOT, MSTR |
| **german** | Deutsche Aktien | SAP, SIE.DE, DTE.DE, VOW3.DE, BAS.DE |

### 3. Watchlist-Funktionen

#### Echtzeit-Preise

Die Watchlist zeigt automatisch:
- **Aktueller Preis**: In USD (Alpaca) oder der konfigurierten Währung
- **Änderung**: Absolut in $ oder %
- **Volumen**: Handelsvolumen (formatiert als K/M)
- **Farb-Coding**: Grün (steigend), Rot (fallend)

#### Interaktionen

**Doppelklick auf Symbol**: Öffnet Chart

**Rechtsklick-Menü**:
- View Chart → Chart öffnen
- Remove from Watchlist → Symbol entfernen
- New Order... → Order-Dialog öffnen

### 4. Symbole entfernen

#### In der UI

1. Rechtsklick auf Symbol
2. "Remove from Watchlist" wählen

#### Mit dem Tool

```bash
python tools/manage_watchlist.py

>>> remove AAPL
>>> clear  # Alle entfernen
```

## Charts aktivieren

### 1. Chart für Symbol öffnen

#### Methode 1: Doppelklick
1. Watchlist öffnen (links)
2. Doppelklick auf Symbol
3. → Chart öffnet sich automatisch im Tab "Advanced Charts"

#### Methode 2: Rechtsklick
1. Rechtsklick auf Symbol in Watchlist
2. "View Chart" auswählen

#### Methode 3: Direkt im Chart-Tab
1. Klicke auf Tab "Charts" oder "Advanced Charts"
2. Wähle Symbol aus Dropdown (wenn vorhanden)
3. Lade Daten

### 2. Chart-Features

#### Basic Chart (Tab "Charts")
- Einfache Candlestick-Charts
- Zeitrahmen-Auswahl
- Zoom & Pan

#### Advanced Charts (Tab "Advanced Charts")
- Technische Indikatoren
- RSI, MACD, Bollinger Bands
- Mehrere Zeitrahmen
- Export-Funktionen

### 3. Mit Echtzeit-Daten verbinden

#### Alpaca Stream aktivieren

```python
from src.core.market_data.history_provider import HistoryManager

manager = HistoryManager()

# Stream starten
await manager.start_realtime_stream(
    symbols=["AAPL", "MSFT", "QQQ"],
    enable_indicators=True
)
```

#### In der UI

Nach Start der App:
1. Trading → Connect Broker
2. Wähle "Alpaca"
3. Stream startet automatisch für Watchlist-Symbole

#### Automatisch bei Symbol-Hinzufügung

Wenn Alpaca verbunden ist:
- Neue Symbole werden automatisch abonniert
- Echtzeit-Updates in Watchlist
- Charts aktualisieren sich live

## Beispiel-Workflows

### Workflow 1: US-Aktien überwachen

```bash
# 1. Watchlist erstellen
python tools/manage_watchlist.py

>>> preset tech         # Tech-Stocks hinzufügen
>>> add QQQ            # Nasdaq-Index hinzufügen
>>> add SPY            # S&P 500 hinzufügen
>>> save

# 2. App starten
python start_orderpilot.py

# 3. In der UI:
# - Siehst du alle Symbole in der Watchlist
# - Doppelklick auf AAPL → Chart öffnet sich
# - Rechtsklick auf MSFT → New Order
```

### Workflow 2: Indizes mit Echtzeit verfolgen

```bash
# 1. Watchlist mit Indizes
python tools/manage_watchlist.py

>>> preset indices  # QQQ, DIA, SPY, IWM, VTI
>>> save

# 2. App starten
python start_orderpilot.py

# 3. Broker verbinden
# Trading → Connect Broker → Alpaca

# 4. Echtzeit-Daten
# - Watchlist zeigt Live-Preise
# - Charts aktualisieren sich
# - Indicators berechnen sich neu
```

### Workflow 3: Trading Setup

```bash
# 1. Watchlist für Trading
python tools/manage_watchlist.py

>>> add AAPL
>>> add MSFT
>>> add NVDA
>>> save

# 2. App starten mit Alpaca
python start_orderpilot.py

# 3. In der UI:
# - Watchlist zeigt Echtzeit-Preise
# - Doppelklick auf AAPL → Chart mit RSI/MACD
# - Bei Signal: Rechtsklick → New Order
# - Order aufgeben (Paper Trading!)
```

## Programmierung

### Watchlist programmatisch verwalten

```python
from src.config.loader import config_manager

# Watchlist laden
watchlist = config_manager.settings.watchlist

# Symbole hinzufügen
if not hasattr(config_manager.settings, 'watchlist'):
    config_manager.settings.watchlist = []

config_manager.settings.watchlist.extend(["AAPL", "MSFT", "GOOGL"])

# Dupletten entfernen
config_manager.settings.watchlist = list(set(
    config_manager.settings.watchlist
))
```

### Chart-Widget verwenden

```python
from src.ui.widgets.chart_view import ChartView

# Chart-Widget erstellen
chart = ChartView()

# Symbol laden
if hasattr(chart, 'load_symbol'):
    chart.load_symbol("AAPL")
```

### Event-basiert reagieren

```python
from src.common.event_bus import Event, EventType, event_bus

async def on_symbol_selected(event: Event):
    symbol = event.data.get('symbol')
    print(f"Symbol ausgewählt: {symbol}")
    # Chart laden, Order öffnen, etc.

event_bus.subscribe(EventType.UI_ACTION, on_symbol_selected)
```

## Tipps & Tricks

### 1. Indizes als ETFs handeln

Statt Futures/Options nutze ETF-Proxies:
- **Nasdaq-100**: QQQ (kostenlos bei Alpaca)
- **Dow Jones**: DIA
- **S&P 500**: SPY
- **Russell 2000**: IWM

### 2. Watchlist organisieren

**Nach Sektor**:
```
# Watchlist 1: Tech
AAPL, MSFT, GOOGL, NVDA

# Watchlist 2: Indizes
QQQ, DIA, SPY

# Watchlist 3: Trading
Symbole mit aktuellen Trades
```

**Tipp**: Nutze mehrere Profile für verschiedene Setups!

### 3. Symbole schnell finden

```bash
# Management-Tool nutzen
python tools/manage_watchlist.py

>>> preset tech      # Schnell alle Tech-Stocks
>>> add COIN         # Einzeln hinzufügen
```

### 4. Echtzeit-Performance

**Alpaca**: 30 Symbole gleichzeitig (Free Tier)

Wenn mehr Symbole gewünscht:
- Prioritäre Symbole in Watchlist
- Andere via Search/Chart öffnen
- Oder Alpaca Premium ($9/Monat für 10.000 Symbole)

### 5. Charteinstellungen speichern

Charts merken sich:
- Ausgewählte Zeitrahmen
- Aktive Indikatoren
- Zoom-Level

## Fehlerbehebung

### "Symbol nicht gefunden"

**Problem**: Symbol existiert nicht oder falsches Format

**Lösung**:
- US-Aktien: `AAPL`, `MSFT` (keine Suffix)
- Deutsche Aktien: `SAP.DE`, `VOW3.DE`
- Prüfe Schreibweise

### "Keine Echtzeit-Daten"

**Problem**: Stream nicht aktiv

**Lösung**:
```python
# In der App
Trading → Connect Broker → Alpaca

# Oder programmatisch
await manager.start_realtime_stream(symbols=["AAPL"])
```

### "Chart lädt nicht"

**Problem**: Keine historischen Daten

**Lösung**:
- Alpaca API-Keys konfiguriert?
- Symbol existiert?
- Zeitrahmen zu weit zurück?

### "Watchlist nicht gespeichert"

**Problem**: Änderungen gehen verloren

**Lösung**:
```bash
# Im Tool explizit speichern
>>> save

# Oder beim Beenden
>>> quit  # Fragt automatisch
```

## Nächste Schritte

1. **Watchlist erstellen**: `python tools/manage_watchlist.py`
2. **App starten**: `python start_orderpilot.py`
3. **Alpaca verbinden**: Echtzeit-Daten aktivieren
4. **Charts nutzen**: Doppelklick auf Symbole
5. **Trading**: Rechtsklick → New Order

## Weitere Ressourcen

- [Alpaca Integration](ALPACA_INTEGRATION.md)
- [Real-Time Indicators](REALTIME_INDICATORS.md)
- [Quick Start](QUICKSTART_INDICATORS.md)
