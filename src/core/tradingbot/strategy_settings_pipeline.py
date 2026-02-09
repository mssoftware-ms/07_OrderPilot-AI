"""Unified Strategy Settings Pipeline.

Single Source of Truth for:
- Schema validation (kind-aware)
- Indicator calculation
- Regime detection
- Entry evaluation (fail-closed)
- Scoring + explainability
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import logging
import math

import numpy as np
import pandas as pd

from src.core.indicators.engine import IndicatorEngine
from src.core.indicators.types import IndicatorConfig, IndicatorType
from src.core.tradingbot.cel_engine_utils import get_cel_engine
from src.core.tradingbot.config.detector import ActiveRegime
from src.core.tradingbot.config.models import RegimeDefinition, RegimeScope, TradingBotConfig
from src.core.tradingbot.config.router import StrategyRouter, MatchedStrategySet
from src.core.tradingbot.config.kind_loader import KindConfigLoader
from src.core.tradingbot.json_entry_loader import JsonEntryConfig
from src.core.tradingbot.json_entry_scorer import JsonEntryScorer
from src.core.tradingbot.models import RegimeState, RegimeType

logger = logging.getLogger(__name__)

MIN_CANDLES = 50


@dataclass
class PipelineConfig:
    path: Path
    kind: str
    schema_version: str
    raw: dict[str, Any]
    strategy_config: TradingBotConfig | None = None
    indicators_def: list[dict[str, Any]] = field(default_factory=list)
    regimes_def: list[dict[str, Any]] = field(default_factory=list)
    entry_expression: str = ""
    entry_enabled: bool = False
    entry_errors: list[str] = field(default_factory=list)


@dataclass
class IndicatorComputationResult:
    values: dict[str, dict[str, float]]
    series: dict[str, Any]
    missing: list[str]
    nan: list[str]
    errors: list[str]
    candle_count: int


@dataclass
class RegimeEvaluation:
    regime_id: str
    name: str | None
    passed: bool
    details: list[dict[str, Any]]
    scope: str | None
    priority: int | None


@dataclass
class RegimeDetectionResult:
    active_regimes: list[RegimeEvaluation]
    selected_regime: RegimeEvaluation | None
    all_regimes: list[RegimeEvaluation]
    missing_indicators: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


@dataclass
class EntryEvaluationResult:
    enabled: bool
    expression: str
    result: bool
    long_result: bool
    short_result: bool
    reasons: list[str]
    errors: list[str]


@dataclass
class ScoreResult:
    total_score: int
    regime_match_score: int
    entry_signal_score: int
    data_quality_score: int
    explain: dict[str, Any]


@dataclass
class StrategySettingsRunResult:
    config: PipelineConfig
    indicators: IndicatorComputationResult
    regimes: RegimeDetectionResult
    entry: EntryEvaluationResult
    matched_sets: list[MatchedStrategySet]
    score: ScoreResult


class StrategySettingsPipeline:
    """Unified pipeline for Strategy Settings."""

    def __init__(self) -> None:
        self.loader = KindConfigLoader()
        self.indicator_engine = IndicatorEngine()

    def load_validate(self, json_path: str | Path) -> PipelineConfig:
        """Load and validate config file.

        Relies on KindConfigLoader for schema validation.
        """
        path = Path(json_path)
        data = self.loader.load(path)

        kind = data["kind"] # Schema guarantees existence
        schema_version = data.get("schema_version", "2.1.0")

        # Standardize Entry Expression
        entry_expression = data.get("entry_expression", "")
        entry_expression = str(entry_expression) if entry_expression else ""
        entry_enabled = bool(entry_expression.strip())
        entry_errors: list[str] = []
        if not entry_enabled:
            # Logic warning, not schema error
            entry_errors.append("ENTRY_EXPRESSION_MISSING")

        # Default values
        strategy_config = None
        indicators_def = []
        regimes_def = []

        if kind == "strategy_config":
            strategy_config = TradingBotConfig(**data)
            indicators_def = [i.model_dump() for i in strategy_config.indicators]
            regimes_def = [r.model_dump() for r in strategy_config.regimes]
            # Strategy config might have its own entry expression logic or use strategies[0].entry
            # But here we stick to the common pipeline field if present, or blank.

        elif kind == "indicator_set":
            indicators_def = data.get("indicators", [])
            regimes_def = data.get("regimes", [])
            # entry_enabled override from JSON if present
            if "entry_enabled" in data:
                entry_enabled = bool(data["entry_enabled"]) and entry_enabled

        elif kind == "regime_optimization_results":
            opt = self._select_optimization_result(data.get("optimization_results", []))
            indicators_def = opt.get("indicators", [])
            regimes_def = opt.get("regimes", [])

        else:
            # Should be caught by KindConfigLoader, but safe guard
            raise ValueError(f"Unsupported kind: {kind}")

        return PipelineConfig(
            path=path,
            kind=kind,
            schema_version=schema_version,
            raw=data,
            strategy_config=strategy_config,
            indicators_def=indicators_def,
            regimes_def=regimes_def,
            entry_expression=entry_expression,
            entry_enabled=entry_enabled,
            entry_errors=entry_errors,
        )

    def compute_indicators(self, candles: list[dict], config: PipelineConfig) -> IndicatorComputationResult:
        df, errors = self._candles_to_df(candles)
        if errors:
            return IndicatorComputationResult(
                values={},
                series={},
                missing=[],
                nan=[],
                errors=errors,
                candle_count=len(candles) if candles else 0,
            )

        indicator_values: dict[str, dict[str, float]] = {}
        indicator_series: dict[str, Any] = {}
        missing: list[str] = []
        nan: list[str] = []
        errors = []
        type_index: dict[str, str] = {}

        for ind in config.indicators_def:
            ind_id = ind.get("id") or ind.get("name")
            ind_type = ind.get("type")
            params_raw = ind.get("params")

            if not ind_id or not ind_type:
                missing.append(str(ind_id) if ind_id else "<missing-id>")
                errors.append(f"Indicator missing id/type: {ind}")
                continue

            type_index.setdefault(str(ind_type).upper(), str(ind_id))

            params = self._normalize_params(params_raw)
            try:
                ind_config = IndicatorConfig(
                    indicator_type=IndicatorType(str(ind_type).lower()),
                    params=params,
                    use_talib=False,
                    cache_results=True,
                )
                result = self.indicator_engine.calculate(df, ind_config)
                indicator_series[ind_id] = result.values
                value_map = self._extract_latest_values(result.values)
                indicator_values[ind_id] = value_map

                # Flag NaN values
                if any(self._is_nan(v) for v in value_map.values()):
                    nan.append(ind_id)

            except Exception as exc:
                logger.error("Indicator calc failed for %s: %s", ind_id, exc)
                missing.append(ind_id)
                indicator_values[ind_id] = {"value": float("nan")}
                indicator_series[ind_id] = pd.Series([np.nan] * len(df))

        if config.kind in ("indicator_set", "regime_optimization_results"):
            self._augment_threshold_series(df, indicator_values, indicator_series, nan)

        # attach type index for downstream threshold mapping
        indicator_values["__type_index__"] = {"value": float("nan")}
        indicator_series["__type_index__"] = type_index

        return IndicatorComputationResult(
            values=indicator_values,
            series=indicator_series,
            missing=missing,
            nan=nan,
            errors=errors,
            candle_count=len(df),
        )

    def detect_regime(
        self,
        indicators: IndicatorComputationResult,
        config: PipelineConfig,
        scope: str = "entry",
    ) -> RegimeDetectionResult:
        if config.kind == "strategy_config" and config.strategy_config:
            return self._detect_regime_conditions(indicators.values, config.strategy_config.regimes, scope)
        return self._detect_regime_thresholds(indicators, config.regimes_def, scope)

    def evaluate_entry(
        self,
        config: PipelineConfig,
        features: Any | None = None,
        chart_window: Any | None = None,
        prev_regime: str | None = None,
        selected_regime: str | None = None,
    ) -> EntryEvaluationResult:
        if not config.entry_enabled:
            return EntryEvaluationResult(
                enabled=False,
                expression=config.entry_expression,
                result=False,
                long_result=False,
                short_result=False,
                reasons=[],
                errors=list(config.entry_errors),
            )

        if features is None:
            return EntryEvaluationResult(
                enabled=True,
                expression=config.entry_expression,
                result=False,
                long_result=False,
                short_result=False,
                reasons=[],
                errors=["ENTRY_CONTEXT_MISSING"],
            )

        try:
            entry_cfg = JsonEntryConfig.from_data(
                regime_data=config.raw,
                regime_json_path=str(config.path),
                indicator_data=None,
                indicator_json_path=None,
                entry_expression_override=config.entry_expression,
            )
            entry_cfg.entry_enabled = config.entry_enabled
            entry_cfg.entry_errors = list(config.entry_errors)

            scorer = JsonEntryScorer(entry_cfg, get_cel_engine())
            regime_state = self._build_regime_state(selected_regime)

            long_ok, _, long_reasons = scorer.should_enter_long(
                features, regime_state, chart_window=chart_window, prev_regime=prev_regime
            )
            short_ok, _, short_reasons = scorer.should_enter_short(
                features, regime_state, chart_window=chart_window, prev_regime=prev_regime
            )

            return EntryEvaluationResult(
                enabled=True,
                expression=config.entry_expression,
                result=bool(long_ok or short_ok),
                long_result=bool(long_ok),
                short_result=bool(short_ok),
                reasons=list(dict.fromkeys(long_reasons + short_reasons)),
                errors=[],
            )
        except Exception as exc:
            logger.error("Entry evaluation failed: %s", exc, exc_info=True)
            return EntryEvaluationResult(
                enabled=True,
                expression=config.entry_expression,
                result=False,
                long_result=False,
                short_result=False,
                reasons=[],
                errors=[f"ENTRY_EVAL_ERROR: {exc}"],
            )

    def score(
        self,
        config: PipelineConfig,
        indicators: IndicatorComputationResult,
        regimes: RegimeDetectionResult,
        entry: EntryEvaluationResult,
        matched_sets: list[MatchedStrategySet] | None = None,
    ) -> ScoreResult:
        combined_missing = sorted(set(indicators.missing + regimes.missing_indicators))
        data_quality_score, penalties = self._data_quality_score(indicators, combined_missing)

        regime_match = False
        if config.kind == "strategy_config":
            regime_match = bool(matched_sets)
        else:
            regime_match = regimes.selected_regime is not None

        regime_match_score = 60 if regime_match else 0
        entry_signal_score = 30 if entry.result else 0
        total_score = max(0, min(100, regime_match_score + entry_signal_score + data_quality_score))

        explain = {
            "schema": {
                "kind": config.kind,
                "schema_version": config.schema_version,
                "valid": True,
            },
            "regime": {
                "matched": regime_match,
                "selected_regime": regimes.selected_regime.regime_id if regimes.selected_regime else None,
                "active_regimes": [r.regime_id for r in regimes.active_regimes],
                "evaluations": [r.__dict__ for r in regimes.all_regimes],
                "routing": {
                    "matched_sets": [s.id for s in matched_sets] if matched_sets else [],
                },
            },
            "entry": {
                "enabled": entry.enabled,
                "expression": entry.expression,
                "result": entry.result,
                "long": entry.long_result,
                "short": entry.short_result,
                "reasons": entry.reasons,
                "errors": entry.errors,
            },
            "data_quality": {
                "candle_count": indicators.candle_count,
                "missing_indicators": combined_missing,
                "nan_indicators": indicators.nan,
                "penalties": penalties,
            },
        }

        return ScoreResult(
            total_score=total_score,
            regime_match_score=regime_match_score,
            entry_signal_score=entry_signal_score,
            data_quality_score=data_quality_score,
            explain=explain,
        )

    def run(
        self,
        json_path: str | Path,
        candles: list[dict],
        features: Any | None = None,
        chart_window: Any | None = None,
        prev_regime: str | None = None,
    ) -> StrategySettingsRunResult:
        config = self.load_validate(json_path)
        indicators = self.compute_indicators(candles, config)
        regimes = self.detect_regime(indicators, config, scope="entry")

        matched_sets: list[MatchedStrategySet] = []
        if config.kind == "strategy_config" and config.strategy_config:
            active = [
                ActiveRegime(definition=reg)
                for reg in config.strategy_config.regimes
                if any(r.regime_id == reg.id and r.passed for r in regimes.active_regimes)
            ]
            router = StrategyRouter(config.strategy_config.routing, config.strategy_config.strategy_sets)
            matched_sets = router.route_regimes(active)

        entry = self.evaluate_entry(
            config,
            features=features,
            chart_window=chart_window,
            prev_regime=prev_regime,
            selected_regime=regimes.selected_regime.regime_id if regimes.selected_regime else None,
        )

        score = self.score(config, indicators, regimes, entry, matched_sets)

        return StrategySettingsRunResult(
            config=config,
            indicators=indicators,
            regimes=regimes,
            entry=entry,
            matched_sets=matched_sets,
            score=score,
        )

    def detect_regime_periods(self, candles: list[dict], config: PipelineConfig) -> list[dict]:
        indicators = self.compute_indicators(candles, config)
        if indicators.errors:
            raise ValueError("; ".join(indicators.errors))

        df, errors = self._candles_to_df(candles)
        if errors:
            raise ValueError("; ".join(errors))

        if len(df) < MIN_CANDLES:
            raise ValueError(f"Need at least {MIN_CANDLES} candles for regime detection")

        regime_periods = []
        current_regime = None

        for idx in range(MIN_CANDLES, len(df)):
            values_at_idx = self._slice_indicator_values(indicators.series, idx)
            if config.kind == "strategy_config" and config.strategy_config:
                regime_result = self._detect_regime_conditions(
                    values_at_idx, config.strategy_config.regimes, scope="entry"
                )
            else:
                sliced = IndicatorComputationResult(
                    values=values_at_idx,
                    series={"__type_index__": indicators.series.get("__type_index__", {})},
                    missing=indicators.missing,
                    nan=indicators.nan,
                    errors=indicators.errors,
                    candle_count=indicators.candle_count,
                )
                regime_result = self._detect_regime_thresholds(
                    sliced,
                    config.regimes_def,
                    scope="entry",
                    values_override=values_at_idx,
                )

            active_id = regime_result.selected_regime.regime_id if regime_result.selected_regime else "UNKNOWN"
            ts = df.iloc[idx]["timestamp"]
            dt = self._timestamp_to_datetime(ts)

            if current_regime is None:
                current_regime = {
                    "regime": active_id,
                    "score": 100.0,
                    "start_timestamp": ts,
                    "start_date": dt.strftime("%Y-%m-%d"),
                    "start_time": dt.strftime("%H:%M:%S"),
                    "start_bar_index": idx,
                }
            elif current_regime["regime"] != active_id:
                current_regime["end_timestamp"] = ts
                current_regime["end_date"] = dt.strftime("%Y-%m-%d")
                current_regime["end_time"] = dt.strftime("%H:%M:%S")
                current_regime["end_bar_index"] = idx
                current_regime["duration_bars"] = idx - current_regime["start_bar_index"]
                dur_s = ts - current_regime["start_timestamp"]
                if current_regime["start_timestamp"] > 1e10:
                    dur_s /= 1000
                current_regime["duration_time"] = self._fmt_duration(dur_s)
                regime_periods.append(current_regime)

                current_regime = {
                    "regime": active_id,
                    "score": 100.0,
                    "start_timestamp": ts,
                    "start_date": dt.strftime("%Y-%m-%d"),
                    "start_time": dt.strftime("%H:%M:%S"),
                    "start_bar_index": idx,
                }

        if current_regime is not None:
            last_ts = df.iloc[-1]["timestamp"]
            last_dt = self._timestamp_to_datetime(last_ts)
            current_regime["end_timestamp"] = last_ts
            current_regime["end_date"] = last_dt.strftime("%Y-%m-%d")
            current_regime["end_time"] = last_dt.strftime("%H:%M:%S")
            current_regime["end_bar_index"] = len(df)
            current_regime["duration_bars"] = len(df) - current_regime["start_bar_index"]
            dur_s = last_ts - current_regime["start_timestamp"]
            if current_regime["start_timestamp"] > 1e10:
                dur_s /= 1000
            current_regime["duration_time"] = self._fmt_duration(dur_s)
            regime_periods.append(current_regime)

        return regime_periods

    # ------------------------------------------------------------------ Helpers

    def _select_optimization_result(self, results: list[dict[str, Any]]) -> dict[str, Any]:
        if not results:
            return {}
        applied = [r for r in results if r.get("applied")]
        return applied[-1] if applied else results[0]

    def _normalize_params(self, params_raw: Any) -> dict[str, Any]:
        if isinstance(params_raw, list):
            return {p.get("name"): p.get("value") for p in params_raw if p.get("name") is not None}
        if isinstance(params_raw, dict):
            return params_raw
        return {}

    def _extract_latest_values(self, values: Any) -> dict[str, float]:
        if isinstance(values, pd.Series):
            latest_value = values.iloc[-1] if len(values) else np.nan
            return {"value": float(latest_value) if latest_value is not None else float("nan")}
        if isinstance(values, pd.DataFrame):
            result: dict[str, float] = {}
            if not values.empty:
                for col in values.columns:
                    result[col] = float(values[col].iloc[-1]) if len(values[col]) else float("nan")
                # Provide a generic value alias for first column
                first_col = values.columns[0]
                result.setdefault("value", result.get(first_col, float("nan")))
            return result
        if isinstance(values, dict):
            return {k: float(v) if v is not None else float("nan") for k, v in values.items()}
        return {"value": float("nan")}

    def _candles_to_df(self, candles: list[dict]) -> tuple[pd.DataFrame, list[str]]:
        if not candles:
            return pd.DataFrame(), ["No candles provided"]

        df = pd.DataFrame(candles)
        if df.empty:
            return df, ["Empty candle DataFrame"]

        # normalize columns
        df.columns = [str(c).lower() for c in df.columns]

        if "timestamp" not in df.columns:
            for alt in ("time", "date", "datetime", "index"):
                if alt in df.columns:
                    df["timestamp"] = df[alt]
                    break

        if "timestamp" not in df.columns:
            df["timestamp"] = range(len(df))

        required = ["open", "high", "low", "close"]
        missing = [c for c in required if c not in df.columns]
        if missing:
            return df, [f"Missing candle columns: {missing}"]

        return df, []

    def _augment_threshold_series(
        self,
        df: pd.DataFrame,
        indicator_values: dict[str, dict[str, float]],
        indicator_series: dict[str, Any],
        nan: list[str],
    ) -> None:
        try:
            import pandas_ta as ta
        except Exception as exc:
            logger.debug("pandas_ta not available: %s", exc)
            return

        adx_period = 14
        for ind_name, values in indicator_values.items():
            if ind_name == "__type_index__":
                continue
            if "adx" in str(ind_name).lower():
                adx_period = 14
                break

        try:
            adx_df = ta.adx(df["high"], df["low"], df["close"], length=adx_period)
            if adx_df is not None and not adx_df.empty:
                di_plus_col = f"DMP_{adx_period}"
                di_minus_col = f"DMN_{adx_period}"
                if di_plus_col in adx_df.columns:
                    indicator_series["PLUS_DI"] = adx_df[di_plus_col]
                    indicator_series["MINUS_DI"] = adx_df[di_minus_col]
                    indicator_series["DI_DIFF"] = adx_df[di_plus_col] - adx_df[di_minus_col]
                    indicator_values["PLUS_DI"] = {"value": float(adx_df[di_plus_col].iloc[-1])}
                    indicator_values["MINUS_DI"] = {"value": float(adx_df[di_minus_col].iloc[-1])}
                    indicator_values["DI_DIFF"] = {"value": float((adx_df[di_plus_col] - adx_df[di_minus_col]).iloc[-1])}
        except Exception as exc:
            logger.debug("Could not calculate DI+/DI-: %s", exc)

        indicator_series["PRICE_CHANGE_PCT"] = df["close"].pct_change() * 100
        indicator_values["PRICE_CHANGE_PCT"] = {"value": float(indicator_series["PRICE_CHANGE_PCT"].iloc[-1])}

        if self._is_nan(indicator_values["PRICE_CHANGE_PCT"]["value"]):
            nan.append("PRICE_CHANGE_PCT")

    def _detect_regime_conditions(
        self,
        indicator_values: dict[str, dict[str, float]],
        regimes: list[RegimeDefinition],
        scope: str,
    ) -> RegimeDetectionResult:
        scope_enum = None
        if scope:
            try:
                scope_enum = RegimeScope(scope)
            except Exception:
                scope_enum = None

        all_evals: list[RegimeEvaluation] = []
        active: list[RegimeEvaluation] = []
        missing_refs: list[str] = []

        for reg in regimes:
            if scope_enum and reg.scope not in (None, RegimeScope.GLOBAL, scope_enum):
                continue

            passed, details, missing = self._evaluate_condition_group(reg.conditions, indicator_values)
            missing_refs.extend(missing)
            eval_result = RegimeEvaluation(
                regime_id=reg.id,
                name=reg.name,
                passed=passed,
                details=details,
                scope=reg.scope.value if reg.scope else None,
                priority=reg.priority,
            )
            all_evals.append(eval_result)
            if passed:
                active.append(eval_result)

        active.sort(key=lambda r: r.priority or 0, reverse=True)
        selected = active[0] if active else None
        return RegimeDetectionResult(
            active_regimes=active,
            selected_regime=selected,
            all_regimes=all_evals,
            missing_indicators=sorted(set(missing_refs)),
        )

    def _evaluate_condition_group(
        self,
        group: Any,
        indicator_values: dict[str, dict[str, float]],
    ) -> tuple[bool, list[dict[str, Any]], list[str]]:
        details: list[dict[str, Any]] = []
        missing_refs: list[str] = []

        all_list = getattr(group, "all", None) or []
        any_list = getattr(group, "any", None) or []

        def eval_condition(cond: Any) -> bool:
            if hasattr(cond, "cel_expression") and cond.cel_expression:
                return self._eval_cel_condition(cond.cel_expression, indicator_values, details)
            return self._eval_operator_condition(cond, indicator_values, details, missing_refs)

        all_results = [eval_condition(c) for c in all_list]
        any_results = [eval_condition(c) for c in any_list]

        all_ok = all(all_results) if all_list else True
        any_ok = any(any_results) if any_list else True

        return all_ok and any_ok, details, missing_refs

    def _eval_cel_condition(
        self,
        expression: str,
        indicator_values: dict[str, dict[str, float]],
        details: list[dict[str, Any]],
    ) -> bool:
        try:
            cel = get_cel_engine()
            result = cel.evaluate(expression, indicator_values, default=False)
            passed = bool(result)
            details.append({
                "type": "cel",
                "expression": expression,
                "result": passed,
            })
            return passed
        except Exception as exc:
            details.append({
                "type": "cel",
                "expression": expression,
                "result": False,
                "error": str(exc),
            })
            return False

    def _eval_operator_condition(
        self,
        cond: Any,
        indicator_values: dict[str, dict[str, float]],
        details: list[dict[str, Any]],
        missing_refs: list[str],
    ) -> bool:
        try:
            left_val = self._resolve_operand(cond.left, indicator_values)
            op = cond.op.value if hasattr(cond.op, "value") else cond.op
            passed = False
            right_val: Any = None

            if op == "between":
                right_val = {"min": cond.right.min, "max": cond.right.max}
                passed = cond.right.min <= left_val <= cond.right.max
            else:
                right_val = self._resolve_operand(cond.right, indicator_values)
                if op == "gt":
                    passed = left_val > right_val
                elif op == "lt":
                    passed = left_val < right_val
                elif op == "eq":
                    passed = math.isclose(left_val, right_val)

            details.append({
                "type": "op",
                "left": left_val,
                "op": op,
                "right": right_val,
                "result": passed,
            })
            return passed
        except Exception as exc:
            msg = str(exc)
            if "Missing indicator value:" in msg or "NaN indicator value:" in msg:
                indicator_id = msg.split(":", 1)[1].strip().split(".")[0]
                missing_refs.append(indicator_id)
            details.append({
                "type": "op",
                "error": str(exc),
                "result": False,
            })
            return False

    def _resolve_operand(self, operand: Any, indicator_values: dict[str, dict[str, float]]) -> float:
        if hasattr(operand, "value") and not hasattr(operand, "indicator_id"):
            return float(operand.value)
        if hasattr(operand, "indicator_id"):
            ind_id = operand.indicator_id
            field = operand.field
            if ind_id not in indicator_values or field not in indicator_values[ind_id]:
                raise ValueError(f"Missing indicator value: {ind_id}.{field}")
            value = indicator_values[ind_id][field]
            if value is None or self._is_nan(value):
                raise ValueError(f"NaN indicator value: {ind_id}.{field}")
            return float(value)
        if isinstance(operand, dict):
            if "value" in operand:
                return float(operand["value"])
            if "indicator_id" in operand and "field" in operand:
                ind_id = operand["indicator_id"]
                field = operand["field"]
                if ind_id not in indicator_values or field not in indicator_values[ind_id]:
                    raise ValueError(f"Missing indicator value: {ind_id}.{field}")
                value = indicator_values[ind_id][field]
                if value is None or self._is_nan(value):
                    raise ValueError(f"NaN indicator value: {ind_id}.{field}")
                return float(value)
        raise ValueError(f"Unsupported operand: {operand}")

    def _detect_regime_thresholds(
        self,
        indicators: IndicatorComputationResult,
        regimes_def: list[dict[str, Any]],
        scope: str,
        values_override: dict[str, dict[str, float]] | None = None,
    ) -> RegimeDetectionResult:
        all_evals: list[RegimeEvaluation] = []
        active: list[RegimeEvaluation] = []
        missing_refs: list[str] = []
        type_index = indicators.series.get("__type_index__", {}) if indicators.series else {}
        values_map = values_override if values_override is not None else indicators.values

        def get_value(th_name: str) -> float | None:
            if values_override is not None:
                return self._resolve_threshold_value_from_values(th_name, values_map, type_index)
            return self._resolve_threshold_value(th_name, indicators.series, type_index)

        regimes_sorted = sorted(regimes_def, key=lambda r: r.get("priority", 0), reverse=True)

        for regime in regimes_sorted:
            if scope and regime.get("scope") not in (None, scope):
                continue
            details = []
            passed = True
            for th in regime.get("thresholds", []):
                th_name = th.get("name")
                th_value = th.get("value")
                current = get_value(th_name)
                if current is None or th_value is None or self._is_nan(current):
                    details.append({
                        "threshold": th_name,
                        "value": th_value,
                        "current": current,
                        "result": False,
                        "error": "MISSING_VALUE",
                    })
                    if th_name:
                        missing_refs.append(th_name)
                    passed = False
                    continue

                result = self._evaluate_threshold(th_name, current, th_value, regime_id=regime.get("id", ""))
                details.append({
                    "threshold": th_name,
                    "value": th_value,
                    "current": current,
                    "result": result,
                })
                if not result:
                    passed = False

            eval_result = RegimeEvaluation(
                regime_id=regime.get("id", ""),
                name=regime.get("name"),
                passed=passed,
                details=details,
                scope=regime.get("scope"),
                priority=regime.get("priority"),
            )
            all_evals.append(eval_result)
            if passed:
                active.append(eval_result)

        active.sort(key=lambda r: r.priority or 0, reverse=True)
        selected = active[0] if active else None
        return RegimeDetectionResult(
            active_regimes=active,
            selected_regime=selected,
            all_regimes=all_evals,
            missing_indicators=sorted(set(missing_refs)),
        )

    def _resolve_threshold_value(
        self,
        th_name: str,
        series_map: dict[str, Any],
        type_index: dict[str, str],
    ) -> float | None:
        if not th_name:
            return None

        base = th_name.split("_", 1)[0].lower()

        # Direct field match
        for ind_vals in series_map.values():
            if isinstance(ind_vals, pd.DataFrame):
                if th_name in ind_vals.columns:
                    return float(ind_vals[th_name].iloc[-1])
                if base in ind_vals.columns:
                    return float(ind_vals[base].iloc[-1])
            elif isinstance(ind_vals, pd.Series):
                if base in ("value", th_name):
                    return float(ind_vals.iloc[-1])

        # Type-based fallback
        adx_id = type_index.get("ADX")
        rsi_id = type_index.get("RSI")
        atr_id = type_index.get("ATR")

        if "adx" in th_name and adx_id and adx_id in series_map:
            return self._extract_series_value(series_map[adx_id])
        if "di_diff" in th_name and "DI_DIFF" in series_map:
            return self._extract_series_value(series_map["DI_DIFF"])
        if "rsi" in th_name and rsi_id and rsi_id in series_map:
            return self._extract_series_value(series_map[rsi_id])
        if "atr" in th_name and atr_id and atr_id in series_map:
            return self._extract_series_value(series_map[atr_id])
        if "price_change" in th_name and "PRICE_CHANGE_PCT" in series_map:
            return self._extract_series_value(series_map["PRICE_CHANGE_PCT"])

        return None

    def _resolve_threshold_value_from_values(
        self,
        th_name: str,
        values_map: dict[str, dict[str, float]],
        type_index: dict[str, str],
    ) -> float | None:
        if not th_name:
            return None

        base = th_name.split("_", 1)[0].lower()

        for ind_vals in values_map.values():
            if th_name in ind_vals:
                return float(ind_vals[th_name])
            if base in ind_vals:
                return float(ind_vals[base])
            if "value" in ind_vals and base in ("value", th_name):
                return float(ind_vals["value"])

        adx_id = type_index.get("ADX")
        rsi_id = type_index.get("RSI")
        atr_id = type_index.get("ATR")

        if "adx" in th_name and adx_id and adx_id in values_map:
            return self._extract_value_from_map(values_map[adx_id])
        if "di_diff" in th_name and "DI_DIFF" in values_map:
            return self._extract_value_from_map(values_map["DI_DIFF"])
        if "rsi" in th_name and rsi_id and rsi_id in values_map:
            return self._extract_value_from_map(values_map[rsi_id])
        if "atr" in th_name and atr_id and atr_id in values_map:
            return self._extract_value_from_map(values_map[atr_id])
        if "price_change" in th_name and "PRICE_CHANGE_PCT" in values_map:
            return self._extract_value_from_map(values_map["PRICE_CHANGE_PCT"])

        return None

    @staticmethod
    def _extract_value_from_map(values: dict[str, float]) -> float | None:
        if not values:
            return None
        if "value" in values:
            return float(values["value"])
        # fallback: first value
        return float(next(iter(values.values())))

    def _extract_series_value(self, series: Any) -> float | None:
        if isinstance(series, pd.Series):
            if series.empty:
                return None
            return float(series.iloc[-1])
        if isinstance(series, pd.DataFrame):
            if series.empty:
                return None
            return float(series.iloc[-1, 0])
        return None

    def _evaluate_threshold(self, th_name: str, current: float, value: float, regime_id: str) -> bool:
        if th_name == "di_diff_min":
            if "BULL" in regime_id:
                return current >= value
            if "BEAR" in regime_id:
                return current <= -value
            return abs(current) >= value
        if th_name in ("rsi_strong_bull", "rsi_confirm_bull"):
            return current >= value
        if th_name in ("rsi_strong_bear", "rsi_confirm_bear"):
            return current <= value
        if th_name == "rsi_exhaustion_max":
            return current <= value
        if th_name == "rsi_exhaustion_min":
            return current >= value
        if th_name == "extreme_move_pct":
            if "BULL" in regime_id:
                return current >= value
            if "BEAR" in regime_id:
                return current <= -value
            return abs(current) >= value
        if th_name.endswith("_min"):
            return current >= value
        if th_name.endswith("_max"):
            return current <= value
        return False

    def _slice_indicator_values(self, series_map: dict[str, Any], idx: int) -> dict[str, dict[str, float]]:
        values: dict[str, dict[str, float]] = {}
        for name, series in series_map.items():
            if name == "__type_index__":
                continue
            if isinstance(series, pd.Series):
                if idx < len(series):
                    values[name] = {"value": float(series.iloc[idx])}
            elif isinstance(series, pd.DataFrame):
                if idx < len(series):
                    row = series.iloc[idx]
                    values[name] = {col: float(row[col]) for col in series.columns}
                    values[name].setdefault("value", float(row[series.columns[0]]))
        return values

    def _data_quality_score(
        self,
        indicators: IndicatorComputationResult,
        missing_override: list[str] | None = None,
    ) -> tuple[int, list[dict[str, Any]]]:
        penalties = []
        score = 10

        missing_list = missing_override if missing_override is not None else indicators.missing

        if indicators.candle_count < MIN_CANDLES:
            penalties.append({"code": "INSUFFICIENT_CANDLES", "delta": -5, "count": indicators.candle_count})
            score -= 5

        if missing_list:
            delta = -min(5, len(missing_list))
            penalties.append({"code": "MISSING_INDICATORS", "delta": delta, "count": len(missing_list)})
            score += delta

        if indicators.nan:
            delta = -min(5, len(indicators.nan))
            penalties.append({"code": "NAN_INDICATORS", "delta": delta, "count": len(indicators.nan)})
            score += delta

        score = max(0, min(10, score))
        return score, penalties

    def _build_regime_state(self, regime_id: str | None) -> RegimeState:
        return RegimeState(
            regime=RegimeType.UNKNOWN,
            regime_name=regime_id or "UNKNOWN",
            regime_confidence=1.0 if regime_id else 0.2,
            timestamp=datetime.utcnow(),
            gate_reason="",
            allows_market_entry=True,
        )

    def _timestamp_to_datetime(self, ts: Any) -> datetime:
        if isinstance(ts, datetime):
            return ts
        try:
            ts_val = float(ts)
            return datetime.fromtimestamp(ts_val / 1000 if ts_val > 1e10 else ts_val)
        except Exception:
            return datetime.utcnow()

    @staticmethod
    def _fmt_duration(seconds: float) -> str:
        try:
            seconds = float(seconds)
            if math.isnan(seconds) or seconds < 0:
                return "n/a"
        except (TypeError, ValueError):
            return "n/a"
        if seconds < 60:
            return f"{int(seconds)}s"
        if seconds < 3600:
            return f"{int(seconds / 60)}m"
        hours = int(seconds / 3600)
        minutes = int((seconds % 3600) / 60)
        return f"{hours}h {minutes}m" if minutes > 0 else f"{hours}h"

    @staticmethod
    def _is_nan(value: Any) -> bool:
        try:
            return value is None or (isinstance(value, float) and math.isnan(value))
        except Exception:
            return False
