"""Bot Signals Exit Mixin - Exit signal handling and position closing.

This module handles:
- Manual position closing (sell button)
- Async order execution
- Chart element drawing (Entry, SL, TR lines)
- Signal deletion (clear selected/all)
- Sell button state management
"""

from __future__ import annotations

import asyncio
import logging
from decimal import Decimal

from PyQt6.QtWidgets import QMessageBox

logger = logging.getLogger(__name__)


class BotSignalsExitMixin:
    """Mixin for exit signal handling and position closing.

    This mixin provides:
    - Signal deletion (_on_clear_selected_signal, _on_clear_all_signals)
    - Manual position closing (_on_sell_position_clicked)
    - Async sell order execution (_execute_sell_order)
    - Sell button state management (_update_sell_button_state)
    - Chart elements drawing (_on_draw_chart_elements_clicked)
    """

    # ==========================================
    # Signal Deletion
    # ==========================================

    def _on_clear_selected_signal(self) -> None:
        """Delete selected row(s) from signals table.

        Deletes from both UI table and _signal_history.
        Rows are deleted from bottom to top to avoid index shifting.
        """
        selected_rows = self.signals_table.selectionModel().selectedRows()
        if not selected_rows:
            return

        # Delete from bottom to top to avoid index shifting
        rows_to_delete = sorted([idx.row() for idx in selected_rows], reverse=True)

        # Map table rows (latest on top) back to _signal_history indices
        history_len = len(self._signal_history)
        indices_to_delete = {
            history_len - 1 - row for row in rows_to_delete
            if 0 <= history_len - 1 - row < history_len
        }

        # Remove from history and UI
        if indices_to_delete:
            self._signal_history = [
                sig for i, sig in enumerate(self._signal_history)
                if i not in indices_to_delete
            ]
            self._save_signal_history()

        for row in rows_to_delete:
            self.signals_table.removeRow(row)

        # Refresh to ensure P&L / selection stays consistent
        self._update_signals_table()

    def _on_clear_all_signals(self) -> None:
        """Delete all rows from signals table with confirmation."""
        if self.signals_table.rowCount() == 0:
            return

        reply = QMessageBox.question(
            self,
            "Alle Signale löschen",
            f"Alle {self.signals_table.rowCount()} Signale aus der Tabelle löschen?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self._signal_history.clear()
            self._save_signal_history()
            self.signals_table.setRowCount(0)
            self._update_signals_table()

    # ==========================================
    # Manual Position Closing
    # ==========================================

    def _on_sell_position_clicked(self) -> None:
        """Sell current position with limit order 0.05% below/above current price.

        Issue #11: Places a limit order to close the active position.
        - For long positions: SELL 0.05% below current price
        - For short positions: BUY 0.05% above current price
        """
        # Find active position
        active_sig = None
        if hasattr(self, '_find_active_signal'):
            active_sig = self._find_active_signal()

        if not active_sig:
            QMessageBox.warning(
                self,
                "Keine offene Position",
                "Es gibt keine offene Position zum Verkaufen.",
            )
            return

        # Get current price
        current_price = active_sig.get("current_price", 0)
        if current_price <= 0:
            current_price = active_sig.get("price", 0)

        if current_price <= 0:
            QMessageBox.warning(
                self,
                "Kein Kurs verfügbar",
                "Aktueller Kurs ist nicht verfügbar.",
            )
            return

        # Calculate limit price (0.05% below current for long, above for short)
        side = active_sig.get("side", "long").lower()
        current_price_decimal = Decimal(str(current_price))
        if side == "long":
            limit_price = current_price_decimal * Decimal("0.9995")  # 0.05% below
            order_side = "SELL"
        else:
            limit_price = current_price_decimal * Decimal("1.0005")  # 0.05% above for short
            order_side = "BUY"

        quantity = active_sig.get("quantity", 0)
        symbol = active_sig.get("symbol", "")

        if not symbol:
            # Try to get symbol from chart widget
            if hasattr(self, 'chart_widget') and hasattr(self.chart_widget, 'current_symbol'):
                symbol = self.chart_widget.current_symbol

        if quantity <= 0:
            QMessageBox.warning(
                self,
                "Keine Positionsgröße",
                "Die Positionsgröße ist nicht verfügbar.",
            )
            return

        # Confirmation dialog
        reply = QMessageBox.question(
            self,
            "Position verkaufen",
            f"Position verkaufen?\n\n"
            f"Symbol: {symbol}\n"
            f"Side: {order_side}\n"
            f"Menge: {quantity:.6f}\n"
            f"Aktueller Kurs: {current_price:.4f}\n"
            f"Limit-Preis: {limit_price:.4f} (0.05% {'unter' if side == 'long' else 'über'} Kurs)\n",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        # Execute the sell
        asyncio.create_task(self._execute_sell_order(
            symbol=symbol,
            side=order_side,
            quantity=quantity,
            limit_price=limit_price,
            signal=active_sig,
        ))

    async def _execute_sell_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        limit_price: Decimal,
        signal: dict,
    ) -> None:
        """Execute the sell order via adapter.

        Issue #11: Places a limit order to close the position.

        Args:
            symbol: Trading symbol
            side: Order side (SELL for long, BUY for short)
            quantity: Position quantity
            limit_price: Limit price for the order
            signal: The signal dict containing position info
        """
        try:
            # Get adapter
            adapter = getattr(self, '_bitunix_adapter', None)
            if not adapter:
                # Try from bitunix widget
                bitunix_widget = getattr(self, '_bitunix_widget', None)
                if bitunix_widget:
                    adapter = getattr(bitunix_widget, 'adapter', None)

            if not adapter:
                logger.error("No adapter available for selling position")
                QMessageBox.critical(
                    self,
                    "Fehler",
                    "Kein Broker-Adapter verfügbar.",
                )
                return

            # Import order types
            from src.core.broker.broker_types import OrderRequest
            from src.database.models import OrderSide, OrderType as DBOrderType

            # Create order request
            order = OrderRequest(
                symbol=symbol,
                side=OrderSide.SELL if side == "SELL" else OrderSide.BUY,
                quantity=Decimal(str(quantity)),
                order_type=DBOrderType.LIMIT,
                limit_price=Decimal(str(limit_price)),
            )

            logger.info(
                f"Issue #11: Placing limit {side} order: {symbol} qty={quantity} @ {limit_price}"
            )

            # Place order
            response = await adapter.place_order(order)

            if response and response.broker_order_id:
                logger.info(f"Issue #11: Order placed successfully: {response.broker_order_id}")

                # Update signal status
                signal["status"] = "CLOSING"
                signal["exit_order_id"] = response.broker_order_id
                if hasattr(self, '_save_signal_history'):
                    self._save_signal_history()
                if hasattr(self, '_update_signals_table'):
                    self._update_signals_table()

                # Add to KI log
                if hasattr(self, '_add_ki_log_entry'):
                    self._add_ki_log_entry(
                        "SELL",
                        f"Limit-Order platziert: {symbol} {side} {quantity:.6f} @ {limit_price:.4f}"
                    )

                # Issue #13: Remove position lines from chart when selling
                if hasattr(self, 'chart_widget'):
                    try:
                        self.chart_widget.remove_stop_line("initial_stop")
                        self.chart_widget.remove_stop_line("trailing_stop")
                        self.chart_widget.remove_stop_line("entry_line")
                        if hasattr(self, '_add_ki_log_entry'):
                            self._add_ki_log_entry("CHART", "Linien entfernt (Verkauf eingeleitet)")
                    except Exception as e:
                        logger.error(f"Error removing chart lines: {e}")

                QMessageBox.information(
                    self,
                    "Order platziert",
                    f"Limit-Order wurde platziert.\n\n"
                    f"Order ID: {response.broker_order_id}\n"
                    f"Preis: {limit_price:.4f}",
                )
            else:
                logger.error("Issue #11: Order placement failed - no order ID returned")
                QMessageBox.warning(
                    self,
                    "Order fehlgeschlagen",
                    "Die Order konnte nicht platziert werden. Siehe Logs für Details.",
                )

        except Exception as e:
            logger.exception(f"Issue #11: Failed to place sell order: {e}")
            QMessageBox.critical(
                self,
                "Fehler",
                f"Fehler beim Platzieren der Order:\n{str(e)}",
            )

    def _update_sell_button_state(self) -> None:
        """Update the sell button enabled state based on open positions.

        Issue #11: Button is enabled only when there's an open position.
        Issue #18: Also updates draw_chart_elements_btn state.
        """
        has_open_position = False
        if hasattr(self, '_find_active_signal'):
            active_sig = self._find_active_signal()
            has_open_position = active_sig is not None

        if hasattr(self, 'sell_position_btn'):
            self.sell_position_btn.setEnabled(has_open_position)

        # Issue #18: Update chart elements button state
        if hasattr(self, 'draw_chart_elements_btn'):
            self.draw_chart_elements_btn.setEnabled(has_open_position)

    # ==========================================
    # Chart Elements Drawing (Issue #18)
    # ==========================================

    def _on_draw_chart_elements_clicked(self) -> None:
        """Draw chart elements (Entry, SL, TR) for active position.

        Issue #18: Draws Entry line, Stop-Loss and Trailing-Stop lines in chart.
        Labels show values in percentage.
        Lines can be moved in chart - values in Signals are automatically updated.
        """
        # Find active position
        active_sig = None
        if hasattr(self, '_find_active_signal'):
            active_sig = self._find_active_signal()

        if not active_sig:
            QMessageBox.warning(
                self,
                "Keine offene Position",
                "Es gibt keine offene Position für Chart-Elemente.",
            )
            return

        # Get position details
        entry_price = active_sig.get("price", 0)
        stop_price = active_sig.get("stop_price", 0)
        trailing_price = active_sig.get("trailing_stop_price", 0)
        side = active_sig.get("side", "long")
        initial_sl_pct = active_sig.get("initial_sl_pct", 0)
        trailing_pct = active_sig.get("trailing_stop_pct", 0)
        trailing_activation_pct = active_sig.get("trailing_activation_pct", 0)
        current_price = active_sig.get("current_price", entry_price)

        if entry_price <= 0:
            QMessageBox.warning(
                self,
                "Keine Entry-Daten",
                "Entry-Preis ist nicht verfügbar.",
            )
            return

        # Check for chart widget
        if not hasattr(self, 'chart_widget') or not self.chart_widget:
            QMessageBox.warning(
                self,
                "Kein Chart",
                "Chart-Widget ist nicht verfügbar.",
            )
            return

        try:
            # Calculate percentages if not available
            if initial_sl_pct <= 0 and stop_price > 0 and entry_price > 0:
                initial_sl_pct = abs((stop_price - entry_price) / entry_price) * 100

            if trailing_pct <= 0 and trailing_price > 0 and entry_price > 0:
                if side == "long":
                    trailing_pct = abs((entry_price - trailing_price) / entry_price) * 100
                else:
                    trailing_pct = abs((trailing_price - entry_price) / entry_price) * 100

            # Calculate TRA% (distance from current price)
            tra_pct = 0
            if trailing_price > 0 and current_price > 0:
                tra_pct = abs((current_price - trailing_price) / current_price) * 100

            # Draw Entry Line (blue)
            entry_label = f"Entry @ {entry_price:.2f}"
            self.chart_widget.add_stop_line(
                line_id="entry_line",
                price=entry_price,
                line_type="initial",
                color="#2196f3",  # Blue
                label=entry_label
            )

            # Draw Stop-Loss Line (red) with percentage
            if stop_price > 0:
                sl_label = f"SL @ {stop_price:.2f} ({initial_sl_pct:.2f}%)"
                self.chart_widget.add_stop_line(
                    line_id="initial_stop",
                    price=stop_price,
                    line_type="initial",
                    color="#ef5350",  # Red
                    label=sl_label
                )

            # Draw Trailing-Stop Line (orange) with percentage
            if trailing_price > 0:
                tr_is_active = active_sig.get("tr_active", False)
                if tr_is_active:
                    tr_label = f"TSL @ {trailing_price:.2f} ({trailing_pct:.2f}% / TRA: {tra_pct:.2f}%)"
                    color = "#ff9800"  # Orange when active
                else:
                    tr_label = f"TSL @ {trailing_price:.2f} ({trailing_pct:.2f}%) [inaktiv]"
                    color = "#888888"  # Gray when inactive

                self.chart_widget.add_stop_line(
                    line_id="trailing_stop",
                    price=trailing_price,
                    line_type="trailing",
                    color=color,
                    label=tr_label
                )

            # Log action
            if hasattr(self, '_add_ki_log_entry'):
                lines_drawn = ["Entry"]
                if stop_price > 0:
                    lines_drawn.append(f"SL ({initial_sl_pct:.2f}%)")
                if trailing_price > 0:
                    lines_drawn.append(f"TR ({trailing_pct:.2f}%)")
                self._add_ki_log_entry("CHART", f"Elemente gezeichnet: {', '.join(lines_drawn)}")

            logger.info(
                f"Issue #18: Chart elements drawn - Entry: {entry_price:.2f}, "
                f"SL: {stop_price:.2f} ({initial_sl_pct:.2f}%), "
                f"TR: {trailing_price:.2f} ({trailing_pct:.2f}%)"
            )

        except Exception as e:
            logger.exception(f"Issue #18: Failed to draw chart elements: {e}")
            QMessageBox.critical(
                self,
                "Fehler",
                f"Fehler beim Zeichnen der Chart-Elemente:\n{str(e)}",
            )
