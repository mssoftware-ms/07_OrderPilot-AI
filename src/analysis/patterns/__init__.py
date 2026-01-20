"""Chart pattern detection module.

This module provides detectors for identifying geometric chart patterns
such as Cup & Handle, Triple Bottom, Ascending Triangle, etc.
"""

from src.analysis.patterns.base_detector import (
    BaseDetector,
    Pattern,
    Pivot,
    DirectionBias
)

__all__ = [
    'BaseDetector',
    'Pattern',
    'Pivot',
    'DirectionBias'
]
