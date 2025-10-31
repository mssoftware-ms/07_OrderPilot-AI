# Real-Time Market Data and Technical Indicators

OrderPilot-AI now supports real-time market data streaming and technical indicator calculations powered by Alpha Vantage.

## Features

### ✅ Implemented Features

1. **Real-Time Market Data Streaming**
   - Live price quotes
   - Volume data
   - Polling-based updates (60-second intervals for free tier)
   - Multi-symbol support

2. **Technical Indicators**
   - **RSI (Relative Strength Index)**
     - Period: 14 (configurable)
     - Real-time and historical data
     - Overbought/oversold detection

   - **MACD (Moving Average Convergence Divergence)**
     - Fast period: 12 (default)
     - Slow period: 26 (default)
     - Signal period: 9 (default)
     - Histogram calculations
     - Bullish/bearish signal detection

3. **Intraday Bars**
   - 1-minute, 5-minute, 15-minute, 30-minute, 60-minute
   - Historical intraday data (20+ years via Alpha Vantage)
   - Real-time updates

4. **Event-Driven Architecture**
   - Market tick events
   - Indicator calculation events
   - Connection status events

## Setup

### 1. Get Alpha Vantage API Key

Get a free API key from [Alpha Vantage](https://www.alphavantage.co/support/#api-key).

### 2. Configure API Key

**Option A: Using Configuration File**

Edit your trading profile config (e.g., `config/profiles/paper.yaml`):

```yaml
market_data:
  alpha_vantage_enabled: true
  # ... other settings
```

Then add the credential using the credential manager:

```python
from src.config.loader import config_manager

config_manager.store_credential("alpha_vantage_api_key", "YOUR_API_KEY_HERE")
```

**Option B: Using Environment Variable**

```bash
export ALPHA_VANTAGE_API_KEY="YOUR_API_KEY_HERE"
```

### 3. Enable in Configuration

In your profile config (`config/profiles/paper.yaml`):

```yaml
market_data:
  alpha_vantage_enabled: true
  finnhub_enabled: false
  yahoo_enabled: true
  prefer_live_broker: false
```

## Usage

### Basic Usage - Historical Indicators

```python
from src.core.market_data.history_provider import HistoryManager
from datetime import datetime, timedelta

# Initialize history manager
history_manager = HistoryManager()

# Fetch RSI and MACD
indicators = await history_manager.fetch_realtime_indicators(
    symbol="AAPL",
    interval="1min"  # or "5min", "15min", "30min", "60min", "daily"
)

# Access RSI
if "rsi" in indicators:
    rsi = indicators["rsi"]
    print(f"RSI: {rsi['value']}")  # Current RSI value
    print(f"Timestamp: {rsi['timestamp']}")

    # Interpret
    if rsi['value'] > 70:
        print("OVERBOUGHT")
    elif rsi['value'] < 30:
        print("OVERSOLD")

# Access MACD
if "macd" in indicators:
    macd = indicators["macd"]
    print(f"MACD: {macd['macd']}")
    print(f"Signal: {macd['signal']}")
    print(f"Histogram: {macd['histogram']}")

    # Interpret
    if macd['histogram'] > 0:
        print("BULLISH signal")
    else:
        print("BEARISH signal")
```

### Real-Time Streaming

```python
import asyncio
from src.core.market_data.history_provider import HistoryManager
from src.common.event_bus import Event, EventType, event_bus

# Setup event handler
async def on_market_tick(event: Event):
    data = event.data
    print(f"Price update: {data['symbol']} ${data['price']}")

async def on_indicator_update(event: Event):
    data = event.data
    if 'rsi' in data:
        print(f"RSI: {data['rsi']}")
    if 'macd' in data:
        print(f"MACD: {data['macd']}")

# Subscribe to events
event_bus.subscribe(EventType.MARKET_DATA_TICK, on_market_tick)
event_bus.subscribe(EventType.INDICATOR_CALCULATED, on_indicator_update)

# Initialize and start streaming
history_manager = HistoryManager()

# Start streaming for specific symbols
success = await history_manager.start_realtime_stream(
    symbols=["AAPL", "MSFT", "GOOGL"],
    enable_indicators=True  # Enable real-time RSI/MACD calculations
)

if success:
    print("Stream started successfully")

    # Let it run for 5 minutes
    await asyncio.sleep(300)

    # Get metrics
    metrics = history_manager.get_stream_metrics()
    print(f"Messages received: {metrics['messages_received']}")
    print(f"Average latency: {metrics['average_latency_ms']}ms")

    # Stop streaming
    await history_manager.stop_realtime_stream()
```

### Intraday Historical Data

```python
from src.core.market_data.history_provider import (
    DataRequest,
    HistoryManager,
    Timeframe,
    DataSource
)
from datetime import datetime, timedelta

history_manager = HistoryManager()

# Request intraday bars
request = DataRequest(
    symbol="AAPL",
    start_date=datetime.utcnow() - timedelta(days=7),
    end_date=datetime.utcnow(),
    timeframe=Timeframe.MINUTE_5,  # 5-minute bars
    source=DataSource.ALPHA_VANTAGE  # Optional: force specific source
)

bars, source = await history_manager.fetch_data(request)

for bar in bars[-10:]:  # Last 10 bars
    print(f"{bar.timestamp}: O:{bar.open} H:{bar.high} L:{bar.low} C:{bar.close} V:{bar.volume}")
```

### Access Alpha Vantage Provider Directly

```python
from src.core.market_data.history_provider import HistoryManager, DataSource

history_manager = HistoryManager()

# Get Alpha Vantage provider
if DataSource.ALPHA_VANTAGE in history_manager.providers:
    av_provider = history_manager.providers[DataSource.ALPHA_VANTAGE]

    # Fetch RSI
    rsi_series = await av_provider.fetch_rsi(
        symbol="AAPL",
        interval="1min",
        time_period=14,
        series_type="close"
    )

    # Fetch MACD
    macd_df = await av_provider.fetch_macd(
        symbol="AAPL",
        interval="1min",
        fast_period=12,
        slow_period=26,
        signal_period=9
    )

    print(f"Latest RSI: {rsi_series.iloc[-1]}")
    print(f"Latest MACD: {macd_df.iloc[-1]}")
```

## Rate Limits

### Free Tier Limits
- **API calls**: 25 requests per day
- **Intraday data**: End-of-day updates only
- **Polling interval**: Minimum 60 seconds

### Premium Tier Benefits
- **API calls**: 75-1200 requests per day (depending on plan)
- **Real-time intraday**: Yes
- **Polling interval**: Can be reduced to 1 second

To optimize API usage:
1. Cache indicator results locally
2. Use longer polling intervals (60-300 seconds)
3. Subscribe only to actively traded symbols
4. Consider upgrading for production use

## Architecture

### Components

```
┌─────────────────────────────────────────────────┐
│           HistoryManager                        │
│  ┌───────────────────────────────────────────┐ │
│  │  Data Providers                            │ │
│  │  - AlphaVantageProvider                    │ │
│  │  - IBKRHistoricalProvider                  │ │
│  │  - YahooFinanceProvider                    │ │
│  │  - DatabaseProvider                        │ │
│  └───────────────────────────────────────────┘ │
│  ┌───────────────────────────────────────────┐ │
│  │  Stream Client                             │ │
│  │  - AlphaVantageStreamClient               │ │
│  │    * Polling loop                          │ │
│  │    * Event emission                        │ │
│  │    * Indicator fetching                    │ │
│  └───────────────────────────────────────────┘ │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│           Event Bus                             │
│  - MARKET_DATA_TICK                            │
│  - INDICATOR_CALCULATED                        │
│  - MARKET_DATA_CONNECTED                       │
│  - MARKET_DATA_DISCONNECTED                    │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│           Application                           │
│  - UI widgets                                   │
│  - Trading strategies                          │
│  - Order execution                             │
└─────────────────────────────────────────────────┘
```

### Data Flow

1. **Streaming Mode**:
   ```
   Poll Timer → API Request → Parse Response →
   Store in Buffer → Emit Event → Update UI
   ```

2. **Indicator Calculation**:
   ```
   Request Indicator → Fetch from API →
   Parse Data → Cache → Emit Event → Update UI
   ```

## Events

### EventType.MARKET_DATA_TICK

Emitted when new market data arrives:

```python
{
    "symbol": "AAPL",
    "price": 150.25,
    "volume": 1234567,
    "source": "AlphaVantageStream"
}
```

### EventType.INDICATOR_CALCULATED

Emitted when indicators are calculated:

```python
{
    "symbol": "AAPL",
    "source": "AlphaVantageStream",
    "rsi": 65.32,
    "macd": {
        "macd": 1.23,
        "signal": 1.10,
        "histogram": 0.13
    }
}
```

### EventType.MARKET_DATA_CONNECTED

Emitted when stream connects:

```python
{
    "source": "AlphaVantageStream"
}
```

### EventType.MARKET_DATA_DISCONNECTED

Emitted when stream disconnects:

```python
{
    "source": "AlphaVantageStream"
}
```

## Examples

See the complete example in `examples/realtime_indicators_demo.py`:

```bash
# Make sure to activate venv first
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Run the demo
python examples/realtime_indicators_demo.py
```

The demo showcases:
- Historical data fetching
- Real-time indicator calculations
- Live streaming with multiple symbols
- Event handling
- Metrics monitoring

## Troubleshooting

### "API key not found" Error

**Solution**: Set your Alpha Vantage API key in the configuration:

```python
from src.config.loader import config_manager
config_manager.store_credential("alpha_vantage_api_key", "YOUR_KEY")
```

### "No data available" Warning

**Possible causes**:
1. Invalid symbol
2. API rate limit exceeded
3. Network connectivity issues
4. Alpha Vantage service outage

**Solution**: Check the logs for detailed error messages.

### Stream Not Updating

**Possible causes**:
1. Polling interval too long (60s minimum on free tier)
2. No active subscriptions
3. API rate limits

**Solution**: Check stream metrics:

```python
metrics = history_manager.get_stream_metrics()
print(metrics)
```

### High Latency

**Possible causes**:
1. Network issues
2. Alpha Vantage server load
3. Too many subscriptions

**Solution**:
- Reduce number of subscribed symbols
- Increase polling interval
- Consider premium tier for better performance

## Future Enhancements

Planned features:
- WebSocket support (when available from Alpha Vantage)
- More technical indicators (Bollinger Bands, Stochastic, etc.)
- Custom indicator calculations
- Multi-source aggregation
- Tick-level data
- Level 2 market data (premium)

## API Reference

### HistoryManager

#### Methods

- `start_realtime_stream(symbols, enable_indicators=True)` - Start streaming
- `stop_realtime_stream()` - Stop streaming
- `get_realtime_tick(symbol)` - Get latest tick
- `get_stream_metrics()` - Get stream metrics
- `fetch_realtime_indicators(symbol, interval)` - Fetch indicators

### AlphaVantageProvider

#### Methods

- `fetch_rsi(symbol, interval, time_period, series_type)` - Fetch RSI
- `fetch_macd(symbol, interval, fast_period, slow_period, signal_period)` - Fetch MACD
- `fetch_technical_indicator(symbol, indicator, interval, time_period)` - Generic indicator fetch

### AlphaVantageStreamClient

#### Methods

- `connect()` - Connect to stream
- `disconnect()` - Disconnect from stream
- `subscribe(symbols)` - Subscribe to symbols
- `unsubscribe(symbols)` - Unsubscribe from symbols
- `get_latest_tick(symbol)` - Get latest tick
- `get_metrics()` - Get stream metrics

## License

This feature integrates with Alpha Vantage API. Please review [Alpha Vantage Terms of Service](https://www.alphavantage.co/terms_of_service/).
