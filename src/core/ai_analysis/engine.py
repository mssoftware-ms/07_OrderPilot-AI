import pandas as pd
import logging
from typing import Optional
from datetime import datetime, timezone

from src.core.ai_analysis.types import AIAnalysisOutput, AIAnalysisInput
from src.core.ai_analysis.validators import DataValidator
from src.core.ai_analysis.regime import RegimeDetector
from src.core.ai_analysis.features import FeatureEngineer
from src.core.ai_analysis.prompt import PromptComposer
from src.core.ai_analysis.openai_client import OpenAIClient

logger = logging.getLogger(__name__)

class AIAnalysisEngine:
    """
    Orchestrator for the AI Analysis Workflow.
    Connects Data -> Validation -> Regime -> Features -> Prompt -> LLM -> Result.
    """

    def __init__(self, api_key: str):
        self.validator = DataValidator()
        self.regime_detector = RegimeDetector()
        self.feature_engineer = FeatureEngineer()
        self.prompt_composer = PromptComposer()
        self.client = OpenAIClient(api_key=api_key)
        self._is_running = False

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
            logger.warning("Analysis already running for this engine instance.")
            return None # Or wait

        self._is_running = True
        try:
            # 1. Validate
            # TODO: Infer interval from timeframe string (e.g. "1h" -> 60)
            # For now hardcoded or safe default, assuming DataValidator is robust.
            is_valid, error = self.validator.validate_data(df, interval_minutes=5) 
            if not is_valid:
                logger.warning(f"Validation failed: {error}")
                # We return None, but maybe we should return an error object?
                # The prompt asks for Output. For now None + Log is fine.
                return None

            # 1b. Clean (Optional per checklist, but good practice)
            df_clean = self.validator.clean_data(df)

            # 2. Regime
            regime = self.regime_detector.detect_regime(df_clean)
            logger.info(f"Detected Regime for {symbol}: {regime}")

            # 3. Features
            technicals = self.feature_engineer.extract_technicals(df_clean)
            structure = self.feature_engineer.extract_structure(df_clean)
            summary = self.feature_engineer.summarize_candles(df_clean)

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

            # 6. Call LLM
            result = await self.client.analyze(sys_prompt, user_prompt, model=model)
            
            return result

        except Exception as e:
            logger.error(f"Analysis run failed: {e}", exc_info=True)
            return None
        finally:
            self._is_running = False