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
    _last_regime_name: str | None = None  # Track regime changes for line drawing

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
            debounce_ms: Milliseconds to wait before updating.
                         If 0, runs SYNCHRONOUSLY (blocking) so CEL can use result immediately.
        """
        print(f"[REGIME] trigger_regime_update called (debounce={debounce_ms}ms)", flush=True)
        
        # When debounce_ms=0, run SYNCHRONOUSLY so last_closed_regime() gets updated value
        if debounce_ms == 0:
            print("[REGIME] ⚡ SYNC MODE: Running detection immediately", flush=True)
            self._update_regime_from_data()
            return
        
        if self._regime_update_timer:
            self._regime_update_timer.stop()
            self._regime_update_timer.start(debounce_ms)
            print(f"[REGIME] Timer started, will update in {debounce_ms}ms", flush=True)
        else:
            print("[REGIME] ❌ No timer available!", flush=True)

    def _update_regime_from_data(self) -> None:
        """
        Update regime from current chart data.

        Uses the RegimeDetectorService to detect the regime.
        """
        print("[REGIME] _update_regime_from_data called", flush=True)
        
        try:
            # Get current DataFrame
            df = self._get_chart_dataframe()
            print(f"[REGIME] DataFrame retrieved: {df is not None}, empty: {df.empty if df is not None else 'N/A'}", flush=True)
            if df is None or df.empty:
                logger.debug("No data available for regime detection")
                print("[REGIME] ❌ No DataFrame available", flush=True)
                if self._regime_badge:
                    self._regime_badge.set_regime("UNKNOWN")
                return
            
            print(f"[REGIME] ✅ DataFrame available: {len(df)} rows, columns: {list(df.columns)[:5]}", flush=True)

            # Check if data changed (simple hash check)
            # BUT: Always run the FIRST detection, even if hash matches
            df_hash = str(hash(tuple(df.tail(5)["close"].values)))
            is_first_detection = self._last_regime_name is None
            
            if df_hash == self._last_regime_df_hash and not is_first_detection:
                print(f"[REGIME] ⏭️ Data unchanged (hash match), skipping detection", flush=True)
                return  # No change
            
            if is_first_detection:
                print(f"[REGIME] 🎯 FIRST DETECTION - forcing regime analysis regardless of hash", flush=True)
            else:
                print(f"[REGIME] 🔄 Data changed, detecting regime...", flush=True)
            
            self._last_regime_df_hash = df_hash

            # Detect regime
            from src.core.trading_bot.regime_detector import get_regime_detector

            detector = get_regime_detector()
            result = detector.detect(df)

            if result and self._regime_badge:
                self._regime_badge.set_regime_from_result(result)
                
                # Draw regime line if regime changed OR first detection
                current_regime = result.regime.value if hasattr(result.regime, 'value') else str(result.regime)
                print(f"[REGIME] Current: {current_regime}, Last: {self._last_regime_name}", flush=True)
                
                if current_regime != self._last_regime_name:
                    if self._last_regime_name is None:
                        print(f"[REGIME] 🎨 First regime detected: {current_regime} - Drawing initial line", flush=True)
                    else:
                        print(f"[REGIME] 🎨 Regime changed! Drawing line for {current_regime}", flush=True)
                    self._draw_regime_line_for_change(current_regime, df)
                else:
                    print(f"[REGIME] No change (still {current_regime})", flush=True)
                
                self._last_regime_name = current_regime
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
        # Try common attribute names (priority order)
        if hasattr(self, "data") and self.data is not None:
            return self.data
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

    def _draw_regime_line_for_change(self, regime_name: str, df: "pd.DataFrame") -> None:
        """Draw regime line in chart when regime changes.
        
        Called by trigger_regime_analysis() when a regime change is detected.
        
        Args:
            regime_name: New regime name
            df: Current chart dataframe
        """
        print(f"[REGIME] _draw_regime_line_for_change called for {regime_name}", flush=True)
        
        # Check if chart has add_regime_line method (from BotOverlayMixin)
        if not hasattr(self, 'add_regime_line'):
            logger.warning("❌ Chart has no add_regime_line method - skipping regime line drawing")
            print("[REGIME] ❌ No add_regime_line method!", flush=True)
            return
        
        print(f"[REGIME] ✅ add_regime_line method exists", flush=True)
        
        try:
            # Get last candle timestamp
            if df is None or df.empty:
                print("[REGIME] ❌ DataFrame is None or empty!", flush=True)
                return
            
            print(f"[REGIME] DataFrame has {len(df)} rows", flush=True)
            
            last_timestamp = df.iloc[-1]['timestamp'] if 'timestamp' in df.columns else df.index[-1]
            print(f"[REGIME] Last timestamp (raw): {last_timestamp}", flush=True)
            
            # Convert to seconds (not ms)
            if last_timestamp > 1e10:
                last_timestamp = int(last_timestamp / 1000)
            else:
                last_timestamp = int(last_timestamp)
            
            print(f"[REGIME] Last timestamp (converted): {last_timestamp}", flush=True)
            
            # Generate unique line ID
            import time
            line_id = f"regime_{regime_name}_{int(time.time())}"
            
            print(f"[REGIME] 🎨 Drawing line: {line_id} at {last_timestamp}", flush=True)
            
            # Draw line using BotOverlayMixin API
            self.add_regime_line(
                line_id=line_id,
                timestamp=last_timestamp,
                regime_name=regime_name,
                color=None,  # Auto-select color
                label=regime_name
            )
            logger.info(f"✅ Drew regime line for {regime_name} at timestamp {last_timestamp}")
            print(f"[REGIME] ✅ Line drawn successfully!", flush=True)
            
        except Exception as e:
            logger.error(f"❌ Failed to draw regime line: {e}", exc_info=True)
            print(f"[REGIME] ❌ Error drawing line: {e}", flush=True)

    def get_regime_badge_widget(self):
        """
        Get the regime badge widget for external use.

        Returns:
            RegimeBadgeWidget or None
        """
        return self._regime_badge
