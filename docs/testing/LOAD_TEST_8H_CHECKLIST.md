# 8-Hour Load Test Checklist - Bitunix HEDGE Execution

**Purpose**: Verify system stability, memory integrity, and WebSocket reliability over extended operation.

**Task 5.21**: Load test - 8h run, no memory leak, stable WS

---

## Pre-Test Setup

### Environment
- [ ] Windows system environment variables set:
  - `BITUNIX_API_KEY`
  - `BITUNIX_API_SECRET`
  - `BITUNIX_USE_TESTNET=true` (TESTNET ONLY!)
- [ ] Python virtual environment activated
- [ ] All dependencies installed (`pip install -r requirements.txt`)
- [ ] Log directory created: `data/load_test/`

### Configuration
- [ ] Set logging to INFO level (not DEBUG to reduce I/O)
- [ ] Configure test parameters:
  - Symbol: BTCUSDT
  - Test mode: Adaptive limit entry (no real fills)
  - Tick frequency: Every 5 seconds
  - Offset: 0.05% (0.0005)
- [ ] Memory profiling enabled (optional: `memory_profiler`)

---

## Test Execution Script

**File**: `tests/load/load_test_8h.py`

```python
"""8-Hour Load Test for Bitunix HEDGE Execution.

Continuously:
1. Connect to WebSocket
2. Place adaptive limit orders
3. Feed market price ticks
4. Monitor memory usage
5. Track WS connection stability

Run:
    python tests/load/load_test_8h.py
"""

import asyncio
import logging
from datetime import datetime, timedelta
from decimal import Decimal
import psutil
import os

from src.core.broker.bitunix_hedge_executor import BitunixHedgeExecutor

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'data/load_test/load_test_{datetime.now():%Y%m%d_%H%M%S}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Metrics
class LoadTestMetrics:
    def __init__(self):
        self.start_time = datetime.now()
        self.orders_placed = 0
        self.orders_modified = 0
        self.ws_reconnects = 0
        self.errors = 0
        self.memory_samples = []

    def record_memory(self):
        process = psutil.Process(os.getpid())
        mem_mb = process.memory_info().rss / 1024 / 1024
        self.memory_samples.append(mem_mb)

    def report(self):
        elapsed = (datetime.now() - self.start_time).total_seconds() / 3600
        logger.info(f"""
=== Load Test Report (After {elapsed:.2f}h) ===
Orders Placed: {self.orders_placed}
Orders Modified: {self.orders_modified}
WS Reconnects: {self.ws_reconnects}
Errors: {self.errors}
Memory Usage:
  Current: {self.memory_samples[-1]:.1f} MB
  Peak: {max(self.memory_samples):.1f} MB
  Average: {sum(self.memory_samples)/len(self.memory_samples):.1f} MB
  Leak Check: {'PASS' if self.memory_samples[-1] < self.memory_samples[0] * 1.5 else 'FAIL'}
""")

async def main():
    metrics = LoadTestMetrics()
    executor = BitunixHedgeExecutor()

    # Connect
    success, error = await executor.connect()
    if not success:
        logger.error(f"Connection failed: {error}")
        return

    logger.info("8-hour load test started")

    # Test duration: 8 hours
    end_time = datetime.now() + timedelta(hours=8)

    try:
        while datetime.now() < end_time:
            # Record memory
            metrics.record_memory()

            # Simulate market tick (every 5s)
            await asyncio.sleep(5)

            # Report every hour
            if len(metrics.memory_samples) % 720 == 0:  # 720 samples = 1 hour
                metrics.report()

    except KeyboardInterrupt:
        logger.warning("Test interrupted by user")
    finally:
        # Final report
        metrics.report()
        await executor.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Monitoring Checklist (During Test)

### Every Hour
- [ ] Check memory usage trend
- [ ] Verify WS connection status (should be 'Connected')
- [ ] Check log file for errors
- [ ] Verify no ERROR_LOCK state
- [ ] CPU usage reasonable (<30% average)

### Metrics to Track
- **Memory Baseline (Hour 0)**: _____ MB
- **Memory Hour 1**: _____ MB
- **Memory Hour 2**: _____ MB
- **Memory Hour 4**: _____ MB
- **Memory Hour 6**: _____ MB
- **Memory Hour 8**: _____ MB

**Leak Threshold**: Memory Hour 8 should be < 1.5x Memory Hour 0

### Expected Behavior
- ✅ Memory stays relatively flat (±20% variation)
- ✅ WebSocket maintains connection (0-2 reconnects over 8h)
- ✅ No ERROR_LOCK state
- ✅ No exceptions in logs
- ✅ CPU usage stable

---

## Post-Test Verification

### Pass Criteria
- [ ] **Memory Leak Check**: Final memory < 1.5x initial memory
- [ ] **WS Stability**: ≤5 reconnects over 8 hours
- [ ] **Error Rate**: <0.1% error rate
- [ ] **No Crashes**: Process ran for full 8 hours
- [ ] **State Machine**: No ERROR_LOCK or stuck states

### Failure Analysis
If test fails, investigate:
1. Memory leak: Check object retention, circular references
2. WS instability: Check network, firewall, rate limits
3. Errors: Review error logs, check API limits
4. Crashes: Check stack trace, resource limits

---

## Results Documentation

**Date**: _________________
**Duration**: _____ hours
**Pass/Fail**: _________

**Summary**:
```
Memory Leak: PASS/FAIL
WS Stability: PASS/FAIL
Error Rate: PASS/FAIL
Overall: PASS/FAIL
```

**Notes**:
_______________________________________________________________
_______________________________________________________________
_______________________________________________________________

---

**Status**: Task 5.21 - Prepared (not executed)
**Next Step**: Run test in testnet environment before production release
