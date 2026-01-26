"""Utility to convert Pattern objects to drawable line segments/boxes."""

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


def pattern_to_boxes(pattern: Pattern) -> Dict[str, Tuple[int, int, float, float]]:
    """Convert pattern metadata (e.g., order blocks/FVG) to drawable boxes.

    Returns dict name -> (start_idx, end_idx, price_low, price_high)
    """
    meta = pattern.metadata or {}
    if pattern.name.startswith("Bullish Order Block") and "index" in meta:
        idx = int(meta["index"])
        return {"order_block": (idx, idx, meta.get("break_high", 0), meta.get("break_high", 0))}
    if pattern.name.endswith("FVG") and {"from", "to", "gap"} <= meta.keys():
        return {
            "fvg": (
                int(meta["from"]),
                int(meta["to"]),
                meta.get("gap_low", 0) or 0,
                meta.get("gap_high", 0) or 0,
            )
        }
    return {}


__all__ = ["pattern_to_lines", "pattern_to_boxes"]


__all__ = ["pattern_to_lines"]
