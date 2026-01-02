#!/usr/bin/env python
"""
OrderPilot-AI Trading Application - Main Entry Point

Usage:
    python main.py                  # Start with default settings
    python main.py --help           # Show all options
    python main.py --check          # Check dependencies only
    python main.py --mock           # Use mock broker for testing
    python main.py --env production # Start in production mode
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Minimize console window on Windows (optional; harmless if no console)
if os.name == "nt":
    try:
        import ctypes

        _SW_MINIMIZE = 6
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, _SW_MINIMIZE)
    except Exception:
        # Non-critical: ignore if API not available
        pass

if __name__ == "__main__":
    # Import and run the full-featured launcher
    import start_orderpilot
    sys.exit(start_orderpilot.main())
