"""MarketContext Main - Single Source of Truth data model.

Module 6/8 of market_context.py split.

This module contains:
- MarketContext: Canonical market context used by Trading Engine, AI Analysis, Chatbot
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from .market_context_candles import CandleSummary
from .market_context_enums import RegimeType, TrendDirection
from .market_context_indicators import IndicatorSnapshot
from .market_context_levels import LevelsSnapshot
from .market_context_signals import SignalSnapshot

logger = logging.getLogger(__name__)


@dataclass
class MarketContext:
    """
    Kanonischer MarketContext - Single Source of Truth.

    Wird von Trading-Engine, AI Analyse Popup und Chatbot
    identisch verwendet.

    Enthält:
    - Regime + Confidence
    - Multi-Timeframe Trends
    - Indikatoren (via IndicatorSnapshot)
    - Levels (via LevelsSnapshot)
    - Aktives Signal (via SignalSnapshot)
    - Candle-Daten (via CandleSummary)

    Wird pro Symbol/Timeframe erzeugt und gecached.
    """

    # === IDENTIFIKATION ===
    symbol: str
    timeframe: str  # Primary timeframe
    timestamp: datetime
    context_id: str = ""  # Unique Hash für Caching/Audit

    # === REGIME ===
    regime: RegimeType = RegimeType.NEUTRAL
    regime_confidence: float = 0.0  # 0-1
    regime_reason: str | None = None  # z.B. "EMA20 > EMA50, ADX > 30"

    # === MULTI-TIMEFRAME TRENDS ===
    trend_1d: TrendDirection | None = None
    trend_4h: TrendDirection | None = None
    trend_1h: TrendDirection | None = None
    trend_15m: TrendDirection | None = None
    trend_5m: TrendDirection | None = None

    # Trend-Alignment Score (-1 bis +1)
    mtf_alignment_score: float = 0.0
    mtf_aligned: bool = False  # Alle TFs in gleicher Richtung

    # === INDIKATOR SNAPSHOTS ===
    indicators_5m: IndicatorSnapshot | None = None
    indicators_1h: IndicatorSnapshot | None = None
    indicators_4h: IndicatorSnapshot | None = None
    indicators_1d: IndicatorSnapshot | None = None

    # === LEVELS ===
    levels: LevelsSnapshot | None = None

    # Quick Access
    nearest_support: float | None = None
    nearest_resistance: float | None = None
    distance_to_support_pct: float | None = None
    distance_to_resistance_pct: float | None = None

    # === AKTIVES SIGNAL ===
    signal: SignalSnapshot | None = None

    # === CANDLE DATA ===
    current_candle: CandleSummary | None = None
    previous_candles: list[CandleSummary] = field(default_factory=list)

    # === PRICE & VOLATILITY ===
    current_price: float = 0.0
    price_24h_change_pct: float = 0.0
    atr_pct: float = 0.0  # ATR als % vom Preis
    volatility_state: str = "NORMAL"  # LOW, NORMAL, HIGH, EXTREME

    # === DATA QUALITY ===
    data_fresh: bool = True
    data_freshness_seconds: int = 0
    data_quality_issues: list[str] = field(default_factory=list)

    # === METADATA ===
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    ttl_seconds: int = 60  # Cache TTL
    source: str = "market_context_builder"

    def __post_init__(self) -> None:
        """Generiere Context-ID falls nicht gesetzt."""
        if not self.context_id:
            self.context_id = self._generate_context_id()

    def _generate_context_id(self) -> str:
        """
        Generiert einzigartigen Hash für diesen Context.

        Basiert auf Symbol, TF, Timestamp und Key-Werten.
        """
        key_data = {
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "timestamp": self.timestamp.isoformat() if self.timestamp else "",
            "regime": self.regime.value if isinstance(self.regime, RegimeType) else self.regime,
            "price": self.current_price,
        }
        hash_str = json.dumps(key_data, sort_keys=True)
        return hashlib.sha256(hash_str.encode()).hexdigest()[:16]

    def to_dict(self) -> dict[str, Any]:
        """
        Konvertiert zu Dictionary (für JSON Export/AI Prompts).
        """
        import numpy as np
        import pandas as pd

        def convert_value(v: Any) -> Any:
            # Handle pandas Timestamp first (before datetime check)
            if isinstance(v, pd.Timestamp):
                return v.isoformat()
            if isinstance(v, datetime):
                return v.isoformat()
            if isinstance(v, Enum):
                return v.value
            # Handle numpy types
            if isinstance(v, (np.integer, np.floating)):
                return v.item()
            if isinstance(v, np.ndarray):
                return v.tolist()
            if hasattr(v, "to_dict"):
                return v.to_dict()
            if isinstance(v, dict):
                return {k: convert_value(val) for k, val in v.items()}
            if isinstance(v, list):
                return [convert_value(item) for item in v]
            return v

        result = {}
        for key, value in asdict(self).items():
            result[key] = convert_value(value)

        return result

    def to_json(self, indent: int = 2) -> str:
        """Konvertiert zu JSON String."""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    def to_ai_prompt_context(self) -> dict:
        """
        Erzeugt kompaktes Context-Dict für AI Prompts.

        Enthält nur die relevanten Felder, keine Rohdaten.
        """
        return {
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "current_price": self.current_price,
            "regime": {
                "type": self.regime.value if isinstance(self.regime, RegimeType) else self.regime,
                "confidence": self.regime_confidence,
                "reason": self.regime_reason,
            },
            "trends": {
                "1d": self.trend_1d.value if self.trend_1d else None,
                "4h": self.trend_4h.value if self.trend_4h else None,
                "1h": self.trend_1h.value if self.trend_1h else None,
                "5m": self.trend_5m.value if self.trend_5m else None,
                "alignment_score": self.mtf_alignment_score,
                "aligned": self.mtf_aligned,
            },
            "levels": {
                "nearest_support": self.nearest_support,
                "nearest_resistance": self.nearest_resistance,
                "distance_to_support_pct": self.distance_to_support_pct,
                "distance_to_resistance_pct": self.distance_to_resistance_pct,
            },
            "volatility": {
                "atr_pct": self.atr_pct,
                "state": self.volatility_state,
            },
            "indicators_5m": self._get_key_indicators(self.indicators_5m),
            "signal": self._get_signal_summary(),
            "data_quality": {
                "fresh": self.data_fresh,
                "issues": self.data_quality_issues,
            },
        }

    def _get_key_indicators(self, snapshot: IndicatorSnapshot | None) -> dict | None:
        """Extrahiert Key-Indikatoren aus Snapshot."""
        if not snapshot:
            return None
        return {
            "rsi": snapshot.rsi_14,
            "rsi_state": snapshot.rsi_state,
            "macd_crossover": snapshot.macd_crossover,
            "adx": snapshot.adx_14,
            "bb_pct_b": snapshot.bb_pct_b,
            "volume_ratio": snapshot.volume_ratio,
        }

    def _get_signal_summary(self) -> dict | None:
        """Extrahiert Signal-Zusammenfassung."""
        if not self.signal:
            return None
        return {
            "direction": self.signal.direction.value,
            "strength": self.signal.strength.value,
            "entry_score": self.signal.entry_score,
            "confluence_score": self.signal.confluence_score,
            "setup_type": self.signal.setup_type.value,
            "regime_allows_entry": self.signal.regime_allows_entry,
            "is_tradeable": self.signal.is_tradeable,
        }

    def is_valid_for_trading(self) -> tuple[bool, list[str]]:
        """
        Prüft ob Context für Trading geeignet ist.

        Returns:
            Tuple von (is_valid, list_of_issues)
        """
        issues = []

        # Data Quality
        if not self.data_fresh:
            issues.append(f"Data not fresh ({self.data_freshness_seconds}s old)")

        if self.data_quality_issues:
            issues.extend(self.data_quality_issues)

        # Price Sanity
        if self.current_price <= 0:
            issues.append("Invalid current price")

        # Indicators vorhanden
        if not self.indicators_5m:
            issues.append("Missing 5m indicators")

        # Regime bekannt
        if self.regime == RegimeType.NEUTRAL and self.regime_confidence < 0.5:
            issues.append("Regime unclear")

        return len(issues) == 0, issues

    @property
    def is_bullish_regime(self) -> bool:
        """Prüft ob bullishes Regime."""
        return self.regime in [RegimeType.STRONG_TREND_BULL, RegimeType.WEAK_TREND_BULL]

    @property
    def is_bearish_regime(self) -> bool:
        """Prüft ob bearishes Regime."""
        return self.regime in [RegimeType.STRONG_TREND_BEAR, RegimeType.WEAK_TREND_BEAR]

    @property
    def is_ranging_regime(self) -> bool:
        """Prüft ob Range/Chop Regime."""
        return self.regime == RegimeType.CHOP_RANGE
