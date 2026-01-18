"""Bitunix Paper Trading Adapter.

Simulates Bitunix Futures trading logic (Margin, Leverage, PnL) locally.
"""

import logging
import uuid
import asyncio
from decimal import Decimal
from datetime import datetime
from typing import TYPE_CHECKING

from src.core.broker.base import BrokerAdapter
from src.core.broker.broker_types import (
    Balance,
    OrderRequest,
    OrderResponse,
    Position,
    FeeModel,
    BrokerError,
)
from src.database.models import OrderSide, OrderStatus, OrderType

if TYPE_CHECKING:
    from src.core.market_data.history_provider import HistoryManager

logger = logging.getLogger(__name__)

class BitunixPaperAdapter(BrokerAdapter):
    """Paper trading adapter for Bitunix Futures."""

    def __init__(self, start_balance: float = 10000.0, history_manager: "HistoryManager | None" = None):
        super().__init__(name="Bitunix Paper", fee_model=FeeModel(
            broker="bitunix_paper",
            fee_type="percentage",
            maker_fee=Decimal("0.0002"),
            taker_fee=Decimal("0.0006")
        ))
        
        self.start_balance = Decimal(str(start_balance))
        self.history_manager = history_manager
        
        # State
        self.balance_usdt = self.start_balance
        self.positions: dict[str, Position] = {} # Symbol -> Position
        self.orders: list[OrderResponse] = []
        
        self._connected = True # Always connected

    # --- Connection lifecycle -------------------------------------------------
    @property
    def connected(self) -> bool:
        return self._connected

    async def _establish_connection(self) -> None:
        """Simulate establishing a connection (no-op for paper)."""
        self._connected = True

    async def _cleanup_resources(self) -> None:
        """Simulate cleaning up resources (no-op for paper)."""
        self._connected = False

    async def get_balance(self) -> Balance:
        """Get simulated balance."""
        total_unrealized_pnl = Decimal("0")

        if self.history_manager:
            for symbol, pos in self.positions.items():
                current_price = await self.history_manager.get_latest_price(symbol)
                if current_price:
                    self._update_position_pnl(pos, current_price)
                    total_unrealized_pnl += pos.unrealized_pnl or Decimal("0")

        total_equity = self.balance_usdt + total_unrealized_pnl

        margin_used = Decimal("0")

        return Balance(
            currency="USDT",
            cash=self.balance_usdt,
            market_value=Decimal("0"),
            total_equity=total_equity,
            buying_power=total_equity * 5,
            margin_used=margin_used,
            margin_available=total_equity - margin_used,
            daily_pnl=total_unrealized_pnl,
            daily_pnl_percentage=0.0,
        )

    async def get_positions(self) -> list[Position]:
        """Get current open positions."""
        if self.history_manager:
            for symbol, pos in self.positions.items():
                current_price = await self.history_manager.get_latest_price(symbol)
                if current_price:
                    self._update_position_pnl(pos, current_price)

        return list(self.positions.values())

    # --- Order handling -------------------------------------------------------
    async def place_order(self, order: OrderRequest) -> OrderResponse:
        """Validate and place order via base template method."""
        return await super().place_order(order)

    async def _place_order_impl(
        self,
        order: OrderRequest,
        estimated_fee: Decimal,
    ) -> OrderResponse:
        """Simulate order placement and update in-memory state."""
        order_type = order.order_type
        if not isinstance(order_type, OrderType):
            order_type = OrderType(order_type)

        exec_price = order.limit_price
        if order_type == OrderType.MARKET:
            if self.history_manager:
                exec_price = await self.history_manager.get_latest_price(order.symbol)

            if not exec_price:
                logger.warning("No price found for %s, using mock 100.0", order.symbol)
                exec_price = Decimal("100.0")

        if exec_price is None:
            raise BrokerError("NO_PRICE", "Could not determine execution price")

        fee = estimated_fee if estimated_fee is not None else Decimal("0")
        self.balance_usdt -= fee

        self._update_position_on_fill(order.symbol, order.side, order.quantity, exec_price)

        order_id = str(uuid.uuid4())
        now = datetime.utcnow()
        internal_id = order.internal_order_id or order_id

        response = OrderResponse(
            broker_order_id=order_id,
            internal_order_id=internal_id,
            status=OrderStatus.FILLED,
            symbol=order.symbol,
            side=order.side,
            order_type=order_type,
            quantity=order.quantity,
            filled_quantity=order.quantity,
            average_fill_price=exec_price,
            created_at=now,
            submitted_at=now,
            updated_at=now,
            estimated_fee=fee,
            actual_fee=fee,
            message="Paper Order Filled",
        )

        self.orders.append(response)
        return response

    async def cancel_order(self, order_id: str) -> bool:
        """Mark an order as cancelled if it exists."""
        for idx, order in enumerate(self.orders):
            if order.broker_order_id == order_id:
                updated = order.model_copy(update={
                    "status": OrderStatus.CANCELLED,
                    "updated_at": datetime.utcnow(),
                })
                self.orders[idx] = updated
                return True
        return False

    async def get_order_status(self, order_id: str) -> OrderResponse:
        """Return current status of an order."""
        for order in self.orders:
            if order.broker_order_id == order_id:
                return order
        raise BrokerError("ORDER_NOT_FOUND", f"Order {order_id} not found")

    def _update_position_on_fill(self, symbol: str, side: OrderSide, qty: Decimal, price: Decimal):
        """Update position logic (Netting)."""
        pos = self.positions.get(symbol)
        
        if not pos:
            # New Position
            new_pos = Position(
                symbol=symbol,
                quantity=qty if side == OrderSide.BUY else -qty,
                average_cost=price,
                current_price=price,
                market_value=qty * price,
                unrealized_pnl=Decimal("0"),
                leverage=1,
                exchange="bitunix_paper",
                currency="USDT"
            )
            self.positions[symbol] = new_pos
        else:
            # Existing Position - Netting Logic
            current_qty = pos.quantity
            fill_qty = qty if side == OrderSide.BUY else -qty
            new_qty = current_qty + fill_qty
            
            if new_qty == 0:
                # Position Closed
                # Realize PnL
                pnl = (price - pos.average_cost) * current_qty # (Exit - Entry) * Size
                self.balance_usdt += pnl
                del self.positions[symbol]
            elif (current_qty > 0 and fill_qty > 0) or (current_qty < 0 and fill_qty < 0):
                # Increase Position size (Average Up/Down)
                total_cost = (pos.average_cost * abs(current_qty)) + (price * abs(fill_qty))
                new_avg = total_cost / abs(new_qty)
                pos.quantity = new_qty
                pos.average_cost = new_avg
            else:
                # Partial Close / Flip
                # 1. Close portion
                closing_qty = min(abs(current_qty), abs(fill_qty)) * (-1 if current_qty > 0 else 1)
                
                # Realize PnL on closed portion
                # PnL = (Exit - Entry) * Closed_Size * Direction(1 for Long, -1 for Short)
                # Actually simpler: (Exit Price - Entry Price) * Quantity_Closed
                # If Long (qty>0), closing means selling. 
                realized_pnl = (price - pos.average_cost) * (closing_qty * (-1 if current_qty < 0 else 1)) # Logic check needed
                # Let's stick to: (Exit - Entry) * Qty
                # If I have 1 BTC Long @ 50k. Sell 0.5 @ 60k. 
                # PnL = (60k - 50k) * 0.5 = 5k.
                
                # Correct logic for linear futures:
                # Long: (Exit - Entry) * Qty
                # Short: (Entry - Exit) * Qty  => (Entry - Exit) * abs(Qty)
                
                # Helper:
                direction = 1 if current_qty > 0 else -1
                closed_abs_qty = min(abs(current_qty), abs(fill_qty))
                
                trade_pnl = (price - pos.average_cost) * closed_abs_qty * direction
                self.balance_usdt += trade_pnl
                
                # 2. Remaining / Flip
                remaining_qty = current_qty + fill_qty
                pos.quantity = remaining_qty
                
                if (current_qty > 0 > remaining_qty) or (current_qty < 0 < remaining_qty):
                    # Flip position -> Average cost becomes new price for the flipped part
                    pos.average_cost = price

            if symbol in self.positions:
                self._update_position_pnl(self.positions[symbol], price)

    def _update_position_pnl(self, pos: Position, current_price: Decimal):
        """Update PnL for a position."""
        pos.current_price = current_price
        diff = current_price - pos.average_cost
        pos.unrealized_pnl = diff * pos.quantity # Works for both Long (qty>0) and Short (qty<0)
        
        # PnL %
        if pos.average_cost > 0:
            # Simple unleveraged ROI
            pos.pnl_percentage = (float(pos.unrealized_pnl) / (float(pos.average_cost) * abs(float(pos.quantity)))) * 100
            
    def reset_account(self, amount: float = 10000.0):
        """Reset paper account."""
        self.start_balance = Decimal(str(amount))
        self.balance_usdt = self.start_balance
        self.positions.clear()
        self.orders.clear()

    # --- Market Data Methods (Delegation to HistoryManager) -------------------
    async def get_historical_bars(
        self,
        symbol: str,
        timeframe: str = "5m",
        limit: int = 200,
    ) -> list[dict] | None:
        """Get historical bars for the given symbol.

        Delegates to the HistoryManager if available.

        Args:
            symbol: Trading symbol (e.g., 'BTCUSDT')
            timeframe: Bar timeframe (e.g., '1m', '5m', '1h')
            limit: Maximum number of bars to return

        Returns:
            List of bar dictionaries with OHLCV data, or None if unavailable
        """
        if not self.history_manager:
            logger.warning(
                "BitunixPaperAdapter.get_historical_bars called but no history_manager set. "
                "Use set_history_manager() to enable market data."
            )
            return None

        try:
            from datetime import datetime, timedelta, timezone
            from src.core.market_data.types import DataRequest, Timeframe, AssetClass

            # Map timeframe string to Timeframe enum
            tf_map = {
                "1m": Timeframe.MINUTE_1,
                "5m": Timeframe.MINUTE_5,
                "10m": Timeframe.MINUTE_10,
                "15m": Timeframe.MINUTE_15,
                "30m": Timeframe.MINUTE_30,
                "1h": Timeframe.HOUR_1,
                "4h": Timeframe.HOUR_4,
                "1d": Timeframe.DAY_1,
            }
            tf = tf_map.get(timeframe, Timeframe.MINUTE_5)

            # Calculate time range based on limit and timeframe
            minutes_per_bar = {
                "1m": 1, "5m": 5, "15m": 15, "30m": 30,
                "1h": 60, "4h": 240, "1d": 1440,
            }
            minutes = minutes_per_bar.get(timeframe, 5) * limit

            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(minutes=minutes)

            # Create request for Bitunix-style symbol (BTCUSDT)
            request = DataRequest(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                timeframe=tf,
                asset_class=AssetClass.CRYPTO,
            )

            # Fetch data through HistoryManager
            bars, source = await self.history_manager.fetch_data(request)

            if not bars:
                logger.warning(f"No bars returned for {symbol} from {source}")
                return None

            # Convert HistoricalBar objects to dict format expected by TradingBotEngine
            result = []
            for bar in bars[-limit:]:  # Take last 'limit' bars
                result.append({
                    "timestamp": bar.timestamp,
                    "open": float(bar.open),
                    "high": float(bar.high),
                    "low": float(bar.low),
                    "close": float(bar.close),
                    "volume": bar.volume,
                })

            logger.debug(f"get_historical_bars: Returned {len(result)} bars for {symbol}")
            return result

        except Exception as e:
            logger.error(f"Failed to get historical bars for {symbol}: {e}")
            return None

    def set_history_manager(self, history_manager: "HistoryManager") -> None:
        """Set or update the HistoryManager for market data access.

        Args:
            history_manager: HistoryManager instance for fetching market data
        """
        self.history_manager = history_manager
        logger.info("BitunixPaperAdapter: HistoryManager set/updated")
