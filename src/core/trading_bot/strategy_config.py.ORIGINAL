"""
Strategy Configuration - Lädt und verarbeitet JSON-basierte Trading-Strategien

Ermöglicht Optimierungen ohne Code-Änderungen:
- Entry/Exit Bedingungen
- Indikator-Parameter
- Risk Management
- Timing
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

import pandas as pd

logger = logging.getLogger(__name__)


# Default config path
DEFAULT_CONFIG_PATH = Path("config/trading_bot/strategy_config.json")


@dataclass
class TimeframeConfig:
    """Konfiguration für einen Timeframe."""

    interval: str
    source: Literal["alpaca", "bitunix"]
    lookback_bars: int
    update_interval_minutes: int
    purpose: str


@dataclass
class IndicatorConfig:
    """Konfiguration für einen Indikator."""

    enabled: bool
    params: dict[str, Any]


@dataclass
class ConditionRule:
    """Regel für eine Bedingung."""

    id: str
    name: str
    condition_type: str
    enabled: bool
    weight: int
    rule: dict[str, Any]
    description: str


@dataclass
class EntryConditions:
    """Entry-Bedingungen für eine Richtung."""

    min_confluence: int
    max_confluence: int
    conditions: list[ConditionRule]

    def get_enabled_conditions(self) -> list[ConditionRule]:
        """Gibt nur aktivierte Bedingungen zurück."""
        return [c for c in self.conditions if c.enabled]


@dataclass
class ExitConfig:
    """Exit-Konfiguration."""

    stop_loss: dict[str, Any]
    take_profit: dict[str, Any]
    trailing_stop: dict[str, Any]
    signal_reversal: dict[str, Any]
    rsi_extreme: dict[str, Any]
    session_end: dict[str, Any]


@dataclass
class RiskConfig:
    """Risiko-Konfiguration."""

    max_position_risk_percent: float
    max_daily_loss_percent: float
    max_position_size_btc: float
    leverage: int
    single_position_only: bool


@dataclass
class AIValidationConfig:
    """
    AI-Validation Konfiguration mit hierarchischer Validierung.

    WICHTIG: Provider und Model werden aus QSettings geladen!
             Einstellbar über: File -> Settings -> AI
             KEINE hardcodierten Modelle!
    """

    enabled: bool
    confidence_threshold: int  # Backwards compatibility
    confidence_threshold_trade: int  # >= Trade ausführen
    confidence_threshold_deep: int  # >= Deep Analysis
    deep_analysis_enabled: bool
    fallback_to_technical: bool
    timeout_seconds: int
    min_confluence_for_ai: int  # KOSTENOPTIMIERUNG: AI nur bei starken Signalen


@dataclass
class FilterConfig:
    """Filter-Konfiguration."""

    volume: dict[str, Any]
    spread: dict[str, Any]
    volatility: dict[str, Any]


class StrategyConfig:
    """
    Lädt und verwaltet Trading-Strategie aus JSON-Datei.

    Ermöglicht flexible Konfiguration ohne Code-Änderungen.
    """

    def __init__(self, config_path: Path | str | None = None):
        """
        Args:
            config_path: Pfad zur JSON-Konfigurationsdatei
        """
        self.config_path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH
        self._raw_config: dict = {}
        self._load_config()

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

    @property
    def strategy_name(self) -> str:
        """Name der Strategie."""
        return self._raw_config.get("strategy", {}).get("name", "Unknown Strategy")

    @property
    def symbol(self) -> str:
        """Trading Symbol."""
        return self._raw_config.get("strategy", {}).get("symbol", "BTCUSDT")

    @property
    def enabled(self) -> bool:
        """Strategie aktiviert?"""
        return self._raw_config.get("strategy", {}).get("enabled", True)

    # === TIMEFRAMES ===

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

    # === INDICATORS ===

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

    # === ENTRY CONDITIONS ===

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

    # === EXIT CONDITIONS ===

    @property
    def exit_config(self) -> ExitConfig:
        """Exit-Konfiguration."""
        exit_data = self._raw_config.get("exit_conditions", {})
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
        risk_data = self._raw_config.get("risk_management", {})
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
        ai_data = self._raw_config.get("ai_validation", {})
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
        filter_data = self._raw_config.get("filters", {})
        return FilterConfig(
            volume=filter_data.get("volume", {}),
            spread=filter_data.get("spread", {}),
            volatility=filter_data.get("volatility", {}),
        )

    # === TIMING ===

    @property
    def analysis_interval_seconds(self) -> int:
        """Analyse-Intervall in Sekunden."""
        return self._raw_config.get("timing", {}).get("analysis_interval_seconds", 60)

    @property
    def position_check_interval_ms(self) -> int:
        """Position-Check Intervall in Millisekunden."""
        return self._raw_config.get("timing", {}).get("position_check_interval_ms", 1000)

    # === CONDITION EVALUATION ===

    def evaluate_condition(
        self, condition: ConditionRule, data: pd.Series, regime: str | None = None
    ) -> tuple[bool, str]:
        """
        Evaluiert eine einzelne Bedingung.

        Args:
            condition: Die zu evaluierende Bedingung
            data: Aktuelle Marktdaten (letzte Zeile des DataFrame)
            regime: Aktuelles Market Regime

        Returns:
            Tuple (condition_met, description)
        """
        if not condition.enabled:
            return False, "Condition disabled"

        rule = condition.rule

        try:
            if condition.condition_type == "regime":
                return self._eval_regime(rule, regime)

            elif condition.condition_type == "indicator_comparison":
                return self._eval_comparison(rule, data)

            elif condition.condition_type == "indicator_range":
                return self._eval_range(rule, data)

            elif condition.condition_type == "indicator_threshold":
                return self._eval_threshold(rule, data)

            else:
                logger.warning(f"Unknown condition type: {condition.condition_type}")
                return False, f"Unknown type: {condition.condition_type}"

        except Exception as e:
            logger.error(f"Error evaluating condition {condition.id}: {e}")
            return False, f"Error: {str(e)}"

    def _eval_regime(
        self, rule: dict, regime: str | None
    ) -> tuple[bool, str]:
        """Evaluiert Regime-Bedingung."""
        if regime is None:
            return True, "No regime data"

        not_in = rule.get("not_in", [])
        must_be = rule.get("must_be", [])

        regime_upper = regime.upper()

        if not_in:
            for forbidden in not_in:
                if forbidden.upper() in regime_upper:
                    return False, f"Regime {regime} is forbidden"
            return True, f"Regime {regime} is acceptable"

        if must_be:
            for required in must_be:
                if required.upper() in regime_upper:
                    return True, f"Regime {regime} matches requirement"
            return False, f"Regime {regime} doesn't match requirements"

        return True, "No regime constraints"

    def _eval_comparison(
        self, rule: dict, data: pd.Series
    ) -> tuple[bool, str]:
        """Evaluiert Vergleichs-Bedingung."""
        conditions = rule.get("conditions", [])
        logic = rule.get("logic", "AND")

        results = []
        details = []

        for cond in conditions:
            left_name = cond.get("left", "")
            operator = cond.get("operator", "")
            right_name = cond.get("right", "")

            left_val = self._get_value(left_name, data)
            right_val = self._get_value(right_name, data)

            if left_val is None or right_val is None:
                results.append(False)
                details.append(f"{left_name} or {right_name} not available")
                continue

            result = self._compare(left_val, operator, right_val)
            results.append(result)
            details.append(
                f"{left_name}({left_val:.2f}) {operator} {right_name}({right_val:.2f}) = {result}"
            )

        if logic == "AND":
            final = all(results)
        elif logic == "OR":
            final = any(results)
        else:
            final = all(results)

        return final, "; ".join(details)

    def _eval_range(
        self, rule: dict, data: pd.Series
    ) -> tuple[bool, str]:
        """Evaluiert Bereichs-Bedingung."""
        indicator = rule.get("indicator", "")
        min_val = rule.get("min", float("-inf"))
        max_val = rule.get("max", float("inf"))

        value = self._get_value(indicator, data)

        if value is None:
            return False, f"{indicator} not available"

        in_range = min_val <= value <= max_val
        return in_range, f"{indicator}={value:.2f} (range: {min_val}-{max_val})"

    def _eval_threshold(
        self, rule: dict, data: pd.Series
    ) -> tuple[bool, str]:
        """Evaluiert Schwellwert-Bedingung."""
        indicator = rule.get("indicator", "")
        operator = rule.get("operator", ">")
        threshold = rule.get("threshold", 0)

        value = self._get_value(indicator, data)

        if value is None:
            return False, f"{indicator} not available"

        result = self._compare(value, operator, threshold)
        return result, f"{indicator}={value:.2f} {operator} {threshold}"

    def _get_value(self, name: str, data: pd.Series) -> float | None:
        """Holt Wert aus Daten (mit verschiedenen Namenskonventionen)."""
        if name == "price":
            return data.get("close")

        # Versuche verschiedene Namenskonventionen
        variations = [
            name,
            name.lower(),
            name.upper(),
            name.replace("_", ""),
            f"{name}_14",  # z.B. rsi -> rsi_14
            f"{name.upper()}_14",
        ]

        for var in variations:
            val = data.get(var)
            if val is not None:
                return float(val)

        return None

    def _compare(self, left: float, operator: str, right: float) -> bool:
        """Führt Vergleich durch."""
        ops = {
            ">": lambda a, b: a > b,
            ">=": lambda a, b: a >= b,
            "<": lambda a, b: a < b,
            "<=": lambda a, b: a <= b,
            "==": lambda a, b: abs(a - b) < 0.0001,
            "!=": lambda a, b: abs(a - b) >= 0.0001,
        }
        return ops.get(operator, lambda a, b: False)(left, right)

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
