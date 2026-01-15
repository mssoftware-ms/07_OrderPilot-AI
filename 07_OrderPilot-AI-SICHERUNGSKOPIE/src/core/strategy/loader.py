"""Strategy Loader for loading and managing strategy definitions.

Provides utilities to discover, load, and cache strategy definitions from YAML files.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional

import yaml

from .definition import StrategyDefinition

logger = logging.getLogger(__name__)


class StrategyLoader:
    """Loads and manages strategy definitions from YAML files."""

    def __init__(self, strategy_dirs: Optional[List[Path]] = None):
        """Initialize strategy loader.

        Args:
            strategy_dirs: List of directories to search for strategies.
                          Defaults to examples/strategies and config/strategies.
        """
        if strategy_dirs is None:
            # Default strategy directories
            base_path = Path(__file__).parent.parent.parent.parent
            strategy_dirs = [
                base_path / "examples" / "strategies",
                base_path / "config" / "strategies",
            ]

        self.strategy_dirs = [Path(d) for d in strategy_dirs]
        self._strategies: Dict[str, StrategyDefinition] = {}
        self._strategy_files: Dict[str, Path] = {}

    def discover_strategies(self) -> List[str]:
        """Discover all available strategy YAML files.

        Returns:
            List of strategy names
        """
        strategy_names = []

        for directory in self.strategy_dirs:
            if not directory.exists():
                logger.debug(f"Strategy directory does not exist: {directory}")
                continue

            for yaml_file in directory.glob("*.yaml"):
                try:
                    strategy_name = yaml_file.stem
                    strategy_names.append(strategy_name)
                    self._strategy_files[strategy_name] = yaml_file
                    logger.debug(f"Discovered strategy: {strategy_name} at {yaml_file}")
                except Exception as e:
                    logger.warning(f"Error discovering strategy {yaml_file}: {e}")

        logger.info(f"Discovered {len(strategy_names)} strategies")
        return sorted(strategy_names)

    def load_strategy(self, name: str) -> Optional[StrategyDefinition]:
        """Load a strategy by name.

        Args:
            name: Strategy name (filename without .yaml extension)

        Returns:
            StrategyDefinition if found, None otherwise
        """
        # Check cache first
        if name in self._strategies:
            logger.debug(f"Returning cached strategy: {name}")
            return self._strategies[name]

        # Find strategy file
        if name not in self._strategy_files:
            # Try to discover it
            self.discover_strategies()

        if name not in self._strategy_files:
            logger.error(f"Strategy not found: {name}")
            return None

        # Load from YAML
        yaml_file = self._strategy_files[name]
        try:
            with open(yaml_file, 'r', encoding='utf-8') as f:
                yaml_content = f.read()
                strategy = StrategyDefinition.from_yaml(yaml_content)

            # Cache it
            self._strategies[name] = strategy
            logger.info(f"✅ Loaded strategy: {name} ({strategy.name})")
            return strategy

        except Exception as e:
            logger.error(f"Failed to load strategy {name} from {yaml_file}: {e}", exc_info=True)
            return None

    def load_strategy_from_file(self, file_path: str | Path) -> Optional[StrategyDefinition]:
        """Load a strategy directly from a YAML file path.

        Args:
            file_path: Path to strategy YAML file

        Returns:
            StrategyDefinition if loaded, None otherwise
        """
        yaml_file = Path(file_path)
        if not yaml_file.exists():
            logger.error(f"Strategy file not found: {yaml_file}")
            return None

        try:
            with open(yaml_file, 'r', encoding='utf-8') as f:
                yaml_content = f.read()
                strategy = StrategyDefinition.from_yaml(yaml_content)

            strategy_name = yaml_file.stem
            self._strategies[strategy_name] = strategy
            self._strategy_files[strategy_name] = yaml_file
            logger.info(f"✅ Loaded strategy from file: {strategy_name} ({yaml_file})")
            return strategy

        except Exception as e:
            logger.error(f"Failed to load strategy from {yaml_file}: {e}", exc_info=True)
            return None

    def load_all_strategies(self) -> Dict[str, StrategyDefinition]:
        """Load all discovered strategies.

        Returns:
            Dictionary of strategy name -> StrategyDefinition
        """
        strategy_names = self.discover_strategies()

        for name in strategy_names:
            self.load_strategy(name)

        logger.info(f"Loaded {len(self._strategies)} strategies")
        return self._strategies.copy()

    def get_strategy_info(self, name: str) -> Optional[Dict]:
        """Get metadata about a strategy without fully loading it.

        Args:
            name: Strategy name

        Returns:
            Dictionary with strategy metadata (name, version, description, etc.)
        """
        if name not in self._strategy_files:
            self.discover_strategies()

        if name not in self._strategy_files:
            return None

        yaml_file = self._strategy_files[name]
        try:
            with open(yaml_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            return {
                "file_name": name,
                "name": data.get("name", name),
                "version": data.get("version", "unknown"),
                "description": data.get("description", "").strip(),
                "category": data.get("meta", {}).get("category", "Unknown"),
                "timeframe": data.get("meta", {}).get("timeframe", "Any"),
                "tags": data.get("meta", {}).get("tags", []),
                "file_path": str(yaml_file)
            }
        except Exception as e:
            logger.warning(f"Failed to get info for strategy {name}: {e}")
            return None


# Global strategy loader instance
_strategy_loader: Optional[StrategyLoader] = None


def get_strategy_loader() -> StrategyLoader:
    """Get the global strategy loader instance.

    Returns:
        StrategyLoader singleton
    """
    global _strategy_loader
    if _strategy_loader is None:
        _strategy_loader = StrategyLoader()
    return _strategy_loader
