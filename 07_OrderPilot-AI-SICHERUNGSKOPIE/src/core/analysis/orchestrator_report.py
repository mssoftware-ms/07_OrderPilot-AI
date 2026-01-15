"""Orchestrator Report - Report formatting and generation.

Refactored from 666 LOC monolith using composition pattern.

Module 5/6 of orchestrator.py split.

Contains:
- generate_report(): Main report generator
- format_technical_summary(): Format technical indicators
- format_levels_summary(): Format support/resistance levels
- generate_trading_setup(): Generate trading setup
"""

from __future__ import annotations

import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class OrchestratorReport:
    """Helper für AnalysisWorker report generation."""

    def __init__(self, parent):
        """
        Args:
            parent: AnalysisWorker Instanz
        """
        self.parent = parent

    def generate_report(self, strategy: str, symbol: str, features: dict) -> str:
        """Generate comprehensive markdown report.

        If LLM analysis is available, it will be used as the primary content.
        Otherwise, falls back to the rule-based technical analysis report.

        Args:
            strategy: Strategy name
            symbol: Trading symbol
            features: Dict of timeframe -> feature data

        Returns:
            Markdown report string
        """
        # If we have LLM analysis, use it as the primary report
        if self.parent._llm_analysis:
            lines = [f"# Deep Market Analysis: {symbol}", f"**Strategy:** {strategy}", ""]
            lines.append("---")
            lines.append("")
            lines.append(self.parent._llm_analysis)
            lines.append("")
            lines.append("---")
            lines.append("")

            # Add data collection summary at the end
            lines.append("## Datengrundlage")
            for tf, stat in features.items():
                bars = stat.get('bars', 0)
                price = stat.get('last_price', 'N/A')
                change = stat.get('period_change_pct', 0)
                lines.append(f"- **{tf}:** {bars} Bars geladen. Preis: {price} ({change}%)")
            lines.append("")
            lines.append(f"*Analyse generiert mit KI-Unterstützung ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})*")

            return "\n".join(lines)

        # Fallback: Rule-based report (no LLM available)
        lines = [f"# Deep Market Analysis: {symbol}", f"**Strategy:** {strategy}", ""]
        lines.append("*Hinweis: LLM-Analyse nicht verfügbar. Fallback auf regelbasierte Analyse.*")
        lines.append("")

        # Data Collection Summary
        lines.append("## Data Collection Report")
        for tf, stat in features.items():
            bars = stat.get('bars', 0)
            price = stat.get('last_price', 'N/A')
            change = stat.get('period_change_pct', 0)
            lines.append(f"- **{tf}:** {bars} bars loaded. Price: {price} ({change}%)")
        lines.append("")

        # Technical Analysis Summary
        lines.append("## Technical Analysis Summary")
        for tf in sorted(features.keys()):
            lines.extend(self.format_technical_summary(tf, features[tf]))

        # Support/Resistance Levels
        lines.append("## Support/Resistance Levels")
        lines.extend(self.format_levels_summary(features, symbol))

        # Trading Setup
        lines.append("## Trading Setup (Preliminary)")
        lines.extend(self.generate_trading_setup(features, symbol))
        lines.append("")

        # Footer
        lines.append("## Analysis Context")
        lines.append("Daten wurden erfolgreich live von der API abgerufen. LLM-Analyse war nicht verfügbar (API-Key fehlt oder AI deaktiviert).")
        lines.append("")
        lines.append("**Zur Aktivierung der KI-Analyse:**")
        lines.append("1. Settings → AI → AI Provider wählen")
        lines.append("2. API-Key als Umgebungsvariable setzen (z.B. OPENAI_API_KEY)")
        lines.append("3. AI aktivieren (Checkbox)")

        return "\n".join(lines)

    def format_technical_summary(self, tf: str, feature_data: dict) -> list[str]:
        """Format technical indicators for a timeframe.

        Args:
            tf: Timeframe string
            feature_data: Feature dict for timeframe

        Returns:
            List of markdown lines
        """
        lines = []
        role = self.parent._llm.get_tf_role(tf)

        lines.append(f"### {tf} ({role})")
        lines.append(f"- **Price:** {feature_data.get('last_price', 'N/A')} ({feature_data.get('period_change_pct', 0)}%)")
        lines.append(f"- **Trend:** {feature_data.get('trend_state', 'N/A')} (EMA20 dist: {feature_data.get('ema20_distance_pct', 0)}%)")
        lines.append(f"- **RSI(14):** {feature_data.get('rsi', 'N/A')} - {feature_data.get('rsi_state', 'N/A')}")
        lines.append(f"- **BB %B:** {feature_data.get('bb_percent', 'N/A')}%")
        lines.append(f"- **ATR(14):** {feature_data.get('atr', 'N/A')} ({feature_data.get('atr_pct', 0)}% of price)")
        lines.append(f"- **ADX(14):** {feature_data.get('adx', 'N/A')} (Trend Strength)")

        if feature_data.get('error'):
            lines.append(f"- **Note:** Some indicators unavailable: {feature_data['error']}")

        lines.append("")
        return lines

    def format_levels_summary(self, features: dict, symbol: str) -> list[str]:
        """Aggregate support/resistance levels across timeframes.

        Args:
            features: Dict of timeframe -> feature data
            symbol: Trading symbol

        Returns:
            List of markdown lines
        """
        lines = []
        all_support = []
        all_resistance = []

        for tf, data in features.items():
            support = data.get('support_levels', [])
            resistance = data.get('resistance_levels', [])

            if support:
                all_support.extend([(tf, level) for level in support])
            if resistance:
                all_resistance.extend([(tf, level) for level in resistance])

        if all_resistance:
            lines.append("**Resistance Levels:**")
            for tf, level in sorted(all_resistance, key=lambda x: x[1], reverse=True)[:5]:
                lines.append(f"- {level} ({tf})")
            lines.append("")

        if all_support:
            lines.append("**Support Levels:**")
            for tf, level in sorted(all_support, key=lambda x: x[1], reverse=True)[:5]:
                lines.append(f"- {level} ({tf})")
            lines.append("")

        return lines

    def generate_trading_setup(self, features: dict, symbol: str) -> list[str]:
        """Generate preliminary trading setup based on technical analysis.

        Args:
            features: Dict of timeframe -> feature data
            symbol: Trading symbol

        Returns:
            List of markdown lines
        """
        lines = []

        # Use the smallest timeframe for execution details
        exec_tf = None
        for tf in ["1m", "5m", "15m"]:
            if tf in features:
                exec_tf = tf
                break

        if not exec_tf:
            lines.append("*Insufficient data for trading setup*")
            return lines

        data = features[exec_tf]
        current_price = data.get('last_price', 0)
        atr = data.get('atr', 0)
        trend = data.get('trend_state', 'Neutral')

        if current_price == 0 or atr == 0:
            lines.append("*Insufficient data for trading setup*")
            return lines

        # Calculate entry, target, and stop based on trend
        if "Uptrend" in trend:
            # Long setup
            entry = current_price
            target = entry + (2 * atr)
            stop_loss = entry - (1.5 * atr)
            direction = "LONG"
        elif "Downtrend" in trend:
            # Short setup
            entry = current_price
            target = entry - (2 * atr)
            stop_loss = entry + (1.5 * atr)
            direction = "SHORT"
        else:
            # Neutral - no clear setup
            lines.append(f"*No clear directional bias. Current price: {current_price}*")
            return lines

        risk = abs(entry - stop_loss)
        reward = abs(target - entry)
        rr_ratio = reward / risk if risk > 0 else 0

        lines.append(f"**Direction:** {direction}")
        lines.append(f"**Entry:** {round(entry, 4)}")
        lines.append(f"**Target:** {round(target, 4)}")
        lines.append(f"**Stop Loss:** {round(stop_loss, 4)}")
        lines.append(f"**Risk/Reward:** 1:{round(rr_ratio, 2)}")
        lines.append("")
        lines.append("*Note: This is a preliminary setup based on technical indicators. Not financial advice.*")

        return lines
