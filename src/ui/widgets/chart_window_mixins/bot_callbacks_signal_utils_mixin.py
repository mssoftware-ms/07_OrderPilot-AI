from __future__ import annotations

import logging
from datetime import datetime
from decimal import Decimal

from PyQt6.QtCore import Qt, QDateTime
from PyQt6.QtGui import QColor, QIcon
from PyQt6.QtWidgets import QTableWidgetItem

logger = logging.getLogger(__name__)

class BotCallbacksSignalUtilsMixin:
    """Signal utilities and helpers"""

    def _extract_signal_fields(self, signal) -> tuple[str, str, float, float, str, float]:
        """Extract key fields from Signal object.

        Args:
            signal: Signal object from bot controller

        Returns:
            Tuple of (signal_type, side, entry_price, score, strategy_name, signal_stop_price)
        """
        try:
            # Extract signal type (candidate or confirmed)
            signal_type = signal.signal_type.value if hasattr(signal.signal_type, 'value') else str(signal.signal_type)

            # Extract side (long or short)
            side = signal.side.value if hasattr(signal.side, 'value') else str(signal.side)

            # Extract prices and score
            entry_price = float(signal.entry_price)
            score = float(signal.score)
            signal_stop_price = float(signal.stop_loss_price)

            # Extract strategy name
            strategy_name = signal.strategy_name if signal.strategy_name else "Unknown"

            return signal_type, side, entry_price, score, strategy_name, signal_stop_price

        except Exception as e:
            logger.error(f"Error extracting signal fields: {e}")
            # Return safe defaults
            return "candidate", "long", 0.0, 0.0, "Unknown", 0.0

    def _map_signal_status(self, signal_type: str) -> str:
        """Map signal type to display status.

        Args:
            signal_type: Type of signal ('candidate', 'confirmed', etc.)

        Returns:
            Status string for display ('PENDING', 'ENTERED', etc.)
        """
        status_map = {
            "candidate": "PENDING",
            "confirmed": "ENTERED",
            "exit": "EXITED",
            "stopped": "SL",
            "cancelled": "CANCELLED",
        }
        return status_map.get(signal_type.lower(), "PENDING")

    def _get_strategy_details(self, strategy_name: str) -> str:
        """
        Get detailed strategy information including name and ALL parameters.

        Issue #7: Now shows ALL parameters, not just first 5.
        Display without line breaks, full text visible via tooltip.

        Args:
            strategy_name: Name of the strategy

        Returns:
            Formatted string with strategy name and ALL parameters
        """
        if not strategy_name or strategy_name == "Neutral":
            return "Neutral (keine Strategie)"

        try:
            # Try to get strategy parameters from bot controller
            if self._bot_controller and hasattr(self._bot_controller, '_active_strategy'):
                active_strategy = self._bot_controller._active_strategy
                if active_strategy:
                    # Get strategy profile with parameters
                    params_str = f"{strategy_name}"

                    # Add ALL parameters if available (Issue #7: removed [:5] limit)
                    if hasattr(active_strategy, '__dict__'):
                        params = []
                        for key, value in active_strategy.__dict__.items():
                            if not key.startswith('_') and key not in ['name', 'profile']:
                                # Format parameter value
                                if isinstance(value, float):
                                    params.append(f"{key}={value:.2f}")
                                elif isinstance(value, (int, str, bool)):
                                    params.append(f"{key}={value}")
                                elif isinstance(value, (list, tuple)) and len(value) < 5:
                                    # Small lists/tuples
                                    params.append(f"{key}={value}")
                                elif value is not None:
                                    # Other types (converted to string)
                                    params.append(f"{key}={str(value)[:30]}")

                        if params:
                            # Issue #7: Show ALL parameters (no limit), single line
                            params_str += f" ({', '.join(params)})"

                    return params_str

            return strategy_name

        except Exception as e:
            logger.warning(f"Could not get strategy details: {e}")
            return strategy_name

