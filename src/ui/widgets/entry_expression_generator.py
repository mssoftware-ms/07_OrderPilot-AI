"""Entry Expression Generator - Generiert CEL Entry Expressions.

Erstellt CEL Expressions basierend auf Regime-Auswahl und Templates.
Verwendet für Regime Entry Expression Editor.

Author: Claude Code
Date: 2026-01-29
"""

from __future__ import annotations

import logging
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class StrategyTemplate(Enum):
    """Vorgefertigte Strategy Templates."""

    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"
    MEAN_REVERSION = "mean_reversion"
    CUSTOM = "custom"


class EntryExpressionGenerator:
    """Generiert CEL Entry Expressions aus Regime-Auswahl."""

    @staticmethod
    def generate(
        long_regimes: list[str],
        short_regimes: list[str],
        add_trigger: bool = True,
        add_side_check: bool = True,
        add_indicators: Optional[dict[str, str]] = None,
        pretty: bool = True
    ) -> str:
        """Generiert entry_expression für Regime JSON.

        Args:
            long_regimes: Liste von Regime-IDs für Long Entry (z.B. ["STRONG_BULL", "STRONG_TF"])
            short_regimes: Liste von Regime-IDs für Short Entry (z.B. ["STRONG_BEAR"])
            add_trigger: Fügt trigger_regime_analysis() hinzu (empfohlen)
            add_side_check: Fügt side == 'long'/'short' checks hinzu (empfohlen)
            add_indicators: Optional zusätzliche Indicator-Bedingungen (z.B. {"rsi": "> 50", "adx": "> 25"})
            pretty: Formatiert Expression mit Zeilenumbrüchen und Einrückung

        Returns:
            CEL Entry Expression String

        Example:
            >>> gen = EntryExpressionGenerator()
            >>> expr = gen.generate(
            ...     long_regimes=["STRONG_BULL", "STRONG_TF"],
            ...     short_regimes=["STRONG_BEAR"]
            ... )
            >>> print(expr)
            trigger_regime_analysis() &&
            ((side == 'long' && (
              last_closed_regime() == 'STRONG_BULL' ||
              last_closed_regime() == 'STRONG_TF'
            )) ||
            (side == 'short' && last_closed_regime() == 'STRONG_BEAR'))
        """
        parts = []

        # Teil 1: Trigger (optional)
        if add_trigger:
            parts.append("trigger_regime_analysis()")

        # Teil 2: Entry Conditions
        entry_conditions = []

        # Long Conditions
        if long_regimes and add_side_check:
            long_regime_checks = [
                f"last_closed_regime() == '{regime}'"
                for regime in long_regimes
            ]

            if len(long_regime_checks) == 1:
                long_condition = f"side == 'long' && {long_regime_checks[0]}"
            else:
                regime_part = " || ".join(long_regime_checks)
                long_condition = f"side == 'long' && ({regime_part})"

            # Füge Indicator-Bedingungen hinzu
            if add_indicators:
                indicator_checks = [
                    f"{name} {condition}"
                    for name, condition in add_indicators.items()
                ]
                indicator_part = " && ".join(indicator_checks)
                long_condition = f"{long_condition} && ({indicator_part})"

            entry_conditions.append(long_condition)

        elif long_regimes and not add_side_check:
            # Ohne side check (nicht empfohlen)
            long_regime_checks = [
                f"last_closed_regime() == '{regime}'"
                for regime in long_regimes
            ]
            entry_conditions.append(" || ".join(long_regime_checks))

        # Short Conditions
        if short_regimes and add_side_check:
            short_regime_checks = [
                f"last_closed_regime() == '{regime}'"
                for regime in short_regimes
            ]

            if len(short_regime_checks) == 1:
                short_condition = f"side == 'short' && {short_regime_checks[0]}"
            else:
                regime_part = " || ".join(short_regime_checks)
                short_condition = f"side == 'short' && ({regime_part})"

            # Füge Indicator-Bedingungen hinzu (für Short umgekehrt)
            if add_indicators:
                indicator_checks = [
                    f"{name} {condition}"
                    for name, condition in add_indicators.items()
                ]
                indicator_part = " && ".join(indicator_checks)
                short_condition = f"{short_condition} && ({indicator_part})"

            entry_conditions.append(short_condition)

        elif short_regimes and not add_side_check:
            # Ohne side check (nicht empfohlen)
            short_regime_checks = [
                f"last_closed_regime() == '{regime}'"
                for regime in short_regimes
            ]
            entry_conditions.append(" || ".join(short_regime_checks))

        # Kombiniere Entry Conditions
        if len(entry_conditions) == 1:
            entry_part = entry_conditions[0]
        elif len(entry_conditions) > 1:
            # Wrap in ()
            wrapped = [f"({cond})" for cond in entry_conditions]
            entry_part = " || ".join(wrapped)
        else:
            # Keine Conditions - Fallback
            entry_part = "false"
            logger.warning("No long or short regimes provided - using 'false'")

        # Kombiniere alle Teile
        if parts:
            # Mit Trigger
            full_expression = f"{' && '.join(parts)} && ({entry_part})"
        else:
            # Ohne Trigger
            full_expression = entry_part

        # Pretty-Print (optional)
        if pretty and len(full_expression) > 80:
            full_expression = EntryExpressionGenerator._prettify(
                full_expression,
                long_regimes,
                short_regimes,
                add_trigger
            )

        return full_expression

    @staticmethod
    def _prettify(
        expression: str,
        long_regimes: list[str],
        short_regimes: list[str],
        has_trigger: bool
    ) -> str:
        """Formatiert Expression mit Zeilenumbrüchen und Einrückung."""
        lines = []

        if has_trigger:
            lines.append("trigger_regime_analysis() && (")
        else:
            lines.append("(")

        # Long Conditions
        if long_regimes:
            lines.append("  (side == 'long' && (")
            for i, regime in enumerate(long_regimes):
                connector = " ||" if i < len(long_regimes) - 1 else ""
                lines.append(f"    last_closed_regime() == '{regime}'{connector}")
            lines.append("  ))")

        # Short Conditions
        if short_regimes:
            if long_regimes:
                lines.append("  ||")
            lines.append("  (side == 'short' && (")
            for i, regime in enumerate(short_regimes):
                connector = " ||" if i < len(short_regimes) - 1 else ""
                lines.append(f"    last_closed_regime() == '{regime}'{connector}")
            lines.append("  ))")

        lines.append(")")

        return "\n".join(lines)

    @staticmethod
    def generate_from_template(
        template: StrategyTemplate,
        available_regimes: list[str]
    ) -> tuple[list[str], list[str]]:
        """Generiert Regime-Auswahl basierend auf Template.

        Args:
            template: Strategy Template
            available_regimes: Verfügbare Regime-IDs aus JSON

        Returns:
            (long_regimes, short_regimes) - Listen von Regime-IDs

        Example:
            >>> gen = EntryExpressionGenerator()
            >>> regimes = ["STRONG_TF", "STRONG_BULL", "STRONG_BEAR", "BULL", "BEAR", "SIDEWAYS"]
            >>> long, short = gen.generate_from_template(StrategyTemplate.CONSERVATIVE, regimes)
            >>> print(long)
            ['STRONG_TF']
            >>> print(short)
            []
        """
        long_regimes = []
        short_regimes = []

        if template == StrategyTemplate.CONSERVATIVE:
            # Nur extremste Trends
            for regime in available_regimes:
                if regime == "STRONG_TF":
                    long_regimes.append(regime)

        elif template == StrategyTemplate.MODERATE:
            # Strong Bull/Bear + Strong TF
            for regime in available_regimes:
                if "STRONG" in regime.upper():
                    if "BULL" in regime.upper() or regime == "STRONG_TF":
                        long_regimes.append(regime)
                    elif "BEAR" in regime.upper():
                        short_regimes.append(regime)

        elif template == StrategyTemplate.AGGRESSIVE:
            # Alle außer SIDEWAYS und Gegen-Trend
            for regime in available_regimes:
                if "SIDEWAYS" in regime.upper():
                    continue
                if "BULL" in regime.upper() and "BEAR" not in regime.upper():
                    long_regimes.append(regime)
                elif "BEAR" in regime.upper():
                    short_regimes.append(regime)
                elif "TF" in regime.upper():
                    # Trend Following - zu Long
                    long_regimes.append(regime)

        elif template == StrategyTemplate.MEAN_REVERSION:
            # Exhaustion-Regimes (umgekehrt!)
            for regime in available_regimes:
                if "BEAR_EXHAUSTION" in regime.upper():
                    # Bear Exhaustion → Long Entry
                    long_regimes.append(regime)
                elif "BULL_EXHAUSTION" in regime.upper():
                    # Bull Exhaustion → Short Entry
                    short_regimes.append(regime)

        else:  # CUSTOM
            # Keine automatische Auswahl
            pass

        return long_regimes, short_regimes

    @staticmethod
    def get_template_description(template: StrategyTemplate) -> str:
        """Gibt Beschreibung des Templates zurück."""
        descriptions = {
            StrategyTemplate.CONSERVATIVE: (
                "Conservative: Nur extremste Trends (STRONG_TF)\n"
                "Höchste Gewinnwahrscheinlichkeit, weniger Trades"
            ),
            StrategyTemplate.MODERATE: (
                "Moderate: Strong Bull/Bear + Strong TF\n"
                "Balance zwischen Trades und Qualität"
            ),
            StrategyTemplate.AGGRESSIVE: (
                "Aggressive: Alle Trend-Regimes außer Range\n"
                "Viele Trades, höheres Risiko"
            ),
            StrategyTemplate.MEAN_REVERSION: (
                "Mean Reversion: Entry bei Trend-Erschöpfung\n"
                "Fängt Trendwenden, höheres Risiko"
            ),
            StrategyTemplate.CUSTOM: (
                "Custom: Manuelle Regime-Auswahl\n"
                "Volle Kontrolle über Entry-Bedingungen"
            )
        }
        return descriptions.get(template, "Unbekanntes Template")


# Convenience Functions

def quick_generate(long_regimes: list[str], short_regimes: list[str]) -> str:
    """Quick-Generate mit Standard-Einstellungen."""
    return EntryExpressionGenerator.generate(
        long_regimes=long_regimes,
        short_regimes=short_regimes,
        add_trigger=True,
        add_side_check=True,
        pretty=True
    )


def generate_conservative(available_regimes: list[str]) -> str:
    """Generiert Conservative Strategy."""
    gen = EntryExpressionGenerator()
    long, short = gen.generate_from_template(
        StrategyTemplate.CONSERVATIVE,
        available_regimes
    )
    return gen.generate(long, short)


def generate_moderate(available_regimes: list[str]) -> str:
    """Generiert Moderate Strategy."""
    gen = EntryExpressionGenerator()
    long, short = gen.generate_from_template(
        StrategyTemplate.MODERATE,
        available_regimes
    )
    return gen.generate(long, short)


def generate_aggressive(available_regimes: list[str]) -> str:
    """Generiert Aggressive Strategy."""
    gen = EntryExpressionGenerator()
    long, short = gen.generate_from_template(
        StrategyTemplate.AGGRESSIVE,
        available_regimes
    )
    return gen.generate(long, short)
