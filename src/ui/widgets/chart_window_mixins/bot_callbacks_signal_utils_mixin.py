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

    def _get_strategy_details(self, strategy_name: str) -> str:
        """
        Get detailed strategy information including name and parameters.

        Args:
            strategy_name: Name of the strategy

        Returns:
            Formatted string with strategy name and parameters
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

                    # Add key parameters if available
                    if hasattr(active_strategy, '__dict__'):
                        params = []
                        for key, value in active_strategy.__dict__.items():
                            if not key.startswith('_') and key not in ['name', 'profile']:
                                # Format parameter value
                                if isinstance(value, float):
                                    params.append(f"{key}={value:.2f}")
                                elif isinstance(value, (int, str, bool)):
                                    params.append(f"{key}={value}")

                        if params:
                            # Limit to first 5 parameters to keep it readable
                            params_str += f" ({', '.join(params[:5])})"

                    return params_str

            return strategy_name

        except Exception as e:
            logger.warning(f"Could not get strategy details: {e}")

