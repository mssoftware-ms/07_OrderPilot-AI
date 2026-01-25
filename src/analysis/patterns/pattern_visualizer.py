"""Utility to convert Pattern objects to drawable line segments."""

from __future__ import annotations

from typing import Dict, List, Tuple

from .named_patterns import Pattern


def pattern_to_lines(pattern: Pattern) -> Dict[str, List[Tuple[int, float]]]:
    if hasattr(pattern, "lines"):
        try:
            return pattern.lines(pattern)
        except Exception:
            pass
    return {}


__all__ = ["pattern_to_lines"]
