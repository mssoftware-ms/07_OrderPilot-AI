# Market Data Module

## Übersicht

Dieses Modul verwaltet alle Marktdaten-Operationen für OrderPilot-AI.

## Hauptkomponenten

### HistoryManager (`history_provider.py`)
- Zentrale Schnittstelle für historische Daten
- Wählt automatisch den besten Provider
- Verwaltet Streaming-Verbindungen

### Provider (`providers/`)
- `AlpacaProvider` - Alpaca Stock API (primär)
- `AlpacaCryptoProvider` - Alpaca Crypto API
- `YahooFinanceProvider` - Fallback für historische Daten
- `DatabaseProvider` - Lokaler Cache

## Verwendung

```python
from src.core.market_data.history_provider import HistoryManager, DataRequest
from src.core.market_data.types import Timeframe, AssetClass

manager = HistoryManager()
request = DataRequest(
    symbol="AAPL",
    start_date=datetime.now() - timedelta(days=30),
    end_date=datetime.now(),
    timeframe=Timeframe.MINUTE_1,
    asset_class=AssetClass.STOCK
)
bars, source = await manager.fetch_data(request)
```

## Erweiterung

Neuen Provider hinzufügen:
1. Neue Datei in `providers/` erstellen
2. Von `HistoricalDataProvider` erben
3. `fetch_historical()` implementieren
4. In `providers/__init__.py` exportieren
5. In `history_provider.py` registrieren
