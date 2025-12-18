"""Qdrant Client for Trading Pattern Database.

Connects to Qdrant running in Docker (localhost:6333).
Stores and retrieves trading patterns for similarity search.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import uuid4

import numpy as np

from .extractor import Pattern
from .embedder import PatternEmbedder

logger = logging.getLogger(__name__)

# Qdrant configuration for Docker
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
COLLECTION_NAME = "trading_patterns"


@dataclass
class PatternMatch:
    """A matched pattern from similarity search."""
    pattern_id: str
    score: float
    symbol: str
    timeframe: str
    start_time: str
    end_time: str
    price_change_pct: float
    trend_direction: str
    outcome_return_pct: float
    outcome_label: str
    metadata: dict


class TradingPatternDB:
    """Qdrant-based trading pattern database.

    Stores patterns as vectors for similarity search.
    Uses Docker Qdrant instance on localhost:6333.
    """

    def __init__(
        self,
        host: str = QDRANT_HOST,
        port: int = QDRANT_PORT,
        collection_name: str = COLLECTION_NAME,
        embedding_dim: int = 96,
    ):
        """Initialize Qdrant client.

        Args:
            host: Qdrant host (default: localhost for Docker)
            port: Qdrant port (default: 6333)
            collection_name: Name of the collection
            embedding_dim: Vector embedding dimension
        """
        self.host = host
        self.port = port
        self.collection_name = collection_name
        self.embedding_dim = embedding_dim
        self.embedder = PatternEmbedder(window_size=20)

        self._client = None
        self._initialized = False

    def _get_client(self):
        """Get or create Qdrant client."""
        if self._client is None:
            try:
                from qdrant_client import QdrantClient
                self._client = QdrantClient(host=self.host, port=self.port)
                logger.info(f"Connected to Qdrant at {self.host}:{self.port}")
            except ImportError:
                logger.error("qdrant-client not installed. Run: pip install qdrant-client")
                raise
            except Exception as e:
                logger.error(f"Failed to connect to Qdrant: {e}")
                raise
        return self._client

    async def initialize(self) -> bool:
        """Initialize the collection if it doesn't exist.

        Returns:
            True if successful
        """
        try:
            from qdrant_client.models import Distance, VectorParams, PayloadSchemaType

            client = self._get_client()

            # Check if collection exists
            collections = client.get_collections().collections
            exists = any(c.name == self.collection_name for c in collections)

            if not exists:
                logger.info(f"Creating collection '{self.collection_name}'...")
                client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.embedding_dim,
                        distance=Distance.COSINE,
                    ),
                )

                # Create payload indexes for filtering
                client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name="symbol",
                    field_schema=PayloadSchemaType.KEYWORD,
                )
                client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name="timeframe",
                    field_schema=PayloadSchemaType.KEYWORD,
                )
                client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name="trend_direction",
                    field_schema=PayloadSchemaType.KEYWORD,
                )
                client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name="outcome_label",
                    field_schema=PayloadSchemaType.KEYWORD,
                )

                logger.info(f"Collection '{self.collection_name}' created with indexes")
            else:
                logger.info(f"Collection '{self.collection_name}' already exists")

            self._initialized = True
            return True

        except Exception as e:
            logger.error(f"Failed to initialize collection: {e}")
            return False

    async def insert_pattern(self, pattern: Pattern) -> str:
        """Insert a single pattern into the database.

        Args:
            pattern: Pattern to insert

        Returns:
            Pattern ID
        """
        if not self._initialized:
            await self.initialize()

        try:
            from qdrant_client.models import PointStruct

            client = self._get_client()

            # Generate embedding
            embedding = self.embedder.embed(pattern)

            # Generate unique ID
            pattern_id = str(uuid4())

            # Create payload from pattern
            payload = pattern.to_dict()

            # Insert point
            client.upsert(
                collection_name=self.collection_name,
                points=[
                    PointStruct(
                        id=pattern_id,
                        vector=embedding.tolist(),
                        payload=payload,
                    )
                ],
            )

            return pattern_id

        except Exception as e:
            logger.error(f"Failed to insert pattern: {e}")
            raise

    async def insert_patterns_batch(
        self,
        patterns: list[Pattern],
        batch_size: int = 100,
        progress_callback: callable = None,
    ) -> int:
        """Insert multiple patterns in batches.

        Args:
            patterns: List of patterns to insert
            batch_size: Number of patterns per batch
            progress_callback: Optional callback(inserted, total)

        Returns:
            Number of patterns inserted
        """
        if not self._initialized:
            await self.initialize()

        try:
            from qdrant_client.models import PointStruct

            client = self._get_client()
            total_inserted = 0

            for i in range(0, len(patterns), batch_size):
                batch = patterns[i:i + batch_size]

                points = []
                for pattern in batch:
                    embedding = self.embedder.embed(pattern)
                    pattern_id = str(uuid4())
                    payload = pattern.to_dict()

                    points.append(
                        PointStruct(
                            id=pattern_id,
                            vector=embedding.tolist(),
                            payload=payload,
                        )
                    )

                # Upsert batch
                client.upsert(
                    collection_name=self.collection_name,
                    points=points,
                )

                total_inserted += len(points)

                if progress_callback:
                    progress_callback(total_inserted, len(patterns))

                logger.debug(f"Inserted batch: {total_inserted}/{len(patterns)}")

            logger.info(f"Inserted {total_inserted} patterns into Qdrant")
            return total_inserted

        except Exception as e:
            logger.error(f"Failed to insert pattern batch: {e}")
            raise

    async def search_similar(
        self,
        pattern: Pattern,
        limit: int = 10,
        symbol_filter: str = None,
        timeframe_filter: str = None,
        trend_filter: str = None,
        outcome_filter: str = None,
        score_threshold: float = 0.7,
    ) -> list[PatternMatch]:
        """Search for similar patterns.

        Args:
            pattern: Query pattern
            limit: Max results to return
            symbol_filter: Filter by symbol (optional)
            timeframe_filter: Filter by timeframe (optional)
            trend_filter: Filter by trend direction (optional)
            outcome_filter: Filter by outcome label (optional)
            score_threshold: Minimum similarity score

        Returns:
            List of matched patterns
        """
        if not self._initialized:
            await self.initialize()

        try:
            from qdrant_client.models import Filter, FieldCondition, MatchValue

            client = self._get_client()

            # Generate query embedding
            query_embedding = self.embedder.embed(pattern)

            # Build filter conditions
            must_conditions = []
            if symbol_filter:
                must_conditions.append(
                    FieldCondition(key="symbol", match=MatchValue(value=symbol_filter))
                )
            if timeframe_filter:
                must_conditions.append(
                    FieldCondition(key="timeframe", match=MatchValue(value=timeframe_filter))
                )
            if trend_filter:
                must_conditions.append(
                    FieldCondition(key="trend_direction", match=MatchValue(value=trend_filter))
                )
            if outcome_filter:
                must_conditions.append(
                    FieldCondition(key="outcome_label", match=MatchValue(value=outcome_filter))
                )

            query_filter = Filter(must=must_conditions) if must_conditions else None

            # Search
            results = client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding.tolist(),
                limit=limit,
                query_filter=query_filter,
                score_threshold=score_threshold,
            )

            # Convert to PatternMatch objects
            matches = []
            for result in results:
                payload = result.payload
                match = PatternMatch(
                    pattern_id=str(result.id),
                    score=result.score,
                    symbol=payload.get("symbol", ""),
                    timeframe=payload.get("timeframe", ""),
                    start_time=payload.get("start_time", ""),
                    end_time=payload.get("end_time", ""),
                    price_change_pct=payload.get("price_change_pct", 0),
                    trend_direction=payload.get("trend_direction", ""),
                    outcome_return_pct=payload.get("outcome_return_pct", 0),
                    outcome_label=payload.get("outcome_label", ""),
                    metadata=payload,
                )
                matches.append(match)

            logger.info(f"Found {len(matches)} similar patterns (threshold={score_threshold})")
            return matches

        except Exception as e:
            logger.error(f"Failed to search patterns: {e}")
            return []

    async def get_pattern_statistics(
        self,
        matches: list[PatternMatch],
    ) -> dict:
        """Calculate statistics from matched patterns.

        Args:
            matches: List of pattern matches

        Returns:
            Statistics dict with win rate, avg return, etc.
        """
        if not matches:
            return {
                "count": 0,
                "win_rate": 0,
                "avg_return": 0,
                "avg_score": 0,
            }

        wins = sum(1 for m in matches if m.outcome_label == "win")
        losses = sum(1 for m in matches if m.outcome_label == "loss")
        total_with_outcome = wins + losses

        returns = [m.outcome_return_pct for m in matches if m.outcome_return_pct != 0]
        scores = [m.score for m in matches]

        return {
            "count": len(matches),
            "wins": wins,
            "losses": losses,
            "neutral": len(matches) - total_with_outcome,
            "win_rate": wins / total_with_outcome if total_with_outcome > 0 else 0,
            "avg_return": np.mean(returns) if returns else 0,
            "median_return": np.median(returns) if returns else 0,
            "std_return": np.std(returns) if returns else 0,
            "avg_score": np.mean(scores) if scores else 0,
            "min_score": min(scores) if scores else 0,
            "max_score": max(scores) if scores else 0,
        }

    async def get_collection_info(self) -> dict:
        """Get information about the collection.

        Returns:
            Collection info dict
        """
        try:
            client = self._get_client()
            info = client.get_collection(self.collection_name)
            return {
                "name": self.collection_name,
                "vectors_count": info.vectors_count,
                "points_count": info.points_count,
                "status": info.status.value,
            }
        except Exception as e:
            logger.error(f"Failed to get collection info: {e}")
            return {"error": str(e)}

    async def delete_collection(self) -> bool:
        """Delete the entire collection.

        Returns:
            True if successful
        """
        try:
            client = self._get_client()
            client.delete_collection(self.collection_name)
            self._initialized = False
            logger.info(f"Deleted collection '{self.collection_name}'")
            return True
        except Exception as e:
            logger.error(f"Failed to delete collection: {e}")
            return False
