# Live Chart Diagnosis

## Current Status
1.  **WebSocket Connection:** I reverted the "Sandbox URL" change because it caused an Authentication Failure (`auth failed`). The application is now back to using the standard Live URL, which your logs confirmed was connecting successfully (`connected to wss://stream.data.alpaca.markets/v1beta3/crypto/us`).
2.  **Chart Update Logic:** I have kept the "Timezone Fix" in `embedded_tradingview_chart.py`. This fix ensures that incoming live ticks (which are in UTC) are correctly compared against the historical data (also UTC) to prevent the "Cannot update oldest data" error.
3.  **Debug Logging:** I have verified that the `LIVE TICK DEBUG` logging is present in the code.

## Why it "doesn't work" (Hypothesis)
If the logs show "Connected" but you see no "Received crypto trade" logs:
- The stream is connected but silent. This can happen with `alpaca-py` if the subscription handshake completes but no data flows. This is often an internal library behavior or a network quirk.
- OR, you just haven't waited for the first trade (BTC/USD trades frequently, but can have 5-10s gaps).

## Next Steps
1.  **Restart** the application (essential to apply the revert).
2.  Start the Live Stream.
3.  **Wait** 15-30 seconds.
4.  **Send the logs.**

We need to see:
- `alpaca.data.live.websocket - connected`
- `alpaca.data.live.websocket - subscribed`
- **CRITICAL:** `src.core.market_data.alpaca_crypto_stream - 🔔 Received crypto trade...`
- **CRITICAL:** `ui.widgets.embedded_tradingview_chart - LIVE TICK DEBUG: ...`

If we see the first two but not the last two, the issue is **upstream** (Alpaca API not sending data to your client).
If we see "Received crypto trade" but not "LIVE TICK DEBUG", the issue is **internal** (EventBus failure).
