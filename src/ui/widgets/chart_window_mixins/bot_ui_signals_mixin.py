"""Bot UI Signals Mixin - Composite mixin for all signal handling.

This module provides the main BotUISignalsMixin class which inherits from all
specialized signal mixins. It provides backward compatibility with the original
monolithic implementation.

Architecture:
- BotSignalsBaseMixin: Base infrastructure (price updates, logs, export, settings)
- BotSignalsEntryMixin: Entry signal handling (tab creation, order entry, price updates)
- BotSignalsExitMixin: Exit signal handling (position closing, chart drawing, signal deletion)
- BotSignalsStatusMixin: Status display (position widget, signals table, bot log)

All mixins work together through proper MRO (Method Resolution Order).
"""

from __future__ import annotations

from .signals.bot_signals_base import BotSignalsBaseMixin
from .signals.bot_signals_entry import BotSignalsEntryMixin
from .signals.bot_signals_exit import BotSignalsExitMixin
from .signals.bot_signals_status import BotSignalsStatusMixin
from .signals.widgets.sltp_progress_bar import SLTPProgressBar


class BotUISignalsMixin(
    BotSignalsEntryMixin,
    BotSignalsExitMixin,
    BotSignalsStatusMixin,
    BotSignalsBaseMixin,
):
    """Composite mixin for bot UI signals handling.

    This mixin combines all signal-related functionality:
    - Entry signal handling (order entry, price updates, tab creation)
    - Exit signal handling (position closing, chart drawing, signal deletion)
    - Status display (position widget, signals table, bot log)
    - Base infrastructure (price updates, logs, export, settings)

    MRO (Method Resolution Order):
    1. BotSignalsEntryMixin (entry signals, tab creation)
    2. BotSignalsExitMixin (exit signals, position closing)
    3. BotSignalsStatusMixin (status display, signals table)
    4. BotSignalsBaseMixin (base infrastructure)

    Usage (in BotUIPanelsMixin):
    ```python
    class BotUIPanelsMixin(
        BotUIControlMixin,
        BotUIStrategyMixin,
        BotUISignalsMixin,  # This composite mixin
        BotUIKILogsMixin,
        BotUIEngineSettingsMixin,
    ):
        pass
    ```

    Backward Compatibility:
    All methods from the original BotUISignalsMixin are available through
    the specialized mixins. No code changes required in existing usage.
    """

    pass  # All functionality inherited from base mixins


# Re-export SLTPProgressBar for backward compatibility
__all__ = ['BotUISignalsMixin', 'SLTPProgressBar']
