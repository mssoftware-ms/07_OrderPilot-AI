from __future__ import annotations

import json
import logging

from PyQt6.QtCore import QTimer

logger = logging.getLogger(__name__)

class BotPositionPersistenceStorageMixin:
    """BotPositionPersistenceStorageMixin extracted from BotPositionPersistenceMixin."""
    def _get_signal_history_key(self) -> str:
        """Get settings key for signal history based on current symbol."""
        symbol = getattr(self, 'symbol', '') or self._current_bot_symbol
        safe_symbol = symbol.replace("/", "_").replace(":", "_")
        return f"SignalHistory/{safe_symbol}"
    def _save_signal_history(self) -> None:
        """Save signal history to settings for the current symbol."""
        key = self._get_signal_history_key()
        if not key or key == "SignalHistory/":
            return

        try:
            if not self._signal_history:
                # Clearing history should also clear persisted storage
                self._bot_settings.remove(key)
                logger.info(f"Cleared signal history for {key}")
                return

            history_json = json.dumps(self._signal_history)
            self._bot_settings.setValue(key, history_json)
            logger.info(f"Saved {len(self._signal_history)} signals for {key}")
        except Exception as e:
            logger.error(f"Failed to save signal history: {e}")
    def _load_signal_history(self) -> None:
        """Load signal history from settings for the current symbol."""
        key = self._get_signal_history_key()
        if not key or key == "SignalHistory/":
            return

        try:
            history_json = self._bot_settings.value(key)
            if history_json:
                if isinstance(history_json, str):
                    self._signal_history = json.loads(history_json)
                else:
                    self._signal_history = history_json

                # Ensure only one open position after loading; drop newer duplicates
                if hasattr(self, "_enforce_single_open_signal"):
                    self._enforce_single_open_signal(refresh=False)

                logger.info(f"Loaded {len(self._signal_history)} signals for {key}")

                if hasattr(self, 'signals_table'):
                    self._update_signals_table()

                # Check for active positions
                active_positions = [s for s in self._signal_history
                                   if s.get("status") == "ENTERED" and s.get("is_open", False)]
                if active_positions:
                    logger.info(f"Found {len(active_positions)} active positions, scheduling restoration")
                    self._pending_position_restore = active_positions
                    if hasattr(self, 'chart_widget') and hasattr(self.chart_widget, 'data_loaded'):
                        self.chart_widget.data_loaded.connect(self._on_chart_data_loaded_restore_position)
                    else:
                        QTimer.singleShot(2000, lambda: self._restore_persisted_position(active_positions))

        except Exception as e:
            logger.error(f"Failed to load signal history: {e}")
