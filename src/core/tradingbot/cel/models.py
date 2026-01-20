"""Pydantic models for CEL RulePack structures.

Type-safe models matching rulepack.schema.json specification.
"""

from datetime import datetime
from typing import Any, Literal, Optional
from pydantic import BaseModel, Field, field_validator


class Rule(BaseModel):
    """A single CEL rule within a pack."""

    id: str = Field(..., pattern=r"^[a-zA-Z0-9_-]+$")
    name: str = Field(..., min_length=1)
    enabled: bool = True
    description: Optional[str] = None
    expression: str = Field(..., min_length=1)
    severity: Literal["block", "exit", "update_stop", "warn"]
    message: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    priority: int = Field(default=50, ge=0, le=100)

    @field_validator("expression")
    @classmethod
    def validate_expression_not_empty(cls, v: str) -> str:
        """Ensure expression is not just whitespace."""
        if not v.strip():
            raise ValueError("Expression cannot be empty or whitespace")
        return v


class Pack(BaseModel):
    """A collection of rules for a specific purpose."""

    pack_type: Literal["no_trade", "entry", "exit", "update_stop", "risk"]
    description: Optional[str] = None
    rules: list[Rule]

    @field_validator("rules")
    @classmethod
    def validate_rules_not_empty(cls, v: list[Rule]) -> list[Rule]:
        """Ensure at least one rule is present."""
        if not v:
            raise ValueError("Pack must contain at least one rule")
        return v


class RulePackMetadata(BaseModel):
    """Metadata for a RulePack."""

    name: Optional[str] = None
    description: Optional[str] = None
    author: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    tags: list[str] = Field(default_factory=list)


class RulePack(BaseModel):
    """Complete RulePack with metadata and packs."""

    rules_version: str = Field(..., pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    engine: Literal["CEL"] = "CEL"
    metadata: Optional[RulePackMetadata] = None
    packs: list[Pack]

    @field_validator("packs")
    @classmethod
    def validate_packs_not_empty(cls, v: list[Pack]) -> list[Pack]:
        """Ensure at least one pack is present."""
        if not v:
            raise ValueError("RulePack must contain at least one pack")
        return v

    def get_pack(self, pack_type: str) -> Optional[Pack]:
        """Get pack by type.

        Args:
            pack_type: Pack type to find

        Returns:
            Pack if found, None otherwise
        """
        for pack in self.packs:
            if pack.pack_type == pack_type:
                return pack
        return None

    def get_enabled_rules(self, pack_type: str = None) -> list[Rule]:
        """Get all enabled rules, optionally filtered by pack type.

        Args:
            pack_type: Optional pack type filter

        Returns:
            List of enabled rules
        """
        rules = []
        for pack in self.packs:
            if pack_type is None or pack.pack_type == pack_type:
                rules.extend([r for r in pack.rules if r.enabled])
        return rules

    def get_rules_by_severity(self, severity: str) -> list[Rule]:
        """Get all enabled rules with specific severity.

        Args:
            severity: Severity to filter by

        Returns:
            List of enabled rules with matching severity
        """
        return [
            rule
            for pack in self.packs
            for rule in pack.rules
            if rule.enabled and rule.severity == severity
        ]
