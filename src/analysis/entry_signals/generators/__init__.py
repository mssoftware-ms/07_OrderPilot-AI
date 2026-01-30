"""Entry signal generators using Rule Type Pattern.

This module provides a registry-based approach to entry signal generation,
replacing the monolithic generate_entries() function with specialized generators.

Architecture:
    - BaseEntryGenerator: Abstract base class for all generators
    - EntryGeneratorRegistry: Central registry for generator dispatch
    - Specialized generators for each regime/rule type

Example:
    >>> registry = EntryGeneratorRegistry()
    >>> entries = registry.generate(df, rule, params)
"""

from .base_generator import BaseEntryGenerator
from .registry import EntryGeneratorRegistry

__all__ = ["BaseEntryGenerator", "EntryGeneratorRegistry"]
