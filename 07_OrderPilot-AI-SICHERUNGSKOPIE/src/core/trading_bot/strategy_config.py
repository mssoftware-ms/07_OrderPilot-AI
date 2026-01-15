"""Strategy Configuration - Lädt und verarbeitet JSON-basierte Trading-Strategien (REFACTORED).

Ermöglicht Optimierungen ohne Code-Änderungen:
- Entry/Exit Bedingungen
- Indikator-Parameter
- Risk Management
- Timing

Module 4/4 of strategy_config.py split - Main Orchestrator
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import pandas as pd

from .strategy_config_dataclasses import (
    ConditionRule,
    EntryConditions,
    IndicatorConfig,
    TimeframeConfig,
)
from .strategy_config_evaluation import StrategyConfigEvaluation
from .strategy_config_properties import StrategyConfigProperties

logger = logging.getLogger(__name__)

# Default config path
DEFAULT_CONFIG_PATH = Path("config/trading_bot/strategy_config.json")


class StrategyConfig:
    """
    Lädt und verwaltet Trading-Strategie aus JSON-Datei (REFACTORED).

    Ermöglicht flexible Konfiguration ohne Code-Änderungen.
    Delegiert an Helper-Klassen:
    - StrategyConfigProperties: Alle @property methods
    - StrategyConfigEvaluation: Condition evaluation
    """

    def __init__(self, config_path: Path | str | None = None):
        """
        Args:
            config_path: Pfad zur JSON-Konfigurationsdatei
        """
        self.config_path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH
        self._raw_config: dict = {}
        self._load_config()

        # Composition pattern - Helper-Klassen
        self._properties = StrategyConfigProperties(parent=self)
        self._evaluation = StrategyConfigEvaluation(parent=self)

    def _load_config(self) -> None:
        """Lädt Konfiguration aus JSON-Datei."""
        if not self.config_path.exists():
            logger.warning(
                f"Config file not found: {self.config_path}. Using defaults."
            )
            self._raw_config = self._get_default_config()
            return

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                self._raw_config = json.load(f)
            logger.info(f"Loaded strategy config from {self.config_path}")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse config JSON: {e}")
            self._raw_config = self._get_default_config()
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            self._raw_config = self._get_default_config()

    def reload(self) -> None:
        """Lädt Konfiguration neu (für Hot-Reload)."""
        self._load_config()
        logger.info("Strategy config reloaded")

    def save(self, path: Path | str | None = None) -> None:
        """Speichert aktuelle Konfiguration."""
        save_path = Path(path) if path else self.config_path
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(self._raw_config, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved strategy config to {save_path}")

    # =========================================================================
    # PROPERTIES (delegiert an StrategyConfigProperties)
    # =========================================================================

    @property
    def strategy_name(self) -> str:
        """Name der Strategie."""
        return self._properties.strategy_name

    @property
    def symbol(self) -> str:
        """Trading Symbol."""
        return self._properties.symbol

    @property
    def enabled(self) -> bool:
        """Strategie aktiviert?"""
        return self._properties.enabled

    @property
    def exit_config(self):
        """Exit-Konfiguration."""
        return self._properties.exit_config

    @property
    def sl_type(self) -> str:
        """Stop Loss Type."""
        return self._properties.sl_type

    @property
    def sl_atr_multiplier(self) -> float:
        """Stop Loss ATR Multiplier."""
        return self._properties.sl_atr_multiplier

    @property
    def sl_percent(self) -> float:
        """Stop Loss Prozent."""
        return self._properties.sl_percent

    @property
    def tp_type(self) -> str:
        """Take Profit Type."""
        return self._properties.tp_type

    @property
    def tp_atr_multiplier(self) -> float:
        """Take Profit ATR Multiplier."""
        return self._properties.tp_atr_multiplier

    @property
    def tp_percent(self) -> float:
        """Take Profit Prozent."""
        return self._properties.tp_percent

    @property
    def trailing_stop_enabled(self) -> bool:
        """Trailing Stop aktiviert?"""
        return self._properties.trailing_stop_enabled

    @property
    def trailing_stop_type(self) -> str:
        """Trailing Stop Type."""
        return self._properties.trailing_stop_type

    @property
    def trailing_stop_atr_multiplier(self) -> float:
        """Trailing Stop ATR Multiplier."""
        return self._properties.trailing_stop_atr_multiplier

    @property
    def trailing_stop_percent(self) -> float:
        """Trailing Stop Prozent."""
        return self._properties.trailing_stop_percent

    @property
    def trailing_stop_activation_percent(self) -> float:
        """Trailing Stop Aktivierung."""
        return self._properties.trailing_stop_activation_percent

    @property
    def risk_config(self):
        """Risiko-Konfiguration."""
        return self._properties.risk_config

    @property
    def ai_config(self):
        """AI-Validation Konfiguration."""
        return self._properties.ai_config

    @property
    def filters(self):
        """Filter-Konfiguration."""
        return self._properties.filters

    @property
    def analysis_interval_seconds(self) -> int:
        """Analyse-Intervall."""
        return self._properties.analysis_interval_seconds

    @property
    def position_check_interval_ms(self) -> int:
        """Position-Check Intervall."""
        return self._properties.position_check_interval_ms

    # =========================================================================
    # TIMEFRAMES
    # =========================================================================

    def get_timeframe(self, role: str) -> TimeframeConfig | None:
        """Gibt Timeframe-Config für Rolle zurück (macro, trend, context, execution)."""
        tf_data = self._raw_config.get("timeframes", {}).get(role)
        if not tf_data:
            return None

        return TimeframeConfig(
            interval=tf_data.get("interval", "5m"),
            source=tf_data.get("source", "bitunix"),
            lookback_bars=tf_data.get("lookback_bars", 200),
            update_interval_minutes=tf_data.get("update_interval_minutes", 5),
            purpose=tf_data.get("purpose", ""),
        )

    @property
    def all_timeframes(self) -> dict[str, TimeframeConfig]:
        """Alle Timeframe-Konfigurationen."""
        result = {}
        for role in ["macro", "trend", "context", "execution"]:
            tf = self.get_timeframe(role)
            if tf:
                result[role] = tf
        return result

    # =========================================================================
    # INDICATORS
    # =========================================================================

    def get_indicator_config(self, name: str) -> IndicatorConfig | None:
        """Gibt Indikator-Konfiguration zurück."""
        ind_data = self._raw_config.get("indicators", {}).get(name)
        if not ind_data:
            return None

        enabled = ind_data.pop("enabled", True)
        return IndicatorConfig(enabled=enabled, params=ind_data)

    @property
    def enabled_indicators(self) -> list[str]:
        """Liste aktivierter Indikatoren."""
        indicators = self._raw_config.get("indicators", {})
        return [
            name for name, config in indicators.items() if config.get("enabled", True)
        ]

    def update_indicator_config(
        self,
        indicator_updates: dict[str, Any],
        save: bool = True,
    ) -> None:
        """Update indicator configuration with new parameters.

        Used by Strategy Bridge to apply simulator-optimized parameters.

        Args:
            indicator_updates: Dict with indicator params to update
                Format: {"rsi_period": 14, "adx_threshold": 25, ...}
            save: Whether to save config to file after update
        """
        if "indicators" not in self._raw_config:
            self._raw_config["indicators"] = {}

        indicators = self._raw_config["indicators"]

        # Map parameter names to indicator sections
        param_to_indicator = {
            "rsi_period": "rsi",
            "rsi_oversold": "rsi",
            "rsi_overbought": "rsi",
            "adx_period": "adx",
            "adx_threshold": "adx",
            "bb_period": "bollinger",
            "bb_std": "bollinger",
            "macd_fast": "macd",
            "macd_slow": "macd",
            "macd_signal": "macd",
            "atr_period": "atr",
            "sma_fast": "sma",
            "sma_slow": "sma",
            "ema_period": "ema",
            "volume_ratio": "volume",
        }

        for param_name, param_value in indicator_updates.items():
            indicator_name = param_to_indicator.get(param_name)

            if indicator_name:
                # Update specific indicator section
                if indicator_name not in indicators:
                    indicators[indicator_name] = {"enabled": True}
                indicators[indicator_name][param_name] = param_value
            else:
                # Store in general config
                self._raw_config.setdefault("bridged_params", {})[param_name] = param_value

        logger.info(f"Updated indicator config: {indicator_updates}")

        if save:
            self.save()
            logger.info("Saved updated indicator config to file")

    # =========================================================================
    # ENTRY CONDITIONS
    # =========================================================================

    def get_entry_conditions(self, direction: str) -> EntryConditions:
        """
        Gibt Entry-Bedingungen für Richtung zurück.

        Args:
            direction: "long" oder "short"
        """
        entry_data = self._raw_config.get("entry_conditions", {}).get(direction, {})

        conditions = []
        for cond_data in entry_data.get("conditions", []):
            conditions.append(
                ConditionRule(
                    id=cond_data.get("id", "unknown"),
                    name=cond_data.get("name", "Unknown"),
                    condition_type=cond_data.get("type", "unknown"),
                    enabled=cond_data.get("enabled", True),
                    weight=cond_data.get("weight", 1),
                    rule=cond_data.get("rule", {}),
                    description=cond_data.get("description", ""),
                )
            )

        return EntryConditions(
            min_confluence=entry_data.get("min_confluence", 3),
            max_confluence=entry_data.get("max_confluence", 5),
            conditions=conditions,
        )

    @property
    def min_confluence_long(self) -> int:
        """Minimum Confluence für Long Entry."""
        return self.get_entry_conditions("long").min_confluence

    @property
    def min_confluence_short(self) -> int:
        """Minimum Confluence für Short Entry."""
        return self.get_entry_conditions("short").min_confluence

    # =========================================================================
    # CONDITION EVALUATION (delegiert an StrategyConfigEvaluation)
    # =========================================================================

    def evaluate_condition(
        self, condition: ConditionRule, data: pd.Series, regime: str | None = None
    ) -> tuple[bool, str]:
        """Evaluiert eine einzelne Bedingung."""
        return self._evaluation.evaluate_condition(condition, data, regime)

    # =========================================================================
    # UTILITY METHODS
    # =========================================================================

    def _get_default_config(self) -> dict:
        """Gibt Default-Konfiguration zurück wenn keine Datei vorhanden."""
        return {
            "strategy": {"name": "Default", "symbol": "BTCUSDT", "enabled": True},
            "entry_conditions": {
                "long": {"min_confluence": 3, "conditions": []},
                "short": {"min_confluence": 3, "conditions": []},
            },
            "exit_conditions": {
                "stop_loss": {"enabled": True, "atr_multiplier": 1.5},
                "take_profit": {"enabled": True, "atr_multiplier": 2.0},
                "trailing_stop": {"enabled": True, "atr_multiplier": 1.0},
            },
            "risk_management": {
                "max_position_risk_percent": 1.0,
                "leverage": 10,
            },
            "timing": {
                "analysis_interval_seconds": 60,
            },
        }

    def to_dict(self) -> dict:
        """Gibt gesamte Konfiguration als Dictionary zurück."""
        return self._raw_config.copy()

    def update_parameter(self, path: str, value: Any) -> None:
        """
        Aktualisiert einen Parameter.

        Args:
            path: Pfad zum Parameter (z.B. "entry_conditions.long.min_confluence")
            value: Neuer Wert
        """
        parts = path.split(".")
        current = self._raw_config

        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]

        current[parts[-1]] = value
        logger.info(f"Updated config parameter: {path} = {value}")


# Singleton-Instanz für globalen Zugriff
_strategy_config: StrategyConfig | None = None


def get_strategy_config(config_path: Path | str | None = None) -> StrategyConfig:
    """
    Gibt Singleton-Instanz der StrategyConfig zurück.

    Args:
        config_path: Optional Pfad zur Konfigurationsdatei

    Returns:
        StrategyConfig Instanz
    """
    global _strategy_config

    if _strategy_config is None or config_path:
        _strategy_config = StrategyConfig(config_path)

    return _strategy_config


__all__ = ["StrategyConfig", "get_strategy_config"]
