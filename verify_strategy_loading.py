
import sys
import os
import logging

# Configure logging to see output
logging.basicConfig(level=logging.DEBUG)

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

try:
    from core.tradingbot.strategy_catalog import StrategyCatalog
    
    print("Initializing StrategyCatalog...")
    catalog = StrategyCatalog()
    
    strategies = catalog.get_all_strategies()
    print(f"Successfully loaded {len(strategies)} strategies.")
    
    for s in strategies:
        print(f" - {s.profile.name} ({s.strategy_type.value})")
        
    # Test getting a specific strategy
    s = catalog.get_strategy("trend_following_conservative")
    if s:
        print(f"\nRetrieved 'trend_following_conservative': {s.profile.description}")
        print(f"Entry Rules: {len(s.entry_rules)}")
    else:
        print("FAILED to retrieve 'trend_following_conservative'")
        sys.exit(1)

except Exception as e:
    print(f"FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

