"""
Pydantic models for project-specific variables in CEL expressions.

This module defines the data structures for storing and validating
project variables that can be used in CEL (Common Expression Language)
expressions throughout the application.

Architecture:
    - ProjectVariable: Single variable with type, value, metadata
    - ProjectVariables: Container for all project variables
    - Supports .cel_variables.json format

Author: OrderPilot-AI Development Team
Created: 2026-01-28
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, field_validator, model_validator


class VariableType(str, Enum):
    """Supported variable types for CEL expressions."""

    FLOAT = "float"
    INT = "int"
    STRING = "string"
    BOOL = "bool"
    LIST = "list"


class ProjectVariable(BaseModel):
    """
    Single project variable with type, value, and metadata.

    Attributes:
        type: Variable type (float, int, string, bool, list)
        value: Current value of the variable
        description: Human-readable description
        category: Logical grouping (Entry Rules, Risk Management, etc.)
        unit: Optional unit of measurement (USD, %, pips, etc.)
        tags: Optional list of tags for filtering/searching
        readonly: Whether variable can be modified at runtime (default: False)
        source: Optional source of the variable (user, system, computed)

    Examples:
        >>> var = ProjectVariable(
        ...     type="float",
        ...     value=90000.0,
        ...     description="Minimum BTC price for entry",
        ...     category="Entry Rules",
        ...     unit="USD",
        ...     tags=["price", "entry", "threshold"]
        ... )
        >>> var.value
        90000.0
    """

    type: VariableType = Field(
        ...,
        description="Variable type (float, int, string, bool, list)"
    )

    value: Union[float, int, str, bool, List[Any]] = Field(
        ...,
        description="Current value of the variable"
    )

    description: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Human-readable description of the variable"
    )

    category: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Logical grouping (e.g., Entry Rules, Risk Management)"
    )

    unit: Optional[str] = Field(
        None,
        max_length=20,
        description="Unit of measurement (USD, %, pips, etc.)"
    )

    tags: List[str] = Field(
        default_factory=list,
        description="Tags for filtering and searching"
    )

    readonly: bool = Field(
        default=False,
        description="Whether variable can be modified at runtime"
    )

    source: Optional[str] = Field(
        None,
        max_length=50,
        description="Source of the variable (user, system, computed)"
    )

    @field_validator("value")
    @classmethod
    def validate_value_type(cls, v: Any, info) -> Any:
        """Validate that value matches declared type."""
        var_type = info.data.get("type")

        if var_type == VariableType.FLOAT:
            if not isinstance(v, (float, int)):
                raise ValueError(f"Expected float, got {type(v).__name__}")
            return float(v)

        elif var_type == VariableType.INT:
            if not isinstance(v, int) or isinstance(v, bool):
                raise ValueError(f"Expected int, got {type(v).__name__}")
            return v

        elif var_type == VariableType.STRING:
            if not isinstance(v, str):
                raise ValueError(f"Expected string, got {type(v).__name__}")
            return v

        elif var_type == VariableType.BOOL:
            if not isinstance(v, bool):
                raise ValueError(f"Expected bool, got {type(v).__name__}")
            return v

        elif var_type == VariableType.LIST:
            if not isinstance(v, list):
                raise ValueError(f"Expected list, got {type(v).__name__}")
            return v

        return v

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: List[str]) -> List[str]:
        """Validate and normalize tags."""
        # Remove duplicates while preserving order
        seen = set()
        unique_tags = []
        for tag in v:
            tag_lower = tag.lower().strip()
            if tag_lower and tag_lower not in seen:
                seen.add(tag_lower)
                unique_tags.append(tag_lower)
        return unique_tags

    def get_cel_value(self) -> Any:
        """
        Get value formatted for CEL context.

        Returns:
            Value in format suitable for CEL expressions
        """
        return self.value

    def to_display_value(self) -> str:
        """
        Get human-readable display value with unit.

        Returns:
            Formatted string with value and unit

        Examples:
            >>> var = ProjectVariable(type="float", value=1.5, unit="%", ...)
            >>> var.to_display_value()
            '1.5%'
        """
        if self.unit:
            return f"{self.value}{self.unit}"
        return str(self.value)


class ProjectVariables(BaseModel):
    """
    Container for all project variables loaded from .cel_variables.json.

    Attributes:
        version: Schema version for forward compatibility
        project_name: Human-readable project name
        variables: Dictionary of variable_name -> ProjectVariable
        description: Optional project description
        created_at: Optional creation timestamp
        updated_at: Optional last update timestamp

    Examples:
        >>> variables = ProjectVariables(
        ...     version="1.0",
        ...     project_name="BTC Scalping Strategy",
        ...     variables={
        ...         "entry_min_price": ProjectVariable(
        ...             type="float",
        ...             value=90000.0,
        ...             description="Min BTC price",
        ...             category="Entry Rules",
        ...             unit="USD"
        ...         )
        ...     }
        ... )
        >>> variables.get_variable("entry_min_price").value
        90000.0
    """

    version: str = Field(
        default="1.0",
        pattern=r"^\d+\.\d+$",
        description="Schema version (e.g., 1.0, 1.1)"
    )

    project_name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Human-readable project name"
    )

    variables: Dict[str, ProjectVariable] = Field(
        default_factory=dict,
        description="Dictionary of variable_name -> ProjectVariable"
    )

    description: Optional[str] = Field(
        None,
        max_length=1000,
        description="Optional project description"
    )

    created_at: Optional[str] = Field(
        None,
        description="ISO 8601 timestamp of creation"
    )

    updated_at: Optional[str] = Field(
        None,
        description="ISO 8601 timestamp of last update"
    )

    @field_validator("variables")
    @classmethod
    def validate_variable_names(cls, v: Dict[str, ProjectVariable]) -> Dict[str, ProjectVariable]:
        """
        Validate variable names follow naming conventions.

        Rules:
            - Must start with letter or underscore
            - Can contain letters, numbers, underscores
            - Must be valid Python/CEL identifiers
        """
        import re

        pattern = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")

        for var_name in v.keys():
            if not pattern.match(var_name):
                raise ValueError(
                    f"Invalid variable name '{var_name}'. "
                    f"Must start with letter/underscore and contain only "
                    f"alphanumeric characters and underscores."
                )

            # Check for reserved keywords
            reserved = {"and", "or", "not", "in", "if", "else", "true", "false", "null"}
            if var_name.lower() in reserved:
                raise ValueError(
                    f"Variable name '{var_name}' is a reserved keyword"
                )

        return v

    @model_validator(mode="after")
    def validate_unique_combinations(self) -> ProjectVariables:
        """Validate that variable names are unique (case-insensitive)."""
        names_lower = [name.lower() for name in self.variables.keys()]
        if len(names_lower) != len(set(names_lower)):
            raise ValueError("Variable names must be unique (case-insensitive)")
        return self

    def get_variable(self, name: str) -> Optional[ProjectVariable]:
        """
        Get variable by name.

        Args:
            name: Variable name

        Returns:
            ProjectVariable if found, None otherwise
        """
        return self.variables.get(name)

    def get_variables_by_category(self, category: str) -> Dict[str, ProjectVariable]:
        """
        Get all variables in a specific category.

        Args:
            category: Category name

        Returns:
            Dictionary of variable_name -> ProjectVariable for category
        """
        return {
            name: var
            for name, var in self.variables.items()
            if var.category == category
        }

    def get_variables_by_tag(self, tag: str) -> Dict[str, ProjectVariable]:
        """
        Get all variables with a specific tag.

        Args:
            tag: Tag to search for

        Returns:
            Dictionary of variable_name -> ProjectVariable with tag
        """
        tag_lower = tag.lower()
        return {
            name: var
            for name, var in self.variables.items()
            if tag_lower in var.tags
        }

    def get_categories(self) -> List[str]:
        """
        Get list of all categories.

        Returns:
            Sorted list of unique category names
        """
        categories = {var.category for var in self.variables.values()}
        return sorted(categories)

    def get_all_tags(self) -> List[str]:
        """
        Get list of all tags used across variables.

        Returns:
            Sorted list of unique tags
        """
        tags = set()
        for var in self.variables.values():
            tags.update(var.tags)
        return sorted(tags)

    def to_cel_context(self) -> Dict[str, Any]:
        """
        Convert to CEL context dictionary.

        Returns:
            Dictionary of variable_name -> value for CEL

        Examples:
            >>> variables.to_cel_context()
            {'entry_min_price': 90000.0, 'max_risk_pct': 2.0, ...}
        """
        return {
            name: var.get_cel_value()
            for name, var in self.variables.items()
        }

    def add_variable(self, name: str, variable: ProjectVariable) -> None:
        """
        Add or update a variable.

        Args:
            name: Variable name
            variable: ProjectVariable instance

        Raises:
            ValueError: If name is invalid
        """
        # Validate name
        import re
        pattern = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")
        if not pattern.match(name):
            raise ValueError(f"Invalid variable name: {name}")

        self.variables[name] = variable

    def remove_variable(self, name: str) -> bool:
        """
        Remove a variable.

        Args:
            name: Variable name

        Returns:
            True if variable was removed, False if not found
        """
        if name in self.variables:
            del self.variables[name]
            return True
        return False

    def clear_all(self) -> None:
        """Remove all variables."""
        self.variables.clear()

    def count(self) -> int:
        """Get total number of variables."""
        return len(self.variables)

    def __len__(self) -> int:
        """Support len() function."""
        return self.count()

    def __contains__(self, name: str) -> bool:
        """Support 'in' operator."""
        return name in self.variables
