"""Chart Context Builder for AI Analysis.

Extracts and formats chart data for AI prompts.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import pandas as pd

from .chart_markings import ChartMarkingsState

if TYPE_CHECKING:
    from src.ui.widgets.embedded_tradingview_chart import EmbeddedTradingViewChart

logger = logging.getLogger(__name__)


@dataclass
class ChartContext:
    """Complete chart context for AI analysis."""

    symbol: str
    timeframe: str
    current_price: float

    # OHLCV Summary
    ohlcv_summary: dict[str, Any] = field(default_factory=dict)

    # Active Indicators
    indicators: dict[str, Any] = field(default_factory=dict)

    # Chart Markings (bidirectional)
    markings: ChartMarkingsState = field(default_factory=lambda: ChartMarkingsState())

    # Derived Metrics
    price_change_pct: float = 0.0
    volatility_atr: float | None = None
    volume_trend: str = "unknown"

    # Recent Highs/Lows
    recent_high: float = 0.0
    recent_low: float = 0.0

    # Data availability
    bars_available: int = 0

    def to_prompt_context(self) -> dict[str, Any]:
        """Convert to dictionary for prompt formatting."""
        return {
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "current_price": self.current_price,
            "ohlcv_summary": self._format_ohlcv_summary(),
            "indicators": self._format_indicators(),
            "markings": self.markings.to_prompt_text(),
            "price_change_pct": self.price_change_pct,
            "volatility_atr": self.volatility_atr,
            "volume_trend": self.volume_trend,
            "recent_high": self.recent_high,
            "recent_low": self.recent_low,
            "lookback": self.bars_available,
        }

    def _format_ohlcv_summary(self) -> str:
        """Format OHLCV summary for prompt."""
        if not self.ohlcv_summary:
            return "Keine OHLCV-Daten verfügbar"

        lines = []
        s = self.ohlcv_summary

        if "current" in s:
            c = s["current"]
            lines.append(f"Aktuelle Kerze: O={c.get('open', 'N/A'):.4f} "
                        f"H={c.get('high', 'N/A'):.4f} "
                        f"L={c.get('low', 'N/A'):.4f} "
                        f"C={c.get('close', 'N/A'):.4f}")

        if "stats" in s:
            st = s["stats"]
            lines.append(f"Durchschnitt Close: {st.get('avg_close', 0):.4f}")
            lines.append(f"Höchster Preis: {st.get('max_high', 0):.4f}")
            lines.append(f"Tiefster Preis: {st.get('min_low', 0):.4f}")
            lines.append(f"Durchschnittliches Volumen: {st.get('avg_volume', 0):,.0f}")

        if "trend" in s:
            t = s["trend"]
            lines.append(f"Trend (SMA-basiert): {t.get('direction', 'N/A')}")
            lines.append(f"Trendstärke: {t.get('strength', 'N/A')}")

        return "\n".join(lines) if lines else "Keine Details verfügbar"

    def _format_indicators(self) -> str:
        """Format indicators for prompt."""
        if not self.indicators:
            return "Keine Indikatoren aktiv"

        lines = []
        for name, values in self.indicators.items():
            if isinstance(values, dict):
                # Multi-value indicator (e.g., MACD, Bollinger)
                parts = [f"{k}={v:.4f}" if isinstance(v, float) else f"{k}={v}"
                        for k, v in values.items()]
                lines.append(f"{name}: {', '.join(parts)}")
            elif isinstance(values, (int, float)):
                lines.append(f"{name}: {values:.4f}")
            else:
                lines.append(f"{name}: {values}")

        return "\n".join(lines)


class ChartContextBuilder:
    """Builds chart context from EmbeddedTradingViewChart widget."""

    def __init__(self, chart_widget: "EmbeddedTradingViewChart"):
        """Initialize context builder.

        Args:
            chart_widget: The chart widget to extract data from
        """
        self.chart = chart_widget

    def build_context(self, lookback_bars: int = 100) -> ChartContext:
        """Extract complete context from chart widget.

        Args:
            lookback_bars: Number of recent bars to analyze

        Returns:
            ChartContext with all available data
        """
        symbol = getattr(self.chart, "current_symbol", "") or "UNKNOWN"
        timeframe = getattr(self.chart, "current_timeframe", "") or "1T"

        # Get current price
        current_price = self._get_current_price()

        # Get OHLCV data
        df = getattr(self.chart, "data", None)
        if df is None or df.empty:
            logger.warning("No chart data available")
            return ChartContext(
                symbol=symbol,
                timeframe=timeframe,
                current_price=current_price,
            )

        # Limit to lookback
        df_recent = df.tail(lookback_bars)

        # Build context
        context = ChartContext(
            symbol=symbol,
            timeframe=timeframe,
            current_price=current_price,
            ohlcv_summary=self._summarize_ohlcv(df_recent),
            indicators=self._extract_indicators(df_recent),
            price_change_pct=self._calculate_price_change(df_recent),
            volatility_atr=self._calculate_atr(df_recent),
            volume_trend=self._determine_volume_trend(df_recent),
            recent_high=float(df_recent["high"].max()),
            recent_low=float(df_recent["low"].min()),
            bars_available=len(df_recent),
        )

        return context

    def _get_current_price(self) -> float:
        """Get current price from chart."""
        # Try _last_price first (from streaming)
        price = getattr(self.chart, "_last_price", None)
        if price is not None:
            return float(price)

        # Fall back to last close
        df = getattr(self.chart, "data", None)
        if df is not None and not df.empty and "close" in df.columns:
            return float(df["close"].iloc[-1])

        return 0.0

    def _summarize_ohlcv(self, df: pd.DataFrame) -> dict[str, Any]:
        """Summarize OHLCV data for prompt.

        Args:
            df: DataFrame with OHLCV data

        Returns:
            Summary dictionary
        """
        if df.empty:
            return {}

        summary = {
            "current": {
                "open": float(df["open"].iloc[-1]),
                "high": float(df["high"].iloc[-1]),
                "low": float(df["low"].iloc[-1]),
                "close": float(df["close"].iloc[-1]),
            },
            "stats": {
                "avg_close": float(df["close"].mean()),
                "max_high": float(df["high"].max()),
                "min_low": float(df["low"].min()),
                "avg_volume": float(df["volume"].mean()) if "volume" in df else 0,
            },
        }

        # Simple trend detection
        if len(df) >= 20:
            sma_short = df["close"].tail(10).mean()
            sma_long = df["close"].tail(20).mean()

            if sma_short > sma_long * 1.01:
                direction = "aufwärts"
                strength = "stark" if sma_short > sma_long * 1.02 else "moderat"
            elif sma_short < sma_long * 0.99:
                direction = "abwärts"
                strength = "stark" if sma_short < sma_long * 0.98 else "moderat"
            else:
                direction = "seitwärts"
                strength = "schwach"

            summary["trend"] = {
                "direction": direction,
                "strength": strength,
            }

        return summary

    def _extract_indicators(self, df: pd.DataFrame) -> dict[str, Any]:
        """Extract active indicator values.

        Args:
            df: DataFrame with OHLCV data

        Returns:
            Dictionary of indicator values
        """
        indicators: dict[str, Any] = {}
        active = getattr(self.chart, "active_indicators", {})

        for indicator_name, is_active in active.items():
            if not is_active:
                continue
            try:
                self._compute_indicator(df, indicator_name, indicators)
            except Exception as e:
                logger.warning("Failed to calculate %s: %s", indicator_name, e)

        self._ensure_default_sma(df, indicators)
        return indicators

    def _compute_indicator(
        self,
        df: pd.DataFrame,
        indicator_name: str,
        indicators: dict[str, Any],
    ) -> None:
        indicator_name_upper = indicator_name.upper()
        if indicator_name_upper == "RSI":
            rsi = self._calculate_rsi(df["close"])
            if rsi is not None:
                indicators["RSI"] = round(rsi, 2)
            return
        if indicator_name_upper == "MACD":
            macd_data = self._calculate_macd(df["close"])
            if macd_data:
                indicators["MACD"] = macd_data
            return
        if indicator_name_upper in ("SMA", "SMA20"):
            sma = df["close"].tail(20).mean()
            indicators["SMA20"] = round(sma, 4)
            return
        if indicator_name_upper in ("EMA", "EMA20"):
            ema = df["close"].ewm(span=20).mean().iloc[-1]
            indicators["EMA20"] = round(ema, 4)
            return
        if indicator_name_upper in ("BB", "BOLLINGER"):
            bb_data = self._calculate_bollinger(df["close"])
            if bb_data:
                indicators["Bollinger"] = bb_data

    def _ensure_default_sma(self, df: pd.DataFrame, indicators: dict[str, Any]) -> None:
        if len(df) >= 20 and "SMA20" not in indicators:
            indicators["SMA20"] = round(df["close"].tail(20).mean(), 4)

    def _calculate_price_change(self, df: pd.DataFrame) -> float:
        """Calculate price change percentage over the period."""
        if len(df) < 2:
            return 0.0

        first_close = df["close"].iloc[0]
        last_close = df["close"].iloc[-1]

        if first_close == 0:
            return 0.0

        return ((last_close - first_close) / first_close) * 100

    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> float | None:
        """Calculate Average True Range."""
        if len(df) < period:
            return None

        high = df["high"]
        low = df["low"]
        close = df["close"]

        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))

        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean().iloc[-1]

        return float(atr) if not pd.isna(atr) else None

    def _determine_volume_trend(self, df: pd.DataFrame) -> str:
        """Determine volume trend (increasing/decreasing/stable)."""
        if "volume" not in df or len(df) < 10:
            return "unbekannt"

        recent_vol = df["volume"].tail(5).mean()
        earlier_vol = df["volume"].head(5).mean()

        if earlier_vol == 0:
            return "unbekannt"

        ratio = recent_vol / earlier_vol

        if ratio > 1.2:
            return "steigend"
        elif ratio < 0.8:
            return "fallend"
        else:
            return "stabil"

    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> float | None:
        """Calculate RSI indicator."""
        if len(prices) < period + 1:
            return None

        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        return float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else None

    def _calculate_macd(
        self, prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9
    ) -> dict[str, float] | None:
        """Calculate MACD indicator."""
        if len(prices) < slow + signal:
            return None

        ema_fast = prices.ewm(span=fast).mean()
        ema_slow = prices.ewm(span=slow).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal).mean()
        histogram = macd_line - signal_line

        return {
            "macd": round(float(macd_line.iloc[-1]), 4),
            "signal": round(float(signal_line.iloc[-1]), 4),
            "histogram": round(float(histogram.iloc[-1]), 4),
        }

    def _calculate_bollinger(
        self, prices: pd.Series, period: int = 20, std_dev: float = 2.0
    ) -> dict[str, float] | None:
        """Calculate Bollinger Bands."""
        if len(prices) < period:
            return None

        sma = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()

        upper = sma + (std * std_dev)
        lower = sma - (std * std_dev)

        current_price = prices.iloc[-1]
        bb_width = (upper.iloc[-1] - lower.iloc[-1]) / sma.iloc[-1] * 100

        return {
            "upper": round(float(upper.iloc[-1]), 4),
            "middle": round(float(sma.iloc[-1]), 4),
            "lower": round(float(lower.iloc[-1]), 4),
            "width_pct": round(bb_width, 2),
            "position": round((current_price - lower.iloc[-1]) /
                             (upper.iloc[-1] - lower.iloc[-1]) * 100, 1),
        }
