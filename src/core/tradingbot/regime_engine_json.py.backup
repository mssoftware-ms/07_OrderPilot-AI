"""JSON-based Regime Engine for Tradingbot.

Refactored from hardcoded RegimeEngine to JSON-based configuration.
Uses IndicatorEngine for calculations and RegimeDetector for evaluation.

Architecture:
    JSON Config -> IndicatorEngine (calculate) -> RegimeDetector (evaluate) -> RegimeState

Migration:
    - Old: RegimeEngine.classify(features) -> RegimeState
    - New: RegimeEngineJSON.classify(data, config_path) -> RegimeState
"""

from __future__ import annotations

import logging
from datetime import datetime
import json
import tempfile
from pathlib import Path

import pandas as pd
import pandas_ta as ta

from src.core.indicators.engine import IndicatorEngine
from src.core.indicators.types import IndicatorConfig, IndicatorType

from .config.detector import RegimeDetector
from .config.loader import ConfigLoader
from .models import (
    FeatureVector,
    RegimeState,
    RegimeType,
    VolatilityLevel,
)

logger = logging.getLogger(__name__)


class RegimeEngineJSON:
    """JSON-based regime engine using IndicatorEngine + RegimeDetector.

    Replaces hardcoded thresholds with configurable JSON-based regime definitions.

    Features:
    - Load regime definitions from JSON
    - Calculate indicators using IndicatorEngine
    - Evaluate regimes using RegimeDetector
    - Convert to legacy RegimeState for compatibility

    Example:
        >>> engine = RegimeEngineJSON()
        >>> state = engine.classify_from_config(
        ...     data=df,  # OHLCV DataFrame
        ...     config_path="03_JSON/Trading_Bot/momentum_downtrend.json"
        ... )
        >>> print(state.regime_label)
        'TREND_DOWN (EXTREME)'
    """

    def __init__(self):
        """Initialize JSON-based regime engine."""
        self.indicator_engine = IndicatorEngine()
        self.config_loader = ConfigLoader()
        self._cached_config = None
        self._cached_config_path = None
        logger.info("RegimeEngineJSON initialized (JSON-based regime detection)")

    def classify_from_config(
        self,
        data: pd.DataFrame,
        config_path: str | Path,
        scope: str = "entry"
    ) -> RegimeState:
        """Classify market regime using JSON configuration.

        Args:
            data: OHLCV DataFrame with columns: open, high, low, close, volume
            config_path: Path to JSON strategy config
            scope: Regime scope ("entry", "exit", "in_trade")

        Returns:
            RegimeState with regime and volatility classification
        """
        # 0. Peek raw JSON to detect Entry-Analyzer optimization format
        raw = self._load_raw_json(config_path)
        if raw and "optimization_results" in raw and "indicators" not in raw:
            return self._classify_entry_optimizer(raw, data, scope=scope)

        # 1. Load JSON config (strategy schema)
        config = self._load_config(config_path)

        # 2. Calculate indicators
        indicator_values = self._calculate_indicators(data, config)

        # 3. Detect active regimes
        detector = RegimeDetector(config.regimes)
        active_regimes = detector.detect_active_regimes(indicator_values, scope=scope)

        # 4. Convert to RegimeState
        state = self._convert_to_regime_state(
            active_regimes=active_regimes,
            indicator_values=indicator_values,
            timestamp=datetime.utcnow()
        )

        logger.info(
            f"Regime classified from JSON: {state.regime_label} "
            f"(confidence={state.regime_confidence:.2f})"
        )

        return state

    def classify_from_features(
        self,
        features: FeatureVector,
        config_path: str | Path,
        scope: str = "entry"
    ) -> RegimeState:
        """Classify regime from pre-calculated FeatureVector.

        Convenience wrapper that converts FeatureVector to indicator_values dict.

        Args:
            features: Pre-calculated feature vector
            config_path: Path to JSON strategy config
            scope: Regime scope

        Returns:
            RegimeState
        """
        # Convert FeatureVector to indicator_values dict
        indicator_values = self._features_to_indicator_values(features)

        # Load config
        config = self._load_config(config_path)

        # Detect regimes
        detector = RegimeDetector(config.regimes)
        active_regimes = detector.detect_active_regimes(indicator_values, scope=scope)

        # Convert to RegimeState
        return self._convert_to_regime_state(
            active_regimes=active_regimes,
            indicator_values=indicator_values,
            timestamp=features.timestamp
        )

    def _load_config(self, config_path: str | Path):
        """Load and cache JSON configuration.

        Args:
            config_path: Path to JSON file

        Returns:
            TradingBotConfig object
        """
        config_path = str(config_path)

        # Use cache if same path
        if self._cached_config_path == config_path:
            return self._cached_config

        # Load new config
        config = self.config_loader.load_config(config_path)
        self._cached_config = config
        self._cached_config_path = config_path

        logger.info(
            f"Loaded config: {len(config.regimes)} regimes, "
            f"{len(config.indicators)} indicators"
        )

        return config

    def _load_raw_json(self, config_path: str | Path) -> dict | None:
        """Load raw JSON without schema validation (used to detect optimizer format)."""
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    # --- Entry Analyzer optimization format (regime JSON v2) ---
    def _classify_entry_optimizer(
        self,
        raw_config: dict,
        data: pd.DataFrame,
        scope: str = "entry",
    ) -> RegimeState:
        """
        Handle Entry Analyzer optimization JSON directly (no strategy schema).

        Expects structure:
        {
            "schema_version": "2.0.0",
            "metadata": {...},
            "optimization_results": [
                {
                    "applied": true,
                    "indicators": [...],
                    "regimes": [...]
                }
            ]
        }
        """
        if "optimization_results" not in raw_config:
            raise ValueError("optimizer JSON missing 'optimization_results'")

        opt = next(
            (o for o in raw_config["optimization_results"] if o.get("applied")),
            raw_config["optimization_results"][0],
        )

        indicators_def = opt.get("indicators") or []
        regimes_def = opt.get("regimes") or []

        if not indicators_def or not regimes_def:
            raise ValueError("optimizer JSON missing indicators/regimes")

        indicator_values, type_index = self._calculate_opt_indicators(data, indicators_def)
        active_regime = self._detect_opt_regime(indicator_values, regimes_def, type_index, scope=scope)

        regime_id = active_regime["id"] if active_regime else "UNKNOWN"
        state = RegimeState(
            regime=RegimeType.UNKNOWN,
            regime_confidence=1.0 if active_regime else 0.2,
            regime_name=regime_id,
            timestamp=datetime.utcnow(),
            gate_reason="",
            allows_market_entry=True,
        )
        return state

    def _calculate_opt_indicators(
        self,
        data: pd.DataFrame,
        indicators_def: list[dict],
    ) -> tuple[dict[str, dict[str, float]], dict[str, str]]:
        """
        Calculate indicators for optimization-format JSON.

        Returns:
            indicator_values: {indicator_name: {field: value}}
            type_index: {indicator_type: indicator_name}
        """
        indicator_values: dict[str, dict[str, float]] = {}
        type_index: dict[str, str] = {}

        computed = 0
        for ind in indicators_def:
            name = ind.get("name")
            ind_type = (ind.get("type") or "").upper()
            params = ind.get("params") or []

            def _param(pname, default=None):
                for p in params:
                    if p.get("name") == pname:
                        return p.get("value", default)
                return default

            if not name or not ind_type:
                raise ValueError("Indicator definition missing name or type")

            type_index.setdefault(ind_type, name)

            try:
                # Dynamische Berechnung je nach Typ; wenn ein Typ fehlt, wird er übersprungen.
                if ind_type == "ADX":
                    period = int(_param("period", 14))
                    adx_res = ta.adx(data["high"], data["low"], data["close"], length=period)
                    if adx_res is None or adx_res.empty:
                        raise ValueError(f"Indicator {name} (ADX) produced no data")
                    adx_col = next((c for c in adx_res.columns if "ADX" in c.upper()), None)
                    dmp_col = next((c for c in adx_res.columns if "DMP" in c.upper()), None)
                    dmn_col = next((c for c in adx_res.columns if "DMN" in c.upper()), None)
                    adx_val = adx_res[adx_col].iloc[-1] if adx_col else None
                    dmp_val = adx_res[dmp_col].iloc[-1] if dmp_col else None
                    dmn_val = adx_res[dmn_col].iloc[-1] if dmn_col else None
                    di_diff = None
                    if dmp_val is not None and dmn_val is not None:
                        di_diff = abs(float(dmp_val) - float(dmn_val))
                    indicator_values[name] = {
                        "adx": float(adx_val) if adx_val is not None else None,
                        "di_diff": di_diff,
                    }

                elif ind_type == "RSI":
                    period = int(_param("period", 14))
                    rsi_res = ta.rsi(data["close"], length=period)
                    if rsi_res is None or rsi_res.empty:
                        raise ValueError(f"Indicator {name} (RSI) produced no data")
                    rsi_val = rsi_res.iloc[-1]
                    indicator_values[name] = {"rsi": float(rsi_val)}

                elif ind_type == "ATR":
                    period = int(_param("period", 14))
                    atr_res = ta.atr(data["high"], data["low"], data["close"], length=period)
                    if atr_res is None or atr_res.empty:
                        raise ValueError(f"Indicator {name} (ATR) produced no data")
                    atr_val = atr_res.iloc[-1]
                    close_val = data["close"].iloc[-1]
                    atr_pct = float(atr_val / close_val * 100) if close_val else None
                    indicator_values[name] = {"atr": float(atr_val), "atr_percent": atr_pct}

                elif ind_type == "EMA":
                    period = int(_param("period", 20))
                    ema_res = ta.ema(data["close"], length=period)
                    if ema_res is None or ema_res.empty:
                        raise ValueError(f"Indicator {name} (EMA) produced no data")
                    indicator_values[name] = {"value": float(ema_res.iloc[-1])}

                elif ind_type == "SMA":
                    period = int(_param("period", 20))
                    sma_res = ta.sma(data["close"], length=period)
                    if sma_res is None or sma_res.empty:
                        raise ValueError(f"Indicator {name} (SMA) produced no data")
                    indicator_values[name] = {"value": float(sma_res.iloc[-1])}

                elif ind_type == "MACD":
                    fast = int(_param("fast", 12))
                    slow = int(_param("slow", 26))
                    signal = int(_param("signal", 9))
                    macd_res = ta.macd(data["close"], fast=fast, slow=slow, signal=signal)
                    if macd_res is None or macd_res.empty:
                        raise ValueError(f"Indicator {name} (MACD) produced no data")
                    macd_col = next((c for c in macd_res.columns if "MACD" in c.upper() and "SIGNAL" not in c.upper() and "HIST" not in c.upper()), None)
                    signal_col = next((c for c in macd_res.columns if "SIGNAL" in c.upper()), None)
                    hist_col = next((c for c in macd_res.columns if "HIST" in c.upper()), None)
                    indicator_values[name] = {
                        "macd": float(macd_res[macd_col].iloc[-1]) if macd_col else None,
                        "signal": float(macd_res[signal_col].iloc[-1]) if signal_col else None,
                        "hist": float(macd_res[hist_col].iloc[-1]) if hist_col else None,
                    }

                elif ind_type == "BB":
                    length = int(_param("period", 20))
                    mult = float(_param("mult", 2.0))
                    bb_res = ta.bbands(data["close"], length=length, std=mult)
                    if bb_res is None or bb_res.empty:
                        raise ValueError(f"Indicator {name} (BB) produced no data")
                    upper = next((c for c in bb_res.columns if "UPPER" in c.upper()), None)
                    lower = next((c for c in bb_res.columns if "LOWER" in c.upper()), None)
                    mid = next((c for c in bb_res.columns if "MID" in c.upper() or "MIDDLE" in c.upper()), None)
                    width = next((c for c in bb_res.columns if "WIDTH" in c.upper()), None)
                    indicator_values[name] = {
                        "upper": float(bb_res[upper].iloc[-1]) if upper else None,
                        "lower": float(bb_res[lower].iloc[-1]) if lower else None,
                        "middle": float(bb_res[mid].iloc[-1]) if mid else None,
                        "width": float(bb_res[width].iloc[-1]) if width else None,
                    }

                elif ind_type == "STOCH":
                    k = int(_param("k", 14))
                    d = int(_param("d", 3))
                    stoch_res = ta.stoch(data["high"], data["low"], data["close"], k=k, d=d)
                    if stoch_res is None or stoch_res.empty:
                        raise ValueError(f"Indicator {name} (STOCH) produced no data")
                    k_col = next((c for c in stoch_res.columns if "K" in c.upper()), None)
                    d_col = next((c for c in stoch_res.columns if "D" in c.upper()), None)
                    indicator_values[name] = {
                        "k": float(stoch_res[k_col].iloc[-1]) if k_col else None,
                        "d": float(stoch_res[d_col].iloc[-1]) if d_col else None,
                    }

                elif ind_type == "MFI":
                    period = int(_param("period", 14))
                    mfi_res = ta.mfi(data["high"], data["low"], data["close"], data["volume"], length=period)
                    if mfi_res is None or mfi_res.empty:
                        raise ValueError(f"Indicator {name} (MFI) produced no data")
                    indicator_values[name] = {"mfi": float(mfi_res.iloc[-1])}

                elif ind_type == "CCI":
                    period = int(_param("period", 20))
                    cci_res = ta.cci(data["high"], data["low"], data["close"], length=period)
                    if cci_res is None or cci_res.empty:
                        raise ValueError(f"Indicator {name} (CCI) produced no data")
                    indicator_values[name] = {"cci": float(cci_res.iloc[-1])}

                elif ind_type == "CHOP":
                    length = int(_param("period", 14))
                    chop_res = ta.chop(data["high"], data["low"], data["close"], length=length)
                    if chop_res is None or chop_res.empty:
                        raise ValueError(f"Indicator {name} (CHOP) produced no data")
                    indicator_values[name] = {"chop": float(chop_res.iloc[-1])}

                else:
                    raise ValueError(f"Unsupported indicator type in optimizer JSON: {ind_type}")
                computed += 1
            except Exception as e:
                logger.error(f"Failed to compute indicator {name} ({ind_type}): {e}")
                raise

        if computed != len(indicators_def):
            raise ValueError(
                f"Only {computed}/{len(indicators_def)} indicators computed. Check definitions."
            )

        return indicator_values, type_index

    def _detect_opt_regime(
        self,
        indicator_values: dict[str, dict[str, float]],
        regimes_def: list[dict],
        type_index: dict[str, str],
        scope: str = "entry",
    ) -> dict | None:
        """Evaluate regimes based on simple threshold rules from optimizer JSON."""

        def _value_from_threshold(th_name: str):
            """Resolve a threshold name to a current indicator value."""
            base = th_name.split("_", 1)[0].lower()

            # 1) Try direct field match across all indicators
            for ind_vals in indicator_values.values():
                if th_name in ind_vals:
                    return ind_vals[th_name]
                if base in ind_vals:
                    return ind_vals[base]

            # 2) Type-based fallback (common prefixes)
            adx_id = type_index.get("ADX")
            rsi_id = type_index.get("RSI")
            atr_id = type_index.get("ATR")

            if "adx" in th_name and adx_id:
                return indicator_values.get(adx_id, {}).get("adx")
            if "di_diff" in th_name and adx_id:
                return indicator_values.get(adx_id, {}).get("di_diff")
            if "rsi" in th_name and rsi_id:
                return indicator_values.get(rsi_id, {}).get("rsi")
            if "atr" in th_name and atr_id:
                if "percent" in th_name:
                    return indicator_values.get(atr_id, {}).get("atr_percent")
                return indicator_values.get(atr_id, {}).get("atr")
            return None

        # Sort by priority (desc)
        regimes_sorted = sorted(regimes_def, key=lambda r: r.get("priority", 0), reverse=True)

        for regime in regimes_sorted:
            if scope and regime.get("scope") not in (None, scope):
                continue

            thresholds = regime.get("thresholds", [])
            active = True
            for th in thresholds:
                th_name = th.get("name", "")
                th_value = th.get("value")
                current = _value_from_threshold(th_name)
                if current is None or th_value is None:
                    raise ValueError(f"Missing value for threshold '{th_name}'")

                if th_name.endswith("_min"):
                    if current < th_value:
                        active = False
                        break
                elif th_name.endswith("_max"):
                    if current > th_value:
                        active = False
                        break
                elif "confirm_bull" in th_name or "exhaustion_min" in th_name:
                    if current < th_value:
                        active = False
                        break
                elif "confirm_bear" in th_name or "exhaustion_max" in th_name:
                    if current > th_value:
                        active = False
                        break
                else:
                    # Unknown threshold type -> treat as inactive but do not crash
                    active = False
                    break

            if active:
                return regime

        return None

    def _calculate_indicators(
        self,
        data: pd.DataFrame,
        config
    ) -> dict[str, dict[str, float]]:
        """Calculate all indicators defined in config.

        Args:
            data: OHLCV DataFrame
            config: TradingBotConfig

        Returns:
            Dict mapping indicator_id -> {field -> value}
            Example: {"momentum_score": {"value": -4.2}, "volume_ratio": {"value": 2.8}}
        """
        indicator_values = {}

        for ind_def in config.indicators:
            try:
                # Create IndicatorConfig
                ind_config = IndicatorConfig(
                    indicator_type=IndicatorType(ind_def.type.lower()),
                    params=ind_def.params,
                    use_talib=False,  # Use pandas_ta by default
                    cache_results=True
                )

                # Calculate indicator
                result = self.indicator_engine.calculate(data, ind_config)

                # Extract value(s)
                if isinstance(result.values, pd.Series):
                    # Single value indicator
                    latest_value = result.values.iloc[-1] if len(result.values) > 0 else None
                    indicator_values[ind_def.id] = {"value": latest_value}
                elif isinstance(result.values, pd.DataFrame):
                    # Multi-value indicator (e.g., MACD, BB)
                    indicator_values[ind_def.id] = {}
                    for col in result.values.columns:
                        latest_value = result.values[col].iloc[-1] if len(result.values) > 0 else None
                        indicator_values[ind_def.id][col] = latest_value

                    # Add field aliases for user-friendly naming
                    if 'bandwidth' in indicator_values[ind_def.id]:
                        # Alias: bandwidth → width (for BB indicators)
                        indicator_values[ind_def.id]['width'] = indicator_values[ind_def.id]['bandwidth']
                    if ind_config.indicator_type == IndicatorType.MACD:
                        # Normalize MACD column names across TA-Lib / pandas_ta
                        cols = list(indicator_values[ind_def.id].keys())
                        macd_col = next(
                            (c for c in cols if "macd" in c.lower() and "signal" not in c.lower() and "hist" not in c.lower()),
                            None
                        )
                        signal_col = next((c for c in cols if "signal" in c.lower()), None)
                        hist_col = next((c for c in cols if "hist" in c.lower()), None)

                        if macd_col and "macd" not in indicator_values[ind_def.id]:
                            indicator_values[ind_def.id]["macd"] = indicator_values[ind_def.id][macd_col]
                        if signal_col and "signal" not in indicator_values[ind_def.id]:
                            indicator_values[ind_def.id]["signal"] = indicator_values[ind_def.id][signal_col]
                        if hist_col and "histogram" not in indicator_values[ind_def.id]:
                            indicator_values[ind_def.id]["histogram"] = indicator_values[ind_def.id][hist_col]
                        # Backward-compatible alias: value -> macd line
                        if "macd" in indicator_values[ind_def.id] and "value" not in indicator_values[ind_def.id]:
                            indicator_values[ind_def.id]["value"] = indicator_values[ind_def.id]["macd"]
                elif isinstance(result.values, dict):
                    # Dict result (e.g., from custom indicators)
                    indicator_values[ind_def.id] = result.values
                else:
                    logger.warning(
                        f"Unknown result type for {ind_def.id}: {type(result.values)}"
                    )

                logger.debug(f"Calculated {ind_def.id}: {indicator_values[ind_def.id]}")

            except Exception as e:
                logger.error(f"Failed to calculate indicator {ind_def.id}: {e}")
                # Set null value to avoid missing key errors
                indicator_values[ind_def.id] = {"value": None}

        return indicator_values

    def _features_to_indicator_values(
        self,
        features: FeatureVector
    ) -> dict[str, dict[str, float]]:
        """Convert FeatureVector to indicator_values dict.

        Maps common FeatureVector attributes to indicator format.

        Args:
            features: Feature vector

        Returns:
            Dict mapping indicator_id -> {field -> value}
        """
        indicator_values = {}

        # Map common indicators
        mappings = {
            "sma_20": ("sma20", features.sma_20),
            "sma_50": ("sma50", features.sma_50),
            "adx": ("adx14", features.adx),
            "rsi_14": ("rsi14", features.rsi_14),
            "atr_14": ("atr14", features.atr_14),
            "bb_upper": ("bb20", features.bb_upper),
            "bb_lower": ("bb20", features.bb_lower),
            "bb_width": ("bb20", features.bb_width),
            "volume": ("volume", features.volume),
            "volume_sma": ("volume_sma", features.volume_sma),
        }

        for attr_name, (ind_id, value) in mappings.items():
            if value is not None:
                if ind_id not in indicator_values:
                    indicator_values[ind_id] = {}

                # Determine field name
                if attr_name.startswith("bb_"):
                    field = attr_name.replace("bb_", "")  # upper, lower, width
                elif attr_name.startswith("volume_"):
                    field = attr_name.replace("volume_", "") or "value"
                else:
                    field = "value"

                indicator_values[ind_id][field] = value

        # Calculate composite indicators from FeatureVector data
        # These are needed for JSON configs that reference momentum_score, volume_ratio, etc.

        # 1. MOMENTUM_SCORE: Price momentum based on SMA crossovers
        if "sma20" in indicator_values and "sma50" in indicator_values and features.close is not None:
            sma_fast = indicator_values["sma20"].get("value")
            sma_slow = indicator_values["sma50"].get("value")
            close = features.close

            if sma_fast is not None and sma_slow is not None and sma_slow > 0:
                # Component 1: SMA crossover distance (trend strength)
                sma_diff_pct = ((sma_fast - sma_slow) / sma_slow) * 100

                # Component 2: Current price vs Fast SMA (current momentum)
                if sma_fast > 0:
                    price_vs_sma_pct = ((close - sma_fast) / sma_fast) * 100
                    # Combined score (weighted: 60% SMA crossover, 40% price position)
                    momentum_score = (sma_diff_pct * 0.6) + (price_vs_sma_pct * 0.4)
                else:
                    momentum_score = sma_diff_pct

                indicator_values["momentum_score"] = {"value": momentum_score}

        # 2. VOLUME_RATIO: Volume relative to moving average
        if "volume" in indicator_values and "volume_sma" in indicator_values:
            volume = indicator_values["volume"].get("value")
            volume_ma = indicator_values["volume_sma"].get("value")

            if volume is not None and volume_ma is not None and volume_ma > 0:
                volume_ratio = volume / volume_ma
                indicator_values["volume_ratio"] = {"value": volume_ratio}
            else:
                # Neutral ratio if no data
                indicator_values["volume_ratio"] = {"value": 1.0}

        # 3. PRICE_STRENGTH: Complex composite indicator
        # Note: This is a simplified version. For full calculation, use classify_from_config()
        if "momentum_score" in indicator_values and "volume_ratio" in indicator_values:
            momentum = indicator_values["momentum_score"].get("value", 0)
            vol_ratio = indicator_values["volume_ratio"].get("value", 1.0)
            rsi = indicator_values.get("rsi14", {}).get("value", 50)

            # Simplified price strength (weighted combination)
            # Full calculation requires BB position and more indicators
            price_strength = (momentum * 0.5) + ((vol_ratio - 1.0) * 10 * 0.3) + ((rsi - 50) * 0.2)
            indicator_values["price_strength"] = {"value": price_strength}

        # Handle composite BB indicator
        if "bb20" in indicator_values:
            # Add middle band if upper/lower exist
            if "upper" in indicator_values["bb20"] and "lower" in indicator_values["bb20"]:
                upper = indicator_values["bb20"]["upper"]
                lower = indicator_values["bb20"]["lower"]
                if upper is not None and lower is not None:
                    indicator_values["bb20"]["middle"] = (upper + lower) / 2

            # Add width alias for bandwidth (user-friendly naming)
            if "bandwidth" in indicator_values["bb20"]:
                indicator_values["bb20"]["width"] = indicator_values["bb20"]["bandwidth"]
            elif "width" in indicator_values["bb20"]:
                # If width exists but bandwidth doesn't, create reverse alias
                indicator_values["bb20"]["bandwidth"] = indicator_values["bb20"]["width"]

        logger.debug(f"Converted FeatureVector to {len(indicator_values)} indicators")

        return indicator_values

    def _convert_to_regime_state(
        self,
        active_regimes: list,
        indicator_values: dict[str, dict[str, float]],
        timestamp: datetime
    ) -> RegimeState:
        """Convert active regimes to legacy RegimeState format.

        Mapping logic:
        - If "extreme_downtrend" or "extreme_uptrend" active → TREND_DOWN/UP, EXTREME vol
        - If "strong_downtrend" or "strong_uptrend" active → TREND_DOWN/UP, HIGH vol
        - If "moderate_downtrend" or "moderate_uptrend" active → TREND_DOWN/UP, NORMAL vol
        - If "range_bound" active → RANGE, volatility from indicators
        - Else → RANGE, NORMAL

        Args:
            active_regimes: List of ActiveRegime objects
            indicator_values: Calculated indicator values
            timestamp: Current timestamp

        Returns:
            RegimeState
        """
        # Default values
        regime = RegimeType.RANGE
        volatility = VolatilityLevel.NORMAL
        regime_confidence = 0.5
        volatility_confidence = 0.5

        if not active_regimes:
            logger.info("No active regimes → defaulting to RANGE/NORMAL")
            return RegimeState(
                timestamp=timestamp,
                regime=regime,
                volatility=volatility,
                regime_confidence=regime_confidence,
                volatility_confidence=volatility_confidence,
                adx_value=indicator_values.get("adx14", {}).get("value"),
                atr_pct=self._calc_atr_pct_from_indicators(indicator_values),
                bb_width_pct=indicator_values.get("bb20", {}).get("width")
            )

        # Use highest priority regime
        highest = active_regimes[0]
        regime_id = highest.id.lower()

        # Map regime ID to RegimeType
        if "extreme_downtrend" in regime_id:
            regime = RegimeType.TREND_DOWN
            volatility = VolatilityLevel.EXTREME
            regime_confidence = 0.9
            volatility_confidence = 0.85
        elif "extreme_uptrend" in regime_id:
            regime = RegimeType.TREND_UP
            volatility = VolatilityLevel.EXTREME
            regime_confidence = 0.9
            volatility_confidence = 0.85
        elif "strong_downtrend" in regime_id:
            regime = RegimeType.TREND_DOWN
            volatility = VolatilityLevel.HIGH
            regime_confidence = 0.8
            volatility_confidence = 0.75
        elif "strong_uptrend" in regime_id:
            regime = RegimeType.TREND_UP
            volatility = VolatilityLevel.HIGH
            regime_confidence = 0.8
            volatility_confidence = 0.75
        elif "moderate_downtrend" in regime_id or "downtrend" in regime_id:
            regime = RegimeType.TREND_DOWN
            volatility = VolatilityLevel.NORMAL
            regime_confidence = 0.7
            volatility_confidence = 0.65
        elif "moderate_uptrend" in regime_id or "uptrend" in regime_id:
            regime = RegimeType.TREND_UP
            volatility = VolatilityLevel.NORMAL
            regime_confidence = 0.7
            volatility_confidence = 0.65
        elif "range" in regime_id:
            regime = RegimeType.RANGE
            # Determine volatility from indicators
            volume_ratio = indicator_values.get("volume_ratio", {}).get("value")
            if volume_ratio is not None:
                if volume_ratio > 2.5:
                    volatility = VolatilityLevel.EXTREME
                    volatility_confidence = 0.8
                elif volume_ratio > 1.5:
                    volatility = VolatilityLevel.HIGH
                    volatility_confidence = 0.75
                elif volume_ratio < 0.8:
                    volatility = VolatilityLevel.LOW
                    volatility_confidence = 0.7
                else:
                    volatility = VolatilityLevel.NORMAL
                    volatility_confidence = 0.65
            regime_confidence = 0.6

        # Check for high/low volatility regimes
        for active in active_regimes:
            if "high_volatility" in active.id.lower():
                volatility = VolatilityLevel.HIGH
                volatility_confidence = max(volatility_confidence, 0.75)
            elif "low_volatility" in active.id.lower():
                volatility = VolatilityLevel.LOW
                volatility_confidence = max(volatility_confidence, 0.7)

        logger.info(
            f"Mapped {len(active_regimes)} active regime(s) → {regime.name} / {volatility.name} "
            f"(regime_conf={regime_confidence:.2f}, vol_conf={volatility_confidence:.2f})"
        )

        # Prefer the top active regime's id (stable) for labeling
        regime_label = None
        if active_regimes:
            top = active_regimes[0]
            # Use ID primarily (matches JSON), fallback to name
            regime_label = top.id or top.name

        return RegimeState(
            timestamp=timestamp,
            regime=regime,
            volatility=volatility,
            regime_confidence=regime_confidence,
            volatility_confidence=volatility_confidence,
            regime_name=regime_label,
            adx_value=indicator_values.get("adx14", {}).get("value"),
            atr_pct=self._calc_atr_pct_from_indicators(indicator_values),
            bb_width_pct=indicator_values.get("bb20", {}).get("width")
        )

    def _calc_atr_pct_from_indicators(
        self,
        indicator_values: dict[str, dict[str, float]]
    ) -> float | None:
        """Calculate ATR as percentage of price from indicator values.

        Args:
            indicator_values: Dict with indicator values

        Returns:
            ATR% or None if not available
        """
        atr = indicator_values.get("atr14", {}).get("value")

        # Try to get close price from various sources
        close = None
        for key in ["close", "price", "sma20", "sma50"]:
            if key in indicator_values and "value" in indicator_values[key]:
                close = indicator_values[key]["value"]
                break

        if atr is not None and close is not None and close > 0:
            return (atr / close) * 100

        return None

    def get_regime_descriptions(self, config_path: str | Path) -> dict[str, str]:
        """Get descriptions of all regimes in config.

        Args:
            config_path: Path to JSON config

        Returns:
            Dict mapping regime_id -> regime_name
        """
        config = self._load_config(config_path)
        return {regime.id: regime.name for regime in config.regimes}

    def list_required_indicators(self, config_path: str | Path) -> list[str]:
        """List all indicators required by config.

        Args:
            config_path: Path to JSON config

        Returns:
            List of indicator IDs
        """
        config = self._load_config(config_path)
        return [ind.id for ind in config.indicators]
