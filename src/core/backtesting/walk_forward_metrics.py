"""Walk-Forward Runner - Metrics Aggregation.

Refactored from walk_forward_runner.py monolith.

Module 5/6 of walk_forward_runner.py split.

Contains:
- Aggregated metrics calculation
- Stability metrics calculation
"""

from __future__ import annotations

import statistics


class WalkForwardMetrics:
    """Helper für WalkForwardRunner metrics aggregation."""

    def __init__(self, parent):
        """
        Args:
            parent: WalkForwardRunner Instanz
        """
        self.parent = parent

    def calculate_aggregated_metrics(self) -> dict[str, float]:
        """Berechnet aggregierte OOS-Metriken über alle Folds."""
        successful_folds = [f for f in self.parent._folds if f.is_successful]

        if not successful_folds:
            return {}

        # Sammle Metriken
        metrics_lists: dict[str, list[float]] = {
            "expectancy": [],
            "profit_factor": [],
            "win_rate": [],
            "max_drawdown_pct": [],
            "total_return_pct": [],
            "sharpe_ratio": [],
            "total_trades": [],
        }

        for fold in successful_folds:
            m = fold.test_metrics
            if m.expectancy is not None:
                metrics_lists["expectancy"].append(m.expectancy)
            if m.profit_factor is not None and m.profit_factor < float('inf'):
                metrics_lists["profit_factor"].append(m.profit_factor)
            metrics_lists["win_rate"].append(m.win_rate)
            metrics_lists["max_drawdown_pct"].append(m.max_drawdown_pct)
            metrics_lists["total_return_pct"].append(m.total_return_pct)
            if m.sharpe_ratio is not None:
                metrics_lists["sharpe_ratio"].append(m.sharpe_ratio)
            metrics_lists["total_trades"].append(float(m.total_trades))

        # Aggregieren (Mittelwert)
        aggregated = {}
        for metric, values in metrics_lists.items():
            if values:
                aggregated[f"avg_{metric}"] = statistics.mean(values)
                aggregated[f"min_{metric}"] = min(values)
                aggregated[f"max_{metric}"] = max(values)

        # Gesamte OOS-Performance
        total_trades = sum(int(f.test_metrics.total_trades) for f in successful_folds)
        total_winners = sum(f.test_metrics.winning_trades for f in successful_folds)
        aggregated["combined_win_rate"] = total_winners / total_trades if total_trades > 0 else 0

        return aggregated

    def calculate_stability_metrics(self) -> dict[str, float]:
        """Berechnet Stabilitätsmetriken über alle Folds.

        Niedrigere Werte = stabilere Performance.
        """
        successful_folds = [f for f in self.parent._folds if f.is_successful]

        if len(successful_folds) < 2:
            return {}

        stability = {}

        # Coefficient of Variation für wichtige Metriken
        metrics_to_check = ["expectancy", "profit_factor", "total_return_pct"]

        for metric in metrics_to_check:
            values = []
            for fold in successful_folds:
                m = fold.test_metrics
                val = getattr(m, metric, None)
                if val is not None and val != float('inf') and val != float('-inf'):
                    values.append(val)

            if len(values) >= 2:
                mean = statistics.mean(values)
                std = statistics.stdev(values)

                # Coefficient of Variation (CV)
                cv = (std / abs(mean)) if mean != 0 else float('inf')
                stability[f"{metric}_cv"] = cv
                stability[f"{metric}_std"] = std

        # Worst Fold Performance
        worst_fold_return = min(f.test_metrics.total_return_pct for f in successful_folds)
        stability["worst_fold_return_pct"] = worst_fold_return

        # Profitable Folds Ratio
        profitable_folds = sum(1 for f in successful_folds if f.test_metrics.total_return_pct > 0)
        stability["profitable_folds_ratio"] = profitable_folds / len(successful_folds)

        return stability
