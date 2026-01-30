"""Signal generator modules for indicator-based trading signals.

This package implements the Strategy Pattern to replace the monster
_generate_signals() function (CC=157) with focused, testable generators.

Architecture:
- BaseSignalGenerator: Abstract base class (Strategy interface)
- Concrete generators: One per indicator family (CC < 5 each)

Target: 22 focused generators replacing 322 lines of nested if-statements.
"""

from .base_generator import BaseSignalGenerator

__all__ = ['BaseSignalGenerator']
