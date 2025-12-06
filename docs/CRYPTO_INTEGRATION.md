# Cryptocurrency Integration

OrderPilot-AI unterstützt vollständig Kryptowährungen über Alpaca's Crypto Data API.

## Übersicht

Die Crypto-Integration bietet:

- ✅ **Historische Crypto-Daten** (Bars, Trades, Quotes)
- ✅ **Echtzeit-Crypto-Streaming** via WebSocket
- ✅ **Unterstützte Trading-Paare**: BTC/USD, ETH/USD, SOL/USD, und viele mehr
- ✅ **Nahtlose Integration** mit bestehendem Market Data Framework

## Architektur

```
src/core/market_data/
├── types.py                      # AssetClass Enum (STOCK, CRYPTO, OPTION, FOREX)
├── alpaca_crypto_provider.py     # Historical Crypto Data Provider
├── alpaca_crypto_stream.py       # Real-time Crypto WebSocket Client
└── history_provider.py           # HistoryManager mit Crypto-Support
```

### Komponenten

1. **AlpacaCryptoProvider**
   - Historische Crypto-Daten über REST API
   - Endpoint: `/v1beta3/crypto/us/bars`
   - Unterstützt alle Standard-Timeframes (1min - 1M)

2. **AlpacaCryptoStreamClient**
   - Echtzeit-Daten über WebSocket
   - Endpoint: `wss://stream.data.alpaca.markets/v1beta3/crypto/us`
   - Streams: Bars, Trades, Quotes, Orderbooks

3. **AssetClass Enum**
   - Unterscheidung zwischen Asset-Typen (STOCK, CRYPTO, etc.)
   - Automatisches Provider-Routing basierend auf Asset Class

## Verwendung

### 1. Historische Crypto-Daten

```python
from datetime import datetime, timedelta
from src.core.market_data import (
    AlpacaCryptoProvider,
    Timeframe
)

# Provider erstellen
provider = AlpacaCryptoProvider(
    api_key="YOUR_API_KEY",
    api_secret="YOUR_API_SECRET"
)

# BTC/USD Daten abrufen (letzte 24 Stunden)
end_date = datetime.utcnow()
start_date = end_date - timedelta(days=1)

bars = await provider.fetch_bars(
    symbol="BTC/USD",
    start_date=start_date,
    end_date=end_date,
    timeframe=Timeframe.HOUR_1
)

# Daten verarbeiten
for bar in bars:
    print(f"{bar.timestamp}: ${bar.close}")
```

### 2. Echtzeit-Crypto-Streaming

```python
from src.core.market_data import AlpacaCryptoStreamClient

# Stream Client erstellen
stream = AlpacaCryptoStreamClient(
    api_key="YOUR_API_KEY",
    api_secret="YOUR_API_SECRET"
)

# Verbinden
await stream.connect()

# Zu Crypto-Paaren subscriben
await stream.subscribe(["BTC/USD", "ETH/USD", "SOL/USD"])

# Daten empfangen (automatisch via Event-Bus)
# Events: MARKET_BAR, MARKET_DATA_TICK

# Aktuellen Preis abrufen
tick = stream.get_latest_tick("BTC/USD")
print(f"BTC: ${tick.last}")

# Disconnecten
await stream.disconnect()
```

### 3. Verwendung mit HistoryManager

```python
from src.core.market_data import (
    AssetClass,
    DataRequest,
    HistoryManager,
    Timeframe
)

# HistoryManager erstellen (registriert automatisch alle Provider)
manager = HistoryManager()

# Crypto-Daten mit AssetClass.CRYPTO abrufen
request = DataRequest(
    symbol="BTC/USD",
    start_date=start_date,
    end_date=end_date,
    timeframe=Timeframe.HOUR_1,
    asset_class=AssetClass.CRYPTO  # Wichtig!
)

bars, source = await manager.fetch_data(request)
print(f"Fetched {len(bars)} bars from {source}")

# Crypto-Stream starten
await manager.start_crypto_realtime_stream(["BTC/USD", "ETH/USD"])

# Stream stoppen
await manager.stop_crypto_realtime_stream()
```

## Unterstützte Crypto-Paare

Alpaca unterstützt viele Kryptowährungen, darunter:

| Symbol      | Name        | Beschreibung            |
|-------------|-------------|-------------------------|
| BTC/USD     | Bitcoin     | Bitcoin zu US-Dollar    |
| ETH/USD     | Ethereum    | Ethereum zu US-Dollar   |
| ETH/BTC     | ETH/BTC     | Ethereum zu Bitcoin     |
| SOL/USD     | Solana      | Solana zu US-Dollar     |
| AVAX/USD    | Avalanche   | Avalanche zu US-Dollar  |
| MATIC/USD   | Polygon     | Polygon zu US-Dollar    |
| DOT/USD     | Polkadot    | Polkadot zu US-Dollar   |
| LINK/USD    | Chainlink   | Chainlink zu US-Dollar  |

**Vollständige Liste**: Siehe [Alpaca Crypto API Dokumentation](docs/alpaca/docs.alpaca.markets/docs/crypto-pricing-data.html)

## Asset Class Filtering

Der `HistoryManager` nutzt automatisches Provider-Routing basierend auf `AssetClass`:

- **AssetClass.CRYPTO** → Nutzt nur `AlpacaCryptoProvider` und `DATABASE`
- **AssetClass.STOCK** → Nutzt Stock-Provider (Alpaca, Yahoo, etc.), **NICHT** Crypto-Provider

```python
# Crypto Request
crypto_request = DataRequest(
    symbol="BTC/USD",
    ...,
    asset_class=AssetClass.CRYPTO  # → Verwendet AlpacaCryptoProvider
)

# Stock Request
stock_request = DataRequest(
    symbol="AAPL",
    ...,
    asset_class=AssetClass.STOCK  # → Verwendet AlpacaProvider (Stock)
)
```

## Event-Bus Integration

Crypto-Daten werden über den Event-Bus publiziert:

### Events

1. **MARKET_DATA_CONNECTED**
   ```python
   {
       "source": "AlpacaCryptoStream",
       "asset_class": "crypto"
   }
   ```

2. **MARKET_BAR** (Crypto OHLCV Bar)
   ```python
   {
       "symbol": "BTC/USD",
       "asset_class": "crypto",
       "open": 45000.0,
       "high": 45500.0,
       "low": 44800.0,
       "close": 45200.0,
       "volume": 123.45,
       "timestamp": "2025-01-01T12:00:00Z",
       "source": "AlpacaCryptoStream"
   }
   ```

3. **MARKET_DATA_TICK** (Crypto Trade)
   ```python
   {
       "symbol": "ETH/USD",
       "asset_class": "crypto",
       "price": 2500.0,
       "size": 10.5,
       "source": "AlpacaCryptoStream"
   }
   ```

### Event-Listener registrieren

```python
from src.common.event_bus import event_bus, EventType

def on_crypto_tick(event):
    data = event.data
    if data.get("asset_class") == "crypto":
        print(f"{data['symbol']}: ${data['price']}")

# Listener registrieren
event_bus.on(EventType.MARKET_DATA_TICK, on_crypto_tick)
```

## Konfiguration

Crypto-Support wird automatisch aktiviert, wenn Alpaca in der Konfiguration enabled ist:

**`config/profiles/default.yaml`**:
```yaml
market_data:
  alpaca_enabled: true  # Aktiviert BEIDE: Stock UND Crypto Provider
  prefer_live_broker: false
```

**Credentials** (`.env` oder `config/secrets/.env`):
```bash
ALPACA_API_KEY=your_alpaca_key
ALPACA_API_SECRET=your_alpaca_secret
```

**Wichtig**: Dieselben Alpaca-Credentials funktionieren sowohl für Stock- als auch für Crypto-Daten.

## Rate Limits

Alpaca Crypto API Limits (Free Tier):

- **REST API**: 200 Aufrufe/Minute
- **WebSocket**: Unbegrenzte Verbindungen
- **Concurrent Symbols**: Unbegrenzt (im Gegensatz zu Stock IEX Feed mit 30 Symbols)

Der Provider respektiert automatisch Rate Limits (`rate_limit_delay = 0.3s`).

## Tests

Tests ausführen:

```bash
# Alle Crypto-Tests
pytest tests/test_crypto_integration.py -v

# Spezifischer Test
pytest tests/test_crypto_integration.py::TestAlpacaCryptoProvider::test_fetch_btc_bars -v

# Mit Logging
pytest tests/test_crypto_integration.py -v -s
```

**Voraussetzung**: Alpaca Credentials in Umgebungsvariablen:
```bash
export ALPACA_API_KEY=your_key
export ALPACA_API_SECRET=your_secret
```

## Demo

Demo-Script ausführen:

```bash
# Alle Demos
python tools/demo_crypto_integration.py

# Nur bestimmte Demo (im Code auskommentieren/einkommentieren)
# - demo_crypto_historical_data()
# - demo_crypto_streaming()
# - demo_history_manager_crypto()
# - demo_multiple_crypto_pairs()
```

## Sicherheitshinweise

⚠️ **Wichtige Trading-Sicherheitsregeln**:

1. **Paper-Trading Standard**: Crypto-Daten nutzen dieselben Credentials wie Stock-Daten. Stelle sicher, dass du Paper-Trading-Keys verwendest für Tests.

2. **Keine Real-Crypto-Trades ohne explizite Anweisung**: Die aktuelle Implementation deckt NUR Market Data ab, NICHT Trading. Crypto-Trading-Funktionalität muss separat implementiert werden.

3. **API-Key-Sicherheit**:
   - NIEMALS API-Keys ins Repository committen
   - Verwende `.env` Dateien (bereits in `.gitignore`)
   - Rotiere Keys regelmäßig

## Troubleshooting

### Problem: "No data found for BTC/USD"

**Lösung**:
- Prüfe, ob Alpaca-Credentials korrekt sind
- Stelle sicher, dass das Symbol korrekt ist (z.B. `BTC/USD`, nicht `BTCUSD`)
- Prüfe Zeitbereich (zu weit in der Vergangenheit?)

### Problem: "Alpaca SDK not available"

**Lösung**:
```bash
pip install alpaca-py
```

### Problem: WebSocket Connection Failed

**Lösung**:
- Prüfe Internet-Verbindung
- Prüfe Firewall-Einstellungen (Port 443)
- Prüfe Alpaca API Status: https://status.alpaca.markets/

## Weiterführende Dokumentation

- [Alpaca Crypto Pricing Data](docs/alpaca/docs.alpaca.markets/docs/crypto-pricing-data.html)
- [Alpaca Crypto Trading](docs/alpaca/docs.alpaca.markets/docs/crypto-trading.html)
- [Alpaca WebSocket Spec](docs/alpaca/docs.alpaca.markets/docs/real-time-crypto-pricing-data.html)
- [OpenAPI Spec](docs/alpaca/alpaca_openapi/market-data-api.json)

## Crypto Trading Strategien

OrderPilot-AI beinhaltet **3 vorgefertigte Crypto-Strategien**:

### 1. Volatility Breakout (`crypto_volatility_breakout.yaml`)

**Strategie-Typ**: Trend Following
**Best for**: Trending Crypto Markets mit hoher Volatilität

- **Entry Long**: Preis bricht über SMA + (2 × ATR) + RSI > 50
- **Exit Long**: Preis fällt unter SMA - (1.5 × ATR)
- **Indikatoren**: SMA(50), ATR(14), RSI(14)
- **Risk/Reward**: 3% Stop Loss / 9% Take Profit (1:3 R/R)
- **Trailing Stop**: Ja (aktiviert bei +4.5%)

**Verwendung**:
```bash
# Backtest mit Strategie
python tools/demo_crypto_strategies.py
```

### 2. Mean Reversion (`crypto_mean_reversion.yaml`)

**Strategie-Typ**: Mean Reversion
**Best for**: Range-bound / Seitwärts-Märkte

- **Entry Long**: Preis ≤ Lower Bollinger Band + RSI < 30
- **Exit Long**: Preis erreicht Middle Bollinger Band
- **Entry Short**: Preis ≥ Upper Bollinger Band + RSI > 70
- **Exit Short**: Preis erreicht Middle Bollinger Band
- **Indikatoren**: BBANDS(20, 2.0), RSI(14), ATR(14)
- **Risk/Reward**: 2.5% Stop Loss / 5% Take Profit (1:2 R/R)

**Hinweis**: Funktioniert NICHT in starken Trends!

### 3. Momentum Combo (`crypto_momentum_combo.yaml`)

**Strategie-Typ**: Momentum
**Best for**: Klare Trends mit Momentum

- **Entry Long**: MACD Bullish Crossover + RSI 50-70 + Preis > EMA(50) + EMA(50) > EMA(200)
- **Exit Long**: MACD Bearish Crossover ODER RSI > 80 ODER Preis < EMA(50)
- **Indikatoren**: MACD(12,26,9), RSI(14), EMA(50), EMA(200), ATR(14)
- **Risk/Reward**: ATR-basiert (2.5 × ATR Stop / 5 × ATR Target)
- **Trailing Stop**: Ja (aktiviert bei +5%)

**Verwendung**:
```python
from src.core.strategy.loader import StrategyLoader

loader = StrategyLoader()
strategy = loader.load_strategy_from_file("examples/strategies/crypto_momentum_combo.yaml")

# Strategie kompilieren
from src.core.strategy.compiler import StrategyCompiler
compiler = StrategyCompiler()
compiled_strategy = compiler.compile(strategy)
```

### Strategien verwenden

```bash
# Alle Strategien anzeigen
python tools/demo_crypto_strategies.py

# Tests ausführen
pytest tests/test_crypto_strategies.py -v

# Backtest ausführen (via UI)
# 1. OrderPilot-AI starten
# 2. Chart öffnen für BTC/USD, ETH/USD, etc.
# 3. Strategy Tab → Strategie auswählen
# 4. Backtest Tab → Run Backtest
```

## UI Integration

### Watchlist

Die Watchlist hat jetzt einen **"Crypto" Quick-Add Button**:

```
[Indices] [Tech] [Crypto] [Clear]
```

Klicke auf **"Crypto"** um automatisch hinzuzufügen:
- BTC/USD (Bitcoin)
- ETH/USD (Ethereum)
- SOL/USD (Solana)
- AVAX/USD (Avalanche)
- MATIC/USD (Polygon)

### Chart

Der Chart **funktioniert automatisch** mit Crypto-Symbolen:
- Doppelklick auf Crypto-Symbol in Watchlist → Chart öffnet sich
- Chart lädt automatisch Crypto-Daten (erkennt "/" im Symbol)
- Live-Streaming nutzt `start_crypto_realtime_stream()`

### Portfolio

Das Portfolio/Positions Widget **funktioniert automatisch** mit Crypto:
- Zeigt Crypto-Positionen genauso wie Stock-Positionen
- Real-time Preis-Updates via MARKET_TICK Events
- Keine Änderungen nötig!

## Nächste Schritte

- [x] ✅ Crypto Market Data Integration
- [x] ✅ Crypto Streaming (WebSocket)
- [x] ✅ Crypto Trading Strategien (3 Strategien)
- [x] ✅ UI Integration (Watchlist, Chart, Portfolio)
- [ ] Crypto Trading API Integration (Orders, Positions) - **NICHT implementiert** (nur Market Data)
- [ ] Crypto Wallet Management
- [ ] Crypto Portfolio Tracking (Live-Anzeige)
- [ ] Multi-Pair Arbitrage Strategien
- [ ] Crypto-spezifische Risk Management Tools
