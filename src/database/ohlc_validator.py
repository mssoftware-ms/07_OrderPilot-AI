"""OHLC Data Validator - Validates and fixes OHLC inconsistencies in database.

Ensures that:
- high >= max(open, close)
- low <= min(open, close)

Fixes rounding errors from exchanges (especially Bitunix).
"""

import logging
from datetime import datetime
from typing import Optional

from sqlalchemy import func

from src.database import get_db_manager
from src.database.models import MarketBar

logger = logging.getLogger(__name__)


class OHLCValidator:
    """Validates and fixes OHLC data inconsistencies."""

    def __init__(self):
        """Initialize validator."""
        self.db_manager = get_db_manager()

    def validate_and_fix(
        self,
        symbol: Optional[str] = None,
        dry_run: bool = False,
        progress_callback: Optional[callable] = None
    ) -> dict:
        """Validate and fix OHLC data in database.

        Args:
            symbol: Optional symbol filter (default: all symbols)
            dry_run: If True, only report issues without fixing
            progress_callback: Optional callback(current, total, message) for progress updates

        Returns:
            Dictionary with validation results:
            {
                'total_bars': int,
                'invalid_bars': int,
                'fixed_bars': int,
                'symbols_affected': list[str]
            }
        """
        with self.db_manager.session() as session:
            # Build query for invalid bars
            query = session.query(MarketBar).filter(
                (MarketBar.high < MarketBar.open) |
                (MarketBar.high < MarketBar.close) |
                (MarketBar.low > MarketBar.open) |
                (MarketBar.low > MarketBar.close)
            )

            if symbol:
                query = query.filter(MarketBar.symbol == symbol)

            query = query.order_by(MarketBar.symbol, MarketBar.timestamp)

            # Get all invalid bars
            invalid_bars = query.all()
            total_invalid = len(invalid_bars)

            if total_invalid == 0:
                logger.info("✅ No OHLC inconsistencies found!")
                return {
                    'total_bars': 0,
                    'invalid_bars': 0,
                    'fixed_bars': 0,
                    'symbols_affected': []
                }

            logger.info(f"Found {total_invalid} bars with OHLC inconsistencies")

            symbols_affected = set()
            fixed_count = 0

            for i, bar in enumerate(invalid_bars):
                # Progress callback
                if progress_callback and i % 10 == 0:
                    progress_callback(i, total_invalid, f"Validating bar {i+1}/{total_invalid}")

                symbols_affected.add(bar.symbol)

                # Calculate corrected high/low
                correct_high = max(bar.open, bar.high, bar.close)
                correct_low = min(bar.open, bar.low, bar.close)

                # Determine what's wrong
                issues = []
                if bar.high < bar.open:
                    issues.append(f"high < open ({bar.high:.2f} < {bar.open:.2f})")
                if bar.high < bar.close:
                    issues.append(f"high < close ({bar.high:.2f} < {bar.close:.2f})")
                if bar.low > bar.open:
                    issues.append(f"low > open ({bar.low:.2f} > {bar.open:.2f})")
                if bar.low > bar.close:
                    issues.append(f"low > close ({bar.low:.2f} > {bar.close:.2f})")

                if i < 5:  # Log first 5 for debugging
                    logger.debug(
                        f"{bar.timestamp} | {bar.symbol} | {', '.join(issues)}\n"
                        f"  Before: O={bar.open:.2f} H={bar.high:.2f} L={bar.low:.2f} C={bar.close:.2f}\n"
                        f"  After:  O={bar.open:.2f} H={correct_high:.2f} L={correct_low:.2f} C={bar.close:.2f}"
                    )

                if not dry_run:
                    # Apply fix
                    bar.high = correct_high
                    bar.low = correct_low
                    fixed_count += 1

            if not dry_run:
                session.commit()
                logger.info(f"✅ Fixed {fixed_count} bars!")
            else:
                logger.info(f"⚠️ DRY RUN - Would fix {total_invalid} bars")

            results = {
                'total_bars': total_invalid,
                'invalid_bars': total_invalid,
                'fixed_bars': fixed_count if not dry_run else 0,
                'symbols_affected': sorted(list(symbols_affected))
            }

            # Final progress callback
            if progress_callback:
                status = "Fixed" if not dry_run else "Found"
                progress_callback(
                    total_invalid,
                    total_invalid,
                    f"{status} {total_invalid} inconsistent bars"
                )

            return results

    def get_validation_summary(self, symbol: Optional[str] = None) -> dict:
        """Get summary of OHLC data quality without fixing.

        Args:
            symbol: Optional symbol filter

        Returns:
            Dictionary with summary statistics
        """
        with self.db_manager.session() as session:
            # Total bars
            query = session.query(func.count(MarketBar.id))
            if symbol:
                query = query.filter(MarketBar.symbol == symbol)
            total_bars = query.scalar()

            # Invalid bars
            query = session.query(func.count(MarketBar.id)).filter(
                (MarketBar.high < MarketBar.open) |
                (MarketBar.high < MarketBar.close) |
                (MarketBar.low > MarketBar.open) |
                (MarketBar.low > MarketBar.close)
            )
            if symbol:
                query = query.filter(MarketBar.symbol == symbol)
            invalid_bars = query.scalar()

            return {
                'total_bars': total_bars,
                'invalid_bars': invalid_bars,
                'valid_bars': total_bars - invalid_bars,
                'quality_percentage': ((total_bars - invalid_bars) / total_bars * 100) if total_bars > 0 else 100.0
            }


def validate_and_fix_ohlc(
    symbol: Optional[str] = None,
    dry_run: bool = False,
    progress_callback: Optional[callable] = None
) -> dict:
    """Convenience function for OHLC validation.

    Args:
        symbol: Optional symbol filter
        dry_run: If True, only report without fixing
        progress_callback: Optional progress callback

    Returns:
        Validation results dictionary
    """
    validator = OHLCValidator()
    return validator.validate_and_fix(symbol, dry_run, progress_callback)
