"""Interactive Brokers (IBKR) Adapter - Official API.

Uses the official IBKR TWS/Gateway API for reliable trading.
"""

import asyncio
import logging
import threading
from datetime import datetime
from decimal import Decimal
from typing import Any

from ibapi.client import EClient
from ibapi.common import BarData, OrderId, TickerId
from ibapi.contract import Contract
from ibapi.order import Order as IBOrder
from ibapi.wrapper import EWrapper

from src.common.logging_setup import log_order_action
from src.database.models import OrderSide, OrderStatus, OrderType, TimeInForce

from .base import (
    Balance,
    BrokerAdapter,
    BrokerConnectionError,
    FeeModel,
    OrderRequest,
    OrderResponse,
    Position,
)

logger = logging.getLogger(__name__)


class IBKRWrapper(EWrapper):
    """IB API Wrapper for handling callbacks."""

    def __init__(self):
        super().__init__()
        self.connection_event = threading.Event()
        self.order_responses: dict[int, OrderResponse] = {}
        self.positions: list[Position] = []
        self.account_values: dict[str, Any] = {}
        self.market_data: dict[int, dict[str, Any]] = {}
        self.historical_data: dict[int, list[BarData]] = {}
        self.errors: list[dict[str, Any]] = []

    def nextValidId(self, orderId: int):
        """Callback for next valid order ID."""
        super().nextValidId(orderId)
        self.next_order_id = orderId
        self.connection_event.set()
        logger.info(f"Connected to IBKR, next order ID: {orderId}")

    def connectionClosed(self):
        """Callback when connection is closed."""
        logger.warning("IBKR connection closed")
        self.connection_event.clear()

    def error(self, reqId: TickerId, errorCode: int, errorString: str):
        """Error callback."""
        error_info = {
            "reqId": reqId,
            "errorCode": errorCode,
            "errorString": errorString,
            "timestamp": datetime.utcnow()
        }
        self.errors.append(error_info)

        if errorCode < 2000:  # Information messages
            logger.info(f"IBKR info: {errorString}")
        elif errorCode < 10000:  # System messages
            logger.warning(f"IBKR warning: {errorString}")
        else:  # Error messages
            logger.error(f"IBKR error: {errorString}")

    def orderStatus(self, orderId: OrderId, status: str, filled: float,
                   _remaining: float, avgFillPrice: float, _permId: int,
                   _parentId: int, _lastFillPrice: float, _clientId: int,
                   _whyHeld: str, _mktCapPrice: float):
        """Order status update callback."""
        if orderId in self.order_responses:
            order_resp = self.order_responses[orderId]
            order_resp.status = self._map_order_status(status)
            order_resp.filled_quantity = Decimal(str(filled))
            order_resp.average_fill_price = Decimal(str(avgFillPrice)) if avgFillPrice > 0 else None
            order_resp.updated_at = datetime.utcnow()

            logger.info(f"Order {orderId} status: {status}, filled: {filled}")

    def position(self, account: str, contract: Contract, position: float,
                avgCost: float):
        """Position update callback."""
        pos = Position(
            symbol=contract.symbol,
            quantity=Decimal(str(position)),
            average_cost=Decimal(str(avgCost)),
            currency=contract.currency or "USD"
        )
        self.positions.append(pos)

    def accountSummary(self, reqId: int, account: str, tag: str, value: str,
                      currency: str):
        """Account summary callback."""
        self.account_values[tag] = {
            "value": value,
            "currency": currency
        }

    def historicalData(self, reqId: int, bar: BarData):
        """Historical data callback."""
        if reqId not in self.historical_data:
            self.historical_data[reqId] = []
        self.historical_data[reqId].append(bar)

    def tickPrice(self, reqId: TickerId, tickType: int, price: float,
                 _attrib: Any):
        """Tick price callback."""
        if reqId not in self.market_data:
            self.market_data[reqId] = {}

        tick_map = {
            1: "bid",
            2: "ask",
            4: "last",
            6: "high",
            7: "low",
            9: "close"
        }

        if tickType in tick_map:
            self.market_data[reqId][tick_map[tickType]] = price

    def _map_order_status(self, ib_status: str) -> OrderStatus:
        """Map IB order status to internal status."""
        status_map = {
            "PendingSubmit": OrderStatus.PENDING,
            "PendingCancel": OrderStatus.PENDING,
            "PreSubmitted": OrderStatus.PENDING,
            "Submitted": OrderStatus.SUBMITTED,
            "Filled": OrderStatus.FILLED,
            "Cancelled": OrderStatus.CANCELLED,
            "Inactive": OrderStatus.CANCELLED
        }
        return status_map.get(ib_status, OrderStatus.PENDING)


class IBKRClient(EClient):
    """IB API Client."""

    def __init__(self, wrapper):
        super().__init__(wrapper)


class IBKRAdapter(BrokerAdapter):
    """Interactive Brokers adapter using official TWS/Gateway API."""

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 7497,  # 7497 for TWS Paper, 7496 for TWS Live
        client_id: int = 1,
        paper_trading: bool = True,
        **kwargs
    ):
        """Initialize IBKR adapter.

        Args:
            host: TWS/Gateway host
            port: TWS/Gateway port (7497 for paper, 7496 for live)
            client_id: Unique client ID
            paper_trading: Whether to use paper trading
            **kwargs: Additional arguments for base class
        """
        # Set up fee model for IBKR
        if 'fee_model' not in kwargs:
            kwargs['fee_model'] = FeeModel(
                broker="ibkr",
                fee_type="tiered",
                flat_fee=Decimal('0.35'),  # Minimum per order
                percentage=0.0035,  # 0.35% for stocks
                min_fee=Decimal('0.35'),
                max_fee=Decimal('1.00')
            )

        super().__init__(name="IBKR", **kwargs)

        self.host = host
        self.port = port
        self.client_id = client_id
        self.paper_trading = paper_trading

        # Initialize IB API components
        self.wrapper = IBKRWrapper()
        self.client = IBKRClient(self.wrapper)

        # Threading for IB API
        self.api_thread: threading.Thread | None = None

        # Request ID management
        self.next_req_id = 1
        self.req_id_lock = threading.Lock()

        # Order tracking
        self.pending_orders: dict[int, OrderRequest] = {}

        logger.info(f"IBKR adapter initialized: {host}:{port} (paper={paper_trading})")

    def _get_next_req_id(self) -> int:
        """Get next request ID thread-safely."""
        with self.req_id_lock:
            req_id = self.next_req_id
            self.next_req_id += 1
            return req_id

    # ==================== Template Method Implementations ====================

    async def _establish_connection(self) -> None:
        """Establish connection to IBKR TWS/Gateway (template method implementation)."""
        # Connect to TWS/Gateway
        self.client.connect(self.host, self.port, self.client_id)

        # Start API thread
        self.api_thread = threading.Thread(
            target=self.client.run,
            daemon=True
        )
        self.api_thread.start()

    async def _verify_connection(self) -> None:
        """Verify IBKR connection by waiting for connection event."""
        # Wait for connection
        if not self.wrapper.connection_event.wait(timeout=10):
            raise BrokerConnectionError(
                "IBKR_TIMEOUT",
                "Connection timeout - ensure TWS/Gateway is running"
            )

        logger.info(f"IBKR connection verified ({'Paper' if self.paper_trading else 'Live'} Trading)")

    async def _setup_initial_state(self) -> None:
        """Request initial account and position data (template method implementation)."""
        # Request account summary
        self.client.reqAccountSummary(
            self._get_next_req_id(),
            "All",
            "TotalCashValue,NetLiquidation,BuyingPower"
        )

        # Request positions
        self.client.reqPositions()

        # Give time for responses
        await asyncio.sleep(2)

    async def _cleanup_resources(self) -> None:
        """Clean up IBKR resources (template method implementation)."""
        if self.client.isConnected():
            self.client.disconnect()

    async def is_connected(self) -> bool:
        """Check if connected to IBKR."""
        return self._connected and self.client.isConnected()

    async def _place_order_impl(
        self,
        order: OrderRequest,
        estimated_fee: Decimal
    ) -> OrderResponse:
        """Place order with IBKR."""
        if not self.client.isConnected():
            raise BrokerConnectionError("NOT_CONNECTED", "Not connected to IBKR")

        # Create IB contract
        contract = self._create_contract(order.symbol)

        # Create IB order
        ib_order = self._create_ib_order(order)

        # Get order ID
        order_id = self.wrapper.next_order_id
        self.wrapper.next_order_id += 1

        # Track order
        self.pending_orders[order_id] = order

        # Create order response
        order_response = OrderResponse(
            broker_order_id=str(order_id),
            internal_order_id=order.internal_order_id or str(order_id),
            status=OrderStatus.PENDING,
            symbol=order.symbol,
            side=order.side,
            order_type=order.order_type,
            quantity=order.quantity,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            estimated_fee=estimated_fee
        )

        self.wrapper.order_responses[order_id] = order_response

        # Place order
        self.client.placeOrder(order_id, contract, ib_order)

        # Log order action
        log_order_action(
            action="placed",
            order_id=str(order_id),
            symbol=order.symbol,
            details={
                "broker": "ibkr",
                "paper": self.paper_trading,
                "ai_analysis": order.ai_analysis
            }
        )

        # Wait briefly for initial status
        await asyncio.sleep(0.5)

        return order_response

    def _create_contract(self, symbol: str) -> Contract:
        """Create IB contract object."""
        contract = Contract()
        contract.symbol = symbol
        contract.secType = "STK"  # Stock
        contract.exchange = "SMART"  # Smart routing
        contract.currency = "USD"
        return contract

    def _create_ib_order(self, order: OrderRequest) -> IBOrder:
        """Create IB order object."""
        ib_order = IBOrder()

        # Order action
        ib_order.action = "BUY" if order.side == OrderSide.BUY else "SELL"

        # Order type
        if order.order_type == OrderType.LIMIT:
            ib_order.orderType = "LMT"
            ib_order.lmtPrice = float(order.limit_price)
        elif order.order_type == OrderType.STOP:
            ib_order.orderType = "STP"
            ib_order.auxPrice = float(order.stop_price)
        elif order.order_type == OrderType.STOP_LIMIT:
            ib_order.orderType = "STP LMT"
            ib_order.lmtPrice = float(order.limit_price)
            ib_order.auxPrice = float(order.stop_price)
        else:  # Market
            ib_order.orderType = "MKT"

        # Quantity
        ib_order.totalQuantity = int(order.quantity)

        # Time in force
        if order.time_in_force == TimeInForce.DAY:
            ib_order.tif = "DAY"
        elif order.time_in_force == TimeInForce.GTC:
            ib_order.tif = "GTC"
        else:
            ib_order.tif = "DAY"

        return ib_order

    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an order."""
        try:
            self.client.cancelOrder(int(order_id))
            await asyncio.sleep(0.5)  # Wait for cancellation
            return True
        except Exception as e:
            logger.error(f"Failed to cancel order {order_id}: {e}")
            return False

    async def get_order_status(self, order_id: str) -> OrderResponse:
        """Get current order status."""
        order_id_int = int(order_id)
        if order_id_int in self.wrapper.order_responses:
            return self.wrapper.order_responses[order_id_int]
        else:
            raise ValueError(f"Order not found: {order_id}")

    async def get_positions(self) -> list[Position]:
        """Get all current positions."""
        # Clear existing positions
        self.wrapper.positions.clear()

        # Request current positions
        self.client.reqPositions()

        # Wait for response
        await asyncio.sleep(2)

        return self.wrapper.positions

    async def get_balance(self) -> Balance:
        """Get account balance."""
        # Request account summary
        req_id = self._get_next_req_id()
        self.client.reqAccountSummary(
            req_id,
            "All",
            "TotalCashValue,NetLiquidation,BuyingPower,DailyPnL"
        )

        # Wait for response
        await asyncio.sleep(2)

        # Parse account values
        cash = Decimal(self.wrapper.account_values.get(
            "TotalCashValue", {"value": "0"})["value"]
        )
        net_liquidation = Decimal(self.wrapper.account_values.get(
            "NetLiquidation", {"value": "0"})["value"]
        )
        buying_power = Decimal(self.wrapper.account_values.get(
            "BuyingPower", {"value": "0"})["value"]
        )
        daily_pnl = Decimal(self.wrapper.account_values.get(
            "DailyPnL", {"value": "0"})["value"]
        )

        return Balance(
            cash=cash,
            market_value=net_liquidation - cash,
            total_equity=net_liquidation,
            buying_power=buying_power,
            daily_pnl=daily_pnl
        )

    async def get_quote(self, symbol: str) -> dict[str, Any] | None:
        """Get current quote for symbol."""
        req_id = self._get_next_req_id()

        # Create contract
        contract = self._create_contract(symbol)

        # Request market data
        self.client.reqMktData(
            req_id,
            contract,
            "",  # Generic tick list
            False,  # Snapshot
            False,  # Regulatory snapshot
            []
        )

        # Wait for data
        await asyncio.sleep(1)

        # Cancel market data
        self.client.cancelMktData(req_id)

        if req_id in self.wrapper.market_data:
            data = self.wrapper.market_data[req_id]
            return {
                'symbol': symbol,
                'bid': data.get('bid'),
                'ask': data.get('ask'),
                'last': data.get('last'),
                'high': data.get('high'),
                'low': data.get('low'),
                'close': data.get('close'),
                'timestamp': datetime.utcnow()
            }

        return None

    async def get_historical_bars(
        self,
        symbol: str,
        duration: str = "1 D",
        bar_size: str = "1 min"
    ) -> list[dict[str, Any]]:
        """Get historical bars for symbol.

        Args:
            symbol: Trading symbol
            duration: Duration string (e.g., "1 D", "1 W")
            bar_size: Bar size (e.g., "1 min", "5 mins", "1 hour")

        Returns:
            List of bar data
        """
        req_id = self._get_next_req_id()

        # Create contract
        contract = self._create_contract(symbol)

        # Clear existing data
        self.wrapper.historical_data[req_id] = []

        # Request historical data
        self.client.reqHistoricalData(
            req_id,
            contract,
            "",  # End datetime (empty = now)
            duration,
            bar_size,
            "TRADES",  # What to show
            1,  # Use RTH
            1,  # Format date as yyyyMMdd HH:mm:ss
            False,  # Keep up to date
            []
        )

        # Wait for data
        await asyncio.sleep(3)

        # Convert to dict format
        bars = []
        for bar in self.wrapper.historical_data.get(req_id, []):
            bars.append({
                'timestamp': bar.date,
                'open': bar.open,
                'high': bar.high,
                'low': bar.low,
                'close': bar.close,
                'volume': bar.volume,
                'vwap': bar.average
            })

        return bars