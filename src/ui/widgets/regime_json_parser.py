"""Regime JSON Parser - Parst Entry Analyzer Regime JSON Dateien.

Extrahiert Regime-Definitionen und Entry Expression aus JSON.
Verwendet für Regime Entry Expression Editor.

Author: Claude Code
Date: 2026-01-29
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class RegimeInfo:
    """Information über ein einzelnes Regime."""

    id: str  # z.B. "STRONG_BULL"
    name: str  # z.B. "Starker Aufwärtstrend"
    priority: int  # z.B. 95
    scope: str  # z.B. "entry"
    thresholds: list[dict[str, Any]]  # Threshold-Definitionen

    def __str__(self) -> str:
        return f"{self.id} - {self.name} (Priority: {self.priority})"

    @property
    def display_name(self) -> str:
        """Display-Name für UI."""
        return f"{self.id} ({self.priority})"


@dataclass
class RegimeJsonData:
    """Geparste Daten aus Regime JSON."""

    file_path: str
    regimes: list[RegimeInfo]
    has_entry_expression: bool
    current_expression: str | None
    indicators: list[dict[str, Any]]
    metadata: dict[str, Any]

    @property
    def regime_ids(self) -> list[str]:
        """Liste aller Regime-IDs."""
        return [r.id for r in self.regimes]

    @property
    def regime_by_id(self) -> dict[str, RegimeInfo]:
        """Dict mit Regime-ID als Key."""
        return {r.id: r for r in self.regimes}

    def get_bull_regimes(self) -> list[RegimeInfo]:
        """Gibt alle Bull-Regimes zurück (heuristisch)."""
        return [
            r for r in self.regimes
            if "BULL" in r.id.upper() and "BEAR" not in r.id.upper()
        ]

    def get_bear_regimes(self) -> list[RegimeInfo]:
        """Gibt alle Bear-Regimes zurück (heuristisch)."""
        return [r for r in self.regimes if "BEAR" in r.id.upper()]

    def get_neutral_regimes(self) -> list[RegimeInfo]:
        """Gibt neutrale Regimes zurück (heuristisch)."""
        bull_bear_ids = {r.id for r in self.get_bull_regimes() + self.get_bear_regimes()}
        return [r for r in self.regimes if r.id not in bull_bear_ids]


class RegimeJsonParser:
    """Parser für Entry Analyzer Regime JSON Dateien."""

    @staticmethod
    def parse(json_path: str | Path) -> RegimeJsonData:
        """Parst Regime JSON und extrahiert relevante Daten.

        Args:
            json_path: Pfad zur Regime JSON Datei

        Returns:
            RegimeJsonData mit allen extrahierten Informationen

        Raises:
            FileNotFoundError: Wenn Datei nicht existiert
            json.JSONDecodeError: Wenn JSON ungültig
            ValueError: Wenn JSON-Schema nicht kompatibel
        """
        path = Path(json_path)
        if not path.exists():
            raise FileNotFoundError(f"Regime JSON nicht gefunden: {path}")

        logger.info(f"Parsing Regime JSON: {path.name}")

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(
                f"Invalid JSON in {path.name}: {e.msg}",
                e.doc,
                e.pos
            )

        # Validiere Schema-Version
        schema_version = data.get("schema_version", "unknown")
        if not schema_version.startswith("2."):
            logger.warning(
                f"Schema version {schema_version} might not be compatible. "
                "Expected 2.x.x"
            )

        # Extrahiere Metadata
        metadata = data.get("metadata", {})

        # Extrahiere Entry Expression (falls vorhanden)
        has_entry_expression = "entry_expression" in data
        current_expression = data.get("entry_expression")

        # Extrahiere Optimization Results
        optimization_results = data.get("optimization_results", [])
        if not optimization_results:
            raise ValueError(
                f"Keine optimization_results in {path.name} gefunden. "
                "JSON muss mindestens ein Optimization Result enthalten."
            )

        # Nimm das erste (und meist einzige) Optimization Result
        first_result = optimization_results[0]

        # Extrahiere Indicators
        indicators = first_result.get("indicators", [])

        # Extrahiere Regimes
        regimes_raw = first_result.get("regimes", [])
        if not regimes_raw:
            raise ValueError(
                f"Keine regimes in {path.name} gefunden. "
                "JSON muss Regime-Definitionen enthalten."
            )

        # Parse Regimes zu RegimeInfo-Objekten
        regimes = []
        for regime_data in regimes_raw:
            try:
                regime = RegimeInfo(
                    id=regime_data["id"],
                    name=regime_data.get("name", regime_data["id"]),
                    priority=regime_data.get("priority", 50),
                    scope=regime_data.get("scope", "entry"),
                    thresholds=regime_data.get("thresholds", [])
                )
                regimes.append(regime)
            except KeyError as e:
                logger.warning(
                    f"Skipping regime without required field {e} in {path.name}"
                )
                continue

        # Sortiere Regimes nach Priority (höchste zuerst)
        regimes.sort(key=lambda r: r.priority, reverse=True)

        logger.info(
            f"Parsed {len(regimes)} regimes from {path.name}. "
            f"Entry expression present: {has_entry_expression}"
        )

        return RegimeJsonData(
            file_path=str(path),
            regimes=regimes,
            has_entry_expression=has_entry_expression,
            current_expression=current_expression,
            indicators=indicators,
            metadata=metadata
        )

    @staticmethod
    def validate_json_structure(json_path: str | Path) -> tuple[bool, str]:
        """Validiert JSON-Struktur ohne vollständiges Parsing.

        Args:
            json_path: Pfad zur JSON

        Returns:
            (is_valid, error_message) - error_message ist leer wenn valid
        """
        try:
            RegimeJsonParser.parse(json_path)
            return True, ""
        except FileNotFoundError as e:
            return False, f"Datei nicht gefunden: {e}"
        except json.JSONDecodeError as e:
            return False, f"Ungültiges JSON: {e.msg}"
        except ValueError as e:
            return False, f"Schema-Fehler: {e}"
        except Exception as e:
            return False, f"Unbekannter Fehler: {e}"


# Convenience Functions

def load_regime_json(json_path: str | Path) -> RegimeJsonData:
    """Convenience-Funktion zum Laden von Regime JSON."""
    return RegimeJsonParser.parse(json_path)


def get_regime_names(json_path: str | Path) -> list[str]:
    """Extrahiert nur Regime-Namen aus JSON."""
    data = RegimeJsonParser.parse(json_path)
    return data.regime_ids
