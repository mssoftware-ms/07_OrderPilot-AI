import pandas as pd
import logging
from typing import Optional
from datetime import datetime, timezone
import re

from src.core.ai_analysis.types import AIAnalysisOutput, AIAnalysisInput
from src.core.ai_analysis.validators import DataValidator
from src.core.ai_analysis.regime import RegimeDetector
from src.core.ai_analysis.features import FeatureEngineer
from src.core.ai_analysis.prompt import PromptComposer
from src.core.ai_analysis.openai_client import OpenAIClient

analysis_logger = logging.getLogger('ai_analysis')

class AIAnalysisEngine:
    """
    Orchestrator for the AI Analysis Workflow.
    Connects Data -> Validation -> Regime -> Features -> Prompt -> LLM -> Result.
    """

    def __init__(self, api_key: str):
        # Use larger lag multiplier for historical data analysis
        # Historical data is always at least 1-2 intervals old (last completed candle)
        self.validator = DataValidator(max_lag_multiplier=5.0)
        self.regime_detector = RegimeDetector()
        self.feature_engineer = FeatureEngineer()
        self.prompt_composer = PromptComposer()
        self.client = OpenAIClient(api_key=api_key)
        self._is_running = False

    def apply_prompt_overrides(
        self,
        system_prompt: str | None = None,
        tasks_prompt: str | None = None,
    ) -> None:
        """Inject UI-provided prompt overrides into the composer."""
        self.prompt_composer.set_overrides(system_prompt, tasks_prompt)

    def _timeframe_to_minutes(self, timeframe: str) -> int:
        tf = (timeframe or "").strip().upper()
        m = re.match(r"^(\d+)([A-Z]+)$", tf)
        if not m:
            return 5
        value = int(m.group(1))
        unit = m.group(2)

        if unit == "T":
            return value
        if unit == "H":
            return value * 60
        if unit == "D":
            return value * 60 * 24

        return 5

    async def run_analysis(self, symbol: str, timeframe: str, df: pd.DataFrame, model: Optional[str] = None) -> Optional[AIAnalysisOutput]:
        """
        Main entry point.

        Args:
            symbol: Ticker symbol
            timeframe: Chart timeframe
            df: OHLCV Data
            model: Optional model override

        Returns:
            Analysis result or None if failed.
        """
        if self._is_running:
            analysis_logger.warning("Analysis already running for this engine instance.", extra={
                'symbol': symbol,
                'timeframe': timeframe
            })
            return None # Or wait

        self._is_running = True

        # Determine data type for logging
        data_type = "UNKNOWN"
        if hasattr(df, '_data_source_type'):
            data_type = df._data_source_type
        elif len(df) > 0:
            # Heuristic: if we have real data, it's likely historical
            data_type = "HISTORICAL"

        try:
            analysis_logger.info("Analysis started", extra={
                'symbol': symbol,
                'timeframe': timeframe,
                'data_type': data_type,
                'bars_count': len(df),
                'model': model or 'default'
            })

            # 1. Validate
            interval_minutes = self._timeframe_to_minutes(timeframe)
            is_valid, error = self.validator.validate_data(df, interval_minutes=interval_minutes)
            if not is_valid:
                analysis_logger.warning(f"Data validation failed", extra={
                    'symbol': symbol,
                    'timeframe': timeframe,
                    'validation_error': error,
                    'step': 'validation'
                })
                raise ValueError(error)

            analysis_logger.info("Data validation passed", extra={
                'symbol': symbol,
                'step': 'validation'
            })

            # 1b. Clean (Optional per checklist, but good practice)
            df_clean = self.validator.clean_data(df)
            analysis_logger.info("Data cleaned", extra={
                'symbol': symbol,
                'step': 'cleaning',
                'bars_after_cleaning': len(df_clean)
            })

            # 2. Regime
            regime = self.regime_detector.detect_regime(df_clean)
            analysis_logger.info(f"Regime detection completed", extra={
                'symbol': symbol,
                'timeframe': timeframe,
                'regime': regime,
                'step': 'regime_detection'
            })

            # 3. Features
            technicals = self.feature_engineer.extract_technicals(df_clean)
            structure = self.feature_engineer.extract_structure(df_clean)
            summary = self.feature_engineer.summarize_candles(df_clean)

            analysis_logger.info("Feature engineering completed", extra={
                'symbol': symbol,
                'step': 'feature_engineering',
                'technicals_count': len(technicals.model_fields) if technicals else 0,
                'structure_keys': list(structure.model_fields.keys()) if structure else []
            })

            # 4. Input Construction
            last_ts = df_clean.index[-1]
            # Ensure ISO string
            if isinstance(last_ts, (pd.Timestamp, datetime)):
                 ts_str = last_ts.isoformat()
            else:
                 ts_str = str(last_ts)

            analysis_input = AIAnalysisInput(
                symbol=symbol,
                timeframe=timeframe,
                timestamp=ts_str,
                regime=regime,
                technicals=technicals,
                structure=structure,
                last_candles_summary=summary,
                funding_rate=None, # Optional
                open_interest_change_pct=None # Optional
            )

            # 5. Prompt
            sys_prompt = self.prompt_composer.compose_system_prompt()
            user_prompt = self.prompt_composer.compose_user_prompt(analysis_input)

            analysis_logger.info("Prompts composed", extra={
                'symbol': symbol,
                'step': 'prompt_composition',
                'system_prompt_length': len(sys_prompt),
                'user_prompt_length': len(user_prompt)
            })

            # 6. Call LLM
            analysis_logger.info("Calling LLM", extra={
                'symbol': symbol,
                'step': 'llm_call',
                'model': model or 'default'
            })

            result = await self.client.analyze(sys_prompt, user_prompt, model=model)

            if result:
                analysis_logger.info("Analysis completed successfully", extra={
                    'symbol': symbol,
                    'timeframe': timeframe,
                    'step': 'completion',
                    'result_available': True
                })
            else:
                analysis_logger.warning("Analysis completed but returned None", extra={
                    'symbol': symbol,
                    'timeframe': timeframe,
                    'step': 'completion',
                    'result_available': False
                })

            return result

        except Exception as e:
            analysis_logger.error(f"Analysis run failed", extra={
                'symbol': symbol,
                'timeframe': timeframe,
                'data_type': data_type,
                'error': str(e),
                'error_type': type(e).__name__,
                'step': 'error'
            }, exc_info=True)
            raise
        finally:
            self._is_running = False
