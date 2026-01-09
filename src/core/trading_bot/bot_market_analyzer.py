"""
Bot Market Analyzer - Market Data and Analysis Methods

Handles market data fetching and technical analysis:
- Chart data interface (set/clear/has_chart_data)
- Market data fetching with chart prioritization
- Indicator calculation (EMA, RSI, MACD, ATR, Bollinger Bands)
- Regime detection (Trending/Choppy)
- Market context extraction (trend, volatility, momentum)

Module 2/4 of bot_engine.py split (Lines 252-899)
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pandas as pd
import pandas_ta as ta  # type: ignore

if TYPE_CHECKING:
    from .trade_logger import MarketContext

logger = logging.getLogger(__name__)


class BotMarketAnalyzer:
    """
    Verwaltet Marktdaten-Fetching und technische Analyse.

    Wird von TradingBotEngine als Helper verwendet um Marktdaten zu holen,
    Indikatoren zu berechnen und das Regime zu erkennen.
    """

    def __init__(self, parent_engine: "TradingBotEngine"):
        """
        Args:
            parent_engine: Referenz zur TradingBotEngine
        """
        self.engine = parent_engine

        # Chart Data (von UI übergeben - vermeidet doppeltes Laden!)
        self._chart_data: pd.DataFrame | None = None
        self._chart_symbol: str | None = None
        self._chart_timeframe: str | None = None

    # =========================================================================
    # CHART DATA INTERFACE
    # =========================================================================

    def set_chart_data(
        self,
        data: pd.DataFrame,
        symbol: str,
        timeframe: str,
    ) -> None:
        """
        Setzt Chart-Daten für die Analyse.

        Wird vom UI aufgerufen wenn Chart-Daten geladen werden.
        Der Bot verwendet diese Daten anstatt eigene zu laden.

        Args:
            data: DataFrame mit OHLCV-Daten und Indikatoren
            symbol: Symbol (z.B. 'BTCUSDT')
            timeframe: Timeframe (z.B. '5m', '1H')
        """
        if data is None or data.empty:
            logger.warning("set_chart_data: Empty data received, ignoring")
            return

        self._chart_data = data.copy()  # Kopie um Änderungen zu vermeiden
        self._chart_symbol = symbol
        self._chart_timeframe = timeframe

        self.engine._log(
            f"Chart-Daten erhalten: {symbol} {timeframe}, "
            f"{len(data)} Bars"
        )
        logger.info(
            f"BotMarketAnalyzer: Chart data set - {symbol} {timeframe}, "
            f"{len(data)} bars, columns: {list(data.columns)}"
        )

    def clear_chart_data(self) -> None:
        """Löscht die Chart-Daten (z.B. bei Symbol-Wechsel)."""
        self._chart_data = None
        self._chart_symbol = None
        self._chart_timeframe = None
        logger.debug("BotMarketAnalyzer: Chart data cleared")

    @property
    def has_chart_data(self) -> bool:
        """Sind Chart-Daten verfügbar?"""
        return (
            self._chart_data is not None
            and not self._chart_data.empty
        )

    # =========================================================================
    # MARKET DATA FETCHING
    # =========================================================================

    async def fetch_market_data(self) -> pd.DataFrame | None:
        """
        Holt Marktdaten mit Indikatoren.

        Priorisierung:
        1. Chart-Daten (falls verfügbar und Symbol passt) - kein API-Call!
        2. Fallback: API via HistoryManager/Adapter

        Returns:
            DataFrame mit OHLCV + Indikatoren oder None
        """
        try:
            # === OPTION 1: Chart-Daten verwenden (bevorzugt) ===
            if self.has_chart_data:
                chart_symbol = (self._chart_symbol or "").upper()
                config_symbol = self.engine.config.symbol.upper()

                if chart_symbol == config_symbol:
                    logger.debug(
                        f"Using chart data: {chart_symbol} "
                        f"({len(self._chart_data)} bars)"
                    )
                    # Chart-Daten haben normalerweise bereits Indikatoren
                    return self._chart_data.copy()
                else:
                    logger.warning(
                        f"Chart symbol mismatch: {chart_symbol} != {config_symbol}, "
                        f"falling back to API"
                    )

            # === OPTION 2: API Fallback ===
            # Hier würde man normalerweise HistoryManager verwenden
            # Vorerst: nicht implementiert, da Chart-Daten Priorität haben
            logger.warning("No chart data available and API fallback not implemented")
            return None

        except Exception as e:
            logger.error(f"Failed to fetch market data: {e}")
            return None

    # =========================================================================
    # INDICATOR CALCULATION
    # =========================================================================

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Berechnet technische Indikatoren.

        Args:
            df: DataFrame mit OHLCV-Daten

        Returns:
            DataFrame mit berechneten Indikatoren
        """
        if df.empty or len(df) < 200:
            logger.warning("Not enough data for indicators (need 200+ bars)")
            return df

        try:
            df = df.copy()

            # EMAs (Trend)
            df["ema_20"] = ta.ema(df["close"], length=20)
            df["ema_50"] = ta.ema(df["close"], length=50)
            df["ema_200"] = ta.ema(df["close"], length=200)

            # RSI (Momentum)
            df["rsi_14"] = ta.rsi(df["close"], length=14)

            # MACD (Momentum)
            macd = ta.macd(df["close"], fast=12, slow=26, signal=9)
            if macd is not None:
                df["macd"] = macd["MACD_12_26_9"]
                df["macd_signal"] = macd["MACDs_12_26_9"]
                df["macd_histogram"] = macd["MACDh_12_26_9"]

            # ATR (Volatility)
            df["atr_14"] = ta.atr(df["high"], df["low"], df["close"], length=14)

            # Bollinger Bands (Volatility)
            bbands = ta.bbands(df["close"], length=20, std=2)
            if bbands is not None:
                df["bb_upper"] = bbands["BBU_20_2.0"]
                df["bb_middle"] = bbands["BBM_20_2.0"]
                df["bb_lower"] = bbands["BBL_20_2.0"]

            # Volume SMA (Volume confirmation)
            df["volume_sma_20"] = ta.sma(df["volume"], length=20)

            logger.debug("Indicators calculated successfully")
            return df

        except Exception as e:
            logger.error(f"Failed to calculate indicators: {e}")
            return df

    # =========================================================================
    # REGIME DETECTION
    # =========================================================================

    def detect_regime(self, df: pd.DataFrame) -> str:
        """
        Erkennt Markt-Regime (Trending/Choppy).

        Args:
            df: DataFrame mit Indikatoren

        Returns:
            Regime string ("trending_up", "trending_down", "choppy")
        """
        if df.empty or len(df) < 50:
            return "unknown"

        try:
            current = df.iloc[-1]

            # EMA-Stack prüfen
            ema_20 = current.get("ema_20")
            ema_50 = current.get("ema_50")
            ema_200 = current.get("ema_200")

            if pd.isna(ema_20) or pd.isna(ema_50) or pd.isna(ema_200):
                return "unknown"

            # Trending Up: EMA_20 > EMA_50 > EMA_200
            if ema_20 > ema_50 > ema_200:
                return "trending_up"

            # Trending Down: EMA_20 < EMA_50 < EMA_200
            if ema_20 < ema_50 < ema_200:
                return "trending_down"

            # Choppy: EMAs sind nicht klar geordnet
            return "choppy"

        except Exception as e:
            logger.error(f"Failed to detect regime: {e}")
            return "unknown"

    # =========================================================================
    # MARKET CONTEXT
    # =========================================================================

    def extract_market_context(
        self,
        df: pd.DataFrame,
        regime: str,
    ) -> "MarketContext":
        """
        Extrahiert Markt-Kontext für Trade Logging.

        Args:
            df: DataFrame mit Indikatoren
            regime: Erkanntes Regime

        Returns:
            MarketContext object
        """
        from .trade_logger import MarketContext

        trend = self._get_trend_from_ema(df)
        return MarketContext(
            regime=regime,
            trend=trend,
            volatility=self._get_volatility_level(df),
            momentum=self._get_momentum_direction(df),
        )

    def _get_trend_from_ema(self, df: pd.DataFrame) -> str:
        """Ermittelt Trend aus EMA-Stack."""
        if df.empty:
            return "unknown"

        current = df.iloc[-1]
        ema_20 = current.get("ema_20")
        ema_50 = current.get("ema_50")

        if pd.isna(ema_20) or pd.isna(ema_50):
            return "neutral"

        if ema_20 > ema_50:
            return "bullish"
        elif ema_20 < ema_50:
            return "bearish"
        else:
            return "neutral"

    def _get_volatility_level(self, df: pd.DataFrame) -> str:
        """Ermittelt Volatilitätslevel aus ATR."""
        if df.empty:
            return "unknown"

        current = df.iloc[-1]
        atr = current.get("atr_14")
        close = current.get("close")

        if pd.isna(atr) or pd.isna(close) or close == 0:
            return "normal"

        atr_percent = (atr / close) * 100

        if atr_percent > 3.0:
            return "high"
        elif atr_percent < 1.0:
            return "low"
        else:
            return "normal"

    def _get_momentum_direction(self, df: pd.DataFrame) -> str:
        """Ermittelt Momentum-Richtung aus RSI."""
        if df.empty:
            return "neutral"

        current = df.iloc[-1]
        rsi = current.get("rsi_14")

        if pd.isna(rsi):
            return "neutral"

        if rsi > 60:
            return "bullish"
        elif rsi < 40:
            return "bearish"
        else:
            return "neutral"
