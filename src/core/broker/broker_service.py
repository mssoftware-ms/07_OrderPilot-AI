"""BrokerService Singleton for OrderPilot-AI.

Provides centralized broker management with thread-safe connection handling.
All ChartWindows and UI components should use this service instead of
managing broker connections directly.

Part of Phase 0: Singleton Services (UI Refactoring Plan)
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from src.common.event_bus import Event, EventType, event_bus
from src.config.loader import config_manager

if TYPE_CHECKING:
    from src.core.broker.base import BrokerAdapter

logger = logging.getLogger(__name__)


class BrokerService:
    """Singleton service for centralized broker management.
    
    This service owns the broker connection and provides thread-safe
    connect/disconnect operations. UI components should emit events
    (BROKER_CONNECT_REQUESTED, BROKER_DISCONNECT_REQUESTED) rather than
    calling connect/disconnect directly.
    
    Usage:
        # Get the singleton instance
        broker_service = BrokerService.instance()
        
        # Connect to broker (async)
        await broker_service.connect("Interactive Brokers")
        
        # Check connection status
        if broker_service.is_connected:
            positions = await broker_service.broker.get_positions()
        
        # Disconnect
        await broker_service.disconnect()
    
    Events Emitted:
        - BROKER_CONNECTED: When connection succeeds
        - BROKER_DISCONNECTED: When disconnection completes
    
    Events Subscribed:
        - BROKER_CONNECT_REQUESTED: Trigger async connect
        - BROKER_DISCONNECT_REQUESTED: Trigger async disconnect
    """
    
    _instance: Optional['BrokerService'] = None
    _lock = asyncio.Lock()
    
    @classmethod
    def instance(cls) -> 'BrokerService':
        """Get the singleton instance.
        
        Returns:
            The global BrokerService instance
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @classmethod
    def reset_instance(cls) -> None:
        """Reset the singleton instance (for testing only)."""
        cls._instance = None
    
    def __init__(self):
        """Initialize the BrokerService.
        
        Note: Use BrokerService.instance() instead of direct instantiation.
        """
        if BrokerService._instance is not None:
            raise RuntimeError(
                "BrokerService is a singleton. Use BrokerService.instance()"
            )
        
        self._broker: Optional[BrokerAdapter] = None
        self._broker_type: str = ""
        self._connection_lock = asyncio.Lock()
        self._connected = False
        self._connecting = False
        self._last_error: Optional[Exception] = None
        
        # Subscribe to broker events
        self._setup_event_subscriptions()
        
        logger.info("BrokerService initialized")
    
    def _setup_event_subscriptions(self) -> None:
        """Subscribe to broker-related events."""
        # Note: These are for UI components to request actions
        # The actual handling is done via async methods
        pass  # Event handling will be connected in Phase 2
    
    @property
    def broker(self) -> Optional['BrokerAdapter']:
        """Get the current broker adapter.
        
        Returns:
            The active BrokerAdapter or None if not connected
        """
        return self._broker
    
    @property
    def broker_type(self) -> str:
        """Get the current broker type name.
        
        Returns:
            Broker type string (e.g., "Interactive Brokers")
        """
        return self._broker_type
    
    @property
    def is_connected(self) -> bool:
        """Check if broker is connected.
        
        Returns:
            True if connected to a broker
        """
        return self._connected and self._broker is not None
    
    @property
    def is_connecting(self) -> bool:
        """Check if connection is in progress.
        
        Returns:
            True if currently connecting
        """
        return self._connecting
    
    @property
    def last_error(self) -> Optional[Exception]:
        """Get the last connection error.
        
        Returns:
            The last exception or None
        """
        return self._last_error
    
    async def connect(self, broker_type: str) -> bool:
        """Connect to a broker (thread-safe).
        
        Uses asyncio.Lock to prevent race conditions when multiple
        UI components attempt to connect simultaneously.
        
        Args:
            broker_type: Broker name ("Mock Broker", "Interactive Brokers", 
                        "Trade Republic", "Alpaca", "Bitunix")
        
        Returns:
            True if connection succeeded, False otherwise
        """
        async with self._connection_lock:
            # Already connected to this broker?
            if self._connected and self._broker_type == broker_type:
                logger.debug(f"Already connected to {broker_type}")
                return True
            
            # Disconnect from current broker first
            if self._connected:
                await self._disconnect_internal()
            
            self._connecting = True
            self._last_error = None
            
            try:
                logger.info(f"Connecting to {broker_type}...")
                
                # Create broker adapter
                self._broker = await self._create_broker(broker_type)
                
                if self._broker is None:
                    raise ValueError(f"Unknown broker type: {broker_type}")
                
                # Connect
                await self._broker.connect()
                
                self._connected = True
                self._broker_type = broker_type
                self._connecting = False
                
                # Emit connected event
                event_bus.emit(Event(
                    type=EventType.MARKET_CONNECTED,
                    timestamp=datetime.now(),
                    data={
                        "broker": broker_type,
                        "broker_name": self._broker.name,
                    },
                    source="BrokerService"
                ))
                
                logger.info(f"Successfully connected to {broker_type}")
                return True
                
            except Exception as e:
                self._connected = False
                self._connecting = False
                self._last_error = e
                self._broker = None
                self._broker_type = ""
                
                logger.error(f"Failed to connect to {broker_type}: {e}")
                return False
    
    async def disconnect(self) -> None:
        """Disconnect from current broker (thread-safe).
        
        Uses asyncio.Lock to prevent race conditions.
        """
        async with self._connection_lock:
            await self._disconnect_internal()
    
    async def _disconnect_internal(self) -> None:
        """Internal disconnect (must be called with lock held)."""
        if not self._connected:
            logger.debug("Already disconnected")
            return
        
        broker_type = self._broker_type
        
        try:
            if self._broker:
                await self._broker.disconnect()
        except Exception as e:
            logger.error(f"Error during disconnect: {e}")
        finally:
            self._broker = None
            self._connected = False
            self._broker_type = ""
            
            # Emit disconnected event
            event_bus.emit(Event(
                type=EventType.MARKET_DISCONNECTED,
                timestamp=datetime.now(),
                data={"broker": broker_type},
                source="BrokerService"
            ))
            
            logger.info(f"Disconnected from {broker_type}")
    
    async def _create_broker(self, broker_type: str) -> Optional['BrokerAdapter']:
        """Create a broker adapter based on type.
        
        Args:
            broker_type: Broker name
        
        Returns:
            BrokerAdapter instance or None if unknown type
        """
        from decimal import Decimal
        
        # Import broker implementations
        from src.core.broker.mock_broker import MockBroker
        from src.core.broker.ibkr_adapter import IBKRAdapter
        from src.core.broker.trade_republic_adapter import TradeRepublicAdapter
        from src.core.broker.alpaca_adapter import AlpacaAdapter
        from src.core.broker.bitunix_adapter import BitunixAdapter
        
        if broker_type == "Mock Broker":
            return MockBroker(initial_cash=Decimal("10000"))
        
        elif broker_type == "Interactive Brokers":
            from PyQt6.QtCore import QSettings
            settings = QSettings("OrderPilot", "TradingApp")
            
            ibkr_host = settings.value("ibkr_host", "localhost")
            ibkr_port_text = settings.value("ibkr_port", "7497 (Paper)")
            ibkr_port = int(ibkr_port_text.split()[0])
            ibkr_client_id = int(settings.value("ibkr_client_id", "1"))
            
            return IBKRAdapter(
                host=ibkr_host,
                port=ibkr_port,
                client_id=ibkr_client_id
            )
        
        elif broker_type == "Trade Republic":
            from PyQt6.QtCore import QSettings
            settings = QSettings("OrderPilot", "TradingApp")
            
            tr_phone = settings.value("tr_phone", "")
            tr_pin = config_manager.get_credential("tr_pin")
            
            if not tr_phone or not tr_pin:
                raise ValueError("Trade Republic credentials not configured")
            
            return TradeRepublicAdapter(
                phone_number=tr_phone,
                pin=tr_pin
            )
        
        elif broker_type == "Alpaca":
            api_key = config_manager.get_credential("alpaca_api_key")
            api_secret = config_manager.get_credential("alpaca_api_secret")
            
            if not api_key or not api_secret:
                raise ValueError("Alpaca API credentials not configured")
            
            return AlpacaAdapter(
                api_key=api_key,
                api_secret=api_secret,
                paper=True  # Default to paper trading
            )
        
        elif broker_type == "Bitunix":
            from PyQt6.QtCore import QSettings
            settings = QSettings("OrderPilot", "TradingApp")
            
            api_key = config_manager.get_credential("bitunix_api_key")
            api_secret = config_manager.get_credential("bitunix_secret_key")
            use_testnet = settings.value("bitunix_testnet", True, type=bool)
            
            if not api_key or not api_secret:
                raise ValueError("Bitunix API credentials not configured")
            
            return BitunixAdapter(
                api_key=api_key,
                api_secret=api_secret,
                testnet=use_testnet
            )
        
        else:
            logger.error(f"Unknown broker type: {broker_type}")
            return None


# Convenience function for getting the singleton
def get_broker_service() -> BrokerService:
    """Get the global BrokerService instance.
    
    Returns:
        The BrokerService singleton
    """
    return BrokerService.instance()
