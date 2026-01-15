"""Bot Derivative Mixin - Integration of KO products into trading signals.

Handles:
- Automatic KO product search on signal confirmation
- Derivative selection and storage in signal history
- P&L calculation for derivatives
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.derivatives.ko_finder.models import SearchResponse

logger = logging.getLogger(__name__)


class BotDerivativeMixin:
    """Mixin providing derivative trading integration for ChartWindow."""

    def _init_derivative_state(self) -> None:
        """Initialize derivative-related state."""
        self._derivative_workers: list = []  # Prevent GC of workers

    def _fetch_derivative_for_signal(self, signal: dict) -> None:
        """
        Search for best KO product for a confirmed signal.

        Called when a signal transitions from candidate to confirmed
        and Derivathandel is enabled.

        Args:
            signal: The confirmed signal dict from _signal_history
        """
        from src.derivatives.ko_finder.config import KOFilterConfig

        from .ko_finder_mixin import KOFinderWorker

        # Get underlying info
        underlying = self._get_current_underlying()
        if not underlying:
            logger.warning("Cannot fetch derivative: no underlying symbol")
            return

        price = self._get_current_price()
        direction = signal.get("side", "").upper()

        if direction not in ("LONG", "SHORT"):
            logger.warning("Cannot fetch derivative: invalid direction %s", direction)
            return

        # Get filter config from KO-Finder panel if available
        if hasattr(self, "ko_filter_panel"):
            config = self.ko_filter_panel.get_config()
        else:
            config = KOFilterConfig()

        logger.info(
            "Fetching derivative for %s %s signal (price=%.2f)",
            underlying,
            direction,
            price or 0,
        )

        # Create and start worker
        worker = KOFinderWorker(underlying, config, price)
        worker.finished.connect(
            lambda resp: self._on_derivative_fetched(signal, resp, direction)
        )
        worker.error.connect(
            lambda err: self._on_derivative_fetch_error(signal, err)
        )
        worker.start()

        # Keep reference to prevent GC
        self._derivative_workers.append(worker)

    def _on_derivative_fetched(
        self, signal: dict, response: SearchResponse, direction: str
    ) -> None:
        """
        Process KO-Finder result and store best product in signal.

        Args:
            signal: The signal dict to update
            response: SearchResponse from KO-Finder
            direction: "LONG" or "SHORT"
        """
        self._update_ko_result_panel(response, direction)

        # Select products based on direction
        products = response.long if direction == "LONG" else response.short

        if not products:
            self._handle_no_products(signal, response, direction)
            return

        # Best product is already first (sorted by score)
        best = products[0]

        if not self._validate_best_product(best, signal):
            return

        # Store derivative info in signal
        signal["derivative"] = self._build_derivative_payload(best, signal)

        logger.info(
            "Selected derivative: WKN=%s, Hebel=%.1f, Spread=%.2f%%, Score=%.1f",
            best.wkn,
            best.leverage or 0,
            best.spread_pct or 0,
            best.score or 0,
        )

        # Log to KI Log panel
        self._log_derivative_event(
            signal,
            f"KO-Produkt ausgewählt: {best.wkn} (Hebel {best.leverage:.1f}x, "
            f"Score {best.score:.0f})",
        )

        self._finalize_ko_result_panel(response, direction, best)

        # Update displays
        self._update_signals_table()
        self._update_bot_display()

        # Cleanup finished workers
        self._cleanup_derivative_workers()

    def _update_ko_result_panel(self, response: SearchResponse, direction: str) -> None:
        if hasattr(self, "ko_result_panel"):
            logger.info(
                "Updating KO-Finder panel with %d long, %d short products",
                len(response.long),
                len(response.short),
            )
            self.ko_result_panel.set_response(response)
            if hasattr(self.ko_result_panel, "tabs"):
                self.ko_result_panel.tabs.setCurrentIndex(0 if direction == "LONG" else 1)
        else:
            logger.warning("ko_result_panel not found - KO-Finder tab may not be initialized")

    def _handle_no_products(self, signal: dict, response: SearchResponse, direction: str) -> None:
        logger.warning(
            "No KO products found for %s %s",
            response.underlying,
            direction,
        )
        self._log_derivative_event(
            signal,
            f"Kein KO-Produkt gefunden für {direction}",
            is_error=True,
        )
        if hasattr(self, "ko_result_panel"):
            self.ko_result_panel.set_status(
                f"Bot: Keine {direction}-Produkte gefunden", "warning"
            )

    def _validate_best_product(self, best, signal: dict) -> bool:
        if best.score is None or best.score < 20:
            logger.warning(
                "Best product score too low: %s (%.1f)",
                best.wkn,
                best.score or 0,
            )
            self._log_derivative_event(
                signal,
                f"Bestes Produkt {best.wkn} Score zu niedrig ({best.score or 0:.0f})",
                is_error=True,
            )
            if hasattr(self, "ko_result_panel"):
                self.ko_result_panel.set_status(
                    f"Bot: Score zu niedrig ({best.wkn}: {best.score or 0:.0f})",
                    "warning",
                )
            return False

        if not best.quote.is_valid:
            logger.warning("Best product has invalid quote: %s", best.wkn)
            self._log_derivative_event(
                signal,
                f"Produkt {best.wkn} hat ungültigen Kurs",
                is_error=True,
            )
            if hasattr(self, "ko_result_panel"):
                self.ko_result_panel.set_status(
                    f"Bot: Ungültiger Kurs ({best.wkn})", "warning"
                )
            return False
        return True

    def _build_derivative_payload(self, best, signal: dict) -> dict:
        return {
            "wkn": best.wkn,
            "isin": best.isin,
            "leverage": best.leverage,
            "spread_pct": best.spread_pct,
            "ask": best.quote.ask,
            "bid": best.quote.bid,
            "ko_level": best.knockout_level,
            "ko_distance_pct": best.ko_distance_pct,
            "score": best.score,
            "issuer": best.issuer,
            "entry_underlying": signal.get("price"),
            "source_url": best.source_url,
        }

    def _finalize_ko_result_panel(self, response: SearchResponse, direction: str, best) -> None:
        if hasattr(self, "ko_result_panel"):
            logger.info(
                "Updating KO-Finder panel with %d long, %d short products",
                len(response.long),
                len(response.short),
            )
            self.ko_result_panel.set_response(response)
            self.ko_result_panel.set_status(
                f"Bot: {direction} → {best.wkn} (Score {best.score:.0f})",
                "success",
            )
            if hasattr(self.ko_result_panel, "highlight_product"):
                self.ko_result_panel.highlight_product(best.wkn)
        else:
            logger.warning("ko_result_panel not found - KO-Finder tab may not be initialized")

    def _on_derivative_fetch_error(self, signal: dict, error: str) -> None:
        """Handle derivative fetch error."""
        logger.error("Derivative fetch failed for signal: %s", error)
        self._log_derivative_event(signal, f"Derivat-Suche fehlgeschlagen: {error}", is_error=True)
        self._cleanup_derivative_workers()

    def _log_derivative_event(
        self, signal: dict, message: str, is_error: bool = False
    ) -> None:
        """Log derivative event to KI Log panel."""
        if hasattr(self, "_add_ki_log_entry"):
            log_type = "ERROR" if is_error else "DERIV"
            self._add_ki_log_entry(log_type, message)

    def _cleanup_derivative_workers(self) -> None:
        """Remove finished workers from list."""
        self._derivative_workers = [
            w for w in self._derivative_workers if w.isRunning()
        ]

    def _get_current_underlying(self) -> str | None:
        """Get current underlying symbol for KO search."""
        # Try chart widget symbol
        if hasattr(self, "chart_widget"):
            symbol = getattr(self.chart_widget, "current_symbol", None)
            if symbol:
                # Strip exchange suffix (e.g., "BTC/USD" -> "BTC")
                return symbol.split("/")[0].split("-")[0].upper()

        # Try bot symbol label
        if hasattr(self, "bot_symbol_label"):
            symbol = self.bot_symbol_label.text()
            if symbol and symbol != "-":
                return symbol.split("/")[0].split("-")[0].upper()

        return None

    def _calculate_derivative_pnl_for_signal(
        self, signal: dict, current_price: float
    ) -> dict | None:
        """
        Calculate derivative P&L for a signal with derivative.

        Args:
            signal: Signal dict containing derivative info
            current_price: Current underlying price

        Returns:
            Dict with pnl_eur, pnl_pct, or None if not calculable
        """
        deriv = signal.get("derivative")
        if not deriv:
            return None

        entry_underlying = deriv.get("entry_underlying")
        if not entry_underlying or entry_underlying <= 0:
            return None

        leverage = deriv.get("leverage")
        spread_pct = deriv.get("spread_pct")
        ask_entry = deriv.get("ask")

        if not all([leverage, spread_pct is not None, ask_entry]):
            return None

        try:
            from src.derivatives.ko_finder.pnl_calculator import (
                Direction,
                calculate_derivative_pnl,
            )

            direction = Direction.LONG if signal.get("side") == "long" else Direction.SHORT
            invested = signal.get("invested", 1000)

            result = calculate_derivative_pnl(
                direction=direction,
                leverage=leverage,
                spread_pct=spread_pct,
                u0=entry_underlying,
                u1=current_price,
                capital=invested,
                ask_entry=ask_entry,
            )

            return {
                "pnl_eur": result.pnl_eur,
                "pnl_pct": result.pnl_pct,
                "v1": result.v1,
                "p_bid1": result.p_bid1,
            }
        except Exception as e:
            logger.debug("Could not calculate derivative P&L: %s", e)
            return None
