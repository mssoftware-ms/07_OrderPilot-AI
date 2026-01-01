"""KO-Finder Mixin for ChartWindow.

Provides the KO-Finder tab for searching Knock-Out products.
All data comes exclusively from Onvista.
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from PyQt6.QtCore import QSettings, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QMessageBox,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    from src.derivatives.ko_finder.models import SearchResponse

logger = logging.getLogger(__name__)


class KOFinderWorker(QThread):
    """Worker Thread für KO-Finder Suche."""

    finished = pyqtSignal(object)  # SearchResponse
    error = pyqtSignal(str)

    def __init__(self, underlying: str, config, underlying_price: float | None = None):
        super().__init__()
        self.underlying = underlying
        self.config = config
        self.underlying_price = underlying_price

    def run(self):
        """Führe Suche in separatem Thread aus."""
        try:
            from src.derivatives.ko_finder.service import KOFinderService

            service = KOFinderService()
            # Reset circuit breaker für frischen Start
            service.reset_circuit_breaker()

            # Async in Thread ausführen
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(
                    service.search(
                        self.underlying,
                        self.config,
                        self.underlying_price,
                    )
                )
                self.finished.emit(result)
            finally:
                # Cleanup
                loop.run_until_complete(service.fetcher.close())
                loop.close()

        except Exception as e:
            logger.error("KO-Finder search failed: %s", e, exc_info=True)
            self.error.emit(str(e))


class KOFinderMixin:
    """Mixin providing KO-Finder tab for ChartWindow."""

    def _create_ko_finder_tab(self) -> QWidget:
        """Create KO-Finder tab with filter and result panels."""
        from src.ui.widgets.ko_finder import KOFilterPanel, KOResultPanel

        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)

        # Splitter für Filter und Ergebnisse
        splitter = QSplitter()

        # Filter Panel (links)
        self.ko_filter_panel = KOFilterPanel()
        self.ko_filter_panel.setMaximumWidth(250)
        self.ko_filter_panel.setMinimumWidth(180)
        self.ko_filter_panel.refresh_requested.connect(self._on_ko_refresh)
        splitter.addWidget(self.ko_filter_panel)

        # Result Panel (rechts)
        self.ko_result_panel = KOResultPanel()
        self.ko_result_panel.product_selected.connect(self._on_ko_product_selected)
        self.ko_result_panel.refresh_ko_distance_requested.connect(
            self._on_refresh_ko_distance
        )
        splitter.addWidget(self.ko_result_panel)

        # Splitter-Verhältnis
        splitter.setSizes([200, 600])
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        layout.addWidget(splitter)

        # Worker-Referenz
        self._ko_worker: KOFinderWorker | None = None

        # Config aus Settings laden
        self._load_ko_settings()

        return widget

    def _on_ko_refresh(self) -> None:
        """Handler für KO-Finder Refresh."""
        # Underlying aus Chart holen
        underlying = self._get_current_underlying()
        if not underlying:
            QMessageBox.warning(
                self,
                "KO-Finder",
                "Bitte zuerst ein Symbol im Chart auswählen.",
            )
            return

        # Underlying-Preis holen (wenn verfügbar)
        underlying_price = self._get_current_price()

        # Config aus Panel holen
        config = self.ko_filter_panel.get_config()

        # Settings speichern
        self._save_ko_settings()

        # UI auf Loading setzen
        self.ko_filter_panel.set_loading(True)
        self.ko_result_panel.clear()
        self.ko_result_panel.set_status("Suche läuft...")

        # Map symbol to Onvista URL slug for display
        from src.derivatives.ko_finder.constants import SYMBOL_TO_ONVISTA_SLUG
        slug = SYMBOL_TO_ONVISTA_SLUG.get(underlying, SYMBOL_TO_ONVISTA_SLUG.get(underlying.upper(), underlying))

        # Log in KI-Log
        if slug != underlying:
            self._log_ko_event(
                "SEARCH",
                f"Starte KO-Suche: {underlying} → 'Knock-Outs-auf-{slug}' "
                f"(Hebel: {config.min_leverage}+, Spread: <{config.max_spread_pct}%)"
            )
        else:
            self._log_ko_event(
                "SEARCH",
                f"Starte KO-Suche für 'Knock-Outs-auf-{slug}' "
                f"(Hebel: {config.min_leverage}+, Spread: <{config.max_spread_pct}%)"
            )

        # Worker starten
        self._ko_worker = KOFinderWorker(underlying, config, underlying_price)
        self._ko_worker.finished.connect(self._on_ko_search_finished)
        self._ko_worker.error.connect(self._on_ko_search_error)
        self._ko_worker.start()

        logger.info("KO-Finder search started for %s", underlying)

    def _on_ko_search_finished(self, response: SearchResponse) -> None:
        """Handler für erfolgreiche Suche."""
        self.ko_filter_panel.set_loading(False)
        self.ko_result_panel.set_response(response)

        total = len(response.long) + len(response.short)
        meta = response.meta

        # Fehler ins KI-Log schreiben (die gleichen wie vorher im Tab)
        if meta.errors:
            for err in meta.errors:
                self._log_ko_event("ERROR", err)

            # Bei 403-Fehler: URL zum Debuggen loggen
            if any("403" in err for err in meta.errors):
                from src.derivatives.ko_finder.adapter import OnvistaURLBuilder
                from src.derivatives.ko_finder.config import KOFilterConfig
                url_builder = OnvistaURLBuilder()
                config = self.ko_filter_panel.get_config()
                underlying = self._get_current_underlying() or ""
                debug_url = url_builder.build_long_url(config, underlying)
                self._log_ko_event("DEBUG", f"Versuchte URL: {debug_url[:100]}...")

            # Kurzer Status im Panel
            self.ko_result_panel.set_status("Fehler - siehe KI-Log", "error")
        else:
            # Erfolg ins KI-Log
            cache_info = " (Cache)" if meta.cache_hit else ""
            fetch_time = f" in {meta.fetch_time_ms}ms" if meta.fetch_time_ms else ""
            self._log_ko_event(
                "OK",
                f"Suche abgeschlossen{cache_info}{fetch_time}: "
                f"{len(response.long)} Long, {len(response.short)} Short"
            )

            # Wenn 0 Ergebnisse, Hinweis geben
            if total == 0:
                self._log_ko_event(
                    "INFO",
                    "Keine Produkte gefunden. Prüfe Suchbegriff - Onvista braucht exakte Namen (z.B. 'DAX' statt 'DAX 40')"
                )
                self.ko_result_panel.set_status("Keine Produkte gefunden", "warning")
            else:
                # Kurzer Status im Panel
                self.ko_result_panel.set_status(f"{total} Produkte gefunden", "success")

        logger.info(
            "KO-Finder search completed: %d long, %d short",
            len(response.long),
            len(response.short),
        )

    def _on_ko_search_error(self, error: str) -> None:
        """Handler für Suchfehler."""
        self.ko_filter_panel.set_loading(False)

        # Fehler ins KI-Log (gleiche Meldung wie vorher)
        self._log_ko_event("ERROR", error)

        # Kurzer Status im Panel
        self.ko_result_panel.set_status("Fehler - siehe KI-Log", "error")

        logger.error("KO-Finder search error: %s", error)

    def _on_ko_product_selected(self, wkn: str) -> None:
        """Handler für Produkt-Auswahl."""
        logger.info("KO product selected: %s", wkn)
        # Könnte später für Order-Dialog verwendet werden

    def _get_current_underlying(self) -> str | None:
        """Hole aktuelles Symbol aus Chart."""
        # Versuche verschiedene Wege
        if hasattr(self, 'current_symbol') and self.current_symbol:
            return self.current_symbol

        if hasattr(self, 'chart_widget') and hasattr(self.chart_widget, 'current_symbol'):
            return self.chart_widget.current_symbol

        return None

    def _get_current_price(self) -> float | None:
        """Hole aktuellen Preis aus Chart (wenn verfügbar)."""
        try:
            price = self._get_price_from_chart()
            if price is not None:
                return price

            price = self._get_price_from_features()
            if price is not None:
                return price

        except Exception as e:
            logger.debug("Could not get current price: %s", e)
        return None

    def _get_price_from_chart(self) -> float | None:
        if not hasattr(self, 'chart_widget'):
            return None
        chart = self.chart_widget
        candidates = [
            getattr(chart, '_current_candle_close', None),
        ]
        if hasattr(chart, 'get_current_price'):
            candidates.append(chart.get_current_price())
        candidates.append(getattr(chart, 'last_price', None))
        for candidate in candidates:
            price = self._extract_price(candidate)
            if price is not None:
                return price

        if hasattr(chart, 'data') and chart.data is not None:
            if len(chart.data) > 0 and 'close' in chart.data.columns:
                price = float(chart.data['close'].iloc[-1])
                if price > 0:
                    return price
        return None

    def _get_price_from_features(self) -> float | None:
        if hasattr(self, '_bot_controller') and self._bot_controller:
            if hasattr(self._bot_controller, '_last_features'):
                features = self._bot_controller._last_features
                if features and hasattr(features, 'close') and features.close > 0:
                    return float(features.close)
        return None

    def _extract_price(self, value) -> float | None:
        if value and value > 0:
            return float(value)
        return None

    def _load_ko_settings(self) -> None:
        """Lade KO-Filter Settings."""
        try:
            from src.derivatives.ko_finder.config import KOFilterConfig

            settings = QSettings()
            config = KOFilterConfig.load_from_qsettings(settings)
            self.ko_filter_panel.set_config(config)
        except Exception as e:
            logger.debug("Could not load KO settings: %s", e)

    def _save_ko_settings(self) -> None:
        """Speichere KO-Filter Settings."""
        try:
            config = self.ko_filter_panel.get_config()
            settings = QSettings()
            config.save_to_qsettings(settings)
        except Exception as e:
            logger.debug("Could not save KO settings: %s", e)

    def _log_ko_event(self, entry_type: str, message: str) -> None:
        """
        Log KO-Finder Event in KI-Log.

        Uses _add_ki_log_entry from BotDisplayManagerMixin if available.

        Args:
            entry_type: Type of log entry (SEARCH, OK, WARN, ERROR)
            message: Log message
        """
        prefixed_msg = f"[KO-Finder] {message}"

        # Use KI-Log if available (from BotDisplayManagerMixin)
        if hasattr(self, '_add_ki_log_entry'):
            self._add_ki_log_entry(entry_type, prefixed_msg)
        else:
            # Fallback: nur logger
            logger.info("[%s] %s", entry_type, prefixed_msg)

    def _on_refresh_ko_distance(self) -> None:
        """Handler für KO-Abstand Refresh - holt aktuellen Preis und aktualisiert."""
        price = self._get_current_price()

        if price is None or price <= 0:
            self._log_ko_event(
                "WARN",
                "Kein aktueller Kurs verfügbar für KO-Abstand Berechnung"
            )
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(
                self,
                "KO-Abstand",
                "Kein aktueller Kurs verfügbar.\n"
                "Bitte stellen Sie sicher, dass Marktdaten geladen sind.",
            )
            return

        # Underlying für Logging
        underlying = self._get_current_underlying() or "?"

        # KO-Abstand aktualisieren
        self.ko_result_panel.update_ko_distance(price)

        self._log_ko_event(
            "OK",
            f"KO-Abstand aktualisiert mit Kurs {price:.2f} ({underlying})"
        )
        self.ko_result_panel.set_status(
            f"KO-Abstand aktualisiert @ {price:.2f}",
            "success"
        )
