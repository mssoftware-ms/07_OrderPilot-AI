"""
ExecutionSimulator - Realistische Trade-Ausführung für Backtesting

Simuliert realistische Trade-Ausführung mit:
- Fees (Maker/Taker)
- Slippage (Fixed BPS, ATR-based, Volume-adjusted)
- Leverage (Margin, Liquidation Buffer)
- Optional: Funding Rates für Perpetuals

Features:
- Konfigurierbare Fee-Modelle
- Slippage basierend auf Volatilität/Volumen
- Margin- und Liquidations-Berechnung
- Deterministisch und reproduzierbar
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Optional
import uuid

from .config import ExecutionConfig, SlippageMethod

logger = logging.getLogger(__name__)


class OrderSide(Enum):
    """Order-Seite."""
    BUY = "buy"
    SELL = "sell"


class OrderType(Enum):
    """Order-Typ."""
    MARKET = "market"
    LIMIT = "limit"
    STOP_MARKET = "stop_market"
    TAKE_PROFIT = "take_profit"


class FillStatus(Enum):
    """Fill-Status."""
    FILLED = "filled"
    PARTIAL = "partial"
    REJECTED = "rejected"
    LIQUIDATED = "liquidated"


@dataclass
class SimulatedOrder:
    """Eine simulierte Order.

    Attributes:
        order_id: Eindeutige Order-ID
        symbol: Trading-Symbol
        side: Buy oder Sell
        order_type: Market, Limit, etc.
        quantity: Menge
        price: Limit-Preis (für Limit Orders)
        stop_price: Stop-Preis (für Stop Orders)
        leverage: Verwendeter Hebel
        timestamp: Order-Timestamp
    """
    order_id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: float
    price: float | None = None
    stop_price: float | None = None
    leverage: int = 1
    timestamp: int = 0
    notes: str = ""

    def __post_init__(self):
        if not self.order_id:
            self.order_id = f"sim_{uuid.uuid4().hex[:8]}"


@dataclass
class SimulatedFill:
    """Ergebnis einer simulierten Order-Ausführung.

    Attributes:
        order_id: Referenz zur Order
        fill_id: Eindeutige Fill-ID
        status: Fill-Status
        fill_price: Tatsächlicher Ausführungspreis (inkl. Slippage)
        fill_quantity: Ausgeführte Menge
        fee: Gezahlte Gebühr (absolut)
        fee_rate: Angewendete Fee-Rate
        slippage: Angewendete Slippage (in Preis-Einheiten)
        slippage_bps: Slippage in Basis-Punkten
        notional_value: Notional Value der Position
        margin_used: Verwendete Margin
        liquidation_price: Liquidationspreis
        timestamp: Fill-Timestamp
        reason: Grund (bei Rejection/Liquidation)
    """
    order_id: str
    fill_id: str
    status: FillStatus
    fill_price: float
    fill_quantity: float
    fee: float
    fee_rate: float
    slippage: float
    slippage_bps: float
    notional_value: float
    margin_used: float
    liquidation_price: float | None
    timestamp: int
    side: OrderSide
    leverage: int = 1
    reason: str = ""

    def __post_init__(self):
        if not self.fill_id:
            self.fill_id = f"fill_{uuid.uuid4().hex[:8]}"

    @property
    def total_cost(self) -> float:
        """Gesamtkosten inkl. Fees."""
        return self.notional_value + self.fee

    @property
    def effective_price(self) -> float:
        """Effektiver Preis inkl. Slippage und Fees pro Einheit."""
        if self.fill_quantity == 0:
            return self.fill_price
        return self.total_cost / self.fill_quantity


class FeeModel:
    """Fee-Berechnungsmodell."""

    def __init__(
        self,
        maker_rate: float = 0.02,  # 0.02% = 2bps
        taker_rate: float = 0.06,  # 0.06% = 6bps
    ):
        """Initialisiert das Fee-Modell.

        Args:
            maker_rate: Maker-Fee in Prozent
            taker_rate: Taker-Fee in Prozent
        """
        self.maker_rate = maker_rate / 100  # Konvertiere zu Dezimal
        self.taker_rate = taker_rate / 100

    def calculate_fee(
        self,
        notional: float,
        is_taker: bool = True,
    ) -> tuple[float, float]:
        """Berechnet die Fee.

        Args:
            notional: Notional Value
            is_taker: True für Taker, False für Maker

        Returns:
            Tuple aus (fee_absolut, fee_rate)
        """
        rate = self.taker_rate if is_taker else self.maker_rate
        fee = notional * rate
        return fee, rate


class SlippageModel:
    """Slippage-Berechnungsmodell."""

    def __init__(
        self,
        method: SlippageMethod = SlippageMethod.FIXED_BPS,
        fixed_bps: float = 5.0,
        atr_mult: float = 0.1,
    ):
        """Initialisiert das Slippage-Modell.

        Args:
            method: Berechnungsmethode
            fixed_bps: Fixe Basis-Punkte (für FIXED_BPS)
            atr_mult: ATR-Multiplikator (für ATR_BASED)
        """
        self.method = method
        self.fixed_bps = fixed_bps
        self.atr_mult = atr_mult

    def calculate_slippage(
        self,
        price: float,
        side: OrderSide,
        atr: float | None = None,
        volume_ratio: float = 1.0,
    ) -> tuple[float, float]:
        """Berechnet Slippage.

        Args:
            price: Basis-Preis
            side: Order-Seite
            atr: ATR für ATR_BASED Methode
            volume_ratio: Volumen-Verhältnis für Volume-Adjusted

        Returns:
            Tuple aus (slippage_absolut, slippage_bps)
        """
        if self.method == SlippageMethod.FIXED_BPS:
            slippage_bps = self.fixed_bps
        elif self.method == SlippageMethod.ATR_BASED:
            if atr is None or atr <= 0:
                slippage_bps = self.fixed_bps  # Fallback
            else:
                # Slippage als Anteil des ATR
                slippage_abs = atr * self.atr_mult
                slippage_bps = (slippage_abs / price) * 10000
        elif self.method == SlippageMethod.VOLUME_ADJUSTED:
            # Höhere Slippage bei niedrigem Volumen
            base_bps = self.fixed_bps
            slippage_bps = base_bps * (2.0 - min(volume_ratio, 1.0))
        else:
            slippage_bps = self.fixed_bps

        # Slippage in Preis-Einheiten
        slippage_abs = price * (slippage_bps / 10000)

        # Slippage-Richtung: Buy = höherer Preis, Sell = niedrigerer Preis
        if side == OrderSide.SELL:
            slippage_abs = -slippage_abs

        return slippage_abs, slippage_bps


class ExecutionSimulator:
    """Simuliert realistische Order-Ausführung für Backtesting.

    Features:
    - Fee-Berechnung (Maker/Taker)
    - Slippage-Simulation
    - Margin und Liquidations-Berechnung
    - Position Tracking

    Usage:
        simulator = ExecutionSimulator(config)

        # Order erstellen und ausführen
        order = SimulatedOrder(...)
        fill = simulator.execute_order(order, market_price, atr)

        if fill.status == FillStatus.FILLED:
            # Position wurde eröffnet
            pass
    """

    def __init__(self, config: ExecutionConfig | None = None):
        """Initialisiert den Simulator.

        Args:
            config: Execution-Konfiguration
        """
        self.config = config or ExecutionConfig()

        self.fee_model = FeeModel(
            maker_rate=self.config.fee_rate_maker,
            taker_rate=self.config.fee_rate_taker,
        )

        self.slippage_model = SlippageModel(
            method=self.config.slippage_method,
            fixed_bps=self.config.slippage_bps,
            atr_mult=self.config.slippage_atr_mult,
        )

        # Tracking
        self._fills: list[SimulatedFill] = []
        self._total_fees_paid: float = 0.0

    def execute_order(
        self,
        order: SimulatedOrder,
        market_price: float,
        atr: float | None = None,
        available_margin: float | None = None,
        volume_ratio: float = 1.0,
    ) -> SimulatedFill:
        """Führt eine Order aus.

        Args:
            order: Die auszuführende Order
            market_price: Aktueller Marktpreis
            atr: ATR für Slippage-Berechnung
            available_margin: Verfügbare Margin (für Leverage-Check)
            volume_ratio: Volumen-Verhältnis (für Volume-Adjusted Slippage)

        Returns:
            SimulatedFill mit Ausführungsdetails
        """
        # Basis-Preis bestimmen
        if order.order_type == OrderType.LIMIT and order.price:
            base_price = order.price
        elif order.order_type == OrderType.STOP_MARKET and order.stop_price:
            base_price = order.stop_price
        else:
            base_price = market_price

        # Slippage berechnen
        slippage, slippage_bps = self.slippage_model.calculate_slippage(
            price=base_price,
            side=order.side,
            atr=atr,
            volume_ratio=volume_ratio,
        )

        # Fill-Preis mit Slippage
        fill_price = base_price + slippage

        # Notional Value berechnen
        notional = fill_price * order.quantity

        # Leverage validieren
        effective_leverage = min(order.leverage, self.config.max_leverage)

        # Margin berechnen
        margin_required = notional / effective_leverage

        # Margin-Check
        if available_margin is not None and margin_required > available_margin:
            return SimulatedFill(
                order_id=order.order_id,
                fill_id=f"fill_{uuid.uuid4().hex[:8]}",
                status=FillStatus.REJECTED,
                fill_price=0,
                fill_quantity=0,
                fee=0,
                fee_rate=0,
                slippage=0,
                slippage_bps=0,
                notional_value=0,
                margin_used=0,
                liquidation_price=None,
                timestamp=order.timestamp,
                side=order.side,
                leverage=effective_leverage,
                reason=f"Insufficient margin: required {margin_required:.2f}, available {available_margin:.2f}",
            )

        # Fee berechnen
        is_taker = order.order_type == OrderType.MARKET or self.config.assume_taker
        fee, fee_rate = self.fee_model.calculate_fee(notional, is_taker)

        # Liquidationspreis berechnen
        liquidation_price = self._calculate_liquidation_price(
            entry_price=fill_price,
            side=order.side,
            leverage=effective_leverage,
        )

        # Fill erstellen
        fill = SimulatedFill(
            order_id=order.order_id,
            fill_id=f"fill_{uuid.uuid4().hex[:8]}",
            status=FillStatus.FILLED,
            fill_price=fill_price,
            fill_quantity=order.quantity,
            fee=fee,
            fee_rate=fee_rate * 100,  # Zurück zu Prozent
            slippage=abs(slippage),
            slippage_bps=slippage_bps,
            notional_value=notional,
            margin_used=margin_required,
            liquidation_price=liquidation_price,
            timestamp=order.timestamp,
            side=order.side,
            leverage=effective_leverage,
        )

        # Tracking
        self._fills.append(fill)
        self._total_fees_paid += fee

        logger.debug(
            f"Order executed: {order.side.value} {order.quantity} @ {fill_price:.2f} "
            f"(slippage: {slippage_bps:.1f}bps, fee: {fee:.4f})"
        )

        return fill

    def _calculate_liquidation_price(
        self,
        entry_price: float,
        side: OrderSide,
        leverage: int,
    ) -> float:
        """Berechnet den Liquidationspreis.

        Args:
            entry_price: Entry-Preis
            side: Position-Seite
            leverage: Verwendeter Leverage

        Returns:
            Liquidationspreis
        """
        if leverage <= 1:
            return 0.0  # Kein Leverage = keine Liquidation

        # Margin = Notional / Leverage
        # Liquidation wenn Margin aufgebraucht (mit Buffer)
        buffer = self.config.liquidation_buffer_pct / 100
        margin_ratio = 1 / leverage

        if side == OrderSide.BUY:
            # Long: Liquidation bei Preisfall
            # Verlust = (entry - liq_price) / entry = margin_ratio * (1 - buffer)
            liquidation_price = entry_price * (1 - margin_ratio * (1 - buffer))
        else:
            # Short: Liquidation bei Preisanstieg
            liquidation_price = entry_price * (1 + margin_ratio * (1 - buffer))

        return liquidation_price

    def check_liquidation(
        self,
        position_side: OrderSide,
        entry_price: float,
        current_price: float,
        leverage: int,
    ) -> tuple[bool, float]:
        """Prüft, ob eine Position liquidiert werden würde.

        Args:
            position_side: Position-Seite
            entry_price: Entry-Preis
            current_price: Aktueller Preis
            leverage: Position-Leverage

        Returns:
            Tuple aus (is_liquidated, unrealized_pnl_pct)
        """
        if leverage <= 1:
            return False, 0.0

        liq_price = self._calculate_liquidation_price(entry_price, position_side, leverage)

        if position_side == OrderSide.BUY:
            is_liquidated = current_price <= liq_price
            pnl_pct = (current_price - entry_price) / entry_price * 100 * leverage
        else:
            is_liquidated = current_price >= liq_price
            pnl_pct = (entry_price - current_price) / entry_price * 100 * leverage

        return is_liquidated, pnl_pct

    def calculate_pnl(
        self,
        entry_price: float,
        exit_price: float,
        quantity: float,
        side: OrderSide,
        leverage: int = 1,
        include_fees: bool = True,
        entry_fee: float = 0,
        exit_fee: float = 0,
    ) -> dict:
        """Berechnet den PnL für einen Trade.

        Args:
            entry_price: Entry-Preis
            exit_price: Exit-Preis
            quantity: Menge
            side: Position-Seite
            leverage: Verwendeter Leverage
            include_fees: Fees einberechnen
            entry_fee: Entry-Fee
            exit_fee: Exit-Fee

        Returns:
            Dictionary mit PnL-Details
        """
        # Raw PnL (ohne Fees)
        if side == OrderSide.BUY:
            raw_pnl = (exit_price - entry_price) * quantity
        else:
            raw_pnl = (entry_price - exit_price) * quantity

        # PnL mit Leverage
        leveraged_pnl = raw_pnl * leverage

        # Notional Values
        entry_notional = entry_price * quantity
        exit_notional = exit_price * quantity

        # Total Fees
        total_fees = entry_fee + exit_fee if include_fees else 0

        # Net PnL
        net_pnl = leveraged_pnl - total_fees

        # Return Prozent (bezogen auf Margin, nicht Notional)
        margin_used = entry_notional / leverage
        return_pct = (net_pnl / margin_used) * 100 if margin_used > 0 else 0

        return {
            "raw_pnl": raw_pnl,
            "leveraged_pnl": leveraged_pnl,
            "total_fees": total_fees,
            "net_pnl": net_pnl,
            "return_pct": return_pct,
            "entry_notional": entry_notional,
            "exit_notional": exit_notional,
            "margin_used": margin_used,
        }

    def get_statistics(self) -> dict:
        """Gibt Ausführungsstatistiken zurück."""
        if not self._fills:
            return {}

        filled = [f for f in self._fills if f.status == FillStatus.FILLED]
        rejected = [f for f in self._fills if f.status == FillStatus.REJECTED]

        return {
            "total_orders": len(self._fills),
            "filled_orders": len(filled),
            "rejected_orders": len(rejected),
            "fill_rate": len(filled) / len(self._fills) * 100 if self._fills else 0,
            "total_fees_paid": self._total_fees_paid,
            "avg_slippage_bps": sum(f.slippage_bps for f in filled) / len(filled) if filled else 0,
            "total_notional": sum(f.notional_value for f in filled),
        }

    def reset(self) -> None:
        """Setzt den Simulator zurück."""
        self._fills.clear()
        self._total_fees_paid = 0.0
