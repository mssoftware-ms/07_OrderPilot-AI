"""
Backtesting Configuration Validator V2

Validiert BacktestConfigV2 Konfigurationen:
- Schema-Validierung mit JSON Schema
- Semantische Validierung (Weights summe, Ranges, etc.)
- Conditional Evaluation
- Constraint Checking
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .config_v2 import (
    BacktestConfigV2,
    WeightPreset,
    DEFAULT_WEIGHT_PRESETS
)

logger = logging.getLogger(__name__)


# VALIDATION RESULT
@dataclass
class ValidationError:
    """Ein einzelner Validierungsfehler."""
    path: str          # JSON-Pfad zum fehlerhaften Feld
    message: str       # Fehlerbeschreibung
    severity: str      # "error" oder "warning"
    value: Any = None  # Der fehlerhafte Wert

    def __str__(self) -> str:
        return f"[{self.severity.upper()}] {self.path}: {self.message}"


@dataclass
class ValidationResult:
    """Ergebnis einer Validierung."""
    valid: bool
    errors: List[ValidationError]
    warnings: List[ValidationError]

    @property
    def has_errors(self) -> bool:
        return len(self.errors) > 0

    @property
    def has_warnings(self) -> bool:
        return len(self.warnings) > 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "valid": self.valid,
            "errors": [{"path": e.path, "message": e.message, "value": e.value} for e in self.errors],
            "warnings": [{"path": w.path, "message": w.message, "value": w.value} for w in self.warnings]
        }

    def __str__(self) -> str:
        lines = [f"Validation {'PASSED' if self.valid else 'FAILED'}"]
        if self.errors:
            lines.append(f"  Errors ({len(self.errors)}):")
            for e in self.errors:
                lines.append(f"    - {e}")
        if self.warnings:
            lines.append(f"  Warnings ({len(self.warnings)}):")
            for w in self.warnings:
                lines.append(f"    - {w}")
        return "\n".join(lines)


# VALIDATOR CLASS
class ConfigValidator:
    """Validator fuer BacktestConfigV2."""

    def __init__(self, schema_path: Optional[Path] = None):
        """
        Initialisiert den Validator.

        Args:
            schema_path: Pfad zur JSON Schema Datei (optional)
        """
        self.schema_path = schema_path or Path("config/schemas/backtest_config_v2.schema.json")
        self._schema: Optional[Dict[str, Any]] = None

    def _load_schema(self) -> Optional[Dict[str, Any]]:
        """Laedt das JSON Schema."""
        if self._schema is not None:
            return self._schema

        if not self.schema_path.exists():
            logger.warning(f"Schema file not found: {self.schema_path}")
            return None

        try:
            with open(self.schema_path, "r", encoding="utf-8") as f:
                self._schema = json.load(f)
            return self._schema
        except Exception as e:
            logger.error(f"Failed to load schema: {e}")
            return None

    def validate(self, config: BacktestConfigV2) -> ValidationResult:
        """
        Fuehrt vollstaendige Validierung durch.

        Args:
            config: Zu validierende Konfiguration

        Returns:
            ValidationResult mit Fehlern und Warnungen
        """
        errors: List[ValidationError] = []
        warnings: List[ValidationError] = []

        # 1. Strukturelle Validierung
        struct_errors, struct_warnings = self._validate_structure(config)
        errors.extend(struct_errors)
        warnings.extend(struct_warnings)

        # 2. Semantische Validierung
        sem_errors, sem_warnings = self._validate_semantics(config)
        errors.extend(sem_errors)
        warnings.extend(sem_warnings)

        # 3. Range-Validierung
        range_errors, range_warnings = self._validate_ranges(config)
        errors.extend(range_errors)
        warnings.extend(range_warnings)

        # 4. Constraint-Validierung
        constraint_errors, constraint_warnings = self._validate_constraints(config)
        errors.extend(constraint_errors)
        warnings.extend(constraint_warnings)

        # 5. Conditional-Evaluation
        cond_errors, cond_warnings = self._validate_conditionals(config)
        errors.extend(cond_errors)
        warnings.extend(cond_warnings)

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

    def _validate_structure(self, config: BacktestConfigV2) -> Tuple[List[ValidationError], List[ValidationError]]:
        """Validiert Grundstruktur."""
        errors = []
        warnings = []

        # Meta validieren
        if not config.meta.name:
            errors.append(ValidationError(
                path="meta.name",
                message="Name ist erforderlich",
                severity="error"
            ))

        # Version validieren
        if not config.version.startswith("2."):
            warnings.append(ValidationError(
                path="version",
                message=f"Version {config.version} ist nicht V2.x",
                severity="warning",
                value=config.version
            ))

        return errors, warnings

    def _validate_semantics(self, config: BacktestConfigV2) -> Tuple[List[ValidationError], List[ValidationError]]:
        """Validiert semantische Regeln."""
        errors = []
        warnings = []

        # 1. Weight-Validierung
        if config.constraints.weights_must_sum_to_one:
            weights = config.entry_score.get_weights()
            if not weights.validate():
                total = weights.trend + weights.rsi + weights.macd + weights.adx + weights.vol + weights.volume
                errors.append(ValidationError(
                    path="entry_score.weights",
                    message=f"Weights summieren zu {total:.2f}, erwartet: 1.0",
                    severity="error",
                    value=total
                ))

        # 2. SL < TP (bei gleichen Typen)
        sl_mult = config.exit_management.stop_loss.atr_multiplier.value
        tp_mult = config.exit_management.take_profit.atr_multiplier.value

        if config.exit_management.stop_loss.type == config.exit_management.take_profit.type:
            if sl_mult >= tp_mult:
                warnings.append(ValidationError(
                    path="exit_management",
                    message=f"SL ({sl_mult}) >= TP ({tp_mult}) - Risk:Reward negativ",
                    severity="warning",
                    value={"sl": sl_mult, "tp": tp_mult}
                ))

        # 3. Trailing Activation < Distance
        if config.exit_management.trailing_stop.enabled:
            act = config.exit_management.trailing_stop.activation_atr.value
            dist = config.exit_management.trailing_stop.distance_atr.value
            if dist >= act:
                warnings.append(ValidationError(
                    path="exit_management.trailing_stop",
                    message=f"Trailing distance ({dist}) >= activation ({act})",
                    severity="warning"
                ))

        # 4. Leverage < Max Leverage
        base_lev = config.risk_leverage.base_leverage.value
        max_lev = config.risk_leverage.max_leverage
        if base_lev > max_lev:
            errors.append(ValidationError(
                path="risk_leverage",
                message=f"base_leverage ({base_lev}) > max_leverage ({max_lev})",
                severity="error"
            ))

        # 5. Liquidation Distance bei hohem Leverage
        if base_lev >= 20 and config.risk_leverage.min_liquidation_distance_pct < 5.0:
            warnings.append(ValidationError(
                path="risk_leverage.min_liquidation_distance_pct",
                message=f"Bei Leverage {base_lev}x sollte min_liquidation_distance >= 5% sein",
                severity="warning"
            ))

        return errors, warnings

    def _validate_ranges(self, config: BacktestConfigV2) -> Tuple[List[ValidationError], List[ValidationError]]:
        """Validiert Optimierungs-Ranges."""
        errors = []
        warnings = []

        # Sammle alle optimierbaren Parameter
        optimizable = [
            ("entry_score.min_score_for_entry", config.entry_score.min_score_for_entry, 0.0, 1.0),
            ("exit_management.stop_loss.atr_multiplier", config.exit_management.stop_loss.atr_multiplier, 0.1, 10.0),
            ("exit_management.take_profit.atr_multiplier", config.exit_management.take_profit.atr_multiplier, 0.1, 10.0),
            ("exit_management.trailing_stop.activation_atr", config.exit_management.trailing_stop.activation_atr, 0.0, 5.0),
            ("exit_management.trailing_stop.distance_atr", config.exit_management.trailing_stop.distance_atr, 0.0, 3.0),
            ("risk_leverage.risk_per_trade_pct", config.risk_leverage.risk_per_trade_pct, 0.0, 100.0),
        ]

        for path, param, min_val, max_val in optimizable:
            # Wert im gueltigen Bereich?
            if not (min_val <= param.value <= max_val):
                errors.append(ValidationError(
                    path=path,
                    message=f"Wert {param.value} ausserhalb [{min_val}, {max_val}]",
                    severity="error",
                    value=param.value
                ))

            # Range-Werte im gueltigen Bereich?
            if param.optimize and param.range:
                for v in param.range:
                    if not (min_val <= v <= max_val):
                        errors.append(ValidationError(
                            path=f"{path}.range",
                            message=f"Range-Wert {v} ausserhalb [{min_val}, {max_val}]",
                            severity="error",
                            value=v
                        ))

        # Integer-Ranges
        base_lev = config.risk_leverage.base_leverage
        if base_lev.optimize and base_lev.range:
            for v in base_lev.range:
                if v > config.risk_leverage.max_leverage:
                    errors.append(ValidationError(
                        path="risk_leverage.base_leverage.range",
                        message=f"Range-Wert {v} > max_leverage ({config.risk_leverage.max_leverage})",
                        severity="error",
                        value=v
                    ))

        return errors, warnings

    def _validate_constraints(self, config: BacktestConfigV2) -> Tuple[List[ValidationError], List[ValidationError]]:
        """Validiert Constraints-Sektion."""
        errors = []
        warnings = []

        c = config.constraints

        # Sinnvolle Constraint-Werte
        if c.min_trades < 10:
            warnings.append(ValidationError(
                path="constraints.min_trades",
                message=f"min_trades={c.min_trades} ist sehr niedrig, statistisch wenig aussagekraeftig",
                severity="warning"
            ))

        if c.max_drawdown_pct > 50:
            warnings.append(ValidationError(
                path="constraints.max_drawdown_pct",
                message=f"max_drawdown_pct={c.max_drawdown_pct}% ist sehr hoch",
                severity="warning"
            ))

        if c.min_win_rate > 0.80:
            warnings.append(ValidationError(
                path="constraints.min_win_rate",
                message=f"min_win_rate={c.min_win_rate} ist unrealistisch hoch",
                severity="warning"
            ))

        return errors, warnings

    def _validate_conditionals(self, config: BacktestConfigV2) -> Tuple[List[ValidationError], List[ValidationError]]:
        """Validiert Conditional-Definitionen."""
        errors = []
        warnings = []

        for i, cond in enumerate(config.conditionals):
            if not cond.condition:
                errors.append(ValidationError(
                    path=f"conditionals[{i}].if",
                    message="Leere Bedingung",
                    severity="error"
                ))
            if not cond.actions:
                errors.append(ValidationError(
                    path=f"conditionals[{i}].then",
                    message="Leere Aktionen",
                    severity="error"
                ))

        return errors, warnings

    def validate_file(self, path: Path) -> ValidationResult:
        """
        Validiert eine JSON-Datei.

        Args:
            path: Pfad zur JSON-Datei

        Returns:
            ValidationResult
        """
        try:
            config = BacktestConfigV2.load(path)
            return self.validate(config)
        except json.JSONDecodeError as e:
            return ValidationResult(
                valid=False,
                errors=[ValidationError(
                    path="<file>",
                    message=f"JSON Parse Error: {e}",
                    severity="error"
                )],
                warnings=[]
            )
        except Exception as e:
            return ValidationResult(
                valid=False,
                errors=[ValidationError(
                    path="<file>",
                    message=f"Load Error: {e}",
                    severity="error"
                )],
                warnings=[]
            )


# CONDITIONAL EVALUATOR
class ConditionalEvaluator:
    """Evaluiert und wendet Conditionals auf Konfigurationen an."""

    @staticmethod
    def evaluate_condition(config: BacktestConfigV2, condition: Dict[str, Any]) -> bool:
        """
        Evaluiert eine Bedingung gegen die Konfiguration.

        Args:
            config: Aktuelle Konfiguration
            condition: Bedingungs-Dictionary

        Returns:
            True wenn Bedingung erfuellt
        """
        config_dict = config.to_dict()

        for path, expected in condition.items():
            value = ConditionalEvaluator._get_nested_value(config_dict, path)

            if value is None:
                return False

            if isinstance(expected, dict):
                # Vergleichsoperatoren
                if ">=" in expected:
                    if not (value >= expected[">="]):
                        return False
                elif "<=" in expected:
                    if not (value <= expected["<="]):
                        return False
                elif ">" in expected:
                    if not (value > expected[">"]):
                        return False
                elif "<" in expected:
                    if not (value < expected["<"]):
                        return False
                elif "==" in expected:
                    if value != expected["=="]:
                        return False
                elif "!=" in expected:
                    if value == expected["!="]:
                        return False
                elif "in" in expected:
                    if value not in expected["in"]:
                        return False
            else:
                # Direkter Vergleich
                if value != expected:
                    return False

        return True

    @staticmethod
    def apply_actions(config_dict: Dict[str, Any], actions: Dict[str, Any]) -> Dict[str, Any]:
        """
        Wendet Aktionen auf ein Config-Dictionary an.

        Args:
            config_dict: Konfiguration als Dictionary
            actions: Aktionen als {path: value}

        Returns:
            Modifiziertes Dictionary
        """
        for path, value in actions.items():
            ConditionalEvaluator._set_nested_value(config_dict, path, value)
        return config_dict

    @staticmethod
    def _get_nested_value(data: Dict[str, Any], path: str) -> Any:
        """Holt einen Wert aus verschachteltem Dictionary."""
        keys = path.split(".")
        current = data
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        return current

    @staticmethod
    def _set_nested_value(data: Dict[str, Any], path: str, value: Any) -> None:
        """Setzt einen Wert in verschachteltem Dictionary."""
        keys = path.split(".")
        current = data
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        current[keys[-1]] = value

    @classmethod
    def process_conditionals(cls, config: BacktestConfigV2) -> BacktestConfigV2:
        """
        Evaluiert und wendet alle Conditionals an.

        Args:
            config: Urspruengliche Konfiguration

        Returns:
            Modifizierte Konfiguration
        """
        if not config.conditionals:
            return config

        config_dict = config.to_dict()

        for cond in config.conditionals:
            if cls.evaluate_condition(config, cond.condition):
                logger.debug(f"Applying conditional: {cond.condition}")
                config_dict = cls.apply_actions(config_dict, cond.actions)

        return BacktestConfigV2.from_dict(config_dict)


# CONVENIENCE FUNCTIONS
def validate_config(config: BacktestConfigV2) -> ValidationResult:
    """Schnelle Validierung einer Konfiguration."""
    validator = ConfigValidator()
    return validator.validate(config)


def validate_config_file(path: Path) -> ValidationResult:
    """Schnelle Validierung einer JSON-Datei."""
    validator = ConfigValidator()
    return validator.validate_file(path)


def apply_conditionals(config: BacktestConfigV2) -> BacktestConfigV2:
    """Wendet alle Conditionals auf eine Konfiguration an."""
    return ConditionalEvaluator.process_conditionals(config)
