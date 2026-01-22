"""Chart Statistics Labels Mixin - Issue #26.

Provides methods to update OHLC info, DB status, and price labels.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd

logger = logging.getLogger(__name__)


class ChartStatsLabelsMixin:
    """Mixin for updating chart statistics labels (OHLC, DB status, Price)."""

    def update_ohlc_label(self, data: pd.DataFrame | None = None) -> None:
        """Update OHLC info label with latest candle data.

        Args:
            data: DataFrame with OHLC data. If None, uses self.data.
        """
        if not hasattr(self, 'ohlc_info_label'):
            return

        try:
            df = data if data is not None else getattr(self, 'data', None)

            if df is None or df.empty:
                self.ohlc_info_label.setText("O -- | H -- | L -- | C -- | -- % | V --")
                return

            # Get latest candle
            latest = df.iloc[-1]

            open_price = float(latest.get('open', 0))
            high_price = float(latest.get('high', 0))
            low_price = float(latest.get('low', 0))
            close_price = float(latest.get('close', 0))
            volume = float(latest.get('volume', 0))

            # Calculate change percentage
            if open_price > 0:
                change_pct = ((close_price - open_price) / open_price) * 100
            else:
                change_pct = 0.0

            # Format volume (K, M, B)
            if volume >= 1e9:
                volume_str = f"{volume/1e9:.2f}B"
            elif volume >= 1e6:
                volume_str = f"{volume/1e6:.2f}M"
            elif volume >= 1e3:
                volume_str = f"{volume/1e3:.2f}K"
            else:
                volume_str = f"{volume:.0f}"

            # Format OHLC text
            text = (
                f"O {open_price:,.2f} | "
                f"H {high_price:,.2f} | "
                f"L {low_price:,.2f} | "
                f"C {close_price:,.2f} | "
                f"{change_pct:+.2f} % | "
                f"V {volume_str}"
            )

            # Update color based on change
            if change_pct > 0:
                color = "#26a69a"  # Green
            elif change_pct < 0:
                color = "#ef5350"  # Red
            else:
                color = "#E0E0E0"  # Gray

            self.ohlc_info_label.setText(text)
            self.ohlc_info_label.setStyleSheet(f"""
                color: {color};
                background-color: transparent;
                font-family: monospace;
                font-size: 11px;
                font-weight: bold;
                padding: 5px 10px;
                border-bottom: 1px solid #3D3D3D;
            """)

        except Exception as e:
            logger.warning(f"Failed to update OHLC label: {e}")

    def update_db_status_label(self) -> None:
        """Update DB status label with record count and symbol/interval."""
        if not hasattr(self, 'db_status_label'):
            return

        try:
            # Get data count
            count = 0
            if hasattr(self, 'data') and self.data is not None:
                count = len(self.data)

            # Get symbol and timeframe
            symbol = getattr(self, 'current_symbol', 'N/A')
            timeframe = getattr(self, 'current_timeframe', 'N/A')

            text = f"DB: {count} Einträge ({symbol}/{timeframe})"
            self.db_status_label.setText(text)

        except Exception as e:
            logger.warning(f"Failed to update DB status label: {e}")

    def update_last_price_label(self, price: float | None = None) -> None:
        """Update 'Last Price:' label with current price only.

        Args:
            price: Current price. If None, uses latest close from data.
        """
        if not hasattr(self, 'info_label'):
            return

        try:
            # Get current price
            if price is None:
                if hasattr(self, 'data') and self.data is not None and not self.data.empty:
                    price = float(self.data.iloc[-1].get('close', 0))
                else:
                    self.info_label.setText("Last Price: --")
                    return

            text = f"Last Price: ${price:,.2f}"
            self.info_label.setText(text)

        except Exception as e:
            logger.warning(f"Failed to update last price label: {e}")

    def update_price_label(self, price: float | None = None, reference_price: float | None = None) -> None:
        """Update price info label with current price and daily change since 0 Uhr.

        Args:
            price: Current price. If None, uses latest close from data.
            reference_price: Reference price at 0 Uhr (midnight). If None, searches for candle at 0 Uhr.
        """
        if not hasattr(self, 'price_info_label'):
            return

        try:
            # Get current price
            if price is None:
                if hasattr(self, 'data') and self.data is not None and not self.data.empty:
                    price = float(self.data.iloc[-1].get('close', 0))
                else:
                    self.price_info_label.setText("Preis: --")
                    return

            # Get reference price from 0 Uhr (midnight candle)
            if reference_price is None:
                if hasattr(self, 'data') and self.data is not None and not self.data.empty:
                    reference_price = self._find_midnight_price()
                    if reference_price is None:
                        # Fallback: use first candle's open
                        reference_price = float(self.data.iloc[0].get('open', price))
                else:
                    reference_price = price

            # Calculate change since 0 Uhr
            if reference_price > 0 and reference_price != price:
                change = price - reference_price
                change_pct = (change / reference_price) * 100
                arrow = "▲" if change >= 0 else "▼"
                color = "#26a69a" if change >= 0 else "#ef5350"

                text = f"Preis: ${price:,.2f} {arrow} {abs(change_pct):.2f}%"
            else:
                text = f"Preis: ${price:,.2f}"
                color = "#26a69a"

            self.price_info_label.setText(text)
            self.price_info_label.setStyleSheet(f"""
                color: {color};
                font-family: monospace;
                font-size: 10px;
                font-weight: bold;
                padding: 5px;
            """)

        except Exception as e:
            logger.warning(f"Failed to update price label: {e}")

    def _find_midnight_price(self) -> float | None:
        """Find the close price of the candle at or near midnight (0 Uhr).

        Returns:
            Close price at midnight, or None if not found.
        """
        try:
            from datetime import datetime, timezone, timedelta

            if not hasattr(self, 'data') or self.data is None or self.data.empty:
                return None

            # Check if data has 'time' column (unix timestamp)
            if 'time' not in self.data.columns:
                # Fallback: use first candle
                return float(self.data.iloc[0].get('open'))

            # Get current timezone offset for Germany (CET/CEST)
            # Simple approach: UTC+1 (CET) or UTC+2 (CEST)
            # Better: use proper timezone handling if available, else approximate
            try:
                import zoneinfo
                berlin_tz = zoneinfo.ZoneInfo("Europe/Berlin")
                now = datetime.now(berlin_tz)
            except ImportError:
                # Fallback for older Python versions or missing zoneinfo
                # Approximate with fixed offset (UTC+1 for winter, +2 for summer is hard without lib)
                # Using local system time which is likely correct for the user
                now = datetime.now().astimezone()

            today_midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)

            # Convert to timestamp (and ensure it's comparable with data timestamps)
            midnight_ts = int(today_midnight.timestamp())

            # Find candle closest to midnight
            self.data['time_diff'] = abs(self.data['time'] - midnight_ts)
            midnight_idx = self.data['time_diff'].idxmin()
            midnight_candle = self.data.loc[midnight_idx]

            # Clean up temporary column
            self.data.drop('time_diff', axis=1, inplace=True)

            # Use close of midnight candle as reference
            return float(midnight_candle.get('close', midnight_candle.get('open')))

        except Exception as e:
            logger.warning(f"Failed to find midnight price: {e}")
            # Fallback: use first candle
            if hasattr(self, 'data') and self.data is not None and not self.data.empty:
                return float(self.data.iloc[0].get('open'))
            return None

    def update_all_stats_labels(self, data: pd.DataFrame | None = None, price: float | None = None) -> None:
        """Update all statistics labels (convenience method).

        Args:
            data: DataFrame with OHLC data. If None, uses self.data.
            price: Current price for price label. If None, uses latest close.
        """
        self.update_ohlc_label(data)
        self.update_db_status_label()
        self.update_last_price_label(price)
        self.update_price_label(price)
