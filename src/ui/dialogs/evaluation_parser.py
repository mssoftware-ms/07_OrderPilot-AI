"""Parser for Evaluation Entries.

Parses evaluation entries from text content or list format.
Supports format: [#Label; value; info; color]
"""

from __future__ import annotations

import re
import logging
from typing import Optional

from .evaluation_models import EvaluationEntry

logger = logging.getLogger(__name__)


class EvaluationParser:
    """Parse evaluation entries from text or list."""

    # Pattern for variable lines: [#Label; value; info; color]
    VAR_PATTERN = re.compile(r"^\[#(.+?)\]$")

    # Pattern for numeric values or ranges (e.g., "100" or "100-200")
    NUMERIC_PATTERN = re.compile(r"^-?\d+(?:\.\d+)?(?:-?-?\d+(?:\.\d+)?)?$")

    @classmethod
    def parse_from_content(cls, content: str) -> tuple[list[EvaluationEntry], list[str]]:
        """Parse entries from text content.

        Args:
            content: Text content with lines like "[#Label; value; info; color]"

        Returns:
            Tuple of (valid_entries, invalid_lines)
            - valid_entries: List of successfully parsed EvaluationEntry objects
            - invalid_lines: List of lines that couldn't be parsed
        """
        entries = []
        invalid = []

        for line in content.splitlines():
            stripped = line.strip()

            # Skip lines that don't match the pattern
            if not stripped.startswith("[#") or not stripped.endswith("]"):
                continue

            entry = cls._parse_line(stripped)
            if entry:
                entries.append(entry)
            else:
                invalid.append(stripped)

        logger.debug(f"Parsed {len(entries)} entries, {len(invalid)} invalid lines")
        return entries, invalid

    @classmethod
    def parse_from_list(cls, entries_list: list) -> list[EvaluationEntry]:
        """Parse entries from list of tuples.

        Args:
            entries_list: List of tuples in format (label, value, info?, color?)

        Returns:
            List of EvaluationEntry objects
        """
        entries = []
        for e in entries_list:
            try:
                entry = EvaluationEntry.from_tuple(e)
                entries.append(entry)
            except (ValueError, IndexError) as ex:
                logger.warning(f"Failed to parse entry from tuple: {e}, error: {ex}")
                continue

        logger.debug(f"Parsed {len(entries)} entries from list")
        return entries

    @classmethod
    def _parse_line(cls, line: str) -> Optional[EvaluationEntry]:
        """Parse a single line like '[#Label; value; info; color]'.

        Args:
            line: Single line to parse

        Returns:
            EvaluationEntry or None if parsing failed
        """
        m = cls.VAR_PATTERN.match(line)
        if not m:
            return None

        inner = m.group(1)
        parts = [p.strip() for p in inner.split(";")]

        # Need at least label and value
        if len(parts) < 2:
            return None

        label = parts[0]
        value = parts[1]
        info = parts[2] if len(parts) > 2 else ""
        color = parts[3] if len(parts) > 3 else "#0d6efd55"

        # Validate numeric pattern
        if not cls.NUMERIC_PATTERN.match(value):
            logger.debug(f"Value '{value}' does not match numeric pattern")
            return None

        return EvaluationEntry(label, value, info, color)

    @classmethod
    def validate_value(cls, value: str) -> bool:
        """Validate if value matches expected numeric pattern.

        Args:
            value: Value string to validate

        Returns:
            True if valid, False otherwise
        """
        return bool(cls.NUMERIC_PATTERN.match(value))
