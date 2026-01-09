"""Walk-Forward Runner - Fold Period Calculation.

Refactored from walk_forward_runner.py monolith.

Module 1/6 of walk_forward_runner.py split.

Contains:
- Fold period calculation (train/test windows)
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class WalkForwardFoldCalculator:
    """Helper für WalkForwardRunner fold period calculation."""

    def __init__(self, parent):
        """
        Args:
            parent: WalkForwardRunner Instanz
        """
        self.parent = parent

    def calculate_folds(self) -> list[tuple[datetime, datetime, datetime, datetime]]:
        """Berechnet die Fold-Zeiträume.

        Returns:
            Liste von (train_start, train_end, test_start, test_end) Tuples
        """
        base_config = self.parent.config.base_config
        total_start = base_config.start_date
        total_end = base_config.end_date

        train_days = self.parent.config.train_window_days
        test_days = self.parent.config.test_window_days
        step_days = self.parent.config.step_size_days

        folds = []
        current_start = total_start

        while True:
            train_start = current_start
            train_end = train_start + timedelta(days=train_days)
            test_start = train_end
            test_end = test_start + timedelta(days=test_days)

            # Prüfe ob Test-End noch innerhalb des Gesamtzeitraums liegt
            if test_end > total_end:
                # Letzter Fold - passe an
                if test_start < total_end:
                    test_end = total_end
                    folds.append((train_start, train_end, test_start, test_end))
                break

            folds.append((train_start, train_end, test_start, test_end))

            # Nächster Fold
            current_start = current_start + timedelta(days=step_days)

            # Stoppe wenn nicht genug Platz für Training
            if current_start + timedelta(days=train_days) > total_end:
                break

        # Mindest-Folds prüfen
        if len(folds) < self.parent.config.min_folds:
            logger.warning(
                f"Only {len(folds)} folds possible (min: {self.parent.config.min_folds}). "
                f"Consider shorter windows or longer data period."
            )

        return folds
