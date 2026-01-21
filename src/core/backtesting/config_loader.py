"""
Backtesting Configuration Loader V2

Laedt BacktestConfigV2 Konfigurationen mit:
- Extends/Vererbungs-Support (rekursives Laden von Basis-Templates)
- Override-Merging (tiefes Dictionary-Merging)
- Parameter-Gruppen-Expansion
- Conditional-Aufloesung nach dem Laden
"""

from __future__ import annotations

import json
import logging
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from .config_v2 import (
    BacktestConfigV2,
    OptimizableFloat,
    OptimizableInt,
    ParameterGroup,
)
from .config_validator import (
    ConfigValidator,
    ConditionalEvaluator,
    ValidationResult,
)

logger = logging.getLogger(__name__)


# CONFIG LOADER
class ConfigLoader:
    """
    Laedt BacktestConfigV2 Konfigurationen mit Vererbungs-Support.

    Features:
    - Rekursives Laden von Basis-Templates via "extends"
    - Tiefes Merging von Overrides
    - Parameter-Gruppen-Expansion fuer Grid-Search
    - Conditional-Aufloesung
    """

    def __init__(
        self,
        base_path: Optional[Path] = None,
        validate: bool = True,
        resolve_conditionals: bool = True
    ):
        """
        Initialisiert den ConfigLoader.

        Args:
            base_path: Basis-Pfad fuer relative Template-Pfade
            validate: Ob nach dem Laden validiert werden soll
            resolve_conditionals: Ob Conditionals aufgeloest werden sollen
        """
        self.base_path = base_path or Path("config/backtest_templates")
        self.validate = validate
        self.resolve_conditionals = resolve_conditionals
        self.validator = ConfigValidator() if validate else None
        self._loaded_paths: Set[str] = set()  # Zyklus-Detection

    def load(self, path: Union[str, Path]) -> BacktestConfigV2:
        """
        Laedt eine Konfigurationsdatei mit Vererbungs-Support.

        Args:
            path: Pfad zur JSON-Datei

        Returns:
            Vollstaendig geladene und gemergte Konfiguration

        Raises:
            FileNotFoundError: Datei nicht gefunden
            ValueError: Zyklische Vererbung oder ungueltige Konfiguration
        """
        self._loaded_paths.clear()
        config_dict = self._load_with_extends(Path(path))

        # Conditionals aufloesen
        if self.resolve_conditionals:
            config = BacktestConfigV2.from_dict(config_dict)
            config = ConditionalEvaluator.process_conditionals(config)
            config_dict = config.to_dict()

        # Finale Konfiguration erstellen
        config = BacktestConfigV2.from_dict(config_dict)

        # Validierung
        if self.validate and self.validator:
            result = self.validator.validate(config)
            if not result.valid:
                logger.error(f"Configuration validation failed:\n{result}")
                raise ValueError(f"Invalid configuration: {result.errors}")
            if result.has_warnings:
                logger.warning(f"Configuration warnings:\n{result}")

        return config

    def _load_with_extends(self, path: Path) -> Dict[str, Any]:
        """
        Laedt eine Konfiguration rekursiv mit extends-Support.

        Args:
            path: Pfad zur JSON-Datei

        Returns:
            Gemergtes Dictionary
        """
        # Absoluten Pfad bestimmen
        if not path.is_absolute():
            path = self.base_path / path

        path_str = str(path.resolve())

        # Zyklus-Detection
        if path_str in self._loaded_paths:
            raise ValueError(f"Circular inheritance detected: {path_str}")
        self._loaded_paths.add(path_str)

        # Datei laden
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {path}")

        with open(path, "r", encoding="utf-8") as f:
            config_dict = json.load(f)

        logger.debug(f"Loaded configuration: {path}")

        # Extends verarbeiten
        extends_path = config_dict.pop("extends", None)
        overrides = config_dict.pop("overrides", None)

        if extends_path:
            # Basis-Konfiguration laden
            base_path = Path(extends_path)
            if not base_path.is_absolute():
                base_path = path.parent / base_path

            base_dict = self._load_with_extends(base_path)

            # Overrides anwenden (flache Pfade)
            if overrides:
                for override_path, value in overrides.items():
                    self._set_nested_value(base_dict, override_path, value)

            # Aktuelle Konfiguration ueber Basis mergen
            config_dict = self._deep_merge(base_dict, config_dict)

        return config_dict

    @staticmethod
    def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fuehrt tiefes Merging zweier Dictionaries durch.

        Args:
            base: Basis-Dictionary
            override: Override-Dictionary (hat Vorrang)

        Returns:
            Gemergtes Dictionary
        """
        result = deepcopy(base)

        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                # Rekursives Merging fuer verschachtelte Dicts
                result[key] = ConfigLoader._deep_merge(result[key], value)
            else:
                # Direktes Ueberschreiben
                result[key] = deepcopy(value)

        return result

    @staticmethod
    def _set_nested_value(data: Dict[str, Any], path: str, value: Any) -> None:
        """
        Setzt einen Wert in einem verschachtelten Dictionary.

        Args:
            data: Ziel-Dictionary
            path: Pfad wie "section.subsection.key"
            value: Zu setzender Wert
        """
        keys = path.split(".")
        current = data

        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        current[keys[-1]] = value

    @staticmethod
    def _get_nested_value(data: Dict[str, Any], path: str) -> Any:
        """
        Holt einen Wert aus einem verschachtelten Dictionary.

        Args:
            data: Quell-Dictionary
            path: Pfad wie "section.subsection.key"

        Returns:
            Wert oder None wenn nicht gefunden
        """
        keys = path.split(".")
        current = data

        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None

        return current


# PARAMETER GROUP EXPANDER
class ParameterGroupExpander:
    """
    Expandiert Parameter-Gruppen zu Grid-Search-Kombinationen.

    Parameter-Gruppen erlauben es, mehrere Parameter zusammen zu testen
    (z.B. SL und TP als Paare), anstatt alle Kombinationen zu erzeugen.
    """

    @staticmethod
    def expand_groups(config: BacktestConfigV2) -> List[Dict[str, Any]]:
        """
        Expandiert alle Parameter-Gruppen zu Konfigurations-Varianten.

        Args:
            config: Basis-Konfiguration

        Returns:
            Liste von Config-Dictionaries mit expandierten Gruppen
        """
        if not config.parameter_groups:
            return [config.to_dict()]

        base_dict = config.to_dict()
        variants = [base_dict]

        for group in config.parameter_groups:
            new_variants = []

            for variant in variants:
                group_variants = ParameterGroupExpander._expand_single_group(
                    variant, group
                )
                new_variants.extend(group_variants)

            variants = new_variants

        logger.info(f"Expanded {len(config.parameter_groups)} parameter groups "
                   f"to {len(variants)} variants")

        return variants

    @staticmethod
    def _expand_single_group(
        base_dict: Dict[str, Any],
        group: ParameterGroup
    ) -> List[Dict[str, Any]]:
        """
        Expandiert eine einzelne Parameter-Gruppe.

        Args:
            base_dict: Basis-Konfiguration
            group: Zu expandierende Gruppe

        Returns:
            Liste von Varianten
        """
        variants = []

        for combination in group.combinations:
            if len(combination) != len(group.parameters):
                logger.warning(
                    f"Group '{group.name}': combination length mismatch "
                    f"({len(combination)} vs {len(group.parameters)})"
                )
                continue

            variant = deepcopy(base_dict)

            for param_path, value in zip(group.parameters, combination):
                # Wert im verschachtelten Dict setzen
                ConfigLoader._set_nested_value(variant, param_path, value)

            variants.append(variant)

        if not variants:
            return [base_dict]

        return variants


# GRID SPACE GENERATOR
class GridSpaceGenerator:
    """
    Generiert den vollstaendigen Suchraum fuer Optimierung.

    Kombiniert:
    - Optimierbare Parameter (mit optimize=True und range)
    - Parameter-Gruppen-Kombinationen
    """

    @staticmethod
    def generate(config: BacktestConfigV2) -> List[Dict[str, Any]]:
        """
        Generiert alle Konfigurations-Varianten fuer Grid-Search.

        Args:
            config: Basis-Konfiguration

        Returns:
            Liste aller Konfigurations-Varianten
        """
        # 1. Parameter-Gruppen expandieren
        group_variants = ParameterGroupExpander.expand_groups(config)

        # 2. Fuer jede Variante die optimierbaren Parameter expandieren
        all_variants = []

        for variant_dict in group_variants:
            variant_config = BacktestConfigV2.from_dict(variant_dict)
            optimizable = variant_config.get_optimizable_parameters()

            if not optimizable:
                all_variants.append(variant_dict)
                continue

            # Grid ueber alle optimierbaren Parameter
            param_variants = GridSpaceGenerator._expand_optimizable(
                variant_dict, optimizable
            )
            all_variants.extend(param_variants)

        logger.info(f"Generated {len(all_variants)} total grid variants")

        return all_variants

    @staticmethod
    def _expand_optimizable(
        base_dict: Dict[str, Any],
        optimizable: Dict[str, List[Any]]
    ) -> List[Dict[str, Any]]:
        """
        Expandiert optimierbare Parameter zu Grid-Varianten.

        Args:
            base_dict: Basis-Konfiguration
            optimizable: Dict von {path: range_values}

        Returns:
            Liste aller Kombinationen
        """
        if not optimizable:
            return [base_dict]

        # Iterative Expansion (vermeidet tiefe Rekursion)
        variants = [deepcopy(base_dict)]

        for param_path, values in optimizable.items():
            new_variants = []

            for variant in variants:
                for value in values:
                    new_variant = deepcopy(variant)
                    # Setze sowohl .value als auch den direkten Wert
                    GridSpaceGenerator._set_param_value(
                        new_variant, param_path, value
                    )
                    new_variants.append(new_variant)

            variants = new_variants

        return variants

    @staticmethod
    def _set_param_value(
        data: Dict[str, Any],
        path: str,
        value: Any
    ) -> None:
        """
        Setzt einen Parameter-Wert im Config-Dict.

        Handhabt sowohl OptimizableFloat/Int-Strukturen als auch direkte Werte.

        Args:
            data: Config-Dictionary
            path: Pfad zum Parameter
            value: Neuer Wert
        """
        keys = path.split(".")
        current = data

        # Navigiere zum Eltern-Dict
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        final_key = keys[-1]

        # Pruefe ob es ein Optimizable-Dict ist
        if isinstance(current.get(final_key), dict) and "value" in current[final_key]:
            current[final_key]["value"] = value
        else:
            current[final_key] = value


# CONVENIENCE FUNCTIONS
def load_config(
    path: Union[str, Path],
    base_path: Optional[Path] = None,
    validate: bool = True
) -> BacktestConfigV2:
    """
    Schnelles Laden einer Konfigurationsdatei.

    Args:
        path: Pfad zur JSON-Datei
        base_path: Basis-Pfad fuer relative Template-Pfade
        validate: Ob validiert werden soll

    Returns:
        Geladene Konfiguration
    """
    loader = ConfigLoader(base_path=base_path, validate=validate)
    return loader.load(path)


def load_and_expand(
    path: Union[str, Path],
    base_path: Optional[Path] = None
) -> List[BacktestConfigV2]:
    """
    Laedt eine Konfiguration und expandiert alle Varianten.

    Args:
        path: Pfad zur JSON-Datei
        base_path: Basis-Pfad fuer relative Template-Pfade

    Returns:
        Liste aller Konfigurations-Varianten
    """
    loader = ConfigLoader(base_path=base_path, validate=True)
    config = loader.load(path)

    variants_dicts = GridSpaceGenerator.generate(config)

    return [BacktestConfigV2.from_dict(v) for v in variants_dicts]


def count_grid_combinations(config: BacktestConfigV2) -> int:
    """
    Zaehlt die Anzahl der Grid-Kombinationen ohne sie zu generieren.

    Args:
        config: Konfiguration

    Returns:
        Anzahl der Kombinationen
    """
    count = 1

    # Parameter-Gruppen
    for group in config.parameter_groups:
        count *= len(group.combinations)

    # Optimierbare Parameter
    optimizable = config.get_optimizable_parameters()
    for values in optimizable.values():
        count *= len(values)

    return count


def list_templates(
    base_path: Optional[Path] = None,
    pattern: str = "*.json"
) -> List[Path]:
    """
    Listet alle verfuegbaren Template-Dateien.

    Args:
        base_path: Basis-Verzeichnis
        pattern: Glob-Pattern

    Returns:
        Liste der Template-Pfade
    """
    base = base_path or Path("config/backtest_templates")

    if not base.exists():
        return []

    return sorted(base.glob(pattern))


def create_from_preset(
    preset: str,
    overrides: Optional[Dict[str, Any]] = None
) -> BacktestConfigV2:
    """
    Erstellt eine Konfiguration aus einem benannten Preset.

    Args:
        preset: Preset-Name (z.B. "trendfollowing_conservative")
        overrides: Optionale Ueberschreibungen

    Returns:
        Konfiguration
    """
    base_path = Path("config/backtest_templates")
    preset_path = base_path / f"{preset}.json"

    if not preset_path.exists():
        # Versuche mit _v2 Suffix
        preset_path = base_path / f"{preset}_v2.json"

    if not preset_path.exists():
        available = [p.stem for p in list_templates(base_path)]
        raise FileNotFoundError(
            f"Preset '{preset}' not found. Available: {available}"
        )

    loader = ConfigLoader(base_path=base_path, validate=True)
    config = loader.load(preset_path)

    if overrides:
        config_dict = config.to_dict()
        for path, value in overrides.items():
            ConfigLoader._set_nested_value(config_dict, path, value)
        config = BacktestConfigV2.from_dict(config_dict)

    return config
