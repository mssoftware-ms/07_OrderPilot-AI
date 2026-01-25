"""Regime Results Manager - Stufe 1 Ergebnisse verwalten.

Verwaltet Regime-Optimierungs-Ergebnisse (Stufe 1):
- Sortierung & Ranking nach Composite Score
- Export regime_optimization_results.json
- Export optimized_regime.json
- JSON Schema Validation
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from src.core.tradingbot.config.validator import SchemaValidator, ValidationError

logger = logging.getLogger(__name__)


class RegimeResult:
    """Single regime optimization result."""

    def __init__(
        self,
        score: float,
        params: dict[str, Any],
        metrics: dict[str, Any],
        timestamp: str | None = None,
        rank: int | None = None,
        selected: bool = False,
        exported: bool = False,
    ):
        """Initialize regime result.

        Args:
            score: Composite score (0-100)
            params: Regime parameters (adx_period, adx_threshold, etc.)
            metrics: Performance metrics (regime_count, f1_scores, etc.)
            timestamp: ISO timestamp of result
            rank: Result rank (1st, 2nd, 3rd, etc.)
            selected: Whether this result is selected
            exported: Whether this result has been exported
        """
        self.score = score
        self.params = params
        self.metrics = metrics
        self.timestamp = timestamp or datetime.utcnow().isoformat() + "Z"
        self.rank = rank
        self.selected = selected
        self.exported = exported

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary format matching schema."""
        result = {
            "score": self.score,
            "params": self.params,
            "metrics": self.metrics,
            "timestamp": self.timestamp,
            "selected": self.selected,
            "exported": self.exported,
        }

        if self.rank is not None:
            result["rank"] = self.rank

        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RegimeResult:
        """Create from dictionary."""
        return cls(
            score=data["score"],
            params=data["params"],
            metrics=data["metrics"],
            timestamp=data.get("timestamp"),
            rank=data.get("rank"),
            selected=data.get("selected", False),
            exported=data.get("exported", False),
        )


class RegimeResultsManager:
    """Manages regime optimization results (Stufe 1).

    Features:
    - Sort and rank results by composite score
    - Export regime_optimization_results.json
    - Export optimized_regime.json (selected configuration)
    - JSON Schema validation with SchemaValidator

    Example:
        manager = RegimeResultsManager()

        # Add results
        manager.add_result(score=78.5, params={...}, metrics={...})
        manager.add_result(score=65.2, params={...}, metrics={...})

        # Rank and export
        manager.rank_results()
        manager.export_optimization_results("results.json")

        # Export selected config
        manager.select_result(rank=1)
        manager.export_optimized_regime("optimized.json", ...)
    """

    def __init__(self, schemas_dir: Path | None = None):
        """Initialize results manager.

        Args:
            schemas_dir: Directory containing JSON schemas.
                        Defaults to project's config/schemas/ or
                        01_Projectplan/.../schemas/
        """
        self.results: list[RegimeResult] = []
        self._selected_rank: int | None = None

        # Initialize validator
        if schemas_dir is None:
            # Try project schemas first
            project_root = Path(__file__).parents[2]
            schemas_dir = (
                project_root
                / "01_Projectplan"
                / "260124 New Regime and Indicator Analyzer"
                / "schemas"
            )

            # Fallback to config/schemas if project schemas not found
            if not schemas_dir.exists():
                schemas_dir = project_root / "config" / "schemas"

        self.schemas_dir = schemas_dir
        self.validator = SchemaValidator(schemas_dir=schemas_dir)

        logger.info(f"RegimeResultsManager initialized with schemas_dir: {self.schemas_dir}")

    def add_result(
        self,
        score: float,
        params: dict[str, Any],
        metrics: dict[str, Any],
        timestamp: str | None = None,
    ) -> RegimeResult:
        """Add optimization result.

        Args:
            score: Composite score (0-100)
            params: Regime parameters
            metrics: Performance metrics
            timestamp: Optional ISO timestamp

        Returns:
            Created RegimeResult
        """
        result = RegimeResult(
            score=score,
            params=params,
            metrics=metrics,
            timestamp=timestamp,
        )

        self.results.append(result)
        logger.debug(f"Added result: score={score:.2f}, params={params}")

        return result

    def rank_results(self) -> None:
        """Sort results by score (descending) and assign ranks."""
        # Sort by score descending
        self.results.sort(key=lambda r: r.score, reverse=True)

        # Assign ranks
        for idx, result in enumerate(self.results, start=1):
            result.rank = idx

        logger.info(f"Ranked {len(self.results)} results")

        if self.results:
            logger.info(f"  Best: rank={self.results[0].rank}, score={self.results[0].score:.2f}")
            if len(self.results) > 1:
                logger.info(
                    f"  Worst: rank={self.results[-1].rank}, score={self.results[-1].score:.2f}"
                )

    def select_result(self, rank: int = 1) -> RegimeResult:
        """Select a result by rank.

        Args:
            rank: Rank to select (1-based)

        Returns:
            Selected result

        Raises:
            ValueError: If rank is invalid
        """
        if not self.results:
            raise ValueError("No results available to select")

        if rank < 1 or rank > len(self.results):
            raise ValueError(f"Invalid rank {rank}. Must be 1-{len(self.results)}")

        # Clear previous selection
        for result in self.results:
            result.selected = False

        # Select new result
        selected = self.results[rank - 1]
        selected.selected = True
        self._selected_rank = rank

        logger.info(f"Selected result: rank={rank}, score={selected.score:.2f}")

        return selected

    def get_selected_result(self) -> RegimeResult | None:
        """Get currently selected result."""
        for result in self.results:
            if result.selected:
                return result
        return None

    def export_optimization_results(
        self,
        output_path: str | Path,
        meta: dict[str, Any],
        optimization_config: dict[str, Any],
        param_ranges: dict[str, Any],
        validate: bool = True,
    ) -> Path:
        """Export all optimization results to JSON.

        Schema: regime_optimization_results.schema.json

        Args:
            output_path: Path to output JSON file
            meta: Metadata (stage, created_at, source, statistics, etc.)
            optimization_config: Optimization configuration (mode, method, etc.)
            param_ranges: Parameter ranges used
            validate: Whether to validate against schema (default: True)

        Returns:
            Path to exported file

        Raises:
            ValidationError: If validation fails
        """
        output_path = Path(output_path)

        # Ensure results are ranked
        if not self.results or any(r.rank is None for r in self.results):
            self.rank_results()

        # Build JSON structure
        data = {
            "version": "2.0",
            "meta": meta,
            "optimization_config": optimization_config,
            "param_ranges": param_ranges,
            "results": [result.to_dict() for result in self.results],
        }

        # Validate if requested
        if validate:
            try:
                self.validator.validate_data(data, "regime_optimization_results")
                logger.info("✅ Schema validation passed: regime_optimization_results")
            except ValidationError as e:
                logger.error(f"❌ Schema validation failed: {e}")
                raise

        # Write to file
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info(f"✅ Exported optimization results: {output_path}")
        logger.info(f"   Total results: {len(self.results)}")

        return output_path

    def export_optimized_regime(
        self,
        output_path: str | Path,
        symbol: str,
        timeframe: str,
        bars: int,
        data_range: dict[str, str],
        regime_periods: list[dict[str, Any]],
        validate: bool = True,
    ) -> Path:
        """Export selected regime configuration.

        Schema: optimized_regime_config.schema.json

        Args:
            output_path: Path to output JSON file
            symbol: Trading symbol (e.g., "BTCUSDT")
            timeframe: Timeframe (e.g., "5m")
            bars: Number of bars analyzed
            data_range: Data range (start, end timestamps)
            regime_periods: Regime periods with bar indices
            validate: Whether to validate against schema (default: True)

        Returns:
            Path to exported file

        Raises:
            ValueError: If no result is selected
            ValidationError: If validation fails
        """
        output_path = Path(output_path)

        # Get selected result
        selected = self.get_selected_result()
        if not selected:
            raise ValueError("No result selected. Call select_result() first.")

        # Extract parameters
        params = selected.params

        # Build indicators
        indicators = self._build_indicators(params)

        # Build regimes
        regimes = self._build_regimes(params, selected.metrics)

        # Build metadata
        meta = {
            "stage": "regime_config",
            "created_at": datetime.utcnow().isoformat() + "Z",
            "name": f"{symbol}_{timeframe}_Regime_Config",
            "optimization_score": selected.score,
            "selected_rank": selected.rank,
            "source_file": None,  # Can be set externally
            "source": {
                "symbol": symbol,
                "timeframe": timeframe,
                "bars": bars,
                "data_range": data_range,
            },
            "metrics": {
                "f1_bull": selected.metrics.get("f1_bull", 0.0),
                "f1_bear": selected.metrics.get("f1_bear", 0.0),
                "f1_sideways": selected.metrics.get("f1_sideways", 0.0),
                "stability_score": selected.metrics.get("stability_score", 0.0),
                "bull_bars": selected.metrics.get("bull_bars", 0),
                "bear_bars": selected.metrics.get("bear_bars", 0),
                "sideways_bars": selected.metrics.get("sideways_bars", 0),
            },
            "optimized_params": params,
            "classification_logic": {
                "bull": "ADX > trending_threshold AND DI+ > DI- AND (DI+ - DI-) > di_diff_threshold",
                "bear": "ADX > trending_threshold AND DI- > DI+ AND (DI- - DI+) > di_diff_threshold",
                "sideways": "ADX < weak_threshold (low directional strength)",
            },
        }

        # Calculate percentages if we have bar counts
        total_bars = (
            selected.metrics.get("bull_bars", 0)
            + selected.metrics.get("bear_bars", 0)
            + selected.metrics.get("sideways_bars", 0)
        )

        if total_bars > 0:
            meta["metrics"]["bull_percentage"] = round(
                selected.metrics.get("bull_bars", 0) / total_bars * 100, 1
            )
            meta["metrics"]["bear_percentage"] = round(
                selected.metrics.get("bear_bars", 0) / total_bars * 100, 1
            )
            meta["metrics"]["sideways_percentage"] = round(
                selected.metrics.get("sideways_bars", 0) / total_bars * 100, 1
            )

        # Build JSON structure
        data = {
            "version": "2.0",
            "meta": meta,
            "indicators": indicators,
            "regimes": regimes,
            "regime_periods": regime_periods,
        }

        # Validate if requested
        if validate:
            try:
                self.validator.validate_data(data, "optimized_regime_config")
                logger.info("✅ Schema validation passed: optimized_regime_config")
            except ValidationError as e:
                logger.error(f"❌ Schema validation failed: {e}")
                raise

        # Write to file
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info(f"✅ Exported optimized regime config: {output_path}")
        logger.info(f"   Score: {selected.score:.2f}, Rank: {selected.rank}")

        # Mark as exported
        selected.exported = True

        return output_path

    def _build_indicators(self, params: dict[str, Any]) -> list[dict[str, Any]]:
        """Build indicators list from parameters (ADX/DI-based).

        Args:
            params: Optimized parameters (ADX/DI-based)

        Returns:
            List of indicator definitions
        """
        indicators = []

        # ADX (includes DI+/DI- internally)
        indicators.append(
            {
                "type": "Indicator",
                "id": f"adx{params['adx_period']}",
                "name": "ADX",
                "purpose": "trend_strength",
                "params": {
                    "period": params["adx_period"],
                    "di_diff_threshold": params.get("di_diff_threshold", 5.0),
                },
            }
        )

        # RSI
        indicators.append(
            {
                "type": "Indicator",
                "id": f"rsi{params['rsi_period']}",
                "name": "RSI",
                "purpose": "momentum_filter",
                "params": {
                    "period": params["rsi_period"],
                    "strong_bull": params.get("rsi_strong_bull", 55.0),
                    "strong_bear": params.get("rsi_strong_bear", 45.0),
                },
            }
        )

        # ATR (for move detection)
        indicators.append(
            {
                "type": "Indicator",
                "id": f"atr{params['atr_period']}",
                "name": "ATR",
                "purpose": "volatility_move_detection",
                "params": {
                    "period": params["atr_period"],
                    "strong_move_pct": params.get("strong_move_pct", 1.5),
                    "extreme_move_pct": params.get("extreme_move_pct", 3.0),
                },
            }
        )

        return indicators

    def _build_regimes(
        self,
        params: dict[str, Any],
        metrics: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Build regimes list from parameters and metrics (ADX/DI-based).

        Args:
            params: Optimized parameters (ADX/DI-based)
            metrics: Performance metrics

        Returns:
            List of regime definitions
        """
        adx_id = f"adx{params['adx_period']}"
        rsi_id = f"rsi{params['rsi_period']}"
        atr_id = f"atr{params['atr_period']}"

        # Get thresholds with defaults
        adx_trending = params.get("adx_trending_threshold", 25.0)
        adx_weak = params.get("adx_weak_threshold", 20.0)
        di_diff = params.get("di_diff_threshold", 5.0)

        regimes = []

        # BULL Regime (ADX > trending AND DI+ > DI- AND diff > threshold)
        regimes.append(
            {
                "type": "Regime",
                "id": "bull",
                "name": "BULL",
                "priority": 90,
                "color": "#26a69a",
                "bar_count": metrics.get("bull_bars", 0),
                "conditions": {
                    "all": [
                        {
                            "left": {"indicator_id": adx_id, "field": "value"},
                            "op": "gt",
                            "right": {"value": adx_trending},
                        },
                        {
                            "left": {"indicator_id": adx_id, "field": "plus_di"},
                            "op": "gt",
                            "right": {"indicator_id": adx_id, "field": "minus_di"},
                        },
                        {
                            "left": {"indicator_id": adx_id, "field": "di_diff"},
                            "op": "gt",
                            "right": {"value": di_diff},
                        },
                    ]
                },
            }
        )

        # BEAR Regime (ADX > trending AND DI- > DI+ AND diff > threshold)
        regimes.append(
            {
                "type": "Regime",
                "id": "bear",
                "name": "BEAR",
                "priority": 90,
                "color": "#ef5350",
                "bar_count": metrics.get("bear_bars", 0),
                "conditions": {
                    "all": [
                        {
                            "left": {"indicator_id": adx_id, "field": "value"},
                            "op": "gt",
                            "right": {"value": adx_trending},
                        },
                        {
                            "left": {"indicator_id": adx_id, "field": "minus_di"},
                            "op": "gt",
                            "right": {"indicator_id": adx_id, "field": "plus_di"},
                        },
                        {
                            "left": {"indicator_id": adx_id, "field": "di_diff"},
                            "op": "gt",
                            "right": {"value": di_diff},
                        },
                    ]
                },
            }
        )

        # SIDEWAYS Regime (ADX < weak threshold - low directional strength)
        regimes.append(
            {
                "type": "Regime",
                "id": "sideways",
                "name": "SIDEWAYS",
                "priority": 80,
                "color": "#ffa726",
                "bar_count": metrics.get("sideways_bars", 0),
                "conditions": {
                    "all": [
                        {
                            "left": {"indicator_id": adx_id, "field": "value"},
                            "op": "lt",
                            "right": {"value": adx_weak},
                        },
                    ]
                },
            }
        )

        return regimes

    def load_optimization_results(
        self,
        input_path: str | Path,
        validate: bool = True,
    ) -> dict[str, Any]:
        """Load optimization results from JSON file.

        Args:
            input_path: Path to JSON file
            validate: Whether to validate against schema (default: True)

        Returns:
            Loaded data

        Raises:
            ValidationError: If validation fails
        """
        input_path = Path(input_path)

        # Validate and load
        if validate:
            data = self.validator.validate_file(input_path, "regime_optimization_results")
        else:
            with open(input_path, "r", encoding="utf-8") as f:
                data = json.load(f)

        # Clear existing results
        self.results.clear()

        # Load results
        for result_data in data.get("results", []):
            result = RegimeResult.from_dict(result_data)
            self.results.append(result)

        logger.info(f"✅ Loaded {len(self.results)} results from {input_path}")

        return data

    def get_statistics(self) -> dict[str, Any]:
        """Get statistics about current results.

        Returns:
            Statistics dictionary
        """
        if not self.results:
            return {
                "count": 0,
                "score_min": 0.0,
                "score_max": 0.0,
                "score_avg": 0.0,
                "score_median": 0.0,
            }

        scores = [r.score for r in self.results]
        scores_sorted = sorted(scores)

        return {
            "count": len(self.results),
            "score_min": min(scores),
            "score_max": max(scores),
            "score_avg": sum(scores) / len(scores),
            "score_median": scores_sorted[len(scores_sorted) // 2],
        }

    def clear(self) -> None:
        """Clear all results."""
        self.results.clear()
        self._selected_rank = None
        logger.info("Cleared all results")
