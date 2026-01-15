"""OpenAI Utility Classes.

Contains CostTracker for budget management and CacheManager
for response caching.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
from datetime import datetime, timedelta
from typing import Any

from .openai_models import QuotaExceededError

logger = logging.getLogger(__name__)


# ==================== Cost Tracking ====================

class CostTracker:
    """Tracks AI API costs and enforces budget limits."""

    # Pricing per 1M tokens (as of 2024)
    PRICING = {
        "gpt-4o": {"input": 2.50, "output": 10.00},
        "gpt-4o-mini": {"input": 0.15, "output": 0.60},
        "gpt-4-turbo": {"input": 10.00, "output": 30.00}
    }

    def __init__(self, monthly_budget: float, warn_threshold: float):
        """Initialize cost tracker.

        Args:
            monthly_budget: Monthly budget in EUR
            warn_threshold: Warning threshold in EUR
        """
        self.monthly_budget = monthly_budget
        self.warn_threshold = warn_threshold
        self.current_month_cost = 0.0
        self.current_month = datetime.utcnow().month
        self._lock = asyncio.Lock()

    async def track_usage(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """Track API usage and calculate cost.

        Args:
            model: Model name
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Cost in EUR

        Raises:
            QuotaExceededError: If budget exceeded
        """
        async with self._lock:
            # Reset monthly tracking if new month
            current_month = datetime.utcnow().month
            if current_month != self.current_month:
                self.current_month = current_month
                self.current_month_cost = 0.0

            # Calculate cost
            model_base = model.split("-2024")[0]  # Remove date suffix
            pricing = self.PRICING.get(model_base, self.PRICING["gpt-4o-mini"])

            input_cost = (input_tokens / 1_000_000) * pricing["input"]
            output_cost = (output_tokens / 1_000_000) * pricing["output"]
            total_cost = input_cost + output_cost

            # Check budget
            if self.current_month_cost + total_cost > self.monthly_budget:
                raise QuotaExceededError(
                    f"Monthly budget of €{self.monthly_budget} would be exceeded"
                )

            # Update tracking
            self.current_month_cost += total_cost

            # Log warning if threshold reached
            if self.current_month_cost > self.warn_threshold:
                logger.warning(
                    f"AI cost warning: €{self.current_month_cost:.2f} "
                    f"of €{self.monthly_budget:.2f} budget used"
                )

            return total_cost


# ==================== Cache Manager ====================

class CacheManager:
    """Manages caching of AI responses."""

    def __init__(self, ttl_seconds: int = 3600):
        """Initialize cache manager.

        Args:
            ttl_seconds: Cache TTL in seconds
        """
        self.ttl_seconds = ttl_seconds
        self._memory_cache: dict[str, Any] = {}

    def _generate_key(self, prompt: str, model: str, schema: dict[str, Any]) -> str:
        """Generate cache key from request parameters."""
        content = f"{prompt}:{model}:{json.dumps(schema, sort_keys=True)}"
        return hashlib.sha256(content.encode()).hexdigest()

    async def get(
        self,
        prompt: str,
        model: str,
        schema: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Get cached response if available.

        Args:
            prompt: The prompt
            model: Model name
            schema: Response schema

        Returns:
            Cached response or None
        """
        key = self._generate_key(prompt, model, schema)

        # Check memory cache first
        if key in self._memory_cache:
            entry = self._memory_cache[key]
            if datetime.utcnow() < entry['expires_at']:
                logger.debug(f"Cache hit for key {key[:8]}...")
                return entry['response']

        return None

    async def set(
        self,
        prompt: str,
        model: str,
        schema: dict[str, Any],
        response: dict[str, Any]
    ) -> None:
        """Cache a response.

        Args:
            prompt: The prompt
            model: Model name
            schema: Response schema
            response: The response to cache
        """
        key = self._generate_key(prompt, model, schema)
        expires_at = datetime.utcnow() + timedelta(seconds=self.ttl_seconds)

        self._memory_cache[key] = {
            'response': response,
            'expires_at': expires_at
        }

        # Clean up expired entries
        await self._cleanup_expired()

    async def _cleanup_expired(self) -> None:
        """Remove expired entries from memory cache."""
        now = datetime.utcnow()
        expired_keys = [
            k for k, v in self._memory_cache.items()
            if now >= v['expires_at']
        ]
        for key in expired_keys:
            del self._memory_cache[key]
