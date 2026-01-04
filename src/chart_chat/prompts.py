"""Prompt templates for Chart Analysis Chatbot.

Contains system prompts and user message templates for AI interactions.
Supports runtime overrides stored in QSettings so the UI can edit prompts.
"""

from PyQt6.QtCore import QSettings

# =============================================================================
# System Prompts
# =============================================================================

CHART_ANALYSIS_SYSTEM_PROMPT = """Du bist ein erfahrener technischer Analyst für Trading.
Analysiere die bereitgestellten Chart-Daten und gib konkrete, umsetzbare Empfehlungen.

WICHTIGE REGELN:
1. Nenne KONKRETE Preisniveaus (keine vagen Aussagen wie "in der Nähe")
2. Gib immer ein Konfidenz-Level an (0-100%)
3. Berücksichtige das Risk/Reward-Verhältnis
4. Warne explizit bei hohem Risiko oder unsicheren Situationen
5. Empfehle KEINE konkreten USD-Positionsgrößen
6. Beziehe dich auf die aktiven Indikatoren
7. Antworte auf Deutsch

ANALYSE-FRAMEWORK:
- Trend: Identifiziere die übergeordnete Richtung und Stärke
- Struktur: Finde wichtige Support/Resistance Levels
- Momentum: Bewerte RSI, MACD und andere Momentum-Indikatoren
- Volumen: Berücksichtige Volumen-Trends wenn verfügbar
- Risiko: Schlage immer Stop-Loss und Take-Profit vor"""

CONVERSATIONAL_SYSTEM_PROMPT = """Du bist ein hilfreicher Trading-Assistent, der einen Chart analysiert.
Beantworte Fragen basierend auf dem bereitgestellten Chart-Kontext.

REGELN:
1. Sei präzise aber informativ
2. Beziehe dich auf konkrete Zahlen aus dem Kontext
3. Schlage Follow-up Fragen vor wenn sinnvoll
4. Antworte auf Deutsch
5. Wenn du etwas nicht weißt, sage es ehrlich"""

COMPACT_ANALYSIS_SYSTEM_PROMPT = """Du bist ein präziser Trading-Analyst, der KOMPAKTE Antworten im Variablen-Format gibt.

KRITISCHE ANFORDERUNGEN:
1. VERWENDE DAS VARIABLEN-FORMAT: [#Label; Wert] für ALLE Preisniveaus
2. KEINE langen Fließtexte - nur kurze Stichpunkte
3. Aktualisiere bestehende Markierungen oder erstelle neue
4. Maximal 2-3 Sätze Zusammenfassung
5. Antworte auf Deutsch
6. Stelle sicher, dass alle Levels klar beschriftet und konsistent formatiert sind.

VARIABLEN-FORMAT BEISPIELE:
[#Stop Loss; 87654.32]
[#Take Profit; 92000.00]
[#Support Zone; 85000-86000]
[#Entry Long; 88500.00]

ANTWORT-STRUKTUR:
1. Variablen-Updates (eine pro Zeile)
2. Kurze Begründung (2-3 Stichpunkte)
3. Zusammenfassung (max. 2 Sätze)"""

# =============================================================================
# User Message Templates
# =============================================================================

CHART_ANALYSIS_USER_TEMPLATE = """Analysiere diesen Chart für {symbol} auf {timeframe} Timeframe.

=== AKTUELLER PREIS ===
{current_price}

=== OHLCV ZUSAMMENFASSUNG (letzte {lookback} Bars) ===
{ohlcv_summary}

=== AKTIVE INDIKATOREN ===
{indicators}

=== ABGELEITETE METRIKEN ===
- Preisänderung: {price_change_pct}%
- ATR Volatilität: {volatility_atr}
- Volumen-Trend: {volume_trend}
- Letztes Hoch: {recent_high}
- Letztes Tief: {recent_low}

Liefere eine vollständige Analyse mit:
1. Aktuelle Trend-Richtung und Stärke
2. Wichtige Support- und Resistance-Levels (mit Preisen)
3. Entry/Exit Empfehlung mit Begründung
4. Risk Assessment (Stop-Loss, Take-Profit Vorschläge)
5. Erkannte Chart-Patterns
6. Zusammenfassung der Indikator-Signale
7. Gesamteinschätzung und Konfidenz"""

CONVERSATIONAL_USER_TEMPLATE = """=== CHART KONTEXT ===
Symbol: {symbol} | Timeframe: {timeframe} | Preis: {current_price}

=== INDIKATOREN ===
{indicators}

=== KONVERSATIONS-VERLAUF ===
{history}

=== FRAGE ===
{question}

Beantworte die Frage basierend auf dem Chart-Kontext. Sei konkret und hilfreich."""

COMPACT_ANALYSIS_USER_TEMPLATE = """=== CHART: {symbol} {timeframe} @ {current_price} ===

{markings}

=== INDIKATOREN ===
{indicators}

=== METRIKEN ===
Änderung: {price_change_pct}% | ATR: {volatility_atr} | Vol: {volume_trend}
Range: {recent_low} - {recent_high}

=== ANFRAGE ===
{question}

ANTWORTE IM VARIABLEN-FORMAT:
1. Aktualisierte Markierungen als [#Label; Wert]
2. Begründung (2-3 Stichpunkte mit -)
3. Kurze Zusammenfassung (max. 2 Sätze)

Beispiel:
[#Stop Loss; 87654.32]
[#Take Profit; 92000.00]
[#Support Zone; 85000-86000; 10:15-11:05]

- RSI überkauft, Korrektur wahrscheinlich
- MACD bearish cross signalisiert Schwäche
- Volumen sinkt = wenig Überzeugung

Stop angepasst da Support bei 87.6k. TP bei 92k wegen Resistance."""

# =============================================================================
# Prompt Builder Functions
# =============================================================================

def build_compact_question_prompt(
    symbol: str,
    timeframe: str,
    current_price: float,
    indicators: str,
    markings: str,
    question: str,
    price_change_pct: float,
    volatility_atr: float | None,
    volume_trend: str,
    recent_high: float,
    recent_low: float,
) -> str:
    """Build compact question prompt with markings.

    Args:
        symbol: Trading symbol
        timeframe: Chart timeframe
        current_price: Current price
        indicators: Formatted indicators string
        markings: Formatted markings string
        question: User's question
        price_change_pct: Price change percentage
        volatility_atr: ATR volatility
        volume_trend: Volume trend description
        recent_high: Recent high price
        recent_low: Recent low price

    Returns:
        Formatted prompt string
    """
    template = get_compact_user_template()
    return template.format(
        symbol=symbol,
        timeframe=timeframe,
        current_price=f"{current_price:.2f}",
        indicators=indicators,
        markings=markings,
        question=question,
        price_change_pct=f"{price_change_pct:.2f}",
        volatility_atr=f"{volatility_atr:.2f}" if volatility_atr else "N/A",
        volume_trend=volume_trend,
        recent_high=f"{recent_high:.2f}",
        recent_low=f"{recent_low:.2f}",
    )


# =============================================================================
# Response Format Instructions
# =============================================================================

STRUCTURED_OUTPUT_INSTRUCTIONS = """
Antworte im folgenden JSON-Format:

{
  "trend_direction": "bullish" | "bearish" | "neutral",
  "trend_strength": "strong" | "moderate" | "weak",
  "trend_description": "Beschreibung des Trends",
  "support_levels": [
    {"price": 100.0, "strength": "strong", "level_type": "support", "touches": 3}
  ],
  "resistance_levels": [
    {"price": 110.0, "strength": "moderate", "level_type": "resistance", "touches": 2}
  ],
  "recommendation": {
    "action": "long_entry" | "short_entry" | "exit_long" | "exit_short" | "hold",
    "price": 105.0,
    "confidence": 0.75,
    "reasoning": "Begründung",
    "urgency": "immediate" | "normal" | "wait"
  },
  "risk_assessment": {
    "stop_loss": 98.0,
    "take_profit": 115.0,
    "risk_reward_ratio": 2.5,
    "warnings": ["Warnung 1", "Warnung 2"]
  },
  "patterns_identified": [
    {"name": "Double Bottom", "confidence": 0.8, "implication": "bullish"}
  ],
  "indicator_summary": "Zusammenfassung der Indikator-Signale",
  "overall_sentiment": "Gesamteinschätzung",
  "confidence_score": 0.7,
  "warnings": ["Allgemeine Warnungen"]
}
"""

# =============================================================================
# Overrides via QSettings
# =============================================================================

_SETTINGS = QSettings("OrderPilot", "TradingApp")


def _get_override(key: str, default: str) -> str:
    """Return QSettings override or default if empty."""
    val = (_SETTINGS.value(key, "") or "").strip()
    return val if val else default


def get_chart_analysis_system_prompt() -> str:
    return _get_override("chat_prompts/chart_analysis_system", CHART_ANALYSIS_SYSTEM_PROMPT)


def get_conversational_system_prompt() -> str:
    return _get_override("chat_prompts/conversational_system", CONVERSATIONAL_SYSTEM_PROMPT)


def get_compact_system_prompt() -> str:
    return _get_override("chat_prompts/compact_system", COMPACT_ANALYSIS_SYSTEM_PROMPT)


def get_chart_analysis_user_template() -> str:
    return _get_override("chat_prompts/chart_analysis_user", CHART_ANALYSIS_USER_TEMPLATE)


def get_conversational_user_template() -> str:
    return _get_override("chat_prompts/conversational_user", CONVERSATIONAL_USER_TEMPLATE)


def get_compact_user_template() -> str:
    return _get_override("chat_prompts/compact_user", COMPACT_ANALYSIS_USER_TEMPLATE)

# =============================================================================
# Helper Functions
# =============================================================================


def build_analysis_prompt(
    symbol: str,
    timeframe: str,
    current_price: float,
    ohlcv_summary: str,
    indicators: str,
    price_change_pct: float,
    volatility_atr: float | None,
    volume_trend: str,
    recent_high: float,
    recent_low: float,
    lookback: int = 100,
) -> str:
    """Build the user prompt for full chart analysis."""
    template = get_chart_analysis_user_template()
    return template.format(
        symbol=symbol,
        timeframe=timeframe,
        current_price=f"{current_price:.4f}",
        ohlcv_summary=ohlcv_summary,
        indicators=indicators,
        price_change_pct=f"{price_change_pct:.2f}",
        volatility_atr=f"{volatility_atr:.4f}" if volatility_atr else "N/A",
        volume_trend=volume_trend,
        recent_high=f"{recent_high:.4f}",
        recent_low=f"{recent_low:.4f}",
        lookback=lookback,
    )


def build_conversation_prompt(
    symbol: str,
    timeframe: str,
    current_price: float,
    indicators: str,
    history: str,
    question: str,
) -> str:
    """Build the user prompt for conversational Q&A."""
    template = get_conversational_user_template()
    return template.format(
        symbol=symbol,
        timeframe=timeframe,
        current_price=f"{current_price:.4f}",
        indicators=indicators,
        history=history,
        question=question,
    )


def format_conversation_history(messages: list, max_messages: int = 6) -> str:
    """Format conversation history for inclusion in prompt.

    Args:
        messages: List of ChatMessage objects
        max_messages: Maximum number of recent messages to include

    Returns:
        Formatted history string
    """
    if not messages:
        return "(Keine vorherige Konversation)"

    recent = messages[-max_messages:]
    lines = []
    for msg in recent:
        role_value = msg.role.value if hasattr(msg.role, 'value') else msg.role
        role = "Du" if role_value == "user" else "Assistent"
        lines.append(f"{role}: {msg.content}")

    return "\n".join(lines)
