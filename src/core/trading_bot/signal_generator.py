"""
Signal Generator - Confluence-basierte Entry/Exit Signal Generierung (REFACTORED).

REFACTORED: Split into focused helper modules using composition pattern.

Generiert Trading-Signale basierend auf:
- Multi-Timeframe Analyse (1D, 4h, 1h, 5m)
- Technische Indikatoren (EMA, RSI, MACD, BB, ATR, ADX)
- Regime-Erkennung (Trend vs. Range)
- Confluence-Score (mind. 3 von 5 Bedingungen)
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pandas as pd

# Import types and results from new locations
from .signal_types import SignalDirection, SignalStrength, TradeSignal

# Import helper modules
from .signal_generator_exit_signal import SignalGeneratorExitSignal
from .signal_generator_indicator_snapshot import SignalGeneratorIndicatorSnapshot
from .signal_generator_long_conditions import SignalGeneratorLongConditions
from .signal_generator_short_conditions import SignalGeneratorShortConditions

if TYPE_CHECKING:
    from .trade_logger import IndicatorSnapshot

# Re-export types for backward compatibility
__all__ = [
    "SignalGenerator",
    "SignalDirection",
    "SignalStrength",
    "TradeSignal",
]

logger = logging.getLogger(__name__)


class SignalGenerator:
    """
    Generiert Trading-Signale basierend auf technischer Analyse (REFACTORED).

    Verwendet Confluence-basierte Logik:
    - Mindestens 3 von 5 Bedingungen müssen erfüllt sein
    - Regime muss zur Signal-Richtung passen

    Delegiert spezifische Aufgaben an Helper-Klassen.
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

        # Create helpers (composition pattern)
        self._long_conditions = SignalGeneratorLongConditions(self)
        self._short_conditions = SignalGeneratorShortConditions(self)
        self._exit_signal = SignalGeneratorExitSignal(self)
        self._indicator_snapshot = SignalGeneratorIndicatorSnapshot(self)

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
        # Validate data
        validation_signal = self._validate_signal_data(df)
        if validation_signal:
            return validation_signal

        current_price = float(df.iloc[-1].get("close", 0))

        # Check conditions and determine direction
        signal_result = self._determine_signal_direction(df)
        if signal_result is None:
            return self._create_neutral_signal(
                f"Insufficient confluence"
            )

        direction, confluence, conditions_met, conditions_failed = signal_result

        # Validate regime alignment
        if require_regime_alignment and regime:
            regime_error = self._validate_regime_alignment(direction, regime)
            if regime_error:
                return regime_error

        # Calculate signal strength
        strength = self._calculate_signal_strength(confluence)

        # Create signal
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

    def _validate_signal_data(self, df: pd.DataFrame) -> TradeSignal | None:
        """Validate DataFrame and price data.

        Returns:
            Neutral signal if validation fails, None if data is valid.
        """
        if df.empty or len(df) < self.EMA_LONG:
            logger.warning("Insufficient data for signal generation")
            return self._create_neutral_signal("Insufficient data")

        current_price = float(df.iloc[-1].get("close", 0))
        if current_price <= 0:
            return self._create_neutral_signal("Invalid price data")

        return None

    def _determine_signal_direction(
        self, df: pd.DataFrame
    ) -> tuple[SignalDirection, int, list, list] | None:
        """Determine signal direction based on confluence scores.

        Returns:
            Tuple of (direction, confluence, conditions_met, conditions_failed)
            or None if no valid signal.
        """
        current = df.iloc[-1]

        # Get conditions from helpers
        long_conditions = self._long_conditions.check_long_conditions(df, current)
        short_conditions = self._short_conditions.check_short_conditions(df, current)

        long_score = sum(1 for c in long_conditions if c.met)
        short_score = sum(1 for c in short_conditions if c.met)

        # Determine direction based on scores
        if long_score >= self.min_confluence and long_score > short_score:
            return self._build_signal_result(
                SignalDirection.LONG, long_score, long_conditions
            )

        if short_score >= self.min_confluence and short_score > long_score:
            return self._build_signal_result(
                SignalDirection.SHORT, short_score, short_conditions
            )

        return None

    def _build_signal_result(
        self, direction: SignalDirection, score: int, conditions: list
    ) -> tuple[SignalDirection, int, list, list]:
        """Build signal result tuple from direction and conditions.

        Args:
            direction: Signal direction.
            score: Confluence score.
            conditions: List of all conditions checked.

        Returns:
            Tuple of (direction, score, conditions_met, conditions_failed).
        """
        conditions_met = [c for c in conditions if c.met]
        conditions_failed = [c for c in conditions if not c.met]
        return direction, score, conditions_met, conditions_failed

    def _validate_regime_alignment(
        self, direction: SignalDirection, regime: str
    ) -> TradeSignal | None:
        """Validate that signal direction aligns with market regime.

        Returns:
            Neutral signal if regime misaligned, None if aligned.
        """
        if not self._is_regime_aligned(direction, regime):
            return self._create_neutral_signal(
                f"Regime mismatch: {regime} vs {direction.value}"
            )
        return None

    def _calculate_signal_strength(self, confluence: int) -> SignalStrength:
        """Calculate signal strength from confluence score.

        Args:
            confluence: Confluence score (0-5).

        Returns:
            SignalStrength enum value.
        """
        if confluence >= 5:
            return SignalStrength.STRONG
        if confluence >= 4:
            return SignalStrength.MODERATE
        return SignalStrength.WEAK

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
        from .signal_types import ConditionResult

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
        Prüft ob Exit-Signal für bestehende Position vorliegt (delegiert).

        Args:
            df: DataFrame mit OHLCV und Indikatoren
            current_position_side: "BUY" (Long) oder "SELL" (Short)

        Returns:
            Tuple (should_exit, reason)
        """
        return self._exit_signal.check_exit_signal(df, current_position_side)

    def extract_indicator_snapshot(self, df: pd.DataFrame) -> "IndicatorSnapshot":
        """
        Extrahiert Indikator-Snapshot aus DataFrame (delegiert).

        Für Trade-Logging.
        """
        return self._indicator_snapshot.extract_indicator_snapshot(df)
