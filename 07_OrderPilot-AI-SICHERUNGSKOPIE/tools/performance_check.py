
import time
import sys
import os
import asyncio
import psutil
from datetime import datetime, timedelta

# Add src to path
sys.path.append(os.getcwd())

def measure_time(func):
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        return result, end - start
    return wrapper

@measure_time
def test_imports():
    """Measure import times of heavy modules"""
    try:
        import src.core.execution.engine
    except ImportError as e:
        print(f"Failed to import execution.engine: {e}")
    try:
        import src.core.market_data.history_provider
    except ImportError as e:
        print(f"Failed to import market_data.history_provider: {e}")
    try:
        import src.database.database
    except ImportError as e:
        print(f"Failed to import database: {e}")
    try:
        import src.ai.openai_service
    except ImportError as e:
        print(f"Failed to import openai_service: {e}")
    return "Imports done"

async def test_event_bus_throughput():
    """Measure EventBus throughput"""
    from src.common.event_bus import EventBus, Event, EventType
    from datetime import datetime
    
    bus = EventBus()
    count = 0
    target = 10000
    
    def handler(event):
        nonlocal count
        count += 1
        
    bus.subscribe(EventType.MARKET_TICK, handler)
    
    start = time.perf_counter()
    
    # Emit 10k events
    for i in range(target):
        event = Event(
            type=EventType.MARKET_TICK,
            timestamp=datetime.utcnow(),
            data={"price": i, "symbol": "BTC/USD"}
        )
        bus.emit(event)
        
    duration = time.perf_counter() - start
    return target / duration  # Events per second

def test_strategy_compilation():
    """Measure Strategy Compilation Time"""
    from src.core.strategy.compiler import StrategyCompiler
    from src.core.strategy.definition import StrategyDefinition, IndicatorConfig, Condition, LogicGroup, LogicOperator
    
    # Create a complex strategy def
    strategy_def = StrategyDefinition(
        name="Benchmark Strategy",
        version="1.0.0",
        author="PerfTest",
        description="Complex strategy for benchmarking",
        asset_class="crypto",
        recommended_symbols=["BTC/USD"],
        indicators=[
            IndicatorConfig(alias="fast_ma", type="SMA", params={"period": 10}),
            IndicatorConfig(alias="slow_ma", type="SMA", params={"period": 50}),
            IndicatorConfig(alias="rsi", type="RSI", params={"period": 14}),
            IndicatorConfig(alias="macd", type="MACD", params={})
        ],
        entry_long=LogicGroup(
            operator=LogicOperator.AND,
            conditions=[
                Condition(left="fast_ma", operator=">", right="slow_ma"),
                Condition(left="rsi", operator="<", right=30)
            ]
        ),
        exit_long=Condition(left="rsi", operator=">", right=70)
    )
    
    compiler = StrategyCompiler()
    
    start = time.perf_counter()
    # Compile 100 times
    for _ in range(100):
        _ = compiler.compile(strategy_def)
    duration = time.perf_counter() - start
    
    return 100 / duration  # Compilations per second

def test_database_performance():
    """Measure Database Insert Speed (In-Memory for raw speed)"""
    from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
    from sqlalchemy.orm import declarative_base, sessionmaker
    
    Base = declarative_base()
    
    class PerfTestModel(Base):
        __tablename__ = 'perf_test'
        id = Column(Integer, primary_key=True)
        data = Column(String)
        value = Column(Float)
        created_at = Column(DateTime, default=datetime.utcnow)
        
    engine = create_engine('sqlite:///:memory:') # In-memory for pure logic speed
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    start = time.perf_counter()
    
    objects = [
        PerfTestModel(data=f"row_{i}", value=float(i))
        for i in range(1000)
    ]
    session.add_all(objects)
    session.commit()
    
    duration = time.perf_counter() - start
    return 1000 / duration # Inserts per second

async def main():
    print("# PERFORMANCE CHECK REPORT\n")
    
    # 1. Imports
    print("## 1. Startup & Imports")
    _, duration = test_imports()
    print(f"- Core Modules Import Time: {duration:.4f}s")
    
    # 2. Event Bus
    print("\n## 2. Core Throughput")
    try:
        throughput = await test_event_bus_throughput()
        print(f"- Event Bus Throughput: {throughput:.0f} events/sec")
    except Exception as e:
        print(f"- Event Bus Test Failed: {e}")

    # 3. Strategy Compilation
    print("\n## 3. Logic Performance")
    try:
        compilation_speed = test_strategy_compilation()
        print(f"- Strategy Compilation: {compilation_speed:.0f} compiles/sec")
    except Exception as e:
        print(f"- Strategy Test Failed: {e}")
        
    # 4. Database
    print("\n## 4. Data Persistence")
    try:
        db_speed = test_database_performance()
        print(f"- SQLite Insert Speed (Memory): {db_speed:.0f} rows/sec")
    except Exception as e:
        print(f"- DB Test Failed: {e}")
        
    # 5. Memory Usage
    process = psutil.Process(os.getpid())
    print("\n## 5. Resource Usage")
    print(f"- Memory Usage: {process.memory_info().rss / 1024 / 1024:.2f} MB")

if __name__ == "__main__":
    asyncio.run(main())
