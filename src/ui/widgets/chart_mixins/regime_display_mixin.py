"""
Regime Display Mixin for Chart Widgets.

Adds regime detection and display functionality to chart widgets.

Phase 2.2 der Bot-Integration.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from PyQt6.QtCore import QTimer

if TYPE_CHECKING:
    import pandas as pd

logger = logging.getLogger(__name__)


class RegimeDisplayMixin:
    """
    Mixin für Regime-Anzeige in Chart-Widgets.

    Fügt folgende Funktionalität hinzu:
    - Regime Badge in der Toolbar
    - Automatische Regime-Erkennung bei Datenänderung
    - Integration mit RegimeDetectorService

    Usage:
        class MyChartWidget(RegimeDisplayMixin, QWidget):
            def __init__(self):
                super().__init__()
                self._setup_regime_display()
    """

    _regime_badge = None
    _regime_update_timer: QTimer | None = None
    _last_regime_df_hash: str = ""

    def _setup_regime_display(self) -> None:
        """
        Setup regime display components.

        Should be called after toolbar is created.
        """
        try:
            from src.ui.widgets.regime_badge_widget import RegimeBadgeWidget

            # Create badge
            self._regime_badge = RegimeBadgeWidget(compact=True, show_icon=True)
            self._regime_badge.clicked.connect(self._on_regime_badge_clicked)
            self._regime_badge.regime_changed.connect(self._on_regime_changed)

            # Add to toolbar if exists
            if hasattr(self, "_add_regime_badge_to_toolbar"):
                self._add_regime_badge_to_toolbar()

            # Setup auto-update timer (debounce)
            self._regime_update_timer = QTimer()
            self._regime_update_timer.setSingleShot(True)
            self._regime_update_timer.timeout.connect(self._update_regime_from_data)

            logger.debug("Regime display setup complete")

        except ImportError as e:
            logger.warning(f"Could not setup regime display: {e}")

    def _add_regime_badge_to_toolbar(self) -> None:
        """
        Add regime badge to the second toolbar row.

        Override this method if toolbar structure differs.
        """
        # This method should be implemented in the toolbar mixin
        pass

    def trigger_regime_update(self, debounce_ms: int = 500) -> None:
        """
        Trigger regime update with debounce.

        Args:
            debounce_ms: Milliseconds to wait before updating
        """
        if self._regime_update_timer:
            self._regime_update_timer.stop()
            self._regime_update_timer.start(debounce_ms)

    def _update_regime_from_data(self) -> None:
        """
        Update regime from current chart data.

        Uses the RegimeDetectorService to detect the regime.
        """
        try:
            # Get current DataFrame
            df = self._get_chart_dataframe()
            if df is None or df.empty:
                logger.debug("No data available for regime detection")
                if self._regime_badge:
                    self._regime_badge.set_regime("UNKNOWN")
                return

            # Check if data changed (simple hash check)
            df_hash = str(hash(tuple(df.tail(5)["close"].values)))
            if df_hash == self._last_regime_df_hash:
                return  # No change
            self._last_regime_df_hash = df_hash

            # Detect regime
            from src.core.trading_bot.regime_detector import get_regime_detector

            detector = get_regime_detector()
            result = detector.detect(df)

            if result and self._regime_badge:
                self._regime_badge.set_regime_from_result(result)
                logger.debug(f"Regime updated: {result.regime.value}")

        except Exception as e:
            logger.error(f"Failed to update regime: {e}", exc_info=True)
            if self._regime_badge:
                self._regime_badge.set_regime("UNKNOWN")

    def _get_chart_dataframe(self) -> "pd.DataFrame | None":
        """
        Get current DataFrame from chart.

        Override this method to provide the actual DataFrame.

        Returns:
            DataFrame with OHLCV data or None
        """
        # Try common attribute names
        if hasattr(self, "_current_df"):
            return self._current_df
        if hasattr(self, "df"):
            return self.df
        if hasattr(self, "_data"):
            return self._data
        if hasattr(self, "chart_data"):
            return self.chart_data

        return None

    def set_regime_manually(
        self,
        regime: str,
        adx: float | None = None,
        gate_reason: str = "",
        allows_entry: bool = True,
    ) -> None:
        """
        Set regime manually (e.g., from MarketContext).

        Args:
            regime: Regime type string
            adx: Optional ADX value
            gate_reason: Reason for blocking entries
            allows_entry: Whether market entries are allowed
        """
        if self._regime_badge:
            self._regime_badge.set_regime(regime, adx, gate_reason, allows_entry)

    def set_regime_from_context(self, context) -> None:
        """
        Set regime from MarketContext.

        Args:
            context: MarketContext object
        """
        if context is None:
            if self._regime_badge:
                self._regime_badge.set_regime("UNKNOWN")
            return

        regime_str = context.regime.value if hasattr(context.regime, "value") else str(context.regime)
        self.set_regime_manually(
            regime=regime_str,
            adx=context.indicators.adx if context.indicators else None,
            gate_reason="",  # Gate reason not stored in MarketContext
            allows_entry=context.is_valid_for_trading(),
        )

    def get_current_regime(self) -> str | None:
        """
        Get current regime type.

        Returns:
            Regime type string or None
        """
        if self._regime_badge:
            return self._regime_badge.get_regime()
        return None

    def _on_regime_badge_clicked(self) -> None:
        """Handle regime badge click - show details."""
        logger.debug("Regime badge clicked")
        # Could open a details dialog or show extended info
        # For now, just log

    def _on_regime_changed(self, regime: str) -> None:
        """
        Handle regime change event.

        Args:
            regime: New regime type
        """
        logger.info(f"Regime changed to: {regime}")
        # Emit signal or notify other components if needed

    def get_regime_badge_widget(self):
        """
        Get the regime badge widget for external use.

        Returns:
            RegimeBadgeWidget or None
        """
        return self._regime_badge
