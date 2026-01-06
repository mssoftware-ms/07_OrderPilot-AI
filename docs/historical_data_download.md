# Historical Data Download Documentation

## Overview

The `tools/download_historical_data.py` script downloads and caches historical market data from Alpaca and Bitunix providers. Data is stored in the local database with provider-prefixed symbols for unique, multi-source storage.

## Features

- ✅ **Multi-Provider Support**: Download from both Alpaca Crypto and Bitunix Futures
- ✅ **Provider-Prefixed Symbols**: Separate storage for same assets from different providers
  - Alpaca: `alpaca_crypto:BTC/USD`
  - Bitunix: `bitunix:BTCUSDT`
- ✅ **Flexible Timeframes**: 1min, 5min, 15min, 1h, 4h, 1d
- ✅ **Batch Processing**: Efficient database writes with duplicate detection
- ✅ **Database Flexibility**: PostgreSQL (production) or SQLite (development/testing)

## Quick Start

### Basic Usage

Download BTC from both providers (default: 1 year of 1-minute data):

```bash
python tools/download_historical_data.py --both --days 365
```

### Test Mode

Quick test with 7 days of data using SQLite (recommended for first run):

```bash
python tools/download_historical_data.py --both --test --sqlite --verbose
```

## Command-Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--provider` | Data provider: `alpaca`, `bitunix`, or `both` | `both` |
| `--symbols` | Comma-separated symbols (e.g., `BTC/USD,ETH/USD`) | BTC from both providers |
| `--days` | Number of days of history to download | 365 |
| `--timeframe` | Bar timeframe: `1min`, `5min`, `15min`, `1h`, `4h`, `1d` | `1min` |
| `--both` | Download BTC from both providers | - |
| `--test` | Test mode (only 7 days) | - |
| `--sqlite` | Use SQLite instead of PostgreSQL | - |
| `--verbose` `-v` | Verbose output (DEBUG level) | - |

## Usage Examples

### Download BTC from Both Providers (1 Year)

```bash
# Default: BTC from Alpaca (BTC/USD) and Bitunix (BTCUSDT)
python tools/download_historical_data.py --both --days 365
```

**Expected Output:**
```
📥 Downloading BTC from both Alpaca and Bitunix
📡 Downloading BTC/USD from alpaca_crypto...
✅ BTC/USD: Saved 525,600 bars to database
📡 Downloading BTCUSDT from bitunix...
✅ BTCUSDT: Saved 525,600 bars to database
```

**Storage:**
- Alpaca: `alpaca_crypto:BTC/USD` (~100 MB for 1 year of 1min bars)
- Bitunix: `bitunix:BTCUSDT` (~100 MB for 1 year of 1min bars)

### Download Specific Symbols from Alpaca

```bash
python tools/download_historical_data.py \
  --provider alpaca \
  --symbols "BTC/USD,ETH/USD" \
  --days 365 \
  --timeframe 1min
```

### Download Specific Symbols from Bitunix

```bash
python tools/download_historical_data.py \
  --provider bitunix \
  --symbols "BTCUSDT,ETHUSDT" \
  --days 365 \
  --timeframe 1min
```

### Download Larger Timeframes

```bash
# 1-hour bars (less storage, faster download)
python tools/download_historical_data.py --both --days 365 --timeframe 1h

# Daily bars (minimal storage)
python tools/download_historical_data.py --both --days 365 --timeframe 1d
```

## Database Storage

### Schema

Data is stored in the `market_bars` table with provider-prefixed symbols:

```sql
CREATE TABLE market_bars (
    id INTEGER PRIMARY KEY,
    symbol VARCHAR(50) NOT NULL,        -- e.g., "alpaca_crypto:BTC/USD"
    timestamp DATETIME NOT NULL,
    open DECIMAL(20,8),
    high DECIMAL(20,8),
    low DECIMAL(20,8),
    close DECIMAL(20,8),
    volume INTEGER,
    vwap DECIMAL(20,8),
    source VARCHAR(50),                  -- e.g., "alpaca_crypto"
    UNIQUE(symbol, timestamp)           -- Prevents duplicates
);
```

### Symbol Format

Symbols are prefixed with the data source for unique storage:

| Provider | Raw Symbol | Database Symbol |
|----------|-----------|-----------------|
| Alpaca Crypto | `BTC/USD` | `alpaca_crypto:BTC/USD` |
| Bitunix Futures | `BTCUSDT` | `bitunix:BTCUSDT` |

### Querying Data

**PostgreSQL:**
```sql
-- Get Alpaca BTC/USD data
SELECT * FROM market_bars
WHERE symbol = 'alpaca_crypto:BTC/USD'
ORDER BY timestamp DESC
LIMIT 100;

-- Get Bitunix BTCUSDT data
SELECT * FROM market_bars
WHERE symbol = 'bitunix:BTCUSDT'
ORDER BY timestamp DESC
LIMIT 100;

-- Coverage summary
SELECT symbol, COUNT(*) as bars,
       MIN(timestamp) as first_date,
       MAX(timestamp) as last_date
FROM market_bars
GROUP BY symbol;
```

**SQLite (Development):**
```bash
sqlite3 ./data/orderpilot_historical.db "
SELECT symbol, COUNT(*), MIN(timestamp), MAX(timestamp)
FROM market_bars
GROUP BY symbol;"
```

## Configuration

### API Credentials

The script loads credentials in this priority order:

1. **Memory cache** (if already loaded)
2. **System environment variables** (WSL/Linux):
   ```bash
   export ALPACA_API_KEY="your_key"
   export ALPACA_API_SECRET="your_secret"
   export BITUNIX_API_KEY="your_key"
   export BITUNIX_API_SECRET="your_secret"
   ```

3. **`.env` file** in `config/secrets/.env`:
   ```bash
   ALPACA_API_KEY=your_key_here
   ALPACA_API_SECRET=your_secret_here
   BITUNIX_API_KEY=your_key_here
   BITUNIX_API_SECRET=your_secret_here
   ```

4. **Windows Credential Manager** (when running from Windows)

### Database Configuration

**Production (PostgreSQL):**

Edit `config/paper.yaml`:
```yaml
database:
  engine: postgresql
  host: localhost
  port: 5432
  database: orderpilot
  username: orderpilot
  password: orderpilot
```

**Development/Testing (SQLite):**

Use the `--sqlite` flag:
```bash
python tools/download_historical_data.py --both --sqlite
```

This creates `./data/orderpilot_historical.db` automatically.

## API Rate Limits & Performance

### Alpaca Crypto API

- **Rate Limit**: 200 calls/minute
- **Pagination**: Handled automatically by SDK
- **Max Bars per Request**: 10,000
- **Performance**: ~2-3 minutes for 1 year of 1min BTC/USD data

### Bitunix Futures API

- **Rate Limit**: 600 calls/minute (conservative: 0.1s delay)
- **Pagination**: Manual (200 bars per request)
- **Max Bars per Symbol**: 525,600 (1 year of 1min bars)
- **Max Batches**: 2,628 (525,600 / 200)
- **Performance**: ~5-7 minutes for 1 year of 1min BTCUSDT data

### Storage Requirements

**1-minute bars, 1 year:**
- **Alpaca BTC/USD**: ~525,600 bars ≈ 100 MB
- **Bitunix BTCUSDT**: ~525,600 bars ≈ 100 MB
- **Total**: ~200 MB for both providers

**Other timeframes (storage savings):**
- **1-hour bars**: ~8,760 bars ≈ 1.7 MB per symbol (1/60th of 1min)
- **Daily bars**: ~365 bars ≈ 70 KB per symbol (1/1440th of 1min)

## Troubleshooting

### Issue: PostgreSQL Connection Refused

**Symptom:**
```
psycopg2.OperationalError: connection to server at "localhost" (127.0.0.1),
port 5432 failed: Connection refused
```

**Solution:**

Option 1: Use SQLite for testing:
```bash
python tools/download_historical_data.py --both --sqlite
```

Option 2: Start PostgreSQL:
```bash
# WSL/Linux
sudo service postgresql start

# Windows
# Start PostgreSQL service from Services panel
```

Option 3: Install `psycopg2-binary`:
```bash
pip install psycopg2-binary
```

### Issue: Bitunix API Keys Not Found

**Symptom:**
```
ERROR - Bitunix API keys not found in environment variables!
```

**Solution:**

Create `config/secrets/.env`:
```bash
mkdir -p config/secrets
cat > config/secrets/.env << EOF
BITUNIX_API_KEY=your_key_here
BITUNIX_API_SECRET=your_secret_here
EOF
```

**Note:** In WSL, Windows system environment variables are not directly accessible. Use the `.env` file or export in WSL:
```bash
export BITUNIX_API_SECRET="$BITUNIX_SECRET_KEY"
```

### Issue: No Data Returned from Bitunix

**Symptom:**
```
⚠️ No data received for BTCUSDT
```

**Possible Causes:**
1. **Testnet has limited data**: Switch to mainnet by editing `config/paper.yaml`:
   ```yaml
   market_data:
     bitunix_testnet: false  # Use mainnet
   ```

2. **Symbol format incorrect**: Bitunix uses `BTCUSDT` (not `BTC/USD`)

3. **Time range too old**: Try a recent time range:
   ```bash
   python tools/download_historical_data.py --provider bitunix --symbols BTCUSDT --days 7
   ```

### Issue: Duplicate Key Errors

**Symptom:**
```
UNIQUE constraint failed: market_bars.symbol, market_bars.timestamp
```

**Solution:**

This is **normal behavior**. The script automatically skips duplicates. The unique constraint prevents duplicate bars from being inserted. Run the script again - it will only insert new bars.

## Verification

### Check Downloaded Data

**Option 1: Python Query**
```python
import sqlite3
conn = sqlite3.connect('./data/orderpilot_historical.db')
cursor = conn.cursor()
cursor.execute('''
    SELECT symbol, COUNT(*) as bars,
           MIN(timestamp) as first,
           MAX(timestamp) as last
    FROM market_bars
    GROUP BY symbol
''')
for row in cursor.fetchall():
    print(f"{row[0]:25} | {row[1]:7} bars | {row[2]} to {row[3]}")
```

**Option 2: SQL Query (PostgreSQL)**
```sql
SELECT
    symbol,
    COUNT(*) as total_bars,
    MIN(timestamp) as first_date,
    MAX(timestamp) as last_date,
    EXTRACT(DAY FROM MAX(timestamp) - MIN(timestamp)) as coverage_days
FROM market_bars
GROUP BY symbol
ORDER BY symbol;
```

**Expected Output:**
```
alpaca_crypto:BTC/USD     |  525600 bars | 2025-01-06 to 2026-01-06
bitunix:BTCUSDT           |  525600 bars | 2025-01-06 to 2026-01-06
```

## Best Practices

### 1. Start with Test Mode

Always test first with small data:
```bash
python tools/download_historical_data.py --both --test --sqlite --verbose
```

### 2. Use SQLite for Development

Avoid PostgreSQL setup during development:
```bash
python tools/download_historical_data.py --both --sqlite
```

### 3. Download in Stages

For large datasets, download in smaller chunks:
```bash
# Month by month
python tools/download_historical_data.py --both --days 30
# Wait and verify, then continue
python tools/download_historical_data.py --both --days 60
```

### 4. Use Larger Timeframes for Testing

1-hour or daily bars download much faster:
```bash
python tools/download_historical_data.py --both --days 365 --timeframe 1h
```

### 5. Monitor Progress

Use `--verbose` to see detailed progress:
```bash
python tools/download_historical_data.py --both --verbose
```

## Architecture

### Data Flow

```
User Input → Script → Provider API → HistoricalDataManager → Database
                ↓                              ↓
          Credentials          Batch Processing (100 bars)
          from .env           Symbol Prefixing (source:symbol)
```

### Key Components

1. **`download_historical_data.py`**
   - CLI interface
   - Argument parsing
   - Database initialization
   - Result reporting

2. **`HistoricalDataManager`** (`src/core/market_data/historical_data_manager.py`)
   - Bulk download coordination
   - Batch processing (100 bars per batch)
   - Progress tracking
   - Data coverage reporting

3. **Providers**
   - **`AlpacaCryptoProvider`**: Alpaca Crypto API client
   - **`BitunixProvider`**: Bitunix Futures API client

4. **Database**
   - **PostgreSQL**: Production (scalable, time-series optimized)
   - **SQLite**: Development (lightweight, file-based)

### Symbol Formatting

The `format_symbol_with_source()` function ensures unique storage:

```python
from src.core.market_data.types import format_symbol_with_source, DataSource

# Alpaca
db_symbol = format_symbol_with_source("BTC/USD", DataSource.ALPACA_CRYPTO)
# Result: "alpaca_crypto:BTC/USD"

# Bitunix
db_symbol = format_symbol_with_source("BTCUSDT", DataSource.BITUNIX)
# Result: "bitunix:BTCUSDT"
```

## Future Enhancements

- [ ] Parallel downloads for multiple symbols
- [ ] Resume capability for interrupted downloads
- [ ] Data gap detection and auto-fill
- [ ] Real-time download scheduling (cron jobs)
- [ ] Web UI for download management
- [ ] Data quality validation
- [ ] Export to CSV/Parquet

## Support

For issues or questions:
1. Check this documentation
2. Check `--verbose` output for errors
3. Verify API credentials in `config/secrets/.env`
4. Review `CLAUDE.md` for project architecture

## Related Documentation

- **Project Overview**: `CLAUDE.md`
- **Database Schema**: `src/database/models.py`
- **Data Types**: `src/core/market_data/types.py`
- **Alpaca API Docs**: `docs/alpaca/docs.alpaca.markets/`
- **Bitunix Provider**: `src/core/market_data/providers/bitunix_provider.py`
