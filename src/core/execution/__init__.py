"""Execution module for order and trade event handling.

This module provides event emitters for orders and executions,
enabling real-time chart markers and UI updates.
"""

from src.core.execution.events import (
    BacktraderEventAdapter,
    ExecutionEventEmitter,
    OrderEventEmitter,
)

__all__ = [
    "OrderEventEmitter",
    "ExecutionEventEmitter",
    "BacktraderEventAdapter",
]
