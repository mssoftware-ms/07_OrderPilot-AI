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

        long_products = self._handle_fetch_result(
            long_result,
            Direction.LONG,
            config,
            underlying_price,
            meta,
        )
        short_products = self._handle_fetch_result(
            short_result,
            Direction.SHORT,
            config,
            underlying_price,
            meta,
        )

        # Filter + Ranking
        filters = HardFilters(config)

        # Scoring-Parameter aus UI-Einstellungen laden (falls verfügbar)
        scoring_params = self._load_scoring_params()

        ranking = RankingEngine(
            config,
            params=scoring_params,
            underlying_price=underlying_price,
        )

        # Long filtern und ranken
        long_products = self._filter_and_rank(
            long_products,
            Direction.LONG,
            filters,
            ranking,
            config.top_n,
            meta,
        )

        # Short filtern und ranken
        short_products = self._filter_and_rank(
            short_products,
            Direction.SHORT,
            filters,
            ranking,
            config.top_n,
            meta,
        )

        # Confidence berechnen
        self._update_parser_confidence(meta, long_products, short_products)

        return long_products, short_products, meta

    def _handle_fetch_result(
        self,
        result,
        direction: Direction,
        config: KOFilterConfig,
        underlying_price: float | None,
        meta: SearchMeta,
    ) -> list[KnockoutProduct]:
        label = "LONG" if direction == Direction.LONG else "SHORT"
        if isinstance(result, Exception):
            status = f"ERROR: {result}"
            if direction == Direction.LONG:
                meta.long_status = status
            else:
                meta.short_status = status
            meta.errors.append(f"{label.title()} fetch failed: {result}")
            logger.error("[KO-Finder] %s fetch exception: %s", label, result)
            return []

        if not result.success:
            status = f"ERROR: {result.error}"
            if direction == Direction.LONG:
                meta.long_status = status
            else:
                meta.short_status = status
            meta.errors.append(f"{label.title()} fetch failed: {result.error}")
            logger.error("[KO-Finder] %s fetch failed: %s", label, result.error)
            return []

        logger.info(
            "[KO-Finder] %s fetch OK: %d bytes in %dms",
            label,
            len(result.html) if result.html else 0,
            result.fetch_time_ms,
        )
        products = self._process_fetch_result(
            result,
            direction,
            config,
            underlying_price,
        )
        if direction == Direction.LONG:
            meta.long_found = len(products)
        else:
            meta.short_found = len(products)

        if len(products) == 0:
            logger.warning(
                "[KO-Finder] No %s products parsed! HTML length: %d",
                label,
                len(result.html) if result.html else 0,
            )
            if direction == Direction.LONG and result.html:
                html_lower = result.html.lower()
                has_table = "<table" in html_lower
                has_wkn = "wkn" in html_lower
                has_no_results = "keine treffer" in html_lower
                logger.warning(
                    "[KO-Finder] HTML analysis: has_table=%s, has_wkn=%s, no_results=%s",
                    has_table,
                    has_wkn,
                    has_no_results,
                )
        return products

    def _load_scoring_params(self):
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
            return scoring_params
        except Exception as e:
            logger.debug("Could not load scoring params from settings: %s", e)
            return None

    def _filter_and_rank(
        self,
        products: list[KnockoutProduct],
        direction: Direction,
        filters: HardFilters,
        ranking: RankingEngine,
        top_n: int,
        meta: SearchMeta,
    ) -> list[KnockoutProduct]:
        if not products:
            return products
        label = "LONG" if direction == Direction.LONG else "SHORT"
        logger.info(
            "[KO-Finder] %s: %d products before filtering",
            label,
            len(products),
        )
        filtered = filters.apply(products)
        logger.info(
            "[KO-Finder] %s: %d passed, %d filtered. Reasons: %s",
            label,
            len(filtered.passed),
            filtered.filtered_out,
            filtered.reasons,
        )
        if direction == Direction.LONG:
            meta.long_filtered = filtered.filtered_out
        else:
            meta.short_filtered = filtered.filtered_out
        return ranking.rank(filtered.passed, top_n)

    def _update_parser_confidence(
        self,
        meta: SearchMeta,
        long_products: list[KnockoutProduct],
        short_products: list[KnockoutProduct],
    ) -> None:
        all_products = long_products + short_products
        if not all_products:
            return
        confidences = [p.parser_confidence for p in all_products]
        meta.parser_confidence_avg = sum(confidences) / len(confidences)
        meta.parser_confidence_min = min(confidences)

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
