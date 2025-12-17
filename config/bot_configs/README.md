# Bot Konfigurationen

Dieses Verzeichnis enthält Beispiel-Konfigurationen für den OrderPilot-AI Tradingbot.

## Verfügbare Konfigurationen

| Datei | Markt | Risiko | KI-Modus | Beschreibung |
|-------|-------|--------|----------|--------------|
| `crypto_conservative.json` | Crypto | LOW | NO_KI | Konservativ, Capital Preservation |
| `crypto_aggressive.json` | Crypto | HIGH | FULL_KI | Aggressiv, mehr Trades |
| `nasdaq_conservative.json` | NASDAQ | LOW | LOW_KI | Konservativ, nur RTH |
| `nasdaq_aggressive.json` | NASDAQ | HIGH | FULL_KI | Aggressiv, inkl. ETH |

## Risiko-Level Übersicht

### LOW (Konservativ)
- Risk per Trade: 0.5%
- Max Daily Loss: 2-3%
- Weniger Trades pro Tag (3-5)
- Engere Stops
- Höhere Entry-Score-Schwelle

### HIGH (Aggressiv)
- Risk per Trade: 1.5-2%
- Max Daily Loss: 5-8%
- Mehr Trades pro Tag (10-15)
- Weitere Stops (mehr Raum für Volatilität)
- Niedrigere Entry-Score-Schwelle

## KI-Modi

- **NO_KI**: Rein regelbasiert, keine API-Kosten
- **LOW_KI**: 1 LLM-Call pro Tag für Strategy Selection
- **FULL_KI**: Intraday Events (RegimeFlip, ExitCandidate, SignalChange)

## Verwendung

```python
from src.core.tradingbot import FullBotConfig
import json

# Config laden
with open("config/bot_configs/crypto_conservative.json") as f:
    config_dict = json.load(f)

# BotConfig erstellen
config = FullBotConfig.from_dict(config_dict)
```

## Anpassung

Kopiere eine der Beispiel-Konfigurationen und passe sie an deine Bedürfnisse an.
Die wichtigsten Parameter:

1. **symbol**: Das zu handelnde Symbol (z.B. "BTC/USD", "AAPL")
2. **initial_stop_loss_pct**: Einziger fixer Parameter - der initiale Stop-Loss
3. **risk_per_trade_pct**: Bestimmt die Positionsgröße
4. **trailing_mode**: PCT, ATR oder SWING

## Warnung

⚠️ **RISIKO-HINWEIS**:
- Automatisierter Handel birgt erhebliche Risiken
- Vergangene Performance garantiert keine zukünftigen Ergebnisse
- Handeln Sie nur mit Kapital, dessen Verlust Sie verkraften können
- Diese Software ist KEINE Anlageberatung
- Testen Sie immer zuerst im Paper-Modus!
