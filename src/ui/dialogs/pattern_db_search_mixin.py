from __future__ import annotations

import asyncio
import json
import logging
import subprocess
from datetime import datetime
from typing import Optional

from PyQt6.QtCore import Qt, QTimer, QSettings
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QPushButton,
    QTabWidget,
    QMessageBox,
    QListWidget,
    QListWidgetItem,
)

from .pattern_db_tabs_mixin import PatternDbTabsMixin
from .pattern_db_worker import DatabaseBuildWorker

logger = logging.getLogger(__name__)

QDRANT_CONTAINER_NAME = "09_rag-system-ai_cl-qdrant-1"
QDRANT_IMAGE = "qdrant/qdrant"
QDRANT_PORT = 6333
COLLECTION_NAME = "trading_patterns"


class PatternDbSearchMixin:
    """PatternDbSearchMixin extracted from PatternDatabaseDialog."""
    def _run_search_test(self):
        """Run a search test."""
        self.search_results.clear()
        self.search_results.append("Running search test...\n")

        try:
            from datetime import timedelta, timezone

            symbol = self.search_symbol.currentText()
            timeframe = self.search_timeframe.currentText()
            threshold = self.search_threshold.value() / 100

            async def run_search():
                from src.core.market_data.types import DataRequest, Timeframe, AssetClass
                from src.core.market_data.history_provider import HistoryManager
                from src.core.pattern_db import get_pattern_service
                from src.core.pattern_db.fetcher import resolve_symbol

                # Determine asset class
                is_crypto = "/" in symbol
                asset_class = AssetClass.CRYPTO if is_crypto else AssetClass.STOCK
                fetch_symbol = resolve_symbol(symbol, asset_class)

                # Fetch recent bars
                tf_map = {
                    "1Min": Timeframe.MINUTE_1,
                    "5Min": Timeframe.MINUTE_5,
                    "15Min": Timeframe.MINUTE_15,
                }

                hm = HistoryManager()
                end = datetime.now(timezone.utc)
                start = end - timedelta(hours=2)

                request = DataRequest(
                    symbol=fetch_symbol,
                    start_date=start,
                    end_date=end,
                    timeframe=tf_map.get(timeframe, Timeframe.MINUTE_1),
                    asset_class=asset_class,
                )

                bars, source = await hm.fetch_data(request)

                if len(bars) < 20:
                    return f"Not enough bars ({len(bars)}). Need at least 20."

                # Get pattern service
                service = await get_pattern_service()

                # Analyze
                analysis = await service.analyze_signal(
                    bars=bars,
                    symbol=symbol,
                    timeframe=timeframe,
                    signal_direction="long",
                )

                if not analysis:
                    return "Analysis failed - check if database has patterns"

                # Format results
                result = f"Symbol: {symbol} | Timeframe: {timeframe}\n"
                if fetch_symbol != symbol:
                    result += f"Data proxy used: {fetch_symbol}\n"
                result += f"Bars analyzed: {len(bars)}\n"
                result += "=" * 50 + "\n\n"
                result += f"Similar Patterns Found: {analysis.similar_patterns_count}\n"
                result += f"Win Rate: {analysis.win_rate:.1%}\n"
                result += f"Avg Return: {analysis.avg_return:.2f}%\n"
                result += f"Confidence: {analysis.confidence:.1%}\n"
                result += f"Signal Boost: {analysis.signal_boost:+.2f}\n"
                result += f"Recommendation: {analysis.recommendation.upper()}\n"
                result += f"Trend Consistency: {analysis.trend_consistency:.1%}\n"
                result += "\n" + "=" * 50 + "\n"
                result += "Top Matches:\n"

                for i, match in enumerate(analysis.best_matches[:5], 1):
                    result += f"\n{i}. {match.symbol} ({match.timeframe})\n"
                    result += f"   Score: {match.score:.3f}\n"
                    result += f"   Trend: {match.trend_direction} | Outcome: {match.outcome_label}\n"
                    result += f"   Return: {match.outcome_return_pct:+.2f}%\n"

                return result

            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            result = loop.run_until_complete(run_search())
            self.search_results.append(result)

        except Exception as e:
            self.search_results.append(f"Error: {e}")
            logger.error(f"Search test error: {e}", exc_info=True)
