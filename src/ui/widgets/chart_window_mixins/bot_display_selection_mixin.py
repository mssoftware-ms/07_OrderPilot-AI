from __future__ import annotations



class BotDisplaySelectionMixin:
    """BotDisplaySelectionMixin extracted from BotDisplayManagerMixin."""
    def _has_signals_table_selection(self) -> bool:
        """Return True if a row in the signals table is selected."""
        if not hasattr(self, "signals_table"):
            return False
        try:
            model = self.signals_table.selectionModel()
            return model is not None and model.hasSelection()
        except Exception:
            return False
    def _get_selected_signal_from_table(self) -> dict | None:
        """Resolve the selected signals table row to a signal dict."""
        if not self._has_signals_table_selection():
            return None
        if getattr(self, "_signals_table_updating", False):
            return None
        try:
            selected = self.signals_table.selectionModel().selectedRows()
            if not selected:
                return None
            row = selected[0].row()
        except Exception:
            return None

        recent_signals = list(reversed(self._signal_history))
        if row < 0 or row >= len(recent_signals):
            return None
        return recent_signals[row]
    def _update_current_position_from_selection(self) -> bool:
        """Update Current Position panel from selected signals table row."""
        signal = self._get_selected_signal_from_table()
        if not signal:
            return False
        self._render_current_position_from_signal(signal)
        return True
    def _on_signals_table_selection_changed(self) -> None:
        """Handle selection changes in signals table."""
        if getattr(self, "_signals_table_updating", False):
            return
        if not self._update_current_position_from_selection():
            # No selection -> fall back to normal current position display
            self._update_bot_display()
