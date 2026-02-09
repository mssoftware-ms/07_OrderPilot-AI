"""Kind-aware JSON loader with schema validation.

Validates JSON against v2.1 schemas in /schemas using the required `kind` field.
Fail-closed: invalid JSON raises ValidationError and must not be used for computation.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .validator import SchemaValidator


class KindConfigLoader:
    """Load JSON files by kind with schema validation."""

    def __init__(self, schemas_dir: Path | None = None) -> None:
        if schemas_dir is None:
            project_root = Path(__file__).parents[4]
            schemas_dir = project_root / "schemas"
        self.validator = SchemaValidator(schemas_dir=schemas_dir)

    def load(self, json_path: str | Path) -> dict[str, Any]:
        """Load and validate JSON file by kind.

        Args:
            json_path: Path to JSON file.

        Returns:
            Validated JSON data.

        Raises:
            ValidationError: If schema validation fails or kind is missing/unknown.
        """
        import json
        import logging

        logger = logging.getLogger(__name__)
        path = Path(json_path)

        if not path.exists():
             raise FileNotFoundError(f"JSON file not found: {path}")

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            from .validator import ValidationError
            raise ValidationError(f"Invalid JSON in file {path}: {e}", original_error=e)

        # --- LEGACY SHIM START ---
        if "kind" not in data:
            guessed_kind = None
            if "strategies" in data and "routing" in data:
                guessed_kind = "strategy_config"
            elif "optimization_results" in data:
                guessed_kind = "regime_optimization_results"
            elif "indicators" in data:
                guessed_kind = "indicator_set"

            if guessed_kind:
                logger.warning(
                    f"⚠️ LEGACY FILE DETECTED: {path.name} is missing 'kind'. "
                    f"Auto-detected as '{guessed_kind}'. "
                    "Please migrate this file to v2.1 format."
                )
                data["kind"] = guessed_kind

        # Fix schema_version if wrong or missing (all v1.x.x → 2.1.0)
        current_version = data.get("schema_version", "")
        if not current_version or not current_version.startswith("2.1."):
            if current_version:
                logger.warning(
                    f"⚠️ LEGACY VERSION: {path.name} has schema_version '{current_version}'. "
                    "Auto-upgrading to '2.1.0'."
                )
            data["schema_version"] = "2.1.0"

        # Remove disallowed fields (v1 legacy)
        if "metadata" in data:
            logger.warning(
                f"⚠️ REMOVING LEGACY FIELD: {path.name} contains 'metadata' which is "
                "not allowed in v2.1. Field removed automatically."
            )
            del data["metadata"]
        # --- LEGACY SHIM END ---

        self.validator.validate_data_by_kind(data)
        return data
