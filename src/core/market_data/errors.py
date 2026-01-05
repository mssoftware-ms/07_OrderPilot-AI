"""Market data specific exception types."""

from __future__ import annotations

from typing import Optional


class MarketDataAccessBlocked(Exception):
    """Raised when a market data endpoint blocks access (e.g., 403/Cloudflare)."""

    def __init__(
        self,
        provider: str,
        status_code: Optional[int] = None,
        reason: Optional[str] = None,
        body_snippet: Optional[str] = None,
    ):
        self.provider = provider
        self.status_code = status_code
        self.reason = reason
        self.body_snippet = body_snippet

        parts: list[str] = [provider or "market data", "access blocked"]
        if status_code is not None:
            parts.append(f"(HTTP {status_code})")
        if reason:
            parts.append(f"- {reason}")

        super().__init__(" ".join(parts))

    def details(self) -> str:
        """Return a human-readable detail string."""
        parts: list[str] = []
        if self.status_code is not None:
            parts.append(f"HTTP {self.status_code}")
        if self.reason:
            parts.append(self.reason)
        if self.body_snippet:
            parts.append(self.body_snippet)
        return "\n".join(parts)
