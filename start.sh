#!/bin/bash
# ========================================
#  OrderPilot-AI Trading Application
#  Linux/Mac Startup Script
# ========================================

echo ""
echo "==================================================="
echo "   OrderPilot-AI Trading Application Launcher"
echo "==================================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | grep -Po '(?<=Python )\d+\.\d+')
REQUIRED_VERSION="3.10"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo -e "${RED}❌ Python $REQUIRED_VERSION or higher is required. Found: $PYTHON_VERSION${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Python $PYTHON_VERSION detected${NC}"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Check if requirements are installed
if ! python -c "import PyQt6" 2>/dev/null; then
    echo -e "${YELLOW}Installing requirements...${NC}"
    pip install -r requirements.txt
    echo ""
fi

# Create necessary directories
mkdir -p data logs config

# Start the application with arguments
echo -e "${GREEN}Starting OrderPilot-AI...${NC}"
echo "=========================================="
echo ""

# Check if we have a display (for GUI)
if [ -z "$DISPLAY" ] && [ -z "$WAYLAND_DISPLAY" ]; then
    echo -e "${YELLOW}Warning: No display detected. Running in headless mode.${NC}"
    python3 start_orderpilot.py --check
else
    python3 start_orderpilot.py "$@"
fi

# Exit code
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✅ Application exited successfully${NC}"
else
    echo -e "${RED}❌ Application exited with error code: $EXIT_CODE${NC}"
fi

# Deactivate virtual environment
deactivate

exit $EXIT_CODE