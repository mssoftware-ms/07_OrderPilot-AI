"""Bitunix Stream - Subscription Management.

Refactored from bitunix_stream.py monolith.

Module 4/5 of bitunix_stream.py split.

Contains:
- normalize_symbol: Symbol normalization
- build_subscription_args: Build sub/unsub payload
- handle_subscription: Subscribe to symbols
- handle_unsubscription: Unsubscribe from symbols
"""

from __future__ import annotations

import json
import logging

logger = logging.getLogger(__name__)


class BitunixStreamSubscription:
    """Helper für BitunixStreamClient subscription management."""

    def __init__(self, parent):
        """
        Args:
            parent: BitunixStreamClient Instanz
        """
        self.parent = parent

    @staticmethod
    def normalize_symbol(symbol: str) -> str:
        """Normalize symbols to Bitunix format (uppercase, no separators)."""
        return str(symbol).replace("/", "").replace("-", "").upper()

    def build_subscription_args(self, symbols: list[str]) -> list[dict[str, str]]:
        """Build subscription args for ticker + 1m kline channels."""
        args: list[dict[str, str]] = []
        for symbol in symbols:
            normalized = self.normalize_symbol(symbol)
            args.append({"symbol": normalized, "ch": self.parent._kline_channel})
            args.append({"symbol": normalized, "ch": "ticker"})
        return args

    async def handle_subscription(self, symbols: list[str]) -> None:
        """Send subscription request for given symbols."""
        if not self.parent.ws or not self.parent._connection._is_ws_open(self.parent.ws):
            logger.warning("⚠️ Bitunix Stream: WebSocket not connected; subscription deferred")
            return

        args = self.build_subscription_args(symbols)
        if not args:
            logger.warning("⚠️ Bitunix Stream: No subscription args generated (no symbols)")
            return

        payload = {"op": "subscribe", "args": args}
        logger.info(f"📡 Bitunix Stream: Subscribing to {len(args)} channels for {len(symbols)} symbols...")
        logger.debug(f"📡 Bitunix Stream: Subscription payload: {payload}")

        try:
            await self.parent.ws.send(json.dumps(payload))
            logger.info(f"✅ Bitunix Stream: Subscription request sent for {len(symbols)} symbols")
        except Exception as e:
            logger.error(f"❌ Bitunix Stream: Failed to send subscription: {e}")

    async def handle_unsubscription(self, symbols: list[str]) -> None:
        """Send unsubscription request for given symbols."""
        if not self.parent.ws or not self.parent._connection._is_ws_open(self.parent.ws):
            logger.warning("⚠️ Bitunix Stream: WebSocket not connected; unsubscription skipped")
            return

        args = self.build_subscription_args(symbols)
        payload = {"op": "unsubscribe", "args": args}
        logger.info(f"📡 Bitunix Stream: Unsubscribing from {len(args)} channels for {len(symbols)} symbols...")
        logger.debug(f"📡 Bitunix Stream: Unsubscription payload: {payload}")

        try:
            await self.parent.ws.send(json.dumps(payload))
            logger.info(f"✅ Bitunix Stream: Unsubscription request sent for {len(symbols)} symbols")
        except Exception as e:
            logger.error(f"❌ Bitunix Stream: Failed to send unsubscription: {e}")
