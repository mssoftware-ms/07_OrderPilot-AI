"""Resampling and Noise Reduction for Market Data.

Handles resampling of market data to 1-second bars with noise filtering.
"""

import logging
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

import numpy as np
import pandas as pd

from src.common.event_bus import Event, EventType, event_bus

logger = logging.getLogger(__name__)


@dataclass
class OHLCV:
    """OHLC data with volume."""
    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int = 0
    vwap: Decimal | None = None
    trades: int = 0


class NoiseFilter:
    """Base class for noise filters."""

    def filter(self, values: list[Decimal]) -> Decimal:
        """Apply filter to values.

        Args:
            values: List of values to filter

        Returns:
            Filtered value
        """
        raise NotImplementedError


class MedianFilter(NoiseFilter):
    """Median filter for noise reduction."""

    def __init__(self, window_size: int = 3):
        """Initialize median filter.

        Args:
            window_size: Size of the filter window
        """
        self.window_size = window_size

    def filter(self, values: list[Decimal]) -> Decimal:
        """Apply median filter.

        Args:
            values: List of values to filter

        Returns:
            Median value
        """
        if not values:
            return Decimal('0')

        if len(values) < self.window_size:
            # Not enough values, return last value
            return values[-1]

        # Get last window_size values
        window = values[-self.window_size:]

        # Convert to float for numpy, then back to Decimal
        np_values = [float(v) for v in window]
        median = np.median(np_values)

        return Decimal(str(median))


class MovingAverageFilter(NoiseFilter):
    """Moving average filter for noise reduction."""

    def __init__(self, window_size: int = 3, alpha: float = 0.3):
        """Initialize MA filter.

        Args:
            window_size: Size of the filter window
            alpha: Exponential smoothing factor for EMA
        """
        self.window_size = window_size
        self.alpha = alpha

    def filter(self, values: list[Decimal]) -> Decimal:
        """Apply moving average filter.

        Args:
            values: List of values to filter

        Returns:
            Moving average value
        """
        if not values:
            return Decimal('0')

        if len(values) < self.window_size:
            # Simple average of available values
            return sum(values) / len(values)

        # Get last window_size values
        window = values[-self.window_size:]

        # Simple moving average
        sma = sum(window) / len(window)

        return sma


class KalmanFilter(NoiseFilter):
    """Kalman filter for advanced noise reduction."""

    def __init__(self, process_variance: float = 1e-5, measurement_variance: float = 1e-2):
        """Initialize Kalman filter.

        Args:
            process_variance: Process noise variance
            measurement_variance: Measurement noise variance
        """
        self.process_variance = process_variance
        self.measurement_variance = measurement_variance

        # State variables
        self.estimate = None
        self.error_covariance = 1.0

    def filter(self, values: list[Decimal]) -> Decimal:
        """Apply Kalman filter.

        Args:
            values: List of values to filter

        Returns:
            Kalman filtered value
        """
        if not values:
            return Decimal('0')

        current_value = float(values[-1])

        if self.estimate is None:
            # Initialize with first value
            self.estimate = current_value
            return values[-1]

        # Prediction step
        prediction = self.estimate
        prediction_error = self.error_covariance + self.process_variance

        # Update step
        kalman_gain = prediction_error / (prediction_error + self.measurement_variance)
        self.estimate = prediction + kalman_gain * (current_value - prediction)
        self.error_covariance = (1 - kalman_gain) * prediction_error

        return Decimal(str(self.estimate))


class MarketDataResampler:
    """Resamples market data to specified intervals with noise reduction."""

    def __init__(
        self,
        resample_interval: str = "1S",
        filter_type: str = "median",
        filter_window: int = 3,
        buffer_size: int = 10000
    ):
        """Initialize resampler.

        Args:
            resample_interval: Resampling interval (pandas format)
            filter_type: Type of noise filter (median, ma, kalman)
            filter_window: Window size for filter
            buffer_size: Size of the data buffer
        """
        self.resample_interval = resample_interval
        self.filter_window = filter_window
        self.buffer_size = buffer_size

        # Initialize filter
        if filter_type == "median":
            self.filter = MedianFilter(filter_window)
        elif filter_type == "ma":
            self.filter = MovingAverageFilter(filter_window)
        elif filter_type == "kalman":
            self.filter = KalmanFilter()
        else:
            self.filter = MedianFilter(filter_window)

        # Data buffers per symbol
        self.tick_buffers: dict[str, deque] = defaultdict(
            lambda: deque(maxlen=buffer_size)
        )
        self.price_buffers: dict[str, deque[Decimal]] = defaultdict(
            lambda: deque(maxlen=filter_window * 2)
        )
        self.bar_buffers: dict[str, list[OHLCV]] = defaultdict(list)

        # Last bar timestamps
        self.last_bar_time: dict[str, datetime] = {}

        logger.info(f"Resampler initialized: {resample_interval} with {filter_type} filter")

    def add_tick(self, symbol: str, price: Decimal, volume: int = 0,
                 timestamp: datetime | None = None) -> OHLCV | None:
        """Add a tick and return resampled bar if ready.

        Args:
            symbol: Trading symbol
            price: Tick price
            volume: Tick volume
            timestamp: Tick timestamp

        Returns:
            OHLCV bar if a new bar is complete, None otherwise
        """
        if timestamp is None:
            timestamp = datetime.utcnow()

        # Add to buffers
        self.tick_buffers[symbol].append({
            'price': price,
            'volume': volume,
            'timestamp': timestamp
        })
        self.price_buffers[symbol].append(price)

        # Apply noise filter
        filtered_price = self.filter.filter(list(self.price_buffers[symbol]))

        # Check if we should create a new bar
        bar_time = self._get_bar_time(timestamp)

        if symbol not in self.last_bar_time:
            self.last_bar_time[symbol] = bar_time
            return None

        if bar_time > self.last_bar_time[symbol]:
            # Create bar for previous period
            bar = self._create_bar(symbol, self.last_bar_time[symbol], bar_time)
            self.last_bar_time[symbol] = bar_time

            if bar:
                # Store bar
                self.bar_buffers[symbol].append(bar)

                # Emit event
                self._emit_bar_event(symbol, bar)

                return bar

        return None

    def _get_bar_time(self, timestamp: datetime) -> datetime:
        """Get the bar time for a given timestamp.

        Args:
            timestamp: Current timestamp

        Returns:
            Bar timestamp (floored to interval)
        """
        # For 1-second bars
        if self.resample_interval == "1S":
            return timestamp.replace(microsecond=0)
        elif self.resample_interval == "5S":
            seconds = (timestamp.second // 5) * 5
            return timestamp.replace(second=seconds, microsecond=0)
        elif self.resample_interval == "1T" or self.resample_interval == "1min":
            return timestamp.replace(second=0, microsecond=0)
        else:
            # Default to 1 second
            return timestamp.replace(microsecond=0)

    def _create_bar(self, symbol: str, start_time: datetime, end_time: datetime) -> OHLCV | None:
        """Create an OHLCV bar from ticks.

        Args:
            symbol: Trading symbol
            start_time: Bar start time
            end_time: Bar end time

        Returns:
            OHLCV bar or None if no data
        """
        # Get ticks in time range
        ticks = [
            t for t in self.tick_buffers[symbol]
            if start_time <= t['timestamp'] < end_time
        ]

        if not ticks:
            return None

        # Extract prices and volumes
        prices = [t['price'] for t in ticks]
        volumes = [t['volume'] for t in ticks]

        # Apply filter to prices
        filtered_prices = []
        for i in range(len(prices)):
            # Build window of prices up to current
            window_start = max(0, i - self.filter_window + 1)
            window = prices[window_start:i + 1]
            filtered_price = self.filter.filter(window)
            filtered_prices.append(filtered_price)

        # Create OHLCV
        bar = OHLCV(
            timestamp=start_time,
            open=filtered_prices[0] if filtered_prices else prices[0],
            high=max(filtered_prices) if filtered_prices else max(prices),
            low=min(filtered_prices) if filtered_prices else min(prices),
            close=filtered_prices[-1] if filtered_prices else prices[-1],
            volume=sum(volumes),
            trades=len(ticks)
        )

        # Calculate VWAP if we have volume
        if bar.volume > 0:
            total_value = sum(p * v for p, v in zip(prices, volumes))
            bar.vwap = total_value / bar.volume

        return bar

    def _emit_bar_event(self, symbol: str, bar: OHLCV) -> None:
        """Emit event for new bar.

        Args:
            symbol: Trading symbol
            bar: OHLCV bar
        """
        event_bus.emit(Event(
            type=EventType.MARKET_BAR,
            timestamp=datetime.utcnow(),
            data={
                'symbol': symbol,
                'bar': {
                    'timestamp': bar.timestamp.isoformat(),
                    'open': float(bar.open),
                    'high': float(bar.high),
                    'low': float(bar.low),
                    'close': float(bar.close),
                    'volume': bar.volume,
                    'vwap': float(bar.vwap) if bar.vwap else None,
                    'trades': bar.trades
                }
            },
            source='resampler'
        ))

    def get_bars(self, symbol: str, count: int = 100) -> list[OHLCV]:
        """Get recent bars for symbol.

        Args:
            symbol: Trading symbol
            count: Number of bars to return

        Returns:
            List of OHLCV bars
        """
        bars = self.bar_buffers.get(symbol, [])
        return bars[-count:] if len(bars) > count else bars

    def get_latest_bar(self, symbol: str) -> OHLCV | None:
        """Get latest bar for symbol.

        Args:
            symbol: Trading symbol

        Returns:
            Latest OHLCV bar or None
        """
        bars = self.bar_buffers.get(symbol)
        return bars[-1] if bars else None

    def resample_dataframe(self, df: pd.DataFrame, interval: str = None) -> pd.DataFrame:
        """Resample a DataFrame of tick data.

        Args:
            df: DataFrame with columns [timestamp, price, volume]
            interval: Resampling interval (uses default if None)

        Returns:
            Resampled DataFrame with OHLCV data
        """
        if interval is None:
            interval = self.resample_interval

        # Ensure timestamp is datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.set_index('timestamp')

        # Resample
        ohlc = df['price'].resample(interval).ohlc()
        volume = df['volume'].resample(interval).sum()

        # Combine
        result = pd.concat([ohlc, volume], axis=1)

        # Apply noise filter to close prices
        if len(result) > 0:
            filtered_close = []
            price_window = deque(maxlen=self.filter_window * 2)

            for close_price in result['close']:
                price_window.append(Decimal(str(close_price)))
                filtered_price = self.filter.filter(list(price_window))
                filtered_close.append(float(filtered_price))

            result['filtered_close'] = filtered_close

        return result

    def detect_anomalies(self, symbol: str, threshold: float = 3.0) -> list[datetime]:
        """Detect anomalous price movements.

        Args:
            symbol: Trading symbol
            threshold: Standard deviation threshold for anomaly

        Returns:
            List of timestamps with anomalies
        """
        bars = self.bar_buffers.get(symbol, [])
        if len(bars) < 20:
            return []

        # Calculate returns
        closes = [float(bar.close) for bar in bars]
        returns = np.diff(np.log(closes))

        # Calculate rolling statistics
        window = min(20, len(returns) // 2)
        rolling_mean = pd.Series(returns).rolling(window).mean()
        rolling_std = pd.Series(returns).rolling(window).std()

        # Find anomalies
        anomalies = []
        for i in range(window, len(returns)):
            if abs(returns[i] - rolling_mean.iloc[i]) > threshold * rolling_std.iloc[i]:
                anomalies.append(bars[i + 1].timestamp)

        return anomalies

    def get_statistics(self, symbol: str) -> dict[str, float]:
        """Get statistics for symbol.

        Args:
            symbol: Trading symbol

        Returns:
            Dictionary of statistics
        """
        bars = self.bar_buffers.get(symbol, [])
        if not bars:
            return {}

        closes = [float(bar.close) for bar in bars]
        volumes = [bar.volume for bar in bars]

        return {
            'mean_price': np.mean(closes),
            'std_price': np.std(closes),
            'min_price': min(closes),
            'max_price': max(closes),
            'total_volume': sum(volumes),
            'avg_volume': np.mean(volumes),
            'bar_count': len(bars)
        }