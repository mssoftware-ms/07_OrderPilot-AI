"""Chat History Storage for Chart Analysis Chatbot.

Persists chat history per chart window (symbol + timeframe combination).
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from .models import ChatMessage, MessageRole

logger = logging.getLogger(__name__)

# Default storage directory
DEFAULT_STORAGE_DIR = Path.home() / ".orderpilot" / "chat_history"


class HistoryStore:
    """Manages chat history persistence per chart window.

    History is stored as JSON files with the naming convention:
    {symbol}_{timeframe}.json (e.g., BTC_USD_1H.json)
    """

    def __init__(self, storage_dir: Path | None = None, max_messages: int = 50):
        """Initialize history store.

        Args:
            storage_dir: Directory for history files (default: ~/.orderpilot/chat_history)
            max_messages: Maximum messages to keep per chart (FIFO)
        """
        self.storage_dir = storage_dir or DEFAULT_STORAGE_DIR
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.max_messages = max_messages

    def _make_key(self, symbol: str, timeframe: str) -> str:
        """Create a safe filename key from symbol and timeframe.

        Args:
            symbol: Trading symbol (e.g., "BTC/USD")
            timeframe: Chart timeframe (e.g., "1H")

        Returns:
            Safe filename without extension (e.g., "BTC_USD_1H")
        """
        # Replace unsafe characters
        safe_symbol = symbol.replace("/", "_").replace(":", "_").replace(" ", "_")
        safe_timeframe = timeframe.replace(" ", "_")
        return f"{safe_symbol}_{safe_timeframe}"

    def _get_file_path(self, symbol: str, timeframe: str) -> Path:
        """Get the file path for a chart's history.

        Args:
            symbol: Trading symbol
            timeframe: Chart timeframe

        Returns:
            Path to the JSON file
        """
        key = self._make_key(symbol, timeframe)
        return self.storage_dir / f"{key}.json"

    def save_history(
        self, symbol: str, timeframe: str, messages: list[ChatMessage]
    ) -> None:
        """Save chat history for a chart window.

        Args:
            symbol: Trading symbol
            timeframe: Chart timeframe
            messages: List of chat messages to save
        """
        if not messages:
            return

        # Apply FIFO limit
        messages_to_save = messages[-self.max_messages :]

        file_path = self._get_file_path(symbol, timeframe)

        try:
            data = {
                "symbol": symbol,
                "timeframe": timeframe,
                "updated_at": datetime.now().isoformat(),
                "messages": [self._message_to_dict(msg) for msg in messages_to_save],
            }

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.debug(
                "Saved %d messages for %s %s",
                len(messages_to_save), symbol, timeframe
            )

        except Exception as e:
            logger.error("Failed to save history for %s %s: %s", symbol, timeframe, e)

    def load_history(self, symbol: str, timeframe: str) -> list[ChatMessage]:
        """Load chat history for a chart window.

        Args:
            symbol: Trading symbol
            timeframe: Chart timeframe

        Returns:
            List of chat messages (empty if no history exists)
        """
        file_path = self._get_file_path(symbol, timeframe)

        if not file_path.exists():
            return []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            messages = [
                self._dict_to_message(msg_dict)
                for msg_dict in data.get("messages", [])
            ]

            logger.debug(
                "Loaded %d messages for %s %s",
                len(messages), symbol, timeframe
            )
            return messages

        except Exception as e:
            logger.error("Failed to load history for %s %s: %s", symbol, timeframe, e)
            return []

    def clear_history(self, symbol: str, timeframe: str) -> bool:
        """Clear chat history for a chart window.

        Args:
            symbol: Trading symbol
            timeframe: Chart timeframe

        Returns:
            True if deleted, False if not found
        """
        file_path = self._get_file_path(symbol, timeframe)

        if file_path.exists():
            try:
                file_path.unlink()
                logger.info("Cleared history for %s %s", symbol, timeframe)
                return True
            except Exception as e:
                logger.error("Failed to clear history: %s", e)
                return False

        return False

    def list_charts_with_history(self) -> list[tuple[str, str]]:
        """List all chart windows that have saved history.

        Returns:
            List of (symbol, timeframe) tuples
        """
        charts = []

        for file_path in self.storage_dir.glob("*.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                symbol = data.get("symbol", "")
                timeframe = data.get("timeframe", "")
                if symbol and timeframe:
                    charts.append((symbol, timeframe))
            except Exception:
                continue

        return charts

    def get_history_info(self, symbol: str, timeframe: str) -> dict[str, Any] | None:
        """Get metadata about stored history without loading all messages.

        Args:
            symbol: Trading symbol
            timeframe: Chart timeframe

        Returns:
            Dictionary with metadata or None if no history exists
        """
        file_path = self._get_file_path(symbol, timeframe)

        if not file_path.exists():
            return None

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            return {
                "symbol": data.get("symbol"),
                "timeframe": data.get("timeframe"),
                "updated_at": data.get("updated_at"),
                "message_count": len(data.get("messages", [])),
                "file_size_kb": file_path.stat().st_size / 1024,
            }
        except Exception:
            return None

    def _message_to_dict(self, message: ChatMessage) -> dict[str, Any]:
        """Convert ChatMessage to dictionary for JSON serialization."""
        return {
            "id": message.id,
            "role": message.role.value if isinstance(message.role, MessageRole)
                   else message.role,
            "content": message.content,
            "timestamp": message.timestamp.isoformat()
                        if isinstance(message.timestamp, datetime)
                        else message.timestamp,
            "metadata": message.metadata,
        }

    def _dict_to_message(self, data: dict[str, Any]) -> ChatMessage:
        """Convert dictionary to ChatMessage."""
        return ChatMessage(
            id=data.get("id", ""),
            role=MessageRole(data.get("role", "assistant")),
            content=data.get("content", ""),
            timestamp=datetime.fromisoformat(data["timestamp"])
                     if isinstance(data.get("timestamp"), str)
                     else datetime.now(),
            metadata=data.get("metadata", {}),
        )
