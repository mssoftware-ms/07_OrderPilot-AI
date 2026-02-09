"""JSON Schema Validator for OrderPilot-AI configs.

Provides schema validation for all JSON-based configurations
using JSON Schema Draft 2020-12.
"""

import json
import logging
from pathlib import Path
from typing import Any

try:
    from jsonschema import Draft202012Validator, ValidationError as JsonSchemaValidationError
    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False
    Draft202012Validator = None
    JsonSchemaValidationError = None

logger = logging.getLogger(__name__)

KIND_TO_SCHEMA: dict[str, str] = {
    "strategy_config": "strategy_config",
    "indicator_set": "indicator_set",
    "regime_optimization_results": "regime_optimization_results",
}


class ValidationError(Exception):
    """Custom validation error with detailed information."""

    def __init__(
        self,
        message: str,
        json_path: str = "",
        schema_rule: str = "",
        original_error: Exception = None
    ):
        super().__init__(message)
        self.message = message
        self.json_path = json_path
        self.schema_rule = schema_rule
        self.original_error = original_error

    def __str__(self) -> str:
        parts = [f"Validation Error: {self.message}"]
        if self.json_path:
            parts.append(f"  JSON Path: {self.json_path}")
        if self.schema_rule:
            parts.append(f"  Schema Rule: {self.schema_rule}")
        return "\n".join(parts)


class SchemaValidator:
    """Validates JSON data against JSON Schema specifications.

    Supports:
    - trading_bot_config
    - rulepack
    - backtest_config

    Example:
        validator = SchemaValidator()
        validator.validate_file("config.json", "trading_bot_config")
    """

    def __init__(self, schemas_dir: Path = None):
        """Initialize validator.

        Args:
            schemas_dir: Directory containing JSON schema files.
                        Defaults to config/schemas/ in project root.
        """
        if not JSONSCHEMA_AVAILABLE:
            raise ImportError(
                "jsonschema library is required for schema validation. "
                "Install with: pip install jsonschema"
            )

        if schemas_dir is None:
            # Default to config/schemas/ relative to project root
            project_root = Path(__file__).parents[4]  # src/core/tradingbot/config/validator.py → root
            schemas_dir = project_root / "schemas"

        self.schemas_dir = schemas_dir
        self._schema_cache: dict[str, dict] = {}

        # Initialize Registry with all schemas in directory
        self._registry = self._build_registry()

        logger.info(f"SchemaValidator initialized with schemas_dir: {self.schemas_dir}")

    def _build_registry(self):
        """Builds a registry of all available schemas."""
        from referencing import Registry, Resource
        registry = Registry()

        if not self.schemas_dir.exists():
             return registry

        for schema_file in self.schemas_dir.rglob("*.json"):
            try:
                with open(schema_file, "r", encoding="utf-8") as f:
                    schema = json.load(f)
                    resource = Resource.from_contents(schema)
                    # Register by filename (e.g. "defs.json") for relative refs
                    registry = registry.with_resource(uri=schema_file.name, resource=resource)
                    # Also register by ID if present
                    if "$id" in schema:
                         registry = registry.with_resource(uri=schema["$id"], resource=resource)
            except Exception as e:
                logger.warning(f"Failed to load schema for registry: {schema_file} - {e}")

        return registry

    def _load_schema(self, schema_name: str) -> dict:
        """Load JSON schema from file.

        Args:
            schema_name: Name of schema (e.g., "trading_bot_config", "rulepack")

        Returns:
            Parsed JSON schema

        Raises:
            FileNotFoundError: If schema file not found
            ValueError: If schema file is invalid JSON
        """
        # Check cache
        if schema_name in self._schema_cache:
            return self._schema_cache[schema_name]

        # Try multiple search paths in order:
        # 1. config/schemas/<schema_name>.schema.json (root level)
        # 2. config/schemas/regime_optimization/<schema_name>.schema.json (subdirectory)
        search_paths = [
            self.schemas_dir / f"{schema_name}.schema.json",
            self.schemas_dir / "regime_optimization" / f"{schema_name}.schema.json"
        ]

        schema_path = None
        for path in search_paths:
            if path.exists():
                schema_path = path
                break

        if schema_path is None:
             # Fallback: check if mapped in KIND_TO_SCHEMA pointing directly to a filename
             pass

        if schema_path is None:
            available_schemas = [
                p.stem.replace(".schema", "")
                for p in self.schemas_dir.rglob("*.schema.json")
            ]
            raise FileNotFoundError(
                f"Schema file not found: {schema_name}\n"
                f"Searched paths: {[str(p) for p in search_paths]}\n"
                f"Available schemas: {available_schemas}"
            )

        try:
            with open(schema_path, "r", encoding="utf-8") as f:
                schema = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in schema file {schema_path}: {e}")

        # Cache and return
        self._schema_cache[schema_name] = schema
        logger.debug(f"Loaded schema: {schema_name} from {schema_path}")
        return schema

    def validate_data(
        self,
        data: dict[str, Any],
        schema_name: str,
    ) -> None:
        """Validate data against JSON schema.

        Args:
            data: Data to validate
            schema_name: Name of schema to validate against

        Raises:
            ValidationError: If validation fails
        """
        schema = self._load_schema(schema_name)

        # Create validator with registry
        validator = Draft202012Validator(schema, registry=self._registry)

        # Validate
        errors = sorted(validator.iter_errors(data), key=lambda e: e.path)

        if errors:
            # Format first error with detailed information
            first_error = errors[0]
            json_path = ".".join(str(p) for p in first_error.path) if first_error.path else "root"
            schema_rule = first_error.validator
            message = first_error.message

            # Include all errors in debug log
            if len(errors) > 1:
                logger.debug(f"Total validation errors: {len(errors)}")
                for idx, error in enumerate(errors, 1):
                    error_path = ".".join(str(p) for p in error.path) if error.path else "root"
                    logger.debug(f"  Error {idx}: {error_path} - {error.message}")

            raise ValidationError(
                message=message,
                json_path=json_path,
                schema_rule=schema_rule,
                original_error=first_error
            )

        logger.info(f"✅ Validation successful for schema: {schema_name}")

    def validate_data_by_kind(self, data: dict[str, Any]) -> str:
        """Validate data using the schema mapped from its kind.

        Args:
            data: Parsed JSON data with required 'kind' field.

        Returns:
            The schema name that was used for validation.

        Raises:
            ValidationError: If kind is missing/unknown or schema validation fails.
        """
        kind = data.get("kind")
        if not kind:
            raise ValidationError(
                message="Missing required field: kind",
                json_path="kind",
                schema_rule="required"
            )

        schema_name = KIND_TO_SCHEMA.get(kind)
        if not schema_name:
            raise ValidationError(
                message=f"Unsupported kind: {kind}",
                json_path="kind",
                schema_rule="enum"
            )

        self.validate_data(data, schema_name)
        return schema_name

    def validate_file(
        self,
        json_path: str | Path,
        schema_name: str,
    ) -> dict[str, Any]:
        """Validate JSON file against schema.

        Args:
            json_path: Path to JSON file
            schema_name: Name of schema to validate against

        Returns:
            Parsed and validated JSON data

        Raises:
            FileNotFoundError: If JSON file not found
            ValidationError: If validation fails
        """
        json_path = Path(json_path)
        if not json_path.exists():
            raise FileNotFoundError(f"JSON file not found: {json_path}")

        # Load JSON
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValidationError(
                message=f"Invalid JSON in file {json_path}: {e}",
                original_error=e
            )

        # Validate
        self.validate_data(data, schema_name)

        logger.info(f"✅ File validated successfully: {json_path}")
        return data

    def validate_file_by_kind(self, json_path: str | Path) -> dict[str, Any]:
        """Validate JSON file using the schema mapped from its kind.

        Args:
            json_path: Path to JSON file

        Returns:
            Parsed and validated JSON data

        Raises:
            FileNotFoundError: If JSON file not found
            ValidationError: If validation fails or kind is missing/unknown
        """
        json_path = Path(json_path)
        if not json_path.exists():
            raise FileNotFoundError(f"JSON file not found: {json_path}")

        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValidationError(
                message=f"Invalid JSON in file {json_path}: {e}",
                original_error=e
            )

        self.validate_data_by_kind(data)
        logger.info(f"✅ File validated successfully: {json_path}")
        return data

    def list_available_schemas(self) -> list[str]:
        """List all available schema names.

        Returns:
            List of schema names (without .schema.json extension)
        """
        if not self.schemas_dir.exists():
            logger.warning(f"Schemas directory does not exist: {self.schemas_dir}")
            return []

        # Search recursively for all schema files
        schemas = [
            p.stem.replace(".schema", "")
            for p in self.schemas_dir.rglob("*.schema.json")
        ]
        return sorted(schemas)


# Convenience function for quick validation
def validate_json_file(json_path: str | Path, schema_name: str) -> dict[str, Any]:
    """Convenience function to validate a JSON file.

    Args:
        json_path: Path to JSON file
        schema_name: Name of schema (e.g., "trading_bot_config")

    Returns:
        Validated JSON data

    Raises:
        ValidationError: If validation fails

    Example:
        data = validate_json_file("config.json", "trading_bot_config")
    """
    validator = SchemaValidator()
    return validator.validate_file(json_path, schema_name)
