"""Optimization utilities for parameter generation and search.

This package provides:
- ParameterCombinationGenerator: Iterator pattern for generating parameter combinations
- Future: GridSearch, RandomSearch, BayesianOptimization
"""

from src.optimization.parameter_generator import ParameterCombinationGenerator

__all__ = [
    'ParameterCombinationGenerator',
]
