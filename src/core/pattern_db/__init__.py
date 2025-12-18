"""Pattern Database for Trading Pattern Recognition.

Uses Qdrant vector database to store and retrieve trading patterns
for similarity-based signal validation.

Docker Setup:
    Qdrant must be running on localhost:6333
    docker run -p 6333:6333 -v /d/docker/qdrant/07_OrderPilot-AI:/qdrant/storage qdrant/qdrant

Build Database:
    python -m src.core.pattern_db.build_database --stocks --crypto --days 365

Usage in Bot:
    from src.core.pattern_db import get_pattern_service

    service = await get_pattern_service()
    boost, recommendation = await service.get_quick_validation(bars, symbol, "1Min", "long")
"""

from .fetcher import PatternDataFetcher
from .extractor import PatternExtractor, Pattern
from .embedder import PatternEmbedder
from .qdrant_client import TradingPatternDB, PatternMatch
from .pattern_service import PatternService, PatternAnalysis, get_pattern_service

__all__ = [
    "PatternDataFetcher",
    "PatternExtractor",
    "Pattern",
    "PatternEmbedder",
    "TradingPatternDB",
    "PatternMatch",
    "PatternService",
    "PatternAnalysis",
    "get_pattern_service",
]
