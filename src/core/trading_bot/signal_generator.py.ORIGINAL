"""
Signal Generator - Confluence-basierte Entry/Exit Signal Generierung

Generiert Trading-Signale basierend auf:
- Multi-Timeframe Analyse (1D, 4h, 1h, 5m)
- Technische Indikatoren (EMA, RSI, MACD, BB, ATR, ADX)
- Regime-Erkennung (Trend vs. Range)
- Confluence-Score (mind. 3 von 5 Bedingungen)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING

import pandas as pd

if TYPE_CHECKING:
    from .trade_logger import IndicatorSnapshot, MarketContext

logger = logging.getLogger(__name__)


class SignalDirection(str, Enum):
    """Signalrichtung."""

    LONG = "LONG"
    SHORT = "SHORT"
    NEUTRAL = "NEUTRAL"


class SignalStrength(str, Enum):
    """Signalstärke basierend auf Confluence."""

    STRONG = "STRONG"  # 5/5 Conditions
    MODERATE = "MODERATE"  # 4/5 Conditions
    WEAK = "WEAK"  # 3/5 Conditions
    NONE = "NONE"  # < 3 Conditions


@dataclass
class ConditionResult:
    """Ergebnis einer einzelnen Bedingungsprüfung."""

    name: str
    met: bool
    value: float | str | None = None
    threshold: float | str | None = None
    description: str = ""


@dataclass
class TradeSignal:
    """Trading-Signal mit allen Details."""

    direction: SignalDirection
    strength: SignalStrength
    confluence_score: int  # 0-5
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Bedingungen
    conditions_met: list[ConditionResult] = field(default_factory=list)
    conditions_failed: list[ConditionResult] = field(default_factory=list)

    # Kontext
    current_price: float | None = None
    regime: str | None = None

    # Empfohlene Levels (von RiskManager zu füllen)
    suggested_entry: float | None = None
    suggested_sl: float | None = None
    suggested_tp: float | None = None

    @property
    def is_valid(self) -> bool:
        """Signal ist valid wenn confluence_score >= 3."""
        return self.confluence_score >= 3 and self.direction != SignalDirection.NEUTRAL

    def get_conditions_summary(self) -> dict[str, list[str]]:
        """Gibt Zusammenfassung der Bedingungen zurück."""
        return {
            "met": [f"{c.name}: {c.description}" for c in self.conditions_met],
            "failed": [f"{c.name}: {c.description}" for c in self.conditions_failed],
        }


class SignalGenerator:
    """
    Generiert Trading-Signale basierend auf technischer Analyse.

    Verwendet Confluence-basierte Logik:
    - Mindestens 3 von 5 Bedingungen müssen erfüllt sein
    - Regime muss zur Signal-Richtung passen
    """

    # Indikator-Parameter
    EMA_SHORT = 20
    EMA_MEDIUM = 50
    EMA_LONG = 200
    RSI_PERIOD = 14
    RSI_OVERBOUGHT = 70
    RSI_OVERSOLD = 30
    ADX_THRESHOLD = 20
    MACD_FAST = 12
    MACD_SLOW = 26
    MACD_SIGNAL = 9

    def __init__(self, min_confluence: int = 3):
        """
        Args:
            min_confluence: Minimum Confluence Score für valides Signal (default: 3)
        """
        self.min_confluence = min_confluence
        logger.info(f"SignalGenerator initialized. Min confluence: {min_confluence}")

    def generate_signal(
        self,
        df: pd.DataFrame,
        regime: str | None = None,
        require_regime_alignment: bool = True,
    ) -> TradeSignal:
        """
        Generiert Trading-Signal aus OHLCV DataFrame.

        Args:
            df: DataFrame mit OHLCV Daten und berechneten Indikatoren
            regime: Aktuelles Market Regime (optional)
            require_regime_alignment: Ob Regime zum Signal passen muss

        Returns:
            TradeSignal mit Direction, Strength und Confluence Score
        """
        if df.empty or len(df) < self.EMA_LONG:
            logger.warning("Insufficient data for signal generation")
            return self._create_neutral_signal("Insufficient data")

        # Aktuelle Werte
        current = df.iloc[-1]
        current_price = float(current.get("close", 0))

        if current_price <= 0:
            return self._create_neutral_signal("Invalid price data")

        # Prüfe alle Bedingungen
        long_conditions = self._check_long_conditions(df, current)
        short_conditions = self._check_short_conditions(df, current)

        long_score = sum(1 for c in long_conditions if c.met)
        short_score = sum(1 for c in short_conditions if c.met)

        # Bestimme Richtung
        if long_score >= self.min_confluence and long_score > short_score:
            direction = SignalDirection.LONG
            confluence = long_score
            conditions_met = [c for c in long_conditions if c.met]
            conditions_failed = [c for c in long_conditions if not c.met]

        elif short_score >= self.min_confluence and short_score > long_score:
            direction = SignalDirection.SHORT
            confluence = short_score
            conditions_met = [c for c in short_conditions if c.met]
            conditions_failed = [c for c in short_conditions if not c.met]

        else:
            return self._create_neutral_signal(
                f"Insufficient confluence (Long: {long_score}, Short: {short_score})"
            )

        # Regime-Check
        if require_regime_alignment and regime:
            if not self._is_regime_aligned(direction, regime):
                return self._create_neutral_signal(
                    f"Regime mismatch: {regime} vs {direction.value}"
                )

        # Signalstärke
        if confluence >= 5:
            strength = SignalStrength.STRONG
        elif confluence >= 4:
            strength = SignalStrength.MODERATE
        else:
            strength = SignalStrength.WEAK

        signal = TradeSignal(
            direction=direction,
            strength=strength,
            confluence_score=confluence,
            conditions_met=conditions_met,
            conditions_failed=conditions_failed,
            current_price=current_price,
            regime=regime,
        )

        logger.info(
            f"Signal generated: {direction.value} "
            f"(Confluence: {confluence}/5, Strength: {strength.value})"
        )

        return signal

    def _check_long_conditions(
        self, df: pd.DataFrame, current: pd.Series
    ) -> list[ConditionResult]:
        """Prüft alle LONG Entry-Bedingungen."""
        conditions = []

        # 1. Regime Check (nicht BEAR)
        # Wird extern geprüft, hier nur Placeholder
        conditions.append(
            ConditionResult(
                name="regime_favorable",
                met=True,  # Wird von generate_signal überschrieben
                description="Regime is not STRONG_TREND_BEAR",
            )
        )

        # 2. Preis über EMA20 UND EMA20 > EMA50
        ema20 = current.get("ema_20") or current.get("EMA_20")
        ema50 = current.get("ema_50") or current.get("EMA_50")
        price = current.get("close", 0)

        if ema20 and ema50 and price:
            price_above_ema = price > ema20 and ema20 > ema50
            conditions.append(
                ConditionResult(
                    name="ema_alignment",
                    met=price_above_ema,
                    value=f"Price: {price:.2f}, EMA20: {ema20:.2f}, EMA50: {ema50:.2f}",
                    description="Price > EMA20 > EMA50 (bullish alignment)",
                )
            )
        else:
            conditions.append(
                ConditionResult(
                    name="ema_alignment",
                    met=False,
                    description="EMA data not available",
                )
            )

        # 3. RSI zwischen 40-70 (nicht überkauft)
        rsi = current.get("rsi_14") or current.get("RSI_14") or current.get("rsi")

        if rsi is not None:
            rsi_ok = 40 <= rsi <= 70
            conditions.append(
                ConditionResult(
                    name="rsi_favorable",
                    met=rsi_ok,
                    value=rsi,
                    threshold="40-70",
                    description=f"RSI at {rsi:.1f} (not overbought, room to rise)",
                )
            )
        else:
            conditions.append(
                ConditionResult(
                    name="rsi_favorable",
                    met=False,
                    description="RSI data not available",
                )
            )

        # 4. MACD Linie > Signal Linie
        macd = current.get("macd") or current.get("MACD")
        macd_signal = current.get("macd_signal") or current.get("MACD_signal")

        if macd is not None and macd_signal is not None:
            macd_bullish = macd > macd_signal
            conditions.append(
                ConditionResult(
                    name="macd_bullish",
                    met=macd_bullish,
                    value=f"MACD: {macd:.2f}, Signal: {macd_signal:.2f}",
                    description="MACD line above signal line (bullish momentum)",
                )
            )
        else:
            conditions.append(
                ConditionResult(
                    name="macd_bullish",
                    met=False,
                    description="MACD data not available",
                )
            )

        # 5. ADX > 20 (Trend vorhanden)
        adx = current.get("adx_14") or current.get("ADX_14") or current.get("adx")

        if adx is not None:
            adx_ok = adx > self.ADX_THRESHOLD
            conditions.append(
                ConditionResult(
                    name="adx_trending",
                    met=adx_ok,
                    value=adx,
                    threshold=self.ADX_THRESHOLD,
                    description=f"ADX at {adx:.1f} (trend present)" if adx_ok
                    else f"ADX at {adx:.1f} (weak trend)",
                )
            )
        else:
            conditions.append(
                ConditionResult(
                    name="adx_trending",
                    met=False,
                    description="ADX data not available",
                )
            )

        return conditions

    def _check_short_conditions(
        self, df: pd.DataFrame, current: pd.Series
    ) -> list[ConditionResult]:
        """Prüft alle SHORT Entry-Bedingungen."""
        conditions = []

        # 1. Regime Check (nicht BULL)
        conditions.append(
            ConditionResult(
                name="regime_favorable",
                met=True,  # Wird von generate_signal überschrieben
                description="Regime is not STRONG_TREND_BULL",
            )
        )

        # 2. Preis unter EMA20 UND EMA20 < EMA50
        ema20 = current.get("ema_20") or current.get("EMA_20")
        ema50 = current.get("ema_50") or current.get("EMA_50")
        price = current.get("close", 0)

        if ema20 and ema50 and price:
            price_below_ema = price < ema20 and ema20 < ema50
            conditions.append(
                ConditionResult(
                    name="ema_alignment",
                    met=price_below_ema,
                    value=f"Price: {price:.2f}, EMA20: {ema20:.2f}, EMA50: {ema50:.2f}",
                    description="Price < EMA20 < EMA50 (bearish alignment)",
                )
            )
        else:
            conditions.append(
                ConditionResult(
                    name="ema_alignment",
                    met=False,
                    description="EMA data not available",
                )
            )

        # 3. RSI zwischen 30-60 (nicht überverkauft)
        rsi = current.get("rsi_14") or current.get("RSI_14") or current.get("rsi")

        if rsi is not None:
            rsi_ok = 30 <= rsi <= 60
            conditions.append(
                ConditionResult(
                    name="rsi_favorable",
                    met=rsi_ok,
                    value=rsi,
                    threshold="30-60",
                    description=f"RSI at {rsi:.1f} (not oversold, room to fall)",
                )
            )
        else:
            conditions.append(
                ConditionResult(
                    name="rsi_favorable",
                    met=False,
                    description="RSI data not available",
                )
            )

        # 4. MACD Linie < Signal Linie
        macd = current.get("macd") or current.get("MACD")
        macd_signal = current.get("macd_signal") or current.get("MACD_signal")

        if macd is not None and macd_signal is not None:
            macd_bearish = macd < macd_signal
            conditions.append(
                ConditionResult(
                    name="macd_bearish",
                    met=macd_bearish,
                    value=f"MACD: {macd:.2f}, Signal: {macd_signal:.2f}",
                    description="MACD line below signal line (bearish momentum)",
                )
            )
        else:
            conditions.append(
                ConditionResult(
                    name="macd_bearish",
                    met=False,
                    description="MACD data not available",
                )
            )

        # 5. ADX > 20 (Trend vorhanden)
        adx = current.get("adx_14") or current.get("ADX_14") or current.get("adx")

        if adx is not None:
            adx_ok = adx > self.ADX_THRESHOLD
            conditions.append(
                ConditionResult(
                    name="adx_trending",
                    met=adx_ok,
                    value=adx,
                    threshold=self.ADX_THRESHOLD,
                    description=f"ADX at {adx:.1f} (trend present)" if adx_ok
                    else f"ADX at {adx:.1f} (weak trend)",
                )
            )
        else:
            conditions.append(
                ConditionResult(
                    name="adx_trending",
                    met=False,
                    description="ADX data not available",
                )
            )

        return conditions

    def _is_regime_aligned(self, direction: SignalDirection, regime: str) -> bool:
        """Prüft ob Regime zur Signal-Richtung passt."""
        regime_upper = regime.upper()

        if direction == SignalDirection.LONG:
            # Kein Long bei starkem Bären-Trend
            return "STRONG_TREND_BEAR" not in regime_upper

        elif direction == SignalDirection.SHORT:
            # Kein Short bei starkem Bullen-Trend
            return "STRONG_TREND_BULL" not in regime_upper

        return True

    def _create_neutral_signal(self, reason: str) -> TradeSignal:
        """Erstellt neutrales Signal (kein Trade)."""
        return TradeSignal(
            direction=SignalDirection.NEUTRAL,
            strength=SignalStrength.NONE,
            confluence_score=0,
            conditions_failed=[
                ConditionResult(name="no_signal", met=False, description=reason)
            ],
        )

    def check_exit_signal(
        self, df: pd.DataFrame, current_position_side: str
    ) -> tuple[bool, str]:
        """
        Prüft ob Exit-Signal für bestehende Position vorliegt.

        Args:
            df: DataFrame mit OHLCV und Indikatoren
            current_position_side: "BUY" (Long) oder "SELL" (Short)

        Returns:
            Tuple (should_exit, reason)
        """
        if df.empty:
            return False, ""

        current = df.iloc[-1]

        # Generiere neues Signal
        new_signal = self.generate_signal(df, require_regime_alignment=False)

        # Exit bei Signal-Umkehr
        if current_position_side == "BUY" and new_signal.direction == SignalDirection.SHORT:
            if new_signal.confluence_score >= self.min_confluence:
                return True, "Signal reversal: SHORT signal while LONG"

        elif current_position_side == "SELL" and new_signal.direction == SignalDirection.LONG:
            if new_signal.confluence_score >= self.min_confluence:
                return True, "Signal reversal: LONG signal while SHORT"

        # Exit bei starkem RSI Extremwert
        rsi = current.get("rsi_14") or current.get("RSI_14") or current.get("rsi")

        if rsi is not None:
            if current_position_side == "BUY" and rsi > 80:
                return True, f"RSI extremely overbought ({rsi:.1f})"
            elif current_position_side == "SELL" and rsi < 20:
                return True, f"RSI extremely oversold ({rsi:.1f})"

        return False, ""

    def extract_indicator_snapshot(
        self, df: pd.DataFrame
    ) -> "IndicatorSnapshot":
        """
        Extrahiert Indikator-Snapshot aus DataFrame.

        Für Trade-Logging.
        """
        from .trade_logger import IndicatorSnapshot

        if df.empty:
            return IndicatorSnapshot(timestamp=datetime.now(timezone.utc))

        current = df.iloc[-1]
        price = float(current.get("close", 0))

        # EMA Werte
        ema20 = current.get("ema_20") or current.get("EMA_20")
        ema50 = current.get("ema_50") or current.get("EMA_50")
        ema200 = current.get("ema_200") or current.get("EMA_200")

        ema20_dist = None
        if ema20 and price:
            ema20_dist = ((price - ema20) / ema20) * 100

        # RSI
        rsi = current.get("rsi_14") or current.get("RSI_14") or current.get("rsi")
        rsi_state = None
        if rsi is not None:
            if rsi > 70:
                rsi_state = "OVERBOUGHT"
            elif rsi < 30:
                rsi_state = "OVERSOLD"
            else:
                rsi_state = "NEUTRAL"

        # MACD
        macd = current.get("macd") or current.get("MACD")
        macd_signal = current.get("macd_signal") or current.get("MACD_signal")
        macd_hist = current.get("macd_hist") or current.get("MACD_hist")

        macd_crossover = None
        if macd is not None and macd_signal is not None:
            if macd > macd_signal:
                macd_crossover = "BULLISH"
            else:
                macd_crossover = "BEARISH"

        # Bollinger Bands
        bb_upper = current.get("bb_upper") or current.get("BB_upper")
        bb_middle = current.get("bb_middle") or current.get("BB_middle")
        bb_lower = current.get("bb_lower") or current.get("BB_lower")

        bb_pct_b = None
        bb_width = None
        if bb_upper and bb_lower and bb_middle and price:
            if bb_upper != bb_lower:
                bb_pct_b = (price - bb_lower) / (bb_upper - bb_lower)
                bb_width = (bb_upper - bb_lower) / bb_middle

        # ATR
        atr = current.get("atr_14") or current.get("ATR_14") or current.get("atr")
        atr_pct = None
        if atr and price:
            atr_pct = (atr / price) * 100

        # ADX
        adx = current.get("adx_14") or current.get("ADX_14") or current.get("adx")
        plus_di = current.get("plus_di") or current.get("+DI")
        minus_di = current.get("minus_di") or current.get("-DI")

        # Volume
        volume = current.get("volume")
        volume_sma = current.get("volume_sma_20")
        volume_ratio = None
        if volume and volume_sma and volume_sma > 0:
            volume_ratio = volume / volume_sma

        # Timestamp
        timestamp = current.get("timestamp")
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)
        elif isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)

        return IndicatorSnapshot(
            timestamp=timestamp,
            ema_20=float(ema20) if ema20 else None,
            ema_50=float(ema50) if ema50 else None,
            ema_200=float(ema200) if ema200 else None,
            ema_20_distance_pct=float(ema20_dist) if ema20_dist else None,
            rsi_14=float(rsi) if rsi is not None else None,
            rsi_state=rsi_state,
            macd_line=float(macd) if macd is not None else None,
            macd_signal=float(macd_signal) if macd_signal is not None else None,
            macd_histogram=float(macd_hist) if macd_hist is not None else None,
            macd_crossover=macd_crossover,
            bb_upper=float(bb_upper) if bb_upper else None,
            bb_middle=float(bb_middle) if bb_middle else None,
            bb_lower=float(bb_lower) if bb_lower else None,
            bb_pct_b=float(bb_pct_b) if bb_pct_b is not None else None,
            bb_width=float(bb_width) if bb_width is not None else None,
            atr_14=float(atr) if atr else None,
            atr_percent=float(atr_pct) if atr_pct else None,
            adx_14=float(adx) if adx else None,
            plus_di=float(plus_di) if plus_di else None,
            minus_di=float(minus_di) if minus_di else None,
            volume=float(volume) if volume else None,
            volume_sma_20=float(volume_sma) if volume_sma else None,
            volume_ratio=float(volume_ratio) if volume_ratio else None,
            current_price=price if price else None,
        )
