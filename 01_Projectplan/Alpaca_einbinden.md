Kurz & praxisnah zu **Alpaca Market Data** (für deine RSI/MACD-Echtzeit-Signale in OrderPilot-AI):

## Was du kostenlos bekommst (Plan “Basic”)

* **Realtime-Feed:** **IEX** (kein konsolidierter SIP); WebSocket-URL: `wss://stream.data.alpaca.markets/v2/iex`. ([Alpaca API Docs][1])
* **Limits:** **30 Symbole** gleichzeitig über WS, **200 REST-Calls/min**. ([Alpaca][2])
* **Kanäle:** `trades`, `quotes`, `bars` (Minute), `updatedBars` (late trade fix), `dailyBars`. ([Alpaca API Docs][3])
* **Auth & Subscribe (WS):** per Header **oder** JSON-Message
  `{"action":"auth","key":"<KEY>","secret":"<SECRET>"}` → danach `{"action":"subscribe","bars":["AAPL","QQQ"]}`. ([Alpaca API Docs][4])
* **Test-Stream:** `wss://stream.data.alpaca.markets/v2/test` (Symbol **FAKEPACA**), nützlich für deinen Qt-WS-Client. ([Alpaca API Docs][4])

> Für **Nasdaq-100/Dow** nimm im Free-Setup am besten die **ETF-Proxys** **QQQ** (NDX) und **DIA** (DJI), die du über den IEX-WS bekommst. (SIP ist erst im $99-Plan.) ([Alpaca][2])

## Einbindung in deine Architektur (ohne asyncio/qasync)

Dein Event-Bus hat schon `MARKET_BAR`. Hänge den Alpaca-WS wie folgt ein (Qt-Loop bleibt sauber):

1. **Verbinden:** `wss://stream.data.alpaca.markets/v2/iex`
2. **Auth-Message schicken** (s.o.) → auf `authenticated` warten. ([Alpaca API Docs][4])
3. **Subscribe** auf `bars` deiner Symbole (z. B. AAPL, NVDA, **QQQ**, **DIA**). ([Alpaca API Docs][3])
4. Eingehende **Bar-Messages** (`T:"b"`) in dein `HistoryManager`/Cache mappen und als `MARKET_BAR` publishen (Schema enthält `o,h,l,c,v,t`). ([Alpaca API Docs][3])
5. Dein vorhandener **IndicatorService** (RSI 14 / MACD 12-26-9 / ATR 14) triggert Buy + Stop-Loss; Render via PyQtGraph.

> Tipp: Die meisten Abos erlauben **nur 1 aktive WS-Connection** – plane Multiplexing im Backend. Sonst kommt Fehler **406 connection limit exceeded**. ([Alpaca API Docs][4])

## Alternative (wenn du doch asyncio willst)

Mit dem offiziellen **Python-SDK** (`alpaca-py`) geht Streaming in ein paar Zeilen:

```python
from alpaca.data.live import StockDataStream

stream = StockDataStream('APCA-API-KEY-ID', 'APCA-API-SECRET-KEY')

@stream.on_bar("AAPL")
async def on_bar(bar):
    # mappe -> EventBus.publish(MARKET_BAR, ...)
    ...

stream.subscribe_bars(["AAPL","QQQ","DIA"])
stream.run()
```

(Docs & Beispiele hier.) ([Alpaca][5])

## Was du NICHT über Alpaca bekommst

**Spot Gold/Silber** liefert Alpaca nicht im Aktien-Feed. Behalte dafür deinen **Finnhub-WS** (Forex-Symbole wie `OANDA:XAU_USD`, `OANDA:XAG_USD`) und aggregiere → 1-Min-Bars; du hast das Aggregat schon skizziert. ([Alpaca API Docs][3])

---

### TL;DR – Empfehlung für OrderPilot-AI

* **US-Aktien/ETFs in Echtzeit:** Alpaca WS **IEX** (gratis) → `bars` an deinen Event-Bus. ([Alpaca API Docs][1])
* **Nasdaq/Dow als Proxy:** **QQQ/DIA** streamen (Index-Realtime ohne Lizenzkosten). ([Alpaca][2])
* **Limits beachten:** 30 Symbole/WS, 200 REST/min; ggf. Watchlist rotieren. ([Alpaca][2])
* **Metalle:** weiter über Finnhub (XAU/XAG).
  Wenn du willst, schreibe ich dir den **QWebSocket-Client** exakt für `src/core/market_data/stream_client.py` (Auth, Subscribe, Mapping → `MARKET_BAR`) in deinen Stil.

[1]: https://docs.alpaca.markets/docs/market-data-faq?utm_source=chatgpt.com "Market Data FAQ - Alpaca API Docs"
[2]: https://alpaca.markets/data "Alpaca - Unlimited Access, Real-time Market Data API"
[3]: https://docs.alpaca.markets/docs/real-time-stock-pricing-data "Real-time Stock Data"
[4]: https://docs.alpaca.markets/docs/streaming-market-data "WebSocket Stream"
[5]: https://alpaca.markets/sdks/python/market_data.html?utm_source=chatgpt.com "Market Data - Alpaca-py"
