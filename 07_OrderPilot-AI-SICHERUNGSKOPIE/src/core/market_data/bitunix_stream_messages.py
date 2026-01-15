"""Bitunix Stream - Message Processing.

Refactored from bitunix_stream.py monolith.

Module 2/5 of bitunix_stream.py split.

Contains:
- on_message: Main message dispatcher
"""

from __future__ import annotations

import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class BitunixStreamMessages:
    """Helper für BitunixStreamClient message processing."""

    def __init__(self, parent):
        """
        Args:
            parent: BitunixStreamClient Instanz
        """
        self.parent = parent

    async def on_message(self, message: str) -> None:
        """Parse and handle incoming WebSocket messages.

        Args:
            message: JSON message string
        """
        try:
            data = json.loads(message)

            # Update metrics
            self.parent.metrics.messages_received += 1
            self.parent.metrics.last_message_at = datetime.utcnow()

            # Handle different message types
            op = data.get('op')

            # Log first few messages to help debug (including pings)
            if self.parent.metrics.messages_received <= 5:
                logger.debug(f"📨 Bitunix message #{self.parent.metrics.messages_received}: {data}")

            if op == 'ping':
                # Heartbeat response (keep-alive)
                logger.debug("💓 Heartbeat ping/pong received")
                return

            if op in {"subscribe", "unsubscribe"}:
                logger.info(f"Bitunix WS ack: {data}")
                return

            if op == "connect":
                logger.info("✅ Bitunix Stream: Server confirmed connection")
                return

            if op == "error":
                error_code = data.get('code', 'unknown')
                error_msg = data.get('message', data.get('msg', 'Unknown error'))
                error_data = data.get('data', {})
                logger.error(f"❌ Bitunix Stream: Server error received!")
                logger.error(f"   Error Code: {error_code}")
                logger.error(f"   Error Message: {error_msg}")
                if error_data:
                    logger.error(f"   Error Data: {error_data}")
                logger.error(f"   Full Response: {data}")
                return

            # Channel messages
            channel = data.get('ch', '')

            if 'kline' in channel or 'market_kline' in channel:
                await self.parent._handlers.handle_kline(data)
            elif 'ticker' in channel:
                await self.parent._handlers.handle_ticker(data)
            elif 'depth' in channel:
                await self.parent._handlers.handle_depth(data)
            elif 'trade' in channel:
                await self.parent._handlers.handle_trade(data)
            else:
                # Unknown/heartbeat noise -> debug only
                logger.debug(f"⚠ Bitunix: Unknown message type (op={op}, ch={channel}): {data}")

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse message: {e}")
            self.parent.metrics.messages_dropped += 1
        except Exception as e:
            logger.error(f"Message processing error: {e}", exc_info=True)
            self.parent.metrics.messages_dropped += 1
