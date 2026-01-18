"""Feature Engine for Tradingbot.

Calculates technical indicators and constructs FeatureVector
objects for bot decision making.

Uses the existing IndicatorEngine for calculations.

REFACTORED: Preprocessing methods extracted to candle_preprocessing.py
"""

from __future__ import annotations

import logging
from datetime import datetime

import numpy as np
import pandas as pd

from src.core.indicators.engine import IndicatorEngine
from src.core.indicators.types import IndicatorConfig, IndicatorResult, IndicatorType

from .models import FeatureVector

logger = logging.getLogger(__name__)


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
        'chop': 14,  # Choppiness Index
        'ichimoku_tenkan': 9,  # Ichimoku Conversion Line
        'ichimoku_kijun': 26,  # Ichimoku Base Line
        'ichimoku_senkou': 52,  # Ichimoku Leading Span B
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
            # Choppiness Index (range-bound indicator)
            IndicatorConfig(
                indicator_type=IndicatorType.CHOP,
                params={'period': self.periods['chop']},
                cache_results=True
            ),
            # Ichimoku Cloud (trend indicator)
            IndicatorConfig(
                indicator_type=IndicatorType.ICHIMOKU,
                params={
                    'tenkan': self.periods['ichimoku_tenkan'],
                    'kijun': self.periods['ichimoku_kijun'],
                    'senkou': self.periods['ichimoku_senkou']
                },
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

    # Delegate preprocessing methods to module functions for backward compatibility
    def preprocess_candles(self, data: pd.DataFrame, **kwargs) -> pd.DataFrame:
        """Preprocess candles for feature calculation. Delegates to module function."""
        return preprocess_candles(data, **kwargs)

    def detect_missing_candles(self, data: pd.DataFrame, expected_freq: str = "1T") -> list[datetime]:
        """Detect missing candles. Delegates to module function."""
        return detect_missing_candles(data, expected_freq)

    def validate_candles(self, data: pd.DataFrame) -> dict:
        """Validate candle data. Delegates to module function."""
        return validate_candles(data)

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
        self._set_feature_from_result(results, sma_fast_key, 'sma_20', features)
        self._set_feature_from_result(results, sma_slow_key, 'sma_50', features)

        # EMA values
        ema_fast_key = f"ema_period{self.periods['ema_fast']}"
        ema_slow_key = f"ema_period{self.periods['ema_slow']}"
        self._set_feature_from_result(results, ema_fast_key, 'ema_12', features)
        self._set_feature_from_result(results, ema_slow_key, 'ema_26', features)

        # MACD (multi-column result)
        macd_key = (
            f"macd_fast{self.periods['macd_fast']}_signal{self.periods['macd_signal']}"
            f"_slow{self.periods['macd_slow']}"
        )
        self._extract_macd(results, macd_key, features)

        # ADX (multi-column result)
        adx_key = f"adx_period{self.periods['adx']}"
        self._extract_adx(results, adx_key, features)

        # RSI
        rsi_key = f"rsi_period{self.periods['rsi']}"
        self._set_feature_from_result(results, rsi_key, 'rsi_14', features)

        # Stochastic (multi-column result)
        stoch_key = f"stoch_d3_k{self.periods['stoch']}_smooth_k3"
        self._extract_stoch(results, stoch_key, features)

        # CCI
        cci_key = f"cci_period{self.periods['cci']}"
        self._set_feature_from_result(results, cci_key, 'cci', features)

        # MFI
        mfi_key = f"mfi_period{self.periods['mfi']}"
        self._set_feature_from_result(results, mfi_key, 'mfi', features)

        # Bollinger Bands (multi-column result)
        bb_key = f"bb_period{self.periods['bb']}_std2.0"
        self._extract_bbands(results, bb_key, features)

        # ATR
        atr_key = f"atr_period{self.periods['atr']}"
        self._set_feature_from_result(results, atr_key, 'atr_14', features)

        # CHOP (Choppiness Index)
        chop_key = f"chop_period{self.periods['chop']}"
        self._set_feature_from_result(results, chop_key, 'chop', features)

        # Ichimoku Cloud (multi-column result)
        ichimoku_key = (
            f"ichimoku_kijun{self.periods['ichimoku_kijun']}_"
            f"senkou{self.periods['ichimoku_senkou']}_"
            f"tenkan{self.periods['ichimoku_tenkan']}"
        )
        self._extract_ichimoku(results, ichimoku_key, features)

        return features

    def _set_feature_from_result(
        self,
        results: dict[str, IndicatorResult],
        key: str,
        feature_name: str,
        features: dict[str, float | None],
    ) -> None:
        if key in results:
            features[feature_name] = self._get_last_value(results[key].values)

    def _extract_macd(
        self,
        results: dict[str, IndicatorResult],
        key: str,
        features: dict[str, float | None],
    ) -> None:
        if key not in results:
            return
        macd_result = results[key].values
        if isinstance(macd_result, pd.DataFrame) or isinstance(macd_result, dict):
            features['macd'] = self._get_last_value(macd_result.get('macd'))
            features['macd_signal'] = self._get_last_value(macd_result.get('signal'))
            features['macd_hist'] = self._get_last_value(macd_result.get('histogram'))

    def _extract_adx(
        self,
        results: dict[str, IndicatorResult],
        key: str,
        features: dict[str, float | None],
    ) -> None:
        if key not in results:
            return
        adx_result = results[key].values
        if isinstance(adx_result, pd.DataFrame) or isinstance(adx_result, dict):
            features['adx'] = self._get_last_value(adx_result.get('adx'))
            features['plus_di'] = self._get_last_value(
                adx_result.get('plus_di', adx_result.get('+di'))
            )
            features['minus_di'] = self._get_last_value(
                adx_result.get('minus_di', adx_result.get('-di'))
            )
        elif isinstance(adx_result, pd.Series):
            features['adx'] = self._get_last_value(adx_result)

    def _extract_stoch(
        self,
        results: dict[str, IndicatorResult],
        key: str,
        features: dict[str, float | None],
    ) -> None:
        if key not in results:
            return
        stoch_result = results[key].values
        if isinstance(stoch_result, pd.DataFrame) or isinstance(stoch_result, dict):
            features['stoch_k'] = self._get_last_value(
                stoch_result.get('k', stoch_result.get('%k'))
            )
            features['stoch_d'] = self._get_last_value(
                stoch_result.get('d', stoch_result.get('%d'))
            )

    def _extract_bbands(
        self,
        results: dict[str, IndicatorResult],
        key: str,
        features: dict[str, float | None],
    ) -> None:
        if key not in results:
            return
        bb_result = results[key].values
        if isinstance(bb_result, pd.DataFrame) or isinstance(bb_result, dict):
            features['bb_upper'] = self._get_last_value(bb_result.get('upper'))
            features['bb_middle'] = self._get_last_value(bb_result.get('middle'))
            features['bb_lower'] = self._get_last_value(bb_result.get('lower'))

    def _extract_ichimoku(
        self,
        results: dict[str, IndicatorResult],
        key: str,
        features: dict[str, float | None],
    ) -> None:
        """Extract Ichimoku Cloud indicator values."""
        if key not in results:
            return
        ichimoku_result = results[key].values
        if isinstance(ichimoku_result, pd.DataFrame) or isinstance(ichimoku_result, dict):
            features['ichimoku_tenkan'] = self._get_last_value(
                ichimoku_result.get('tenkan_sen', ichimoku_result.get('tenkan'))
            )
            features['ichimoku_kijun'] = self._get_last_value(
                ichimoku_result.get('kijun_sen', ichimoku_result.get('kijun'))
            )
            features['ichimoku_senkou_a'] = self._get_last_value(
                ichimoku_result.get('senkou_span_a', ichimoku_result.get('senkou_a'))
            )
            features['ichimoku_senkou_b'] = self._get_last_value(
                ichimoku_result.get('senkou_span_b', ichimoku_result.get('senkou_b'))
            )
            features['ichimoku_chikou'] = self._get_last_value(
                ichimoku_result.get('chikou_span', ichimoku_result.get('chikou'))
            )

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
