"""Demo: CEL Regime Functions

Demonstrates the usage of the new regime functions:
- last_closed_regime()
- trigger_regime_analysis()
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.tradingbot.cel_engine import CELEngine


def demo_last_closed_regime():
    """Demonstrate last_closed_regime() function."""
    print("=" * 80)
    print("DEMO: last_closed_regime() Function")
    print("=" * 80)

    cel = CELEngine()

    # Example 1: Using last_closed_candle object
    print("\n1. Using last_closed_candle object:")
    context = {
        "last_closed_candle": {
            "regime": "EXTREME_BULL",
            "close": 100.0,
            "high": 102.0,
            "low": 99.0
        },
        "regime": "BULL"  # Current regime
    }

    result = cel.evaluate("last_closed_regime()", context)
    print(f"   Context: {context['last_closed_candle']['regime']}")
    print(f"   Result: last_closed_regime() = '{result}'")

    # Example 2: Check for specific regime
    expr = "last_closed_regime() == 'EXTREME_BULL'"
    result = cel.evaluate(expr, context)
    print(f"   Expression: {expr}")
    print(f"   Result: {result}")

    # Example 3: Detect regime change
    print("\n2. Detect regime change (NEUTRAL → BULL):")
    context = {
        "last_closed_candle": {"regime": "NEUTRAL"},
        "regime": "BULL"
    }
    expr = "last_closed_regime() == 'NEUTRAL' && regime == 'BULL'"
    result = cel.evaluate(expr, context)
    print(f"   Previous: {context['last_closed_candle']['regime']}")
    print(f"   Current: {context['regime']}")
    print(f"   Expression: {expr}")
    print(f"   Result: {result} (Regime changed!)")

    # Example 4: Multi-regime filter
    print("\n3. Multi-regime filter (BULL or EXTREME_BULL):")
    for test_regime in ["EXTREME_BULL", "BULL", "NEUTRAL", "BEAR"]:
        context = {"last_closed_candle": {"regime": test_regime}}
        expr = "(last_closed_regime() == 'BULL' || last_closed_regime() == 'EXTREME_BULL')"
        result = cel.evaluate(expr, context)
        print(f"   Regime: {test_regime:15} → Filter passed: {result}")

    # Example 5: Using chart_data array
    print("\n4. Using chart_data array:")
    context = {
        "chart_data": [
            {"regime": "BEAR", "close": 95.0},
            {"regime": "NEUTRAL", "close": 98.0},  # Last closed candle
            {"regime": "BULL", "close": 100.0}     # Current candle
        ]
    }
    result = cel.evaluate("last_closed_regime()", context)
    print(f"   Chart data: {len(context['chart_data'])} candles")
    print(f"   Result: last_closed_regime() = '{result}' (from index -2)")

    # Example 6: Fallback to prev_regime
    print("\n5. Fallback to prev_regime field:")
    context = {
        "prev_regime": "EXTREME_BEAR",
        "regime": "BEAR"
    }
    result = cel.evaluate("last_closed_regime()", context)
    print(f"   Context: prev_regime = '{context['prev_regime']}'")
    print(f"   Result: last_closed_regime() = '{result}'")

    # Example 7: No data available
    print("\n6. No data available (returns UNKNOWN):")
    context = {"regime": "BULL"}  # Only current regime
    result = cel.evaluate("last_closed_regime()", context)
    print(f"   Context: Only current regime available")
    print(f"   Result: last_closed_regime() = '{result}'")


def demo_trigger_regime_analysis():
    """Demonstrate trigger_regime_analysis() function."""
    print("\n" + "=" * 80)
    print("DEMO: trigger_regime_analysis() Function")
    print("=" * 80)

    cel = CELEngine()

    # Example 1: No chart_window (returns False)
    print("\n1. No chart_window in context:")
    context = {}
    result = cel.evaluate("trigger_regime_analysis()", context)
    print(f"   Context: No chart_window")
    print(f"   Result: trigger_regime_analysis() = {result}")

    # Example 2: Mock chart_window
    print("\n2. With mock chart_window:")

    class MockChartWindow:
        """Mock chart window for demonstration."""
        def __init__(self):
            self.regime_updated = False

        def trigger_regime_update(self, debounce_ms=0):
            """Mock regime update trigger."""
            print(f"   [MockChart] trigger_regime_update(debounce_ms={debounce_ms}) called!")
            self.regime_updated = True

    mock_chart = MockChartWindow()
    context = {"chart_window": mock_chart}
    result = cel.evaluate("trigger_regime_analysis()", context)
    print(f"   Result: trigger_regime_analysis() = {result}")
    print(f"   Chart updated: {mock_chart.regime_updated}")

    # Example 3: Combined expression
    print("\n3. Combined with last_closed_regime():")
    context = {
        "chart_window": mock_chart,
        "last_closed_candle": {"regime": "EXTREME_BULL"}
    }
    expr = "trigger_regime_analysis() && last_closed_regime() == 'EXTREME_BULL'"
    result = cel.evaluate(expr, context)
    print(f"   Expression: {expr}")
    print(f"   Result: {result}")


def demo_trading_rules():
    """Demonstrate practical trading rule examples."""
    print("\n" + "=" * 80)
    print("DEMO: Practical Trading Rules")
    print("=" * 80)

    cel = CELEngine()

    # Example 1: Entry rule with regime filter
    print("\n1. Entry Rule: Only EXTREME_BULL regime")
    context = {
        "last_closed_candle": {"regime": "EXTREME_BULL"},
        "rsi14": {"value": 65.0},
        "ema20": {"value": 95.0},
        "close": 100.0
    }
    rule = "last_closed_regime() == 'EXTREME_BULL' && rsi14.value > 60 && close > ema20.value"
    result = cel.evaluate(rule, context)
    print(f"   Rule: {rule}")
    print(f"   Context: Regime={context['last_closed_candle']['regime']}, RSI={context['rsi14']['value']}, Price={context['close']}")
    print(f"   Result: Entry allowed = {result}")

    # Example 2: Avoid weak regimes
    print("\n2. Exit Rule: Exit if regime weakens to NEUTRAL")
    for test_regime in ["EXTREME_BULL", "BULL", "NEUTRAL", "BEAR"]:
        context = {
            "last_closed_candle": {"regime": test_regime},
            "trade": {"is_open": True, "side": "long"}
        }
        rule = "is_trade_open(trade) && last_closed_regime() == 'NEUTRAL'"
        result = cel.evaluate(rule, context)
        print(f"   Regime: {test_regime:15} → Should exit: {result}")

    # Example 3: Regime change confirmation
    print("\n3. Entry on Regime Change (NEUTRAL → BULL):")
    context = {
        "last_closed_candle": {"regime": "NEUTRAL"},
        "regime": "BULL",
        "rsi14": {"value": 55.0}
    }
    rule = "last_closed_regime() == 'NEUTRAL' && regime == 'BULL' && rsi14.value > 50"
    result = cel.evaluate(rule, context)
    print(f"   Rule: {rule}")
    print(f"   Context: Previous={context['last_closed_candle']['regime']}, Current={context['regime']}")
    print(f"   Result: Entry allowed = {result}")


if __name__ == "__main__":
    print("\n" + "🚀" * 40)
    print("CEL Regime Functions - Complete Demo")
    print("🚀" * 40)

    # Run all demos
    demo_last_closed_regime()
    demo_trigger_regime_analysis()
    demo_trading_rules()

    print("\n" + "=" * 80)
    print("✅ Demo Complete!")
    print("=" * 80)
    print("\nNew CEL Functions:")
    print("  • last_closed_regime()        - Get regime of last closed candle")
    print("  • trigger_regime_analysis()   - Trigger regime analysis on chart")
    print("\nDocumentation: 04_Knowledgbase/CEL_Functions_Reference_v3.md")
    print("Tests: tests/test_cel_last_closed_regime.py")
    print("=" * 80 + "\n")
