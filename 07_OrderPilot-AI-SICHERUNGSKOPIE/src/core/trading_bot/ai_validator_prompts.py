"""AI Validator Prompts - Prompt-Builder für Quick und Deep Analysis.

Refactored from 852 LOC monolith using composition pattern.

Module 2/5 of ai_validator.py split.

Contains:
- _build_prompt(): Baut Quick Validation Prompt
- _build_deep_prompt(): Baut Deep Analysis Prompt mit OHLCV-Daten
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

import pandas as pd

if TYPE_CHECKING:
    from .signal_generator import TradeSignal
    from .trade_logger import IndicatorSnapshot, MarketContext

logger = logging.getLogger(__name__)


class AIValidatorPrompts:
    """Prompt-Builder für AI-Validierung."""

    # Setup-Typen die erkannt werden können
    SETUP_TYPES = [
        "PULLBACK_EMA20",
        "PULLBACK_EMA50",
        "BREAKOUT",
        "BREAKDOWN",
        "MEAN_REVERSION",
        "TREND_CONTINUATION",
        "SWING_FAILURE",
        "ABSORPTION",
        "DIVERGENCE",
        "NO_SETUP",
    ]

    def __init__(self, parent):
        """
        Args:
            parent: AISignalValidator Instanz
        """
        self.parent = parent

    def build_prompt(
        self,
        signal: "TradeSignal",
        indicators: "IndicatorSnapshot | None",
        market_context: "MarketContext | None",
    ) -> str:
        """Erstellt den LLM-Prompt für Quick Validation."""
        # Signal Info
        signal_info = {
            "direction": signal.direction.value,
            "confluence_score": signal.confluence_score,
            "strength": signal.strength.value if hasattr(signal, "strength") else "UNKNOWN",
            "current_price": signal.current_price,
            "regime": signal.regime,
        }

        # Conditions
        conditions_met = [
            {"name": c.name, "description": c.description}
            for c in signal.conditions_met
        ]
        conditions_failed = [
            {"name": c.name, "description": c.description}
            for c in signal.conditions_failed
        ]

        # Indicators
        indicator_data = {}
        if indicators:
            indicator_data = {
                "rsi": indicators.rsi_14,
                "rsi_state": indicators.rsi_state,
                "ema_20": indicators.ema_20,
                "ema_50": indicators.ema_50,
                "ema_200": indicators.ema_200,
                "ema_20_distance_pct": indicators.ema_20_distance_pct,
                "macd_line": indicators.macd_line,
                "macd_signal": indicators.macd_signal,
                "macd_crossover": indicators.macd_crossover,
                "atr": indicators.atr_14,
                "atr_percent": indicators.atr_percent,
                "adx": indicators.adx_14,
                "bb_pct_b": indicators.bb_pct_b,
            }

        # Market Context
        context_data = {}
        if market_context:
            context_data = {
                "regime": market_context.regime,
                "trend_1d": market_context.trend_1d,
                "trend_4h": market_context.trend_4h,
                "trend_1h": market_context.trend_1h,
                "nearest_support": market_context.nearest_support,
                "nearest_resistance": market_context.nearest_resistance,
            }

        prompt = f"""Du bist ein erfahrener Crypto-Trading-Analyst. Analysiere dieses Trading-Signal und gib eine Bewertung ab.

## Signal Details
{json.dumps(signal_info, indent=2)}

## Erfüllte Bedingungen ({len(conditions_met)}/{len(conditions_met) + len(conditions_failed)})
{json.dumps(conditions_met, indent=2)}

## Nicht erfüllte Bedingungen
{json.dumps(conditions_failed, indent=2)}

## Technische Indikatoren
{json.dumps(indicator_data, indent=2)}

## Marktkontext
{json.dumps(context_data, indent=2)}

## Deine Aufgabe
1. Bewerte die Qualität dieses {signal.direction.value} Signals
2. Identifiziere den Setup-Typ
3. Gib einen Confidence Score (0-100)
4. Erkläre kurz dein Reasoning

## Antwort-Format (JSON)
{{
    "confidence_score": <0-100>,
    "setup_type": "<einer von: {', '.join(self.SETUP_TYPES)}>",
    "approved": <true/false>,
    "reasoning": "<kurze Erklärung>"
}}

Antworte NUR mit dem JSON, ohne weitere Erklärung."""

        return prompt

    def build_deep_prompt(
        self,
        signal: "TradeSignal",
        indicators: "IndicatorSnapshot | None",
        market_context: "MarketContext | None",
        ohlcv_data: pd.DataFrame | None,
    ) -> str:
        """Erstellt ausführlichen Deep Analysis Prompt."""
        # Basis-Prompt
        base_prompt = self.build_prompt(signal, indicators, market_context)

        # Zusätzliche OHLCV-Analyse
        ohlcv_analysis = ""
        if ohlcv_data is not None and len(ohlcv_data) > 0:
            last_10 = ohlcv_data.tail(10)
            candle_data = []
            for idx, row in last_10.iterrows():
                candle_data.append({
                    "time": str(idx),
                    "open": round(row.get("open", 0), 2),
                    "high": round(row.get("high", 0), 2),
                    "low": round(row.get("low", 0), 2),
                    "close": round(row.get("close", 0), 2),
                    "volume": round(row.get("volume", 0), 2) if "volume" in row else 0,
                })

            ohlcv_analysis = f"""

## Letzte 10 Kerzen (OHLCV)
{json.dumps(candle_data, indent=2)}

## Zusätzliche Analyse-Anforderungen (Deep Analysis)
1. Analysiere die Kerzenformationen der letzten 10 Kerzen
2. Identifiziere Unterstützungs- und Widerstandsniveaus
3. Bewerte das Momentum und die Volatilität
4. Prüfe auf Divergenzen zwischen Preis und Indikatoren
5. Gib eine detailliertere Einschätzung der Wahrscheinlichkeit
"""

        deep_prompt = f"""{base_prompt}
{ohlcv_analysis}

WICHTIG: Dies ist eine DEEP ANALYSIS. Sei besonders gründlich und konservativ.
Genehmige nur Signale mit hoher Überzeugung (>= 70% Confidence).
Bei Unsicherheit: Lieber ablehnen als ein schlechtes Signal durchlassen."""

        return deep_prompt
