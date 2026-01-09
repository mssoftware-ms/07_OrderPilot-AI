"""Bitunix Trading Positions Manager - Position Loading & Persistence.

Refactored from 1,108 LOC monolith using composition pattern.

Module 3/4 of bitunix_trading_widget.py split.

Contains:
- Position loading and display (_load_positions)
- Real-time tick price updates (_on_tick_price_updated)
- Position persistence (save/load from JSON file)
- Position deletion (_delete_selected_row)
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING

import qasync
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QTableWidgetItem, QMessageBox

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class BitunixTradingPositionsManager:
    """Helper für Position Loading und Persistence."""

    def __init__(self, parent):
        """
        Args:
            parent: BitunixTradingWidget Instanz
        """
        self.parent = parent

    # === Position Loading ===

    @qasync.asyncSlot()
    async def _load_positions(self) -> None:
        """Load and display open positions from adapter."""
        if not self.parent.adapter:
            return

        # Ensure connection is established
        if not self.parent.adapter.connected:
            try:
                await self.parent.adapter.connect()
            except Exception as e:
                if "AUTH_FAILED" in str(e):
                    logger.error(f"Bitunix auth failed, stopping Bitunix timers: {e}")
                    self.parent._stop_updates()
                else:
                    logger.error(f"Failed to connect to Bitunix: {e}")
                return

        try:
            positions = await self.parent.adapter.get_positions()
            self.parent.positions_table.setRowCount(len(positions))

            for row, pos in enumerate(positions):
                # Symbol (Column 0)
                self.parent.positions_table.setItem(row, 0, QTableWidgetItem(pos.symbol))

                # Direction (Column 1)
                direction_text = "🔵 LONG" if pos.is_long else "🔴 SHORT"
                direction_color = "#4CAF50" if pos.is_long else "#f44336"
                direction_item = QTableWidgetItem(direction_text)
                direction_item.setForeground(QColor(direction_color))
                self.parent.positions_table.setItem(row, 1, direction_item)

                # Quantity (Column 2)
                self.parent.positions_table.setItem(row, 2, QTableWidgetItem(f"{pos.quantity:.4f}"))

                # Entry Price (Column 3)
                self.parent.positions_table.setItem(row, 3, QTableWidgetItem(f"{pos.average_cost:.2f}"))

                # Current Price (Column 4)
                self.parent.positions_table.setItem(row, 4, QTableWidgetItem(f"{pos.current_price:.2f}"))

                # Leverage (Column 5)
                self.parent.positions_table.setItem(row, 5, QTableWidgetItem(f"{pos.leverage}x"))

                # PnL with color (Column 6)
                pnl_value = float(pos.unrealized_pnl)
                pnl_color = "#4CAF50" if pnl_value >= 0 else "#f44336"
                pnl_sign = "+" if pnl_value >= 0 else ""
                pnl_item = QTableWidgetItem(f"{pnl_sign}{pnl_value:.2f}")
                pnl_item.setForeground(Qt.GlobalColor.white)
                pnl_item.setBackground(Qt.GlobalColor.green if pnl_value >= 0 else Qt.GlobalColor.red)
                self.parent.positions_table.setItem(row, 6, pnl_item)

        except Exception as e:
            logger.error(f"Failed to load positions: {e}")

    def on_tick_price_updated(self, price: float) -> None:
        """Update current price in positions table in real-time.

        Connected to chart's tick_price_updated signal for live updates.

        Args:
            price: Current market price from streaming ticker
        """
        if not self.parent._current_symbol:
            return

        # Update all rows where symbol matches current symbol
        for row in range(self.parent.positions_table.rowCount()):
            symbol_item = self.parent.positions_table.item(row, 0)
            if symbol_item and symbol_item.text() == self.parent._current_symbol:
                # Update Current price (Column 4 - shifted by 1 due to Direction column)
                self.parent.positions_table.setItem(row, 4, QTableWidgetItem(f"{price:.2f}"))

                # Recalculate PnL (Column 6 - shifted by 2 due to Direction and Leverage columns)
                try:
                    entry_price = float(self.parent.positions_table.item(row, 3).text())
                    quantity = float(self.parent.positions_table.item(row, 2).text())
                    leverage_text = (
                        self.parent.positions_table.item(row, 5).text()
                        if self.parent.positions_table.item(row, 5)
                        else "1x"
                    )
                    leverage = float(leverage_text.rstrip("x"))

                    pnl_value = (price - entry_price) * quantity * leverage
                    pnl_color = "#4CAF50" if pnl_value >= 0 else "#f44336"
                    pnl_sign = "+" if pnl_value >= 0 else ""

                    pnl_item = QTableWidgetItem(f"{pnl_sign}{pnl_value:.2f}")
                    pnl_item.setForeground(QColor(pnl_color))

                    self.parent.positions_table.setItem(row, 6, pnl_item)
                except (ValueError, AttributeError, TypeError):
                    pass  # Silently ignore calculation errors

    # === Position Persistence ===

    def save_positions_to_file(self) -> None:
        """Save current positions table to JSON file."""
        try:
            # Create data directory if not exists
            data_dir = Path("data")
            data_dir.mkdir(exist_ok=True)

            positions_file = data_dir / "bitunix_positions.json"

            # Extract table data
            positions_data = []
            for row in range(self.parent.positions_table.rowCount()):
                row_data = {}
                # Column 0: Symbol
                symbol_item = self.parent.positions_table.item(row, 0)
                row_data["symbol"] = symbol_item.text() if symbol_item else ""

                # Column 1: Direction
                direction_item = self.parent.positions_table.item(row, 1)
                row_data["direction"] = direction_item.text() if direction_item else ""

                # Column 2: Quantity
                qty_item = self.parent.positions_table.item(row, 2)
                row_data["quantity"] = qty_item.text() if qty_item else "0"

                # Column 3: Entry Price
                entry_item = self.parent.positions_table.item(row, 3)
                row_data["entry_price"] = entry_item.text() if entry_item else "0"

                # Column 4: Current Price
                current_item = self.parent.positions_table.item(row, 4)
                row_data["current_price"] = current_item.text() if current_item else "0"

                # Column 5: Leverage
                leverage_item = self.parent.positions_table.item(row, 5)
                row_data["leverage"] = leverage_item.text() if leverage_item else "1x"

                # Column 6: PnL
                pnl_item = self.parent.positions_table.item(row, 6)
                row_data["pnl"] = pnl_item.text() if pnl_item else "0"

                positions_data.append(row_data)

            # Save to JSON
            with open(positions_file, "w", encoding="utf-8") as f:
                json.dump(positions_data, f, indent=2, ensure_ascii=False)

            logger.info(f"Saved {len(positions_data)} positions to {positions_file}")

        except Exception as e:
            logger.error(f"Failed to save positions: {e}")

    def load_positions_from_file(self) -> None:
        """Load positions from JSON file into table."""
        try:
            positions_file = Path("data/bitunix_positions.json")

            if not positions_file.exists():
                logger.debug("No saved positions file found")
                return

            # Load from JSON
            with open(positions_file, "r", encoding="utf-8") as f:
                positions_data = json.load(f)

            if not positions_data:
                return

            # Populate table
            self.parent.positions_table.setRowCount(len(positions_data))

            for row, data in enumerate(positions_data):
                # Symbol (Column 0)
                self.parent.positions_table.setItem(row, 0, QTableWidgetItem(data.get("symbol", "")))

                # Direction (Column 1)
                direction_text = data.get("direction", "")
                direction_item = QTableWidgetItem(direction_text)
                if "LONG" in direction_text:
                    direction_item.setForeground(QColor("#4CAF50"))
                elif "SHORT" in direction_text:
                    direction_item.setForeground(QColor("#f44336"))
                self.parent.positions_table.setItem(row, 1, direction_item)

                # Quantity (Column 2)
                self.parent.positions_table.setItem(row, 2, QTableWidgetItem(data.get("quantity", "0")))

                # Entry Price (Column 3)
                self.parent.positions_table.setItem(row, 3, QTableWidgetItem(data.get("entry_price", "0")))

                # Current Price (Column 4)
                self.parent.positions_table.setItem(row, 4, QTableWidgetItem(data.get("current_price", "0")))

                # Leverage (Column 5)
                self.parent.positions_table.setItem(row, 5, QTableWidgetItem(data.get("leverage", "1x")))

                # PnL (Column 6)
                pnl_text = data.get("pnl", "0")
                pnl_item = QTableWidgetItem(pnl_text)
                # Parse PnL value for color
                try:
                    pnl_value = float(pnl_text.replace("+", "").replace(",", ""))
                    if pnl_value >= 0:
                        pnl_item.setForeground(Qt.GlobalColor.white)
                        pnl_item.setBackground(Qt.GlobalColor.green)
                    else:
                        pnl_item.setForeground(Qt.GlobalColor.white)
                        pnl_item.setBackground(Qt.GlobalColor.red)
                except:
                    pass
                self.parent.positions_table.setItem(row, 6, pnl_item)

            logger.info(f"Loaded {len(positions_data)} positions from {positions_file}")

        except Exception as e:
            logger.error(f"Failed to load positions: {e}")

    def delete_selected_row(self) -> None:
        """Delete the selected row from positions table."""
        current_row = self.parent.positions_table.currentRow()

        if current_row < 0:
            QMessageBox.warning(
                self.parent, "Keine Auswahl", "Bitte wählen Sie eine Zeile zum Löschen aus."
            )
            return

        # Get symbol for confirmation
        symbol_item = self.parent.positions_table.item(current_row, 0)
        symbol = symbol_item.text() if symbol_item else "Unknown"

        # Confirm deletion
        confirm = QMessageBox.question(
            self.parent,
            "Position löschen",
            f"Position für {symbol} wirklich löschen?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if confirm == QMessageBox.StandardButton.Yes:
            self.parent.positions_table.removeRow(current_row)
            self.save_positions_to_file()  # Auto-save after deletion
            logger.info(f"Deleted position row {current_row} ({symbol})")
