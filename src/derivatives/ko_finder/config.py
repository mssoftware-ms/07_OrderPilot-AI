"""
Konfiguration für den KO-Finder.

Enthält:
- KOFilterConfig: User-Parameter für Suche/Filter
- Validierung und Defaults
- Persistenz-Helpers (QSettings)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from .constants import (
    DEFAULT_BROKER_ID,
    DEFAULT_MAX_SPREAD_PCT,
    DEFAULT_MIN_KO_DISTANCE_PCT,
    DEFAULT_MIN_LEVERAGE,
    DEFAULT_TOP_N,
    Issuer,
)

if TYPE_CHECKING:
    from PyQt6.QtCore import QSettings


@dataclass
class KOFilterConfig:
    """
    Konfiguration für KO-Produkt-Suche und -Filter.

    Alle Parameter werden validiert und haben sinnvolle Defaults.
    HINWEIS: Dies ist keine Anlageberatung!
    """

    # Mindesthebel (Produkte mit niedrigerem Hebel werden ausgeschlossen)
    min_leverage: float = DEFAULT_MIN_LEVERAGE

    # Maximaler Spread in Prozent
    max_spread_pct: float = DEFAULT_MAX_SPREAD_PCT

    # Minimaler KO-Abstand in Prozent (Sicherheitspuffer)
    min_ko_distance_pct: float = DEFAULT_MIN_KO_DISTANCE_PCT

    # Anzahl Top-Ergebnisse je Richtung
    top_n: int = DEFAULT_TOP_N

    # Erlaubte Emittenten
    issuers: list[Issuer] = field(default_factory=lambda: list(Issuer))

    # Broker-ID für Onvista-Filter (optional)
    broker_id: int | None = DEFAULT_BROKER_ID

    # Feature-Filter (z.B. STOP_LOSS) - deaktiviert, da nicht in Standard-URLs
    feature: str | None = None

    def __post_init__(self) -> None:
        """Validiere alle Parameter nach Initialisierung."""
        self._validate()

    def _validate(self) -> None:
        """Validiere Konfigurationswerte."""
        if self.min_leverage < 0:
            raise ValueError(f"min_leverage muss >= 0 sein, war: {self.min_leverage}")

        if self.max_spread_pct < 0:
            raise ValueError(
                f"max_spread_pct muss >= 0 sein, war: {self.max_spread_pct}"
            )

        if self.min_ko_distance_pct < 0:
            raise ValueError(
                f"min_ko_distance_pct muss >= 0 sein, war: {self.min_ko_distance_pct}"
            )

        if self.top_n < 1:
            raise ValueError(f"top_n muss >= 1 sein, war: {self.top_n}")

        if not self.issuers:
            raise ValueError("Mindestens ein Issuer muss ausgewählt sein")

    @property
    def issuer_ids_str(self) -> str:
        """Kommaseparierte Issuer-IDs für URL."""
        return ",".join(str(issuer.value) for issuer in self.issuers)

    def to_dict(self) -> dict:
        """Konvertiere zu Dictionary für Serialisierung."""
        return {
            "min_leverage": self.min_leverage,
            "max_spread_pct": self.max_spread_pct,
            "min_ko_distance_pct": self.min_ko_distance_pct,
            "top_n": self.top_n,
            "issuer_ids": [issuer.value for issuer in self.issuers],
            "broker_id": self.broker_id,
            "feature": self.feature,
        }

    @classmethod
    def from_dict(cls, data: dict) -> KOFilterConfig:
        """Erstelle Config aus Dictionary."""
        issuer_ids = data.get("issuer_ids", [i.value for i in Issuer])
        issuers = [Issuer(id_) for id_ in issuer_ids if id_ in [i.value for i in Issuer]]

        return cls(
            min_leverage=data.get("min_leverage", DEFAULT_MIN_LEVERAGE),
            max_spread_pct=data.get("max_spread_pct", DEFAULT_MAX_SPREAD_PCT),
            min_ko_distance_pct=data.get(
                "min_ko_distance_pct", DEFAULT_MIN_KO_DISTANCE_PCT
            ),
            top_n=data.get("top_n", DEFAULT_TOP_N),
            issuers=issuers or list(Issuer),
            broker_id=data.get("broker_id", DEFAULT_BROKER_ID),
            feature=data.get("feature", "STOP_LOSS"),
        )

    def save_to_qsettings(self, settings: QSettings, prefix: str = "ko_finder") -> None:
        """Speichere Config in QSettings."""
        settings.beginGroup(prefix)
        settings.setValue("min_leverage", self.min_leverage)
        settings.setValue("max_spread_pct", self.max_spread_pct)
        settings.setValue("min_ko_distance_pct", self.min_ko_distance_pct)
        settings.setValue("top_n", self.top_n)
        settings.setValue("issuer_ids", [i.value for i in self.issuers])
        settings.setValue("broker_id", self.broker_id)
        settings.setValue("feature", self.feature)
        settings.endGroup()

    @classmethod
    def load_from_qsettings(
        cls, settings: QSettings, prefix: str = "ko_finder"
    ) -> KOFilterConfig:
        """Lade Config aus QSettings."""
        settings.beginGroup(prefix)

        issuer_ids = settings.value("issuer_ids", [i.value for i in Issuer])
        if isinstance(issuer_ids, str):
            issuer_ids = [int(x) for x in issuer_ids.split(",") if x]

        issuers = [
            Issuer(id_) for id_ in issuer_ids if id_ in [i.value for i in Issuer]
        ]

        config = cls(
            min_leverage=float(
                settings.value("min_leverage", DEFAULT_MIN_LEVERAGE)
            ),
            max_spread_pct=float(
                settings.value("max_spread_pct", DEFAULT_MAX_SPREAD_PCT)
            ),
            min_ko_distance_pct=float(
                settings.value("min_ko_distance_pct", DEFAULT_MIN_KO_DISTANCE_PCT)
            ),
            top_n=int(settings.value("top_n", DEFAULT_TOP_N)),
            issuers=issuers or list(Issuer),
            broker_id=settings.value("broker_id", DEFAULT_BROKER_ID),
            feature=settings.value("feature", "STOP_LOSS"),
        )

        settings.endGroup()
        return config
