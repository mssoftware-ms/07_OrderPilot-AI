#!/bin/bash
# Performance Benchmark Script for WSL2 Migration Validation

echo "=================================="
echo "Performance Benchmark - OrderPilot-AI"
echo "=================================="
echo ""
echo "Location: $(pwd)"
echo "Filesystem: $(df -h . | tail -1 | awk '{print $1, $5}')"
echo ""

echo "--- Git Operations ---"
echo -n "git status: "
time_output=$( (time git status > /dev/null 2>&1) 2>&1 | grep real )
echo "$time_output"

echo -n "git diff: "
time_output=$( (time git diff --stat > /dev/null 2>&1) 2>&1 | grep real )
echo "$time_output"

echo -n "git log (100 entries): "
time_output=$( (time git log --oneline -100 > /dev/null 2>&1) 2>&1 | grep real )
echo "$time_output"

echo ""
echo "--- File Operations ---"
echo -n "Count Python files: "
time_output=$( (time find src/ -name "*.py" -type f 2>/dev/null | wc -l > /dev/null) 2>&1 | grep real )
echo "$time_output"

echo -n "Find all files: "
time_output=$( (time find . -type f 2>/dev/null | wc -l > /dev/null) 2>&1 | grep real )
echo "$time_output"

echo ""
echo "--- Python Environment ---"
source .wsl_venv/bin/activate 2>/dev/null || source .venv/bin/activate 2>/dev/null

echo -n "Python version: "
python --version

echo -n "Import test (alpaca): "
time_output=$( (time python -c "import alpaca" 2>/dev/null) 2>&1 | grep real )
echo "$time_output"

echo ""
echo "--- Project Stats ---"
echo "Total files: $(find . -type f 2>/dev/null | wc -l)"
echo "Python files: $(find . -name "*.py" -type f 2>/dev/null | wc -l)"
echo "Test files: $(find tests/ -name "test_*.py" -type f 2>/dev/null | wc -l)"
echo "Total size: $(du -sh . 2>/dev/null | cut -f1)"

echo ""
echo "=================================="
echo "Benchmark Complete"
echo "=================================="
