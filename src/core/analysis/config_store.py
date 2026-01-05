"""Configuration store for AI Analysis strategies and presets.

Provides default configurations for Scalping, Daytrading, and Swingtrading.
"""

from .models import AnalysisStrategyConfig, TimeframeConfig, IndicatorPreset, IndicatorSpec

class AnalysisConfigStore:
    """Static store for analysis configurations."""

    @staticmethod
    def get_default_strategies() -> list[AnalysisStrategyConfig]:
        """Returns the list of built-in strategy configurations."""
        return [
            AnalysisStrategyConfig(
                name="Scalping",
                description="Short-term trading (1m-5m execution). Requires Range or specific Trend conditions.",
                allowed_regimes=["RANGE", "NEUTRAL", "TREND_BULL", "TREND_BEAR"], # Permissive for now, but UI will warn
                indicator_preset_id="scalping_default",
                timeframes=[
                    TimeframeConfig(role="EXECUTION", tf="1m", lookback=1440), # 24h
                    TimeframeConfig(role="CONTEXT", tf="5m", lookback=2000),   # ~7d
                    TimeframeConfig(role="TREND", tf="1h", lookback=720),      # ~30d
                    TimeframeConfig(role="MACRO", tf="1D", lookback=365),      # ~1y
                ]
            ),
            AnalysisStrategyConfig(
                name="Daytrading",
                description="Intraday moves (5m-15m execution). Best in clear trends or defined ranges.",
                allowed_regimes=["TREND_BULL", "TREND_BEAR", "RANGE"],
                indicator_preset_id="daytrading_default",
                timeframes=[
                    TimeframeConfig(role="EXECUTION", tf="5m", lookback=2000),
                    TimeframeConfig(role="CONTEXT", tf="1h", lookback=1000),
                    TimeframeConfig(role="TREND", tf="4h", lookback=500),
                    TimeframeConfig(role="MACRO", tf="1D", lookback=365),
                ]
            ),
            AnalysisStrategyConfig(
                name="Swingtrading",
                description="Multi-day holds (4h-1D execution). Requires strong trend alignment.",
                allowed_regimes=["TREND_BULL", "TREND_BEAR"],
                indicator_preset_id="swing_default",
                timeframes=[
                    TimeframeConfig(role="EXECUTION", tf="4h", lookback=1000),
                    TimeframeConfig(role="CONTEXT", tf="1D", lookback=500),
                    TimeframeConfig(role="TREND", tf="1W", lookback=200),
                    TimeframeConfig(role="MACRO", tf="1M", lookback=60),
                ]
            )
        ]

    @staticmethod
    def get_default_presets() -> list[IndicatorPreset]:
        """Returns the list of built-in indicator presets."""
        return [
            IndicatorPreset(
                preset_id="scalping_default",
                name="Scalping Standard",
                indicators=[
                    IndicatorSpec(name="EMA", params={"period": 9}),
                    IndicatorSpec(name="EMA", params={"period": 21}),
                    IndicatorSpec(name="RSI", params={"period": 14}),
                    IndicatorSpec(name="BB", params={"period": 20, "std_dev": 2}, feature_flags={"bandwidth": True, "percent": True}),
                    IndicatorSpec(name="ATR", params={"period": 14}),
                    IndicatorSpec(name="STOCH", params={"k_period": 14, "d_period": 3, "smooth": 3}),
                    IndicatorSpec(name="ADX", params={"period": 14}),
                ]
            ),
            IndicatorPreset(
                preset_id="daytrading_default",
                name="Daytrading Standard",
                indicators=[
                    IndicatorSpec(name="EMA", params={"period": 20}),
                    IndicatorSpec(name="EMA", params={"period": 50}),
                    IndicatorSpec(name="EMA", params={"period": 200}),
                    IndicatorSpec(name="RSI", params={"period": 14}),
                    IndicatorSpec(name="MACD", params={"fast": 12, "slow": 26, "signal": 9}),
                    IndicatorSpec(name="BB", params={"period": 20, "std_dev": 2}, feature_flags={"bandwidth": True}),
                    IndicatorSpec(name="ATR", params={"period": 14}),
                    IndicatorSpec(name="ADX", params={"period": 14}),
                ]
            ),
            IndicatorPreset(
                preset_id="swing_default",
                name="Swing Standard",
                indicators=[
                    IndicatorSpec(name="EMA", params={"period": 20}),
                    IndicatorSpec(name="EMA", params={"period": 50}),
                    IndicatorSpec(name="EMA", params={"period": 200}),
                    IndicatorSpec(name="RSI", params={"period": 14}),
                    IndicatorSpec(name="MACD", params={"fast": 12, "slow": 26, "signal": 9}),
                    IndicatorSpec(name="ATR", params={"period": 14}),
                    IndicatorSpec(name="ADX", params={"period": 14}),
                ]
            )
        ]
