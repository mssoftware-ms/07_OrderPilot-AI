"""Orchestrator for the Deep Analysis Run.

Coordinates:
1. Data Collection (Multi-TF) using HistoryManager
2. Feature Calculation
3. Payload Assembly
4. LLM Request (simulated for now)
"""

import asyncio
import time
import pandas as pd
from datetime import datetime, timedelta, timezone
from PyQt6.QtCore import QThread, pyqtSignal
from src.core.analysis.context import AnalysisContext
from src.core.market_data.types import DataRequest, Timeframe

class AnalysisWorker(QThread):
    """Background worker for the analysis process."""
    
    status_update = pyqtSignal(str) # "Loading data...", "Done"
    progress_update = pyqtSignal(int) # 0-100
    result_ready = pyqtSignal(str) # Markdown report
    error_occurred = pyqtSignal(str)

    def __init__(self, context: AnalysisContext):
        super().__init__()
        self.context = context
        self._loop = None

    def run(self):
        try:
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            
            self.status_update.emit("Initialisierung...")
            self.progress_update.emit(5)

            # 1. Validation & Setup
            strat = self.context.get_selected_strategy()
            tfs = self.context.get_active_timeframes()
            hm = self.context.history_manager
            symbol = self.context._current_symbol
            
            if not strat or not tfs:
                raise ValueError("Strategie oder Timeframes nicht konfiguriert.")
            if not hm:
                raise ValueError("HistoryManager nicht verfügbar (Kontext fehlt).")

            # 2. Data Collection (Real)
            self.status_update.emit(f"Lade Marktdaten für {len(tfs)} Timeframes...")
            
            fetched_data = {} # { "1m": pd.DataFrame, ... }
            
            total_steps = len(tfs)
            for i, tf_config in enumerate(tfs):
                self.status_update.emit(f"Lade {tf_config.tf} ({tf_config.role})...")
                
                # Resolve timeframe enum
                tf_enum = self._map_timeframe(tf_config.tf)
                
                # Calculate dates
                # Approximate duration based on tf string to ensure we get enough bars
                # Simple logic: 1 bar = X minutes. Lookback = N bars.
                duration_min = self._get_duration_minutes(tf_config.tf)
                total_minutes = tf_config.lookback * duration_min * 1.5 # Buffer
                
                end_date = datetime.now(timezone.utc)
                start_date = end_date - timedelta(minutes=total_minutes)
                
                # Fetch
                request = DataRequest(
                    symbol=symbol,
                    start_date=start_date,
                    end_date=end_date,
                    timeframe=tf_enum,
                    asset_class=self.context.asset_class,
                    source=self.context.data_source
                )
                
                # Async call in sync thread
                bars, source = self._loop.run_until_complete(hm.fetch_data(request))
                
                if not bars:
                    # Retry logic or skip could go here
                    print(f"Warning: No data for {tf_config.tf}")
                    continue
                    
                # Convert to DataFrame
                df = self._bars_to_dataframe(bars)
                fetched_data[tf_config.tf] = df
                
                # Update Progress (10% to 60%)
                progress = 10 + int((i + 1) / total_steps * 50)
                self.progress_update.emit(progress)

            if not fetched_data:
                raise ValueError("Keine Daten für die gewählten Timeframes empfangen.")

            # 3. Feature Engineering (Placeholder/Basic Stats)
            self.status_update.emit("Berechne Indikatoren & Features...")
            features = self._calculate_features(fetched_data)
            self.progress_update.emit(70)

            # 4. LLM Generation (Still Simulated/Stub)
            self.status_update.emit("Generiere KI-Analyse (Deep Reasoning)...")
            # Here we would build the payload and call AIAnalysisEngine
            time.sleep(1.0) 
            self.progress_update.emit(90)

            # 5. Finalize
            self.progress_update.emit(100)
            self.status_update.emit("Fertig.")
            
            # Generate Report based on REAL fetched metadata
            report = self._generate_report(strat.name, symbol, features)
            self.result_ready.emit(report)
            
            self._loop.close()

        except Exception as e:
            self.error_occurred.emit(str(e))
            if self._loop:
                self._loop.close()

    def _map_timeframe(self, tf_str: str) -> Timeframe:
        """Maps config string (1m, 1h) to Timeframe enum."""
        mapping = {
            "1m": Timeframe.MINUTE_1,
            "3m": Timeframe.MINUTE_3, # If supported
            "5m": Timeframe.MINUTE_5,
            "15m": Timeframe.MINUTE_15,
            "30m": Timeframe.MINUTE_30,
            "1h": Timeframe.HOUR_1,
            "4h": Timeframe.HOUR_4,
            "1D": Timeframe.DAY_1,
            "1W": Timeframe.WEEK_1,
            "1M": Timeframe.MONTH_1,
        }
        return mapping.get(tf_str, Timeframe.MINUTE_1) # Fallback

    def _get_duration_minutes(self, tf_str: str) -> int:
        """Helper to calculate lookback duration."""
        if "m" in tf_str: return int(tf_str.replace("m", ""))
        if "h" in tf_str: return int(tf_str.replace("h", "")) * 60
        if "D" in tf_str: return 1440
        if "W" in tf_str: return 10080
        if "M" in tf_str: return 43200
        return 1

    def _bars_to_dataframe(self, bars) -> pd.DataFrame:
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
        if not df.empty:
            df.set_index('time', inplace=True)
        return df

    def _calculate_features(self, data_map: dict) -> dict:
        """Simple stat extraction to prove we have data."""
        stats = {}
        for tf, df in data_map.items():
            if df.empty: continue
            last_close = df['close'].iloc[-1]
            change_pct = ((last_close - df['open'].iloc[0]) / df['open'].iloc[0]) * 100
            stats[tf] = {
                "bars": len(df),
                "last_price": last_close,
                "period_change_pct": round(change_pct, 2)
            }
        return stats

    def _generate_report(self, strategy: str, symbol: str, features: dict) -> str:
        lines = [f"# Deep Market Analysis: {symbol}", f"**Strategy:** {strategy}", ""]
        lines.append("## Data Collection Report")
        for tf, stat in features.items():
            lines.append(f"- **{tf}:** {stat['bars']} bars loaded. Price: {stat['last_price']} ({stat['period_change_pct']}%) ")
        
        lines.append("\n## Analysis Context")
        lines.append("Daten wurden erfolgreich live von der API abgerufen. Die technische Analyse und LLM-Bewertung folgen in der nächsten Ausbaustufe.")
        return "\n".join(lines)