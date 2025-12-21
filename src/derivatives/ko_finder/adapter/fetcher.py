"""
HTTP-Fetcher für Onvista mit Rate-Limiting und Circuit-Breaker.

Implementiert:
- Rate-Limiting (min. Abstand zwischen Requests)
- Retry mit exponentialem Backoff
- Circuit-Breaker bei wiederholten Fehlern
- Timeout-Handling
"""

from __future__ import annotations

import asyncio
import logging
import random
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

import httpx

from ..constants import (
    CIRCUIT_BREAKER_THRESHOLD,
    CIRCUIT_BREAKER_TIMEOUT,
    HTTP_BACKOFF_FACTOR,
    HTTP_HEADERS,
    HTTP_JITTER,
    HTTP_MAX_RETRIES,
    HTTP_TIMEOUT_CONNECT,
    HTTP_TIMEOUT_READ,
    RATE_LIMIT_MIN_DELAY,
)

if TYPE_CHECKING:
    from ..config import KOFilterConfig

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Zustände des Circuit-Breakers."""

    CLOSED = "closed"  # Normal, Requests erlaubt
    OPEN = "open"  # Blockiert, keine Requests
    HALF_OPEN = "half_open"  # Test-Phase


@dataclass
class FetchResult:
    """Ergebnis eines Fetch-Vorgangs."""

    success: bool
    html: str = ""
    url: str = ""
    status_code: int = 0
    error: str | None = None
    fetch_time_ms: int = 0
    from_cache: bool = False
    run_id: str = ""


@dataclass
class CircuitBreaker:
    """
    Circuit-Breaker zum Schutz vor Überlastung.

    Nach mehreren Fehlern wird der Circuit geöffnet und
    Requests werden für eine Zeit blockiert.
    """

    failure_count: int = 0
    last_failure_time: float = 0.0
    state: CircuitState = CircuitState.CLOSED
    threshold: int = CIRCUIT_BREAKER_THRESHOLD
    timeout: float = CIRCUIT_BREAKER_TIMEOUT

    def record_failure(self) -> None:
        """Registriere einen Fehler."""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.threshold:
            self.state = CircuitState.OPEN
            logger.warning(
                "Circuit breaker OPENED after %d failures",
                self.failure_count,
            )

    def record_success(self) -> None:
        """Registriere einen Erfolg."""
        self.failure_count = 0
        self.state = CircuitState.CLOSED

    def can_execute(self) -> bool:
        """Prüfe ob Request ausgeführt werden darf."""
        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            # Prüfe ob Timeout abgelaufen
            if time.time() - self.last_failure_time > self.timeout:
                self.state = CircuitState.HALF_OPEN
                logger.info("Circuit breaker entering HALF_OPEN state")
                return True
            return False

        # HALF_OPEN: Ein Test-Request erlaubt
        return True


class OnvistaFetcher:
    """
    HTTP-Client für Onvista mit Rate-Limiting und Fehlerbehandlung.

    Verwendet httpx für async HTTP-Requests mit persistenter Session.
    """

    def __init__(
        self,
        min_delay: float = RATE_LIMIT_MIN_DELAY,
        max_retries: int = HTTP_MAX_RETRIES,
    ) -> None:
        """
        Initialisiere Fetcher.

        Args:
            min_delay: Minimale Sekunden zwischen Requests
            max_retries: Maximale Retry-Versuche
        """
        self.min_delay = min_delay
        self.max_retries = max_retries
        self.last_request_time: float = 0.0
        self.circuit_breaker = CircuitBreaker()
        self._lock = asyncio.Lock()
        self._client: httpx.AsyncClient | None = None
        self._session_initialized: bool = False

    async def fetch(self, url: str, run_id: str = "") -> FetchResult:
        """
        Hole HTML von URL mit Rate-Limiting und Retry.

        Args:
            url: Ziel-URL
            run_id: Optionale Run-ID für Logging

        Returns:
            FetchResult mit HTML oder Fehler
        """
        # Circuit-Breaker prüfen
        if not self.circuit_breaker.can_execute():
            return FetchResult(
                success=False,
                url=url,
                error="Circuit breaker is OPEN - too many failures",
                run_id=run_id,
            )

        # Rate-Limiting
        async with self._lock:
            await self._wait_for_rate_limit()
            self.last_request_time = time.time()

        # Fetch mit Retry
        start_time = time.time()
        last_error: str | None = None

        for attempt in range(self.max_retries):
            try:
                result = await self._do_fetch(url, run_id)

                if result.success:
                    self.circuit_breaker.record_success()
                    result.fetch_time_ms = int((time.time() - start_time) * 1000)
                    return result

                last_error = result.error

            except Exception as e:
                last_error = str(e)
                logger.warning(
                    "Fetch attempt %d/%d failed: %s",
                    attempt + 1,
                    self.max_retries,
                    last_error,
                    extra={"url": url, "run_id": run_id, "attempt": attempt + 1},
                )

            # Backoff vor Retry
            if attempt < self.max_retries - 1:
                delay = self._calculate_backoff(attempt)
                await asyncio.sleep(delay)

        # Alle Versuche fehlgeschlagen
        self.circuit_breaker.record_failure()

        return FetchResult(
            success=False,
            url=url,
            error=f"All {self.max_retries} attempts failed: {last_error}",
            fetch_time_ms=int((time.time() - start_time) * 1000),
            run_id=run_id,
        )

    async def _get_client(self) -> httpx.AsyncClient:
        """Hole oder erstelle persistente Session mit Cookies."""
        if self._client is None:
            timeout = httpx.Timeout(
                connect=HTTP_TIMEOUT_CONNECT,
                read=HTTP_TIMEOUT_READ,
                write=HTTP_TIMEOUT_READ,
                pool=HTTP_TIMEOUT_READ,
            )
            # HTTP/2 deaktiviert - kann Probleme mit manchen Servern verursachen
            # SSL-Verifikation deaktiviert (Windows Zertifikatsprobleme)
            import ssl
            import warnings
            warnings.filterwarnings('ignore', message='Unverified HTTPS request')

            self._client = httpx.AsyncClient(
                timeout=timeout,
                headers=HTTP_HEADERS,
                follow_redirects=True,
                http2=False,
                verify=False,  # SSL deaktiviert wegen Windows Zertifikatsproblemen
            )
        return self._client

    async def _init_session(self) -> None:
        """Initialisiere Session durch Besuch der Hauptseite (setzt Cookies)."""
        if self._session_initialized:
            return

        try:
            client = await self._get_client()
            # Besuche zuerst Hauptseite
            logger.debug("Initializing Onvista session...")
            await client.get("https://www.onvista.de/")
            await asyncio.sleep(0.5)  # Kurze Pause
            # Dann die Derivate-Hauptseite
            await client.get("https://www.onvista.de/derivate/Knock-Outs")
            await asyncio.sleep(0.3)
            self._session_initialized = True
            logger.debug("Onvista session initialized with cookies")
        except Exception as e:
            logger.warning("Failed to initialize session: %s", e)

    async def _do_fetch(self, url: str, run_id: str) -> FetchResult:
        """Führe einzelnen Fetch-Request aus."""
        # Session initialisieren (Cookies holen)
        await self._init_session()

        client = await self._get_client()

        # Setze Referer passend zur Navigation
        headers = {"Referer": "https://www.onvista.de/derivate/Knock-Outs"}
        response = await client.get(url, headers=headers)

        if response.status_code == 200:
            return FetchResult(
                success=True,
                html=response.text,
                url=url,
                status_code=response.status_code,
                run_id=run_id,
            )

        error_msg = f"HTTP {response.status_code}"
        if response.status_code == 429:
            error_msg = "Rate limit exceeded (429)"
        elif response.status_code == 403:
            # Log response headers and body for debugging
            logger.warning(
                "403 Response - Headers: %s",
                dict(response.headers)
            )
            # Check for specific blocking indicators
            body_preview = response.text[:500] if response.text else ""
            logger.warning("403 Response - Body preview: %s", body_preview)

            error_msg = "Access forbidden (403) - Onvista blockiert Anfrage"
            # Reset session bei 403, vielleicht sind Cookies abgelaufen
            self._session_initialized = False
            self._client = None  # Force new client
        elif response.status_code >= 500:
            error_msg = f"Server error ({response.status_code})"

        return FetchResult(
            success=False,
            url=url,
            status_code=response.status_code,
            error=error_msg,
            run_id=run_id,
        )

    async def _wait_for_rate_limit(self) -> None:
        """Warte bis Rate-Limit erlaubt."""
        if self.last_request_time > 0:
            elapsed = time.time() - self.last_request_time
            if elapsed < self.min_delay:
                wait_time = self.min_delay - elapsed
                logger.debug("Rate limiting: waiting %.2fs", wait_time)
                await asyncio.sleep(wait_time)

    def _calculate_backoff(self, attempt: int) -> float:
        """Berechne Backoff-Zeit mit Jitter."""
        base_delay = HTTP_BACKOFF_FACTOR ** attempt
        jitter = random.uniform(-HTTP_JITTER, HTTP_JITTER)
        return max(0.1, base_delay + jitter)

    def reset_circuit_breaker(self) -> None:
        """Setze Circuit-Breaker manuell zurück."""
        self.circuit_breaker = CircuitBreaker()
        self._session_initialized = False
        logger.info("Circuit breaker manually reset")

    async def close(self) -> None:
        """Schließe HTTP-Client und Session."""
        if self._client:
            await self._client.aclose()
            self._client = None
            self._session_initialized = False
            logger.debug("Onvista HTTP client closed")
