"""Regime Configuration Loader for v2.0 Format.

Loads and validates JSON regime configuration files (Entry Analyzer output)
against the optimized_regime_config_v2.schema.json.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import jsonschema

logger = logging.getLogger(__name__)

DEFAULT_SCHEMA_PATH = Path("config/schemas/regime_optimization/optimized_regime_config_v2.schema.json")


class RegimeConfigLoadError(Exception):
    """Exception raised when regime config loading fails."""
    pass


def _prune_nones(data: Any) -> Any:
    """Remove None-valued keys from dictionaries recursively."""
    if isinstance(data, dict):
        return {key: _prune_nones(value) for key, value in data.items() if value is not None}
    if isinstance(data, list):
        return [_prune_nones(value) for value in data]
    return data


class RegimeConfigLoaderV2:
    """Loads and validates v2.0 Regime configuration files.

    Designed for Entry Analyzer Regime optimization results.
    Uses optimized_regime_config_v2.schema.json for validation.

    Example:
        >>> loader = RegimeConfigLoaderV2()
        >>> config = loader.load_config("03_JSON/Entry_Analyzer/Regime/260125_regime.json")
        >>> print(config["schema_version"])
        '2.0.0'
        >>> print(len(config["optimization_results"]))
        1
    """

    def __init__(self, schema_path: Path | str | None = None):
        """Initialize RegimeConfigLoaderV2 with JSON Schema.

        Args:
            schema_path: Path to optimized_regime_config_v2.schema.json.
                        Uses default if None.

        Raises:
            RegimeConfigLoadError: If schema file cannot be loaded
        """
        if schema_path is None:
            schema_path = DEFAULT_SCHEMA_PATH
        self.schema_path = Path(schema_path)
        self.schema = self._load_schema()

    def _load_schema(self) -> dict[str, Any]:
        """Load JSON Schema from file.

        Returns:
            Parsed JSON Schema

        Raises:
            RegimeConfigLoadError: If schema file is missing or invalid
        """
        if not self.schema_path.exists():
            raise RegimeConfigLoadError(
                f"JSON Schema not found: {self.schema_path}. "
                f"Schema should be in config/schemas/regime_optimization/"
            )

        try:
            with open(self.schema_path, "r", encoding="utf-8") as f:
                schema = json.load(f)
            logger.info(f"Loaded JSON Schema from {self.schema_path}")
            return schema
        except json.JSONDecodeError as e:
            raise RegimeConfigLoadError(
                f"Invalid JSON in schema file {self.schema_path}: {e}"
            ) from e
        except Exception as e:
            raise RegimeConfigLoadError(
                f"Failed to load schema {self.schema_path}: {e}"
            ) from e

    def load_config(self, config_path: Path | str) -> dict[str, Any]:
        """Load and validate v2.0 regime configuration from JSON file.

        Performs JSON Schema validation (Draft 2020-12).

        Args:
            config_path: Path to JSON config file (v2.0 format)

        Returns:
            Validated configuration dict with structure:
            {
                "schema_version": "2.0.0",
                "metadata": {...},
                "optimization_results": [
                    {
                        "timestamp": "...",
                        "score": 85.5,
                        "trial_number": 1,
                        "applied": true,
                        "indicators": [...],
                        "regimes": [...]
                    }
                ]
            }

            Note: entry_params and evaluation_params are deprecated.
            Only entry_expression (CEL) is used for Trading Bot execution.

        Raises:
            RegimeConfigLoadError: If validation fails
        """
        config_path = Path(config_path)

        # Stage 1: Load JSON
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config_data = json.load(f)
            logger.info(f"Loaded JSON from {config_path}")
        except FileNotFoundError:
            raise RegimeConfigLoadError(
                f"Config file not found: {config_path}"
            )
        except json.JSONDecodeError as e:
            raise RegimeConfigLoadError(
                f"Invalid JSON in {config_path}: {e}"
            ) from e

        config_data = _prune_nones(config_data)

        # Stage 2: Validate schema_version
        schema_version = config_data.get("schema_version")
        if schema_version != "2.0.0":
            raise RegimeConfigLoadError(
                f"Invalid schema version: '{schema_version}'. "
                f"This loader only supports v2.0.0 format. "
                f"File: {config_path}"
            )

        # Stage 3: JSON Schema validation
        try:
            jsonschema.validate(instance=config_data, schema=self.schema)
            logger.debug(f"JSON Schema validation passed for {config_path}")
        except jsonschema.ValidationError as e:
            # Extract better error message
            path_str = ".".join(str(p) for p in e.path) if e.path else "root"
            raise RegimeConfigLoadError(
                f"JSON Schema validation failed for {config_path}: "
                f"{e.message} at {path_str}"
            ) from e
        except jsonschema.SchemaError as e:
            raise RegimeConfigLoadError(
                f"Invalid JSON Schema definition: {e}"
            ) from e

        # Log successful load
        num_results = len(config_data.get("optimization_results", []))
        num_indicators = 0
        num_regimes = 0

        if num_results > 0:
            first_result = config_data["optimization_results"][0]
            num_indicators = len(first_result.get("indicators", []))
            num_regimes = len(first_result.get("regimes", []))

        logger.info(
            f"Successfully loaded v2.0 regime config from {config_path}: "
            f"{num_results} optimization results, "
            f"{num_indicators} indicators, "
            f"{num_regimes} regimes"
        )

        return config_data

    def validate_config_data(self, config_data: dict[str, Any]) -> dict[str, Any]:
        """Validate raw config dict (without file I/O).

        Useful for testing or programmatic config generation.

        Args:
            config_data: Raw configuration dictionary

        Returns:
            Validated configuration dict

        Raises:
            RegimeConfigLoadError: If validation fails
        """
        config_data = _prune_nones(config_data)

        # Validate schema_version
        schema_version = config_data.get("schema_version")
        if schema_version != "2.0.0":
            raise RegimeConfigLoadError(
                f"Invalid schema version: '{schema_version}'. "
                f"Expected '2.0.0'"
            )

        # JSON Schema validation
        try:
            jsonschema.validate(instance=config_data, schema=self.schema)
            logger.debug("Config data validation passed")
        except jsonschema.ValidationError as e:
            path_str = ".".join(str(p) for p in e.path) if e.path else "root"
            raise RegimeConfigLoadError(
                f"JSON Schema validation failed: {e.message} at {path_str}"
            ) from e

        return config_data

    def save_config(
        self,
        config_data: dict[str, Any],
        output_path: Path | str,
        indent: int = 2,
        validate: bool = True
    ) -> None:
        """Save configuration to JSON file.

        Args:
            config_data: Config dict to save
            output_path: Target JSON file path
            indent: JSON indentation (default: 2)
            validate: Validate before saving (default: True)

        Raises:
            RegimeConfigLoadError: If validation fails or file write fails
        """
        output_path = Path(output_path)

        # Optional validation before saving
        if validate:
            try:
                self.validate_config_data(config_data)
                logger.debug("Pre-save validation passed")
            except RegimeConfigLoadError as e:
                raise RegimeConfigLoadError(
                    f"Config validation failed before save: {e}"
                ) from e

        # Save to file
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=indent, ensure_ascii=False)
            logger.info(f"Saved v2.0 regime config to {output_path}")
        except Exception as e:
            raise RegimeConfigLoadError(
                f"Failed to write config to {output_path}: {e}"
            ) from e

    def get_applied_result(self, config_data: dict[str, Any]) -> dict[str, Any] | None:
        """Get the currently applied optimization result.

        Args:
            config_data: Loaded config dict

        Returns:
            The optimization result with applied=true, or None if none found
        """
        for result in config_data.get("optimization_results", []):
            if result.get("applied", False):
                return result
        return None

    def get_indicators(self, config_data: dict[str, Any]) -> list[dict[str, Any]]:
        """Get indicators from the applied optimization result.

        Args:
            config_data: Loaded config dict

        Returns:
            List of indicator dicts, or empty list if no applied result
        """
        applied = self.get_applied_result(config_data)
        if applied:
            return applied.get("indicators", [])
        return []

    def get_regimes(self, config_data: dict[str, Any]) -> list[dict[str, Any]]:
        """Get regimes from the applied optimization result.

        Args:
            config_data: Loaded config dict

        Returns:
            List of regime dicts, or empty list if no applied result
        """
        applied = self.get_applied_result(config_data)
        if applied:
            return applied.get("regimes", [])
        return []
