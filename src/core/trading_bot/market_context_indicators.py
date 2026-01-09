"""MarketContext Indicators - Indicator snapshot data model.

Module 3/8 of market_context.py split.

This module contains:
- IndicatorSnapshot: Snapshot of all indicator values at one point in time
  (trend, momentum, volatility, volume, price action)
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime


@dataclass
class IndicatorSnapshot:
    """
    Snapshot aller Indikator-Werte zu einem Zeitpunkt.

    Erweitert gegenüber trade_logger.py um:
    - Trend-Alignment Score
    - Momentum-State
    - Volatility-State
    """

    timestamp: datetime
    timeframe: str = "5m"

    # === TREND INDIKATOREN ===
    ema_9: float | None = None
    ema_20: float | None = None
    ema_50: float | None = None
    ema_200: float | None = None
    ema_20_distance_pct: float | None = None  # Preis-Abstand zu EMA20 in %
    ema_50_distance_pct: float | None = None

    # Trend-State basierend auf EMA-Stacking
    trend_alignment: str | None = None  # ALIGNED_BULL, ALIGNED_BEAR, MIXED

    # === MOMENTUM ===
    rsi_14: float | None = None
    rsi_state: str | None = None  # OVERBOUGHT, OVERSOLD, NEUTRAL
    macd_line: float | None = None
    macd_signal: float | None = None
    macd_histogram: float | None = None
    macd_crossover: str | None = None  # BULLISH, BEARISH, NONE
    macd_histogram_trend: str | None = None  # INCREASING, DECREASING, FLAT

    # Stochastic (optional)
    stoch_k: float | None = None
    stoch_d: float | None = None
    stoch_state: str | None = None  # OVERBOUGHT, OVERSOLD, NEUTRAL

    # === VOLATILITÄT ===
    bb_upper: float | None = None
    bb_middle: float | None = None
    bb_lower: float | None = None
    bb_pct_b: float | None = None  # 0-1 Position in Bollinger Bands
    bb_width: float | None = None
    bb_squeeze: bool | None = None  # Width unter historischem Durchschnitt

    atr_14: float | None = None
    atr_percent: float | None = None  # ATR als % vom Preis
    volatility_state: str | None = None  # LOW, NORMAL, HIGH, EXTREME

    # === TREND STRENGTH ===
    adx_14: float | None = None
    plus_di: float | None = None
    minus_di: float | None = None
    di_crossover: str | None = None  # BULLISH, BEARISH, NONE

    # === VOLUME ===
    volume: float | None = None
    volume_sma_20: float | None = None
    volume_ratio: float | None = None  # Aktuelles Volume / SMA
    volume_state: str | None = None  # LOW, NORMAL, HIGH

    # === PRICE ACTION ===
    current_price: float | None = None
    high_24h: float | None = None
    low_24h: float | None = None
    price_change_24h_pct: float | None = None

    def to_dict(self) -> dict:
        """Konvertiert zu Dictionary."""
        result = asdict(self)
        result["timestamp"] = self.timestamp.isoformat()
        return result

    def get_momentum_score(self) -> float:
        """
        Berechnet einen Momentum-Score von -1 (bearish) bis +1 (bullish).
        """
        score = 0.0
        count = 0

        # RSI Beitrag
        if self.rsi_14 is not None:
            if self.rsi_14 > 70:
                score += 1.0
            elif self.rsi_14 > 50:
                score += 0.5
            elif self.rsi_14 < 30:
                score -= 1.0
            elif self.rsi_14 < 50:
                score -= 0.5
            count += 1

        # MACD Beitrag
        if self.macd_histogram is not None:
            if self.macd_histogram > 0:
                score += 0.5 if self.macd_histogram_trend == "INCREASING" else 0.25
            else:
                score -= 0.5 if self.macd_histogram_trend == "DECREASING" else -0.25
            count += 1

        return score / count if count > 0 else 0.0
