"""RulePack Loader with Schema Validation.

Loads and validates RulePack JSON files using SchemaValidator and Pydantic models.
"""

import json
import logging
from pathlib import Path
from typing import Optional

from src.core.tradingbot.config.validator import SchemaValidator, ValidationError
from .models import RulePack

logger = logging.getLogger(__name__)


class RulePackLoader:
    """Loads and validates RulePack JSON files.

    Uses SchemaValidator for JSON Schema validation and
    Pydantic models for type-safety.

    Example:
        loader = RulePackLoader()
        rulepack = loader.load("03_JSON/RulePacks/default_rules.json")
    """

    def __init__(self, validator: Optional[SchemaValidator] = None):
        """Initialize RulePack loader.

        Args:
            validator: Optional SchemaValidator instance (creates new if None)
        """
        self.validator = validator or SchemaValidator()
        logger.info("RulePackLoader initialized")

    def load(self, json_path: str | Path) -> RulePack:
        """Load and validate RulePack from JSON file.

        Args:
            json_path: Path to RulePack JSON file

        Returns:
            Validated RulePack instance

        Raises:
            FileNotFoundError: If file not found
            ValidationError: If JSON Schema validation fails
            ValueError: If Pydantic validation fails

        Example:
            rulepack = loader.load("03_JSON/RulePacks/default_rules.json")
            print(f"Loaded {len(rulepack.packs)} packs")
        """
        json_path = Path(json_path)

        # 1. JSON Schema Validation
        data = self.validator.validate_file(json_path, schema_name="rulepack")

        # 2. Pydantic Model Validation
        try:
            rulepack = RulePack(**data)
        except Exception as e:
            logger.error(f"Pydantic validation failed for {json_path}: {e}")
            raise ValueError(f"Invalid RulePack structure: {e}") from e

        logger.info(
            f"✅ RulePack loaded successfully: {json_path}\n"
            f"   Version: {rulepack.rules_version}\n"
            f"   Packs: {len(rulepack.packs)}\n"
            f"   Total Rules: {sum(len(p.rules) for p in rulepack.packs)}"
        )

        return rulepack

    def load_from_dict(self, data: dict) -> RulePack:
        """Load RulePack from dict (already validated).

        Args:
            data: RulePack data dict

        Returns:
            RulePack instance

        Raises:
            ValueError: If Pydantic validation fails
        """
        # Validate with schema first
        self.validator.validate_data(data, schema_name="rulepack")

        # Convert to Pydantic model
        return RulePack(**data)

    def save(self, rulepack: RulePack, json_path: str | Path) -> None:
        """Save RulePack to JSON file.

        Args:
            rulepack: RulePack instance to save
            json_path: Destination path

        Example:
            loader.save(rulepack, "03_JSON/RulePacks/my_rules.json")
        """
        json_path = Path(json_path)

        # Convert to dict
        data = rulepack.model_dump(mode="json", exclude_none=True)

        # Validate before saving
        self.validator.validate_data(data, schema_name="rulepack")

        # Save with pretty formatting
        json_path.parent.mkdir(parents=True, exist_ok=True)
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info(f"✅ RulePack saved: {json_path}")
