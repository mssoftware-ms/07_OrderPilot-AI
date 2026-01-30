"""JSON Entry Scorer - CEL-basierte Entry Evaluation.

Evaluiert CEL-Expressions aus Regime + Indicator JSON für Entry-Entscheidungen.
Ersetzt EntryScoreEngine für JSON-basierte Entry-Logik.

Author: Claude Code
Date: 2026-01-28
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.core.tradingbot.cel_engine import CELEngine
    from .json_entry_loader import JsonEntryConfig
    from .models import FeatureVector, RegimeState

logger = logging.getLogger(__name__)


class JsonEntryScorer:
    """Evaluiert Entry via CEL Expression aus JSON.

    Ersetzt EntryScoreEngine für JSON-basierte Entry-Logik.
    Verwendet beide JSON-Dateien (Regime + Indicator) für Context-Building.

    Der Scorer:
    1. Compiled CEL Expression einmalig beim Init
    2. Baut CEL Context aus FeatureVector + RegimeState
    3. Evaluiert Expression (True/False)
    4. Generiert Reason Codes für Entry-Signale

    Attributes:
        config: JsonEntryConfig mit Entry Expression und Indicators
        cel: CEL Engine für Expression Evaluation
        _compiled_expr: Compiled CEL Program (cached für Performance)

    Example:
        >>> scorer = JsonEntryScorer(json_config, cel_engine)
        >>> should_enter, score, reasons = scorer.should_enter_long(features, regime)
        >>> if should_enter:
        ...     print(f"LONG Entry: score={score}, reasons={reasons}")
    """

    def __init__(
        self,
        json_config: "JsonEntryConfig",
        cel_engine: "CELEngine",
    ):
        """Initialize JSON Entry Scorer.

        Args:
            json_config: Combined Regime + Indicator JSON config
            cel_engine: CEL evaluation engine

        Raises:
            RuntimeError: Wenn CEL Expression nicht compiliert werden kann
        """
        self.config = json_config
        self.cel = cel_engine

        # Validate expression (do a test evaluation)
        self._validate_expression()

    def _validate_expression(self) -> None:
        """Validate CEL expression with a dummy context.

        Raises:
            RuntimeError: If expression is invalid or can't be evaluated
        """
        try:
            # Create minimal test context
            test_context = {
                "side": "long",
                "regime": "TEST",
                "rsi": 50.0,
                "adx": 25.0,
                "macd_hist": 0.0,
            }
            
            # Try to evaluate (will raise ValueError if syntax is invalid)
            # We don't care about the result, just that it doesn't crash
            self.cel.evaluate(self.config.entry_expression, test_context, default=False)
            
            logger.info(
                f"CEL expression validated successfully: "
                f"{self.config.entry_expression[:80]}..."
            )
        except Exception as e:
            logger.error(
                f"CEL validation failed for expression: "
                f"{self.config.entry_expression[:50]}...\n"
                f"Error: {e}"
            )
            raise RuntimeError(
                f"CEL Expression validation failed: {e}\n"
                f"Expression: {self.config.entry_expression[:100]}..."
            ) from e

    def should_enter_long(
        self,
        features: "FeatureVector",
        regime: "RegimeState",
        chart_window: Any | None = None,
        prev_regime: str | None = None,
    ) -> tuple[bool, float, list[str]]:
        """Prüfe Long Entry via CEL Expression.

        Args:
            features: Current feature vector (indicators, price data)
            regime: Current market regime
            chart_window: Chart window reference (für trigger_regime_analysis())
            prev_regime: Previous/last closed regime (für last_closed_regime())

        Returns:
            Tuple of:
                - should_enter: True wenn Entry Signal, False sonst
                - score: Confidence Score (1.0 wenn true, 0.0 wenn false)
                - reason_codes: Liste von Reason-Codes (z.B. ["JSON_CEL_ENTRY", "RSI_OVERSOLD"])

        Example:
            >>> should_enter, score, reasons = scorer.should_enter_long(
            ...     features, regime, chart_window=chart, prev_regime="STRONG_BULL"
            ... )
            >>> if should_enter:
            ...     print(f"LONG Entry: {reasons}")
        """
        return self._evaluate_entry("long", features, regime, chart_window, prev_regime)

    def should_enter_short(
        self,
        features: "FeatureVector",
        regime: "RegimeState",
        chart_window: Any | None = None,
        prev_regime: str | None = None,
    ) -> tuple[bool, float, list[str]]:
        """Prüfe Short Entry via CEL Expression.

        Args:
            features: Current feature vector (indicators, price data)
            regime: Current market regime
            chart_window: Chart window reference (für trigger_regime_analysis())
            prev_regime: Previous/last closed regime (für last_closed_regime())

        Returns:
            Tuple of:
                - should_enter: True wenn Entry Signal, False sonst
                - score: Confidence Score (1.0 wenn true, 0.0 wenn false)
                - reason_codes: Liste von Reason-Codes

        Example:
            >>> should_enter, score, reasons = scorer.should_enter_short(
            ...     features, regime, chart_window=chart, prev_regime="STRONG_BEAR"
            ... )
            >>> if should_enter:
            ...     print(f"SHORT Entry: {reasons}")
        """
        return self._evaluate_entry("short", features, regime, chart_window, prev_regime)

    def _evaluate_entry(
        self,
        side: str,
        features: "FeatureVector",
        regime: "RegimeState",
        chart_window: Any | None = None,
        prev_regime: str | None = None,
    ) -> tuple[bool, float, list[str]]:
        """Evaluiere CEL Expression für Entry.

        Baut Context aus Features + Regime und evaluiert Expression.

        Args:
            side: "long" oder "short"
            features: Feature vector
            regime: Regime state
            chart_window: Chart window reference (für trigger_regime_analysis())
            prev_regime: Previous/last closed regime (für last_closed_regime())

        Returns:
            Tuple (should_enter, score, reason_codes)
        """
        try:
            # 1. Build CEL context from features + regime + chart + prev_regime
            context = self._build_context(side, features, regime, chart_window, prev_regime)

            # 2. Evaluate CEL expression
            # CELEngine.evaluate() does internal caching for performance
            result = self.cel.evaluate(self.config.entry_expression, context, default=False)

            # 3. Convert result to boolean
            should_enter = bool(result)

            # 4. Generate score and reasons
            score = 1.0 if should_enter else 0.0
            reasons = self._generate_reasons(should_enter, side, context)

            logger.debug(
                f"JSON Entry [{side}]: {should_enter} "
                f"(score={score:.2f}, reasons={reasons})"
            )

            return should_enter, score, reasons

        except Exception as e:
            logger.error(
                f"JSON Entry evaluation failed: {e}\n"
                f"Side: {side}, Expression: {self.config.entry_expression[:50]}...",
                exc_info=True,
            )
            return False, 0.0, ["CEL_EVALUATION_ERROR"]

    def _build_context(
        self,
        side: str,
        features: "FeatureVector",
        regime: "RegimeState",
        chart_window: Any | None = None,
        prev_regime: str | None = None,
    ) -> dict[str, Any]:
        """Baut CEL Context aus Features + Regime + Chart + Prev Regime.

        Context-Struktur:
        {
            "side": "long" | "short",
            "close": 49500.0,
            "sma_20": 49000.0,
            "rsi": 28.5,
            "rsi14": {"value": 28.5},  # Nested für Kompatibilität mit CEL Docs
            "adx": 32.0,
            "macd": -0.5,
            "macd_hist": -0.2,
            "bb_pct": 0.35,
            "volume_ratio": 1.2,
            "regime": "TREND_UP",
            "regime_obj": {"regime": "TREND_UP", "strength": 0.8},
            "chart_window": <ChartWindow>,  # Für trigger_regime_analysis()
            "last_closed_candle": {"regime": "STRONG_BULL"}  # Für last_closed_regime()
        }

        Args:
            side: "long" oder "short"
            features: Feature vector mit allen Indicators
            regime: Regime state
            chart_window: Chart window reference (für trigger_regime_analysis())
            prev_regime: Previous/last closed regime string (für last_closed_regime())

        Returns:
            Dict mit CEL Context
        """
        # Helper: Safe get mit fallback auf None
        def get_safe(value: Any, default: Any = None) -> Any:
            return value if value is not None else default

        context = {
            # Meta
            "side": side,

            # Price (flat)
            "close": features.close,
            "open": get_safe(features.open, features.close),
            "high": get_safe(features.high, features.close),
            "low": get_safe(features.low, features.close),
            "volume": get_safe(features.volume, 0.0),

            # Trend Indicators (flat)
            "sma_20": get_safe(features.sma_20),
            "sma_50": get_safe(features.sma_50),
            "ema_12": get_safe(features.ema_12),
            "ema_26": get_safe(features.ema_26),

            # Momentum Indicators (flat)
            "rsi": get_safe(features.rsi_14, 50.0),  # Fallback auf neutral
            "macd": get_safe(features.macd, 0.0),
            "macd_signal": get_safe(features.macd_signal, 0.0),
            "macd_hist": get_safe(features.macd_hist, 0.0),
            "stoch_k": get_safe(features.stoch_k),
            "stoch_d": get_safe(features.stoch_d),
            "cci": get_safe(features.cci),
            "mfi": get_safe(features.mfi),

            # Momentum Indicators (nested für Kompatibilität mit CEL Docs)
            "rsi14": {"value": get_safe(features.rsi_14, 50.0)},
            "adx14": {"value": get_safe(features.adx, 0.0)},
            "macd_obj": {
                "value": get_safe(features.macd, 0.0),
                "signal": get_safe(features.macd_signal, 0.0),
                "histogram": get_safe(features.macd_hist, 0.0),
            },

            # Trend Strength (flat)
            "adx": get_safe(features.adx, 0.0),

            # Volatility (flat)
            "atr": get_safe(features.atr_14, 0.0),
            "bb_pct": get_safe(features.bb_pct, 0.5),
            "bb_width": get_safe(features.bb_width, 0.0),
            "bb_upper": get_safe(features.bb_upper),
            "bb_middle": get_safe(features.bb_middle),
            "bb_lower": get_safe(features.bb_lower),
            "chop": get_safe(features.chop, 50.0),

            # Volume (flat)
            "volume_ratio": get_safe(features.volume_ratio, 1.0),

            # Regime (flat + nested)
            "regime": regime.regime.value,  # "TREND_UP", "RANGE", "TREND_DOWN", etc.
            "regime_obj": {
                "regime": regime.regime.value,
                "confidence": regime.regime_confidence,
                "strength": getattr(regime, "regime_strength", 0.0),
                "volatility": regime.volatility.value,
            },

            # Volatility (flat aus Regime)
            "volatility": regime.volatility.value,

            # Chart Window Reference (für CEL trigger_regime_analysis())
            "chart_window": chart_window,

            # Last Closed Candle mit Regime (für CEL last_closed_regime())
            "last_closed_candle": (
                {"regime": prev_regime} if prev_regime else None
            ),
        }

        # Debug: Log context chart_window
        logger.info(f"Context built: chart_window={type(chart_window).__name__ if chart_window else 'None'}")
        print(f"[JSON_SCORER] Context built, keys: {list(context.keys())}", flush=True)
        print(f"[JSON_SCORER] chart_window in context: {'chart_window' in context}", flush=True)
        if 'chart_window' in context and context['chart_window']:
            print(f"[JSON_SCORER] chart_window type: {type(context['chart_window']).__name__}", flush=True)
        else:
            print(f"[JSON_SCORER] ❌ chart_window is None or missing!", flush=True)

        return context

    def _generate_reasons(
        self, should_enter: bool, side: str, context: dict
    ) -> list[str]:
        """Generiere Reason-Codes basierend auf Context.

        Analysiert Context-Werte und generiert aussagekräftige Reason-Codes.

        Args:
            should_enter: Entry-Entscheidung
            side: "long" oder "short"
            context: CEL Context

        Returns:
            Liste von Reason-Codes (z.B. ["JSON_CEL_ENTRY", "RSI_OVERSOLD"])

        Reason Codes:
            - JSON_CEL_ENTRY: Base reason für JSON-basierte Entry
            - RSI_OVERSOLD / RSI_OVERBOUGHT: RSI extreme
            - MACD_BULLISH / MACD_BEARISH: MACD Histogram
            - STRONG_TREND: ADX > 25
            - TREND_REGIME / RANGE_REGIME: Regime-basiert
            - BB_REVERSAL: Bollinger Band extreme
        """
        if not should_enter:
            return []

        reasons = ["JSON_CEL_ENTRY"]  # Base reason

        # RSI-basierte Reasons
        rsi = context.get("rsi", 50)
        if rsi < 30:
            reasons.append("RSI_OVERSOLD")
        elif rsi > 70:
            reasons.append("RSI_OVERBOUGHT")

        # MACD-basierte Reasons
        macd_hist = context.get("macd_hist", 0)
        if macd_hist > 0:
            reasons.append("MACD_BULLISH")
        elif macd_hist < 0:
            reasons.append("MACD_BEARISH")

        # ADX-basierte Reasons (Trend Strength)
        adx = context.get("adx", 0)
        if adx > 25:
            reasons.append("STRONG_TREND")
        elif adx < 20:
            reasons.append("WEAK_TREND")

        # Regime-basierte Reasons
        regime = context.get("regime", "")
        if "TREND" in regime:
            reasons.append("TREND_REGIME")
        elif "RANGE" in regime or "RANGING" in regime:
            reasons.append("RANGE_REGIME")

        # Bollinger Band Reasons
        bb_pct = context.get("bb_pct")
        if bb_pct is not None:
            if bb_pct < 0.2:
                reasons.append("BB_LOWER_BAND")
            elif bb_pct > 0.8:
                reasons.append("BB_UPPER_BAND")

        # Side-spezifische Reasons
        if side == "long":
            # Long-spezifische Checks
            close = context.get("close", 0)
            sma_20 = context.get("sma_20")
            if sma_20 and close > sma_20:
                reasons.append("PRICE_ABOVE_SMA20")
        elif side == "short":
            # Short-spezifische Checks
            close = context.get("close", 0)
            sma_20 = context.get("sma_20")
            if sma_20 and close < sma_20:
                reasons.append("PRICE_BELOW_SMA20")

        return reasons

    def get_expression_summary(self) -> str:
        """Gibt kurze Zusammenfassung der Expression zurück.

        Returns:
            String mit Expression (gekürzt auf 100 Zeichen)

        Example:
            >>> print(scorer.get_expression_summary())
            'rsi < 35 && adx > 25 && macd_hist > 0...'
        """
        expr = self.config.entry_expression
        if len(expr) > 100:
            return expr[:97] + "..."
        return expr

    def __str__(self) -> str:
        """String representation für Logging."""
        return (
            f"JsonEntryScorer("
            f"expression='{self.get_expression_summary()}', "
            f"compiled={self._compiled_expr is not None}"
            f")"
        )

    def __repr__(self) -> str:
        """Detailed representation für Debugging."""
        return (
            f"JsonEntryScorer(\n"
            f"  config={self.config},\n"
            f"  compiled_expression={self._compiled_expr is not None}\n"
            f")"
        )
