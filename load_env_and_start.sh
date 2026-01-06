#!/bin/bash
# Load Windows environment variables and start OrderPilot-AI

echo "🔑 Loading environment variables from Windows..."

export BITUNIX_API_KEY=$(powershell.exe -Command '[System.Environment]::GetEnvironmentVariable("BITUNIX_API_KEY", "User")' | tr -d '\r')
export BITUNIX_SECRET_KEY=$(powershell.exe -Command '[System.Environment]::GetEnvironmentVariable("BITUNIX_SECRET_KEY", "User")' | tr -d '\r')
export OPENAI_API_KEY=$(powershell.exe -Command '[System.Environment]::GetEnvironmentVariable("OPENAI_API_KEY", "User")' | tr -d '\r')
export ANTHROPIC_API_KEY=$(powershell.exe -Command '[System.Environment]::GetEnvironmentVariable("ANTHROPIC_API_KEY", "User")' | tr -d '\r')
export GEMINI_API_KEY=$(powershell.exe -Command '[System.Environment]::GetEnvironmentVariable("GEMINI_API_KEY", "User")' | tr -d '\r')

# Verify keys are loaded
if [ -n "$BITUNIX_API_KEY" ]; then
    echo "✅ BITUNIX_API_KEY loaded"
else
    echo "❌ BITUNIX_API_KEY not found"
fi

if [ -n "$BITUNIX_SECRET_KEY" ]; then
    echo "✅ BITUNIX_SECRET_KEY loaded"
else
    echo "❌ BITUNIX_SECRET_KEY not found"
fi

echo ""
echo "🚀 Starting OrderPilot-AI..."
python start_orderpilot.py
