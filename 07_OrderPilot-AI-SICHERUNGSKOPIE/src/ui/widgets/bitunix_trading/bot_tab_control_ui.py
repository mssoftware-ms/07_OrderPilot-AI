"""Bot Tab Control UI - UI Updates and Visual Elements.

Refactored from 1,160 LOC monolith using composition pattern.

Module 4/6 of bot_tab_control.py split.

Contains:
- Status Panel management (toggle, update)
- Journal management (toggle, logging)
- SL/TP Visual Bar (update, reset)
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING

from PyQt6.QtGui import QTextCursor

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class BotTabControlUI:
    """Helper für UI Updates und Visual Elements."""

    def __init__(self, parent):
        """
        Args:
            parent: BotTabControl Instanz
        """
        self.parent = parent

    def toggle_status_panel(self) -> None:
        """Togglet die Sichtbarkeit des Status Panels."""
        if self.parent.parent._status_panel:
            visible = self.parent.parent.status_panel_btn.isChecked()
            self.parent.parent._status_panel.setVisible(visible)
            if visible:
                self.parent._log("📊 Status Panel eingeblendet")
                self._update_status_panel()
            else:
                self.parent._log("📊 Status Panel ausgeblendet")

    def on_status_panel_refresh(self) -> None:
        """Callback wenn Status Panel Refresh angefordert wird."""
        self._update_status_panel()

    def _update_status_panel(self) -> None:
        """Aktualisiert das Status Panel mit aktuellen Engine-Ergebnissen.

        Nutzt die Ergebnisse aus der neuen Engine-Pipeline:
        - self.parent.parent._last_regime_result (von RegimeDetectorService)
        - self.parent.parent._last_entry_score (von EntryScoreEngine)
        - self.parent.parent._last_llm_result (von LLMValidationService)
        - self.parent.parent._last_trigger_result (von TriggerExitEngine)
        - self.parent.parent._last_leverage_result (von LeverageRulesEngine)
        """
        if not self.parent.parent._status_panel:
            return

        try:
            # Regime Result
            regime_result = None
            if self.parent.parent._last_market_context and self.parent.parent._last_market_context.regime:
                regime_result = self.parent.parent._last_market_context.regime

            # Entry Score Result
            score_result = self.parent.parent._last_entry_score

            # LLM Validation Result
            llm_result = self.parent.parent._last_llm_result

            # Trigger Result
            trigger_result = self.parent.parent._last_trigger_result

            # Leverage Result
            leverage_result = self.parent.parent._last_leverage_result

            # Update all at once
            self.parent.parent._status_panel.update_all(
                regime_result=regime_result,
                score_result=score_result,
                llm_result=llm_result,
                trigger_result=trigger_result,
                leverage_result=leverage_result,
            )

            logger.debug("Status Panel updated with new engine results")

        except Exception as e:
            logger.warning(f"Failed to update status panel: {e}")

    def toggle_journal(self) -> None:
        """Togglet die Sichtbarkeit des Trading Journals."""
        if self.parent.parent._journal_widget:
            visible = self.parent.parent.journal_btn.isChecked()
            self.parent.parent._journal_widget.setVisible(visible)
            if visible:
                self.parent._log("📔 Trading Journal eingeblendet")
                self.parent.parent._journal_widget.refresh_trades()
            else:
                self.parent._log("📔 Trading Journal ausgeblendet")

    def _log_engine_results_to_journal(self) -> None:
        """Loggt Engine-Ergebnisse ins Trading Journal mit MarketContext ID."""
        if not self.parent.parent._journal_widget or not self.parent.parent._last_market_context:
            return

        try:
            # Entry Score
            if self.parent.parent._last_entry_score:
                entry_data = {
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "context_id": self.parent.parent._last_market_context.context_id,
                    "score": self.parent.parent._last_entry_score.final_score,
                    "quality": self.parent.parent._last_entry_score.quality.value,
                    "direction": self.parent.parent._last_entry_score.direction.value,
                    "components": {
                        comp.name: comp.value for comp in self.parent.parent._last_entry_score.components
                    },
                }
                self.parent.parent._journal_widget.add_entry_score(entry_data)

            # LLM Result
            if self.parent.parent._last_llm_result:
                llm_data = {
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "context_id": self.parent.parent._last_market_context.context_id,
                    "action": self.parent.parent._last_llm_result.action.value,
                    "tier": self.parent.parent._last_llm_result.tier.value,
                    "reasoning": (
                        self.parent.parent._last_llm_result.reasoning[:200]
                        if self.parent.parent._last_llm_result.reasoning
                        else ""
                    ),
                }
                self.parent.parent._journal_widget.add_llm_output(llm_data)

        except Exception as e:
            logger.exception(f"Failed to log engine results to journal: {e}")

    def _update_sltp_bar(self, current_price: float) -> None:
        """Aktualisiert den visuellen SL/TP Balken im Signals-Tab.

        Der Balken zeigt die Position zwischen SL (0%) und TP (100%):
        - Rot (links) = Stop Loss
        - Orange (mitte) = aktueller Preis
        - Grün (rechts) = Take Profit

        Args:
            current_price: Aktueller Marktpreis
        """
        if not self.parent.parent._current_position:
            return

        try:
            sl_price = self.parent.parent._position_stop_loss
            tp_price = self.parent.parent._position_take_profit
            entry_price = self.parent.parent._position_entry_price
            side = self.parent.parent._position_side

            # Berechne Position zwischen SL und TP (0-100%)
            if side == "long":
                # Long: SL < Entry < Current < TP
                price_range = tp_price - sl_price
                current_offset = current_price - sl_price
            else:
                # Short: TP < Current < Entry < SL
                price_range = sl_price - tp_price
                current_offset = sl_price - current_price

            # Position in % (0 = SL, 100 = TP)
            if price_range > 0:
                position_pct = (current_offset / price_range) * 100
                position_pct = max(0, min(100, position_pct))  # Clamp 0-100
            else:
                position_pct = 50  # Fallback

            # Update Bar
            self.parent.parent.sltp_bar.setValue(int(position_pct))

            # Update Labels
            self.parent.parent.sltp_sl_label.setText(f"SL: {sl_price:.2f}")
            self.parent.parent.sltp_current_label.setText(f"{current_price:.2f}")
            self.parent.parent.sltp_tp_label.setText(f"TP: {tp_price:.2f}")

            # Berechne P&L
            quantity = self.parent.parent._position_quantity
            if side == "long":
                pnl = (current_price - entry_price) * quantity
            else:
                pnl = (entry_price - current_price) * quantity

            pnl_pct = (pnl / (entry_price * quantity)) * 100

            # Update P&L Label mit Farbe
            pnl_color = "#26a69a" if pnl >= 0 else "#ef5350"
            pnl_sign = "+" if pnl >= 0 else ""
            self.parent.parent.sltp_pnl_label.setText(f"P&L: {pnl_sign}${pnl:.2f} ({pnl_sign}{pnl_pct:.2f}%)")
            self.parent.parent.sltp_pnl_label.setStyleSheet(
                f"color: {pnl_color}; font-weight: bold; font-size: 12px; margin-top: 5px;"
            )

        except Exception as e:
            logger.exception(f"Failed to update SL/TP bar: {e}")

    def _reset_sltp_bar(self) -> None:
        """Setzt den SL/TP Visual Bar auf Default-Werte zurück (keine aktive Position)."""
        try:
            # Reset Labels
            self.parent.parent.sltp_sl_label.setText("SL: —")
            self.parent.parent.sltp_current_label.setText("—")
            self.parent.parent.sltp_tp_label.setText("TP: —")
            self.parent.parent.sltp_pnl_label.setText("P&L: —")
            self.parent.parent.sltp_pnl_label.setStyleSheet("color: #888; font-size: 11px; margin-top: 5px;")

            # Reset Bar
            self.parent.parent.sltp_bar.setValue(50)  # Mitte

            logger.debug("SL/TP bar reset to default state (no position)")
        except Exception as e:
            logger.exception(f"Failed to reset SL/TP bar: {e}")
