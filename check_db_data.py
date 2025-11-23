"""Check database for existing market data."""
from src.database import get_db_manager, initialize_database
from src.database.models import MarketBar
from src.config.loader import config_manager
from datetime import datetime

# Initialize database first
config = config_manager.load_profile()
initialize_database(config)
db = get_db_manager()

with db.session() as session:
    # Count total bars
    count = session.query(MarketBar).count()
    print(f'Total bars in database: {count}')

    if count > 0:
        # Get distinct symbols
        symbols = session.query(MarketBar.symbol).distinct().all()
        print(f'\nSymbols with data: {[s[0] for s in symbols]}')

        # Get date range for each symbol
        for symbol_tuple in symbols:
            symbol = symbol_tuple[0]
            bars = session.query(MarketBar).filter(MarketBar.symbol == symbol).order_by(MarketBar.timestamp).all()
            if bars:
                first_bar = bars[0]
                last_bar = bars[-1]
                print(f'\n{symbol}:')
                print(f'  Count: {len(bars)} bars')
                print(f'  Range: {first_bar.timestamp} to {last_bar.timestamp}')
                print(f'  Last close: ${last_bar.close}')
    else:
        print('\nDatabase is empty - no market data stored yet')
