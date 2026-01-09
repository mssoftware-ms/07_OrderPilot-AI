"""Bot Tab Display Updates - Display Update Methods für Bot Trading Tab.

Refactored from 850 LOC bot_tab_main.py (further split).

Module 2/3 of bot_tab_main.py second-level split.

Contains:
- BotTabDisplayUpdates: Helper für Thread-sichere UI Updates
  - _update_status_display(): Bot Status aktualisieren
  - _update_signal_display(): Signal-Anzeige aktualisieren
  - _update_position_display(): Position-Anzeige aktualisieren
  - _update_stats_display(): Statistik-Anzeige aktualisieren
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.trading_bot import BotStatistics, MonitoredPosition, TradeSignal

logger = logging.getLogger(__name__)


class BotTabDisplayUpdates:
    """Helper für Thread-sichere UI Display Updates."""

    def __init__(self, parent):
        """
        Args:
            parent: BotTab Instanz mit UI Widgets
        """
        self.parent = parent

    def update_status_display(self, state: str) -> None:
        """Aktualisiert Status-Anzeige."""
        state_config = {
            "IDLE": ("🤖", "#888", "Bot ist gestoppt"),
            "STARTING": ("🔄", "#FFC107", "Bot startet..."),
            "ANALYZING": ("🔍", "#2196F3", "Analysiere Markt..."),
            "WAITING_SIGNAL": ("⏳", "#9C27B0", "Warte auf Signal..."),
            "VALIDATING": ("🧠", "#FF9800", "Validiere Signal mit AI..."),
            "OPENING_POSITION": ("📈", "#4CAF50", "Öffne Position..."),
            "IN_POSITION": ("💰", "#4CAF50", "Position aktiv"),
            "CLOSING_POSITION": ("📉", "#f44336", "Schließe Position..."),
            "STOPPING": ("⏸", "#FFC107", "Bot stoppt..."),
            "ERROR": ("❌", "#f44336", "Fehler aufgetreten"),
        }

        icon, color, detail = state_config.get(state, ("❓", "#888", state))

        self.parent.status_icon.setText(icon)
        self.parent.status_label.setText(state)
        self.parent.status_label.setStyleSheet(
            f"""
            font-size: 16px;
            font-weight: bold;
            color: {color};
        """
        )
        self.parent.status_detail.setText(detail)

    def update_signal_display(self, signal: "TradeSignal | None") -> None:
        """Aktualisiert Signal-Anzeige."""
        from src.core.trading_bot import SignalDirection

        if signal is None:
            self.parent.signal_direction.setText("—")
            self.parent.signal_direction.setStyleSheet(
                """
                font-size: 18px; font-weight: bold;
                padding: 5px 15px; border-radius: 4px;
                background-color: #333;
            """
            )
            self.parent.signal_confluence.setText("—")
            self.parent.signal_regime.setText("Regime: —")
            self.parent.signal_conditions.setText("—")
            self.parent.signal_timestamp.setText("Letztes Update: —")
            return

        # Direction
        if signal.direction == SignalDirection.LONG:
            self.parent.signal_direction.setText("📈 LONG")
            self.parent.signal_direction.setStyleSheet(
                """
                font-size: 18px; font-weight: bold;
                padding: 5px 15px; border-radius: 4px;
                background-color: #1B5E20; color: #4CAF50;
            """
            )
        elif signal.direction == SignalDirection.SHORT:
            self.parent.signal_direction.setText("📉 SHORT")
            self.parent.signal_direction.setStyleSheet(
                """
                font-size: 18px; font-weight: bold;
                padding: 5px 15px; border-radius: 4px;
                background-color: #B71C1C; color: #f44336;
            """
            )
        else:
            self.parent.signal_direction.setText("— NEUTRAL")
            self.parent.signal_direction.setStyleSheet(
                """
                font-size: 18px; font-weight: bold;
                padding: 5px 15px; border-radius: 4px;
                background-color: #333;
            """
            )

        # Confluence
        total = len(signal.conditions_met) + len(signal.conditions_failed)
        met = len(signal.conditions_met)
        self.parent.signal_confluence.setText(f"{met}/{total}")

        # Regime
        self.parent.signal_regime.setText(f"Regime: {signal.regime or '—'}")

        # Conditions
        conditions = ", ".join([c.name for c in signal.conditions_met])
        self.parent.signal_conditions.setText(conditions if conditions else "—")

        # Timestamp
        self.parent.signal_timestamp.setText(f"Update: {datetime.now().strftime('%H:%M:%S')}")

    def update_position_display(self, position: "MonitoredPosition | None") -> None:
        """Aktualisiert Position-Anzeige."""
        if position is None:
            self.parent.pos_side.setText("—")
            self.parent.pos_side.setStyleSheet("font-weight: bold;")
            self.parent.pos_entry.setText("—")
            self.parent.pos_current.setText("—")
            self.parent.pos_sl.setText("—")
            self.parent.pos_tp.setText("—")
            self.parent.pos_pnl.setText("—")
            self.parent.sl_tp_progress.setValue(50)
            self.parent.close_position_btn.setEnabled(False)
            return

        # Side
        if position.side == "BUY":
            self.parent.pos_side.setText("🟢 LONG")
            self.parent.pos_side.setStyleSheet("font-weight: bold; color: #4CAF50;")
        else:
            self.parent.pos_side.setText("🔴 SHORT")
            self.parent.pos_side.setStyleSheet("font-weight: bold; color: #f44336;")

        # Prices
        self.parent.pos_entry.setText(f"${position.entry_price:,.2f}")
        if position.current_price:
            self.parent.pos_current.setText(f"${position.current_price:,.2f}")

        self.parent.pos_sl.setText(f"${position.stop_loss:,.2f}")
        self.parent.pos_tp.setText(f"${position.take_profit:,.2f}")

        # PnL
        pnl = position.unrealized_pnl
        pnl_pct = position.unrealized_pnl_percent
        if pnl >= 0:
            self.parent.pos_pnl.setText(f"+${pnl:,.2f} (+{pnl_pct:.2f}%)")
            self.parent.pos_pnl.setStyleSheet("font-weight: bold; color: #4CAF50;")
        else:
            self.parent.pos_pnl.setText(f"-${abs(pnl):,.2f} ({pnl_pct:.2f}%)")
            self.parent.pos_pnl.setStyleSheet("font-weight: bold; color: #f44336;")

        # Progress Bar (Position zwischen SL und TP)
        if position.current_price and position.stop_loss and position.take_profit:
            price = float(position.current_price)
            sl = float(position.stop_loss)
            tp = float(position.take_profit)

            if position.side == "BUY":
                total_range = tp - sl
                if total_range > 0:
                    progress = int((price - sl) / total_range * 100)
                    progress = max(0, min(100, progress))
                    self.parent.sl_tp_progress.setValue(progress)
            else:  # SHORT
                total_range = sl - tp
                if total_range > 0:
                    progress = int((sl - price) / total_range * 100)
                    progress = max(0, min(100, progress))
                    self.parent.sl_tp_progress.setValue(progress)

        self.parent.close_position_btn.setEnabled(True)

    def update_stats_display(self, stats: "BotStatistics") -> None:
        """Aktualisiert Statistik-Anzeige."""
        self.parent.stats_trades.setText(str(stats.trades_total))

        # Win Rate
        wr = stats.win_rate
        self.parent.stats_winrate.setText(f"{wr:.1f}%")
        if wr >= 50:
            self.parent.stats_winrate.setStyleSheet("font-size: 18px; font-weight: bold; color: #4CAF50;")
        else:
            self.parent.stats_winrate.setStyleSheet("font-size: 18px; font-weight: bold; color: #f44336;")

        # PnL
        pnl = stats.total_pnl
        if pnl >= 0:
            self.parent.stats_pnl.setText(f"+${pnl:,.2f}")
            self.parent.stats_pnl.setStyleSheet("font-size: 18px; font-weight: bold; color: #4CAF50;")
        else:
            self.parent.stats_pnl.setText(f"-${abs(pnl):,.2f}")
            self.parent.stats_pnl.setStyleSheet("font-size: 18px; font-weight: bold; color: #f44336;")

        # Drawdown
        dd = stats.max_drawdown
        self.parent.stats_drawdown.setText(f"-${abs(dd):,.2f}")
