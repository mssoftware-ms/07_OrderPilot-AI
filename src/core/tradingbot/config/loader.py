"""Configuration Loader for JSON Strategy Configs.

Loads and validates JSON configuration files against the JSON Schema
and converts them to type-safe Pydantic models.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import jsonschema
from pydantic import ValidationError

from .models import TradingBotConfig

logger = logging.getLogger(__name__)


class ConfigLoadError(Exception):
    """Exception raised when config loading fails."""
    pass


class ConfigLoader:
    """Loads and validates JSON strategy configurations.

    Provides two-stage validation:
    1. JSON Schema validation (structure + types)
    2. Pydantic model validation (business logic)

    Example:
        >>> loader = ConfigLoader(schema_path="03_JSON/schema/strategy_config_schema.json")
        >>> config = loader.load_config("03_JSON/Trading_Bot/configs/production.json")
        >>> print(config.schema_version)
        '1.0'
    """

    def __init__(self, schema_path: Path | str):
        """Initialize ConfigLoader with JSON Schema.

        Args:
            schema_path: Path to strategy_config_schema.json

        Raises:
            ConfigLoadError: If schema file cannot be loaded
        """
        self.schema_path = Path(schema_path)
        self.schema = self._load_schema()

    def _load_schema(self) -> dict[str, Any]:
        """Load JSON Schema from file.

        Returns:
            Parsed JSON Schema

        Raises:
            ConfigLoadError: If schema file is missing or invalid
        """
        if not self.schema_path.exists():
            raise ConfigLoadError(
                f"JSON Schema not found: {self.schema_path}. "
                f"Run Phase 0 setup to create schema file."
            )

        try:
            with open(self.schema_path, "r", encoding="utf-8") as f:
                schema = json.load(f)
            logger.info(f"Loaded JSON Schema from {self.schema_path}")
            return schema
        except json.JSONDecodeError as e:
            raise ConfigLoadError(
                f"Invalid JSON in schema file {self.schema_path}: {e}"
            ) from e
        except Exception as e:
            raise ConfigLoadError(
                f"Failed to load schema {self.schema_path}: {e}"
            ) from e

    def load_config(self, config_path: Path | str) -> TradingBotConfig:
        """Load and validate configuration from JSON file.

        Performs two-stage validation:
        1. JSON Schema validation (Draft 2020-12)
        2. Pydantic model validation

        Args:
            config_path: Path to JSON config file

        Returns:
            Validated TradingBotConfig instance

        Raises:
            ConfigLoadError: If validation fails at any stage
        """
        config_path = Path(config_path)

        # Stage 1: Load JSON
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config_data = json.load(f)
            logger.debug(f"Loaded JSON from {config_path}")
        except FileNotFoundError:
            raise ConfigLoadError(
                f"Config file not found: {config_path}"
            )
        except json.JSONDecodeError as e:
            raise ConfigLoadError(
                f"Invalid JSON in {config_path}: {e}"
            ) from e

        # Stage 2: JSON Schema validation
        try:
            jsonschema.validate(instance=config_data, schema=self.schema)
            logger.debug(f"JSON Schema validation passed for {config_path}")
        except jsonschema.ValidationError as e:
            raise ConfigLoadError(
                f"JSON Schema validation failed for {config_path}: "
                f"{e.message} at {'.'.join(str(p) for p in e.path)}"
            ) from e
        except jsonschema.SchemaError as e:
            raise ConfigLoadError(
                f"Invalid JSON Schema definition: {e}"
            ) from e

        # Stage 3: Pydantic model validation
        try:
            config = TradingBotConfig(**config_data)
            logger.info(
                f"Successfully loaded config from {config_path}: "
                f"{len(config.indicators)} indicators, "
                f"{len(config.regimes)} regimes, "
                f"{len(config.strategies)} strategies"
            )
            return config
        except ValidationError as e:
            # Extract clearer error messages from Pydantic
            errors = []
            for error in e.errors():
                loc = " -> ".join(str(x) for x in error["loc"])
                msg = error["msg"]
                errors.append(f"{loc}: {msg}")

            raise ConfigLoadError(
                f"Pydantic validation failed for {config_path}:\n" +
                "\n".join(f"  - {err}" for err in errors)
            ) from e

    def validate_config_data(self, config_data: dict[str, Any]) -> TradingBotConfig:
        """Validate raw config dict (without file I/O).

        Useful for testing or programmatic config generation.

        Args:
            config_data: Raw configuration dictionary

        Returns:
            Validated TradingBotConfig instance

        Raises:
            ConfigLoadError: If validation fails
        """
        # JSON Schema validation
        try:
            jsonschema.validate(instance=config_data, schema=self.schema)
        except jsonschema.ValidationError as e:
            raise ConfigLoadError(
                f"JSON Schema validation failed: {e.message}"
            ) from e

        # Pydantic validation
        try:
            return TradingBotConfig(**config_data)
        except ValidationError as e:
            errors = [
                f"{' -> '.join(str(x) for x in err['loc'])}: {err['msg']}"
                for err in e.errors()
            ]
            raise ConfigLoadError(
                "Pydantic validation failed:\n" +
                "\n".join(f"  - {err}" for err in errors)
            ) from e

    def list_configs(self, directory: Path | str) -> list[Path]:
        """List all JSON config files in directory.

        Args:
            directory: Path to config directory

        Returns:
            List of .json file paths

        Raises:
            ConfigLoadError: If directory doesn't exist
        """
        directory = Path(directory)
        if not directory.exists():
            raise ConfigLoadError(f"Config directory not found: {directory}")

        if not directory.is_dir():
            raise ConfigLoadError(f"Not a directory: {directory}")

        json_files = sorted(directory.glob("*.json"))
        logger.debug(f"Found {len(json_files)} JSON files in {directory}")
        return json_files

    def load_all_configs(self, directory: Path | str) -> dict[str, TradingBotConfig]:
        """Load all valid configs from directory.

        Skips invalid configs and logs errors, but doesn't raise.

        Args:
            directory: Path to config directory

        Returns:
            Dict mapping filename -> TradingBotConfig

        Raises:
            ConfigLoadError: If directory doesn't exist
        """
        configs = {}
        for config_path in self.list_configs(directory):
            try:
                config = self.load_config(config_path)
                configs[config_path.name] = config
            except ConfigLoadError as e:
                logger.error(f"Skipping invalid config {config_path.name}: {e}")

        logger.info(f"Loaded {len(configs)} valid configs from {directory}")
        return configs

    def save_config(
        self,
        config: TradingBotConfig,
        output_path: Path | str,
        indent: int = 2,
        validate: bool = True
    ) -> None:
        """Save configuration to JSON file.

        Args:
            config: TradingBotConfig instance to save
            output_path: Target JSON file path
            indent: JSON indentation (default: 2)
            validate: Validate before saving (default: True)

        Raises:
            ConfigLoadError: If validation fails or file write fails
        """
        output_path = Path(output_path)

        # Optional validation before saving
        if validate:
            try:
                # Convert to dict, validate against schema
                config_dict = config.model_dump(mode="json", exclude_none=True)
                jsonschema.validate(instance=config_dict, schema=self.schema)
                logger.debug("Pre-save validation passed")
            except jsonschema.ValidationError as e:
                raise ConfigLoadError(
                    f"Config validation failed before save: {e.message}"
                ) from e

        # Save to file
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            config_json = config.model_dump_json(
                indent=indent,
                exclude_none=True
            )
            output_path.write_text(config_json, encoding="utf-8")
            logger.info(f"Saved config to {output_path}")
        except Exception as e:
            raise ConfigLoadError(
                f"Failed to write config to {output_path}: {e}"
            ) from e
