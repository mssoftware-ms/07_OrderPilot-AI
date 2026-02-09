"""JSON Entry Loader - Lädt Regime + Indicator JSON für Entry-Steuerung.

Kombiniert Regime JSON (v2.0) + optionale Indicator JSON zu einer
einheitlichen Entry-Config für JSON-basierte Entry-Logik.

Verwendet:
- Regime JSON: Regimes, Thresholds, Entry Expression
- Indicator JSON: Indicator-Definitionen (optional)

Author: Claude Code
Date: 2026-01-28
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class JsonEntryConfigError(Exception):
    """Exception raised when JSON Entry Config loading fails."""
    pass


@dataclass
class JsonEntryConfig:
    """Configuration für JSON-basiertes Entry.

    Kombiniert Indicator JSON + Regime JSON + CEL Expression für
    JSON-basierte Entry-Entscheidungen im Trading Bot.

    Attributes:
        regime_json_path: Pfad zur Regime JSON-Datei
        indicator_json_path: Pfad zur Indicator JSON-Datei (optional)
        entry_expression: CEL Expression für Entry (aus Regime JSON)
        indicators: Dict mit Indicator-Definitionen
        regime_thresholds: Dict mit Regime-Schwellenwerten
        metadata: Optional metadata aus Regime JSON
    """

    regime_json_path: str
    indicator_json_path: str | None
    entry_expression: str
    entry_enabled: bool = True
    entry_errors: list[str] = field(default_factory=list)
    indicators: dict[str, Any] = field(default_factory=dict)
    regime_thresholds: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_files(
        cls,
        regime_json_path: str,
        indicator_json_path: str | None = None,
        entry_expression_override: str | None = None,
    ) -> "JsonEntryConfig":
        """Lädt Regime + Indicator JSON und erstellt Entry-Config.

        Args:
            regime_json_path: Pfad zur Regime JSON (v2.0 Format)
            indicator_json_path: Pfad zur Indicator JSON (optional)
            entry_expression_override: Überschreibt entry_expression aus JSON

        Returns:
            JsonEntryConfig mit kombinierten Daten

        Raises:
            JsonEntryConfigError: Wenn JSON-Datei nicht gefunden oder ungültig
            FileNotFoundError: Wenn Datei nicht existiert
            json.JSONDecodeError: Wenn JSON-Format ungültig

        Example:
            >>> config = JsonEntryConfig.from_files(
            ...     regime_json_path="03_JSON/Entry_Analyzer/Regime/my_regime.json",
            ...     indicator_json_path="03_JSON/Entry_Analyzer/Indicators/my_indicators.json"
            ... )
            >>> print(config.entry_expression)
            'rsi < 35 && adx > 25 && macd_hist > 0'
        """
        # 1. Lade Regime JSON
        regime_path = Path(regime_json_path)
        if not regime_path.exists():
            raise FileNotFoundError(
                f"Regime JSON nicht gefunden: {regime_path}\n"
                f"Prüfe Pfad relativ zum Working Directory."
            )

        try:
            with open(regime_path, "r", encoding="utf-8") as f:
                regime_data = json.load(f)
        except json.JSONDecodeError as e:
            raise JsonEntryConfigError(
                f"Invalid JSON in Regime file {regime_path.name}: {e}"
            ) from e
        except Exception as e:
            raise JsonEntryConfigError(
                f"Failed to load Regime JSON {regime_path.name}: {e}"
            ) from e

        logger.info(f"Loaded Regime JSON: {regime_path.name}")

        # 2. Lade Indicator JSON (optional)
        indicator_data = None
        indicator_path = None
        if indicator_json_path:
            indicator_path = Path(indicator_json_path)
            if not indicator_path.exists():
                raise FileNotFoundError(
                    f"Indicator JSON nicht gefunden: {indicator_path}\n"
                    f"Prüfe Pfad relativ zum Working Directory."
                )

            try:
                with open(indicator_path, "r", encoding="utf-8") as f:
                    indicator_data = json.load(f)
            except json.JSONDecodeError as e:
                raise JsonEntryConfigError(
                    f"Invalid JSON in Indicator file {indicator_path.name}: {e}"
                ) from e
            except Exception as e:
                raise JsonEntryConfigError(
                    f"Failed to load Indicator JSON {indicator_path.name}: {e}"
                ) from e

        return cls.from_data(
            regime_data=regime_data,
            regime_json_path=str(regime_path),
            indicator_data=indicator_data,
            indicator_json_path=str(indicator_path) if indicator_json_path else None,
            entry_expression_override=entry_expression_override,
        )

    @classmethod
    def from_data(
        cls,
        regime_data: dict[str, Any],
        regime_json_path: str,
        indicator_data: dict[str, Any] | None = None,
        indicator_json_path: str | None = None,
        entry_expression_override: str | None = None,
    ) -> "JsonEntryConfig":
        """Erstellt Entry-Config aus bereits geladenen JSON-Daten.

        Fail-closed: Missing entry_expression => entry_enabled = False.
        """
        indicators = {}
        if indicator_data:
            indicators = indicator_data.get("indicators", {})
            logger.info(
                "Loaded Indicator JSON data (%d indicators)",
                len(indicators) if hasattr(indicators, "__len__") else 0,
            )

        # 3. Kombiniere Indicators (Indicator JSON hat Vorrang)
        # Unterstützt beide Formate:
        # - Direkt: {"indicators": {...}} (Dict)
        # - Entry Analyzer: {"optimization_results": [{"indicators": [...]}]} (List)
        regime_indicators = regime_data.get("indicators", {})

        # Konvertiere auch regime_indicators zu Dict, falls Liste (JSON v2.0 Standard)
        if isinstance(regime_indicators, list):
            regime_indicators = {
                ind.get("id", ind.get("name", f"indicator_{i}")): ind
                for i, ind in enumerate(regime_indicators)
            }

        if not regime_indicators and "optimization_results" in regime_data:
            # Fallback: Lade aus optimization_results[0].indicators
            opt_results = regime_data.get("optimization_results", [])
            if opt_results and len(opt_results) > 0:
                regime_indicators_raw = opt_results[0].get("indicators", [])

                # Konvertiere Liste → Dict (name als Key)
                if isinstance(regime_indicators_raw, list):
                    regime_indicators = {
                        ind.get("name", f"indicator_{i}"): ind
                        for i, ind in enumerate(regime_indicators_raw)
                    }
                    logger.info(
                        f"Indicators aus optimization_results[0] geladen: "
                        f"{len(regime_indicators)} indicators"
                    )
                else:
                    # Falls es schon ein Dict ist
                    regime_indicators = regime_indicators_raw

        # Konvertiere indicators auch falls es eine Liste ist
        if isinstance(indicators, list):
            indicators = {
                ind.get("name", f"indicator_{i}"): ind
                for i, ind in enumerate(indicators)
            }

        combined_indicators = {**regime_indicators, **indicators}

        if len(indicators) > 0:
            logger.debug(
                f"Combined indicators: {len(regime_indicators)} from Regime + "
                f"{len(indicators)} from Indicator JSON = {len(combined_indicators)} total"
            )

        # 4. Extrahiere Entry Expression
        entry_expr = entry_expression_override or regime_data.get("entry_expression")
        entry_expr = entry_expr if isinstance(entry_expr, str) else ""

        entry_enabled = bool(entry_expr.strip())
        entry_errors: list[str] = []
        if not entry_enabled:
            logger.warning(
                "ENTRY_EXPRESSION_MISSING: Keine 'entry_expression' in Regime JSON gefunden. "
                "Entry wird deaktiviert (fail-closed)."
            )
            entry_errors.append("ENTRY_EXPRESSION_MISSING")

        # 5. Extrahiere Regime Thresholds
        # Unterstützt beide Formate:
        # - Direkt: {"regimes": {...}} (Dict)
        # - Entry Analyzer: {"optimization_results": [{"regimes": [...]}]} (List)
        regime_thresholds = regime_data.get("regimes", {})

        if not regime_thresholds and "optimization_results" in regime_data:
            # Fallback: Lade aus optimization_results[0].regimes
            opt_results = regime_data.get("optimization_results", [])
            if opt_results and len(opt_results) > 0:
                regime_thresholds_raw = opt_results[0].get("regimes", [])

                # Konvertiere Liste → Dict (id als Key)
                if isinstance(regime_thresholds_raw, list):
                    regime_thresholds = {
                        regime.get("id", f"regime_{i}"): regime
                        for i, regime in enumerate(regime_thresholds_raw)
                    }
                    logger.info(
                        f"Regimes aus optimization_results[0] geladen: "
                        f"{len(regime_thresholds)} regimes (Entry Analyzer Format)"
                    )
                else:
                    # Falls es schon ein Dict ist
                    regime_thresholds = regime_thresholds_raw

        # 6. Extrahiere Metadata (optional)
        metadata = regime_data.get("metadata", {})

        # Log summary
        logger.info(
            f"JSON Entry Config loaded: "
            f"{len(combined_indicators)} indicators, "
            f"{len(regime_thresholds)} regimes, "
            f"entry_enabled: {entry_enabled}, "
            f"expression length: {len(entry_expr)}"
        )

        return cls(
            regime_json_path=regime_json_path,
            indicator_json_path=indicator_json_path,
            entry_expression=entry_expr,
            entry_enabled=entry_enabled,
            entry_errors=entry_errors,
            indicators=combined_indicators,
            regime_thresholds=regime_thresholds,
            metadata=metadata,
        )

    def validate(self) -> list[str]:
        """Validiere Config und gebe Warnings zurück.

        Führt einfache Plausibilitäts-Checks durch.
        Vollständige CEL Expression Validierung erfolgt in JsonEntryScorer.

        Returns:
            Liste von Warning-Strings (leer wenn alles ok)

        Example:
            >>> warnings = config.validate()
            >>> if warnings:
            ...     for warning in warnings:
            ...         print(f"⚠️ {warning}")
        """
        warnings = []

        # Check 1: Entry Expression vorhanden
        if not self.entry_enabled:
            warnings.append("ENTRY_EXPRESSION_MISSING: Entry disabled (fail-closed)")

        # Check 2: Entry Expression ist immer-true
        if self.entry_enabled and self.entry_expression.strip().lower() == "true":
            warnings.append(
                "Entry Expression ist 'true' - jeder Bar triggert Entry Signal "
                "(möglicherweise nicht beabsichtigt)"
            )

        # Check 3: Mindestens 1 Indicator definiert
        if not self.indicators:
            warnings.append(
                "Keine Indicators definiert - Entry Expression kann keine "
                "Indicator-Werte verwenden"
            )

        # Check 4: Entry Expression referenziert definierte Indicators (simple check)
        # Vollständige Validierung erfolgt in JsonEntryScorer via CEL compilation
        if self.indicators:
            unused_indicators = []
            for indicator_id in self.indicators.keys():
                # Simple substring check (nicht perfekt, aber gut genug für Warning)
                if indicator_id not in self.entry_expression:
                    unused_indicators.append(indicator_id)

            if unused_indicators and len(unused_indicators) < len(self.indicators):
                # Nur warnen wenn einige (nicht alle) Indicators ungenutzt
                warnings.append(
                    f"Indicators nicht in Entry Expression verwendet: "
                    f"{', '.join(unused_indicators[:3])}"
                    f"{' ...' if len(unused_indicators) > 3 else ''}"
                )

        # Check 5: Regime Thresholds definiert
        if not self.regime_thresholds:
            warnings.append(
                "Keine Regime Thresholds definiert - "
                "Regime-basierte Entry-Logik möglicherweise nicht verfügbar"
            )

        return warnings

    def get_indicator_ids(self) -> list[str]:
        """Gibt Liste aller Indicator-IDs zurück.

        Returns:
            Liste von Indicator-IDs (z.B. ["rsi14", "adx14", "macd"])

        Example:
            >>> ids = config.get_indicator_ids()
            >>> print(ids)
            ['rsi14', 'adx14', 'macd']
        """
        return list(self.indicators.keys())

    def get_regime_ids(self) -> list[str]:
        """Gibt Liste aller Regime-IDs zurück.

        Returns:
            Liste von Regime-IDs (z.B. ["EXTREME_BULL", "TREND_UP"])

        Example:
            >>> ids = config.get_regime_ids()
            >>> print(ids)
            ['EXTREME_BULL', 'TREND_UP', 'NEUTRAL']
        """
        return list(self.regime_thresholds.keys())

    def __str__(self) -> str:
        """String representation für Logging."""
        return (
            f"JsonEntryConfig("
            f"indicators={len(self.indicators)}, "
            f"regimes={len(self.regime_thresholds)}, "
            f"expression_len={len(self.entry_expression)}"
            f")"
        )

    def __repr__(self) -> str:
        """Detailed representation für Debugging."""
        return (
            f"JsonEntryConfig(\n"
            f"  regime_json={Path(self.regime_json_path).name},\n"
            f"  indicator_json={Path(self.indicator_json_path).name if self.indicator_json_path else None},\n"
            f"  entry_expression='{self.entry_expression[:50]}...',\n"
            f"  indicators={list(self.indicators.keys())},\n"
            f"  regimes={list(self.regime_thresholds.keys())}\n"
            f")"
        )
