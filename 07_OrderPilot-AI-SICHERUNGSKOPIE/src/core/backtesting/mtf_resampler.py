"""
MTFResampler - Multi-Timeframe Resampling ohne Data-Leak

Resampled 1-Minuten-Daten zu höheren Timeframes mit strikter
No-Leak-Garantie: Higher-TF Candles sind nur verfügbar, wenn
sie vollständig abgeschlossen sind.

Features:
- Resampling zu 5m/15m/1h/4h/1D
- Nur "closed candles" für höhere TF
- Deterministische Berechnung
- Cache für Performance
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Iterator

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


def _safe_timestamp_to_int(value) -> int:
    """Konvertiert verschiedene Timestamp-Typen sicher zu int (Millisekunden).

    Unterstützt: int, float, pd.Timestamp, datetime, np.datetime64

    Args:
        value: Timestamp in verschiedenen Formaten

    Returns:
        Unix timestamp in Millisekunden als int
    """
    if value is None:
        return 0

    # Bereits int
    if isinstance(value, (int, np.integer)):
        return int(value)

    # Float (z.B. Unix timestamp in Sekunden)
    if isinstance(value, (float, np.floating)):
        # Wenn > 1e12, ist es bereits in ms
        if value > 1e12:
            return int(value)
        return int(value * 1000)

    # pandas Timestamp
    if isinstance(value, pd.Timestamp):
        return int(value.timestamp() * 1000)

    # datetime
    if isinstance(value, datetime):
        return int(value.timestamp() * 1000)

    # numpy datetime64
    if isinstance(value, np.datetime64):
        # Konvertiere zu pandas Timestamp dann zu int
        return int(pd.Timestamp(value).timestamp() * 1000)

    # Fallback: Versuche direkte Konvertierung
    try:
        return int(value)
    except (TypeError, ValueError):
        logger.warning(f"Konnte Timestamp nicht konvertieren: {type(value)} = {value}")
        return 0


# Timeframe-Definitionen in Minuten
TIMEFRAME_MINUTES = {
    "1m": 1,
    "3m": 3,
    "5m": 5,
    "15m": 15,
    "30m": 30,
    "1h": 60,
    "2h": 120,
    "4h": 240,
    "6h": 360,
    "8h": 480,
    "12h": 720,
    "1D": 1440,
    "1d": 1440,
    "1W": 10080,
    "1w": 10080,
}


@dataclass
class ResampledBar:
    """Eine resampelte Bar.

    Attributes:
        timeframe: Timeframe der Bar (z.B. "5m")
        timestamp: Start-Timestamp der Bar (ms)
        timestamp_end: End-Timestamp der Bar (ms)
        open: Open Price
        high: High Price
        low: Low Price
        close: Close Price
        volume: Gesamtvolumen
        bar_count: Anzahl 1m Bars in dieser Bar
        is_complete: True wenn Bar vollständig (alle 1m Bars vorhanden)
    """
    timeframe: str
    timestamp: int
    timestamp_end: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    bar_count: int = 0
    is_complete: bool = False

    @property
    def datetime(self) -> datetime:
        """Start-Timestamp als datetime."""
        return datetime.fromtimestamp(self.timestamp / 1000, tz=timezone.utc)

    @property
    def datetime_end(self) -> datetime:
        """End-Timestamp als datetime."""
        return datetime.fromtimestamp(self.timestamp_end / 1000, tz=timezone.utc)


class MTFResampler:
    """Multi-Timeframe Resampler mit No-Leak-Garantie.

    Regeln:
    1. Eine Higher-TF Bar ist nur verfügbar, wenn sie VOLLSTÄNDIG ist
    2. "Vollständig" = alle 1m Candles der Periode sind durch
    3. Aktuelle (unvollständige) Bars werden NICHT zurückgegeben

    Example:
        resampler = MTFResampler(["5m", "15m", "1h"])

        # Bei jeder neuen 1m Candle:
        mtf_data = resampler.update(current_1m_candle, history_1m)

        # mtf_data enthält nur ABGESCHLOSSENE higher-tf Bars
        for tf, bars in mtf_data.items():
            print(f"{tf}: {len(bars)} closed bars available")
    """

    def __init__(
        self,
        timeframes: list[str],
        history_bars_per_tf: int = 100,
    ):
        """Initialisiert den Resampler.

        Args:
            timeframes: Liste der Ziel-Timeframes (z.B. ["5m", "15m", "1h"])
            history_bars_per_tf: Anzahl historischer Bars pro TF zu behalten
        """
        self._validate_timeframes(timeframes)
        self.timeframes = timeframes
        self.history_bars_per_tf = history_bars_per_tf

        # Cache für resamplete Bars pro Timeframe
        self._cache: dict[str, pd.DataFrame] = {tf: pd.DataFrame() for tf in timeframes}

        # Letzte bekannte vollständige Bar-Timestamps pro TF
        self._last_complete_ts: dict[str, int] = {tf: 0 for tf in timeframes}

        logger.info(f"MTFResampler initialized: {timeframes}")

    def _validate_timeframes(self, timeframes: list[str]) -> None:
        """Validiert die Timeframe-Liste."""
        for tf in timeframes:
            if tf not in TIMEFRAME_MINUTES:
                raise ValueError(f"Unknown timeframe: {tf}. Valid: {list(TIMEFRAME_MINUTES.keys())}")

    def get_timeframe_minutes(self, timeframe: str) -> int:
        """Gibt die Anzahl Minuten für einen Timeframe zurück."""
        return TIMEFRAME_MINUTES.get(timeframe, 1)

    def get_bar_start_timestamp(self, timestamp_ms: int, timeframe: str) -> int:
        """Berechnet den Start-Timestamp einer Bar.

        Args:
            timestamp_ms: Timestamp in Millisekunden
            timeframe: Ziel-Timeframe

        Returns:
            Start-Timestamp der Bar (Beginn der Periode)
        """
        minutes = self.get_timeframe_minutes(timeframe)
        period_ms = minutes * 60 * 1000

        # Floor division zum Beginn der Periode
        return (timestamp_ms // period_ms) * period_ms

    def get_bar_end_timestamp(self, timestamp_ms: int, timeframe: str) -> int:
        """Berechnet den End-Timestamp einer Bar.

        Args:
            timestamp_ms: Timestamp in Millisekunden
            timeframe: Ziel-Timeframe

        Returns:
            End-Timestamp der Bar (Ende der Periode, exklusiv)
        """
        minutes = self.get_timeframe_minutes(timeframe)
        period_ms = minutes * 60 * 1000

        bar_start = self.get_bar_start_timestamp(timestamp_ms, timeframe)
        return bar_start + period_ms

    def is_bar_complete(
        self,
        current_1m_timestamp: int,
        bar_start_timestamp: int,
        timeframe: str,
    ) -> bool:
        """Prüft, ob eine Higher-TF Bar vollständig ist.

        Eine Bar ist vollständig, wenn die aktuelle 1m-Candle
        NACH dem Ende der Bar liegt (nicht mehr darin).

        Args:
            current_1m_timestamp: Timestamp der aktuellen 1m Candle
            bar_start_timestamp: Start-Timestamp der zu prüfenden Bar
            timeframe: Timeframe der Bar

        Returns:
            True wenn Bar vollständig
        """
        bar_end = self.get_bar_end_timestamp(bar_start_timestamp, timeframe)
        return current_1m_timestamp >= bar_end

    def resample_history(
        self,
        history_1m: pd.DataFrame,
        current_timestamp: int,
        timeframe: str,
    ) -> pd.DataFrame:
        """Resampled 1m History zu einem Higher-TF.

        Args:
            history_1m: DataFrame mit 1m OHLCV (muss timestamp, OHLCV haben)
            current_timestamp: Aktueller Timestamp (für No-Leak Check)
            timeframe: Ziel-Timeframe

        Returns:
            DataFrame mit resampelten Bars (nur vollständige!)
        """
        if history_1m.empty:
            return pd.DataFrame()

        minutes = self.get_timeframe_minutes(timeframe)
        period_ms = minutes * 60 * 1000

        # Kopie erstellen und Bar-Start berechnen
        df = history_1m.copy()

        # Konvertiere timestamp zu int (ms) falls es DatetimeArray ist
        if pd.api.types.is_datetime64_any_dtype(df["timestamp"]):
            # Konvertiere datetime zu Unix timestamp in ms
            df["timestamp"] = df["timestamp"].astype('int64') // 10**6
        elif not pd.api.types.is_numeric_dtype(df["timestamp"]):
            # Versuche Konvertierung über _safe_timestamp_to_int
            df["timestamp"] = df["timestamp"].apply(_safe_timestamp_to_int)

        df["bar_start"] = (df["timestamp"] // period_ms) * period_ms

        # Gruppiere und aggregiere
        resampled = df.groupby("bar_start").agg({
            "timestamp": "first",
            "open": "first",
            "high": "max",
            "low": "min",
            "close": "last",
            "volume": "sum",
        }).reset_index()

        # Berechne bar_end und bar_count
        resampled["bar_end"] = resampled["bar_start"] + period_ms
        resampled["bar_count"] = df.groupby("bar_start").size().values

        # KRITISCH: Nur vollständige Bars zurückgeben!
        # Eine Bar ist vollständig wenn current_timestamp >= bar_end
        resampled["is_complete"] = resampled["bar_end"] <= current_timestamp

        # Filtere auf vollständige Bars
        complete_bars = resampled[resampled["is_complete"]].copy()

        # Sortiere nach Timestamp
        complete_bars = complete_bars.sort_values("bar_start").reset_index(drop=True)

        return complete_bars

    def update(
        self,
        current_candle_ts: int,
        history_1m: pd.DataFrame,
    ) -> dict[str, pd.DataFrame]:
        """Update mit neuer 1m Candle, gibt alle MTF Daten zurück.

        Optimierung:
        - Wenn current_candle_ts in der gleichen Minute liegt wie der letzte Update, skip.
        - Nur Timeframes aktualisieren, deren Bar-Ende durch die neue Candle erreicht wurde.

        Args:
            current_candle_ts: Timestamp der aktuellen 1m Candle
            history_1m: DataFrame mit 1m OHLCV History (inkl. vorheriger Candles)

        Returns:
            Dictionary mit TF → DataFrame von vollständigen Bars
        """
        # Wenn wir den gleichen Timestamp schon verarbeitet haben, skip
        if hasattr(self, "_last_candle_ts") and current_candle_ts <= self._last_candle_ts:
            return {tf: df.copy() for tf, df in self._cache.items()}
        
        self._last_candle_ts = current_candle_ts
        result = {}

        for tf in self.timeframes:
            minutes = TIMEFRAME_MINUTES[tf]
            period_ms = minutes * 60 * 1000
            
            # Prüfen ob wir für diesen TF ein Update brauchen
            # Wir brauchen ein Update wenn:
            # 1. Cache leer ist
            # 2. current_candle_ts >= nächstes Bar-Ende
            last_complete = self._last_complete_ts[tf]
            next_bar_end = last_complete + period_ms if last_complete > 0 else 0
            
            if next_bar_end > 0 and current_candle_ts < next_bar_end:
                # Noch in der gleichen Bar, keine neue Bar fertig
                result[tf] = self._cache[tf]
                continue

            # Full resample nur wenn nötig
            resampled = self.resample_history(history_1m, current_candle_ts, tf)

            # Limitiere auf history_bars_per_tf
            if len(resampled) > self.history_bars_per_tf:
                resampled = resampled.tail(self.history_bars_per_tf).reset_index(drop=True)

            self._cache[tf] = resampled
            result[tf] = resampled

            # Update last complete timestamp
            if not resampled.empty:
                self._last_complete_ts[tf] = _safe_timestamp_to_int(resampled["bar_start"].iloc[-1])

        return result

    def get_latest_complete_bar(self, timeframe: str) -> ResampledBar | None:
        """Gibt die letzte vollständige Bar für einen TF zurück.

        Args:
            timeframe: Ziel-Timeframe

        Returns:
            ResampledBar oder None wenn keine vorhanden
        """
        if timeframe not in self._cache:
            return None

        df = self._cache[timeframe]
        if df.empty:
            return None

        row = df.iloc[-1]
        return ResampledBar(
            timeframe=timeframe,
            timestamp=_safe_timestamp_to_int(row["bar_start"]),
            timestamp_end=_safe_timestamp_to_int(row["bar_end"]),
            open=float(row["open"]),
            high=float(row["high"]),
            low=float(row["low"]),
            close=float(row["close"]),
            volume=float(row["volume"]),
            bar_count=int(row.get("bar_count", 0)) if pd.notna(row.get("bar_count", 0)) else 0,
            is_complete=True,
        )

    def get_all_bars(self, timeframe: str) -> list[ResampledBar]:
        """Gibt alle gecachten Bars für einen TF zurück.

        Args:
            timeframe: Ziel-Timeframe

        Returns:
            Liste von ResampledBar
        """
        if timeframe not in self._cache:
            return []

        df = self._cache[timeframe]
        if df.empty:
            return []

        bars = []
        for _, row in df.iterrows():
            bars.append(ResampledBar(
                timeframe=timeframe,
                timestamp=_safe_timestamp_to_int(row["bar_start"]),
                timestamp_end=_safe_timestamp_to_int(row["bar_end"]),
                open=float(row["open"]),
                high=float(row["high"]),
                low=float(row["low"]),
                close=float(row["close"]),
                volume=float(row["volume"]),
                bar_count=int(row.get("bar_count", 0)) if pd.notna(row.get("bar_count", 0)) else 0,
                is_complete=True,
            ))

        return bars

    def clear_cache(self) -> None:
        """Leert den Cache."""
        for tf in self.timeframes:
            self._cache[tf] = pd.DataFrame()
            self._last_complete_ts[tf] = 0

    def get_cache_statistics(self) -> dict[str, int]:
        """Gibt Cache-Statistiken zurück."""
        return {tf: len(df) for tf, df in self._cache.items()}

    def get_current_timeframes(self, bar_index: int = 0) -> dict[str, pd.DataFrame]:
        """Gibt die aktuellen gecachten MTF-Daten zurück.

        Diese Methode wird vom BacktestRunner verwendet, um die aktuellen
        Multi-Timeframe Daten für Signal-Generierung abzurufen.

        Args:
            bar_index: Aktueller Bar-Index (für zukünftige Erweiterungen)

        Returns:
            Dictionary mit Timeframe → DataFrame der vollständigen Bars
        """
        return {tf: df.copy() for tf, df in self._cache.items()}
