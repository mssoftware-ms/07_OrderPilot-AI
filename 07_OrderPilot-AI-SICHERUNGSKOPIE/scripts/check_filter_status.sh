#!/bin/bash
# Check if Hampel Filter is active

echo "============================================"
echo "HAMPEL FILTER STATUS CHECK"
echo "============================================"

LOG_FILE="logs/orderpilot.log"

if [ ! -f "$LOG_FILE" ]; then
    echo "❌ Log file not found: $LOG_FILE"
    exit 1
fi

echo ""
echo "1. Checking for Hampel Filter initialization..."
echo "-----------------------------------------------"
grep "Hampel Filter" "$LOG_FILE" | tail -5

echo ""
echo "2. Checking for BAD TICK rejections..."
echo "-----------------------------------------------"
grep "BAD TICK REJECTED" "$LOG_FILE" | tail -10

echo ""
echo "3. Checking for filter statistics..."
echo "-----------------------------------------------"
grep "🔍 Hampel Filter:" "$LOG_FILE" | tail -5

echo ""
echo "4. Checking for old v1.0 filter messages (should NOT appear)..."
echo "-----------------------------------------------"
grep "bad tick filtering (5% threshold)" "$LOG_FILE" | tail -3

echo ""
echo "============================================"
echo "ANALYSIS"
echo "============================================"

if grep -q "Hampel Filter with Volume Confirmation initialized" "$LOG_FILE"; then
    echo "✅ Hampel Filter v2.0 is ACTIVE"
else
    echo "❌ Hampel Filter v2.0 NOT FOUND - Old version still running?"
fi

if grep -q "BAD TICK REJECTED" "$LOG_FILE"; then
    REJECTED_COUNT=$(grep -c "BAD TICK REJECTED" "$LOG_FILE")
    echo "✅ Filter is working - $REJECTED_COUNT bad ticks rejected"
else
    echo "⚠️  No bad ticks rejected yet (filter might not be seeing bad data)"
fi

echo ""
echo "============================================"
