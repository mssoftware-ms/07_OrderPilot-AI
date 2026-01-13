"""
Storage module for liquidation event persistence.

Provides SQLite database with optimized writes and retention policies.
"""

from .sqlite_store import LiquidationStore

__all__ = [
    "LiquidationStore",
]
