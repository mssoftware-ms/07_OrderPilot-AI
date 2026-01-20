"""RuleContext Builder for CEL Evaluation.

Converts FeatureVector and Trade state into CEL-compatible context.
"""

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


class RuleContextBuilder:
    """Builds CEL evaluation context from FeatureVector and Trade state.

    Context Structure (RuleContext v1):
    - Market/Regime/Features: tf, regime, direction, open, high, low, close, volume, atrp
    - Indicators: rsi14.value, macd_12_26_9.value, ema34.value, etc.
    - Trade State: trade.direction, trade.entry, trade.stop_loss, trade.profit_pct, etc.
    - Config: cfg.capital, cfg.max_position_size, etc.
    - Derived: bars_since_open, prev_close, daily_pnl_pct, swing_low_5, etc.

    Example:
        context = RuleContextBuilder.build(
            features=feature_vector,
            trade=current_trade,
            config=bot_config,
            timeframe="5m"
        )
        # context ready for CEL evaluation
    """

    @staticmethod
    def build(
        features: Any,  # FeatureVector
        trade: Optional[Any] = None,  # Trade
        config: Optional[dict[str, Any]] = None,
        timeframe: str = "5m",
        additional_context: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Build CEL context from feature vector and trade state.

        Args:
            features: FeatureVector with market data and indicators
            trade: Optional current Trade object
            config: Optional bot configuration
            timeframe: Timeframe string (e.g., "5m", "1h")
            additional_context: Optional additional context variables

        Returns:
            CEL-compatible context dict

        Example:
            context = RuleContextBuilder.build(
                features=feature_vector,
                trade=current_trade,
                config={"capital": 10000.0}
            )
        """
        context: dict[str, Any] = {}

        # 1. Timeframe
        context["tf"] = timeframe

        # 2. Market Data (from FeatureVector)
        if features:
            context["regime"] = getattr(features, "regime", "UNKNOWN")
            context["direction"] = getattr(features, "direction", "NONE")
            context["open"] = float(getattr(features, "open", 0.0))
            context["high"] = float(getattr(features, "high", 0.0))
            context["low"] = float(getattr(features, "low", 0.0))
            context["close"] = float(getattr(features, "close", 0.0))
            context["volume"] = float(getattr(features, "volume", 0.0))
            context["atrp"] = float(getattr(features, "atrp", 0.0))

            # 3. Indicators (extracted from FeatureVector)
            # Format: indicator_id → {value: X, signal: Y, ...}
            context.update(
                RuleContextBuilder._extract_indicators(features)
            )

            # 4. Derived Values
            context["prev_close"] = float(
                getattr(features, "prev_close", context["close"])
            )
            context["bars_since_open"] = int(
                getattr(features, "bars_since_open", 0)
            )

        # 5. Trade State (if trade exists)
        if trade:
            context["trade"] = {
                "direction": getattr(trade, "direction", "NONE"),
                "entry": float(getattr(trade, "entry_price", 0.0)),
                "stop_loss": float(getattr(trade, "stop_loss", 0.0)),
                "target": float(getattr(trade, "take_profit", 0.0)),
                "position_value": float(getattr(trade, "position_value", 0.0)),
                "profit_pct": float(getattr(trade, "profit_pct", 0.0)),
                "bars_held": int(getattr(trade, "bars_held", 0)),
            }
        else:
            context["trade"] = None

        # 6. Config (bot configuration)
        if config:
            context["cfg"] = {
                "capital": float(config.get("capital", 10000.0)),
                "max_position_size": float(config.get("max_position_size", 0.2)),
                "max_risk_per_trade": float(config.get("max_risk_per_trade", 0.01)),
            }
        else:
            context["cfg"] = {
                "capital": 10000.0,
                "max_position_size": 0.2,
                "max_risk_per_trade": 0.01,
            }

        # 7. Additional Context (user-provided)
        if additional_context:
            context.update(additional_context)

        logger.debug(
            f"Built RuleContext with {len(context)} top-level keys: "
            f"{list(context.keys())}"
        )

        return context

    @staticmethod
    def _extract_indicators(features: Any) -> dict[str, Any]:
        """Extract indicator values from FeatureVector.

        Args:
            features: FeatureVector with indicator values

        Returns:
            Dict mapping indicator_id → {value: X, ...}

        Example:
            indicators = _extract_indicators(features)
            # {"rsi14": {"value": 28.5}, "macd_12_26_9": {"value": 0.5, "signal": 0.3, "histogram": 0.2}}
        """
        indicators = {}

        # RSI
        if hasattr(features, "rsi") and features.rsi is not None:
            indicators["rsi14"] = {"value": float(features.rsi)}

        # MACD
        if hasattr(features, "macd") and features.macd is not None:
            indicators["macd_12_26_9"] = {
                "value": float(features.macd),
                "signal": float(getattr(features, "macd_signal", 0.0)),
                "histogram": float(getattr(features, "macd_histogram", 0.0)),
            }

        # ADX
        if hasattr(features, "adx") and features.adx is not None:
            indicators["adx14"] = {"value": float(features.adx)}

        # ATR
        if hasattr(features, "atr") and features.atr is not None:
            indicators["atr14"] = {"value": float(features.atr)}

        # EMAs
        if hasattr(features, "ema_34") and features.ema_34 is not None:
            indicators["ema34"] = {"value": float(features.ema_34)}

        if hasattr(features, "ema_89") and features.ema_89 is not None:
            indicators["ema89"] = {"value": float(features.ema_89)}

        # SMAs
        if hasattr(features, "sma_50") and features.sma_50 is not None:
            indicators["sma50"] = {"value": float(features.sma_50)}

        if hasattr(features, "sma_200") and features.sma_200 is not None:
            indicators["sma200"] = {"value": float(features.sma_200)}

        # Volume SMA
        if hasattr(features, "volume_sma") and features.volume_sma is not None:
            indicators["volume_sma_20"] = {"value": float(features.volume_sma)}

        # Bollinger Bands
        if hasattr(features, "bb_upper") and features.bb_upper is not None:
            indicators["bb_20_2"] = {
                "upper": float(features.bb_upper),
                "middle": float(getattr(features, "bb_middle", 0.0)),
                "lower": float(getattr(features, "bb_lower", 0.0)),
                "width": float(getattr(features, "bb_width", 0.0)),
            }

        # Stochastic
        if hasattr(features, "stoch_k") and features.stoch_k is not None:
            indicators["stoch_14_3_3"] = {
                "k": float(features.stoch_k),
                "d": float(getattr(features, "stoch_d", 0.0)),
            }

        # CCI
        if hasattr(features, "cci") and features.cci is not None:
            indicators["cci20"] = {"value": float(features.cci)}

        # MFI
        if hasattr(features, "mfi") and features.mfi is not None:
            indicators["mfi14"] = {"value": float(features.mfi)}

        logger.debug(f"Extracted {len(indicators)} indicators from FeatureVector")

        return indicators

    @staticmethod
    def build_minimal(
        close: float,
        indicators: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Build minimal context for testing.

        Args:
            close: Current close price
            indicators: Optional indicator dict

        Returns:
            Minimal CEL context

        Example:
            context = RuleContextBuilder.build_minimal(
                close=100.0,
                indicators={"rsi14": {"value": 30.0}}
            )
        """
        context = {
            "tf": "test",
            "regime": "UNKNOWN",
            "direction": "NONE",
            "open": close,
            "high": close,
            "low": close,
            "close": close,
            "volume": 0.0,
            "atrp": 0.0,
            "trade": None,
            "cfg": {
                "capital": 10000.0,
                "max_position_size": 0.2,
                "max_risk_per_trade": 0.01,
            },
        }

        if indicators:
            context.update(indicators)

        return context
