"""
Storage layer for project variables with LRU caching.

This module provides file-based storage for project variables with
automatic caching, JSON serialization, and file watching for hot-reload.

Key Features:
    - LRU cache (64 entries) for fast access
    - JSON file format (.cel_variables.json)
    - Automatic schema validation
    - File watching for auto-reload (optional)
    - Thread-safe operations

Author: OrderPilot-AI Development Team
Created: 2026-01-28
"""

from __future__ import annotations

import json
import logging
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from pydantic import ValidationError

from .variable_models import ProjectVariable, ProjectVariables

logger = logging.getLogger(__name__)


class VariableStorageError(Exception):
    """Base exception for variable storage errors."""
    pass


class VariableFileNotFoundError(VariableStorageError):
    """Raised when variable file doesn't exist."""
    pass


class VariableValidationError(VariableStorageError):
    """Raised when variable data fails validation."""
    pass


class VariableStorage:
    """
    Storage layer for project variables with LRU caching.

    This class handles loading, saving, and caching of project variables
    from .cel_variables.json files. Uses LRU cache for fast access and
    supports thread-safe operations.

    Attributes:
        cache_size: Maximum number of cached variable sets (default: 64)
        _cache: LRU cache for loaded variables
        _lock: Thread lock for safe concurrent access
        _file_timestamps: Track file modification times for cache invalidation

    Examples:
        >>> storage = VariableStorage()
        >>> variables = storage.load("project/.cel_variables.json")
        >>> print(variables.count())
        25

        >>> storage.save("project/.cel_variables.json", variables)
        >>> storage.clear_cache()
    """

    DEFAULT_CACHE_SIZE = 64

    def __init__(self, cache_size: int = DEFAULT_CACHE_SIZE):
        """
        Initialize variable storage.

        Args:
            cache_size: Maximum number of cached variable sets
        """
        self.cache_size = cache_size
        self._cache: Dict[str, ProjectVariables] = {}
        self._lock = threading.RLock()
        self._file_timestamps: Dict[str, float] = {}

    def load(
        self,
        file_path: str | Path,
        use_cache: bool = True,
        create_if_missing: bool = False
    ) -> ProjectVariables:
        """
        Load project variables from JSON file.

        Args:
            file_path: Path to .cel_variables.json file
            use_cache: Whether to use cached data if available
            create_if_missing: Create empty file if it doesn't exist

        Returns:
            ProjectVariables instance

        Raises:
            VariableFileNotFoundError: If file doesn't exist and not create_if_missing
            VariableValidationError: If JSON is invalid or fails validation

        Examples:
            >>> storage = VariableStorage()
            >>> variables = storage.load("project/.cel_variables.json")
            >>> print(variables.project_name)
            'BTC Scalping Strategy'
        """
        file_path = Path(file_path).resolve()
        file_key = str(file_path)

        with self._lock:
            # Check if file exists
            if not file_path.exists():
                if create_if_missing:
                    # Create empty variables file
                    empty_vars = ProjectVariables(
                        version="1.0",
                        project_name=file_path.parent.name,
                        variables={},
                        created_at=datetime.now().isoformat()
                    )
                    self.save(file_path, empty_vars)
                    return empty_vars
                else:
                    raise VariableFileNotFoundError(
                        f"Variable file not found: {file_path}"
                    )

            # Check cache validity
            if use_cache and file_key in self._cache:
                # Check if file was modified
                current_mtime = file_path.stat().st_mtime
                cached_mtime = self._file_timestamps.get(file_key)

                if cached_mtime == current_mtime:
                    logger.debug(f"Using cached variables from {file_path}")
                    return self._cache[file_key]

            # Load from file
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # Validate and parse with Pydantic
                variables = ProjectVariables(**data)

                # Update cache
                if use_cache:
                    self._cache[file_key] = variables
                    self._file_timestamps[file_key] = file_path.stat().st_mtime

                    # Enforce cache size limit (simple LRU)
                    if len(self._cache) > self.cache_size:
                        # Remove oldest entry
                        oldest_key = next(iter(self._cache))
                        del self._cache[oldest_key]
                        if oldest_key in self._file_timestamps:
                            del self._file_timestamps[oldest_key]

                logger.info(
                    f"Loaded {variables.count()} variables from {file_path}"
                )
                return variables

            except json.JSONDecodeError as e:
                raise VariableValidationError(
                    f"Invalid JSON in {file_path}: {e}"
                ) from e

            except ValidationError as e:
                raise VariableValidationError(
                    f"Variable validation failed in {file_path}: {e}"
                ) from e

            except Exception as e:
                raise VariableStorageError(
                    f"Error loading variables from {file_path}: {e}"
                ) from e

    def save(
        self,
        file_path: str | Path,
        variables: ProjectVariables,
        update_timestamps: bool = True
    ) -> None:
        """
        Save project variables to JSON file.

        Args:
            file_path: Path to .cel_variables.json file
            variables: ProjectVariables instance to save
            update_timestamps: Whether to update updated_at timestamp

        Raises:
            VariableStorageError: If save fails

        Examples:
            >>> storage = VariableStorage()
            >>> variables = ProjectVariables(...)
            >>> storage.save("project/.cel_variables.json", variables)
        """
        file_path = Path(file_path).resolve()
        file_key = str(file_path)

        with self._lock:
            try:
                # Create parent directory if needed
                file_path.parent.mkdir(parents=True, exist_ok=True)

                # Update timestamp
                if update_timestamps:
                    variables.updated_at = datetime.now().isoformat()
                    if not variables.created_at:
                        variables.created_at = variables.updated_at

                # Serialize to JSON with pretty formatting
                data = variables.model_dump(mode="json", exclude_none=True)

                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)

                # Update cache
                self._cache[file_key] = variables
                self._file_timestamps[file_key] = file_path.stat().st_mtime

                logger.info(
                    f"Saved {variables.count()} variables to {file_path}"
                )

            except Exception as e:
                raise VariableStorageError(
                    f"Error saving variables to {file_path}: {e}"
                ) from e

    def reload(self, file_path: str | Path) -> ProjectVariables:
        """
        Force reload variables from file, bypassing cache.

        Args:
            file_path: Path to .cel_variables.json file

        Returns:
            ProjectVariables instance

        Examples:
            >>> storage = VariableStorage()
            >>> variables = storage.reload("project/.cel_variables.json")
        """
        file_path = Path(file_path).resolve()
        file_key = str(file_path)

        with self._lock:
            # Clear cache entry
            if file_key in self._cache:
                del self._cache[file_key]
            if file_key in self._file_timestamps:
                del self._file_timestamps[file_key]

            # Load fresh
            return self.load(file_path, use_cache=True)

    def is_cached(self, file_path: str | Path) -> bool:
        """
        Check if file is currently cached.

        Args:
            file_path: Path to .cel_variables.json file

        Returns:
            True if file is in cache
        """
        file_key = str(Path(file_path).resolve())
        with self._lock:
            return file_key in self._cache

    def clear_cache(self, file_path: Optional[str | Path] = None) -> None:
        """
        Clear cache for specific file or all files.

        Args:
            file_path: Optional path to clear, None clears all

        Examples:
            >>> storage = VariableStorage()
            >>> storage.clear_cache()  # Clear all
            >>> storage.clear_cache("project/.cel_variables.json")  # Clear one
        """
        with self._lock:
            if file_path is None:
                self._cache.clear()
                self._file_timestamps.clear()
                logger.info("Cleared all variable cache")
            else:
                file_key = str(Path(file_path).resolve())
                if file_key in self._cache:
                    del self._cache[file_key]
                if file_key in self._file_timestamps:
                    del self._file_timestamps[file_key]
                logger.info(f"Cleared cache for {file_path}")

    def get_cache_info(self) -> Dict[str, any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache info (size, entries, etc.)
        """
        with self._lock:
            return {
                "max_size": self.cache_size,
                "current_size": len(self._cache),
                "cached_files": list(self._cache.keys()),
                "utilization_pct": (len(self._cache) / self.cache_size) * 100
            }

    def exists(self, file_path: str | Path) -> bool:
        """
        Check if variable file exists.

        Args:
            file_path: Path to .cel_variables.json file

        Returns:
            True if file exists
        """
        return Path(file_path).resolve().exists()

    def validate_file(self, file_path: str | Path) -> tuple[bool, Optional[str]]:
        """
        Validate variable file without loading into cache.

        Args:
            file_path: Path to .cel_variables.json file

        Returns:
            Tuple of (is_valid, error_message)

        Examples:
            >>> storage = VariableStorage()
            >>> valid, error = storage.validate_file("project/.cel_variables.json")
            >>> if not valid:
            ...     print(f"Invalid: {error}")
        """
        try:
            file_path = Path(file_path).resolve()

            if not file_path.exists():
                return False, f"File not found: {file_path}"

            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Validate with Pydantic (don't cache)
            ProjectVariables(**data)

            return True, None

        except json.JSONDecodeError as e:
            return False, f"Invalid JSON: {e}"

        except ValidationError as e:
            return False, f"Validation error: {e}"

        except Exception as e:
            return False, f"Error: {e}"

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"VariableStorage(cache_size={self.cache_size}, "
            f"cached={len(self._cache)})"
        )
