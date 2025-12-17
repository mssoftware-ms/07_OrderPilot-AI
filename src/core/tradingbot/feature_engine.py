"""Feature Engine for Tradingbot.

Calculates technical indicators and constructs FeatureVector
objects for bot decision making.

Uses the existing IndicatorEngine for calculations.
"""

from __future__ import annotations

import logging
from datetime import datetime, time, timezone
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd
import pytz

from src.core.indicators.engine import IndicatorEngine
from src.core.indicators.types import IndicatorConfig, IndicatorResult, IndicatorType

from .models import FeatureVector

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

# Trading session definitions
NASDAQ_RTH = {
    'start': time(9, 30),
    'end': time(16, 0),
    'tz': 'America/New_York'
}

CRYPTO_24_7 = {
    'start': time(0, 0),
    'end': time(23, 59, 59),
    'tz': 'UTC'
}


class FeatureEngine:
    """Engine for calculating features from market data.

    Integrates with IndicatorEngine to compute all required
    technical indicators and constructs FeatureVector objects.
    """

    # Default indicator periods
    DEFAULT_PERIODS = {
        'sma_fast': 20,
        'sma_slow': 50,
        'ema_fast': 12,
        'ema_slow': 26,
        'rsi': 14,
        'atr': 14,
        'bb': 20,
        'adx': 14,
        'stoch': 14,
        'cci': 20,
        'mfi': 14,
        'macd_fast': 12,
        'macd_slow': 26,
        'macd_signal': 9,
    }

    # Minimum bars needed for valid features
    MIN_BARS = 60  # Need enough for slowest indicator (SMA 50 + warmup)

    def __init__(
        self,
        indicator_engine: IndicatorEngine | None = None,
        periods: dict[str, int] | None = None
    ):
        """Initialize feature engine.

        Args:
            indicator_engine: Existing indicator engine instance.
                            Creates new one if not provided.
            periods: Custom indicator periods. Merges with defaults.
        """
        self.indicator_engine = indicator_engine or IndicatorEngine()
        self.periods = {**self.DEFAULT_PERIODS, **(periods or {})}

        # Pre-build indicator configs
        self._configs = self._build_indicator_configs()

        logger.info(f"FeatureEngine initialized with {len(self._configs)} indicators")

    def _build_indicator_configs(self) -> list[IndicatorConfig]:
        """Build list of indicator configurations."""
        configs = [
            # Trend indicators - SMAs
            IndicatorConfig(
                indicator_type=IndicatorType.SMA,
                params={'period': self.periods['sma_fast']},
                cache_results=True
            ),
            IndicatorConfig(
                indicator_type=IndicatorType.SMA,
                params={'period': self.periods['sma_slow']},
                cache_results=True
            ),
            # Trend indicators - EMAs
            IndicatorConfig(
                indicator_type=IndicatorType.EMA,
                params={'period': self.periods['ema_fast']},
                cache_results=True
            ),
            IndicatorConfig(
                indicator_type=IndicatorType.EMA,
                params={'period': self.periods['ema_slow']},
                cache_results=True
            ),
            # MACD
            IndicatorConfig(
                indicator_type=IndicatorType.MACD,
                params={
                    'fast': self.periods['macd_fast'],
                    'slow': self.periods['macd_slow'],
                    'signal': self.periods['macd_signal']
                },
                cache_results=True
            ),
            # ADX
            IndicatorConfig(
                indicator_type=IndicatorType.ADX,
                params={'period': self.periods['adx']},
                cache_results=True
            ),
            # Momentum - RSI
            IndicatorConfig(
                indicator_type=IndicatorType.RSI,
                params={'period': self.periods['rsi']},
                cache_results=True
            ),
            # Stochastic
            IndicatorConfig(
                indicator_type=IndicatorType.STOCH,
                params={
                    'k': self.periods['stoch'],
                    'd': 3,
                    'smooth_k': 3
                },
                cache_results=True
            ),
            # CCI
            IndicatorConfig(
                indicator_type=IndicatorType.CCI,
                params={'period': self.periods['cci']},
                cache_results=True
            ),
            # MFI
            IndicatorConfig(
                indicator_type=IndicatorType.MFI,
                params={'period': self.periods['mfi']},
                cache_results=True
            ),
            # Volatility - Bollinger Bands
            IndicatorConfig(
                indicator_type=IndicatorType.BB,
                params={
                    'period': self.periods['bb'],
                    'std': 2.0
                },
                cache_results=True
            ),
            # ATR
            IndicatorConfig(
                indicator_type=IndicatorType.ATR,
                params={'period': self.periods['atr']},
                cache_results=True
            ),
        ]
        return configs

    def calculate_features(
        self,
        data: pd.DataFrame,
        symbol: str,
        timestamp: datetime | None = None
    ) -> FeatureVector | None:
        """Calculate feature vector from OHLCV data.

        Args:
            data: DataFrame with columns: open, high, low, close, volume
                  Should have at least MIN_BARS rows.
            symbol: Trading symbol
            timestamp: Override timestamp (uses last bar if not provided)

        Returns:
            FeatureVector with all calculated indicators, or None if
            insufficient data.
        """
        # Validate data
        if len(data) < self.MIN_BARS:
            logger.warning(
                f"Insufficient data for features: {len(data)} bars, "
                f"need {self.MIN_BARS}"
            )
            return None

        # Ensure proper column names
        data = self._normalize_columns(data)

        # Get latest bar data
        latest = data.iloc[-1]
        ts = timestamp or (
            latest.name if isinstance(latest.name, datetime)
            else datetime.utcnow()
        )

        # Calculate all indicators
        results = self._calculate_all_indicators(data)

        # Extract values from results
        feature_dict = self._extract_feature_values(results, data)

        # Calculate derived features
        derived = self._calculate_derived_features(feature_dict, data)
        feature_dict.update(derived)

        # Build FeatureVector
        try:
            features = FeatureVector(
                timestamp=ts,
                symbol=symbol,
                open=float(latest['open']),
                high=float(latest['high']),
                low=float(latest['low']),
                close=float(latest['close']),
                volume=float(latest['volume']),
                **feature_dict
            )
            return features
        except Exception as e:
            logger.error(f"Error building FeatureVector: {e}")
            return None

    def _normalize_columns(self, data: pd.DataFrame) -> pd.DataFrame:
        """Normalize column names to lowercase."""
        data = data.copy()
        data.columns = data.columns.str.lower()
        return data

    def preprocess_candles(
        self,
        data: pd.DataFrame,
        market_type: str = "STOCK",
        target_tz: str = "America/New_York",
        fill_missing: bool = True,
        filter_sessions: bool = True
    ) -> pd.DataFrame:
        """Preprocess candles for feature calculation.

        Handles:
        - Timezone normalization
        - Missing candle detection and forward-fill
        - Session filtering (RTH for stocks, 24/7 for crypto)
        - Invalid price detection

        Args:
            data: DataFrame with OHLCV columns and datetime index
            market_type: "STOCK" or "CRYPTO"
            target_tz: Target timezone for normalization
            fill_missing: Whether to forward-fill missing candles
            filter_sessions: Whether to filter to valid trading sessions

        Returns:
            Preprocessed DataFrame
        """
        df = data.copy()

        # Ensure datetime index
        if not isinstance(df.index, pd.DatetimeIndex):
            if 'timestamp' in df.columns:
                df = df.set_index('timestamp')
            elif 'datetime' in df.columns:
                df = df.set_index('datetime')
            elif 'date' in df.columns:
                df = df.set_index('date')

        # Sort by time
        df = df.sort_index()

        # === TIMEZONE NORMALIZATION ===
        if df.index.tz is None:
            # Assume UTC if no timezone
            df.index = df.index.tz_localize('UTC')
        df.index = df.index.tz_convert(target_tz)

        # === INVALID PRICE DETECTION ===
        # Replace zero/negative prices with NaN
        price_cols = ['open', 'high', 'low', 'close']
        for col in price_cols:
            if col in df.columns:
                df.loc[df[col] <= 0, col] = np.nan

        # Replace infinite values
        df = df.replace([np.inf, -np.inf], np.nan)

        # === MISSING CANDLE HANDLING ===
        if fill_missing and len(df) > 0:
            # Detect expected frequency
            freq = pd.infer_freq(df.index)
            if freq is None and len(df) > 1:
                # Estimate from median time delta
                deltas = df.index.to_series().diff().dropna()
                if len(deltas) > 0:
                    median_delta = deltas.median()
                    freq = f"{int(median_delta.total_seconds() // 60)}T"

            if freq:
                # Count gaps before reindex
                expected_idx = pd.date_range(
                    start=df.index.min(),
                    end=df.index.max(),
                    freq=freq,
                    tz=df.index.tz
                )
                missing_count = len(expected_idx) - len(df)
                if missing_count > 0:
                    logger.debug(f"Filling {missing_count} missing candles")

                # Reindex to fill gaps
                df = df.reindex(expected_idx)

                # Forward fill OHLC (use previous close for all)
                for col in price_cols:
                    if col in df.columns:
                        df[col] = df[col].ffill()

                # Volume: fill with 0 for missing
                if 'volume' in df.columns:
                    df['volume'] = df['volume'].fillna(0)

        # === SESSION FILTERING ===
        if filter_sessions and market_type == "STOCK":
            # NASDAQ Regular Trading Hours
            session = NASDAQ_RTH
            df_time = df.index.time
            mask = (df_time >= session['start']) & (df_time <= session['end'])

            # Also filter weekends
            weekday_mask = df.index.dayofweek < 5  # Mon-Fri = 0-4
            df = df[mask & weekday_mask]

            if len(df) == 0:
                logger.warning("No candles in RTH session after filtering")

        # Drop any remaining NaN rows (first few rows may have NaN after ffill)
        df = df.dropna(subset=['close'])

        logger.debug(
            f"Preprocessed {len(df)} candles "
            f"({market_type}, tz={target_tz})"
        )

        return df

    def detect_missing_candles(
        self,
        data: pd.DataFrame,
        expected_freq: str = "1T"
    ) -> list[datetime]:
        """Detect timestamps where candles are missing.

        Args:
            data: DataFrame with datetime index
            expected_freq: Expected candle frequency (e.g., "1T", "5T", "1H")

        Returns:
            List of missing timestamps
        """
        if len(data) < 2:
            return []

        expected_idx = pd.date_range(
            start=data.index.min(),
            end=data.index.max(),
            freq=expected_freq
        )

        actual_idx = set(data.index)
        missing = [ts for ts in expected_idx if ts not in actual_idx]

        if missing:
            logger.info(f"Detected {len(missing)} missing candles")

        return missing

    def validate_candles(self, data: pd.DataFrame) -> dict:
        """Validate candle data quality.

        Returns dict with validation results:
        - is_valid: Overall validity
        - issues: List of detected issues
        - stats: Data quality statistics
        """
        issues = []
        stats = {}

        # Check required columns
        required = ['open', 'high', 'low', 'close', 'volume']
        missing_cols = [c for c in required if c.lower() not in data.columns.str.lower()]
        if missing_cols:
            issues.append(f"Missing columns: {missing_cols}")

        # Check for NaN values
        nan_counts = data.isna().sum()
        stats['nan_counts'] = nan_counts.to_dict()
        if nan_counts.sum() > 0:
            issues.append(f"NaN values detected: {nan_counts.sum()} total")

        # Check OHLC consistency (high >= low, etc.)
        if 'high' in data.columns and 'low' in data.columns:
            inconsistent = (data['high'] < data['low']).sum()
            if inconsistent > 0:
                issues.append(f"OHLC inconsistency (high < low): {inconsistent} rows")
            stats['ohlc_inconsistent'] = inconsistent

        # Check for zero/negative prices
        for col in ['open', 'high', 'low', 'close']:
            if col in data.columns:
                invalid = (data[col] <= 0).sum()
                if invalid > 0:
                    issues.append(f"Invalid {col} prices (<= 0): {invalid}")
                stats[f'{col}_invalid'] = invalid

        # Check for extreme price jumps (> 20% in one bar)
        if 'close' in data.columns and len(data) > 1:
            pct_change = data['close'].pct_change().abs()
            extreme_moves = (pct_change > 0.20).sum()
            if extreme_moves > 0:
                issues.append(f"Extreme price moves (>20%): {extreme_moves}")
            stats['extreme_moves'] = extreme_moves

        stats['total_rows'] = len(data)
        stats['issues_count'] = len(issues)

        return {
            'is_valid': len(issues) == 0,
            'issues': issues,
            'stats': stats
        }

    def _calculate_all_indicators(
        self,
        data: pd.DataFrame
    ) -> dict[str, IndicatorResult]:
        """Calculate all configured indicators.

        Returns dict keyed by indicator identifier.
        """
        results = {}

        for config in self._configs:
            try:
                result = self.indicator_engine.calculate(data, config)
                # Create unique key for each indicator+params
                key = self._result_key(config)
                results[key] = result
            except Exception as e:
                logger.warning(
                    f"Failed to calculate {config.indicator_type.value}: {e}"
                )

        return results

    def _result_key(self, config: IndicatorConfig) -> str:
        """Generate unique key for indicator result."""
        params_str = '_'.join(f"{k}{v}" for k, v in sorted(config.params.items()))
        return f"{config.indicator_type.value}_{params_str}"

    def _extract_feature_values(
        self,
        results: dict[str, IndicatorResult],
        data: pd.DataFrame
    ) -> dict[str, float | None]:
        """Extract latest values from indicator results."""
        features: dict[str, float | None] = {}

        # SMA values
        sma_fast_key = f"sma_period{self.periods['sma_fast']}"
        sma_slow_key = f"sma_period{self.periods['sma_slow']}"

        if sma_fast_key in results:
            features['sma_20'] = self._get_last_value(results[sma_fast_key].values)
        if sma_slow_key in results:
            features['sma_50'] = self._get_last_value(results[sma_slow_key].values)

        # EMA values
        ema_fast_key = f"ema_period{self.periods['ema_fast']}"
        ema_slow_key = f"ema_period{self.periods['ema_slow']}"

        if ema_fast_key in results:
            features['ema_12'] = self._get_last_value(results[ema_fast_key].values)
        if ema_slow_key in results:
            features['ema_26'] = self._get_last_value(results[ema_slow_key].values)

        # MACD (multi-column result)
        macd_key = f"macd_fast{self.periods['macd_fast']}_signal{self.periods['macd_signal']}_slow{self.periods['macd_slow']}"
        if macd_key in results:
            macd_result = results[macd_key].values
            if isinstance(macd_result, pd.DataFrame):
                features['macd'] = self._get_last_value(macd_result.get('macd'))
                features['macd_signal'] = self._get_last_value(macd_result.get('signal'))
                features['macd_hist'] = self._get_last_value(macd_result.get('histogram'))
            elif isinstance(macd_result, dict):
                features['macd'] = self._get_last_value(macd_result.get('macd'))
                features['macd_signal'] = self._get_last_value(macd_result.get('signal'))
                features['macd_hist'] = self._get_last_value(macd_result.get('histogram'))

        # ADX (multi-column result)
        adx_key = f"adx_period{self.periods['adx']}"
        if adx_key in results:
            adx_result = results[adx_key].values
            if isinstance(adx_result, pd.DataFrame):
                features['adx'] = self._get_last_value(adx_result.get('adx'))
                features['plus_di'] = self._get_last_value(adx_result.get('plus_di', adx_result.get('+di')))
                features['minus_di'] = self._get_last_value(adx_result.get('minus_di', adx_result.get('-di')))
            elif isinstance(adx_result, dict):
                features['adx'] = self._get_last_value(adx_result.get('adx'))
                features['plus_di'] = self._get_last_value(adx_result.get('plus_di', adx_result.get('+di')))
                features['minus_di'] = self._get_last_value(adx_result.get('minus_di', adx_result.get('-di')))
            elif isinstance(adx_result, pd.Series):
                features['adx'] = self._get_last_value(adx_result)

        # RSI
        rsi_key = f"rsi_period{self.periods['rsi']}"
        if rsi_key in results:
            features['rsi_14'] = self._get_last_value(results[rsi_key].values)

        # Stochastic (multi-column result)
        stoch_key = f"stoch_d3_k{self.periods['stoch']}_smooth_k3"
        if stoch_key in results:
            stoch_result = results[stoch_key].values
            if isinstance(stoch_result, pd.DataFrame):
                features['stoch_k'] = self._get_last_value(stoch_result.get('k', stoch_result.get('%k')))
                features['stoch_d'] = self._get_last_value(stoch_result.get('d', stoch_result.get('%d')))
            elif isinstance(stoch_result, dict):
                features['stoch_k'] = self._get_last_value(stoch_result.get('k', stoch_result.get('%k')))
                features['stoch_d'] = self._get_last_value(stoch_result.get('d', stoch_result.get('%d')))

        # CCI
        cci_key = f"cci_period{self.periods['cci']}"
        if cci_key in results:
            features['cci'] = self._get_last_value(results[cci_key].values)

        # MFI
        mfi_key = f"mfi_period{self.periods['mfi']}"
        if mfi_key in results:
            features['mfi'] = self._get_last_value(results[mfi_key].values)

        # Bollinger Bands (multi-column result)
        bb_key = f"bb_period{self.periods['bb']}_std2.0"
        if bb_key in results:
            bb_result = results[bb_key].values
            if isinstance(bb_result, pd.DataFrame):
                features['bb_upper'] = self._get_last_value(bb_result.get('upper'))
                features['bb_middle'] = self._get_last_value(bb_result.get('middle'))
                features['bb_lower'] = self._get_last_value(bb_result.get('lower'))
            elif isinstance(bb_result, dict):
                features['bb_upper'] = self._get_last_value(bb_result.get('upper'))
                features['bb_middle'] = self._get_last_value(bb_result.get('middle'))
                features['bb_lower'] = self._get_last_value(bb_result.get('lower'))

        # ATR
        atr_key = f"atr_period{self.periods['atr']}"
        if atr_key in results:
            features['atr_14'] = self._get_last_value(results[atr_key].values)

        return features

    def _get_last_value(self, values) -> float | None:
        """Safely extract last value from Series, array, or scalar."""
        if values is None:
            return None

        try:
            if isinstance(values, pd.Series):
                val = values.iloc[-1]
            elif isinstance(values, (list, tuple)):
                val = values[-1]
            elif hasattr(values, '__getitem__'):
                val = values[-1]
            else:
                val = values

            if pd.isna(val):
                return None
            return float(val)
        except (IndexError, TypeError, ValueError):
            return None

    def _calculate_derived_features(
        self,
        features: dict[str, float | None],
        data: pd.DataFrame
    ) -> dict[str, float | None]:
        """Calculate derived features from base indicators."""
        derived: dict[str, float | None] = {}

        close = float(data['close'].iloc[-1])

        # MA slope (normalized, using last 5 bars)
        if features.get('sma_20') is not None:
            sma_5_ago = self._get_sma_at_index(data, self.periods['sma_fast'], -5)
            sma_now = features['sma_20']
            if sma_5_ago is not None and sma_now is not None and sma_5_ago != 0:
                # Percent change over 5 bars, normalized
                derived['ma_slope_20'] = ((sma_now - sma_5_ago) / sma_5_ago) * 100
            else:
                derived['ma_slope_20'] = None

        # Price vs SMA20 (percent)
        if features.get('sma_20') is not None and features['sma_20'] != 0:
            derived['price_vs_sma20'] = ((close / features['sma_20']) - 1) * 100
        else:
            derived['price_vs_sma20'] = None

        # Volume ratio (current vs 20-bar average)
        if len(data) >= 20:
            avg_volume = data['volume'].iloc[-20:].mean()
            current_volume = float(data['volume'].iloc[-1])
            if avg_volume > 0:
                derived['volume_ratio'] = current_volume / avg_volume
            else:
                derived['volume_ratio'] = None
        else:
            derived['volume_ratio'] = None

        # BB width and %B
        bb_upper = features.get('bb_upper')
        bb_lower = features.get('bb_lower')
        bb_middle = features.get('bb_middle')

        if bb_upper is not None and bb_lower is not None and bb_middle is not None:
            if bb_middle != 0:
                derived['bb_width'] = (bb_upper - bb_lower) / bb_middle
            else:
                derived['bb_width'] = None

            if bb_upper != bb_lower:
                derived['bb_pct'] = (close - bb_lower) / (bb_upper - bb_lower)
            else:
                derived['bb_pct'] = 0.5

        return derived

    def _get_sma_at_index(
        self,
        data: pd.DataFrame,
        period: int,
        index: int
    ) -> float | None:
        """Calculate SMA at a specific index."""
        try:
            end_idx = len(data) + index
            if end_idx < period:
                return None
            start_idx = end_idx - period
            return float(data['close'].iloc[start_idx:end_idx].mean())
        except (IndexError, ValueError):
            return None

    def get_required_bars(self) -> int:
        """Get minimum bars required for feature calculation."""
        return self.MIN_BARS

    def clear_cache(self) -> None:
        """Clear indicator cache."""
        self.indicator_engine.clear_cache()
        logger.debug("Feature engine cache cleared")
