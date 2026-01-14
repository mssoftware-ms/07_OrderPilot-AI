"""
Aggregation module for heatmap grid generation.

Transforms raw liquidation events into renderable grid cells.
"""

from .grid_builder import GridBuilder
from .normalization import normalize_intensity, NormalizationType

__all__ = [
    "GridBuilder",
    "normalize_intensity",
    "NormalizationType",
]
