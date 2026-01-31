"""compounding_ui_plots.py
Chart rendering and visualization for CompoundingPanel.

This mixin handles all matplotlib chart rendering:
- 6 different plot modes (stacked, daily, cumulative, comparison, monthly, yearly)
- Modern financial chart design
- Gradient fills and multi-series plots
"""

from __future__ import annotations

import numpy as np

# Import MODERN_COLORS from setup module
from .compounding_ui_setup import MODERN_COLORS


class CompoundingUIPlotsMixin:
    """Mixin for chart rendering and visualization."""

    def _update_plot(self, days) -> None:
        """Update plot with modern financial chart design."""
        ax = self.canvas.ax
        ax.clear()
        self.canvas.apply_qt_palette(self)

        xs = np.array([d.day for d in days])
        mode = self.cb_plot_mode.currentIndex()

        if mode == 0:
            # Stacked area chart with all metrics
            self._plot_stacked_metrics(ax, days, xs)
        elif mode == 1:
            # Daily net profit with gradient fill
            self._plot_daily_net(ax, days, xs)
        elif mode == 2:
            # Cumulative net profit
            self._plot_cumulative(ax, days, xs)
        elif mode == 3:
            # Profit vs Costs comparison
            self._plot_profit_vs_costs(ax, days, xs)
        elif mode == 4:
            # Monthly stacked view
            self._plot_monthly(ax, days, xs)
        else:
            # Yearly stacked view
            self._plot_yearly(ax, days, xs)

        # Common styling
        if mode < 4:  # Daily views
            ax.set_xlabel("Tag", fontsize=10, fontweight='medium')
            ax.set_xlim(xs[0], xs[-1])

        ax.grid(True, alpha=0.15, linestyle='-', linewidth=0.5)

        # Modern legend
        legend = ax.legend(
            loc='upper left',
            frameon=True,
            fancybox=True,
            shadow=False,
            framealpha=0.8,
            edgecolor='#3A3A3C',
            fontsize=9,
        )
        if legend:
            legend.get_frame().set_facecolor('#2C2C2E')

        self.canvas.fig.tight_layout(pad=1.5)
        self.canvas.draw()

    def _plot_stacked_metrics(self, ax, days, xs) -> None:
        """Create modern stacked area chart with all key metrics."""
        # Extract data series
        gross = np.array([float(d.gross_profit) for d in days])
        fees = np.array([float(d.fee_amount) for d in days])
        taxes = np.array([float(d.tax_amount) for d in days])
        net = np.array([float(d.net_profit) for d in days])
        start_cap = np.array([float(d.start_capital) for d in days])

        # Normalize for visualization (show relative contributions)
        # Plot lines with area fills

        # Net profit area (base)
        ax.fill_between(xs, 0, net, alpha=0.6, color=MODERN_COLORS['net'], label='Netto-Gewinn')
        ax.plot(xs, net, color=MODERN_COLORS['net'], linewidth=2, alpha=0.9)

        # Gross profit line
        ax.plot(xs, gross, color=MODERN_COLORS['gross'], linewidth=2.5,
                label='Brutto-Gewinn', linestyle='-', marker='o', markersize=3)

        # Fees area (negative visual)
        ax.fill_between(xs, 0, -fees, alpha=0.5, color=MODERN_COLORS['fees'], label='Gebühren')

        # Taxes area (negative visual, stacked on fees)
        ax.fill_between(xs, -fees, -fees - taxes, alpha=0.5, color=MODERN_COLORS['taxes'], label='Steuern')

        # Investment reference line (scaled down for visibility)
        invest_scaled = start_cap / start_cap.max() * gross.max() * 0.3 if gross.max() > 0 else start_cap * 0.01
        ax.plot(xs, invest_scaled, color=MODERN_COLORS['invest'], linewidth=1.5,
                linestyle='--', alpha=0.7, label='Invest (skaliert)')

        ax.set_ylabel("Betrag (€)", fontsize=10, fontweight='medium')
        ax.set_title("Tägliche Übersicht: Gewinn, Gebühren & Steuern",
                     fontsize=12, fontweight='bold', pad=15)
        ax.axhline(y=0, color='#8E8E93', linewidth=0.8, linestyle='-', alpha=0.5)

    def _plot_daily_net(self, ax, days, xs) -> None:
        """Daily net profit with modern gradient fill."""
        ys = np.array([float(d.net_profit) for d in days])

        # Gradient fill under the line
        ax.fill_between(xs, 0, ys, alpha=0.4,
                        color=MODERN_COLORS['net'], label='Netto-Gewinn')
        ax.plot(xs, ys, color=MODERN_COLORS['net'], linewidth=2.5,
                marker='o', markersize=4, markerfacecolor='white', markeredgewidth=1.5)

        ax.set_ylabel("Netto-Gewinn (€)", fontsize=10, fontweight='medium')
        ax.set_title("Täglicher Netto-Gewinn", fontsize=12, fontweight='bold', pad=15)
        ax.axhline(y=0, color='#8E8E93', linewidth=0.8, linestyle='-', alpha=0.5)

    def _plot_cumulative(self, ax, days, xs) -> None:
        """Cumulative net profit with gradient."""
        cum = np.cumsum([float(d.net_profit) for d in days])

        # Gradient fill
        ax.fill_between(xs, 0, cum, alpha=0.4, color=MODERN_COLORS['net'], label='Kumulierter Netto-Gewinn')
        ax.plot(xs, cum, color=MODERN_COLORS['net'], linewidth=2.5)

        # Add cumulative gross for reference
        cum_gross = np.cumsum([float(d.gross_profit) for d in days])
        ax.plot(xs, cum_gross, color=MODERN_COLORS['gross'], linewidth=2,
                linestyle='--', alpha=0.7, label='Kumulierter Brutto')

        ax.set_ylabel("Kumulierter Betrag (€)", fontsize=10, fontweight='medium')
        ax.set_title("Kumulierte Entwicklung", fontsize=12, fontweight='bold', pad=15)
        ax.axhline(y=0, color='#8E8E93', linewidth=0.8, linestyle='-', alpha=0.5)

    def _plot_profit_vs_costs(self, ax, days, xs) -> None:
        """Compare profit vs costs (fees + taxes)."""
        gross = np.array([float(d.gross_profit) for d in days])
        fees = np.array([float(d.fee_amount) for d in days])
        taxes = np.array([float(d.tax_amount) for d in days])
        total_costs = fees + taxes

        # Bar chart comparison
        width = 0.35
        x_offset = xs - width/2

        ax.bar(x_offset, gross, width, label='Brutto-Gewinn',
               color=MODERN_COLORS['gross'], alpha=0.8, edgecolor='white', linewidth=0.5)
        ax.bar(x_offset + width, total_costs, width, label='Kosten (Gebühren + Steuern)',
               color=MODERN_COLORS['fees'], alpha=0.8, edgecolor='white', linewidth=0.5)

        ax.set_ylabel("Betrag (€)", fontsize=10, fontweight='medium')
        ax.set_title("Gewinn vs. Kosten", fontsize=12, fontweight='bold', pad=15)

    def _plot_monthly(self, ax, days, xs) -> None:
        """Create monthly aggregated stacked bar chart."""
        # Aggregate daily data into monthly buckets (assume ~30 days per month)
        days_per_month = 30
        num_months = max(1, (len(days) + days_per_month - 1) // days_per_month)

        months = []
        gross_monthly = []
        fees_monthly = []
        taxes_monthly = []
        net_monthly = []

        for m in range(num_months):
            start_idx = m * days_per_month
            end_idx = min((m + 1) * days_per_month, len(days))
            month_days = days[start_idx:end_idx]

            months.append(m + 1)
            gross_monthly.append(sum(float(d.gross_profit) for d in month_days))
            fees_monthly.append(sum(float(d.fee_amount) for d in month_days))
            taxes_monthly.append(sum(float(d.tax_amount) for d in month_days))
            net_monthly.append(sum(float(d.net_profit) for d in month_days))

        x = np.arange(len(months))
        width = 0.6

        # Stacked bars: Net (bottom), then Fees, then Taxes on top
        ax.bar(x, net_monthly, width, label='Netto-Gewinn', color=MODERN_COLORS['net'], alpha=0.9)
        ax.bar(x, fees_monthly, width, bottom=net_monthly, label='Gebühren', color=MODERN_COLORS['fees'], alpha=0.8)
        bottom_taxes = [n + f for n, f in zip(net_monthly, fees_monthly)]
        ax.bar(x, taxes_monthly, width, bottom=bottom_taxes, label='Steuern', color=MODERN_COLORS['taxes'], alpha=0.8)

        # Gross line on top
        ax.plot(x, gross_monthly, color=MODERN_COLORS['gross'], linewidth=2.5,
                marker='o', markersize=6, label='Brutto-Gewinn')

        ax.set_xticks(x)
        ax.set_xticklabels([f'Monat {m}' for m in months])
        ax.set_ylabel("Betrag (€)", fontsize=10, fontweight='medium')
        ax.set_title("Monatliche Übersicht (gestapelt)", fontsize=12, fontweight='bold', pad=15)
        ax.axhline(y=0, color='#8E8E93', linewidth=0.8, linestyle='-', alpha=0.5)

    def _plot_yearly(self, ax, days, xs) -> None:
        """Create yearly aggregated stacked bar chart."""
        # Aggregate daily data into yearly buckets (assume ~365 days per year)
        days_per_year = 365
        num_years = max(1, (len(days) + days_per_year - 1) // days_per_year)

        years = []
        gross_yearly = []
        fees_yearly = []
        taxes_yearly = []
        net_yearly = []

        for y in range(num_years):
            start_idx = y * days_per_year
            end_idx = min((y + 1) * days_per_year, len(days))
            year_days = days[start_idx:end_idx]

            years.append(y + 1)
            gross_yearly.append(sum(float(d.gross_profit) for d in year_days))
            fees_yearly.append(sum(float(d.fee_amount) for d in year_days))
            taxes_yearly.append(sum(float(d.tax_amount) for d in year_days))
            net_yearly.append(sum(float(d.net_profit) for d in year_days))

        x = np.arange(len(years))
        width = 0.6

        # Stacked bars
        ax.bar(x, net_yearly, width, label='Netto-Gewinn', color=MODERN_COLORS['net'], alpha=0.9)
        ax.bar(x, fees_yearly, width, bottom=net_yearly, label='Gebühren', color=MODERN_COLORS['fees'], alpha=0.8)
        bottom_taxes = [n + f for n, f in zip(net_yearly, fees_yearly)]
        ax.bar(x, taxes_yearly, width, bottom=bottom_taxes, label='Steuern', color=MODERN_COLORS['taxes'], alpha=0.8)

        # Gross line on top
        ax.plot(x, gross_yearly, color=MODERN_COLORS['gross'], linewidth=2.5,
                marker='o', markersize=8, label='Brutto-Gewinn')

        ax.set_xticks(x)
        ax.set_xticklabels([f'Jahr {y}' for y in years])
        ax.set_ylabel("Betrag (€)", fontsize=10, fontweight='medium')
        ax.set_title("Jährliche Übersicht (gestapelt)", fontsize=12, fontweight='bold', pad=15)
        ax.axhline(y=0, color='#8E8E93', linewidth=0.8, linestyle='-', alpha=0.5)
