"""
MarketContext Builder - Baut den kanonischen MarketContext.

Kombiniert:
- Data Preflight Checks
- Indikator-Berechnung (via IndicatorCalculator)
- Regime-Erkennung (via RegimeDetector)
- Multi-Timeframe Trend-Analyse
- Support/Resistance Levels (via LevelDetector)

Erzeugt einen vollständigen MarketContext als Single Source of Truth.

Phase 1.3 der Bot-Integration.
Module 4/4 of market_context_builder.py split - Main orchestrator.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING

import pandas as pd

from .data_preflight import DataPreflightService, PreflightResult
from .market_context import (
    CandleSummary,
    IndicatorSnapshot,
    MarketContext,
    RegimeType,
    TrendDirection,
    create_empty_context,
)
from .market_context_config import MarketContextBuilderConfig
from .indicator_calculator import IndicatorCalculator
from .market_context_detectors import RegimeDetector, LevelDetector

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


# MARKET CONTEXT BUILDER
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

        # Helper classes
        self._indicator_calculator = IndicatorCalculator(self.config)
        self._regime_detector = RegimeDetector(self.config)
        self._level_detector = LevelDetector(self.config)

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

        # 3. Calculate Indicators (delegated)
        df = self._indicator_calculator.calculate_indicators(df)

        # 4. Extract Current Values
        current = df.iloc[-1]
        current_price = float(current.get("close", 0))

        # 5. Detect Regime (delegated)
        regime, regime_confidence, regime_reason = self._regime_detector.detect_regime(df)

        # 6. Detect Trend (delegated)
        trend_5m = self._regime_detector.detect_trend(df)

        # 7. Create Indicator Snapshot
        indicators_5m = self._create_indicator_snapshot(df, timeframe)

        # 8. Detect Levels (delegated)
        levels = self._level_detector.detect_levels(df, symbol, current_price, timeframe)

        # 9. Calculate Volatility State (delegated)
        atr_pct = self._calculate_atr_percent(df)
        volatility_state = self._regime_detector.determine_volatility_state(atr_pct)

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

        # Add MTF trends (delegated)
        trends = {}
        for tf, df in dataframes.items():
            if df is not None and not df.empty:
                df_with_indicators = self._indicator_calculator.calculate_indicators(df.copy())
                trends[tf] = self._regime_detector.detect_trend(df_with_indicators)

        # Update context with MTF data
        context.trend_1d = trends.get("1d") or trends.get("1D")
        context.trend_4h = trends.get("4h") or trends.get("4H")
        context.trend_1h = trends.get("1h") or trends.get("1H")
        context.trend_15m = trends.get("15m") or trends.get("15M")
        context.trend_5m = trends.get("5m") or trends.get("5M") or context.trend_5m

        # Calculate MTF alignment (delegated)
        context.mtf_alignment_score = self._regime_detector.calculate_mtf_alignment(trends)
        context.mtf_aligned = abs(context.mtf_alignment_score) > 0.6

        # Add additional indicator snapshots (delegated)
        if "1h" in dataframes and dataframes["1h"] is not None:
            df_1h = self._indicator_calculator.calculate_indicators(dataframes["1h"].copy())
            context.indicators_1h = self._create_indicator_snapshot(df_1h, "1h")

        if "4h" in dataframes and dataframes["4h"] is not None:
            df_4h = self._indicator_calculator.calculate_indicators(dataframes["4h"].copy())
            context.indicators_4h = self._create_indicator_snapshot(df_4h, "4h")

        if "1d" in dataframes and dataframes["1d"] is not None:
            df_1d = self._indicator_calculator.calculate_indicators(dataframes["1d"].copy())
            context.indicators_1d = self._create_indicator_snapshot(df_1d, "1d")

        # Regenerate context ID (changed data)
        context.context_id = context._generate_context_id()

        return context

    # =========================================================================
    # HELPER METHODS
    # =========================================================================

    @staticmethod
    def _trend_to_score(trend: TrendDirection | None) -> float:
        """Konvertiert Trend zu Score."""
        if trend == TrendDirection.BULLISH:
            return 1.0
        elif trend == TrendDirection.BEARISH:
            return -1.0
        return 0.0

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
        volatility_state = self._regime_detector.determine_volatility_state(atr_pct) if atr_pct else "NORMAL"

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


# CONVENIENCE FUNCTIONS
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
