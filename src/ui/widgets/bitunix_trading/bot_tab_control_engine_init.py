"""Bot Tab Control Engine Init - Engine Initialization and Config Management.

Refactored from 1,160 LOC monolith using composition pattern.

Module 1/6 of bot_tab_control.py split.

Contains:
- _initialize_new_engines(): Initialize all 7 trading engines
- update_engine_configs(): Reload configs and apply to running engines
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class BotTabControlEngineInit:
    """Helper für Engine Initialization und Config Management."""

    def __init__(self, parent):
        """
        Args:
            parent: BotTabControl Instanz
        """
        self.parent = parent

    def _initialize_new_engines(self) -> None:
        """Initialisiert die neuen Engines (Phase 1-4).

        Diese Methode erstellt alle neuen Trading-Engines:
        - MarketContextBuilder: Baut MarketContext aus DataFrame
        - RegimeDetectorService: Erkennt Markt-Regime
        - LevelEngine: Erkennt Support/Resistance Levels
        - EntryScoreEngine: Berechnet normalisierten Entry-Score
        - LLMValidationService: AI-Validierung (Quick→Deep)
        - TriggerExitEngine: Entry-Trigger + Exit-Management
        - LeverageRulesEngine: Dynamisches Leverage-Regelwerk
        """
        try:
            from src.core.trading_bot import (
                EntryScoreConfig,
                EntryScoreEngine,
                LevelEngine,
                LevelEngineConfig,
                LeverageRulesConfig,
                LeverageRulesEngine,
                LLMValidationConfig,
                LLMValidationService,
                MarketContextBuilder,
                MarketContextBuilderConfig,
                RegimeConfig,
                RegimeDetectorService,
                TriggerExitConfig,
                TriggerExitEngine,
            )

            # 1. MarketContextBuilder - Single Source of Truth
            builder_config = MarketContextBuilderConfig(
                enable_caching=True,
                enable_preflight=True,
                require_regime=True,
                require_levels=True,
            )
            self.parent.parent._context_builder = MarketContextBuilder(config=builder_config)
            logger.info("✅ MarketContextBuilder initialized")

            # 2. RegimeDetectorService
            regime_config = RegimeConfig(
                trend_lookback=50,
                volatility_lookback=20,
                threshold_strong_trend=0.7,
                threshold_weak_trend=0.4,
                threshold_chop=0.3,
            )
            self.parent.parent._regime_detector = RegimeDetectorService(config=regime_config)
            logger.info("✅ RegimeDetectorService initialized")

            # 3. LevelEngine
            level_config = LevelEngineConfig(
                swing_lookback=20,
                min_touches=2,
                price_tolerance_pct=0.5,
                enable_daily_levels=True,
                enable_weekly_levels=True,
            )
            self.parent.parent._level_engine = LevelEngine(config=level_config)
            logger.info("✅ LevelEngine initialized")

            # 4. EntryScoreEngine
            entry_config = EntryScoreConfig(
                # Weights
                weight_trend=0.25,
                weight_rsi=0.15,
                weight_macd=0.15,
                weight_adx=0.15,
                weight_volatility=0.15,
                weight_volume=0.15,
                # Quality thresholds
                score_excellent=0.8,
                score_good=0.6,
                score_acceptable=0.4,
            )
            self.parent.parent._entry_score_engine = EntryScoreEngine(config=entry_config)
            logger.info("✅ EntryScoreEngine initialized")

            # 5. LLMValidationService
            llm_config = LLMValidationConfig(
                quick_threshold_score=0.7,
                deep_threshold_score=0.5,
                veto_modifier=-0.3,
                boost_modifier=0.2,
                enable_quick=True,
                enable_deep=True,
            )
            self.parent.parent._llm_validation = LLMValidationService(config=llm_config)
            logger.info("✅ LLMValidationService initialized")

            # 6. TriggerExitEngine
            trigger_config = TriggerExitConfig(
                # Entry triggers
                enable_breakout=True,
                enable_pullback=True,
                enable_sfp=True,
                # Exit settings
                use_atr_stops=True,
                atr_sl_multiplier=2.0,
                atr_tp_multiplier=3.0,
                enable_trailing=True,
            )
            self.parent.parent._trigger_exit_engine = TriggerExitEngine(config=trigger_config)
            logger.info("✅ TriggerExitEngine initialized")

            # 7. LeverageRulesEngine
            leverage_config = LeverageRulesConfig(
                # Asset tiers
                tier_blue_chip_max=5.0,
                tier_mid_cap_max=3.0,
                tier_small_cap_max=2.0,
                # Regime modifiers
                strong_trend_modifier=1.0,
                weak_trend_modifier=0.7,
                chop_range_modifier=0.5,
                volatility_explosive_modifier=0.3,
            )
            self.parent.parent._leverage_engine = LeverageRulesEngine(config=leverage_config)
            logger.info("✅ LeverageRulesEngine initialized")

            self.parent._log("✅ Alle neuen Engines initialisiert (Phase 1-4)")

        except Exception as e:
            logger.exception("Failed to initialize new engines")
            self.parent._log(f"❌ Fehler bei Engine-Initialisierung: {e}")
            raise

    def update_engine_configs(self) -> None:
        """Aktualisiert die Konfiguration aller laufenden Engines.

        Lädt Config-Files und wendet sie auf die laufenden Engine-Instanzen an.
        WICHTIG: Sofort wirksam, kein Bot-Neustart nötig (Punkt 2).
        """
        if not self.parent.parent._context_builder:
            logger.warning("Engines not initialized yet - skipping config update")
            return

        try:
            from src.core.trading_bot import (
                load_entry_score_config,
                load_leverage_config,
                load_llm_validation_config,
                load_trigger_exit_config,
            )

            # 1. Entry Score Config laden und anwenden
            if self.parent.parent._entry_score_engine:
                entry_config = load_entry_score_config()
                self.parent.parent._entry_score_engine.config = entry_config
                logger.info(
                    f"✅ EntryScoreEngine config updated: weights={entry_config.weight_trend}/{entry_config.weight_rsi}/{entry_config.weight_macd}"
                )

            # 2. Trigger/Exit Config laden und anwenden
            if self.parent.parent._trigger_exit_engine:
                trigger_config = load_trigger_exit_config()
                self.parent.parent._trigger_exit_engine.config = trigger_config
                logger.info(
                    f"✅ TriggerExitEngine config updated: breakout={trigger_config.enable_breakout}, pullback={trigger_config.enable_pullback}"
                )

            # 3. Leverage Config laden und anwenden
            if self.parent.parent._leverage_engine:
                leverage_config = load_leverage_config()
                self.parent.parent._leverage_engine.config = leverage_config
                logger.info(f"✅ LeverageRulesEngine config updated: blue_chip_max={leverage_config.tier_blue_chip_max}x")

            # 4. LLM Validation Config laden und anwenden
            if self.parent.parent._llm_validation:
                llm_config = load_llm_validation_config()
                self.parent.parent._llm_validation.config = llm_config
                logger.info(f"✅ LLMValidationService config updated: quick_threshold={llm_config.quick_threshold_score}")

            # Note: RegimeDetector und LevelEngine haben keine Config-Files
            # (nutzen Builder-Config bzw. fest codierte Werte)

            self.parent._log("⚙️ Engine-Konfigurationen aktualisiert (sofort wirksam)")
            logger.info("All engine configs reloaded and applied to running instances")

        except Exception as e:
            logger.exception(f"Failed to update engine configs: {e}")
            self.parent._log(f"❌ Fehler beim Aktualisieren der Engine-Configs: {e}")
