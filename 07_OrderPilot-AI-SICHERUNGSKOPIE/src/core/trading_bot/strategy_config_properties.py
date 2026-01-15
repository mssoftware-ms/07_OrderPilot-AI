"""Strategy Config - Property Methods.

Refactored from strategy_config.py monolith.

Module 2/4 of strategy_config.py split.

Contains:
- All @property methods for config access
- Basic properties (name, symbol, enabled)
- Exit config properties (SL, TP, trailing)
- Risk config property
- AI config property
- Filter config property
- Timing properties
"""

from __future__ import annotations

from .strategy_config_dataclasses import (
    AIValidationConfig,
    ExitConfig,
    FilterConfig,
    RiskConfig,
)


class StrategyConfigProperties:
    """Helper für StrategyConfig @property methods."""

    def __init__(self, parent):
        """
        Args:
            parent: StrategyConfig Instanz
        """
        self.parent = parent

    # === BASIC PROPERTIES ===

    @property
    def strategy_name(self) -> str:
        """Name der Strategie."""
        return self.parent._raw_config.get("strategy", {}).get("name", "Unknown Strategy")

    @property
    def symbol(self) -> str:
        """Trading Symbol."""
        return self.parent._raw_config.get("strategy", {}).get("symbol", "BTCUSDT")

    @property
    def enabled(self) -> bool:
        """Strategie aktiviert?"""
        return self.parent._raw_config.get("strategy", {}).get("enabled", True)

    # === EXIT CONFIG PROPERTIES ===

    @property
    def exit_config(self) -> ExitConfig:
        """Exit-Konfiguration."""
        exit_data = self.parent._raw_config.get("exit_conditions", {})
        return ExitConfig(
            stop_loss=exit_data.get("stop_loss", {}),
            take_profit=exit_data.get("take_profit", {}),
            trailing_stop=exit_data.get("trailing_stop", {}),
            signal_reversal=exit_data.get("signal_reversal", {}),
            rsi_extreme=exit_data.get("rsi_extreme", {}),
            session_end=exit_data.get("session_end", {}),
        )

    @property
    def sl_type(self) -> str:
        """Stop Loss Type: 'atr_based' oder 'percent_based'."""
        return self.exit_config.stop_loss.get("type", "atr_based")

    @property
    def sl_atr_multiplier(self) -> float:
        """Stop Loss ATR Multiplier (nur für atr_based)."""
        return self.exit_config.stop_loss.get("atr_multiplier", 1.5)

    @property
    def sl_percent(self) -> float:
        """Stop Loss Prozent vom Entry (nur für percent_based)."""
        return self.exit_config.stop_loss.get("percent", 0.5)

    @property
    def tp_type(self) -> str:
        """Take Profit Type: 'atr_based' oder 'percent_based'."""
        return self.exit_config.take_profit.get("type", "atr_based")

    @property
    def tp_atr_multiplier(self) -> float:
        """Take Profit ATR Multiplier (nur für atr_based)."""
        return self.exit_config.take_profit.get("atr_multiplier", 2.0)

    @property
    def tp_percent(self) -> float:
        """Take Profit Prozent vom Entry (nur für percent_based)."""
        return self.exit_config.take_profit.get("percent", 1.0)

    @property
    def trailing_stop_enabled(self) -> bool:
        """Trailing Stop aktiviert?"""
        return self.exit_config.trailing_stop.get("enabled", True)

    @property
    def trailing_stop_type(self) -> str:
        """Trailing Stop Type."""
        return self.exit_config.trailing_stop.get("type", "atr_based")

    @property
    def trailing_stop_atr_multiplier(self) -> float:
        """Trailing Stop ATR Multiplier."""
        return self.exit_config.trailing_stop.get("atr_multiplier", 1.0)

    @property
    def trailing_stop_percent(self) -> float:
        """Trailing Stop Prozent Abstand (für percent_based)."""
        return self.exit_config.trailing_stop.get("trail_percent", 0.3)

    @property
    def trailing_stop_activation_percent(self) -> float:
        """Trailing Stop Aktivierungsschwelle in Prozent."""
        return self.exit_config.trailing_stop.get("activation_percent", 0.5)

    # === RISK MANAGEMENT ===

    @property
    def risk_config(self) -> RiskConfig:
        """Risiko-Konfiguration."""
        risk_data = self.parent._raw_config.get("risk_management", {})
        return RiskConfig(
            max_position_risk_percent=risk_data.get("max_position_risk_percent", 1.0),
            max_daily_loss_percent=risk_data.get("max_daily_loss_percent", 3.0),
            max_position_size_btc=risk_data.get("max_position_size_btc", 0.1),
            leverage=risk_data.get("leverage", 10),
            single_position_only=risk_data.get("single_position_only", True),
        )

    # === AI VALIDATION ===

    @property
    def ai_config(self) -> AIValidationConfig:
        """
        AI-Validation Konfiguration.

        WICHTIG: Provider und Model kommen aus QSettings (File -> Settings -> AI)!
        """
        ai_data = self.parent._raw_config.get("ai_validation", {})
        return AIValidationConfig(
            enabled=ai_data.get("enabled", False),  # Default FALSE für Kostenersparnis!
            confidence_threshold=ai_data.get("confidence_threshold_trade", ai_data.get("confidence_threshold", 70)),
            confidence_threshold_trade=ai_data.get("confidence_threshold_trade", 70),
            confidence_threshold_deep=ai_data.get("confidence_threshold_deep", 50),
            deep_analysis_enabled=ai_data.get("deep_analysis_enabled", True),
            fallback_to_technical=ai_data.get("fallback_to_technical", True),
            timeout_seconds=ai_data.get("timeout_seconds", 30),
            min_confluence_for_ai=ai_data.get("min_confluence_for_ai", 4),
        )

    # === FILTERS ===

    @property
    def filters(self) -> FilterConfig:
        """Filter-Konfiguration."""
        filter_data = self.parent._raw_config.get("filters", {})
        return FilterConfig(
            volume=filter_data.get("volume", {}),
            spread=filter_data.get("spread", {}),
            volatility=filter_data.get("volatility", {}),
        )

    # === TIMING ===

    @property
    def analysis_interval_seconds(self) -> int:
        """Analyse-Intervall in Sekunden."""
        return self.parent._raw_config.get("timing", {}).get("analysis_interval_seconds", 60)

    @property
    def position_check_interval_ms(self) -> int:
        """Position-Check Intervall in Millisekunden."""
        return self.parent._raw_config.get("timing", {}).get("position_check_interval_ms", 1000)
