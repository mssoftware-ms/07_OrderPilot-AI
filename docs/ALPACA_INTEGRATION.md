# Alpaca Integration for OrderPilot-AI

Complete integration guide for Alpaca Markets - real-time market data and commission-free trading.

## Overview

Alpaca provides:
- ✅ **Real-time WebSocket market data** (IEX feed - free tier)
- ✅ **Commission-free trading** (US stocks & ETFs)
- ✅ **Paper trading** (unlimited virtual money for testing)
- ✅ **Historical data API** (200 calls/min)
- ✅ **30 concurrent symbols** on free tier
- ✅ **Minute-level bars** in real-time

### Why Alpaca?

1. **Better than Alpha Vantage polling**: True WebSocket streaming (no 60-second delays!)
2. **Commission-free**: $0 per trade vs traditional brokers
3. **Real trading**: Not just data - you can actually trade
4. **Easy setup**: 5 minutes to get started
5. **Good for indices**: Use QQQ (Nasdaq-100) and DIA (Dow Jones) as proxies

## Setup

### 1. Get API Keys (2 minutes)

1. Sign up at [Alpaca](https://alpaca.markets/)
2. Go to **Paper Trading** → **API Keys**
3. Generate new keys (you'll get both `API Key` and `Secret Key`)

**Important**: Start with **Paper Trading** keys for testing!

### 2. Configure OrderPilot-AI (3 minutes)

```python
from src.config.loader import config_manager

# Store credentials
config_manager.store_credential("alpaca_api_key", "YOUR_API_KEY")
config_manager.store_credential("alpaca_api_secret", "YOUR_SECRET_KEY")
```

Enable in `config/profiles/paper.yaml`:

```yaml
broker:
  broker_type: alpaca
  paper_trading: true

market_data:
  alpaca_enabled: true
  prefer_live_broker: true
```

### 3. Test Connection (1 minute)

```python
from src.core.broker.alpaca_adapter import AlpacaAdapter

# Initialize
adapter = AlpacaAdapter(
    api_key="YOUR_API_KEY",
    api_secret="YOUR_SECRET_KEY",
    paper=True
)

# Connect
await adapter.connect()

# Check balance
balance = await adapter.get_balance()
print(f"Buying power: ${balance.buying_power}")
```

## Real-Time Market Data

### WebSocket Streaming

```python
import asyncio
from src.core.market_data.alpaca_stream import AlpacaStreamClient
from src.common.event_bus import Event, EventType, event_bus

# Setup handler
async def on_bar(event: Event):
    data = event.data
    print(f"{data['symbol']}: ${data['close']} (volume: {data['volume']:,})")

event_bus.subscribe(EventType.MARKET_BAR, on_bar)

# Create stream client
stream = AlpacaStreamClient(
    api_key="YOUR_API_KEY",
    api_secret="YOUR_SECRET_KEY",
    paper=True,
    feed="iex"  # Free IEX feed
)

# Connect and subscribe
await stream.connect()
await stream.subscribe(["AAPL", "MSFT", "QQQ", "DIA"])

# Run for 5 minutes
await asyncio.sleep(300)

# Disconnect
await stream.disconnect()
```

### Using HistoryManager

```python
from src.core.market_data.history_provider import HistoryManager

manager = HistoryManager()

# Start real-time streaming
await manager.start_realtime_stream(
    symbols=["AAPL", "MSFT", "QQQ", "DIA"],
    enable_indicators=True
)

# Stream will automatically use Alpaca if configured
# Get metrics
metrics = manager.get_stream_metrics()
print(f"Messages received: {metrics['messages_received']}")
print(f"Average latency: {metrics['average_latency_ms']:.2f}ms")
```

### Real-Time with Indicators

```python
from src.common.event_bus import Event, EventType, event_bus

async def on_indicator_update(event: Event):
    data = event.data
    symbol = data.get('symbol')

    # RSI signal
    if 'rsi' in data:
        rsi = data['rsi']
        if rsi > 70:
            print(f"{symbol}: OVERBOUGHT (RSI: {rsi:.2f})")
        elif rsi < 30:
            print(f"{symbol}: OVERSOLD (RSI: {rsi:.2f})")

    # MACD signal
    if 'macd' in data:
        macd = data['macd']
        if macd['histogram'] > 0:
            print(f"{symbol}: BULLISH MACD")
        else:
            print(f"{symbol}: BEARISH MACD")

event_bus.subscribe(EventType.INDICATOR_CALCULATED, on_indicator_update)
```

## Trading

### Place Orders

```python
from decimal import Decimal
from src.core.broker.alpaca_adapter import AlpacaAdapter
from src.core.broker.base import OrderRequest
from src.database.models import OrderSide, OrderType, TimeInForce

adapter = AlpacaAdapter(
    api_key="YOUR_API_KEY",
    api_secret="YOUR_SECRET_KEY",
    paper=True
)

await adapter.connect()

# Market order
order = OrderRequest(
    symbol="AAPL",
    side=OrderSide.BUY,
    order_type=OrderType.MARKET,
    quantity=Decimal("10"),
    time_in_force=TimeInForce.DAY
)

response = await adapter.place_order(order)
print(f"Order placed: {response.broker_order_id}")

# Limit order with stop loss
order = OrderRequest(
    symbol="MSFT",
    side=OrderSide.BUY,
    order_type=OrderType.LIMIT,
    quantity=Decimal("5"),
    limit_price=Decimal("350.00"),
    stop_loss=Decimal("340.00"),  # Stop loss at $340
    take_profit=Decimal("370.00"),  # Take profit at $370
    time_in_force=TimeInForce.GTC
)

response = await adapter.place_order(order)
```

### Monitor Positions

```python
# Get all positions
positions = await adapter.get_positions()

for pos in positions:
    print(f"{pos.symbol}: {pos.quantity} shares @ ${pos.average_cost}")
    print(f"  Current: ${pos.current_price}")
    print(f"  P&L: ${pos.unrealized_pnl} ({pos.pnl_percentage:.2f}%)")
    print()
```

### Check Order Status

```python
# Get order status
status = await adapter.get_order_status("order_id_here")

print(f"Status: {status.status}")
print(f"Filled: {status.filled_quantity}/{status.quantity}")
if status.average_fill_price:
    print(f"Avg fill price: ${status.average_fill_price}")
```

## Historical Data

```python
from src.core.market_data.history_provider import (
    DataRequest,
    HistoryManager,
    Timeframe,
    DataSource
)
from datetime import datetime, timedelta

manager = HistoryManager()

# Fetch historical bars
request = DataRequest(
    symbol="AAPL",
    start_date=datetime.utcnow() - timedelta(days=30),
    end_date=datetime.utcnow(),
    timeframe=Timeframe.MINUTE_5,
    source=DataSource.ALPACA  # Force Alpaca source
)

bars, source = await manager.fetch_data(request)

print(f"Fetched {len(bars)} bars from {source}")
for bar in bars[-5:]:
    print(f"{bar.timestamp}: OHLCV = {bar.open}/{bar.high}/{bar.low}/{bar.close}/{bar.volume}")
```

## Trading Strategy Example

```python
import asyncio
from decimal import Decimal
from src.core.market_data.alpaca_stream import AlpacaStreamClient
from src.core.broker.alpaca_adapter import AlpacaAdapter
from src.common.event_bus import Event, EventType, event_bus
from src.core.broker.base import OrderRequest
from src.database.models import OrderSide, OrderType, TimeInForce

class SimpleRSIStrategy:
    """Simple RSI-based trading strategy."""

    def __init__(self, api_key: str, api_secret: str):
        self.stream = AlpacaStreamClient(api_key, api_secret, paper=True)
        self.broker = AlpacaAdapter(api_key, api_secret, paper=True)
        self.positions = {}

    async def start(self, symbols: list[str]):
        """Start the strategy."""
        # Setup event handlers
        event_bus.subscribe(EventType.INDICATOR_CALCULATED, self.on_indicator)

        # Connect
        await self.stream.connect()
        await self.broker.connect()

        # Subscribe to real-time data
        await self.stream.subscribe(symbols)

        print(f"Strategy started for {len(symbols)} symbols")

    async def on_indicator(self, event: Event):
        """Handle indicator updates."""
        data = event.data
        symbol = data.get('symbol')

        if 'rsi' not in data:
            return

        rsi = data['rsi']

        # Get current position
        positions = await self.broker.get_positions()
        has_position = any(p.symbol == symbol for p in positions)

        # Trading logic
        if rsi < 30 and not has_position:
            # OVERSOLD - Buy signal
            print(f"BUY signal: {symbol} (RSI: {rsi:.2f})")
            await self.place_buy_order(symbol, quantity=10)

        elif rsi > 70 and has_position:
            # OVERBOUGHT - Sell signal
            print(f"SELL signal: {symbol} (RSI: {rsi:.2f})")
            await self.place_sell_order(symbol, quantity=10)

    async def place_buy_order(self, symbol: str, quantity: int):
        """Place buy order."""
        order = OrderRequest(
            symbol=symbol,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=Decimal(str(quantity)),
            time_in_force=TimeInForce.DAY
        )

        try:
            response = await self.broker.place_order(order)
            print(f"✅ Buy order placed: {response.broker_order_id}")
        except Exception as e:
            print(f"❌ Order failed: {e}")

    async def place_sell_order(self, symbol: str, quantity: int):
        """Place sell order."""
        order = OrderRequest(
            symbol=symbol,
            side=OrderSide.SELL,
            order_type=OrderType.MARKET,
            quantity=Decimal(str(quantity)),
            time_in_force=TimeInForce.DAY
        )

        try:
            response = await self.broker.place_order(order)
            print(f"✅ Sell order placed: {response.broker_order_id}")
        except Exception as e:
            print(f"❌ Order failed: {e}")

# Run the strategy
async def main():
    strategy = SimpleRSIStrategy(
        api_key="YOUR_API_KEY",
        api_secret="YOUR_SECRET_KEY"
    )

    await strategy.start(["AAPL", "MSFT", "QQQ"])

    # Run for 8 hours (trading day)
    await asyncio.sleep(8 * 3600)

asyncio.run(main())
```

## Limits & Best Practices

### Free Tier Limits

- **WebSocket**: 30 symbols simultaneously
- **REST API**: 200 calls per minute
- **Data feed**: IEX (no consolidated SIP)
- **Connection limit**: 1 active WebSocket connection

### Best Practices

1. **Use ETF proxies for indices**:
   - QQQ for Nasdaq-100
   - DIA for Dow Jones
   - SPY for S&P 500

2. **Manage connections**: Only 1 WebSocket connection allowed
   ```python
   # Don't create multiple streams!
   # BAD: Multiple instances
   stream1 = AlpacaStreamClient(...)
   stream2 = AlpacaStreamClient(...)

   # GOOD: One instance, multiple symbols
   stream = AlpacaStreamClient(...)
   await stream.subscribe(["AAPL", "MSFT", "QQQ", "DIA"])
   ```

3. **Rate limiting**: Respect 200 REST calls/min
   ```python
   # Built-in rate limiting in providers
   # Automatic delay between calls
   ```

4. **Paper trading first**: Test everything before going live
   ```python
   adapter = AlpacaAdapter(..., paper=True)  # Always start here!
   ```

5. **Monitor positions**: Check positions regularly
   ```python
   # Get balance
   balance = await adapter.get_balance()
   if balance.buying_power < minimum_threshold:
       print("⚠️ Low buying power!")
   ```

## Troubleshooting

### "Connection limit exceeded"

**Problem**: Error 406 - only 1 WebSocket connection allowed

**Solution**: Don't create multiple stream instances. Use one stream with multiple symbols:
```python
# Correct approach
stream = AlpacaStreamClient(...)
await stream.subscribe(["AAPL", "MSFT", "GOOGL", "AMZN"])
```

### "Rate limit exceeded"

**Problem**: Too many REST API calls (>200/min)

**Solution**: Use WebSocket streaming instead of polling:
```python
# Bad: Polling every second
while True:
    quote = await adapter.get_quote("AAPL")
    await asyncio.sleep(1)

# Good: WebSocket streaming
await stream.subscribe(["AAPL"])
```

### "No data for symbol"

**Problem**: Symbol not available on IEX feed

**Solution**:
- Check if symbol exists and is tradeable
- Use Alpha Vantage as fallback for non-US stocks
- Verify symbol format (US tickers only)

### "Insufficient buying power"

**Problem**: Not enough cash to place order

**Solution**:
```python
# Check balance first
balance = await adapter.get_balance()
print(f"Available: ${balance.buying_power}")

# Calculate order value
order_value = quantity * price
if order_value > balance.buying_power:
    print("Not enough buying power!")
```

## Comparison: Alpaca vs Alpha Vantage

| Feature | Alpaca | Alpha Vantage |
|---------|--------|---------------|
| **Real-time data** | ✅ WebSocket | ❌ Polling (60s) |
| **Latency** | <100ms | 60+ seconds |
| **Concurrent symbols** | 30 | Unlimited |
| **Trading** | ✅ Yes | ❌ No |
| **Commission** | $0 | N/A |
| **Rate limit** | 200/min | 25/day |
| **Setup complexity** | Medium | Easy |
| **Best for** | Active trading | Historical analysis |

**Recommendation**: Use **Alpaca for real-time** + **Alpha Vantage for historical indicators**

## Next Steps

1. **Test in paper trading**: Get comfortable with the API
2. **Build your strategy**: Use the RSI example as template
3. **Monitor performance**: Check logs and metrics
4. **Go live**: Switch to live keys when ready (paper=False)

## Resources

- [Alpaca Documentation](https://docs.alpaca.markets/)
- [Alpaca Python SDK](https://alpaca.markets/sdks/python/)
- [Market Data API](https://docs.alpaca.markets/docs/market-data)
- [Trading API](https://docs.alpaca.markets/docs/trading-api)

## Support

For issues:
- OrderPilot-AI: Check project GitHub
- Alpaca API: [Alpaca Support](https://alpaca.markets/support)
