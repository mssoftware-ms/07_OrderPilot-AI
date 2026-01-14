
import sys
import os
import json
from pathlib import Path

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

try:
    from core.tradingbot.strategy_catalog import StrategyCatalog
    from core.tradingbot.strategy_definitions import StrategyDefinition
except ImportError as e:
    print(f"Error importing modules: {e}")
    sys.exit(1)

def migrate():
    catalog = StrategyCatalog()
    strategies = catalog.get_all_strategies()
    
    output_dir = Path("config/strategies")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Found {len(strategies)} strategies to migrate.")
    
    for strategy in strategies:
        name = strategy.profile.name
        filename = f"{name}.json"
        filepath = output_dir / filename
        
        # Convert to dict using Pydantic's method
        # Handling Enums by converting them to strings via mode='json' if available,
        # or just dumping and relying on default serializer
        try:
            # Pydantic V2
            data = strategy.model_dump(mode='json')
        except AttributeError:
            # Pydantic V1 fallback
            data = json.loads(strategy.json())
            
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
        print(f"Exported: {filepath}")

if __name__ == "__main__":
    migrate()
