# Quick Start: Real-Time Indicators

Get started with real-time RSI and MACD indicators in 5 minutes.

## Step 1: Get API Key (1 minute)

1. Visit [Alpha Vantage](https://www.alphavantage.co/support/#api-key)
2. Enter your email
3. Get your free API key instantly

## Step 2: Configure (2 minutes)

```python
# Set your API key
from src.config.loader import config_manager

config_manager.store_credential(
    "alpha_vantage_api_key",
    "YOUR_API_KEY_HERE"
)
```

Enable in `config/profiles/paper.yaml`:
```yaml
market_data:
  alpha_vantage_enabled: true
```

## Step 3: Use It! (2 minutes)

### Get RSI and MACD for a Symbol

```python
import asyncio
from src.core.market_data.history_provider import HistoryManager

async def get_indicators():
    # Initialize
    manager = HistoryManager()

    # Fetch indicators
    indicators = await manager.fetch_realtime_indicators(
        symbol="AAPL",
        interval="1min"
    )

    # Show RSI
    if "rsi" in indicators:
        rsi = indicators["rsi"]["value"]
        print(f"RSI: {rsi:.2f}")

        if rsi > 70:
            print("⚠️ OVERBOUGHT")
        elif rsi < 30:
            print("⚠️ OVERSOLD")

    # Show MACD
    if "macd" in indicators:
        macd = indicators["macd"]
        print(f"MACD: {macd['macd']:.4f}")
        print(f"Signal: {macd['signal']:.4f}")

        if macd['histogram'] > 0:
            print("📈 BULLISH")
        else:
            print("📉 BEARISH")

# Run it
asyncio.run(get_indicators())
```

### Start Real-Time Streaming

```python
import asyncio
from src.core.market_data.history_provider import HistoryManager
from src.common.event_bus import Event, EventType, event_bus

async def stream_data():
    # Setup event handler
    async def on_update(event: Event):
        data = event.data
        if 'rsi' in data:
            print(f"RSI Update: {data['rsi']}")
        if 'macd' in data:
            print(f"MACD Update: {data['macd']}")

    event_bus.subscribe(EventType.INDICATOR_CALCULATED, on_update)

    # Start streaming
    manager = HistoryManager()
    await manager.start_realtime_stream(
        symbols=["AAPL"],
        enable_indicators=True
    )

    # Run for 5 minutes
    await asyncio.sleep(300)

    # Stop
    await manager.stop_realtime_stream()

# Run it
asyncio.run(stream_data())
```

## That's It! 🎉

You now have:
- ✅ Real-time RSI indicators
- ✅ Real-time MACD indicators
- ✅ Intraday price data
- ✅ Event-driven updates

## Next Steps

- Read the full [documentation](REALTIME_INDICATORS.md)
- Run the [demo script](../examples/realtime_indicators_demo.py)
- Integrate with your trading strategies
- Build custom chart widgets

## Common Issues

**"API key not found"**: Make sure you called `store_credential()` with your key.

**"No data available"**: Check that `alpha_vantage_enabled: true` in your config.

**Too many requests**: Free tier has 25 requests/day limit. Consider upgrading.

## Support

Need help? Check:
- [Full Documentation](REALTIME_INDICATORS.md)
- [Alpha Vantage Docs](https://www.alphavantage.co/documentation/)
- Project GitHub issues
