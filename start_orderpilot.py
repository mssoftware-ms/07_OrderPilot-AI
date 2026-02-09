#!/usr/bin/env python
"""
Enhanced Launch Script for OrderPilot-AI Trading Application
With error handling, logging, and startup checks
"""

import argparse
import asyncio
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Now we can import from src
from ui.app_console_utils import _hide_console_window


def load_windows_env_vars_in_wsl() -> None:
    """Load Windows environment variables in WSL environment.

    When running in WSL, Windows user environment variables are not automatically
    available. This function loads them using PowerShell.
    """
    # Check if running in WSL
    try:
        with open('/proc/version', 'r') as f:
            if 'microsoft' not in f.read().lower():
                return  # Not in WSL, skip
    except FileNotFoundError:
        return  # Not Linux, skip

    # Load Windows env vars via PowerShell
    import subprocess

    env_vars = [
        'ALPACA_API_KEY',
        'ALPACA_API_SECRET',
        'BITUNIX_API_KEY',
        'BITUNIX_SECRET_KEY',
        'OPENAI_API_KEY',
        'ANTHROPIC_API_KEY',
        'GEMINI_API_KEY',
        'DEEPSEEK_API_KEY',
        'GITHUB_TOKEN',
        'PERPLEXITY_API_KEY',
        'FINNHUB_API_KEY',
        'ALPHA_VANTAGE_API_KEY',
    ]

    for var_name in env_vars:
        if var_name in os.environ:
            continue  # Already set, skip

        try:
            # Try User scope first
            result = subprocess.run(
                ['powershell.exe', '-Command',
                 f'[System.Environment]::GetEnvironmentVariable("{var_name}", "User")'],
                capture_output=True,
                text=True,
                timeout=2
            )
            value = result.stdout.strip()

            # If not found in User scope, try Machine scope
            if not value:
                result = subprocess.run(
                    ['powershell.exe', '-Command',
                     f'[System.Environment]::GetEnvironmentVariable("{var_name}", "Machine")'],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                value = result.stdout.strip()

            if value:
                os.environ[var_name] = value
        except Exception:
            pass  # Silently skip on error


# Load Windows environment variables if in WSL
load_windows_env_vars_in_wsl()


def check_ai_api_keys(splash=None) -> None:
    """Check and display status of AI API keys from environment."""
    if splash: splash.set_progress(15, "Prüfe API-Schlüssel...")
    print("\n" + "=" * 50)
    print("[KEY] API Keys Status (from Windows Environment)")
    print("=" * 50)

    keys = [
        ("ALPACA_API_KEY", "Alpaca API Key"),
        ("ALPACA_API_SECRET", "Alpaca Secret"),
        ("BITUNIX_API_KEY", "Bitunix API Key"),
        ("BITUNIX_SECRET_KEY", "Bitunix Secret"),
        ("OPENAI_API_KEY", "OpenAI"),
        ("ANTHROPIC_API_KEY", "Anthropic"),
        ("GEMINI_API_KEY", "Gemini"),
        ("DEEPSEEK_API_KEY", "DeepSeek"),
        ("GITHUB_TOKEN", "GitHub Token"),
        ("PERPLEXITY_API_KEY", "Perplexity"),
        ("FINNHUB_API_KEY", "Finnhub"),
        ("ALPHA_VANTAGE_API_KEY", "Alpha Vantage"),
    ]

    found_any = False
    for env_var, name in keys:
        value = os.environ.get(env_var)
        if value:
            # Show first 10 chars for verification
            masked = value[:10] + "..." if len(value) > 10 else value
            print(f"  [OK] {name}: {masked}")
            found_any = True
        else:
            print(f"  [ERROR] {name}: NOT FOUND")

    if not found_any:
        print("\n[WARNING] WARNUNG: Keine AI API Keys gefunden!")
        print("   Die Keys müssen als Windows-Systemumgebungsvariablen gesetzt sein.")
        print("   Nach dem Setzen: Terminal/CMD neu starten!")

    print("=" * 50 + "\n")


def setup_logging(log_level: str = "INFO") -> None:
    """Setup application logging"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    log_file = log_dir / f"orderpilot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

    logging.info(f"OrderPilot-AI Starting - Log file: {log_file}")


def check_dependencies(splash=None) -> bool:
    """Check if all required dependencies are installed"""
    if splash: splash.set_progress(20, "Prüfe Abhängigkeiten...")
    required_modules = [
        ('PyQt6', 'PyQt6'),
        ('sqlalchemy', 'SQLAlchemy'),
        ('pandas', 'pandas'),
        ('numpy', 'numpy'),
        ('openai', 'OpenAI'),
        ('pydantic', 'Pydantic'),
        ('aiohttp', 'aiohttp'),
        ('cryptography', 'cryptography'),
        ('sklearn', 'scikit-learn'),
        ('optuna', 'Optuna')
    ]

    missing = []
    for module_name, display_name in required_modules:
        try:
            __import__(module_name)
            print(f"[OK] {display_name} is installed")
        except ImportError:
            print(f"[ERROR] {display_name} is missing")
            missing.append(display_name)

    if missing:
        print(f"\n[ERROR] Missing dependencies: {', '.join(missing)}")
        print("\nInstall missing dependencies with:")
        print("pip install -r requirements.txt")
        return False

    print("\n[OK] All dependencies are installed")
    return True


def check_database(splash=None) -> None:
    """Check and initialize database if needed"""
    if splash: splash.set_progress(25, "Datenbank-System...")
    from src.config.loader import DatabaseConfig
    from src.database import initialize_database

    try:
        config = DatabaseConfig(
            engine="sqlite",
            path="./data/orderpilot.db"
        )

        initialize_database(config)
        print("[OK] Database initialized successfully")
    except Exception as e:
        print(f"[WARNING] Database initialization warning: {e}")


def print_startup_banner() -> None:
    """Display startup banner"""
    banner = """
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║     ██████╗ ██████╗ ██████╗ ███████╗██████╗ ██████╗ ██╗██╗      ███████╗████████╗    ║
║    ██╔═══██╗██╔══██╗██╔══██╗██╔════╝██╔══██╗██╔══██╗██║██║     ██╔═══██╗╚══██╔══╝   ║
║    ██║   ██║██████╔╝██║  ██║█████╗  ██████╔╝██████╔╝██║██║     ██║   ██║   ██║      ║
║    ██║   ██║██╔══██╗██║  ██║██╔══╝  ██╔══██╗██╔═══╝ ██║██║     ██║   ██║   ██║      ║
║    ╚██████╔╝██║  ██║██████╔╝███████╗██║  ██║██║     ██║███████╗╚██████╔╝   ██║      ║
║     ╚═════╝ ╚═╝  ╚═╝╚═════╝ ╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝╚══════╝ ╚═════╝    ╚═╝      ║
║                                                                      ║
║                 AI-Powered Trading Application v1.0                  ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
    """
    print(banner)


async def main_with_args(args: argparse.Namespace, app=None, splash=None) -> None:
    """Main function with argument handling"""
    from ui.app import main as app_main

    # Set configuration based on arguments
    os.environ['TRADING_ENV'] = args.env
    os.environ['TRADING_PROFILE'] = args.profile

    if args.mock:
        os.environ['USE_MOCK_BROKER'] = 'true'
        print("[MOCK] Using Mock Broker for testing")

    # Run the application
    await app_main(app=app, splash=splash)


def create_parser() -> argparse.ArgumentParser:
    """Create command line argument parser"""
    parser = argparse.ArgumentParser(
        description='OrderPilot-AI Trading Application',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                     # Start with default settings
  %(prog)s --env production    # Start in production mode
  %(prog)s --profile aggressive # Use aggressive trading profile
  %(prog)s --mock             # Use mock broker for testing
  %(prog)s --check            # Only run dependency checks
        """
    )

    parser.add_argument(
        '--env',
        choices=['development', 'paper', 'production'],
        default='paper',
        help='Trading environment (default: paper)'
    )

    parser.add_argument(
        '--profile',
        default='paper',
        help='Configuration profile to load (default: paper)'
    )

    parser.add_argument(
        '--mock',
        action='store_true',
        help='Use mock broker for testing'
    )

    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Logging level (default: INFO)'
    )

    parser.add_argument(
        '--check',
        action='store_true',
        help='Only check dependencies, do not start application'
    )

    parser.add_argument(
        '--no-banner',
        action='store_true',
        help='Skip startup banner'
    )

    return parser


def main() -> int:
    """Main entry point"""
    splash = None  # Initialize to avoid UnboundLocalError in finally block
    # 0. HIDE CONSOLE IMMEDIATELY on Windows
    _hide_console_window()

    # FIX: "Invalid texture upload" error
    # Force software rendering for QtWebEngine (Chromium) to avoid GPU driver issues
    os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--disable-gpu"
    os.environ["QT_OPENGL"] = "software"

    # Set up global exception handler for uncaught exceptions
    def global_exception_handler(exc_type, exc_value, exc_traceback):
        """Handle uncaught exceptions"""
        # Make sure console is visible on crash
        from ui.app_console_utils import _show_console_window
        _show_console_window()

        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        logging.error("[ERROR] UNCAUGHT EXCEPTION:", exc_info=(exc_type, exc_value, exc_traceback))
        print(f"\n[ERROR] CRITICAL ERROR: {exc_type.__name__}: {exc_value}")
        print("Check logs for full traceback")

    sys.excepthook = global_exception_handler

    parser = create_parser()
    args = parser.parse_args()

    # 1. OPTIONAL EARLY SPLASH SCREEN
    app = None
    splash = None
    try:
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import Qt
        from ui.splash_screen import SplashScreen
        from ui.app_resources import _get_startup_icon_path

        # This will blink the console but hide it again
        _hide_console_window()

        # Set OpenGL attribute before app creation
        if not QApplication.instance():
            QApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)

        app = QApplication.instance()
        if not app:
            app = QApplication(sys.argv)

        app.setApplicationName("OrderPilot-AI")

        startup_icon_path = _get_startup_icon_path()
        splash = SplashScreen(startup_icon_path)
        splash.show()
        splash.set_progress(5, "Lade OrderPilot-AI Launcher...")
    except ImportError:
        # PyQt6 not available yet, will be checked properly in check_dependencies()
        pass
    except Exception as e:
        print(f"Warning: Could not start splash screen: {e}")

    try:
        # Display banner unless disabled
        if not args.no_banner:
            # print_startup_banner() # Disabled to prevent UnicodeEncodeError on Windows
            pass


        # Setup logging
        if splash: splash.set_progress(10, "Konfiguriere Logging...")
        setup_logging(args.log_level)

        # Check AI API keys
        check_ai_api_keys(splash=splash)

        # Check dependencies
        print("\n[CHECK] Checking dependencies...")
        if not check_dependencies(splash=splash):
            if splash: splash.close()
            from ui.app_console_utils import _show_console_window
            _show_console_window()
            return 1

        # If only checking, exit here
        if args.check:
            if splash: splash.close()
            print("\n[OK] Dependency check complete")
            return 0

        # Check database
        print("\n[DB] Checking database...")
        check_database(splash=splash)

        # Start application
        print(f"\n[START] Starting OrderPilot-AI in {args.env} mode with profile '{args.profile}'...")
        print("=" * 70)

        # Run the async main function
        asyncio.run(main_with_args(args, app=app, splash=splash))

        return 0

    except KeyboardInterrupt:
        if splash: splash.close()
        print("\n\n[WARNING] Application terminated by user")
        return 0
    except Exception as e:
        if splash: splash.close()
        from ui.app_console_utils import _show_console_window
        _show_console_window()
        logging.error(f"Fatal error: {e}", exc_info=True)
        print(f"\n[ERROR] Fatal error: {e}")
        print("\nCheck the log file for details")
        return 1


if __name__ == "__main__":
    sys.exit(main())
