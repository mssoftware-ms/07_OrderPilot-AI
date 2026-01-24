"""Trading Jokes Package."""

from src.core.jokes.trading_jokes_service import (
    TradingJokesService,
    get_random_trading_joke,
    get_random_trading_joke_simple,
)

__all__ = ["TradingJokesService", "get_random_trading_joke", "get_random_trading_joke_simple"]
