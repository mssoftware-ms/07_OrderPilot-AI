# Watchlist & Charts - Quick Start

Schnelleinstieg in 3 Minuten! ⚡

## 1. Watchlist erstellen (1 Minute)

```bash
# Tool starten
python tools/manage_watchlist.py

# Indizes hinzufügen
>>> preset indices

# Oder einzelne Symbole
>>> add AAPL
>>> add MSFT
>>> add NVDA

# Speichern
>>> save

# Beenden
>>> quit
```

**Fertig!** Deine Watchlist ist jetzt gespeichert.

## 2. App starten (30 Sekunden)

```bash
# Aktiviere Virtual Environment (falls nicht aktiv)
source venv/bin/activate  # Linux/Mac
# oder
venv\Scripts\activate     # Windows

# App starten
python start_orderpilot.py
```

Die Watchlist erscheint automatisch links in der App!

## 3. Symbol anklicken (30 Sekunden)

### Chart öffnen
1. **Doppelklick** auf Symbol in Watchlist
2. → Chart öffnet sich automatisch

### Order platzieren
1. **Rechtsklick** auf Symbol
2. Wähle "New Order..."
3. → Order-Dialog öffnet sich

### Echtzeit aktivieren
1. Menu: **Trading → Connect Broker**
2. Wähle **Alpaca**
3. → Live-Preise in Watchlist! ✨

## Verfügbare Presets

```bash
# Im Management-Tool:

>>> preset indices          # QQQ, DIA, SPY, IWM, VTI
>>> preset tech            # AAPL, MSFT, GOOGL, AMZN, META, NVDA, TSLA
>>> preset finance         # JPM, BAC, WFC, GS, MS, C
>>> preset energy          # XOM, CVX, COP, SLB, EOG
>>> preset crypto_related  # COIN, MARA, RIOT, MSTR
>>> preset german          # SAP, SIE.DE, DTE.DE, VOW3.DE, BAS.DE
```

## Häufige Aktionen

| Aktion | Wie? |
|--------|------|
| **Symbol hinzufügen** | Eingabefeld oben + Enter |
| **Chart öffnen** | Doppelklick auf Symbol |
| **Order aufgeben** | Rechtsklick → "New Order" |
| **Symbol entfernen** | Rechtsklick → "Remove" |
| **Alle löschen** | Button "Clear" |
| **Indizes hinzufügen** | Button "Indices" |
| **Tech-Stocks** | Button "Tech" |

## Beispiel-Setups

### Setup 1: Index-Trader
```bash
>>> preset indices  # QQQ, DIA, SPY, IWM, VTI
```

### Setup 2: Tech-Fokus
```bash
>>> preset tech     # AAPL, MSFT, GOOGL, AMZN, META, NVDA, TSLA
>>> add QQQ         # + Nasdaq-Index
```

### Setup 3: Day-Trader
```bash
>>> add AAPL
>>> add MSFT
>>> add NVDA
>>> add QQQ
>>> add SPY
```

### Setup 4: Diversifiziert
```bash
>>> preset indices
>>> preset tech
>>> preset finance
# Jetzt hast du ~20 Symbole aus verschiedenen Sektoren
```

## Das war's! 🎉

Du kannst jetzt:
- ✅ Symbole in der Watchlist überwachen
- ✅ Charts mit einem Klick öffnen
- ✅ Orders direkt platzieren
- ✅ Echtzeit-Preise sehen (mit Alpaca)

## Nächste Schritte

1. **Echtzeit aktivieren**: [Alpaca Setup](docs/ALPACA_INTEGRATION.md)
2. **Indicators nutzen**: [RSI & MACD](docs/REALTIME_INDICATORS.md)
3. **Vollständige Anleitung**: [Watchlist & Charts](docs/WATCHLIST_UND_CHARTS.md)

## Tastenkürzel

| Taste | Aktion |
|-------|--------|
| **Ctrl+N** | Neue Order |
| **Ctrl+,** | Settings |
| **Ctrl+Q** | App beenden |

## Hilfe

```bash
# Im Management-Tool
>>> help

# Oder vollständige Doku lesen
docs/WATCHLIST_UND_CHARTS.md
```
