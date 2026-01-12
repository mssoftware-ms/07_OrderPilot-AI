"""Debug logger for Entry Analyzer.

Creates a dedicated log file for debugging analysis issues.
"""

import logging
from pathlib import Path


def setup_entry_analyzer_logger() -> logging.Logger:
    """Setup dedicated logger for Entry Analyzer debugging.

    Creates orderpilot-EntryAnalyzer.log in the current directory.

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger("EntryAnalyzer")
    logger.setLevel(logging.DEBUG)

    # Avoid duplicate handlers
    if logger.handlers:
        return logger

    # File handler
    log_file = Path.cwd() / "orderpilot-EntryAnalyzer.log"
    file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)

    # Formatter
    formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logger.info("=" * 80)
    logger.info("Entry Analyzer Debug Logger Initialized")
    logger.info("Log file: %s", log_file.absolute())
    logger.info("=" * 80)

    return logger


# Create global debug logger
debug_logger = setup_entry_analyzer_logger()
