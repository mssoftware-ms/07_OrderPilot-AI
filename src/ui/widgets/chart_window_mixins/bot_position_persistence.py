from __future__ import annotations

from .bot_tr_lock_mixin import BotTRLockMixin
from .bot_position_persistence_chart_mixin import BotPositionPersistenceChartMixin
from .bot_position_persistence_context_mixin import BotPositionPersistenceContextMixin
from .bot_position_persistence_pnl_mixin import BotPositionPersistencePnlMixin
from .bot_position_persistence_restore_mixin import BotPositionPersistenceRestoreMixin
from .bot_position_persistence_storage_mixin import BotPositionPersistenceStorageMixin


class BotPositionPersistenceMixin(
    BotTRLockMixin,
    BotPositionPersistenceStorageMixin,
    BotPositionPersistenceRestoreMixin,
    BotPositionPersistencePnlMixin,
    BotPositionPersistenceContextMixin,
    BotPositionPersistenceChartMixin,
):
    """Mixin providing position persistence and chart integration."""
