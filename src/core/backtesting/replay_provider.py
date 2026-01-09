"""
ReplayMarketDataProvider - Historische Daten als simulierter Live-Stream

Lädt 1-Minuten OHLCV-Daten und stellt sie Candle-by-Candle bereit,
um Live-Trading zu simulieren.

Features:
- Candle-by-Candle Iterator
- History Window für Lookback
- Deterministische Reihenfolge
- Kein Future-Data-Leak
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Iterator, AsyncIterator

import pandas as pd
import numpy as np

from src.database import get_db_manager
from src.database.models import MarketBar

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


@dataclass
class CandleSnapshot:
    """Einzelne Candle mit Metadaten.

    Attributes:
        timestamp: Unix Timestamp in ms
        open: Open Price
        high: High Price
        low: Low Price
        close: Close Price
        volume: Volumen
        bar_index: Index im Dataset
        is_complete: True wenn Bar abgeschlossen
    """
    timestamp: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    bar_index: int = 0
    is_complete: bool = True

    @property
    def datetime(self) -> datetime:
        """Timestamp als datetime."""
        return datetime.fromtimestamp(self.timestamp / 1000, tz=timezone.utc)

    def to_dict(self) -> dict:
        """Konvertiert zu Dictionary."""
        return {
            "timestamp": self.timestamp,
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
            "datetime": self.datetime.isoformat(),
        }


@dataclass
class CandleIteratorState:
    """State für den Candle Iterator.

    Attributes:
        current_index: Aktueller Index
        total_bars: Gesamtanzahl Bars
        history_window: Lookback-Fenster
        data: DataFrame mit OHLCV Daten
    """
    current_index: int = 0
    total_bars: int = 0
    history_window: int = 200
    data: pd.DataFrame = field(default_factory=pd.DataFrame)


class CandleIterator:
    """Iterator für Candle-by-Candle Replay.

    Liefert bei jedem Aufruf:
    - Aktuelle Candle
    - History Window (N vorherige Candles)

    Garantiert:
    - Deterministische Reihenfolge
    - Kein Zugriff auf zukünftige Daten
    - Reproduzierbare Ergebnisse
    """

    def __init__(
        self,
        data: pd.DataFrame,
        history_window: int = 200,
        start_index: int | None = None,
    ):
        """Initialisiert den Iterator.

        Args:
            data: DataFrame mit OHLCV Daten (muss timestamp, open, high, low, close, volume haben)
            history_window: Anzahl vergangener Candles für Lookback
            start_index: Start-Index (default: history_window, um genug Lookback zu haben)
        """
        self._validate_data(data)

        # Sortiere nach Timestamp (aufsteigend)
        self.data = data.sort_values("timestamp").reset_index(drop=True)
        self.history_window = history_window
        self.total_bars = len(self.data)

        # Start-Index: mindestens history_window, um Lookback zu haben
        self.start_index = start_index if start_index is not None else history_window
        self.current_index = self.start_index

        logger.info(
            f"CandleIterator initialized: {self.total_bars} bars, "
            f"start_index={self.start_index}, history_window={history_window}"
        )

    def _validate_data(self, data: pd.DataFrame) -> None:
        """Validiert das Input-DataFrame."""
        required_columns = ["timestamp", "open", "high", "low", "close", "volume"]
        missing = [col for col in required_columns if col not in data.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

        if data.empty:
            raise ValueError("Data DataFrame is empty")

    def __iter__(self) -> Iterator[tuple[CandleSnapshot, pd.DataFrame]]:
        """Iterator über alle Candles."""
        self.current_index = self.start_index
        return self

    def __next__(self) -> tuple[CandleSnapshot, pd.DataFrame]:
        """Nächste Candle mit History Window.

        Returns:
            Tuple aus (aktuelle_candle, history_dataframe)

        Raises:
            StopIteration: Wenn Ende erreicht
        """
        if self.current_index >= self.total_bars:
            raise StopIteration

        # Aktuelle Candle
        row = self.data.iloc[self.current_index]
        current_candle = CandleSnapshot(
            timestamp=_safe_timestamp_to_int(row["timestamp"]),
            open=float(row["open"]),
            high=float(row["high"]),
            low=float(row["low"]),
            close=float(row["close"]),
            volume=float(row["volume"]),
            bar_index=self.current_index,
            is_complete=True,
        )

        # History Window (NICHT inkl. aktueller Candle - kein Leak!)
        history_start = max(0, self.current_index - self.history_window)
        history_end = self.current_index  # Exclusive - aktuelle Candle nicht dabei
        history = self.data.iloc[history_start:history_end].copy()

        self.current_index += 1
        return current_candle, history

    def __len__(self) -> int:
        """Anzahl verbleibender Candles."""
        return max(0, self.total_bars - self.current_index)

    @property
    def progress(self) -> float:
        """Fortschritt in Prozent (0-100)."""
        if self.total_bars <= self.start_index:
            return 100.0
        total_to_process = self.total_bars - self.start_index
        processed = self.current_index - self.start_index
        return min(100.0, (processed / total_to_process) * 100)

    def reset(self) -> None:
        """Setzt Iterator auf Anfang zurück."""
        self.current_index = self.start_index

    def peek(self) -> CandleSnapshot | None:
        """Zeigt nächste Candle ohne weiterzugehen."""
        if self.current_index >= self.total_bars:
            return None
        row = self.data.iloc[self.current_index]
        return CandleSnapshot(
            timestamp=_safe_timestamp_to_int(row["timestamp"]),
            open=float(row["open"]),
            high=float(row["high"]),
            low=float(row["low"]),
            close=float(row["close"]),
            volume=float(row["volume"]),
            bar_index=self.current_index,
            is_complete=True,
        )


class ReplayMarketDataProvider:
    """Provider für historische Marktdaten im Replay-Modus.

    Lädt Daten aus der Datenbank und stellt sie als Iterator bereit.

    Features:
    - Automatisches Laden aus SQLite
    - Validierung und Bereinigung
    - Lücken-Handling
    - Deterministische Replay

    Usage:
        provider = ReplayMarketDataProvider()
        await provider.load_data("BTCUSDT", start, end)

        for candle, history in provider.iterate():
            # Process candle with history lookback
            pass
    """

    def __init__(self, history_window: int = 200):
        """Initialisiert den Provider.

        Args:
            history_window: Lookback-Fenster für History
        """
        self.db_manager = get_db_manager()
        self.history_window = history_window
        self._data: pd.DataFrame | None = None
        self._iterator: CandleIterator | None = None
        self._symbol: str = ""
        self._start_date: datetime | None = None
        self._end_date: datetime | None = None

    async def load_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        validate: bool = True,
    ) -> int:
        """Lädt historische Daten aus der Datenbank.

        Args:
            symbol: Trading-Symbol (mit Source-Prefix, z.B. "bitunix:BTCUSDT")
            start_date: Startdatum
            end_date: Enddatum
            validate: Daten validieren und bereinigen

        Returns:
            Anzahl geladener Bars

        Raises:
            ValueError: Wenn keine Daten gefunden
        """
        if self._matches_request(symbol, start_date, end_date):
            if self._iterator is None and self._data is not None:
                self._iterator = CandleIterator(
                    data=self._data,
                    history_window=self.history_window,
                )
            logger.info(f"Using cached data for {symbol}: {start_date} to {end_date}")
            return len(self._data) if self._data is not None else 0

        self._symbol = symbol
        self._start_date = start_date
        self._end_date = end_date

        logger.info(f"Loading data for {symbol}: {start_date} to {end_date}")

        # Lade aus Datenbank
        bars = await self._load_from_db(symbol, start_date, end_date)

        if not bars:
            raise ValueError(f"No data found for {symbol} in date range")

        # Konvertiere zu DataFrame
        self._data = self._bars_to_dataframe(bars)

        if validate:
            self._validate_and_clean()

        # Erstelle Iterator
        self._iterator = CandleIterator(
            data=self._data,
            history_window=self.history_window,
        )

        logger.info(f"Loaded {len(self._data)} bars for {symbol}")
        return len(self._data)

    def _matches_request(self, symbol: str, start_date: datetime, end_date: datetime) -> bool:
        """Prüft, ob die aktuellen Daten zur Anfrage passen."""
        if self._data is None or self._data.empty:
            return False
        return (
            self._symbol == symbol
            and self._start_date == start_date
            and self._end_date == end_date
        )

    async def _load_from_db(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
    ) -> list[MarketBar]:
        """Lädt Bars aus der Datenbank."""
        start_ts = int(start_date.timestamp() * 1000)
        end_ts = int(end_date.timestamp() * 1000)

        # Normalisiere Symbol: entferne Prefix wie "bitunix:" oder "alpaca:"
        db_symbol = symbol.split(":")[-1] if ":" in symbol else symbol
        logger.debug(f"Querying DB with symbol: {db_symbol} (original: {symbol})")

        return await self.db_manager.get_bars_async(
            symbol=db_symbol,
            start_ts=start_ts,
            end_ts=end_ts,
            limit=None,  # Alle Bars
        )

    def _bars_to_dataframe(self, bars: list[MarketBar]) -> pd.DataFrame:
        """Konvertiert MarketBar Liste zu DataFrame."""
        data = []
        for bar in bars:
            data.append({
                "timestamp": bar.timestamp,
                "open": float(bar.open),
                "high": float(bar.high),
                "low": float(bar.low),
                "close": float(bar.close),
                "volume": float(bar.volume),
            })

        df = pd.DataFrame(data)
        df = df.sort_values("timestamp").reset_index(drop=True)
        return df

    def _validate_and_clean(self) -> None:
        """Validiert und bereinigt die Daten."""
        if self._data is None or self._data.empty:
            return

        initial_count = len(self._data)

        # 1. Entferne Duplikate
        self._data = self._data.drop_duplicates(subset=["timestamp"], keep="first")

        # 2. Entferne ungültige Preise
        self._data = self._data[
            (self._data["open"] > 0) &
            (self._data["high"] > 0) &
            (self._data["low"] > 0) &
            (self._data["close"] > 0)
        ]

        # 3. Entferne OHLC Inkonsistenzen (high < low)
        self._data = self._data[self._data["high"] >= self._data["low"]]

        # 4. Sortiere nach Timestamp
        self._data = self._data.sort_values("timestamp").reset_index(drop=True)

        removed = initial_count - len(self._data)
        if removed > 0:
            logger.warning(f"Cleaned {removed} invalid bars")

    def load_from_dataframe(self, df: pd.DataFrame) -> int:
        """Lädt Daten direkt aus einem DataFrame.

        Args:
            df: DataFrame mit OHLCV Daten

        Returns:
            Anzahl Bars
        """
        self._data = df.copy()
        self._validate_and_clean()

        self._iterator = CandleIterator(
            data=self._data,
            history_window=self.history_window,
        )

        return len(self._data)

    def iterate(self) -> CandleIterator:
        """Gibt Iterator für Candle-by-Candle Replay zurück.

        Returns:
            CandleIterator

        Raises:
            RuntimeError: Wenn keine Daten geladen
        """
        if self._iterator is None:
            raise RuntimeError("No data loaded. Call load_data() first.")

        self._iterator.reset()
        return self._iterator

    async def replay_iter(
        self,
        yield_every: int = 200,
    ) -> AsyncIterator[tuple[CandleSnapshot, pd.DataFrame]]:
        """Async-Iterator für Candle-by-Candle Replay.

        Args:
            yield_every: Anzahl Candles zwischen Event-Loop-Yields.
        """
        iterator = self.iterate()
        for index, (candle, history) in enumerate(iterator, start=1):
            yield candle, history
            if yield_every > 0 and index % yield_every == 0:
                await asyncio.sleep(0)

    @property
    def data(self) -> pd.DataFrame | None:
        """Rohes DataFrame (für Analyse/Debug)."""
        return self._data

    @property
    def bar_count(self) -> int:
        """Anzahl geladener Bars."""
        return len(self._data) if self._data is not None else 0

    @property
    def date_range(self) -> tuple[datetime | None, datetime | None]:
        """Datum-Bereich der geladenen Daten."""
        if self._data is None or self._data.empty:
            return None, None

        first_ts = self._data["timestamp"].iloc[0]
        last_ts = self._data["timestamp"].iloc[-1]

        return (
            datetime.fromtimestamp(first_ts / 1000, tz=timezone.utc),
            datetime.fromtimestamp(last_ts / 1000, tz=timezone.utc),
        )

    def get_statistics(self) -> dict:
        """Gibt Statistiken über die geladenen Daten zurück."""
        if self._data is None:
            return {}

        return {
            "symbol": self._symbol,
            "bar_count": len(self._data),
            "date_range": self.date_range,
            "price_range": (
                float(self._data["low"].min()),
                float(self._data["high"].max()),
            ),
            "total_volume": float(self._data["volume"].sum()),
            "avg_volume": float(self._data["volume"].mean()),
        }
