"""
Script to simplify _get_signal_callback method (394 LOC → 80 LOC).

Removes:
- Pre-calculation logic (not needed, IndicatorEngine has cache)
- Fallback calculation function (one method is enough)
- Custom cache state (IndicatorEngine already caches)
- Complex lookup logic (overhead not worth it)
- 50+ lines of commented-out thoughts
"""

from pathlib import Path

SOURCE_FILE = Path("src/ui/widgets/bitunix_trading/backtest_tab.py")

# Simplified method
SIMPLIFIED_METHOD = '''    def _get_signal_callback(self) -> Optional[Callable]:
        """
        Erstellt Signal-Callback für Backtest.

        Simplified: Nutzt IndicatorEngine Cache (kein eigenes Pre-Calculation nötig).

        Returns:
            Callable: Signal-Callback Funktion oder None
        """
        # Sammle aktuelle Engine-Configs
        engine_configs = self.collect_engine_configs()

        # Prüfe ob parent (ChartWindow) eine signal_callback hat
        chart_window = self._find_chart_window()
        if chart_window and hasattr(chart_window, 'get_signal_callback'):
            callback = chart_window.get_signal_callback()
            if callback:
                logger.info("Using ChartWindow signal callback for backtest")
                return callback

        # Prüfe ob wir direkten Zugriff auf die Trading Bot Engines haben
        if hasattr(self, '_signal_generator'):
            return self._signal_generator.generate_signal

        # Erstelle Signal-Pipeline mit Engine-Configs
        try:
            from src.core.trading_bot import EntryScoreEngine
            from src.core.indicators import IndicatorEngine, IndicatorConfig, IndicatorType
            import pandas as pd

            # Build Entry Config from engine settings
            entry_config = self._build_entry_config(engine_configs)

            # Engine Settings
            min_score_for_signal = engine_configs.get('entry_score', {}).get('min_score_for_entry', 0.50)
            tp_atr_mult = engine_configs.get('trigger_exit', {}).get('tp_atr_multiplier', 2.0)
            sl_atr_mult = engine_configs.get('trigger_exit', {}).get('sl_atr_multiplier', 1.5)

            # Create engines (IndicatorEngine has built-in cache!)
            indicator_engine = IndicatorEngine(cache_size=500)
            entry_engine = EntryScoreEngine(config=entry_config) if entry_config else EntryScoreEngine()

            def backtest_signal_callback(candle, history_1m, mtf_data):
                """Simplified signal callback for backtest."""
                if history_1m is None or len(history_1m) < 50:
                    return None

                try:
                    # Calculate indicators (IndicatorEngine caches automatically!)
                    df = self._calculate_indicators(history_1m, indicator_engine)

                    # Calculate entry score
                    score_result = entry_engine.calculate(
                        df,
                        regime_result=None,  # Skip regime for speed
                        symbol="BTCUSDT",
                        timeframe="1m"
                    )

                    if not score_result or score_result.final_score < min_score_for_signal:
                        return None

                    # Get ATR for SL/TP
                    atr = df['atr_14'].iloc[-1] if 'atr_14' in df.columns else (candle.close * 0.02)
                    current_price = candle.close
                    direction_str = score_result.direction.value if hasattr(score_result.direction, 'value') else str(score_result.direction)

                    # Generate signal
                    if direction_str == "LONG":
                        return {
                            "action": "buy",
                            "stop_loss": current_price - (atr * sl_atr_mult),
                            "take_profit": current_price + (atr * tp_atr_mult),
                            "sl_distance": atr * sl_atr_mult,
                            "leverage": 1,
                            "reason": f"Score: {score_result.final_score:.2f}",
                            "confidence": score_result.final_score,
                            "atr": atr,
                        }
                    elif direction_str == "SHORT":
                        return {
                            "action": "sell",
                            "stop_loss": current_price + (atr * sl_atr_mult),
                            "take_profit": current_price - (atr * tp_atr_mult),
                            "sl_distance": atr * sl_atr_mult,
                            "leverage": 1,
                            "reason": f"Score: {score_result.final_score:.2f}",
                            "confidence": score_result.final_score,
                            "atr": atr,
                        }

                except Exception as e:
                    logger.warning(f"Signal generation error: {e}")

                return None

            logger.info("Signal callback created with simplified logic")
            return backtest_signal_callback

        except ImportError as e:
            logger.warning(f"Could not create signal callback: {e}")
            return None

    def _build_entry_config(self, engine_configs: dict):
        """Build EntryScoreConfig from engine settings."""
        from src.core.trading_bot import EntryScoreConfig

        if not HAS_ENTRY_SCORE or 'entry_score' not in engine_configs:
            return None

        try:
            es = engine_configs['entry_score']
            return EntryScoreConfig(
                weight_trend_alignment=es.get('weights', {}).get('trend_alignment', 0.25),
                weight_momentum_rsi=es.get('weights', {}).get('rsi', 0.15),
                weight_momentum_macd=es.get('weights', {}).get('macd', 0.20),
                weight_trend_strength=es.get('weights', {}).get('adx', 0.15),
                weight_volatility=es.get('weights', {}).get('volatility', 0.10),
                weight_volume=es.get('weights', {}).get('volume', 0.15),
                threshold_excellent=es.get('thresholds', {}).get('excellent', 0.80),
                threshold_good=es.get('thresholds', {}).get('good', 0.65),
                threshold_moderate=es.get('thresholds', {}).get('moderate', 0.50),
                threshold_weak=es.get('thresholds', {}).get('weak', 0.35),
                min_score_for_entry=es.get('min_score_for_entry', 0.50),
                block_in_chop_range=es.get('gates', {}).get('block_in_chop', True),
                block_against_strong_trend=es.get('gates', {}).get('block_against_strong_trend', True),
                allow_counter_trend_sfp=es.get('gates', {}).get('allow_counter_trend_sfp', True),
                regime_boost_strong_trend=es.get('gates', {}).get('trend_boost', 0.10),
                regime_penalty_chop=es.get('gates', {}).get('chop_penalty', -0.15),
                regime_penalty_volatile=es.get('gates', {}).get('volatile_penalty', -0.10),
            )
        except Exception as e:
            logger.warning(f"EntryScoreConfig error: {e}")
            return None

    def _calculate_indicators(self, df, indicator_engine):
        """
        Calculate indicators with IndicatorEngine (uses internal cache).

        Simplified: No custom cache logic needed!
        """
        from src.core.indicators import IndicatorConfig, IndicatorType
        import pandas as pd

        result = df.copy()

        try:
            # EMA 20, 50
            for period in [20, 50]:
                config = IndicatorConfig(IndicatorType.EMA, {"period": period, "price": "close"}, use_talib=True)
                result[f"ema_{period}"] = indicator_engine.calculate(result, config).values

            # RSI 14
            config = IndicatorConfig(IndicatorType.RSI, {"period": 14}, use_talib=True)
            result["rsi_14"] = indicator_engine.calculate(result, config).values

            # ADX 14
            config = IndicatorConfig(IndicatorType.ADX, {"period": 14}, use_talib=True)
            adx_result = indicator_engine.calculate(result, config)
            if isinstance(adx_result.values, pd.DataFrame):
                result["adx_14"] = adx_result.values["adx"]
                result["plus_di"] = adx_result.values.get("plus_di", 0)
                result["minus_di"] = adx_result.values.get("minus_di", 0)

            # ATR 14
            config = IndicatorConfig(IndicatorType.ATR, {"period": 14}, use_talib=True)
            result["atr_14"] = indicator_engine.calculate(result, config).values

        except Exception as e:
            logger.warning(f"Indicator calculation error: {e}")

        return result
'''

def simplify():
    """Simplify the _get_signal_callback method."""
    print("=" * 80)
    print("🔧 SIMPLIFYING _get_signal_callback")
    print("=" * 80)

    # Read original file
    with open(SOURCE_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    print(f"\n📊 Original file: {len(lines)} lines")

    # Find method boundaries
    start_line = None
    end_line = None

    for i, line in enumerate(lines, 1):
        if 'def _get_signal_callback' in line and start_line is None:
            start_line = i
        if start_line and i > start_line + 10 and line.strip().startswith('def _on_load_configs_clicked'):
            end_line = i
            break

    if not start_line or not end_line:
        print("❌ Could not find method boundaries")
        return

    print(f"📍 Method found: lines {start_line}-{end_line - 1} ({end_line - start_line} lines)")

    # Build new content
    new_content = []

    # Part 1: Before method (lines 1 to start_line-1)
    new_content.extend(lines[:start_line - 1])

    # Part 2: Simplified method
    new_content.append(SIMPLIFIED_METHOD)
    new_content.append('\n')

    # Part 3: After method (lines end_line to end)
    new_content.extend(lines[end_line - 1:])

    # Write new file
    with open(SOURCE_FILE, 'w', encoding='utf-8') as f:
        f.writelines(new_content)

    print(f"\n✅ Simplified file: {len(new_content)} lines")
    print(f"📉 Reduction: {len(lines) - len(new_content)} lines removed")
    print(f"📊 Method: {end_line - start_line} LOC → ~130 LOC")
    print("\n" + "=" * 80)
    print("✅ SIMPLIFICATION COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    simplify()
