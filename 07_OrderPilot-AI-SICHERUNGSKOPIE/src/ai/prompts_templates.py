"""Prompt Templates for OrderPilot-AI Trading Application.

Refactored from prompts.py monolith.

Module 1/5 of prompts.py split.

Contains:
- PromptTemplates class with all prompt template strings
"""


class PromptTemplates:
    """Collection of prompt templates for different AI tasks."""

    # Order Analysis Prompts
    ORDER_ANALYSIS = """As an experienced trading analyst, analyze the following order for risk and opportunity.

Order Details:
{order_details}

Market Context:
{market_context}

Portfolio Context:
{portfolio_context}

Please provide:
1. Approval recommendation with confidence level (0-1)
2. Identified risks (list specific concerns)
3. Identified opportunities (list specific advantages)
4. Fee impact analysis
5. Suggested adjustments if any

Focus on quantitative analysis and specific actionable insights."""

    # Alert Triage Prompts
    ALERT_TRIAGE = """As a trading system monitor, triage the following alert based on urgency and portfolio impact.

Alert Information:
{alert_info}

Current Portfolio:
{portfolio_state}

Market Conditions:
{market_conditions}

Assess:
1. Priority score (0-1, where 1 is most urgent)
2. Whether immediate action is required
3. Key factors driving the priority
4. Suggested actions (specific and actionable)
5. Estimated urgency level (immediate/high/medium/low)

Consider the portfolio risk exposure and current market volatility."""

    # Backtest Review Prompts
    BACKTEST_REVIEW = """As a quantitative trading strategist, review the following backtest results.

Strategy: {strategy_name}
Test Period: {test_period}
Market Conditions: {market_conditions}

Performance Metrics:
{performance_metrics}

Trade Statistics:
{trade_statistics}

Provide:
1. Overall assessment and performance rating (0-10)
2. Key strengths of the strategy
3. Main weaknesses identified
4. Specific improvement suggestions
5. Parameter optimization recommendations
6. Risk assessment
7. Analysis of maximum drawdown periods

Focus on actionable improvements and realistic expectations."""

    # Signal Analysis Prompts
    SIGNAL_ANALYSIS = """As a technical analyst, evaluate the following trading signal.

Signal Information:
{signal_info}

Technical Indicators:
{indicators}

Recent Price Action:
{price_action}

Market Context:
{market_context}

Analyze:
1. Signal quality (0-1)
2. Whether to proceed with the trade
3. Technical analysis summary
4. Current market conditions assessment
5. Warning signals present
6. Confirming signals present
7. Timing assessment (excellent/good/neutral/poor)
8. Suggested delay if timing is suboptimal

Provide objective technical analysis without emotional bias."""

    # Deep Analysis (Multi-Timeframe) Prompts
    DEEP_ANALYSIS = """Du bist ein erfahrener Trading-Analyst für Kryptowährungen. Analysiere die folgenden Multi-Timeframe-Daten und erstelle einen umfassenden Marktreport.

## Asset
**Symbol:** {symbol}
**Strategie:** {strategy}

## Technische Daten (Multi-Timeframe)
{technical_data}

## Support/Resistance Level
{sr_levels}

## Aufgabe
Erstelle einen vollständigen Marktanalysereport mit folgenden Abschnitten:

### 1. Marktübersicht
- Aktueller Trend über alle Timeframes (Trendharmonie vs. Divergenz)
- Dominierendes Momentum (bullish/bearish/neutral)
- Volatilitätseinschätzung basierend auf ATR

### 2. Technische Analyse
- Multi-Timeframe Trend-Alignment (MTF-Konfluenz)
- RSI Divergenzen oder Bestätigungen
- EMA-Positionierung und Crossovers
- Bollinger Band Position und Squeeze-Situationen

### 3. Support/Resistance Analyse
- Wichtigste Levels mit Begründung
- Potentielle Breakout/Breakdown Zonen
- Liquiditätszonen

### 4. Trading Setup (wenn vorhanden)
Nur wenn ein klares Setup existiert:
- **Richtung:** LONG/SHORT/NEUTRAL
- **Entry Zone:** Preisbereich
- **Target 1:** erstes Kursziel
- **Target 2:** zweites Kursziel (optional)
- **Stop Loss:** mit Begründung
- **Risk/Reward:** Verhältnis
- **Konfidenz:** 1-5 (5 = sehr hoch)

### 5. Risikofaktoren
- Gegenläufige Signale
- Wichtige Warnsignale
- Marktbedingungen die gegen das Setup sprechen

### 6. Fazit
- Zusammenfassung in 2-3 Sätzen
- Handlungsempfehlung

**WICHTIG:** Antworte auf Deutsch. Formatiere als Markdown. Sei präzise und datenbasiert."""

    # Risk Assessment Prompts
    RISK_ASSESSMENT = """Assess the risk profile of the following trading position.

Position Details:
{position_details}

Account Status:
{account_status}

Market Volatility:
{volatility_metrics}

Historical Performance:
{historical_data}

Evaluate:
1. Position risk score (0-1)
2. Portfolio impact if stop loss triggered
3. Correlation with existing positions
4. Volatility-adjusted position sizing recommendation
5. Suggested risk mitigation measures

Use quantitative risk metrics and consider portfolio diversification."""
