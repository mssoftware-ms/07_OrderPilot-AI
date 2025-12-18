"""LLM Types for Tradingbot.

Contains enums and dataclasses for LLM integration:
- LLMCallType: Types of LLM calls
- LLMCallRecord: Audit record for LLM calls
- LLMBudgetState: Budget tracking state
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class LLMCallType(str, Enum):
    """Types of LLM calls."""
    DAILY_STRATEGY = "daily_strategy"
    REGIME_FLIP = "regime_flip"
    EXIT_CANDIDATE = "exit_candidate"
    SIGNAL_CHANGE = "signal_change"
    MANUAL = "manual"


@dataclass
class LLMCallRecord:
    """Record of an LLM call for audit trail."""
    call_id: str
    call_type: LLMCallType
    timestamp: datetime
    prompt_hash: str
    response_hash: str | None = None
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    latency_ms: int = 0
    success: bool = True
    error_message: str | None = None
    fallback_used: bool = False


@dataclass
class LLMBudgetState:
    """Budget tracking state."""
    date: datetime = field(default_factory=datetime.utcnow)
    calls_today: int = 0
    tokens_today: int = 0
    cost_today_usd: float = 0.0
    daily_calls_by_type: dict[str, int] = field(default_factory=dict)
    last_call_time: datetime | None = None
    consecutive_errors: int = 0
