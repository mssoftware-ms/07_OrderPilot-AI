"""Pydantic models for trading strategies and pattern integration."""

from __future__ import annotations

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class PatternCategory(str, Enum):
    """Pattern category classification."""
    REVERSAL = "REVERSAL"
    CONTINUATION = "CONTINUATION"
    SMART_MONEY = "SMART_MONEY"
    BREAKOUT = "BREAKOUT"
    HARMONIC = "HARMONIC"
    SCALPING = "SCALPING"
    RANGE_TRADING = "RANGE_TRADING"
    PRICE_ACTION = "PRICE_ACTION"
    VOLATILITY_SQUEEZE = "VOLATILITY_SQUEEZE"


class StrategyType(str, Enum):
    """Trading strategy types."""
    BREAKOUT_LONG = "BREAKOUT_LONG"
    BREAKOUT_SHORT = "BREAKOUT_SHORT"
    BREAKDOWN_SHORT = "BREAKDOWN_SHORT"
    RETEST_LONG = "RETEST_LONG"
    RETEST_SHORT = "RETEST_SHORT"
    REVERSAL_LONG = "REVERSAL_LONG"
    REVERSAL_SHORT = "REVERSAL_SHORT"
    SCALPING_LONG = "SCALPING_LONG"
    SCALPING_SHORT = "SCALPING_SHORT"
    GRID_TRADING = "GRID_TRADING"
    SQUEEZE_BREAKOUT_LONG = "SQUEEZE_BREAKOUT_LONG"
    SQUEEZE_BREAKOUT_SHORT = "SQUEEZE_BREAKOUT_SHORT"
    PRICE_ACTION_LONG = "PRICE_ACTION_LONG"
    PRICE_ACTION_SHORT = "PRICE_ACTION_SHORT"
    RANGE_BOUNCE_LONG = "RANGE_BOUNCE_LONG"
    RANGE_BOUNCE_SHORT = "RANGE_BOUNCE_SHORT"
    HARMONIC_REVERSAL_LONG = "HARMONIC_REVERSAL_LONG"
    HARMONIC_REVERSAL_SHORT = "HARMONIC_REVERSAL_SHORT"


class TradingStrategy(BaseModel):
    """Trading strategy with proven success metrics."""

    strategy_type: StrategyType
    description: str = Field(..., description="Strategy description in German")
    success_rate: float = Field(..., ge=0, le=100, description="Success rate in percent")
    avg_profit: str = Field(..., description="Average profit range (e.g., '35-50%')")

    # Best Practices
    best_practices: List[str] = Field(default_factory=list, description="List of best practices")

    # Risk Management
    stop_loss_placement: str = Field(..., description="Stop loss placement rule")
    target_calculation: str = Field(..., description="Target price calculation")
    risk_reward_ratio: str = Field(default="1:2", description="Minimum risk-reward ratio")

    # Confirmation Indicators
    volume_confirmation: bool = Field(default=True, description="Requires volume confirmation")
    rsi_condition: Optional[str] = Field(None, description="RSI condition (e.g., '>50')")
    macd_confirmation: bool = Field(default=False, description="MACD crossover confirmation")

    # Additional Filters
    trend_direction: Optional[str] = Field(None, description="Required trend direction")
    timeframe_preference: Optional[str] = Field(None, description="Preferred timeframe")


class PatternStrategyMapping(BaseModel):
    """Mapping between chart pattern and trading strategy."""

    pattern_type: str = Field(..., description="Pattern type (e.g., 'cup_and_handle')")
    pattern_name: str = Field(..., description="Human-readable pattern name")
    category: PatternCategory

    # Strategy
    strategy: TradingStrategy

    # Research Data
    research_period: str = Field(default="2020-2025", description="Research time period")
    study_references: List[str] = Field(default_factory=list, description="Research sources")

    # Phase Classification (for implementation priority)
    implementation_phase: int = Field(default=1, ge=1, le=3, description="Implementation priority (1=highest)")


# Pre-defined strategies from research data
PATTERN_STRATEGIES: Dict[str, PatternStrategyMapping] = {
    "cup_and_handle": PatternStrategyMapping(
        pattern_type="cup_and_handle",
        pattern_name="Cup and Handle",
        category=PatternCategory.REVERSAL,
        implementation_phase=1,
        strategy=TradingStrategy(
            strategy_type=StrategyType.BREAKOUT_LONG,
            description="Breakout-Long nach Handle",
            success_rate=95.0,
            avg_profit="35-50%",
            best_practices=[
                "Höchste Erfolgsrate aller Patterns",
                "U-förmiger Cup (keine V-Form)",
                "Handle: 1/3 der Cup-Tiefe",
                "Mindest-Formation: 7 Wochen"
            ],
            stop_loss_placement="Unterhalb Handle-Low",
            target_calculation="Cup-Tiefe vom Breakout-Punkt addieren",
            risk_reward_ratio="1:3",
            volume_confirmation=True,
            rsi_condition=">50",
            trend_direction="BULL"
        ),
        study_references=[
            "VT Markets Chart Patterns Guide 2025",
            "Liberated Stock Trader - 12 Data-Proven Chart Patterns"
        ]
    ),

    "head_and_shoulders_top": PatternStrategyMapping(
        pattern_type="head_and_shoulders_top",
        pattern_name="Head & Shoulders (Top)",
        category=PatternCategory.REVERSAL,
        implementation_phase=1,
        strategy=TradingStrategy(
            strategy_type=StrategyType.BREAKDOWN_SHORT,
            description="Breakdown-Short nach Neckline-Bruch",
            success_rate=91.0,  # Average of 89-93%
            avg_profit="23%",
            best_practices=[
                "Warte auf komplette Formation",
                "Volumen-Bestätigung am Bruch",
                "MACD Crossover erhöht Rate auf 81%",
                "Target: Höhe der Schulter abgetragen"
            ],
            stop_loss_placement="Oberhalb rechter Schulter",
            target_calculation="Abstand Head zu Neckline vom Breakpoint subtrahieren",
            risk_reward_ratio="1:2",
            volume_confirmation=True,
            macd_confirmation=True,
            trend_direction="BEAR"
        ),
        study_references=[
            "Quantified Strategies - Head and Shoulders Backtest",
            "Trader Vue - H&S Complete Guide"
        ]
    ),

    "double_top": PatternStrategyMapping(
        pattern_type="double_top",
        pattern_name="Double Top",
        category=PatternCategory.REVERSAL,
        implementation_phase=1,
        strategy=TradingStrategy(
            strategy_type=StrategyType.BREAKDOWN_SHORT,
            description="Short bei Neckline-Break + Retest",
            success_rate=88.0,
            avg_profit="15-20%",
            best_practices=[
                "Beide Tops auf gleichem Level (±2%)",
                "Volumen am 2. Top niedriger",
                "Bearish Divergence (RSI) verstärkt Signal",
                "Target: Höhe des Patterns"
            ],
            stop_loss_placement="Oberhalb höheres Top",
            target_calculation="Abstand Tops zu Neckline vom Breakpoint subtrahieren",
            risk_reward_ratio="1:2",
            volume_confirmation=True,
            rsi_condition="Bearish Divergence",
            trend_direction="BEAR"
        )
    ),

    "double_bottom": PatternStrategyMapping(
        pattern_type="double_bottom",
        pattern_name="Double Bottom",
        category=PatternCategory.REVERSAL,
        implementation_phase=1,
        strategy=TradingStrategy(
            strategy_type=StrategyType.BREAKOUT_LONG,
            description="Long bei Neckline-Break + Retest",
            success_rate=88.0,
            avg_profit="18-25%",
            best_practices=[
                "Beide Bottoms auf gleichem Level (±2%)",
                "Volumen am 2. Bottom höher",
                "Bullish Divergence verstärkt",
                "Mit Retest-Filter: Höhere Win-Rate"
            ],
            stop_loss_placement="Unterhalb tieferes Bottom",
            target_calculation="Abstand Bottoms zu Neckline vom Breakpoint addieren",
            risk_reward_ratio="1:2",
            volume_confirmation=True,
            rsi_condition="Bullish Divergence",
            trend_direction="BULL"
        )
    ),

    "triple_bottom": PatternStrategyMapping(
        pattern_type="triple_bottom",
        pattern_name="Triple Bottom",
        category=PatternCategory.REVERSAL,
        implementation_phase=1,
        strategy=TradingStrategy(
            strategy_type=StrategyType.BREAKOUT_LONG,
            description="Long bei Widerstandsbruch",
            success_rate=87.0,
            avg_profit="20-28%",
            best_practices=[
                "Drei Tests auf gleichem Support",
                "Abnehmendes Volumen bei Tests",
                "Explosion am Breakout",
                "Sehr seltenes, aber zuverlässiges Pattern"
            ],
            stop_loss_placement="Unterhalb Triple-Bottom-Low",
            target_calculation="Abstand Bottom zu Resistance vom Breakpoint addieren",
            risk_reward_ratio="1:2.5",
            volume_confirmation=True,
            rsi_condition=">50",
            trend_direction="BULL"
        )
    ),

    "ascending_triangle": PatternStrategyMapping(
        pattern_type="ascending_triangle",
        pattern_name="Ascending Triangle",
        category=PatternCategory.CONTINUATION,
        implementation_phase=1,
        strategy=TradingStrategy(
            strategy_type=StrategyType.BREAKOUT_LONG,
            description="Long-Breakout über Resistance",
            success_rate=83.0,  # In bull markets
            avg_profit="25-35%",
            best_practices=[
                "Höchste Rate in Bull-Märkten (83%)",
                "Flacher Widerstand + steigende Lows",
                "Volumen-Bestätigung zwingend",
                "Mit Retest: Weniger Trades, höhere Win-Rate"
            ],
            stop_loss_placement="Unterhalb letzter steigender Low",
            target_calculation="Triangle-Höhe vom Breakpoint addieren",
            risk_reward_ratio="1:2",
            volume_confirmation=True,
            trend_direction="BULL",
            timeframe_preference="Bull Market"
        ),
        study_references=[
            "Liberated Stock Trader - Ascending Triangle 83% Win Rate",
            "Quantified Strategies - Breakout Triangle Strategy"
        ]
    ),

    # ========================================================================
    # SCALPING PATTERNS (Phase 1)
    # ========================================================================

    "pin_bar_ema_retest": PatternStrategyMapping(
        pattern_type="pin_bar_ema_retest",
        pattern_name="Pin Bar at EMA Retest",
        category=PatternCategory.SCALPING,
        implementation_phase=1,
        strategy=TradingStrategy(
            strategy_type=StrategyType.SCALPING_LONG,
            description="Scalping Entry bei Pin Bar Retest am EMA(34)",
            success_rate=86.0,
            avg_profit="1-3%",
            best_practices=[
                "EMA(34) als dynamischer Support/Resistance",
                "Pin Bar mit langem Docht (2-3x Body)",
                "Stochastic(5,3,3) überkauft/überverkauft",
                "RSI(5-7) Divergence verstärkt",
                "Timeframe: 1-5 Min"
            ],
            stop_loss_placement="Unterhalb/Oberhalb Pin Bar Docht",
            target_calculation="1-3% vom Entry (schnelle Exits)",
            risk_reward_ratio="1:1.5",
            volume_confirmation=True,
            rsi_condition="Divergence optional",
            timeframe_preference="1m-5m"
        ),
        study_references=[
            "Chartmuster Erweitert 2026 - Scalping Strategies",
            "VT Markets - Pin Bar Scalping Guide"
        ]
    ),

    "stochastic_ema_scalping": PatternStrategyMapping(
        pattern_type="stochastic_ema_scalping",
        pattern_name="EMA + Stochastic + Volume Scalping",
        category=PatternCategory.SCALPING,
        implementation_phase=1,
        strategy=TradingStrategy(
            strategy_type=StrategyType.SCALPING_LONG,
            description="Multi-Indikator Scalping mit EMA, Stochastic, RSI",
            success_rate=78.0,
            avg_profit="1-2%",
            best_practices=[
                "EMA(34) Trendfilter",
                "Stochastic(5,3,3) <20 oder >80",
                "RSI(5-7) für Momentum",
                "Volumen 150%+ über Average",
                "Sehr hohe Frequenz (50-100 Trades/Tag)"
            ],
            stop_loss_placement="0.5-1% vom Entry",
            target_calculation="1-2% Target (Quick Profit Taking)",
            risk_reward_ratio="1:1.5",
            volume_confirmation=True,
            rsi_condition="<30 für Long, >70 für Short",
            timeframe_preference="1m-5m"
        ),
        study_references=[
            "Chartmuster Erweitert 2026 - Scalping Module"
        ]
    ),

    # ========================================================================
    # DAYTRADING PATTERNS (Phase 2)
    # ========================================================================

    "bull_flag": PatternStrategyMapping(
        pattern_type="bull_flag",
        pattern_name="Bull Flag",
        category=PatternCategory.CONTINUATION,
        implementation_phase=2,
        strategy=TradingStrategy(
            strategy_type=StrategyType.BREAKOUT_LONG,
            description="Long Continuation nach Flag Breakout",
            success_rate=68.0,
            avg_profit="15-25%",
            best_practices=[
                "Starker Vorbewegung (Pole)",
                "Leichte Abwärtskorrektur (Flag)",
                "Volumen sinkt im Flag",
                "Breakout mit Volumen-Spike",
                "Target: Pole-Länge vom Breakout"
            ],
            stop_loss_placement="Unterhalb Flag-Low",
            target_calculation="Pole-Höhe vom Breakout addieren",
            risk_reward_ratio="1:2",
            volume_confirmation=True,
            trend_direction="BULL"
        ),
        study_references=[
            "Chartmuster Erweitert 2026 - Daytrading Patterns"
        ]
    ),

    "engulfing_pattern": PatternStrategyMapping(
        pattern_type="engulfing_pattern",
        pattern_name="Engulfing Pattern",
        category=PatternCategory.REVERSAL,
        implementation_phase=2,
        strategy=TradingStrategy(
            strategy_type=StrategyType.REVERSAL_LONG,
            description="Bullish/Bearish Engulfing für schnelle Reversals",
            success_rate=72.0,
            avg_profit="10-20%",
            best_practices=[
                "Körper umschließt vorherigen Körper vollständig",
                "An wichtigen S/R Levels am stärksten",
                "Volumen-Confirmation critical",
                "Schnelle Entry, schnelle Exits",
                "Timeframe: 15m-1h"
            ],
            stop_loss_placement="Unterhalb/Oberhalb Engulfing-Candle",
            target_calculation="Nächster S/R Level oder 1:2 RRR",
            risk_reward_ratio="1:2",
            volume_confirmation=True,
            timeframe_preference="15m-1h"
        ),
        study_references=[
            "Chartmuster Erweitert 2026 - Price Action Patterns"
        ]
    ),

    "symmetrical_triangle": PatternStrategyMapping(
        pattern_type="symmetrical_triangle",
        pattern_name="Symmetrical Triangle",
        category=PatternCategory.CONTINUATION,
        implementation_phase=2,
        strategy=TradingStrategy(
            strategy_type=StrategyType.BREAKOUT_LONG,
            description="Bidirektionales Breakout Pattern",
            success_rate=76.0,  # In trending markets
            avg_profit="20-30%",
            best_practices=[
                "In Trend: 76% Win Rate",
                "In Range: 54% Win Rate (vorsichtig)",
                "Volumen sinkt im Triangle",
                "Breakout-Richtung folgt Trend",
                "Warte auf Breakout + Retest"
            ],
            stop_loss_placement="Gegenüberliegende Triangle-Seite",
            target_calculation="Triangle-Höhe vom Breakout",
            risk_reward_ratio="1:2",
            volume_confirmation=True,
            trend_direction="Folgt Haupttrend"
        ),
        study_references=[
            "Chartmuster Erweitert 2026 - Daytrading Guide"
        ]
    ),

    # ========================================================================
    # RANGE TRADING PATTERNS (Phase 3)
    # ========================================================================

    "grid_trading": PatternStrategyMapping(
        pattern_type="grid_trading",
        pattern_name="Grid Trading (Seitwärtsmarkt)",
        category=PatternCategory.RANGE_TRADING,
        implementation_phase=3,
        strategy=TradingStrategy(
            strategy_type=StrategyType.GRID_TRADING,
            description="Buy Support, Sell Resistance in Sideways Range",
            success_rate=70.0,
            avg_profit="Multiple kleine Gewinne (2-5% pro Trade)",
            best_practices=[
                "Nur in klaren Ranges (ATR < Threshold)",
                "Bollinger Bands für Grenzen",
                "RSI 70/30 für Entry-Timing",
                "Grid-Levels: 5-10 gleichmäßig verteilt",
                "Exit bei Trendbruch (ADX > 25)"
            ],
            stop_loss_placement="Außerhalb Range (5-10%)",
            target_calculation="Gegenüberliegendes Grid-Level",
            risk_reward_ratio="1:1.5",
            volume_confirmation=False,
            rsi_condition="<30 für Long, >70 für Short"
        ),
        study_references=[
            "Chartmuster Erweitert 2026 - Range Trading Module"
        ]
    ),

    "support_resistance_range": PatternStrategyMapping(
        pattern_type="support_resistance_range",
        pattern_name="Support/Resistance Range Bounce",
        category=PatternCategory.RANGE_TRADING,
        implementation_phase=3,
        strategy=TradingStrategy(
            strategy_type=StrategyType.RANGE_BOUNCE_LONG,
            description="Bounce-Trading an S/R Levels in Seitwärtsmärkten",
            success_rate=68.0,
            avg_profit="3-8%",
            best_practices=[
                "Mind. 3-4 Touches pro Level",
                "BB(20,2) für Range-Identifikation",
                "ATR < 2% vom Preis",
                "Volumen sinkt in Range",
                "Exit sofort bei Breakout-Anzeichen"
            ],
            stop_loss_placement="Außerhalb Range Boundary",
            target_calculation="Gegenüberliegende Range-Grenze",
            risk_reward_ratio="1:2",
            volume_confirmation=False,
            timeframe_preference="Sideways Market"
        ),
        study_references=[
            "Chartmuster Erweitert 2026 - Range Trading Guide"
        ]
    ),

    # ========================================================================
    # BREAKOUT/VOLATILITY PATTERNS (Phase 4)
    # ========================================================================

    "volatility_squeeze": PatternStrategyMapping(
        pattern_type="volatility_squeeze",
        pattern_name="Volatility Squeeze → Surge",
        category=PatternCategory.VOLATILITY_SQUEEZE,
        implementation_phase=2,
        strategy=TradingStrategy(
            strategy_type=StrategyType.SQUEEZE_BREAKOUT_LONG,
            description="Breakout nach Bollinger Band Squeeze",
            success_rate=75.0,
            avg_profit="25-40%",
            best_practices=[
                "BB Width < 20% vom SMA(20)",
                "ATR auf Multi-Monat-Tief",
                "Volumen sinkt auf Minimum",
                "Entry: Erster BB-Bruch nach Squeeze",
                "ATR-basierte Stops (2.0-3.0× ATR)"
            ],
            stop_loss_placement="2.0-3.0× ATR unterhalb Entry",
            target_calculation="Bisherige Average-Bewegung nach Squeeze",
            risk_reward_ratio="1:3",
            volume_confirmation=True,
            timeframe_preference="Daily-Weekly für beste Ergebnisse"
        ),
        study_references=[
            "Chartmuster Erweitert 2026 - Volatility Squeeze Module",
            "Bollinger Band Squeeze Strategy Backtest"
        ]
    ),

    "range_breakout_retest": PatternStrategyMapping(
        pattern_type="range_breakout_retest",
        pattern_name="Range Breakout mit Retest",
        category=PatternCategory.BREAKOUT,
        implementation_phase=2,
        strategy=TradingStrategy(
            strategy_type=StrategyType.RETEST_LONG,
            description="Breakout mit Retest-Confirmation (3-Layer Filter)",
            success_rate=85.0,  # Mit allen 3 Filtern
            avg_profit="20-35%",
            best_practices=[
                "Layer 1: Volumen 150%+ über Average",
                "Layer 2: Retest innerhalb 3-5 Bars",
                "Layer 3: Zweites Volumen-Spike bei Retest",
                "False Breakout Reduction: 56%",
                "Win Rate erhöht von 65% auf 85%"
            ],
            stop_loss_placement="Unterhalb Retest-Low",
            target_calculation="Range-Höhe vom Breakout",
            risk_reward_ratio="1:2.5",
            volume_confirmation=True,
            trend_direction="Breakout-Richtung"
        ),
        study_references=[
            "Chartmuster Erweitert 2026 - Breakout Strategies",
            "3-Layer Breakout Filter Backtest"
        ]
    ),

    # ========================================================================
    # PRICE ACTION PATTERNS (Phase 7)
    # ========================================================================

    "pin_bar": PatternStrategyMapping(
        pattern_type="pin_bar",
        pattern_name="Pin Bar (Hammer/Shooting Star)",
        category=PatternCategory.PRICE_ACTION,
        implementation_phase=2,
        strategy=TradingStrategy(
            strategy_type=StrategyType.PRICE_ACTION_LONG,
            description="Reversal-Signal an wichtigen Levels",
            success_rate=75.0,  # An Schlüssel-Levels
            avg_profit="10-20%",
            best_practices=[
                "Langer Docht (2-3× Body)",
                "Kleiner Körper (10-30% der Candle)",
                "An S/R, Fibonacci, EMA(200)",
                "Volumen-Spike bei Docht-Bildung",
                "Bullish Pin Bar: Unterer Docht, Bearish: Oberer"
            ],
            stop_loss_placement="Unterhalb/Oberhalb Docht-Ende",
            target_calculation="Nächster S/R Level oder 1:2 RRR",
            risk_reward_ratio="1:2",
            volume_confirmation=True,
            timeframe_preference="Key Levels"
        ),
        study_references=[
            "Chartmuster Erweitert 2026 - Price Action Module"
        ]
    ),

    "inside_bar": PatternStrategyMapping(
        pattern_type="inside_bar",
        pattern_name="Inside Bar",
        category=PatternCategory.PRICE_ACTION,
        implementation_phase=2,
        strategy=TradingStrategy(
            strategy_type=StrategyType.PRICE_ACTION_LONG,
            description="Konsolidierungs-Pattern vor Continuation",
            success_rate=72.0,  # In trending markets
            avg_profit="8-15%",
            best_practices=[
                "Entire Bar innerhalb vorherigem Range",
                "In Trending Markets am stärksten",
                "Entry: Breakout aus Inside Bar",
                "Multi-Inside-Bars = größere Bewegung",
                "Kombination mit Trend-Direction"
            ],
            stop_loss_placement="Gegenüberliegende Seite der Mother Bar",
            target_calculation="Mother Bar Range vom Breakout",
            risk_reward_ratio="1:2",
            volume_confirmation=False,
            trend_direction="Folgt Haupttrend"
        ),
        study_references=[
            "Chartmuster Erweitert 2026 - Price Action Guide"
        ]
    ),

    "pin_inside_combo": PatternStrategyMapping(
        pattern_type="pin_inside_combo",
        pattern_name="Pin Bar + Inside Bar Combo",
        category=PatternCategory.PRICE_ACTION,
        implementation_phase=2,
        strategy=TradingStrategy(
            strategy_type=StrategyType.PRICE_ACTION_LONG,
            description="Power-Setup: Pin Bar gefolgt von Inside Bar",
            success_rate=85.0,
            avg_profit="15-30%",
            best_practices=[
                "Pin Bar zeigt Rejection",
                "Inside Bar = Konsolidierung",
                "Entry: Breakout aus Inside Bar",
                "Sehr zuverlässiges Setup",
                "An Major Levels am stärksten"
            ],
            stop_loss_placement="Unterhalb Pin Bar Docht",
            target_calculation="Previous Swing High/Low",
            risk_reward_ratio="1:3",
            volume_confirmation=True,
            trend_direction="Reversal oder Continuation"
        ),
        study_references=[
            "Chartmuster Erweitert 2026 - Power Setups"
        ]
    ),

    # ========================================================================
    # HARMONIC PATTERNS EXTENDED (Phase 5)
    # ========================================================================

    "bat_pattern": PatternStrategyMapping(
        pattern_type="bat_pattern",
        pattern_name="Bat Pattern (Harmonic)",
        category=PatternCategory.HARMONIC,
        implementation_phase=2,
        strategy=TradingStrategy(
            strategy_type=StrategyType.HARMONIC_REVERSAL_LONG,
            description="Konservatives Harmonic Reversal Pattern",
            success_rate=73.0,
            avg_profit="30-55%",
            best_practices=[
                "B-Point: 0.382-0.50 Fibonacci Retracement von XA",
                "D-Point (PRZ): 0.886 Retracement von XA",
                "BC Projection: 1.618-2.618 für D",
                "Konservativstes Harmonic Pattern",
                "RSI Divergence an D verstärkt Signal"
            ],
            stop_loss_placement="Unterhalb X-Point (invalidation)",
            target_calculation="38.2% und 61.8% Retracement von AD",
            risk_reward_ratio="1:2.5",
            volume_confirmation=False,
            rsi_condition="Divergence an Point D"
        ),
        study_references=[
            "Chartmuster Erweitert 2026 - Harmonic Patterns",
            "HarmonicTrader.com - Bat Pattern Guide"
        ]
    ),

    "butterfly_pattern": PatternStrategyMapping(
        pattern_type="butterfly_pattern",
        pattern_name="Butterfly Pattern (Harmonic)",
        category=PatternCategory.HARMONIC,
        implementation_phase=2,
        strategy=TradingStrategy(
            strategy_type=StrategyType.HARMONIC_REVERSAL_LONG,
            description="Aggressives Harmonic Reversal Pattern",
            success_rate=73.0,
            avg_profit="35-60%",
            best_practices=[
                "B-Point: 0.786 Retracement von XA",
                "D-Point (PRZ): 1.27 oder 1.618 Extension von XA",
                "Aggressivere Extensions als Bat",
                "Größere Bewegungen möglich",
                "Entry exakt an PRZ-Zone"
            ],
            stop_loss_placement="Unterhalb 1.618 Extension",
            target_calculation="38.2% und 61.8% Retracement von AD",
            risk_reward_ratio="1:3",
            volume_confirmation=False,
            rsi_condition="Extreme Oversold/Overbought"
        ),
        study_references=[
            "Chartmuster Erweitert 2026 - Harmonic Patterns Advanced"
        ]
    ),

    "crab_pattern": PatternStrategyMapping(
        pattern_type="crab_pattern",
        pattern_name="Crab Pattern (Harmonic)",
        category=PatternCategory.HARMONIC,
        implementation_phase=2,
        strategy=TradingStrategy(
            strategy_type=StrategyType.HARMONIC_REVERSAL_LONG,
            description="Precision Harmonic Pattern mit extremen Extensions",
            success_rate=73.0,
            avg_profit="40-70%",
            best_practices=[
                "B-Point: 0.382-0.618 Retracement",
                "D-Point (PRZ): 1.618 Extension von XA",
                "Extremste Extension aller Patterns",
                "Höchstes Profit-Potential",
                "Präzise Entry an 1.618 critical"
            ],
            stop_loss_placement="Unterhalb 1.618 Extension (eng)",
            target_calculation="61.8% Retracement von AD als Primary Target",
            risk_reward_ratio="1:3.5",
            volume_confirmation=False,
            rsi_condition="Extreme Divergence"
        ),
        study_references=[
            "Chartmuster Erweitert 2026 - Harmonic Precision Trading"
        ]
    ),

    # ========================================================================
    # SMART MONEY CONCEPTS (Phase 6)
    # ========================================================================

    "order_block_bullish": PatternStrategyMapping(
        pattern_type="order_block_bullish",
        pattern_name="Bullish Order Block",
        category=PatternCategory.SMART_MONEY,
        implementation_phase=3,
        strategy=TradingStrategy(
            strategy_type=StrategyType.RETEST_LONG,
            description="Smart Money Buy Zone Retest",
            success_rate=70.0,
            avg_profit="Variable (abhängig von Timeframe)",
            best_practices=[
                "Letzter Down-Candle vor Impulse-Move",
                "Institutional Buying Interest Zone",
                "Entry bei Retest des OB",
                "Multi-Timeframe-Bestätigung (HTF Bias)",
                "FVG + OB Combo = höhere Win Rate"
            ],
            stop_loss_placement="Unterhalb Order Block Low",
            target_calculation="Next Liquidity Pool oder Swing High",
            risk_reward_ratio="1:3",
            volume_confirmation=False,
            trend_direction="BULL"
        ),
        study_references=[
            "Chartmuster Erweitert 2026 - Smart Money Concepts"
        ]
    ),

    "order_block_bearish": PatternStrategyMapping(
        pattern_type="order_block_bearish",
        pattern_name="Bearish Order Block",
        category=PatternCategory.SMART_MONEY,
        implementation_phase=3,
        strategy=TradingStrategy(
            strategy_type=StrategyType.RETEST_SHORT,
            description="Smart Money Sell Zone Retest",
            success_rate=70.0,
            avg_profit="Variable",
            best_practices=[
                "Letzter Up-Candle vor Impulse-Move Down",
                "Institutional Selling Interest Zone",
                "Entry bei Retest des OB",
                "Kombination mit BOS für Confirmation",
                "Mitigation Block = präziserer Entry"
            ],
            stop_loss_placement="Oberhalb Order Block High",
            target_calculation="Next Liquidity Pool oder Swing Low",
            risk_reward_ratio="1:3",
            volume_confirmation=False,
            trend_direction="BEAR"
        ),
        study_references=[
            "Chartmuster Erweitert 2026 - SMC Advanced"
        ]
    ),

    "fair_value_gap": PatternStrategyMapping(
        pattern_type="fair_value_gap",
        pattern_name="Fair Value Gap (FVG)",
        category=PatternCategory.SMART_MONEY,
        implementation_phase=3,
        strategy=TradingStrategy(
            strategy_type=StrategyType.RETEST_LONG,
            description="Imbalance-Retest für Smart Money Entry",
            success_rate=68.0,
            avg_profit="Variable",
            best_practices=[
                "3-Candle-Gap (Candle 1 High < Candle 3 Low)",
                "Preis füllt Gap bei Retest",
                "Entry in oberem Drittel des FVG",
                "Kombination mit OB erhöht Win Rate",
                "HTF FVG > LTF FVG (Priorität)"
            ],
            stop_loss_placement="Unterhalb FVG Low",
            target_calculation="Next FVG oder Liquidity Level",
            risk_reward_ratio="1:2.5",
            volume_confirmation=False
        ),
        study_references=[
            "Chartmuster Erweitert 2026 - FVG Trading Guide"
        ]
    ),

    "break_of_structure": PatternStrategyMapping(
        pattern_type="break_of_structure",
        pattern_name="Break of Structure (BOS)",
        category=PatternCategory.SMART_MONEY,
        implementation_phase=3,
        strategy=TradingStrategy(
            strategy_type=StrategyType.BREAKOUT_LONG,
            description="Trendfortsetzungs-Signal (Bullish BOS)",
            success_rate=72.0,
            avg_profit="Variable",
            best_practices=[
                "Preis bricht letztes Swing High (Bullish)",
                "Bestätigt Trend-Continuation",
                "Entry nach BOS + Retest",
                "Kombination mit OB/FVG",
                "HTF BOS = stärkeres Signal"
            ],
            stop_loss_placement="Unterhalb Retest-Low",
            target_calculation="Previous Swing Extension oder Liquidity",
            risk_reward_ratio="1:3",
            volume_confirmation=False,
            trend_direction="BULL"
        ),
        study_references=[
            "Chartmuster Erweitert 2026 - SMC Structure"
        ]
    ),

    "change_of_character": PatternStrategyMapping(
        pattern_type="change_of_character",
        pattern_name="Change of Character (CHoCH)",
        category=PatternCategory.SMART_MONEY,
        implementation_phase=3,
        strategy=TradingStrategy(
            strategy_type=StrategyType.REVERSAL_LONG,
            description="Trendwechsel-Signal (Bullish CHoCH)",
            success_rate=70.0,
            avg_profit="Variable",
            best_practices=[
                "Downtrend bricht letztes Lower Low (Bullish)",
                "Erstes Anzeichen von Reversal",
                "Warte auf Retest + OB",
                "CHoCH alleine schwächer als BOS",
                "Braucht weitere Bestätigung"
            ],
            stop_loss_placement="Unterhalb CHoCH-Low",
            target_calculation="Previous Resistance oder FVG",
            risk_reward_ratio="1:2.5",
            volume_confirmation=False,
            trend_direction="Reversal to BULL"
        ),
        study_references=[
            "Chartmuster Erweitert 2026 - SMC Reversals"
        ]
    ),

    "liquidity_sweep": PatternStrategyMapping(
        pattern_type="liquidity_sweep",
        pattern_name="Liquidity Sweep",
        category=PatternCategory.SMART_MONEY,
        implementation_phase=3,
        strategy=TradingStrategy(
            strategy_type=StrategyType.REVERSAL_LONG,
            description="Stop Hunt vor Reversal (Bullish Sweep)",
            success_rate=75.0,
            avg_profit="Variable (oft große Moves)",
            best_practices=[
                "Preis swept Swing Low/High (nimmt Stops)",
                "Sofortige Reversal zurück",
                "Entry nach Sweep + Bestätigung",
                "Oft an wichtigen Round Numbers",
                "High-Probability Setup mit OB+FVG"
            ],
            stop_loss_placement="Unterhalb Sweep-Low",
            target_calculation="Next Major Swing oder Liquidity Pool",
            risk_reward_ratio="1:4",
            volume_confirmation=False
        ),
        study_references=[
            "Chartmuster Erweitert 2026 - Liquidity Concepts"
        ]
    ),

    "mitigation_block": PatternStrategyMapping(
        pattern_type="mitigation_block",
        pattern_name="Mitigation Block",
        category=PatternCategory.SMART_MONEY,
        implementation_phase=3,
        strategy=TradingStrategy(
            strategy_type=StrategyType.RETEST_LONG,
            description="Präziser OB-Entry mit Mitigation",
            success_rate=73.0,
            avg_profit="Variable",
            best_practices=[
                "Candle die Imbalance (FVG) kreiert hat",
                "Präziser als Standard Order Block",
                "Entry in oberem Drittel des MB",
                "Kombination mit HTF Structure",
                "Premium/Discount Zones beachten"
            ],
            stop_loss_placement="Unterhalb Mitigation Block Low",
            target_calculation="FVG Fill oder Liquidity Target",
            risk_reward_ratio="1:3.5",
            volume_confirmation=False
        ),
        study_references=[
            "Chartmuster Erweitert 2026 - SMC Precision Entries"
        ]
    ),

    "ob_fvg_sweep_combo": PatternStrategyMapping(
        pattern_type="ob_fvg_sweep_combo",
        pattern_name="OB + FVG + Liquidity Sweep Combo",
        category=PatternCategory.SMART_MONEY,
        implementation_phase=3,
        strategy=TradingStrategy(
            strategy_type=StrategyType.RETEST_LONG,
            description="3-Act Confirmation Model (Highest Probability SMC Setup)",
            success_rate=82.0,
            avg_profit="Variable (oft 50%+)",
            best_practices=[
                "Act 1: Liquidity Sweep (Stop Hunt)",
                "Act 2: FVG Fill (Imbalance)",
                "Act 3: OB Retest (Institutional Zone)",
                "HTF Bias bestätigt LTF Entry",
                "Alle 3 Komponenten müssen aligned sein"
            ],
            stop_loss_placement="Unterhalb OB Low (eng)",
            target_calculation="Next Major Liquidity Pool oder 1:5+ RRR",
            risk_reward_ratio="1:5",
            volume_confirmation=False,
            trend_direction="HTF Bias"
        ),
        study_references=[
            "Chartmuster Erweitert 2026 - SMC Master Setup",
            "ICT Concepts - 3-Act Model"
        ]
    )
}
