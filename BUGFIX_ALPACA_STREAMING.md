# Bugfix Report: Alpaca Streaming Stability

## Issue Description
The user reported that the WebSocket stream was failing or not establishing correctly. Upon code review, the following critical issues were identified in `AlpacaStreamClient` and `AlpacaCryptoStreamClient`:
1.  **No Reconnection Logic:** The `_run_stream` method simply awaited `self._stream._run_forever()`. If the underlying library's loop exited (due to network error, disconnect, or unhandled exception), the task would complete, and the stream would permanently stop.
2.  **Brittle Error Handling:** Exceptions in the stream loop were logged but caused the stream to terminate immediately.

## Fix Implementation
Refactored `_run_stream` in both `src/core/market_data/alpaca_stream.py` and `src/core/market_data/alpaca_crypto_stream.py` to implement a robust `while self.connected:` loop.

### Key Changes
1.  **Persistent Loop:** Wrapped the `_run_forever()` call in a `while self.connected` loop.
2.  **Automatic Reconnect:** If the inner `_run_forever()` returns (unexpected disconnect) or raises an exception, the loop waits 5 seconds and then attempts to restart the stream.
3.  **Logging:** Added specific logs for reconnection attempts and connection drops.

### Code Snippet (Generic)
```python
async def _run_stream(self):
    """Run the stream with automatic reconnection."""
    while self.connected:
        try:
            if self._stream:
                logger.info("Starting stream listener...")
                await self._stream._run_forever()
            
            # If run_forever returns, it means the connection closed
            if self.connected:
                logger.warning("Stream connection closed unexpectedly. Reconnecting in 5s...")
                await asyncio.sleep(5)
                
        except Exception as e:
            logger.error(f"Stream error: {e}")
            self.metrics.status = StreamStatus.ERROR
            
            if self.connected:
                logger.info("Attempting to reconnect in 5s...")
                await asyncio.sleep(5)
```

## Verification Checklist (for User)
1.  **Endpoint URL:** Checked and confirmed as correct (`wss://stream.data.alpaca.markets/v1beta3/crypto/us` for crypto, default IEX/SIP for stocks).
2.  **API Keys:** Confirmed they are passed correctly from `HistoryManager`.
3.  **Subscription:** Confirmed correct subscriptions to bars, trades, and quotes.
4.  **Reconnect Logic:** **FIXED** (see above).
5.  **Error Handling:** **IMPROVED** with retry logic.
6.  **Asyncio Loop:** Confirmed tasks are spawned correctly via `asyncio.create_task`.

The streaming should now be significantly more robust against network interruptions.
