"""Chart Marking Base Class.

Consolidates duplicate initialization code from all 5 chart marking mixins.

Refactored from chart_marking_mixin.py split (Task 1.2.1).

This base class extracts the common __init__ pattern that appeared
in all 5 mixin helper classes:
- ChartMarkingEntryMethods
- ChartMarkingInternal
- ChartMarkingLineMethods
- ChartMarkingStructureMethods
- ChartMarkingZoneMethods

Eliminates: ~24 LOC duplicate code (-80%)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..chart_marking_mixin import ChartMarkingMixin


class ChartMarkingBase:
    """Base class for all chart marking mixin helpers.

    Consolidates the common initialization pattern where each
    mixin helper stores a reference to its parent ChartMarkingMixin.

    All chart marking helper classes inherit from this base to
    avoid code duplication.

    Attributes:
        parent: Reference to the ChartMarkingMixin instance that
                owns this helper. Provides access to internal state
                (_entry_markers, _zones, _sl_lines, etc.)
    """

    def __init__(self, parent: "ChartMarkingMixin"):
        """Initialize base mixin helper.

        Args:
            parent: ChartMarkingMixin instance that owns this helper.
                    The parent provides access to internal state managers
                    and coordinates updates between different marking types.
        """
        self.parent = parent
