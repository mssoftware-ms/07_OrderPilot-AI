"""AI Analysis Worker - Background thread for data fetching and analysis.

Refactored from 822 LOC monolith using composition pattern.

Module 1/5 of ai_analysis_window.py split.

Contains:
- AnalysisWorker: QThread worker for async data fetching and analysis
"""

from __future__ import annotations

import asyncio
import logging
from typing import Optional, TYPE_CHECKING

from PyQt6.QtCore import QThread, pyqtSignal

if TYPE_CHECKING:
    from src.core.ai_analysis.engine import AIAnalysisEngine

analysis_logger = logging.getLogger('ai_analysis')


class AnalysisWorker(QThread):
    """
    Worker thread to run the AI analysis without freezing the UI.
    Fetches fresh data from history_manager before analysis.
    """
    finished = pyqtSignal(object)  # Returns AIAnalysisOutput or None
    error = pyqtSignal(str)

    def __init__(self, engine: "AIAnalysisEngine", symbol: str, timeframe: str,
                 history_manager, asset_class, data_source, model: Optional[str] = None,
                 strategy_configs: Optional[list] = None):
        super().__init__()
        self.engine = engine
        self.symbol = symbol
        self.timeframe = timeframe
        self.history_manager = history_manager
        self.asset_class = asset_class
        self.data_source = data_source
        self.model = model
        # Issue #20: Strategy configurations from Strategy Simulator
        self.strategy_configs = strategy_configs

    def run(self):
        from datetime import datetime, timedelta, timezone
        from src.core.market_data.history_provider import DataRequest, Timeframe as TF, DataSource

        try:
            # We need a new loop for this thread if using async
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            # Fetch FRESH data from history_manager (async)
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=7)  # 1 week lookback

            # Map timeframe string to Timeframe enum
            timeframe_map = {
                "1T": TF.MINUTE_1,
                "5T": TF.MINUTE_5,
                "15T": TF.MINUTE_15,
                "1H": TF.HOUR_1,
                "1D": TF.DAY_1
            }
            tf_enum = timeframe_map.get(self.timeframe, TF.MINUTE_1)

            # Convert data_source to enum if it's a string
            # NO FALLBACK - use exact data source from active chart or fail
            if isinstance(self.data_source, str):
                source_str = self.data_source.upper().replace(" ", "_")
                source_map = {
                    "ALPACA": DataSource.ALPACA,
                    "ALPACA_CRYPTO": DataSource.ALPACA_CRYPTO,
                    "BITUNIX": DataSource.BITUNIX,
                    "YAHOO": DataSource.YAHOO,
                    "YAHOO_FINANCE": DataSource.YAHOO,
                    "ALPHA_VANTAGE": DataSource.ALPHA_VANTAGE,
                    "FINNHUB": DataSource.FINNHUB,
                    "IBKR": DataSource.IBKR,
                    "DATABASE": DataSource.DATABASE
                }
                source_enum = source_map.get(source_str, None)

                if source_enum is None:
                    self.error.emit(f"Ungültiger Datenquellen-Typ: '{self.data_source}'. Bitte Chart-Datenquelle überprüfen.")
                    loop.close()
                    return
            else:
                source_enum = self.data_source

            # Analysis logging
            analysis_logger.info("Worker requesting data", extra={
                'symbol': self.symbol,
                'timeframe': self.timeframe,
                'timeframe_enum': str(tf_enum),
                'asset_class': self.asset_class,
                'data_source': str(self.data_source),
                'data_source_enum': str(source_enum),
                'step': 'data_request'
            })

            request = DataRequest(
                symbol=self.symbol,
                start_date=start_date,
                end_date=end_date,
                timeframe=tf_enum,
                asset_class=self.asset_class,
                source=source_enum
            )

            bars, source_used = loop.run_until_complete(
                self.history_manager.fetch_data(request)
            )

            # Determine data type
            data_type = "HISTORICAL" if bars else "NONE"

            analysis_logger.info("Data fetched", extra={
                'symbol': self.symbol,
                'bars_count': len(bars) if bars else 0,
                'data_source_used': str(source_used),
                'data_type': data_type,
                'step': 'data_fetch'
            })

            if not bars:
                analysis_logger.error("No data received", extra={
                    'symbol': self.symbol,
                    'data_source': str(source_used),
                    'step': 'data_fetch_error'
                })
                self.error.emit(f"Failed to fetch data from {source_used}")
                loop.close()
                return

            # Convert bars to DataFrame
            import pandas as pd
            data = []
            for bar in bars:
                data.append({
                    'time': bar.timestamp,
                    'open': float(bar.open),
                    'high': float(bar.high),
                    'low': float(bar.low),
                    'close': float(bar.close),
                    'volume': float(bar.volume)
                })

            df = pd.DataFrame(data)
            df.set_index('time', inplace=True)

            # Tag DataFrame with data source type for logging
            df._data_source_type = data_type

            if df.empty:
                analysis_logger.error("DataFrame conversion resulted in empty DataFrame", extra={
                    'symbol': self.symbol,
                    'step': 'dataframe_conversion_error'
                })
                self.error.emit("Converted DataFrame is empty")
                loop.close()
                return

            analysis_logger.info("DataFrame prepared for analysis", extra={
                'symbol': self.symbol,
                'df_shape': df.shape,
                'data_type': data_type,
                'step': 'dataframe_ready'
            })

            # Issue #20: Run analysis with fresh data and strategy configs
            result = loop.run_until_complete(
                self.engine.run_analysis(
                    self.symbol, self.timeframe, df,
                    model=self.model,
                    strategy_configs=self.strategy_configs
                )
            )
            self.finished.emit(result)
            loop.close()
        except Exception as e:
            import traceback
            analysis_logger.error("Worker exception", extra={
                'symbol': self.symbol,
                'error': str(e),
                'error_type': type(e).__name__,
                'step': 'worker_error'
            }, exc_info=True)
            self.error.emit(f"{str(e)}\n{traceback.format_exc()}")
