"""
KO-Finder Service - Orchestrierung aller Komponenten.

Koordiniert:
- Paralleles Fetching (Long + Short)
- Parsing und Normalisierung
- Filterung und Ranking
- Caching
"""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from .adapter import OnvistaNormalizer, OnvistaParser, OnvistaURLBuilder, PlaywrightFetcher
from .config import KOFilterConfig
from .constants import DATA_SOURCE, Direction
from .engine import CacheManager, HardFilters, RankingEngine
from .models import (
    KnockoutProduct,
    SearchMeta,
    SearchRequest,
    SearchResponse,
)

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class KOFinderService:
    """
    Haupt-Service für KO-Produkt-Suche.

    Orchestriert alle Komponenten und stellt das Public API bereit.
    Alle Daten stammen ausschließlich von Onvista.
    """

    def __init__(
        self,
        cache_enabled: bool = True,
        cache_ttl: int = 30,
        use_playwright: bool = True,
    ) -> None:
        """
        Initialisiere Service.

        Args:
            cache_enabled: Cache aktivieren
            cache_ttl: Cache TTL in Sekunden
            use_playwright: Playwright statt httpx verwenden (umgeht Bot-Protection)
        """
        self.url_builder = OnvistaURLBuilder()
        self.fetcher = PlaywrightFetcher()
        self.parser = OnvistaParser()
        self.normalizer = OnvistaNormalizer()
        self.use_playwright = use_playwright

        self.cache_enabled = cache_enabled
        self.cache = CacheManager(ttl_seconds=cache_ttl) if cache_enabled else None

        logger.info(
            "KOFinderService initialized (cache=%s, ttl=%ds, playwright=%s)",
            cache_enabled,
            cache_ttl,
            use_playwright,
        )

    async def search(
        self,
        underlying: str,
        config: KOFilterConfig | None = None,
        underlying_price: float | None = None,
        force_refresh: bool = False,
    ) -> SearchResponse:
        """
        Suche KO-Produkte für Underlying.

        Args:
            underlying: Underlying-Symbol/Name
            config: Filter-Konfiguration (Default wenn None)
            underlying_price: Optionaler Underlying-Kurs
            force_refresh: Cache ignorieren

        Returns:
            SearchResponse mit Long/Short Ergebnissen
        """
        run_id = str(uuid.uuid4())[:8]
        start_time = time.time()
        config = config or KOFilterConfig()

        logger.info(
            "Starting KO search for %s (run_id=%s)",
            underlying,
            run_id,
            extra={
                "run_id": run_id,
                "underlying": underlying,
                "config": config.to_dict(),
            },
        )

        # Cache prüfen (wenn nicht force_refresh)
        if self.cache_enabled and not force_refresh:
            cached = self._check_cache(underlying, config)
            if cached:
                logger.info("Cache hit for %s", underlying)
                cached.meta.cache_hit = True
                return cached

        # Parallel Long + Short fetchen
        try:
            long_products, short_products, meta = await self._fetch_and_process(
                underlying=underlying,
                config=config,
                underlying_price=underlying_price,
                run_id=run_id,
            )
        except Exception as e:
            logger.error("Search failed: %s", e, exc_info=True)
            return self._create_error_response(underlying, config, str(e), run_id)

        # Response erstellen
        fetch_time_ms = int((time.time() - start_time) * 1000)
        meta.fetch_time_ms = fetch_time_ms

        response = SearchResponse(
            underlying=underlying,
            as_of=datetime.now(),
            long=long_products,
            short=short_products,
            meta=meta,
            criteria=config.to_dict(),
        )

        # Cache aktualisieren
        if self.cache_enabled:
            self._update_cache(underlying, config, response)

        logger.info(
            "Search completed in %dms: %d long, %d short",
            fetch_time_ms,
            len(long_products),
            len(short_products),
            extra={
                "run_id": run_id,
                "fetch_time_ms": fetch_time_ms,
                "long_count": len(long_products),
                "short_count": len(short_products),
            },
        )

        return response

    async def _fetch_and_process(
        self,
        underlying: str,
        config: KOFilterConfig,
        underlying_price: float | None,
        run_id: str,
    ) -> tuple[list[KnockoutProduct], list[KnockoutProduct], SearchMeta]:
        """Fetche und verarbeite Long + Short parallel."""
        meta = SearchMeta(run_id=run_id, source=DATA_SOURCE)

        # URLs bauen
        long_url = self.url_builder.build_long_url(config, underlying)
        short_url = self.url_builder.build_short_url(config, underlying)

        logger.info("Long URL: %s", long_url)
        logger.info("Short URL: %s", short_url)

        # Sequentiell fetchen (parallel triggert Onvista Rate-Limiting)
        long_result = await self.fetcher.fetch(long_url, run_id)
        await asyncio.sleep(1.0)  # Pause zwischen Requests
        short_result = await self.fetcher.fetch(short_url, run_id)

        # Long verarbeiten
        long_products = []
        if isinstance(long_result, Exception):
            meta.long_status = f"ERROR: {long_result}"
            meta.errors.append(f"Long fetch failed: {long_result}")
            logger.error("[KO-Finder] LONG fetch exception: %s", long_result)
        elif long_result.success:
            logger.info(
                "[KO-Finder] LONG fetch OK: %d bytes in %dms",
                len(long_result.html) if long_result.html else 0,
                long_result.fetch_time_ms,
            )
            long_products = self._process_fetch_result(
                long_result,
                Direction.LONG,
                config,
                underlying_price,
            )
            meta.long_found = len(long_products)
            # Debug: Log wenn keine Produkte gefunden
            if len(long_products) == 0:
                logger.warning(
                    "[KO-Finder] No LONG products parsed! HTML length: %d",
                    len(long_result.html) if long_result.html else 0,
                )
                # Check for common issues
                if long_result.html:
                    html_lower = long_result.html.lower()
                    has_table = "<table" in html_lower
                    has_wkn = "wkn" in html_lower
                    has_no_results = "keine treffer" in html_lower
                    logger.warning(
                        "[KO-Finder] HTML analysis: has_table=%s, has_wkn=%s, no_results=%s",
                        has_table, has_wkn, has_no_results,
                    )
        else:
            meta.long_status = f"ERROR: {long_result.error}"
            meta.errors.append(f"Long fetch failed: {long_result.error}")
            logger.error("[KO-Finder] LONG fetch failed: %s", long_result.error)

        # Short verarbeiten
        short_products = []
        if isinstance(short_result, Exception):
            meta.short_status = f"ERROR: {short_result}"
            meta.errors.append(f"Short fetch failed: {short_result}")
            logger.error("[KO-Finder] SHORT fetch exception: %s", short_result)
        elif short_result.success:
            logger.info(
                "[KO-Finder] SHORT fetch OK: %d bytes in %dms",
                len(short_result.html) if short_result.html else 0,
                short_result.fetch_time_ms,
            )
            short_products = self._process_fetch_result(
                short_result,
                Direction.SHORT,
                config,
                underlying_price,
            )
            meta.short_found = len(short_products)
            if len(short_products) == 0:
                logger.warning(
                    "[KO-Finder] No SHORT products parsed! HTML length: %d",
                    len(short_result.html) if short_result.html else 0,
                )
        else:
            meta.short_status = f"ERROR: {short_result.error}"
            meta.errors.append(f"Short fetch failed: {short_result.error}")
            logger.error("[KO-Finder] SHORT fetch failed: %s", short_result.error)

        # Filter + Ranking
        filters = HardFilters(config)

        # Scoring-Parameter aus UI-Einstellungen laden (falls verfügbar)
        scoring_params = None
        try:
            from src.ui.widgets.ko_finder.settings_dialog import KOSettingsDialog
            scoring_params = KOSettingsDialog.get_scoring_params()
            logger.debug(
                "Using scoring params from settings: SL=%.1f%%, TP=%.1f%%, "
                "weights=(spread=%.0f%%, lev=%.0f%%, ko=%.0f%%, ev=%.0f%%)",
                scoring_params.dsl * 100,
                scoring_params.dtp * 100,
                scoring_params.w_spread * 100,
                scoring_params.w_lev * 100,
                scoring_params.w_ko * 100,
                scoring_params.w_ev * 100,
            )
        except Exception as e:
            logger.debug("Could not load scoring params from settings: %s", e)

        ranking = RankingEngine(
            config,
            params=scoring_params,
            underlying_price=underlying_price,
        )

        # Long filtern und ranken
        if long_products:
            logger.info(
                "[KO-Finder] LONG: %d products before filtering",
                len(long_products),
            )
            long_filtered = filters.apply(long_products)
            logger.info(
                "[KO-Finder] LONG: %d passed, %d filtered. Reasons: %s",
                len(long_filtered.passed),
                long_filtered.filtered_out,
                long_filtered.reasons,
            )
            meta.long_filtered = long_filtered.filtered_out
            long_products = ranking.rank(long_filtered.passed, config.top_n)

        # Short filtern und ranken
        if short_products:
            logger.info(
                "[KO-Finder] SHORT: %d products before filtering",
                len(short_products),
            )
            short_filtered = filters.apply(short_products)
            logger.info(
                "[KO-Finder] SHORT: %d passed, %d filtered. Reasons: %s",
                len(short_filtered.passed),
                short_filtered.filtered_out,
                short_filtered.reasons,
            )
            meta.short_filtered = short_filtered.filtered_out
            short_products = ranking.rank(short_filtered.passed, config.top_n)

        # Confidence berechnen
        all_products = long_products + short_products
        if all_products:
            confidences = [p.parser_confidence for p in all_products]
            meta.parser_confidence_avg = sum(confidences) / len(confidences)
            meta.parser_confidence_min = min(confidences)

        return long_products, short_products, meta

    def _process_fetch_result(
        self,
        fetch_result,
        direction: Direction,
        config: KOFilterConfig,
        underlying_price: float | None,
    ) -> list[KnockoutProduct]:
        """Verarbeite Fetch-Ergebnis zu Produkten."""
        # Parsen
        parse_result = self.parser.parse(
            fetch_result.html,
            direction,
            fetch_result.url,
            fetch_result.run_id,
        )

        if not parse_result.success:
            logger.warning(
                "Parsing failed for %s: %s",
                direction.name,
                parse_result.error,
            )
            return []

        # Debug: Zeige Parse-Ergebnis
        logger.info(
            "[KO-Finder] %s: Parsed %d products (confidence: %.2f)",
            direction.name,
            parse_result.rows_parsed,
            parse_result.confidence,
        )

        # Debug: Zeige erstes Produkt Details
        if parse_result.products:
            p = parse_result.products[0]
            logger.info(
                "[KO-Finder] Sample product: WKN=%s, Hebel=%.1f, Spread=%.2f%%, "
                "Bid=%.3f, Ask=%.3f, Issuer=%s",
                p.wkn,
                p.leverage or 0,
                p.spread_pct or 0,
                p.quote.bid or 0,
                p.quote.ask or 0,
                p.issuer,
            )

        # Normalisieren
        products = self.normalizer.normalize_products(
            parse_result.products,
            underlying_price,
        )

        return products

    def _check_cache(
        self,
        underlying: str,
        config: KOFilterConfig,
    ) -> SearchResponse | None:
        """Prüfe Cache auf gültigen Eintrag."""
        if not self.cache:
            return None

        key = CacheManager.build_key(underlying, "ALL", config)
        entry = self.cache.get(key)

        if entry and not entry.is_expired:
            return entry.value

        return None

    def _update_cache(
        self,
        underlying: str,
        config: KOFilterConfig,
        response: SearchResponse,
    ) -> None:
        """Aktualisiere Cache mit neuem Ergebnis."""
        if not self.cache:
            return

        key = CacheManager.build_key(underlying, "ALL", config)
        self.cache.set(key, response)

    def _create_error_response(
        self,
        underlying: str,
        config: KOFilterConfig,
        error: str,
        run_id: str,
    ) -> SearchResponse:
        """Erstelle Error-Response."""
        return SearchResponse(
            underlying=underlying,
            as_of=datetime.now(),
            long=[],
            short=[],
            meta=SearchMeta(
                run_id=run_id,
                long_status=f"ERROR: {error}",
                short_status=f"ERROR: {error}",
                errors=[error],
                source=DATA_SOURCE,
            ),
            criteria=config.to_dict(),
        )

    def reset_circuit_breaker(self) -> None:
        """Setze Circuit-Breaker zurück."""
        self.fetcher.reset_circuit_breaker()

    def clear_cache(self) -> int:
        """Lösche Cache und gib Anzahl gelöschter Einträge zurück."""
        if self.cache:
            return self.cache.clear()
        return 0
