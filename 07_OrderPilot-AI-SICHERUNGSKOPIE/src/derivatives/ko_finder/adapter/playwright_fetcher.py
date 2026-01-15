"""
Playwright-basierter Fetcher für Onvista.

Verwendet einen Headless-Browser um Vercel Bot-Protection zu umgehen.
Playwright rendert JavaScript und umgeht damit Challenge-Pages.
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING

from .fetcher import FetchResult, CircuitBreaker, CircuitState

if TYPE_CHECKING:
    from playwright.async_api import Browser, BrowserContext, Page

logger = logging.getLogger(__name__)

# Playwright-spezifische Einstellungen
PLAYWRIGHT_TIMEOUT_MS = 30000  # 30 Sekunden für Seitenladung
PLAYWRIGHT_TABLE_WAIT_MS = 10000  # 10 Sekunden für Tabelle
PLAYWRIGHT_NAVIGATION_WAIT_MS = 2000  # 2 Sekunden nach Navigation


@dataclass
class PlaywrightConfig:
    """Konfiguration für Playwright Browser."""

    headless: bool = True
    slow_mo: int = 0  # Millisekunden Verzögerung zwischen Aktionen
    viewport_width: int = 1920
    viewport_height: int = 1080
    locale: str = "de-DE"
    timezone: str = "Europe/Berlin"


class PlaywrightFetcher:
    """
    Headless-Browser Fetcher für Onvista.

    Verwendet Playwright um JavaScript zu rendern und
    Bot-Protection zu umgehen.
    """

    def __init__(
        self,
        config: PlaywrightConfig | None = None,
        min_delay: float = 2.0,
    ) -> None:
        """
        Initialisiere Fetcher.

        Args:
            config: Playwright-Konfiguration
            min_delay: Minimale Sekunden zwischen Requests
        """
        self.config = config or PlaywrightConfig()
        self.min_delay = min_delay
        self.last_request_time: float = 0.0
        self.circuit_breaker = CircuitBreaker()

        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self._page: Page | None = None
        self._lock = asyncio.Lock()
        self._initialized = False

        logger.info(
            "PlaywrightFetcher initialized (headless=%s)",
            self.config.headless,
        )

    async def _ensure_browser(self) -> Page:
        """Stelle sicher, dass Browser und Seite initialisiert sind."""
        if self._page is not None and self._initialized:
            return self._page

        try:
            from playwright.async_api import async_playwright
        except ImportError as e:
            raise ImportError(
                "Playwright nicht installiert. "
                "Bitte ausführen: pip install playwright && playwright install chromium"
            ) from e

        logger.info("Starting Playwright browser...")

        # Playwright starten
        self._playwright = await async_playwright().start()

        # Browser starten
        self._browser = await self._playwright.chromium.launch(
            headless=self.config.headless,
            slow_mo=self.config.slow_mo,
        )

        # Context mit realistischen Browser-Einstellungen
        self._context = await self._browser.new_context(
            viewport={
                "width": self.config.viewport_width,
                "height": self.config.viewport_height,
            },
            locale=self.config.locale,
            timezone_id=self.config.timezone,
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
        )

        # Seite erstellen
        self._page = await self._context.new_page()

        # Session initialisieren (Cookies setzen)
        await self._init_session()

        self._initialized = True
        logger.info("Playwright browser ready")

        return self._page

    async def _init_session(self) -> None:
        """Initialisiere Session durch Besuch der Hauptseite."""
        if not self._page:
            return

        try:
            logger.debug("Initializing Onvista session via Playwright...")

            # Hauptseite besuchen
            await self._page.goto(
                "https://www.onvista.de/",
                wait_until="domcontentloaded",
                timeout=PLAYWRIGHT_TIMEOUT_MS,
            )
            await asyncio.sleep(1.0)

            # Cookie-Banner akzeptieren (falls vorhanden)
            try:
                accept_btn = self._page.locator(
                    "button:has-text('Alle akzeptieren'), "
                    "button:has-text('Akzeptieren'), "
                    "[data-testid='uc-accept-all-button']"
                )
                if await accept_btn.count() > 0:
                    await accept_btn.first.click()
                    logger.debug("Cookie banner accepted")
                    await asyncio.sleep(0.5)
            except Exception:
                pass  # Kein Cookie-Banner

            # Derivate-Seite besuchen
            await self._page.goto(
                "https://www.onvista.de/derivate/Knock-Outs",
                wait_until="domcontentloaded",
                timeout=PLAYWRIGHT_TIMEOUT_MS,
            )
            await asyncio.sleep(1.0)

            logger.debug("Onvista session initialized via Playwright")

        except Exception as e:
            logger.warning("Failed to initialize Playwright session: %s", e)

    async def fetch(self, url: str, run_id: str = "") -> FetchResult:
        """
        Hole HTML von URL mit Playwright.

        Args:
            url: Ziel-URL
            run_id: Optionale Run-ID für Logging

        Returns:
            FetchResult mit HTML oder Fehler
        """
        if not self._can_execute():
            return FetchResult(
                success=False,
                url=url,
                error="Circuit breaker is OPEN - too many failures",
                run_id=run_id,
            )

        await self._apply_rate_limit()
        start_time = time.time()

        try:
            page = await self._ensure_browser()
            response = await self._navigate_to_url(page, url)
            if response is None:
                return self._build_failure(
                    url,
                    "No response from page",
                    start_time,
                    run_id,
                )

            status_code = response.status
            if status_code >= 400:
                return self._build_failure(
                    url,
                    f"HTTP {status_code}",
                    start_time,
                    run_id,
                    status_code=status_code,
                )

            await self._wait_for_render()
            await self._wait_for_table(page)
            html = await page.content()

            return self._build_success(url, status_code, html, start_time, run_id)

        except Exception as e:
            return self._build_failure(
                url,
                str(e),
                start_time,
                run_id,
            )

    def _can_execute(self) -> bool:
        return self.circuit_breaker.can_execute()

    async def _apply_rate_limit(self) -> None:
        async with self._lock:
            await self._wait_for_rate_limit()
            self.last_request_time = time.time()

    async def _navigate_to_url(self, page, url: str):
        logger.info("Playwright navigating to: %s", url[:100])
        return await page.goto(
            url,
            wait_until="domcontentloaded",
            timeout=PLAYWRIGHT_TIMEOUT_MS,
        )

    async def _wait_for_render(self) -> None:
        await asyncio.sleep(PLAYWRIGHT_NAVIGATION_WAIT_MS / 1000)

    async def _wait_for_table(self, page) -> None:
        try:
            await page.wait_for_selector(
                "table, .table, [class*='table'], [data-test*='table']",
                timeout=PLAYWRIGHT_TABLE_WAIT_MS,
            )
            logger.debug("Table found on page")
        except Exception:
            logger.warning("No table found within timeout, continuing anyway")

    def _build_success(
        self,
        url: str,
        status_code: int,
        html: str,
        start_time: float,
        run_id: str,
    ) -> FetchResult:
        self.circuit_breaker.record_success()
        fetch_time_ms = int((time.time() - start_time) * 1000)
        logger.info(
            "Playwright fetch successful: %d bytes in %dms",
            len(html),
            fetch_time_ms,
        )
        return FetchResult(
            success=True,
            html=html,
            url=url,
            status_code=status_code,
            fetch_time_ms=fetch_time_ms,
            run_id=run_id,
        )

    def _build_failure(
        self,
        url: str,
        error_msg: str,
        start_time: float,
        run_id: str,
        status_code: int | None = None,
    ) -> FetchResult:
        self.circuit_breaker.record_failure()
        logger.error("Playwright fetch failed: %s", error_msg)
        return FetchResult(
            success=False,
            url=url,
            status_code=status_code,
            error=error_msg,
            fetch_time_ms=int((time.time() - start_time) * 1000),
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

    def reset_circuit_breaker(self) -> None:
        """Setze Circuit-Breaker manuell zurück."""
        self.circuit_breaker = CircuitBreaker()
        logger.info("Circuit breaker manually reset")

    async def close(self) -> None:
        """Schließe Browser und Playwright."""
        try:
            if self._page:
                await self._page.close()
                self._page = None

            if self._context:
                await self._context.close()
                self._context = None

            if self._browser:
                await self._browser.close()
                self._browser = None

            if hasattr(self, '_playwright') and self._playwright:
                await self._playwright.stop()
                self._playwright = None

            self._initialized = False
            logger.info("Playwright browser closed")

        except Exception as e:
            logger.warning("Error closing Playwright: %s", e)
