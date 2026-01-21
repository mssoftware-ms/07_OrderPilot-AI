"""Broker Package for OrderPilot-AI Trading Application."""

from .base import (
    AIAnalysisRequest,
    AIAnalysisResult,
    Balance,
    BrokerAdapter,
    BrokerConnectionError,
    BrokerError,
    FeeModel,
    InsufficientFundsError,
    OrderRequest,
    OrderResponse,
    OrderValidationError,
    Position,
    RateLimitError,
    TokenBucketRateLimiter,
)
from .mock_broker import MockBroker
from .broker_service import BrokerService, get_broker_service

__all__ = [
    # Base classes and interfaces
    'BrokerAdapter',
    # Errors
    'BrokerError',
    'BrokerConnectionError',
    'OrderValidationError',
    'InsufficientFundsError',
    'RateLimitError',
    # Data models
    'OrderRequest',
    'OrderResponse',
    'Position',
    'Balance',
    'FeeModel',
    # AI hooks
    'AIAnalysisRequest',
    'AIAnalysisResult',
    # Rate limiting
    'TokenBucketRateLimiter',
    # Implementations
    'MockBroker',
    # Singleton Service
    'BrokerService',
    'get_broker_service',
]
