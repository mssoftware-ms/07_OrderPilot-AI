#!/usr/bin/env python
"""Test Bitunix Adapter Connection - End-to-End Test.

This test verifies that the BitunixAdapter can successfully connect
and authenticate with the Bitunix API.
"""

import asyncio
import os
import sys
import logging
from pathlib import Path

# Add parent directory to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_adapter_connection():
    """Test BitunixAdapter connection end-to-end."""

    logger.info("=" * 80)
    logger.info("BITUNIX ADAPTER CONNECTION TEST")
    logger.info("=" * 80)

    # 1. Get credentials from environment
    api_key = os.environ.get("BITUNIX_API_KEY")
    api_secret = os.environ.get("BITUNIX_SECRET_KEY")

    if not api_key or not api_secret:
        logger.error("❌ BITUNIX_API_KEY and BITUNIX_SECRET_KEY must be set")
        return False

    logger.info(f"✅ API Key: {api_key[:8]}...")
    logger.info(f"✅ API Secret: {api_secret[:8]}...")

    # 2. Create adapter
    logger.info("\nCreating BitunixAdapter...")
    try:
        from src.core.broker.bitunix_adapter import BitunixAdapter

        adapter = BitunixAdapter(
            api_key=api_key,
            api_secret=api_secret,
            use_testnet=False  # Using mainnet
        )
        logger.info("✅ Adapter created successfully")

    except Exception as e:
        logger.error(f"❌ Failed to create adapter: {e}", exc_info=True)
        return False

    # 3. Connect adapter
    logger.info("\nConnecting to Bitunix API...")
    try:
        await adapter.connect()
        logger.info("✅ Adapter connected successfully!")

    except Exception as e:
        logger.error(f"❌ Failed to connect adapter: {e}", exc_info=True)
        return False

    # 4. Get balance
    logger.info("\nFetching account balance...")
    try:
        balance = await adapter.get_balance()

        if balance:
            logger.info("✅ Balance retrieved successfully!")
            logger.info(f"\n   Account Balance:")
            logger.info(f"   - Currency: {balance.currency}")
            logger.info(f"   - Available Cash: {balance.cash}")
            logger.info(f"   - Market Value: {balance.market_value}")
            logger.info(f"   - Total Equity: {balance.total_equity}")
            logger.info(f"   - Buying Power: {balance.buying_power}")
            logger.info(f"   - Margin Used: {balance.margin_used}")
            logger.info(f"   - Margin Available: {balance.margin_available}")
            logger.info(f"   - Unrealized PNL: {balance.daily_pnl}")
        else:
            logger.error("❌ Balance is None")
            return False

    except Exception as e:
        logger.error(f"❌ Failed to get balance: {e}", exc_info=True)
        return False

    # 5. Disconnect adapter
    logger.info("\nDisconnecting adapter...")
    try:
        await adapter.disconnect()
        logger.info("✅ Adapter disconnected successfully")

    except Exception as e:
        logger.error(f"❌ Failed to disconnect adapter: {e}", exc_info=True)
        return False

    return True


if __name__ == "__main__":
    result = asyncio.run(test_adapter_connection())

    logger.info("\n" + "=" * 80)
    logger.info("FINAL RESULT")
    logger.info("=" * 80)

    if result:
        logger.info("✅ ALL TESTS PASSED - Bitunix Adapter is working correctly!")
        sys.exit(0)
    else:
        logger.error("❌ TEST FAILED - See errors above")
        sys.exit(1)
