#!/usr/bin/env python
"""Launch script for OrderPilot-AI Trading Application."""

import os
import sys

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

if __name__ == "__main__":
    # Import directly and execute the app's main function
    # Note: The app.py file handles its own PyQt6 application creation and event loop
    import asyncio

    from ui.app import main

    # The main() function in app.py handles its own event loop with qasync
    # We need to run it directly, but since it's an async function, we use asyncio.run
    asyncio.run(main())