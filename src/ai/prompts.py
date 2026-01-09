"""Prompt Library for OrderPilot-AI Trading Application.

Contains prompt templates and JSON schemas for structured AI outputs.

REFACTORED: Split into focused modules for better organization.
"""

# Re-export all classes for backward compatibility
from .prompts_builder import PromptBuilder
from .prompts_schemas import JSONSchemas
from .prompts_templates import PromptTemplates
from .prompts_validator import SchemaValidator
from .prompts_versioning import PromptVersion

__all__ = [
    "PromptTemplates",
    "JSONSchemas",
    "PromptBuilder",
    "SchemaValidator",
    "PromptVersion",
]
