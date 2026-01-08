"""Orchestrator for the Deep Analysis Run.

Coordinates:
1. Data Collection (Multi-TF) using HistoryManager
2. Feature Calculation
3. Payload Assembly
4. LLM Request (real AI integration)
"""

import asyncio
import logging
import time
import pandas as pd
from datetime import datetime, timedelta, timezone
from PyQt6.QtCore import QThread, pyqtSignal
from src.core.analysis.context import AnalysisContext
from src.core.market_data.types import DataRequest, Timeframe
from src.core.indicators.engine import IndicatorEngine
from src.core.indicators.types import IndicatorConfig, IndicatorType

logger = logging.getLogger(__name__)

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
        self.indicator_engine = IndicatorEngine()
        self._ai_service = None
        self._llm_analysis: str | None = None  # Stores LLM response

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

            # 4. LLM Generation (Real AI Integration)
            self.status_update.emit("Generiere KI-Analyse (Deep Reasoning)...")
            try:
                self._llm_analysis = self._loop.run_until_complete(
                    self._call_llm(strat.name, symbol, features)
                )
                if self._llm_analysis:
                    logger.info("LLM analysis completed successfully")
                else:
                    logger.warning("LLM returned empty response, using fallback report")
            except Exception as e:
                logger.error(f"LLM analysis failed: {e}", exc_info=True)
                self._llm_analysis = None
                self.status_update.emit(f"LLM-Analyse fehlgeschlagen: {e}")
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

    async def _call_llm(self, strategy: str, symbol: str, features: dict) -> str | None:
        """Call the configured LLM for deep market analysis.

        Args:
            strategy: Strategy name
            symbol: Trading symbol
            features: Dict of timeframe -> feature data

        Returns:
            LLM analysis as markdown string, or None if failed
        """
        try:
            from src.ai.ai_provider_factory import AIProviderFactory
            from src.ai.prompts import PromptTemplates

            # Check if AI is enabled
            if not AIProviderFactory.is_ai_enabled():
                logger.info("AI features are disabled in settings")
                return None

            # Create AI service
            logger.info("Creating AI service for deep analysis...")
            self._ai_service = AIProviderFactory.create_service()
            await self._ai_service.initialize()

            # Build the prompt
            technical_data = self._format_features_for_prompt(features)
            sr_levels = self._format_sr_levels_for_prompt(features)

            prompt = PromptTemplates.DEEP_ANALYSIS.format(
                symbol=symbol,
                strategy=strategy,
                technical_data=technical_data,
                sr_levels=sr_levels
            )

            # Call LLM
            logger.info(f"Calling LLM for deep analysis ({symbol})...")
            messages = [
                {"role": "system", "content": "Du bist ein erfahrener Trading-Analyst für Kryptowährungen. Antworte auf Deutsch im Markdown-Format."},
                {"role": "user", "content": prompt}
            ]

            response = await self._ai_service.chat_completion(
                messages=messages,
                temperature=0.3  # Lower temperature for more focused analysis
            )

            # Cleanup
            await self._ai_service.close()
            self._ai_service = None

            logger.info(f"LLM response received ({len(response)} chars)")
            return response

        except ValueError as e:
            # AI disabled or no API key
            logger.warning(f"AI service not available: {e}")
            return None
        except Exception as e:
            logger.error(f"LLM call failed: {e}", exc_info=True)
            if self._ai_service:
                try:
                    await self._ai_service.close()
                except Exception:
                    pass
                self._ai_service = None
            return None

    def _format_features_for_prompt(self, features: dict) -> str:
        """Format feature data for LLM prompt."""
        lines = []

        # Sort timeframes by duration (smallest first)
        tf_order = {"1m": 1, "5m": 2, "15m": 3, "30m": 4, "1h": 5, "4h": 6, "1D": 7, "1W": 8, "1M": 9}
        sorted_tfs = sorted(features.keys(), key=lambda x: tf_order.get(x, 99))

        for tf in sorted_tfs:
            data = features[tf]
            role = self._get_tf_role(tf)

            lines.append(f"### {tf} ({role})")
            lines.append(f"- **Anzahl Bars:** {data.get('bars', 'N/A')}")
            lines.append(f"- **Letzter Preis:** {data.get('last_price', 'N/A')}")
            lines.append(f"- **Periode Änderung:** {data.get('period_change_pct', 0)}%")
            lines.append(f"- **Trend:** {data.get('trend_state', 'Neutral')}")
            lines.append(f"- **EMA(20):** {data.get('ema20', 'N/A')} (Distanz: {data.get('ema20_distance_pct', 0)}%)")
            lines.append(f"- **RSI(14):** {data.get('rsi', 50)} - {data.get('rsi_state', 'Neutral')}")
            lines.append(f"- **BB %B:** {data.get('bb_percent', 50)}%")
            lines.append(f"- **ATR(14):** {data.get('atr', 0)} ({data.get('atr_pct', 0)}% des Preises)")
            lines.append(f"- **ADX(14):** {data.get('adx', 0)} (Trendstärke)")
            lines.append("")

        return "\n".join(lines)

    def _format_sr_levels_for_prompt(self, features: dict) -> str:
        """Format support/resistance levels for LLM prompt."""
        all_support = []
        all_resistance = []

        for tf, data in features.items():
            support = data.get('support_levels', [])
            resistance = data.get('resistance_levels', [])

            if support:
                all_support.extend([(tf, level) for level in support])
            if resistance:
                all_resistance.extend([(tf, level) for level in resistance])

        lines = []

        if all_resistance:
            lines.append("**Resistance:**")
            for tf, level in sorted(all_resistance, key=lambda x: x[1], reverse=True)[:5]:
                lines.append(f"- {level} ({tf})")
            lines.append("")

        if all_support:
            lines.append("**Support:**")
            for tf, level in sorted(all_support, key=lambda x: x[1], reverse=True)[:5]:
                lines.append(f"- {level} ({tf})")

        if not lines:
            lines.append("*Keine signifikanten Support/Resistance Levels erkannt.*")

        return "\n".join(lines)

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
        """Extract technical analysis features for each timeframe."""
        features = {}

        for tf, df in data_map.items():
            if df.empty:
                continue

            try:
                # Basic stats
                last_close = df['close'].iloc[-1]
                change_pct = ((last_close - df['open'].iloc[0]) / df['open'].iloc[0]) * 100

                # RSI (14)
                rsi_config = IndicatorConfig(
                    indicator_type=IndicatorType.RSI,
                    params={'period': 14}
                )
                rsi_result = self.indicator_engine.calculate(df, rsi_config)
                rsi_value = float(rsi_result.values.iloc[-1]) if isinstance(rsi_result.values, pd.Series) else 50.0

                # Determine RSI state
                if rsi_value > 70:
                    rsi_state = "Overbought"
                elif rsi_value < 30:
                    rsi_state = "Oversold"
                else:
                    rsi_state = "Neutral"

                # EMA (20)
                ema_config = IndicatorConfig(
                    indicator_type=IndicatorType.EMA,
                    params={'period': 20, 'price': 'close'}
                )
                ema_result = self.indicator_engine.calculate(df, ema_config)
                ema_value = float(ema_result.values.iloc[-1]) if isinstance(ema_result.values, pd.Series) else last_close
                ema_distance_pct = ((last_close - ema_value) / ema_value) * 100

                # Determine trend state from EMA
                if ema_distance_pct > 1.0:
                    trend_state = "Strong Uptrend"
                elif ema_distance_pct > 0:
                    trend_state = "Uptrend"
                elif ema_distance_pct < -1.0:
                    trend_state = "Strong Downtrend"
                elif ema_distance_pct < 0:
                    trend_state = "Downtrend"
                else:
                    trend_state = "Neutral"

                # Bollinger Bands
                bb_config = IndicatorConfig(
                    indicator_type=IndicatorType.BB,
                    params={'period': 20, 'std': 2}
                )
                bb_result = self.indicator_engine.calculate(df, bb_config)

                if isinstance(bb_result.values, pd.DataFrame):
                    bb_upper = float(bb_result.values['upper'].iloc[-1])
                    bb_middle = float(bb_result.values['middle'].iloc[-1])
                    bb_lower = float(bb_result.values['lower'].iloc[-1])
                    bb_percent = ((last_close - bb_lower) / (bb_upper - bb_lower)) * 100 if bb_upper != bb_lower else 50.0
                else:
                    bb_percent = 50.0

                # ATR (14)
                atr_config = IndicatorConfig(
                    indicator_type=IndicatorType.ATR,
                    params={'period': 14}
                )
                atr_result = self.indicator_engine.calculate(df, atr_config)
                atr_value = float(atr_result.values.iloc[-1]) if isinstance(atr_result.values, pd.Series) else 0.0
                atr_pct = (atr_value / last_close) * 100 if last_close > 0 else 0.0

                # ADX (14)
                adx_config = IndicatorConfig(
                    indicator_type=IndicatorType.ADX,
                    params={'period': 14}
                )
                adx_result = self.indicator_engine.calculate(df, adx_config)

                if isinstance(adx_result.values, pd.DataFrame) and 'adx' in adx_result.values.columns:
                    adx_value = float(adx_result.values['adx'].iloc[-1])
                elif isinstance(adx_result.values, pd.Series):
                    adx_value = float(adx_result.values.iloc[-1])
                else:
                    adx_value = 0.0

                # Support/Resistance Levels
                sr_config = IndicatorConfig(
                    indicator_type=IndicatorType.SUPPORT_RESISTANCE,
                    params={'window': 20, 'num_levels': 3}
                )
                sr_result = self.indicator_engine.calculate(df, sr_config)

                support_levels = []
                resistance_levels = []
                if isinstance(sr_result.values, dict):
                    support_levels = sr_result.values.get('support', [])
                    resistance_levels = sr_result.values.get('resistance', [])

                features[tf] = {
                    "bars": len(df),
                    "last_price": last_close,
                    "period_change_pct": round(change_pct, 2),
                    "rsi": round(rsi_value, 2),
                    "rsi_state": rsi_state,
                    "ema20": round(ema_value, 4),
                    "ema20_distance_pct": round(ema_distance_pct, 2),
                    "trend_state": trend_state,
                    "bb_percent": round(bb_percent, 2),
                    "atr": round(atr_value, 4),
                    "atr_pct": round(atr_pct, 2),
                    "adx": round(adx_value, 2),
                    "support_levels": [round(x, 4) for x in support_levels],
                    "resistance_levels": [round(x, 4) for x in resistance_levels]
                }

            except Exception as e:
                # Safe fallback with basic stats only
                features[tf] = {
                    "bars": len(df),
                    "last_price": last_close,
                    "period_change_pct": round(change_pct, 2),
                    "rsi": 50.0,
                    "rsi_state": "Neutral",
                    "ema20": last_close,
                    "ema20_distance_pct": 0.0,
                    "trend_state": "Neutral",
                    "bb_percent": 50.0,
                    "atr": 0.0,
                    "atr_pct": 0.0,
                    "adx": 0.0,
                    "support_levels": [],
                    "resistance_levels": [],
                    "error": str(e)
                }

        return features

    def _get_tf_role(self, tf: str) -> str:
        """Map timeframe to analysis role."""
        role_map = {
            "1m": "EXECUTION",
            "5m": "EXECUTION",
            "15m": "CONTEXT",
            "30m": "CONTEXT",
            "1h": "TREND",
            "4h": "TREND",
            "1D": "MACRO",
            "1W": "MACRO",
            "1M": "MACRO"
        }
        return role_map.get(tf, "CONTEXT")

    def _format_technical_summary(self, tf: str, feature_data: dict) -> list[str]:
        """Format technical indicators for a timeframe."""
        lines = []
        role = self._get_tf_role(tf)

        lines.append(f"### {tf} ({role})")
        lines.append(f"- **Price:** {feature_data.get('last_price', 'N/A')} ({feature_data.get('period_change_pct', 0)}%)")
        lines.append(f"- **Trend:** {feature_data.get('trend_state', 'N/A')} (EMA20 dist: {feature_data.get('ema20_distance_pct', 0)}%)")
        lines.append(f"- **RSI(14):** {feature_data.get('rsi', 'N/A')} - {feature_data.get('rsi_state', 'N/A')}")
        lines.append(f"- **BB %B:** {feature_data.get('bb_percent', 'N/A')}%")
        lines.append(f"- **ATR(14):** {feature_data.get('atr', 'N/A')} ({feature_data.get('atr_pct', 0)}% of price)")
        lines.append(f"- **ADX(14):** {feature_data.get('adx', 'N/A')} (Trend Strength)")

        if feature_data.get('error'):
            lines.append(f"- **Note:** Some indicators unavailable: {feature_data['error']}")

        lines.append("")
        return lines

    def _format_levels_summary(self, features: dict, symbol: str) -> list[str]:
        """Aggregate support/resistance levels across timeframes."""
        lines = []
        all_support = []
        all_resistance = []

        for tf, data in features.items():
            support = data.get('support_levels', [])
            resistance = data.get('resistance_levels', [])

            if support:
                all_support.extend([(tf, level) for level in support])
            if resistance:
                all_resistance.extend([(tf, level) for level in resistance])

        if all_resistance:
            lines.append("**Resistance Levels:**")
            for tf, level in sorted(all_resistance, key=lambda x: x[1], reverse=True)[:5]:
                lines.append(f"- {level} ({tf})")
            lines.append("")

        if all_support:
            lines.append("**Support Levels:**")
            for tf, level in sorted(all_support, key=lambda x: x[1], reverse=True)[:5]:
                lines.append(f"- {level} ({tf})")
            lines.append("")

        return lines

    def _generate_trading_setup(self, features: dict, symbol: str) -> list[str]:
        """Generate preliminary trading setup based on technical analysis."""
        lines = []

        # Use the smallest timeframe for execution details
        exec_tf = None
        for tf in ["1m", "5m", "15m"]:
            if tf in features:
                exec_tf = tf
                break

        if not exec_tf:
            lines.append("*Insufficient data for trading setup*")
            return lines

        data = features[exec_tf]
        current_price = data.get('last_price', 0)
        atr = data.get('atr', 0)
        trend = data.get('trend_state', 'Neutral')

        if current_price == 0 or atr == 0:
            lines.append("*Insufficient data for trading setup*")
            return lines

        # Calculate entry, target, and stop based on trend
        if "Uptrend" in trend:
            # Long setup
            entry = current_price
            target = entry + (2 * atr)
            stop_loss = entry - (1.5 * atr)
            direction = "LONG"
        elif "Downtrend" in trend:
            # Short setup
            entry = current_price
            target = entry - (2 * atr)
            stop_loss = entry + (1.5 * atr)
            direction = "SHORT"
        else:
            # Neutral - no clear setup
            lines.append(f"*No clear directional bias. Current price: {current_price}*")
            return lines

        risk = abs(entry - stop_loss)
        reward = abs(target - entry)
        rr_ratio = reward / risk if risk > 0 else 0

        lines.append(f"**Direction:** {direction}")
        lines.append(f"**Entry:** {round(entry, 4)}")
        lines.append(f"**Target:** {round(target, 4)}")
        lines.append(f"**Stop Loss:** {round(stop_loss, 4)}")
        lines.append(f"**Risk/Reward:** 1:{round(rr_ratio, 2)}")
        lines.append("")
        lines.append("*Note: This is a preliminary setup based on technical indicators. Not financial advice.*")

        return lines

    def _generate_report(self, strategy: str, symbol: str, features: dict) -> str:
        """Generate comprehensive markdown report.

        If LLM analysis is available, it will be used as the primary content.
        Otherwise, falls back to the rule-based technical analysis report.
        """
        # If we have LLM analysis, use it as the primary report
        if self._llm_analysis:
            lines = [f"# Deep Market Analysis: {symbol}", f"**Strategy:** {strategy}", ""]
            lines.append("---")
            lines.append("")
            lines.append(self._llm_analysis)
            lines.append("")
            lines.append("---")
            lines.append("")

            # Add data collection summary at the end
            lines.append("## Datengrundlage")
            for tf, stat in features.items():
                bars = stat.get('bars', 0)
                price = stat.get('last_price', 'N/A')
                change = stat.get('period_change_pct', 0)
                lines.append(f"- **{tf}:** {bars} Bars geladen. Preis: {price} ({change}%)")
            lines.append("")
            lines.append(f"*Analyse generiert mit KI-Unterstützung ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})*")

            return "\n".join(lines)

        # Fallback: Rule-based report (no LLM available)
        lines = [f"# Deep Market Analysis: {symbol}", f"**Strategy:** {strategy}", ""]
        lines.append("*Hinweis: LLM-Analyse nicht verfügbar. Fallback auf regelbasierte Analyse.*")
        lines.append("")

        # Data Collection Summary
        lines.append("## Data Collection Report")
        for tf, stat in features.items():
            bars = stat.get('bars', 0)
            price = stat.get('last_price', 'N/A')
            change = stat.get('period_change_pct', 0)
            lines.append(f"- **{tf}:** {bars} bars loaded. Price: {price} ({change}%)")
        lines.append("")

        # Technical Analysis Summary
        lines.append("## Technical Analysis Summary")
        for tf in sorted(features.keys()):
            lines.extend(self._format_technical_summary(tf, features[tf]))

        # Support/Resistance Levels
        lines.append("## Support/Resistance Levels")
        lines.extend(self._format_levels_summary(features, symbol))

        # Trading Setup
        lines.append("## Trading Setup (Preliminary)")
        lines.extend(self._generate_trading_setup(features, symbol))
        lines.append("")

        # Footer
        lines.append("## Analysis Context")
        lines.append("Daten wurden erfolgreich live von der API abgerufen. LLM-Analyse war nicht verfügbar (API-Key fehlt oder AI deaktiviert).")
        lines.append("")
        lines.append("**Zur Aktivierung der KI-Analyse:**")
        lines.append("1. Settings → AI → AI Provider wählen")
        lines.append("2. API-Key als Umgebungsvariable setzen (z.B. OPENAI_API_KEY)")
        lines.append("3. AI aktivieren (Checkbox)")

        return "\n".join(lines)