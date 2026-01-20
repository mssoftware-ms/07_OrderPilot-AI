"""Quick Pattern Database Builder - Für 5-Min Daytrading.

Baut Pattern-Datenbank mit QQQ + BTC/ETH für 30 Tage.
Optimiert für 5-Minuten-Timeframe.

Usage:
    python build_patterns_quick.py
"""

import asyncio
import logging
from datetime import datetime

from src.core.pattern_db.fetcher import PatternDataFetcher, FetchConfig
from src.core.pattern_db.extractor import PatternExtractor
from src.core.pattern_db.qdrant_client import TradingPatternDB
from src.core.market_data.types import Timeframe, AssetClass

# Database initialization
from src.config.loader import DatabaseConfig
from src.database import initialize_database

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)


async def build_quick_patterns():
    """Build pattern database optimized for 5-min daytrading."""

    print("=" * 60)
    print("🚀 OrderPilot Pattern Database - Quick Build")
    print("=" * 60)
    print("📊 Symbols: QQQ, BTC/USD, ETH/USD")
    print("⏱️  Timeframes: 1Min, 5Min, 15Min")
    print("📅 History: 30 Tage")
    print("=" * 60)
    print()

    # 1. Initialize Database FIRST (kritisch!)
    # WSL2-Fix: Verwende /tmp statt /mnt/d (Windows-Laufwerk)
    print("💾 Initialisiere SQLite-Datenbank...")
    import os
    temp_db_path = "/tmp/orderpilot_pattern_build.db"

    # Lösche alte temp DB falls vorhanden
    if os.path.exists(temp_db_path):
        os.remove(temp_db_path)
        print(f"  Alte temporäre DB gelöscht")

    try:
        # Create database config with WSL-native path
        db_config = DatabaseConfig(
            engine="sqlite",
            path=temp_db_path,
            pool_size=5,
            max_overflow=10,
            pool_timeout_seconds=30,
            auto_vacuum=True
        )
        db_manager = initialize_database(db_config)
        print(f"✓ Datenbank initialisiert ({temp_db_path})")
        print("  (WSL2-Workaround: Verwendet /tmp statt Windows-Laufwerk)\n")
    except Exception as e:
        print(f"❌ FEHLER bei Datenbank-Initialisierung: {e}")
        print("   Bitte Fehler in WSL melden!")
        return

    # 2. Initialize components
    fetcher = PatternDataFetcher()
    extractor = PatternExtractor(
        window_size=20,
        step_size=5,
        outcome_bars=5,
    )
    db = TradingPatternDB()

    # Initialize Qdrant
    print("🔌 Verbinde mit Qdrant (Port 6335)...")
    if not await db.initialize():
        print("❌ FEHLER: Qdrant nicht erreichbar!")
        print("   Starte Container: docker run -d -p 6335:6333 -v orderpilot_qdrant:/qdrant/storage --name orderpilot-qdrant qdrant/qdrant:latest")
        return

    print("✓ Qdrant verbunden\n")

    total_patterns = 0
    start_time = datetime.now()

    # === Skip Stocks (QQQ) - Alpaca Keys fehlen, Yahoo kein Intraday ===
    print("📈 Überspringe Stock-Daten (QQQ) - Alpaca-Keys nicht konfiguriert")
    print("   (Yahoo unterstützt nur Daily-Timeframes, kein 1Min/5Min/15Min)\n")

    # === Build Crypto (BTC, ETH) ===
    # Verwende Bitunix-Format (BTCUSDT) statt Alpaca-Format (BTC/USD)
    # da Alpaca-Keys nicht konfiguriert sind
    print("\n💰 Lade Crypto-Daten (BTCUSDT, ETHUSDT)...")
    crypto_symbols = ["BTCUSDT", "ETHUSDT"]

    crypto_config = FetchConfig(
        symbols=crypto_symbols,
        timeframes=[Timeframe.MINUTE_1, Timeframe.MINUTE_5, Timeframe.MINUTE_15],
        days_back=30,
        asset_class=AssetClass.CRYPTO,
    )

    def progress(symbol, tf, bars, done, total):
        print(f"  [{done}/{total}] {symbol} {tf.value}: {bars} Bars")

    async for symbol, timeframe, bars in fetcher.fetch_batch(crypto_config, progress):
        if not bars:
            continue

        patterns = list(extractor.extract_patterns(bars, symbol, timeframe.value))
        if patterns:
            inserted = await db.insert_patterns_batch(patterns, batch_size=500)
            total_patterns += inserted
            print(f"  ✓ {inserted} Patterns eingefügt für {symbol} {timeframe.value}")

    # === Summary ===
    elapsed = (datetime.now() - start_time).total_seconds()
    print("\n" + "=" * 60)
    print("✅ Build abgeschlossen!")
    print("=" * 60)
    print(f"📦 Gesamt Patterns: {total_patterns:,}")
    print(f"⏱️  Zeit: {elapsed:.1f}s ({total_patterns / elapsed:.1f} Patterns/sec)")

    # Final collection info
    info = await db.get_collection_info()
    if "error" not in info:
        print(f"📊 Collection '{info['name']}': {info['points_count']:,} Points")
        print(f"🟢 Status: {info['status']}")

    print("\n🎉 Datenbank bereit für Pattern-Analyse!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(build_quick_patterns())
