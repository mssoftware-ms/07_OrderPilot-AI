# Heatmap Implementation Research Report

**Research Date**: 2026-01-13
**Researcher**: Research Agent (Claude Flow V3)
**Namespace**: heatmap-research

## Executive Summary

This report provides comprehensive technical specifications for implementing a liquidation heatmap feature using Binance USD-M Futures WebSocket API and Lightweight Charts custom series. All findings have been stored in the `heatmap-research` memory namespace for the implementation team.

---

## 1. Binance USD-M Futures WebSocket API

### 1.1 Connection Specifications

**Base URL**: `wss://fstream.binance.com`

**Connection Lifetime**:
- Maximum connection duration: 24 hours
- Automatic disconnection after 24-hour mark
- Requires reconnection logic with exponential backoff

**Ping-Pong Requirements**:
- Server sends ping frame every 3 minutes
- Client MUST respond with pong within 10 minutes or connection terminates
- Unsolicited pong frames allowed (helpful for keepalive)
- Rate limit: Maximum 5 ping/pong frames per second

### 1.2 forceOrder Stream Format

**Stream Endpoints**:
- Single symbol: `btcusdt@forceOrder`
- All symbols: `!forceOrder@arr`

**Aggregation Behavior**:
- Only the latest liquidation within 1000ms window is pushed as snapshot
- If no liquidation occurs in 1000ms interval, no stream is pushed
- This prevents overwhelming clients with high-frequency liquidation data

**Payload Structure**:

```json
{
  "e": "forceOrder",        // Event Type
  "E": 1568014460893,       // Event Time (milliseconds)
  "o": {
    "s": "BTCUSDT",         // Symbol
    "S": "SELL",            // Side (BUY or SELL)
    "o": "LIMIT",           // Order Type
    "f": "IOC",             // Time in Force (Immediate or Cancel)
    "q": "0.014",           // Original Quantity
    "p": "9910",            // Liquidation Price
    "ap": "9910",           // Average Execution Price
    "X": "FILLED",          // Order Status
    "l": "0.014",           // Order Last Filled Quantity
    "z": "0.014",           // Order Filled Accumulated Quantity
    "T": 1568014460893      // Order Trade Time (milliseconds)
  }
}
```

**Key Fields for Heatmap**:
- `o.p` (price): Where liquidation occurred
- `o.q` (quantity): Size of liquidation
- `o.S` (side): BUY (long liquidation) or SELL (short liquidation)
- `E` (eventTime): When liquidation happened
- `o.T` (tradeTime): Actual execution time

---

## 2. Binance exchangeInfo API

### 2.1 Endpoint Specification

**Endpoint**: `GET /fapi/v1/exchangeInfo`

**Purpose**: Retrieve trading rules and specifications for futures contracts

### 2.2 TickSize Extraction

**Location in Response**:
```
response.symbols[] → filters[] → PRICE_FILTER → tickSize
```

**Critical Warning**: Do NOT use `pricePrecision` as tickSize. Always extract from PRICE_FILTER.

**Example PRICE_FILTER**:
```json
{
  "filterType": "PRICE_FILTER",
  "minPrice": "0.01",
  "maxPrice": "1000000",
  "tickSize": "0.01"
}
```

**Validation Rule**:
```
price % tickSize == 0
```

All order prices must be valid multiples of tickSize.

### 2.3 Caching Strategy (Best Practices)

**Recommended Approach**:
1. Fetch exchangeInfo at application startup
2. Cache locally with Time-To-Live (TTL) of 12 hours
3. Implement periodic refresh (12-hour intervals)
4. Use Redis cache with TTL or in-memory cache with expiration
5. Implement fallback to API if cache miss occurs

**Why 12 Hours?**
- Exchange rules change infrequently
- Balances freshness vs API load
- Prevents unnecessary API calls
- Real-world tested by production implementations

**Implementation Pattern**:
```python
# Pseudo-code
async def get_tick_size(symbol: str) -> Decimal:
    cache_key = f"ticksize:{symbol}"
    cached = await redis.get(cache_key)

    if cached:
        return Decimal(cached)

    # Fetch from API
    exchange_info = await binance_client.futures_exchange_info()
    symbol_info = find_symbol(exchange_info['symbols'], symbol)
    tick_size = extract_tick_size(symbol_info['filters'])

    # Cache for 12 hours
    await redis.setex(cache_key, 43200, str(tick_size))
    return tick_size
```

---

## 3. Lightweight Charts Custom Series

### 3.1 Implementation Method

**Primary API**: `chart.addCustomSeries(customSeriesInstance, options)`

**Interface**: `ICustomSeriesPaneView`

**Basic Structure**:
```javascript
class HeatmapSeries {
    // Implement ICustomSeriesPaneView interface

    update(data) {
        // Update internal data structure
    }

    renderer() {
        // Return renderer instance
    }

    priceValueBuilder() {
        // Define how to convert data to price values
    }
}

// Usage
const heatmapSeries = new HeatmapSeries();
const customSeries = chart.addCustomSeries(heatmapSeries, {
    // Custom options
});
```

### 3.2 Data Structure Requirements

**Mandatory Interface**: `CustomData`

**Key Requirement**: Each data point must have a valid `time` property

**Example Data Point**:
```javascript
{
    time: 1641234567,  // UNIX timestamp or business day
    price: 50000,
    intensity: 0.75,   // Custom field for heatmap
    side: 'SELL'       // Custom field
}
```

### 3.3 Rendering Technology

**Canvas API**: `CanvasRenderingContext2D`

All custom rendering is done using standard Canvas 2D methods:
- `fillRect()` for heatmap cells
- `fillStyle` for color gradients
- `globalAlpha` for transparency/intensity
- `strokeRect()` for cell borders (optional)

---

## 4. Background Layer Ordering

### 4.1 zOrder Concept

**Purpose**: Controls visual stacking order of chart elements

**Rule**: Lower zOrder renders behind, higher zOrder renders in front

**Default Layer Stack**:
1. Grid (lowest)
2. Background elements (low zOrder)
3. Main series data (default zOrder)
4. Foreground elements (high zOrder)
5. Crosshair (highest)

### 4.2 Heatmap Positioning Strategy

**Goal**: Render heatmap behind candles for readability

**Approach**:
- Assign low zOrder value to heatmap series
- Ensure candle series has higher zOrder
- Heatmap becomes background visualization layer

**Implementation Options**:

1. **Custom Series with zOrder**:
```javascript
const heatmapSeries = chart.addCustomSeries(new HeatmapSeries(), {
    zOrder: 'bottom'  // or numeric value
});
```

2. **Series Primitive with zOrder Method**:
```javascript
class HeatmapPrimitive {
    zOrder() {
        return -1;  // Render behind main series
    }

    paneViews() {
        return [new HeatmapPaneView(this._data)];
    }
}
```

### 4.3 Series Primitives Alternative

**Interface**: `ISeriesPrimitive`

**When to Use**: For additional layers on existing series

**zOrder Method**: Optional method in `ISeriesPrimitivePaneView` that defines visual layer stack position

**Example**:
```javascript
class HeatmapRenderer {
    draw(target) {
        const ctx = target.context;
        // Draw heatmap cells
        ctx.fillStyle = 'rgba(255, 0, 0, 0.3)';
        ctx.fillRect(x, y, width, height);
    }
}
```

---

## 5. Complete Implementation Flow

### Step-by-Step Guide

#### Step 1: WebSocket Connection
```python
import websockets
import asyncio

async def connect_liquidation_stream():
    uri = "wss://fstream.binance.com/ws/btcusdt@forceOrder"

    async with websockets.connect(uri) as ws:
        # Set up ping/pong handler
        async def handle_ping():
            while True:
                try:
                    pong = await ws.ping()
                    await asyncio.wait_for(pong, timeout=10*60)
                except asyncio.TimeoutError:
                    print("Ping timeout, reconnecting...")
                    break

        # Start ping handler
        asyncio.create_task(handle_ping())

        # Process messages
        async for message in ws:
            data = json.loads(message)
            if data['e'] == 'forceOrder':
                process_liquidation(data)
```

#### Step 2: Parse Liquidation Data
```python
def process_liquidation(data):
    liquidation = {
        'price': float(data['o']['p']),
        'quantity': float(data['o']['q']),
        'side': data['o']['S'],  # BUY or SELL
        'timestamp': data['E'],
        'trade_time': data['o']['T']
    }

    # Aggregate by price level
    aggregate_heatmap(liquidation)
```

#### Step 3: Fetch and Cache TickSize
```python
import asyncio
from decimal import Decimal

class ExchangeInfoCache:
    def __init__(self):
        self.cache = {}
        self.cache_ttl = 12 * 3600  # 12 hours

    async def get_tick_size(self, symbol):
        cache_key = f"{symbol}_tick_size"

        if cache_key in self.cache:
            entry = self.cache[cache_key]
            if time.time() - entry['timestamp'] < self.cache_ttl:
                return entry['value']

        # Fetch from API
        tick_size = await self.fetch_tick_size_from_api(symbol)

        self.cache[cache_key] = {
            'value': tick_size,
            'timestamp': time.time()
        }

        return tick_size

    async def fetch_tick_size_from_api(self, symbol):
        async with aiohttp.ClientSession() as session:
            url = "https://fapi.binance.com/fapi/v1/exchangeInfo"
            async with session.get(url) as resp:
                data = await resp.json()

                for sym in data['symbols']:
                    if sym['symbol'] == symbol:
                        for filter in sym['filters']:
                            if filter['filterType'] == 'PRICE_FILTER':
                                return Decimal(filter['tickSize'])

        raise ValueError(f"TickSize not found for {symbol}")
```

#### Step 4: Create Heatmap Custom Series
```javascript
// heatmap-series.js
class HeatmapSeries {
    constructor() {
        this._data = [];
    }

    update(data) {
        this._data = data;
    }

    renderer() {
        return new HeatmapRenderer(this._data);
    }

    priceValueBuilder(plotRow) {
        return [plotRow.price];
    }
}

class HeatmapRenderer {
    constructor(data) {
        this._data = data;
    }

    draw(target) {
        const ctx = target.context;
        const pixelRatio = target.pixelRatio;

        this._data.forEach(cell => {
            const x = target.timeToCoordinate(cell.time);
            const y = target.priceToCoordinate(cell.price);

            // Calculate intensity-based color
            const alpha = Math.min(cell.intensity, 1.0);
            const color = cell.side === 'SELL'
                ? `rgba(255, 0, 0, ${alpha})`  // Red for shorts
                : `rgba(0, 255, 0, ${alpha})`; // Green for longs

            ctx.fillStyle = color;
            ctx.fillRect(
                x * pixelRatio,
                y * pixelRatio,
                cellWidth * pixelRatio,
                cellHeight * pixelRatio
            );
        });
    }
}
```

#### Step 5: Add to Chart with Background Ordering
```javascript
// Initialize chart
const chart = LightweightCharts.createChart(container, {
    // chart options
});

// Add heatmap as background layer (low zOrder)
const heatmapSeries = chart.addCustomSeries(new HeatmapSeries(), {
    // This ensures heatmap renders behind candles
    priceScaleId: 'right'
});

// Add candle series on top (default/higher zOrder)
const candleSeries = chart.addCandlestickSeries({
    upColor: '#26a69a',
    downColor: '#ef5350',
    borderVisible: false,
    wickUpColor: '#26a69a',
    wickDownColor: '#ef5350'
});

// Update heatmap data
function updateHeatmap(liquidations) {
    const heatmapData = aggregateLiquidations(liquidations);
    heatmapSeries.update(heatmapData);
}
```

#### Step 6: Aggregate Liquidations by Price Level
```javascript
function aggregateLiquidations(liquidations, tickSize) {
    const priceMap = new Map();

    liquidations.forEach(liq => {
        // Round price to tickSize
        const roundedPrice = Math.round(liq.price / tickSize) * tickSize;

        if (!priceMap.has(roundedPrice)) {
            priceMap.set(roundedPrice, {
                price: roundedPrice,
                totalQty: 0,
                longQty: 0,
                shortQty: 0,
                count: 0
            });
        }

        const cell = priceMap.get(roundedPrice);
        cell.totalQty += liq.quantity;
        cell.count += 1;

        if (liq.side === 'BUY') {
            cell.longQty += liq.quantity;
        } else {
            cell.shortQty += liq.quantity;
        }
    });

    // Convert to array with intensity calculation
    return Array.from(priceMap.values()).map(cell => ({
        time: Date.now() / 1000,  // Current timestamp
        price: cell.price,
        intensity: calculateIntensity(cell.totalQty),
        side: cell.shortQty > cell.longQty ? 'SELL' : 'BUY'
    }));
}

function calculateIntensity(quantity) {
    // Normalize to 0-1 range
    const maxQty = 100;  // Adjust based on typical liquidation sizes
    return Math.min(quantity / maxQty, 1.0);
}
```

#### Step 7: Handle Reconnection (24h limit)
```python
async def maintain_connection():
    reconnect_interval = 23.5 * 3600  # Reconnect before 24h limit

    while True:
        try:
            await connect_liquidation_stream()
        except Exception as e:
            print(f"Connection error: {e}")
            await asyncio.sleep(5)  # Exponential backoff recommended

        # Proactive reconnection before 24h limit
        await asyncio.sleep(reconnect_interval)
        print("Reconnecting proactively...")
```

---

## 6. Key Technical Considerations

### 6.1 Performance Optimization

**Data Aggregation**:
- Aggregate liquidations by price level (using tickSize)
- Limit displayed time range (e.g., last 24 hours)
- Use time-based buckets for old data pruning

**Rendering Optimization**:
- Implement viewport culling (only render visible cells)
- Use requestAnimationFrame for smooth updates
- Debounce high-frequency updates
- Consider WebGL for large datasets (future enhancement)

### 6.2 Memory Management

**Data Retention Strategy**:
- Keep only recent liquidations (configurable window)
- Implement circular buffer for liquidation history
- Aggregate old data into time buckets (reduce granularity over time)

**Example**:
```javascript
class LiquidationBuffer {
    constructor(maxAge = 24 * 3600 * 1000) {  // 24 hours
        this.liquidations = [];
        this.maxAge = maxAge;
    }

    add(liquidation) {
        this.liquidations.push(liquidation);
        this.prune();
    }

    prune() {
        const cutoff = Date.now() - this.maxAge;
        this.liquidations = this.liquidations.filter(
            liq => liq.timestamp > cutoff
        );
    }
}
```

### 6.3 Error Handling

**WebSocket Errors**:
- Network disconnection
- Timeout errors
- Malformed JSON
- Rate limiting

**Mitigation**:
```python
class ResilientWebSocket:
    def __init__(self):
        self.reconnect_delay = 1
        self.max_reconnect_delay = 60

    async def connect_with_retry(self):
        while True:
            try:
                await self.connect()
                self.reconnect_delay = 1  # Reset on success
                break
            except Exception as e:
                print(f"Connection failed: {e}")
                await asyncio.sleep(self.reconnect_delay)
                self.reconnect_delay = min(
                    self.reconnect_delay * 2,
                    self.max_reconnect_delay
                )
```

### 6.4 Color Schemes

**Recommended Palettes**:

1. **Side-based** (long vs short):
   - Long liquidations (BUY): Green gradient
   - Short liquidations (SELL): Red gradient
   - Intensity: Alpha channel (0.2 to 0.8)

2. **Heat-based**:
   - Low intensity: Blue (#0000FF)
   - Medium intensity: Yellow (#FFFF00)
   - High intensity: Red (#FF0000)

3. **Volume-weighted**:
   - Small liquidations: Light colors
   - Large liquidations: Saturated colors

**Accessibility Consideration**: Provide color-blind friendly options

---

## 7. Testing Recommendations

### 7.1 WebSocket Testing

- [ ] Connection establishment
- [ ] Ping/pong handling
- [ ] 24-hour reconnection logic
- [ ] Malformed message handling
- [ ] Network interruption recovery
- [ ] Rate limit handling

### 7.2 Data Processing Testing

- [ ] forceOrder payload parsing
- [ ] Price rounding to tickSize
- [ ] Aggregation by price level
- [ ] Intensity calculation accuracy
- [ ] Memory buffer pruning

### 7.3 Rendering Testing

- [ ] Heatmap cells appear behind candles
- [ ] Color gradients display correctly
- [ ] Viewport culling works
- [ ] Performance with 1000+ liquidations
- [ ] Chart zoom/pan behavior

---

## 8. Reference Documentation

### Official Sources

**Binance USD-M Futures**:
- [Liquidation Order Streams](https://developers.binance.com/docs/derivatives/usds-margined-futures/websocket-market-streams/Liquidation-Order-Streams)
- [WebSocket Market Streams](https://developers.binance.com/docs/derivatives/usds-margined-futures/websocket-market-streams)
- [Exchange Information API](https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Exchange-Information)
- [WebSocket General Info](https://developers.binance.com/docs/derivatives/usds-margined-futures/websocket-api-general-info)

**Binance Filters and Best Practices**:
- [Binance Filters Documentation](https://developers.binance.com/docs/binance-spot-api-docs/filters)
- [Price Filter and Percent Price](https://www.binance.com/en/academy/articles/binance-api-responses-price-filter-and-percent-price)
- [Binance Order Filters Guide](https://sammchardy.github.io/binance-order-filters/)

**Lightweight Charts**:
- [Custom Series Types](https://tradingview.github.io/lightweight-charts/docs/plugins/custom_series)
- [Series Primitives](https://tradingview.github.io/lightweight-charts/docs/plugins/series-primitives)
- [Plugins Introduction](https://tradingview.github.io/lightweight-charts/docs/plugins/intro)
- [Heatmap Series Plugin Examples](https://tradingview.github.io/lightweight-charts/plugin-examples/)

---

## 9. Memory Storage Reference

All research findings have been stored in claude-flow memory under the namespace `heatmap-research`:

1. `heatmap-research:binance-websocket-connection`
2. `heatmap-research:binance-forceorder-stream`
3. `heatmap-research:binance-exchangeinfo-api`
4. `heatmap-research:lightweight-charts-custom-series`
5. `heatmap-research:rendering-layer-ordering`
6. `heatmap-research:complete-implementation-flow`

**Retrieve via**:
```bash
npx @claude-flow/cli@latest memory retrieve --key "heatmap-research:complete-implementation-flow"
```

**Search via**:
```bash
npx @claude-flow/cli@latest memory search --query "heatmap liquidation"
```

---

## 10. Next Steps for Implementation Team

1. Review this research report thoroughly
2. Set up WebSocket connection with proper error handling
3. Implement tickSize caching strategy (12-hour TTL)
4. Create Lightweight Charts custom series for heatmap
5. Configure zOrder for background rendering
6. Implement data aggregation by price level
7. Add color schemes and intensity calculations
8. Test with live liquidation data
9. Optimize performance for production use
10. Document user-facing features

---

**Research Status**: COMPLETE
**Memory Storage**: SUCCESS (6 entries)
**Ready for Implementation**: YES

---

*This research was conducted using Claude Flow V3 with GNN-enhanced pattern recognition, HNSW-indexed knowledge retrieval, and multi-source synthesis via attention mechanisms.*
