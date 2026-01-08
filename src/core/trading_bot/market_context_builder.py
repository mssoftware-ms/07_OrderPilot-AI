"""
MarketContext Builder - Baut den kanonischen MarketContext.

Kombiniert:
- Data Preflight Checks
- Indikator-Berechnung
- Regime-Erkennung
- Multi-Timeframe Trend-Analyse
- Support/Resistance Levels (Basis, wird in Phase 2 erweitert)

Erzeugt einen vollständigen MarketContext als Single Source of Truth.

Phase 1.3 der Bot-Integration.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd

from .data_preflight import DataPreflightService, PreflightConfig, PreflightResult
from .market_context import (
    CandleSummary,
    IndicatorSnapshot,
    Level,
    LevelsSnapshot,
    LevelStrength,
    LevelType,
    MarketContext,
    RegimeType,
    TrendDirection,
    create_empty_context,
)

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


# =============================================================================
# BUILDER CONFIG
# =============================================================================


class MarketContextBuilderConfig:
    """Konfiguration für den MarketContext Builder."""

    def __init__(
        self,
        # Preflight
        preflight_enabled: bool = True,
        preflight_config: PreflightConfig | None = None,
        # Indicators
        ema_periods: list[int] | None = None,
        rsi_period: int = 14,
        macd_fast: int = 12,
        macd_slow: int = 26,
        macd_signal: int = 9,
        bb_period: int = 20,
        bb_std: float = 2.0,
        atr_period: int = 14,
        adx_period: int = 14,
        # Regime
        adx_strong_threshold: float = 30.0,
        adx_weak_threshold: float = 20.0,
        volatility_high_atr_pct: float = 3.0,
        volatility_extreme_atr_pct: float = 5.0,
        # Levels
        pivot_lookback: int = 20,
        level_min_touches: int = 2,
        level_zone_atr_mult: float = 0.3,
        top_n_levels: int = 5,
    ):
        self.preflight_enabled = preflight_enabled
        self.preflight_config = preflight_config or PreflightConfig()

        self.ema_periods = ema_periods or [9, 20, 50, 200]
        self.rsi_period = rsi_period
        self.macd_fast = macd_fast
        self.macd_slow = macd_slow
        self.macd_signal = macd_signal
        self.bb_period = bb_period
        self.bb_std = bb_std
        self.atr_period = atr_period
        self.adx_period = adx_period

        self.adx_strong_threshold = adx_strong_threshold
        self.adx_weak_threshold = adx_weak_threshold
        self.volatility_high_atr_pct = volatility_high_atr_pct
        self.volatility_extreme_atr_pct = volatility_extreme_atr_pct

        self.pivot_lookback = pivot_lookback
        self.level_min_touches = level_min_touches
        self.level_zone_atr_mult = level_zone_atr_mult
        self.top_n_levels = top_n_levels


# =============================================================================
# MARKET CONTEXT BUILDER
# =============================================================================


class MarketContextBuilder:
    """
    Baut MarketContext aus Rohdaten.

    Usage:
        builder = MarketContextBuilder()
        context = builder.build(df, symbol="BTCUSD", timeframe="5m")

        # Oder async mit Multi-Timeframe:
        context = await builder.build_multi_timeframe(
            data_provider,
            symbol="BTCUSD",
            timeframes=["5m", "1h", "4h", "1d"]
        )
    """

    def __init__(self, config: MarketContextBuilderConfig | None = None):
        self.config = config or MarketContextBuilderConfig()
        self._preflight_service = DataPreflightService(self.config.preflight_config)
        self._use_talib = self._check_talib_available()

    @staticmethod
    def _check_talib_available() -> bool:
        """Prüft ob TA-Lib verfügbar ist."""
        try:
            import talib  # noqa: F401

            return True
        except ImportError:
            logger.warning("TA-Lib not available, using pandas fallback")
            return False

    def build(
        self,
        df: pd.DataFrame | None,
        symbol: str,
        timeframe: str = "5m",
        skip_preflight: bool = False,
    ) -> MarketContext:
        """
        Baut MarketContext aus einem DataFrame.

        Args:
            df: DataFrame mit OHLCV-Daten
            symbol: Trading-Symbol
            timeframe: Timeframe der Daten
            skip_preflight: Preflight-Checks überspringen

        Returns:
            Vollständiger MarketContext
        """
        timestamp = datetime.now(timezone.utc)

        # 1. Preflight Check
        if not skip_preflight and self.config.preflight_enabled:
            preflight_result = self._preflight_service.run_preflight(
                df, symbol, timeframe
            )

            if not preflight_result.is_tradeable:
                logger.warning(
                    f"Preflight failed for {symbol}/{timeframe}: "
                    f"{[i.message for i in preflight_result.critical_issues]}"
                )
                return self._create_failed_context(
                    symbol, timeframe, preflight_result, timestamp
                )

            # Use cleaned data if available
            if preflight_result.cleaned_df is not None:
                df = preflight_result.cleaned_df
        else:
            preflight_result = None

        # 2. Validate DataFrame
        if df is None or df.empty:
            return create_empty_context(symbol, timeframe)

        # 3. Calculate Indicators
        df = self._calculate_indicators(df)

        # 4. Extract Current Values
        current = df.iloc[-1]
        current_price = float(current.get("close", 0))

        # 5. Detect Regime
        regime, regime_confidence, regime_reason = self._detect_regime(df)

        # 6. Detect Trend
        trend_5m = self._detect_trend(df)

        # 7. Create Indicator Snapshot
        indicators_5m = self._create_indicator_snapshot(df, timeframe)

        # 8. Detect Levels (Basic - will be enhanced in Phase 2)
        levels = self._detect_levels(df, symbol, current_price, timeframe)

        # 9. Calculate Volatility State
        atr_pct = self._calculate_atr_percent(df)
        volatility_state = self._determine_volatility_state(atr_pct)

        # 10. Create Candle Summary
        current_candle = self._create_candle_summary(df, timeframe)

        # 11. Calculate MTF Alignment (single timeframe = just 5m)
        mtf_alignment_score = self._trend_to_score(trend_5m)

        # 12. Build Context
        context = MarketContext(
            symbol=symbol,
            timeframe=timeframe,
            timestamp=timestamp,
            # Regime
            regime=regime,
            regime_confidence=regime_confidence,
            regime_reason=regime_reason,
            # Trends (single timeframe)
            trend_5m=trend_5m,
            mtf_alignment_score=mtf_alignment_score,
            mtf_aligned=True,  # Single TF is always "aligned"
            # Indicators
            indicators_5m=indicators_5m,
            # Levels
            levels=levels,
            nearest_support=levels.nearest_support.midpoint if levels.nearest_support else None,
            nearest_resistance=levels.nearest_resistance.midpoint if levels.nearest_resistance else None,
            distance_to_support_pct=self._calc_distance_pct(
                current_price, levels.nearest_support.midpoint if levels.nearest_support else None
            ),
            distance_to_resistance_pct=self._calc_distance_pct(
                current_price, levels.nearest_resistance.midpoint if levels.nearest_resistance else None
            ),
            # Price & Volatility
            current_price=current_price,
            atr_pct=atr_pct,
            volatility_state=volatility_state,
            # Candle
            current_candle=current_candle,
            # Data Quality
            data_fresh=preflight_result.status.value != "FAILED" if preflight_result else True,
            data_freshness_seconds=preflight_result.data_freshness_seconds if preflight_result else 0,
            data_quality_issues=[i.message for i in preflight_result.warning_issues] if preflight_result else [],
        )

        logger.debug(
            f"Built MarketContext for {symbol}/{timeframe}: "
            f"regime={regime.value}, price={current_price:.2f}"
        )

        return context

    def build_with_multi_timeframe(
        self,
        dataframes: dict[str, pd.DataFrame],
        symbol: str,
        primary_timeframe: str = "5m",
    ) -> MarketContext:
        """
        Baut MarketContext mit Multi-Timeframe Daten.

        Args:
            dataframes: Dict von timeframe -> DataFrame
            symbol: Trading-Symbol
            primary_timeframe: Primärer Timeframe

        Returns:
            MarketContext mit MTF Trends
        """
        if primary_timeframe not in dataframes:
            logger.error(f"Primary timeframe {primary_timeframe} not in dataframes")
            return create_empty_context(symbol, primary_timeframe)

        # Build base context from primary timeframe
        context = self.build(
            dataframes[primary_timeframe],
            symbol,
            primary_timeframe,
        )

        # Add MTF trends
        trends = {}
        for tf, df in dataframes.items():
            if df is not None and not df.empty:
                df_with_indicators = self._calculate_indicators(df.copy())
                trends[tf] = self._detect_trend(df_with_indicators)

        # Update context with MTF data
        context.trend_1d = trends.get("1d") or trends.get("1D")
        context.trend_4h = trends.get("4h") or trends.get("4H")
        context.trend_1h = trends.get("1h") or trends.get("1H")
        context.trend_15m = trends.get("15m") or trends.get("15M")
        context.trend_5m = trends.get("5m") or trends.get("5M") or context.trend_5m

        # Calculate MTF alignment
        context.mtf_alignment_score = self._calculate_mtf_alignment(trends)
        context.mtf_aligned = abs(context.mtf_alignment_score) > 0.6

        # Add additional indicator snapshots
        if "1h" in dataframes and dataframes["1h"] is not None:
            df_1h = self._calculate_indicators(dataframes["1h"].copy())
            context.indicators_1h = self._create_indicator_snapshot(df_1h, "1h")

        if "4h" in dataframes and dataframes["4h"] is not None:
            df_4h = self._calculate_indicators(dataframes["4h"].copy())
            context.indicators_4h = self._create_indicator_snapshot(df_4h, "4h")

        if "1d" in dataframes and dataframes["1d"] is not None:
            df_1d = self._calculate_indicators(dataframes["1d"].copy())
            context.indicators_1d = self._create_indicator_snapshot(df_1d, "1d")

        # Regenerate context ID (changed data)
        context.context_id = context._generate_context_id()

        return context

    # =========================================================================
    # INDICATOR CALCULATION
    # =========================================================================

    def _calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Berechnet alle technischen Indikatoren.

        Verwendet TA-Lib wenn verfügbar, sonst Pandas-Fallback.
        """
        if df.empty:
            return df

        df = df.copy()

        if self._use_talib:
            df = self._calculate_indicators_talib(df)
        else:
            df = self._calculate_indicators_pandas(df)

        # Calculate derived fields
        df = self._calculate_derived_fields(df)

        return df

    def _calculate_indicators_talib(self, df: pd.DataFrame) -> pd.DataFrame:
        """Berechnet Indikatoren mit TA-Lib."""
        import talib

        close = df["close"].values
        high = df["high"].values
        low = df["low"].values

        # EMAs
        for period in self.config.ema_periods:
            df[f"ema_{period}"] = talib.EMA(close, timeperiod=period)

        # RSI
        df["rsi_14"] = talib.RSI(close, timeperiod=self.config.rsi_period)

        # MACD
        macd, macd_signal, macd_hist = talib.MACD(
            close,
            fastperiod=self.config.macd_fast,
            slowperiod=self.config.macd_slow,
            signalperiod=self.config.macd_signal,
        )
        df["macd_line"] = macd
        df["macd_signal"] = macd_signal
        df["macd_histogram"] = macd_hist

        # Bollinger Bands
        upper, middle, lower = talib.BBANDS(
            close,
            timeperiod=self.config.bb_period,
            nbdevup=self.config.bb_std,
            nbdevdn=self.config.bb_std,
        )
        df["bb_upper"] = upper
        df["bb_middle"] = middle
        df["bb_lower"] = lower

        # ATR
        df["atr_14"] = talib.ATR(high, low, close, timeperiod=self.config.atr_period)

        # ADX
        df["adx_14"] = talib.ADX(high, low, close, timeperiod=self.config.adx_period)
        df["plus_di"] = talib.PLUS_DI(high, low, close, timeperiod=self.config.adx_period)
        df["minus_di"] = talib.MINUS_DI(high, low, close, timeperiod=self.config.adx_period)

        # Stochastic
        slowk, slowd = talib.STOCH(high, low, close)
        df["stoch_k"] = slowk
        df["stoch_d"] = slowd

        # Volume SMA
        if "volume" in df.columns:
            df["volume_sma_20"] = talib.SMA(df["volume"].values, timeperiod=20)

        return df

    def _calculate_indicators_pandas(self, df: pd.DataFrame) -> pd.DataFrame:
        """Berechnet Indikatoren mit Pandas (Fallback)."""
        close = df["close"]
        high = df["high"]
        low = df["low"]

        # EMAs
        for period in self.config.ema_periods:
            df[f"ema_{period}"] = close.ewm(span=period, adjust=False).mean()

        # RSI
        delta = close.diff()
        gain = delta.where(delta > 0, 0).rolling(window=self.config.rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.config.rsi_period).mean()
        rs = gain / loss.replace(0, 1)
        df["rsi_14"] = 100 - (100 / (1 + rs))

        # MACD
        ema_fast = close.ewm(span=self.config.macd_fast, adjust=False).mean()
        ema_slow = close.ewm(span=self.config.macd_slow, adjust=False).mean()
        df["macd_line"] = ema_fast - ema_slow
        df["macd_signal"] = df["macd_line"].ewm(span=self.config.macd_signal, adjust=False).mean()
        df["macd_histogram"] = df["macd_line"] - df["macd_signal"]

        # Bollinger Bands
        sma = close.rolling(window=self.config.bb_period).mean()
        std = close.rolling(window=self.config.bb_period).std()
        df["bb_upper"] = sma + (std * self.config.bb_std)
        df["bb_middle"] = sma
        df["bb_lower"] = sma - (std * self.config.bb_std)

        # ATR (simplified)
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        df["atr_14"] = tr.rolling(window=self.config.atr_period).mean()

        # ADX (simplified)
        plus_dm = high.diff()
        minus_dm = -low.diff()
        plus_dm = plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0)
        minus_dm = minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0)

        atr = df["atr_14"]
        plus_di = 100 * (plus_dm.rolling(self.config.adx_period).mean() / atr.replace(0, 1))
        minus_di = 100 * (minus_dm.rolling(self.config.adx_period).mean() / atr.replace(0, 1))
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di).replace(0, 1)
        df["adx_14"] = dx.rolling(self.config.adx_period).mean()
        df["plus_di"] = plus_di
        df["minus_di"] = minus_di

        # Volume SMA
        if "volume" in df.columns:
            df["volume_sma_20"] = df["volume"].rolling(window=20).mean()

        return df

    def _calculate_derived_fields(self, df: pd.DataFrame) -> pd.DataFrame:
        """Berechnet abgeleitete Felder."""
        close = df["close"]

        # EMA Distance %
        if "ema_20" in df.columns:
            df["ema_20_distance_pct"] = ((close - df["ema_20"]) / df["ema_20"]) * 100

        if "ema_50" in df.columns:
            df["ema_50_distance_pct"] = ((close - df["ema_50"]) / df["ema_50"]) * 100

        # Bollinger %B
        if all(col in df.columns for col in ["bb_upper", "bb_lower"]):
            bb_range = df["bb_upper"] - df["bb_lower"]
            df["bb_pct_b"] = (close - df["bb_lower"]) / bb_range.replace(0, 1)
            df["bb_width"] = bb_range / df["bb_middle"].replace(0, 1)

        # ATR Percent
        if "atr_14" in df.columns:
            df["atr_percent"] = (df["atr_14"] / close) * 100

        # Volume Ratio
        if "volume" in df.columns and "volume_sma_20" in df.columns:
            df["volume_ratio"] = df["volume"] / df["volume_sma_20"].replace(0, 1)

        return df

    # =========================================================================
    # REGIME DETECTION
    # =========================================================================

    def _detect_regime(
        self, df: pd.DataFrame
    ) -> tuple[RegimeType, float, str]:
        """
        Erkennt das Marktregime.

        Returns:
            Tuple von (RegimeType, confidence, reason)
        """
        if df.empty:
            return RegimeType.NEUTRAL, 0.0, "No data"

        current = df.iloc[-1]

        ema20 = current.get("ema_20")
        ema50 = current.get("ema_50")
        adx = current.get("adx_14")
        atr_pct = current.get("atr_percent")

        # Check for explosive volatility first
        if atr_pct and atr_pct > self.config.volatility_extreme_atr_pct:
            return (
                RegimeType.VOLATILITY_EXPLOSIVE,
                0.9,
                f"ATR% = {atr_pct:.2f}% > {self.config.volatility_extreme_atr_pct}%",
            )

        # Need EMAs for trend detection
        if not all([ema20, ema50]):
            return RegimeType.NEUTRAL, 0.3, "Missing EMA data"

        reasons = []
        confidence = 0.5

        # Trend Direction
        if ema20 > ema50:
            direction = "BULL"
            reasons.append(f"EMA20 ({ema20:.2f}) > EMA50 ({ema50:.2f})")
        elif ema20 < ema50:
            direction = "BEAR"
            reasons.append(f"EMA20 ({ema20:.2f}) < EMA50 ({ema50:.2f})")
        else:
            direction = "RANGE"
            reasons.append("EMA20 ≈ EMA50")

        # Trend Strength (ADX)
        if adx:
            if adx > self.config.adx_strong_threshold:
                strength = "STRONG"
                confidence += 0.3
                reasons.append(f"ADX ({adx:.1f}) > {self.config.adx_strong_threshold}")
            elif adx > self.config.adx_weak_threshold:
                strength = "WEAK"
                confidence += 0.1
                reasons.append(f"ADX ({adx:.1f}) > {self.config.adx_weak_threshold}")
            else:
                strength = "CHOP"
                confidence -= 0.1
                reasons.append(f"ADX ({adx:.1f}) < {self.config.adx_weak_threshold}")
        else:
            strength = "UNKNOWN"

        # Determine Regime
        if direction == "BULL":
            if strength == "STRONG":
                regime = RegimeType.STRONG_TREND_BULL
            else:
                regime = RegimeType.WEAK_TREND_BULL
        elif direction == "BEAR":
            if strength == "STRONG":
                regime = RegimeType.STRONG_TREND_BEAR
            else:
                regime = RegimeType.WEAK_TREND_BEAR
        else:
            regime = RegimeType.CHOP_RANGE

        # Override to CHOP if ADX very low
        if adx and adx < self.config.adx_weak_threshold:
            regime = RegimeType.CHOP_RANGE
            confidence = max(0.3, confidence - 0.2)

        return regime, min(1.0, max(0.0, confidence)), "; ".join(reasons)

    def _detect_trend(self, df: pd.DataFrame) -> TrendDirection:
        """Erkennt Trend-Richtung aus EMAs."""
        if df.empty:
            return TrendDirection.NEUTRAL

        current = df.iloc[-1]
        ema20 = current.get("ema_20")
        ema50 = current.get("ema_50")

        if ema20 and ema50:
            if ema20 > ema50:
                return TrendDirection.BULLISH
            elif ema20 < ema50:
                return TrendDirection.BEARISH

        return TrendDirection.NEUTRAL

    def _calculate_mtf_alignment(self, trends: dict[str, TrendDirection]) -> float:
        """
        Berechnet Multi-Timeframe Alignment Score.

        Returns:
            Score von -1 (alle bearish) bis +1 (alle bullish)
        """
        if not trends:
            return 0.0

        scores = [self._trend_to_score(t) for t in trends.values()]
        return sum(scores) / len(scores)

    @staticmethod
    def _trend_to_score(trend: TrendDirection | None) -> float:
        """Konvertiert Trend zu Score."""
        if trend == TrendDirection.BULLISH:
            return 1.0
        elif trend == TrendDirection.BEARISH:
            return -1.0
        return 0.0

    # =========================================================================
    # LEVEL DETECTION (Basic - Phase 2 will enhance)
    # =========================================================================

    def _detect_levels(
        self,
        df: pd.DataFrame,
        symbol: str,
        current_price: float,
        timeframe: str,
    ) -> LevelsSnapshot:
        """
        Erkennt Support/Resistance Levels.

        Basis-Implementierung mit Pivot Points.
        Wird in Phase 2 durch LevelEngine v2 ersetzt.
        """
        timestamp = datetime.now(timezone.utc)

        if df.empty or current_price <= 0:
            return LevelsSnapshot(
                timestamp=timestamp,
                symbol=symbol,
                current_price=current_price,
            )

        supports = []
        resistances = []

        # Get ATR for zone width
        atr = df["atr_14"].iloc[-1] if "atr_14" in df.columns else current_price * 0.01
        zone_width = atr * self.config.level_zone_atr_mult

        # Find Swing Highs/Lows
        lookback = self.config.pivot_lookback
        highs = df["high"].values
        lows = df["low"].values

        for i in range(lookback, len(df) - lookback):
            # Swing High
            if highs[i] == max(highs[i - lookback : i + lookback + 1]):
                level = Level(
                    level_id=f"swing_high_{i}",
                    level_type=LevelType.SWING_HIGH,
                    price_low=highs[i] - zone_width,
                    price_high=highs[i] + zone_width,
                    strength=LevelStrength.MODERATE,
                    touches=1,
                    timeframe=timeframe,
                    method="swing",
                )
                if highs[i] > current_price:
                    resistances.append(level)
                else:
                    supports.append(level)

            # Swing Low
            if lows[i] == min(lows[i - lookback : i + lookback + 1]):
                level = Level(
                    level_id=f"swing_low_{i}",
                    level_type=LevelType.SWING_LOW,
                    price_low=lows[i] - zone_width,
                    price_high=lows[i] + zone_width,
                    strength=LevelStrength.MODERATE,
                    touches=1,
                    timeframe=timeframe,
                    method="swing",
                )
                if lows[i] < current_price:
                    supports.append(level)
                else:
                    resistances.append(level)

        # Add EMA levels
        for ema_col in ["ema_20", "ema_50", "ema_200"]:
            if ema_col in df.columns:
                ema_value = df[ema_col].iloc[-1]
                if pd.notna(ema_value):
                    level_type = LevelType.EMA_SUPPORT if ema_value < current_price else LevelType.EMA_RESISTANCE
                    level = Level(
                        level_id=f"{ema_col}_level",
                        level_type=level_type,
                        price_low=ema_value - zone_width * 0.5,
                        price_high=ema_value + zone_width * 0.5,
                        strength=LevelStrength.MODERATE,
                        timeframe=timeframe,
                        method="ema",
                        label=ema_col.upper(),
                    )
                    if ema_value < current_price:
                        supports.append(level)
                    else:
                        resistances.append(level)

        # Sort by distance to current price
        supports.sort(key=lambda l: current_price - l.midpoint)
        resistances.sort(key=lambda l: l.midpoint - current_price)

        # Calculate distance from price
        for level in supports + resistances:
            level.distance_from_price_pct = abs(
                (level.midpoint - current_price) / current_price * 100
            )

        # Get top N
        key_supports = supports[: self.config.top_n_levels]
        key_resistances = resistances[: self.config.top_n_levels]

        return LevelsSnapshot(
            timestamp=timestamp,
            symbol=symbol,
            current_price=current_price,
            support_levels=supports,
            resistance_levels=resistances,
            key_supports=key_supports,
            key_resistances=key_resistances,
            nearest_support=supports[0] if supports else None,
            nearest_resistance=resistances[0] if resistances else None,
        )

    # =========================================================================
    # HELPER METHODS
    # =========================================================================

    def _calculate_atr_percent(self, df: pd.DataFrame) -> float:
        """Berechnet ATR als Prozent vom Preis."""
        if df.empty or "atr_14" not in df.columns:
            return 0.0

        current = df.iloc[-1]
        atr = current.get("atr_14", 0)
        close = current.get("close", 1)

        if close > 0:
            return (atr / close) * 100
        return 0.0

    def _determine_volatility_state(self, atr_pct: float) -> str:
        """Bestimmt Volatilitäts-Zustand."""
        if atr_pct >= self.config.volatility_extreme_atr_pct:
            return "EXTREME"
        elif atr_pct >= self.config.volatility_high_atr_pct:
            return "HIGH"
        elif atr_pct < 1.0:
            return "LOW"
        return "NORMAL"

    def _create_indicator_snapshot(
        self, df: pd.DataFrame, timeframe: str
    ) -> IndicatorSnapshot | None:
        """Erstellt IndicatorSnapshot aus DataFrame."""
        if df.empty:
            return None

        current = df.iloc[-1]
        timestamp = (
            current.name
            if hasattr(current.name, "isoformat")
            else datetime.now(timezone.utc)
        )

        # RSI State
        rsi = current.get("rsi_14")
        rsi_state = None
        if rsi is not None:
            if rsi > 70:
                rsi_state = "OVERBOUGHT"
            elif rsi < 30:
                rsi_state = "OVERSOLD"
            else:
                rsi_state = "NEUTRAL"

        # MACD Crossover
        macd_line = current.get("macd_line")
        macd_signal = current.get("macd_signal")
        macd_crossover = None
        if macd_line is not None and macd_signal is not None:
            if macd_line > macd_signal:
                macd_crossover = "BULLISH"
            elif macd_line < macd_signal:
                macd_crossover = "BEARISH"
            else:
                macd_crossover = "NONE"

        # Volume State
        volume_ratio = current.get("volume_ratio")
        volume_state = None
        if volume_ratio is not None:
            if volume_ratio > 2.0:
                volume_state = "HIGH"
            elif volume_ratio < 0.5:
                volume_state = "LOW"
            else:
                volume_state = "NORMAL"

        # Volatility State
        atr_pct = current.get("atr_percent")
        volatility_state = self._determine_volatility_state(atr_pct) if atr_pct else "NORMAL"

        return IndicatorSnapshot(
            timestamp=timestamp,
            timeframe=timeframe,
            ema_9=current.get("ema_9"),
            ema_20=current.get("ema_20"),
            ema_50=current.get("ema_50"),
            ema_200=current.get("ema_200"),
            ema_20_distance_pct=current.get("ema_20_distance_pct"),
            ema_50_distance_pct=current.get("ema_50_distance_pct"),
            rsi_14=rsi,
            rsi_state=rsi_state,
            macd_line=macd_line,
            macd_signal=macd_signal,
            macd_histogram=current.get("macd_histogram"),
            macd_crossover=macd_crossover,
            stoch_k=current.get("stoch_k"),
            stoch_d=current.get("stoch_d"),
            bb_upper=current.get("bb_upper"),
            bb_middle=current.get("bb_middle"),
            bb_lower=current.get("bb_lower"),
            bb_pct_b=current.get("bb_pct_b"),
            bb_width=current.get("bb_width"),
            atr_14=current.get("atr_14"),
            atr_percent=atr_pct,
            volatility_state=volatility_state,
            adx_14=current.get("adx_14"),
            plus_di=current.get("plus_di"),
            minus_di=current.get("minus_di"),
            volume=current.get("volume"),
            volume_sma_20=current.get("volume_sma_20"),
            volume_ratio=volume_ratio,
            volume_state=volume_state,
            current_price=current.get("close"),
        )

    def _create_candle_summary(
        self, df: pd.DataFrame, timeframe: str
    ) -> CandleSummary | None:
        """Erstellt CandleSummary für aktuelle Candle."""
        if df.empty:
            return None

        current = df.iloc[-1]
        timestamp = (
            current.name
            if hasattr(current.name, "isoformat")
            else datetime.now(timezone.utc)
        )

        return CandleSummary(
            timestamp=timestamp,
            timeframe=timeframe,
            open=float(current.get("open", 0)),
            high=float(current.get("high", 0)),
            low=float(current.get("low", 0)),
            close=float(current.get("close", 0)),
            volume=float(current.get("volume", 0)),
        )

    def _create_failed_context(
        self,
        symbol: str,
        timeframe: str,
        preflight_result: PreflightResult,
        timestamp: datetime,
    ) -> MarketContext:
        """Erstellt Context für fehlgeschlagenen Preflight."""
        return MarketContext(
            symbol=symbol,
            timeframe=timeframe,
            timestamp=timestamp,
            regime=RegimeType.NEUTRAL,
            data_fresh=False,
            data_freshness_seconds=preflight_result.data_freshness_seconds,
            data_quality_issues=[i.message for i in preflight_result.issues],
        )

    @staticmethod
    def _calc_distance_pct(
        current_price: float, level_price: float | None
    ) -> float | None:
        """Berechnet Distanz in Prozent."""
        if level_price is None or current_price <= 0:
            return None
        return abs((level_price - current_price) / current_price * 100)


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================


def build_market_context(
    df: pd.DataFrame | None,
    symbol: str,
    timeframe: str = "5m",
    config: MarketContextBuilderConfig | None = None,
) -> MarketContext:
    """
    Convenience-Funktion zum Erstellen eines MarketContext.

    Usage:
        context = build_market_context(df, "BTCUSD", "5m")
    """
    builder = MarketContextBuilder(config)
    return builder.build(df, symbol, timeframe)
