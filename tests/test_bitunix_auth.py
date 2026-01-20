#!/usr/bin/env python
"""Test Bitunix Authentication - Diagnose-Skript.

Dieses Skript testet die Bitunix-Authentifizierung Schritt für Schritt.
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
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_bitunix_auth():
    """Test Bitunix authentication step by step."""

    # 1. Check environment variables
    logger.info("=" * 80)
    logger.info("STEP 1: Checking environment variables")
    logger.info("=" * 80)

    api_key = os.environ.get("BITUNIX_API_KEY")
    api_secret = os.environ.get("BITUNIX_SECRET_KEY")

    if not api_key:
        logger.error("❌ BITUNIX_API_KEY not found in environment")
        return False
    if not api_secret:
        logger.error("❌ BITUNIX_SECRET_KEY not found in environment")
        return False

    logger.info(f"✅ BITUNIX_API_KEY found: {api_key[:8]}...")
    logger.info(f"✅ BITUNIX_SECRET_KEY found: {api_secret[:8]}...")

    # 2. Test ConfigManager
    logger.info("\n" + "=" * 80)
    logger.info("STEP 2: Testing ConfigManager credential loading")
    logger.info("=" * 80)

    try:
        from src.config.loader import config_manager

        cm_api_key = config_manager.get_credential("bitunix_api_key")
        cm_api_secret = config_manager.get_credential("bitunix_secret_key")

        if cm_api_key == api_key:
            logger.info(f"✅ ConfigManager loaded API key correctly: {cm_api_key[:8]}...")
        else:
            logger.error(f"❌ ConfigManager API key mismatch!")
            logger.error(f"   Expected: {api_key[:8]}...")
            logger.error(f"   Got: {cm_api_key[:8] if cm_api_key else 'None'}...")

        if cm_api_secret == api_secret:
            logger.info(f"✅ ConfigManager loaded API secret correctly: {cm_api_secret[:8]}...")
        else:
            logger.error(f"❌ ConfigManager API secret mismatch!")
            logger.error(f"   Expected: {api_secret[:8]}...")
            logger.error(f"   Got: {cm_api_secret[:8] if cm_api_secret else 'None'}...")

    except Exception as e:
        logger.error(f"❌ ConfigManager error: {e}", exc_info=True)
        return False

    # 3. Test Signer
    logger.info("\n" + "=" * 80)
    logger.info("STEP 3: Testing BitunixSigner")
    logger.info("=" * 80)

    try:
        from src.core.auth.bitunix_signer import BitunixSigner

        signer = BitunixSigner(api_key, api_secret)
        headers = signer.build_headers(query_params="", body="")

        logger.info(f"✅ Signer created headers:")
        for key, value in headers.items():
            if key == 'sign':
                logger.info(f"   {key}: {value[:16]}...")
            else:
                logger.info(f"   {key}: {value}")

    except Exception as e:
        logger.error(f"❌ Signer error: {e}", exc_info=True)
        return False

    # 4. Test API Request
    logger.info("\n" + "=" * 80)
    logger.info("STEP 4: Testing actual API request to Bitunix")
    logger.info("=" * 80)

    try:
        import aiohttp
        from src.core.auth.bitunix_signer import BitunixSigner

        base_url = "https://fapi.bitunix.com"
        endpoint = "/api/v1/futures/account"

        # Bitunix requires marginCoin parameter (according to official demo)
        params = {"marginCoin": "USDT"}

        # Sort params for signature (key1value1key2value2...)
        query_string = ''.join(f"{k}{v}" for k, v in sorted(params.items()))

        signer = BitunixSigner(api_key, api_secret)
        headers = signer.build_headers(query_params=query_string, body="")

        logger.info(f"Request URL: {base_url}{endpoint}")
        logger.info(f"Request Method: GET")
        logger.info(f"Request Params: {params}")
        logger.info(f"Request Query String (for signature): {query_string}")
        logger.info(f"Request Headers: {headers}")

        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{base_url}{endpoint}",
                params=params,  # Pass params for URL construction
                headers=headers
            ) as response:
                status = response.status
                content_type = response.headers.get('Content-Type', '')

                logger.info(f"\nResponse Status: {status}")
                logger.info(f"Response Content-Type: {content_type}")

                # Try to get response text
                try:
                    response_text = await response.text()
                    logger.info(f"Response Body: {response_text[:500]}...")

                    # Try to parse as JSON
                    if 'application/json' in content_type:
                        response_json = await response.json()
                        logger.info(f"Response JSON: {response_json}")

                        # Check for specific error codes
                        if 'code' in response_json:
                            code = response_json['code']
                            msg = response_json.get('msg', '')

                            if code == 0:
                                logger.info("✅ API request successful!")
                                logger.info(f"   Account data: {response_json.get('data', {})}")
                                return True
                            else:
                                logger.error(f"❌ API returned error code {code}: {msg}")
                                return False

                except Exception as e:
                    logger.error(f"Error parsing response: {e}")

                if status == 200:
                    logger.info("✅ HTTP 200 OK - Authentication successful!")
                    return True
                elif status == 401:
                    logger.error("❌ HTTP 401 Unauthorized - Invalid API key or signature")
                    return False
                elif status == 403:
                    logger.error("❌ HTTP 403 Forbidden - API key lacks permissions")
                    return False
                else:
                    logger.error(f"❌ HTTP {status} - Unexpected response")
                    return False

    except Exception as e:
        logger.error(f"❌ API request error: {e}", exc_info=True)
        return False

    return False


if __name__ == "__main__":
    result = asyncio.run(test_bitunix_auth())

    logger.info("\n" + "=" * 80)
    logger.info("FINAL RESULT")
    logger.info("=" * 80)

    if result:
        logger.info("✅ All tests passed - Authentication working!")
        sys.exit(0)
    else:
        logger.error("❌ Authentication failed - See errors above")
        sys.exit(1)
