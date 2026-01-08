"""Historical Data Manager for bulk downloading and caching market data.

Manages downloading and storing historical market data from various providers
with support for multi-source storage using provider-prefixed symbols.

Includes automatic bad tick filtering using Hampel Filter with Volume Confirmation
to remove erroneous data points (price spikes, OHLC inconsistencies) before storage.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pandas as pd
import numpy as np

from src.core.market_data.types import (
    DataSource,
    HistoricalBar,
    Timeframe,
    format_symbol_with_source,
)
from src.database import get_db_manager
from src.database.models import MarketBar

logger = logging.getLogger(__name__)


@dataclass
class FilterConfig:
    """Configuration for bad tick filtering during data download.

    Attributes:
        enabled: Enable/disable filtering (default: True)
        method: Filter method - "hampel" (recommended), "zscore", or "basic"
        cleaning_mode: How to handle bad ticks - "interpolate" (recommended), "remove", or "forward_fill"
        hampel_window: Rolling window for Hampel MAD calculation (default: 15 bars)
        hampel_threshold: Modified Z-score threshold for outliers (default: 3.5, increase for crypto)
        volume_multiplier: Volume must exceed this multiple of median to confirm real event (default: 10x)
        log_stats: Log filtering statistics (default: True)
    """
    enabled: bool = True
    method: str = "hampel"  # "hampel", "zscore", or "basic"
    cleaning_mode: str = "interpolate"  # "interpolate", "remove", or "forward_fill"
    hampel_window: int = 15
    hampel_threshold: float = 3.5
    volume_multiplier: float = 10.0
    log_stats: bool = True


@dataclass
class FilterStats:
    """Statistics from bad tick filtering operation."""
    total_bars: int = 0
    bad_ticks_found: int = 0
    bad_ticks_interpolated: int = 0
    bad_ticks_removed: int = 0
    filtering_percentage: float = 0.0
    bad_tick_types: dict = field(default_factory=dict)


class HistoricalDataManager:
    """Manages bulk downloading and caching of historical market data.

    Includes automatic bad tick filtering to remove erroneous data points
    before storage. Uses Hampel Filter with Volume Confirmation by default.
    """

    def __init__(self, filter_config: FilterConfig | None = None):
        """Initialize the historical data manager.

        Args:
            filter_config: Configuration for bad tick filtering (default: enabled with Hampel)
        """
        self.db_manager = get_db_manager()
        self.filter_config = filter_config or FilterConfig()
        self._last_filter_stats: FilterStats | None = None

    async def bulk_download(
        self,
        provider,
        symbols: list[str],
        days_back: int = 365,
        timeframe: Timeframe = Timeframe.MINUTE_1,
        source: DataSource = DataSource.ALPACA_CRYPTO,
        batch_size: int = 100,
        filter_config: FilterConfig | None = None,
        replace_existing: bool = True,
        progress_callback: callable = None,
    ) -> dict[str, int]:
        """Download historical data for multiple symbols in bulk.

        Args:
            provider: Data provider instance (e.g., AlpacaProvider, BitunixProvider)
            symbols: List of symbols to download
            days_back: Number of days of history to download (default: 365)
            timeframe: Timeframe for bars (default: 1min)
            source: Data source enum for symbol prefixing
            batch_size: Number of bars to save per batch (default: 100)
            filter_config: Override filter configuration for this download
            replace_existing: Delete existing data before downloading (default: True)
                             This ensures clean data without old bad ticks.
            progress_callback: Optional callback(batch_num, total_bars, status_msg) for UI updates

        Returns:
            Dictionary mapping symbols to number of bars saved

        Example:
            >>> from src.core.market_data.providers.bitunix_provider import BitunixProvider
            >>> provider = BitunixProvider(api_key, api_secret)
            >>> manager = HistoricalDataManager()
            >>> results = await manager.bulk_download(
            ...     provider,
            ...     ["BTCUSDT", "ETHUSDT"],
            ...     days_back=365,
            ...     source=DataSource.BITUNIX
            ... )
            >>> print(results)  # {"BTCUSDT": 525600, "ETHUSDT": 525600}

        Note:
            Bad ticks are automatically filtered using Hampel Filter with Volume
            Confirmation. Price spikes without corresponding high volume are
            interpolated to maintain data continuity without gaps.
        """
        # Use provided config or fall back to instance config
        config = filter_config or self.filter_config
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days_back)

        logger.info(f"📥 Bulk download started:")
        logger.info(f"   Symbols: {symbols}")
        logger.info(f"   Period: {start_date.date()} to {end_date.date()} ({days_back} days)")
        logger.info(f"   Timeframe: {timeframe.value}")
        logger.info(f"   Source: {source.value}")
        logger.info(f"   Replace Existing: {'YES' if replace_existing else 'NO'}")
        logger.info(f"   Bad Tick Filter: {'ENABLED' if config.enabled else 'DISABLED'} ({config.method})")

        results = {}
        total_filter_stats = FilterStats()

        for symbol in symbols:
            try:
                # Format symbol with source prefix for database
                db_symbol = format_symbol_with_source(symbol, source)

                # Delete existing data if replace mode is enabled
                if replace_existing:
                    deleted_count = await self._delete_symbol_data(db_symbol)
                    if deleted_count > 0:
                        logger.info(f"🗑️  Deleted {deleted_count:,} existing bars for {db_symbol}")

                logger.info(f"📡 Downloading {symbol} from {source.value}...")

                # Fetch bars from provider with progress callback
                # Check if provider supports progress_callback (BitunixProvider does)
                fetch_kwargs = {
                    'symbol': symbol,
                    'start_date': start_date,
                    'end_date': end_date,
                    'timeframe': timeframe,
                }
                # Add progress_callback if provider supports it
                if progress_callback is not None:
                    import inspect
                    sig = inspect.signature(provider.fetch_bars)
                    if 'progress_callback' in sig.parameters:
                        fetch_kwargs['progress_callback'] = progress_callback

                bars = await provider.fetch_bars(**fetch_kwargs)

                if not bars:
                    logger.warning(f"⚠️ No data received for {symbol}")
                    results[symbol] = 0
                    continue

                # Apply bad tick filtering before saving
                if config.enabled:
                    bars, stats = await self._filter_bad_ticks(bars, config, symbol)
                    total_filter_stats.total_bars += stats.total_bars
                    total_filter_stats.bad_ticks_found += stats.bad_ticks_found
                    total_filter_stats.bad_ticks_interpolated += stats.bad_ticks_interpolated
                    total_filter_stats.bad_ticks_removed += stats.bad_ticks_removed

                # Format symbol with source prefix for database
                db_symbol = format_symbol_with_source(symbol, source)

                # Save to database in batches
                saved_count = await self._save_bars_batched(
                    bars,
                    db_symbol,
                    source.value,
                    batch_size
                )

                results[symbol] = saved_count
                logger.info(f"✅ {symbol}: Saved {saved_count} bars to database")

            except Exception as e:
                logger.error(f"❌ Failed to download {symbol}: {e}", exc_info=True)
                results[symbol] = 0

        # Log filter summary
        if config.enabled and config.log_stats:
            total_filter_stats.filtering_percentage = (
                total_filter_stats.bad_ticks_found / total_filter_stats.total_bars * 100
                if total_filter_stats.total_bars > 0 else 0
            )
            self._last_filter_stats = total_filter_stats
            logger.info(f"🛡️  Filter Summary: {total_filter_stats.bad_ticks_found} bad ticks "
                       f"({total_filter_stats.filtering_percentage:.2f}%) in {total_filter_stats.total_bars} bars")

        logger.info(f"📥 Bulk download completed. Total: {sum(results.values())} bars")
        return results

    async def _delete_symbol_data(self, db_symbol: str) -> int:
        """Delete all existing data for a symbol from the database.

        Args:
            db_symbol: Database symbol with source prefix (e.g., "bitunix:BTCUSDT")

        Returns:
            Number of rows deleted
        """
        return await asyncio.to_thread(self._delete_symbol_data_sync, db_symbol)

    def _delete_symbol_data_sync(self, db_symbol: str) -> int:
        """Delete symbol data synchronously.

        Args:
            db_symbol: Database symbol with source prefix

        Returns:
            Number of rows deleted
        """
        with self.db_manager.session() as session:
            deleted_count = session.query(MarketBar).filter(
                MarketBar.symbol == db_symbol
            ).delete()
            session.commit()
            return deleted_count

    async def _filter_bad_ticks(
        self,
        bars: list[HistoricalBar],
        config: FilterConfig,
        symbol: str
    ) -> tuple[list[HistoricalBar], FilterStats]:
        """Filter bad ticks from downloaded bars.

        Uses Hampel Filter with Volume Confirmation to identify outliers:
        - Price spike WITHOUT high volume = Bad tick (interpolate)
        - Price spike WITH high volume = Real market event (keep)

        Args:
            bars: List of HistoricalBar objects
            config: Filter configuration
            symbol: Symbol for logging

        Returns:
            Tuple of (filtered bars, filter statistics)
        """
        if not bars:
            return bars, FilterStats()

        stats = FilterStats(total_bars=len(bars))

        # Convert bars to DataFrame for filtering
        df = pd.DataFrame([{
            'timestamp': bar.timestamp,
            'open': float(bar.open),
            'high': float(bar.high),
            'low': float(bar.low),
            'close': float(bar.close),
            'volume': float(bar.volume),
            'vwap': float(bar.vwap) if bar.vwap else None,
        } for bar in bars])

        if df.empty or len(df) < config.hampel_window:
            return bars, stats

        # Detect bad ticks using selected method
        bad_mask = self._detect_bad_ticks(df, config)
        stats.bad_ticks_found = bad_mask.sum()

        if stats.bad_ticks_found == 0:
            logger.debug(f"   {symbol}: No bad ticks detected")
            return bars, stats

        # Apply cleaning based on mode
        if config.cleaning_mode == "remove":
            df_clean = df[~bad_mask].copy()
            stats.bad_ticks_removed = stats.bad_ticks_found
            logger.info(f"   🧹 {symbol}: Removed {stats.bad_ticks_removed} bad ticks")

        elif config.cleaning_mode == "interpolate":
            df_clean = self._interpolate_bad_ticks(df, bad_mask)
            stats.bad_ticks_interpolated = stats.bad_ticks_found
            logger.info(f"   🔧 {symbol}: Interpolated {stats.bad_ticks_interpolated} bad ticks")

        elif config.cleaning_mode == "forward_fill":
            df_clean = self._forward_fill_bad_ticks(df, bad_mask)
            stats.bad_ticks_interpolated = stats.bad_ticks_found
            logger.info(f"   ⏭️ {symbol}: Forward-filled {stats.bad_ticks_found} bad ticks")

        else:
            logger.warning(f"Unknown cleaning mode: {config.cleaning_mode}, skipping filter")
            return bars, stats

        # Convert back to HistoricalBar objects
        filtered_bars = []
        for _, row in df_clean.iterrows():
            filtered_bars.append(HistoricalBar(
                timestamp=row['timestamp'],
                open=Decimal(str(row['open'])),
                high=Decimal(str(row['high'])),
                low=Decimal(str(row['low'])),
                close=Decimal(str(row['close'])),
                volume=Decimal(str(row['volume'])),
                vwap=Decimal(str(row['vwap'])) if pd.notna(row.get('vwap')) else None,
            ))

        return filtered_bars, stats

    def _detect_bad_ticks(self, df: pd.DataFrame, config: FilterConfig) -> pd.Series:
        """Detect bad ticks using the configured method.

        Args:
            df: DataFrame with OHLCV data
            config: Filter configuration

        Returns:
            Boolean Series where True = bad tick
        """
        bad_mask = pd.Series(False, index=df.index)

        # 1. Always check OHLC consistency (invalid data)
        ohlc_bad = (
            (df['high'] < df['low']) |
            (df['open'] < df['low']) | (df['open'] > df['high']) |
            (df['close'] < df['low']) | (df['close'] > df['high'])
        )
        bad_mask |= ohlc_bad

        # 2. Check for zero/negative prices
        price_bad = (df['open'] <= 0) | (df['high'] <= 0) | (df['low'] <= 0) | (df['close'] <= 0)
        bad_mask |= price_bad

        # 3. Apply method-specific detection
        if config.method == "hampel":
            # Hampel Filter with Volume Confirmation
            price_outliers = self._detect_hampel_outliers(df, config)

            # High volume detection - price spikes WITH high volume are real events
            vol_median = df['volume'].rolling(
                window=config.hampel_window,
                center=False,
                min_periods=min(config.hampel_window, len(df))
            ).median()
            is_high_volume = (df['volume'] > vol_median * config.volume_multiplier).fillna(False)

            # Bad tick = price outlier WITHOUT high volume
            hampel_bad = price_outliers & (~is_high_volume)
            bad_mask |= hampel_bad

        elif config.method == "zscore":
            # Z-Score based detection (simpler, less robust)
            zscore_bad = self._detect_zscore_outliers(df, config)
            bad_mask |= zscore_bad

        elif config.method == "basic":
            # Basic percentage deviation (legacy)
            basic_bad = self._detect_basic_outliers(df, config)
            bad_mask |= basic_bad

        # Don't mark first window bars as bad (insufficient context)
        bad_mask.iloc[:config.hampel_window] = False

        return bad_mask

    def _detect_hampel_outliers(self, df: pd.DataFrame, config: FilterConfig) -> pd.Series:
        """Detect price outliers using Hampel Filter (MAD-based).

        MAD (Median Absolute Deviation) is more robust than standard deviation
        because it's not affected by the outliers themselves.

        Args:
            df: DataFrame with price data
            config: Filter configuration

        Returns:
            Boolean Series where True = price outlier
        """
        is_outlier = pd.Series(False, index=df.index)

        if len(df) < config.hampel_window:
            return is_outlier

        # Rolling Median of Close price
        rolling_median = df['close'].rolling(
            window=config.hampel_window,
            center=False,
            min_periods=config.hampel_window
        ).median()

        # Absolute Deviation from median
        deviation = np.abs(df['close'] - rolling_median)

        # Rolling MAD (Median Absolute Deviation)
        mad = deviation.rolling(
            window=config.hampel_window,
            center=False,
            min_periods=3  # Minimum for meaningful median
        ).median()

        # Avoid division by zero for constant prices
        price_range = df['close'].max() - df['close'].min()
        mad_floor = price_range * 1e-6 if price_range > 0 else 1.0
        mad = mad.replace(0, mad_floor)

        # Modified Z-Score (Hampel Filter)
        # 0.6745 is the scaling factor for normal distribution
        with np.errstate(divide='ignore', invalid='ignore'):
            mod_z = 0.6745 * (deviation / mad)

        # Mark as outlier if modified z-score exceeds threshold
        is_outlier = (mod_z > config.hampel_threshold) | np.isinf(mod_z)
        is_outlier = is_outlier.fillna(False)

        return is_outlier

    def _detect_zscore_outliers(self, df: pd.DataFrame, config: FilterConfig) -> pd.Series:
        """Detect outliers using standard Z-Score method."""
        is_outlier = pd.Series(False, index=df.index)

        if len(df) < config.hampel_window:
            return is_outlier

        # Rolling mean and std
        rolling_mean = df['close'].rolling(window=config.hampel_window, min_periods=3).mean()
        rolling_std = df['close'].rolling(window=config.hampel_window, min_periods=3).std()

        # Avoid division by zero
        rolling_std = rolling_std.replace(0, 1e-8)

        # Z-Score
        z_score = np.abs((df['close'] - rolling_mean) / rolling_std)

        is_outlier = z_score > config.hampel_threshold
        return is_outlier.fillna(False)

    def _detect_basic_outliers(self, df: pd.DataFrame, config: FilterConfig) -> pd.Series:
        """Detect outliers using simple percentage deviation from moving average."""
        is_outlier = pd.Series(False, index=df.index)

        if len(df) < config.hampel_window:
            return is_outlier

        # Simple moving average
        ma = df['close'].rolling(window=config.hampel_window, min_periods=3).mean()

        # Percentage deviation
        deviation_pct = np.abs((df['close'] - ma) / ma * 100)

        # 10% threshold for basic detection
        is_outlier = deviation_pct > 10.0
        return is_outlier.fillna(False)

    def _interpolate_bad_ticks(self, df: pd.DataFrame, bad_mask: pd.Series) -> pd.DataFrame:
        """Replace bad tick values with interpolated values.

        Uses linear interpolation to maintain data continuity without gaps.
        """
        df_clean = df.copy()
        cols_ohlc = ['open', 'high', 'low', 'close']

        # Set bad tick OHLC to NaN
        df_clean.loc[bad_mask, cols_ohlc] = np.nan

        # Interpolate (time-based if timestamp available)
        if 'timestamp' in df_clean.columns and pd.api.types.is_datetime64_any_dtype(df_clean['timestamp']):
            df_clean = df_clean.set_index('timestamp')
            df_clean[cols_ohlc] = df_clean[cols_ohlc].interpolate(method='time')
            df_clean = df_clean.reset_index()
        else:
            df_clean[cols_ohlc] = df_clean[cols_ohlc].interpolate(method='linear', limit_direction='both')

        # Volume: use forward/backward fill (don't interpolate volume)
        df_clean.loc[bad_mask, 'volume'] = np.nan
        df_clean['volume'] = df_clean['volume'].ffill().bfill()

        return df_clean

    def _forward_fill_bad_ticks(self, df: pd.DataFrame, bad_mask: pd.Series) -> pd.DataFrame:
        """Replace bad tick values with previous valid values."""
        df_clean = df.copy()
        cols = ['open', 'high', 'low', 'close', 'volume']

        for col in cols:
            if col in df_clean.columns:
                df_clean.loc[bad_mask, col] = np.nan
                df_clean[col] = df_clean[col].ffill().bfill()

        return df_clean

    def get_last_filter_stats(self) -> FilterStats | None:
        """Get statistics from the last filtering operation."""
        return self._last_filter_stats

    async def _save_bars_batched(
        self,
        bars: list[HistoricalBar],
        db_symbol: str,
        source: str,
        batch_size: int = 100,
    ) -> int:
        """Save bars to database in batches.

        Args:
            bars: List of historical bars
            db_symbol: Symbol with source prefix (e.g., "bitunix:BTCUSDT")
            source: Source name for metadata
            batch_size: Number of bars per batch

        Returns:
            Number of bars saved (excluding duplicates)
        """
        total_saved = 0
        total_batches = (len(bars) + batch_size - 1) // batch_size

        for i in range(0, len(bars), batch_size):
            batch = bars[i:i + batch_size]
            batch_num = (i // batch_size) + 1

            try:
                saved = await asyncio.to_thread(
                    self._save_batch_sync,
                    batch,
                    db_symbol,
                    source
                )
                total_saved += saved

                if batch_num % 10 == 0 or batch_num == total_batches:
                    logger.debug(f"   Batch {batch_num}/{total_batches}: Saved {saved} bars")

            except Exception as e:
                logger.error(f"   Batch {batch_num} failed: {e}")

        return total_saved

    def _save_batch_sync(
        self,
        bars: list[HistoricalBar],
        db_symbol: str,
        source: str,
    ) -> int:
        """Synchronously save a batch of bars (runs in thread).

        Args:
            bars: List of bars to save
            db_symbol: Database symbol with source prefix
            source: Source name

        Returns:
            Number of bars saved (duplicates are skipped via ON CONFLICT)
        """
        saved_count = 0

        with self.db_manager.session() as session:
            for bar in bars:
                try:
                    # Create MarketBar instance
                    market_bar = MarketBar(
                        symbol=db_symbol,
                        timestamp=bar.timestamp,
                        open=bar.open,
                        high=bar.high,
                        low=bar.low,
                        close=bar.close,
                        volume=bar.volume,
                        vwap=bar.vwap,
                        source=source,
                        is_interpolated=False,
                    )

                    # Add and commit (unique constraint will skip duplicates)
                    session.add(market_bar)
                    session.flush()  # Flush to check for constraint violations
                    saved_count += 1

                except Exception as e:
                    # Skip duplicates (unique constraint violation)
                    session.rollback()
                    if "UNIQUE constraint failed" in str(e) or "duplicate key" in str(e):
                        continue  # Skip duplicate
                    else:
                        logger.warning(f"Error saving bar for {db_symbol}: {e}")

            session.commit()

        return saved_count

    async def get_data_coverage(
        self,
        symbol: str,
        source: DataSource,
    ) -> dict:
        """Get coverage information for a symbol.

        Args:
            symbol: Symbol to check
            source: Data source

        Returns:
            Dictionary with coverage info (first_date, last_date, total_bars)
        """
        db_symbol = format_symbol_with_source(symbol, source)

        return await asyncio.to_thread(
            self._get_coverage_sync,
            db_symbol
        )

    def _get_coverage_sync(self, db_symbol: str) -> dict:
        """Get coverage info synchronously."""
        with self.db_manager.session() as session:
            from sqlalchemy import func

            result = session.query(
                func.min(MarketBar.timestamp).label('first_date'),
                func.max(MarketBar.timestamp).label('last_date'),
                func.count(MarketBar.id).label('total_bars')
            ).filter(
                MarketBar.symbol == db_symbol
            ).first()

            if not result or result.total_bars == 0:
                return {
                    'symbol': db_symbol,
                    'first_date': None,
                    'last_date': None,
                    'total_bars': 0,
                    'coverage_days': 0
                }

            coverage_days = (result.last_date - result.first_date).days if result.first_date else 0

            return {
                'symbol': db_symbol,
                'first_date': result.first_date,
                'last_date': result.last_date,
                'total_bars': result.total_bars,
                'coverage_days': coverage_days
            }

    async def verify_data_integrity(
        self,
        symbol: str,
        source: DataSource,
        expected_timeframe: Timeframe = Timeframe.MINUTE_1,
    ) -> dict:
        """Verify data integrity and find gaps.

        Args:
            symbol: Symbol to verify
            source: Data source
            expected_timeframe: Expected timeframe between bars

        Returns:
            Dictionary with integrity info (gaps, missing_bars, etc.)
        """
        db_symbol = format_symbol_with_source(symbol, source)

        return await asyncio.to_thread(
            self._verify_integrity_sync,
            db_symbol,
            expected_timeframe
        )

    def _verify_integrity_sync(
        self,
        db_symbol: str,
        expected_timeframe: Timeframe,
    ) -> dict:
        """Verify integrity synchronously."""
        with self.db_manager.session() as session:
            bars = session.query(MarketBar).filter(
                MarketBar.symbol == db_symbol
            ).order_by(MarketBar.timestamp).all()

            if len(bars) < 2:
                return {
                    'symbol': db_symbol,
                    'total_bars': len(bars),
                    'gaps_found': 0,
                    'missing_bars': 0,
                    'integrity': 'insufficient_data'
                }

            # Calculate expected interval
            interval_map = {
                Timeframe.MINUTE_1: timedelta(minutes=1),
                Timeframe.MINUTE_5: timedelta(minutes=5),
                Timeframe.MINUTE_15: timedelta(minutes=15),
                Timeframe.HOUR_1: timedelta(hours=1),
                Timeframe.HOUR_4: timedelta(hours=4),
                Timeframe.DAY_1: timedelta(days=1),
            }
            expected_interval = interval_map.get(expected_timeframe, timedelta(minutes=1))

            # Find gaps
            gaps = []
            missing_bars = 0

            for i in range(1, len(bars)):
                actual_interval = bars[i].timestamp - bars[i-1].timestamp
                if actual_interval > expected_interval * 1.5:  # Allow 50% tolerance
                    gap_minutes = actual_interval.total_seconds() / 60
                    expected_bars = int(gap_minutes / (expected_interval.total_seconds() / 60))
                    gaps.append({
                        'start': bars[i-1].timestamp,
                        'end': bars[i].timestamp,
                        'duration': actual_interval,
                        'missing_bars': expected_bars
                    })
                    missing_bars += expected_bars

            return {
                'symbol': db_symbol,
                'total_bars': len(bars),
                'gaps_found': len(gaps),
                'missing_bars': missing_bars,
                'gaps': gaps[:10],  # First 10 gaps
                'integrity': 'good' if len(gaps) == 0 else 'gaps_found'
            }

    async def clean_existing_data(
        self,
        symbol: str,
        source: DataSource,
        filter_config: FilterConfig | None = None,
        dry_run: bool = True,
    ) -> FilterStats:
        """Clean bad ticks from already stored data in the database.

        This method loads existing data, detects bad ticks, and either:
        - dry_run=True: Reports what would be cleaned (safe preview)
        - dry_run=False: Actually updates/removes bad ticks in the database

        Args:
            symbol: Symbol to clean (e.g., "BTC/USD")
            source: Data source (e.g., DataSource.ALPACA_CRYPTO)
            filter_config: Filter configuration (uses instance config if None)
            dry_run: If True, only report what would be cleaned without modifying

        Returns:
            FilterStats with cleaning results

        Example:
            >>> manager = HistoricalDataManager()
            >>> # Preview what would be cleaned
            >>> stats = await manager.clean_existing_data("BTC/USD", DataSource.ALPACA_CRYPTO, dry_run=True)
            >>> print(f"Would clean {stats.bad_ticks_found} bad ticks")
            >>> # Actually clean
            >>> stats = await manager.clean_existing_data("BTC/USD", DataSource.ALPACA_CRYPTO, dry_run=False)
        """
        config = filter_config or self.filter_config
        db_symbol = format_symbol_with_source(symbol, source)

        logger.info(f"{'🔍 DRY RUN - ' if dry_run else ''}Cleaning bad ticks for {db_symbol}...")
        logger.info(f"   Filter: {config.method}, Mode: {config.cleaning_mode}")

        return await asyncio.to_thread(
            self._clean_existing_data_sync,
            db_symbol,
            config,
            dry_run
        )

    def _clean_existing_data_sync(
        self,
        db_symbol: str,
        config: FilterConfig,
        dry_run: bool,
    ) -> FilterStats:
        """Synchronously clean existing data (runs in thread)."""
        stats = FilterStats()

        with self.db_manager.session() as session:
            # Load all bars for this symbol
            bars = session.query(MarketBar).filter(
                MarketBar.symbol == db_symbol
            ).order_by(MarketBar.timestamp).all()

            if not bars:
                logger.warning(f"No data found for {db_symbol}")
                return stats

            stats.total_bars = len(bars)
            logger.info(f"   Loaded {len(bars)} bars for analysis")

            # Convert to DataFrame for filtering
            df = pd.DataFrame([{
                'id': bar.id,
                'timestamp': bar.timestamp,
                'open': float(bar.open),
                'high': float(bar.high),
                'low': float(bar.low),
                'close': float(bar.close),
                'volume': float(bar.volume),
            } for bar in bars])

            if len(df) < config.hampel_window:
                logger.warning(f"Not enough data for filtering (need >= {config.hampel_window} bars)")
                return stats

            # Detect bad ticks
            bad_mask = self._detect_bad_ticks(df, config)
            stats.bad_ticks_found = bad_mask.sum()

            if stats.bad_ticks_found == 0:
                logger.info(f"   ✅ No bad ticks found - data is clean!")
                return stats

            bad_df = df[bad_mask]
            logger.warning(f"   ⚠️ Found {stats.bad_ticks_found} bad ticks ({stats.bad_ticks_found/len(df)*100:.2f}%)")

            # Show sample of bad ticks
            for idx, row in bad_df.head(5).iterrows():
                logger.warning(
                    f"      {row['timestamp']}: O={row['open']:.2f} H={row['high']:.2f} "
                    f"L={row['low']:.2f} C={row['close']:.2f}"
                )
            if len(bad_df) > 5:
                logger.warning(f"      ... and {len(bad_df) - 5} more")

            if dry_run:
                logger.info(f"   🔍 DRY RUN complete - no changes made")
                stats.filtering_percentage = stats.bad_ticks_found / stats.total_bars * 100
                return stats

            # Apply cleaning
            if config.cleaning_mode == "remove":
                # Delete bad tick rows from database
                bad_ids = bad_df['id'].tolist()
                for bar_id in bad_ids:
                    session.query(MarketBar).filter(MarketBar.id == bar_id).delete()
                stats.bad_ticks_removed = len(bad_ids)
                logger.info(f"   🗑️ Deleted {len(bad_ids)} bad tick rows")

            elif config.cleaning_mode in ("interpolate", "forward_fill"):
                # Update bad tick rows with interpolated/ffill values
                if config.cleaning_mode == "interpolate":
                    df_clean = self._interpolate_bad_ticks(df, bad_mask)
                else:
                    df_clean = self._forward_fill_bad_ticks(df, bad_mask)

                # Update each bad tick row in database
                for idx in df[bad_mask].index:
                    bar_id = df.loc[idx, 'id']
                    session.query(MarketBar).filter(MarketBar.id == bar_id).update({
                        'open': Decimal(str(df_clean.loc[idx, 'open'])),
                        'high': Decimal(str(df_clean.loc[idx, 'high'])),
                        'low': Decimal(str(df_clean.loc[idx, 'low'])),
                        'close': Decimal(str(df_clean.loc[idx, 'close'])),
                        'volume': Decimal(str(df_clean.loc[idx, 'volume'])),
                        'is_interpolated': True,  # Mark as corrected
                    })
                stats.bad_ticks_interpolated = stats.bad_ticks_found
                logger.info(f"   🔧 Updated {stats.bad_ticks_found} rows with corrected values")

            session.commit()

            stats.filtering_percentage = stats.bad_ticks_found / stats.total_bars * 100
            self._last_filter_stats = stats

            logger.info(f"   ✅ Cleaning complete!")
            return stats

    async def scan_all_symbols_for_bad_ticks(
        self,
        filter_config: FilterConfig | None = None,
    ) -> dict[str, FilterStats]:
        """Scan all symbols in database for bad ticks (dry run).

        Args:
            filter_config: Filter configuration

        Returns:
            Dictionary mapping symbols to their filter stats
        """
        config = filter_config or self.filter_config

        return await asyncio.to_thread(
            self._scan_all_symbols_sync,
            config
        )

    def _scan_all_symbols_sync(self, config: FilterConfig) -> dict[str, FilterStats]:
        """Synchronously scan all symbols."""
        results = {}

        with self.db_manager.session() as session:
            from sqlalchemy import distinct

            # Get all unique symbols
            symbols = session.query(distinct(MarketBar.symbol)).all()
            symbols = [s[0] for s in symbols]

            logger.info(f"🔍 Scanning {len(symbols)} symbols for bad ticks...")

            for db_symbol in symbols:
                # Load bars
                bars = session.query(MarketBar).filter(
                    MarketBar.symbol == db_symbol
                ).order_by(MarketBar.timestamp).all()

                if len(bars) < config.hampel_window:
                    continue

                # Convert to DataFrame
                df = pd.DataFrame([{
                    'timestamp': bar.timestamp,
                    'open': float(bar.open),
                    'high': float(bar.high),
                    'low': float(bar.low),
                    'close': float(bar.close),
                    'volume': float(bar.volume),
                } for bar in bars])

                # Detect bad ticks
                bad_mask = self._detect_bad_ticks(df, config)
                bad_count = bad_mask.sum()

                stats = FilterStats(
                    total_bars=len(bars),
                    bad_ticks_found=bad_count,
                    filtering_percentage=bad_count / len(bars) * 100 if len(bars) > 0 else 0
                )
                results[db_symbol] = stats

                if bad_count > 0:
                    logger.warning(f"   {db_symbol}: {bad_count} bad ticks ({stats.filtering_percentage:.2f}%)")

        # Summary
        total_bars = sum(s.total_bars for s in results.values())
        total_bad = sum(s.bad_ticks_found for s in results.values())
        logger.info(f"📊 Scan complete: {total_bad} bad ticks in {total_bars} total bars "
                   f"({total_bad/total_bars*100:.2f}% overall)" if total_bars > 0 else "No data found")

        return results
