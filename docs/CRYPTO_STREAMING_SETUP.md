# Live Crypto Data Streaming - Setup Guide

Dieser Guide erklärt, wie Sie Live-Crypto-Kursdaten über Alpaca's WebSocket API in OrderPilot-AI integrieren.

## 🎯 Features

- ✅ **Echtzeit-Daten** für BTC/USD, ETH/USD, SOL/USD, DOGE/USD und weitere
- ✅ **Free Account kompatibel** - funktioniert mit kostenlosem Alpaca-Account
- ✅ **WebSocket Streaming** - niedrige Latenz, kontinuierliche Updates
- ✅ **Automatische Reconnects** - stabile Verbindung
- ✅ **Event-basiert** - Integration mit OrderPilot's Event-System

## 📋 Voraussetzungen

1. **Alpaca Account** (kostenlos)
   - Registrieren Sie sich bei: https://app.alpaca.markets/signup
   - Wählen Sie **"Paper Trading"** für risikofreies Testen

2. **API Keys** (Paper Trading)
   - Gehen Sie zu: https://app.alpaca.markets/paper/dashboard/overview
   - Navigieren Sie zu **"API Keys"**
   - Klicken Sie auf **"Generate New Key"**
   - ⚠️ **Wichtig**: Kopieren Sie sowohl den **Key** als auch das **Secret** sofort!

## 🔧 Installation & Konfiguration

### Schritt 1: API Keys eintragen

Öffnen Sie die Datei `config/secrets/.env` und ersetzen Sie die Platzhalter:

```env
# Alpaca API Keys (Paper Trading)
ALPACA_API_KEY=PKxxxxxxxxxxxxxxxxxxxxxx
ALPACA_API_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**Beispiel:**
```env
ALPACA_API_KEY=PKABCDEF1234567890
ALPACA_API_SECRET=abcdef1234567890abcdef1234567890abcdef12
```

### Schritt 2: Crypto-Trading aktivieren (bereits erledigt ✅)

Die Datei `config/paper.yaml` wurde bereits angepasst:

```yaml
features:
  crypto_trading: true  # ✅ Aktiviert
```

### Schritt 3: Anwendung starten

```bash
python start_orderpilot.py
```

## 🎨 UI-Anzeige

Nach dem Start sehen Sie in der Toolbar rechts oben einen neuen Status-Indikator:

- **"Crypto: Off"** (grau) - Feature nicht aktiviert
- **"Crypto: No Keys"** (orange) - API-Keys fehlen
- **"Crypto: Live"** (grün, fett) - ✅ Streaming aktiv!
- **"Crypto: Error"** (orange) - Verbindungsfehler

**Tooltip** zeigt abonnierte Symbole:
```
Live Crypto Data Stream: Connected
Subscribed to: BTC/USD, ETH/USD, SOL/USD, DOGE/USD
```

## 📊 Verfügbare Daten

Der Stream liefert drei Arten von Daten:

### 1. **Bars** (OHLCV Candlesticks)
- 1-Minuten-Aggregationen
- Open, High, Low, Close, Volume
- VWAP (Volume Weighted Average Price)
- Trade Count

### 2. **Trades** (Einzelne Transaktionen)
- Preis und Größe jeder Transaktion
- Timestamp
- Exchange-Informationen

### 3. **Quotes** (Bid/Ask)
- Bid-Preis und Bid-Größe
- Ask-Preis und Ask-Größe
- Spread-Berechnung möglich

## 🔍 Verfügbare Crypto-Paare

Aktuell abonniert:
- **BTC/USD** - Bitcoin
- **ETH/USD** - Ethereum
- **SOL/USD** - Solana
- **DOGE/USD** - Dogecoin

### Weitere unterstützte Paare:

**USD-Paare:**
- ADA/USD, AVAX/USD, BCH/USD, DOT/USD, LTC/USD, MATIC/USD, SHIB/USD, UNI/USD, XRP/USD

**USDT-Paare:**
- BTC/USDT, ETH/USDT, SOL/USDT

**Crypto-zu-Crypto:**
- ETH/BTC

### Abonnement ändern

In `src/ui/app.py`, Zeile ~529:

```python
# Subscribe to popular crypto pairs
crypto_symbols = ["BTC/USD", "ETH/USD", "SOL/USD", "DOGE/USD"]
await self.crypto_stream.subscribe(crypto_symbols)
```

Fügen Sie weitere Symbole hinzu oder entfernen Sie welche nach Bedarf.

## 📈 Rate Limits (Free Account)

- **REST API**: ~200 requests/minute
- **WebSocket**: ~30 simultane Subscriptions
- **Für die meisten Trading-Apps völlig ausreichend!**

## 🐛 Troubleshooting

### Problem: "Crypto: No Keys"

**Lösung:**
1. Prüfen Sie, ob `.env` existiert: `config/secrets/.env`
2. Prüfen Sie, ob die Keys **nicht** die Platzhalter-Werte enthalten
3. API-Keys dürfen **keine** Leerzeichen enthalten

### Problem: "Crypto: Error"

**Mögliche Ursachen:**
1. **Ungültige API-Keys** - Neue Keys generieren
2. **Netzwerkprobleme** - Firewall/Proxy prüfen
3. **Rate Limit erreicht** - Warten Sie 1 Minute

**Debug-Logs:**
```bash
# Logs finden Sie in:
logs/orderpilot_YYYYMMDD.log

# Suchen Sie nach:
grep "crypto" logs/orderpilot_*.log
```

### Problem: Keine Daten empfangen

1. **Prüfen Sie den Status:**
   - Tooltip des "Crypto: Live" Labels zeigt abonnierte Symbole

2. **Prüfen Sie die Logs:**
   ```bash
   grep "Received crypto" logs/orderpilot_*.log
   ```

   Sie sollten sehen:
   ```
   📊 Received crypto bar: BTC/USD OHLC: 43000/43100/42900/43050 Vol: 1.5
   🔔 Received crypto trade: ETH/USD @ $2300.50 (size: 0.5)
   ```

3. **Marktöffnungszeiten:**
   - Crypto-Märkte sind **24/7 geöffnet**
   - Sie sollten immer Daten empfangen!

## 🔐 Sicherheit

1. **`.env` niemals committen!**
   - Die Datei ist bereits in `.gitignore`

2. **Paper Trading verwenden**
   - Nur für Tests echte Live-Keys verwenden

3. **Keys regelmäßig rotieren**
   - Generieren Sie neue Keys alle 3-6 Monate

## 📚 Event-Integration

Die Stream-Daten werden über das Event-System verteilt:

### Event-Typen:

```python
EventType.MARKET_DATA_CONNECTED   # Stream verbunden
EventType.MARKET_DATA_DISCONNECTED # Stream getrennt
EventType.MARKET_BAR              # Neue Bar (OHLCV)
EventType.MARKET_DATA_TICK        # Neuer Trade
```

### Event-Handler registrieren:

```python
from src.common.event_bus import event_bus, EventType

def on_crypto_bar(event):
    data = event.data
    print(f"Bar: {data['symbol']} @ {data['close']}")

event_bus.subscribe(EventType.MARKET_BAR, on_crypto_bar)
```

## 📖 Weiterführende Links

- **Alpaca Crypto Docs**: https://docs.alpaca.markets/docs/real-time-crypto-pricing-data
- **Alpaca API Keys**: https://app.alpaca.markets/paper/dashboard/overview
- **WebSocket Protocol**: https://docs.alpaca.markets/docs/streaming-real-time-market-data
- **Supported Symbols**: https://alpaca.markets/support/what-crypto-does-alpaca-support

## 🎉 Fertig!

Ihre Live-Crypto-Daten-Integration ist jetzt aktiv! Sie erhalten Echtzeit-Updates für alle abonnierten Kryptowährungen.

Bei Fragen oder Problemen öffnen Sie ein Issue auf GitHub oder konsultieren Sie die Alpaca-Dokumentation.

**Happy Trading! 🚀**
