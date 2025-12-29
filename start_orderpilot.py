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

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))


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


def check_dependencies() -> bool:
    """Check if all required dependencies are installed"""
    required_modules = [
        ('PyQt6', 'PyQt6'),
        ('sqlalchemy', 'SQLAlchemy'),
        ('pandas', 'pandas'),
        ('numpy', 'numpy'),
        ('openai', 'OpenAI'),
        ('pydantic', 'Pydantic'),
        ('aiohttp', 'aiohttp'),
        ('cryptography', 'cryptography')
    ]

    missing = []
    for module_name, display_name in required_modules:
        try:
            __import__(module_name)
            print(f"✅ {display_name} is installed")
        except ImportError:
            print(f"❌ {display_name} is missing")
            missing.append(display_name)

    if missing:
        print(f"\n❌ Missing dependencies: {', '.join(missing)}")
        print("\nInstall missing dependencies with:")
        print("pip install -r requirements.txt")
        return False

    print("\n✅ All dependencies are installed")
    return True


def check_database() -> None:
    """Check and initialize database if needed"""
    from src.config.loader import DatabaseConfig
    from src.database import initialize_database

    try:
        config = DatabaseConfig(
            engine="sqlite",
            path="./data/orderpilot.db"
        )

        initialize_database(config)
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"⚠️ Database initialization warning: {e}")


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


async def main_with_args(args: argparse.Namespace) -> None:
    """Main function with argument handling"""
    from ui.app import main as app_main

    # Set configuration based on arguments
    os.environ['TRADING_ENV'] = args.env
    os.environ['TRADING_PROFILE'] = args.profile

    if args.mock:
        os.environ['USE_MOCK_BROKER'] = 'true'
        print("🎭 Using Mock Broker for testing")

    # Run the application
    await app_main()


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
    # Set up global exception handler for uncaught exceptions
    def global_exception_handler(exc_type, exc_value, exc_traceback):
        """Handle uncaught exceptions"""
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        logging.error("❌ UNCAUGHT EXCEPTION:", exc_info=(exc_type, exc_value, exc_traceback))
        print(f"\n❌ CRITICAL ERROR: {exc_type.__name__}: {exc_value}")
        print("Check logs for full traceback")

    sys.excepthook = global_exception_handler

    parser = create_parser()
    args = parser.parse_args()

    try:
        # Display banner unless disabled
        if not args.no_banner:
            print_startup_banner()

        # Setup logging
        setup_logging(args.log_level)

        # Check dependencies
        print("\n🔍 Checking dependencies...")
        if not check_dependencies():
            return 1

        # If only checking, exit here
        if args.check:
            print("\n✅ Dependency check complete")
            return 0

        # Check database
        print("\n🗄️ Checking database...")
        check_database()

        # Start application
        print(f"\n🚀 Starting OrderPilot-AI in {args.env} mode with profile '{args.profile}'...")
        print("=" * 70)

        # Run the async main function
        asyncio.run(main_with_args(args))

        return 0

    except KeyboardInterrupt:
        print("\n\n⚠️ Application terminated by user")
        return 0
    except Exception as e:
        logging.error(f"Fatal error: {e}", exc_info=True)
        print(f"\n❌ Fatal error: {e}")
        print("\nCheck the log file for details")
        return 1


if __name__ == "__main__":
    sys.exit(main())