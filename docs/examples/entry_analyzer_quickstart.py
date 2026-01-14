"""Quick Start Example: Entry Analyzer mit ATR-normalisierter Engine.

Zeigt, wie man die neue entry_signal_engine.py nutzt, um
Einträge auf 1m/5m-Timeframes zu finden.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_sample_candles(n: int = 200) -> list[dict]:
    """Erstelle Sample-Daten für Demo."""
    from random import random

    candles = []
    base_price = 100.0
    base_ts = int(datetime.now().timestamp()) - (n * 60)

    for i in range(n):
        # Simuliere leichten Uptrend mit Noise
        trend = i * 0.05
        noise = (random() - 0.5) * 2.0
        price = base_price + trend + noise

        # OHLC
        o = price - random() * 0.5
        h = price + random() * 1.0
        l = price - random() * 1.0
        c = price + (random() - 0.5) * 0.3

        candles.append(
            {
                "timestamp": base_ts + (i * 60),
                "open": o,
                "high": max(o, h, c),
                "low": min(o, l, c),
                "close": c,
                "volume": 1000.0 + random() * 500,
            }
        )

    return candles


def example_1_basic_usage():
    """Beispiel 1: Grundlegende Nutzung der Engine."""
    from src.analysis.entry_signals.entry_signal_engine import (
        OptimParams,
        calculate_features,
        detect_regime,
        generate_entries,
    )

    logger.info("=" * 80)
    logger.info("BEISPIEL 1: Grundlegende Nutzung")
    logger.info("=" * 80)

    # Sample-Daten
    candles = create_sample_candles(200)
    logger.info("✓ %d Kerzen generiert", len(candles))

    # 1. Features berechnen
    params = OptimParams()
    features = calculate_features(candles, params)
    logger.info("✓ Features berechnet: %s", ", ".join(features.keys()))

    # 2. Regime erkennen
    regime = detect_regime(features, params)
    logger.info("✓ Regime erkannt: %s", regime.value)

    # 3. Entries generieren
    entries = generate_entries(candles, features, regime, params)
    logger.info("✓ Entries generiert: %d", len(entries))

    # 4. Entries ausgeben
    if entries:
        logger.info("\nErste 5 Entries:")
        for i, e in enumerate(entries[:5], 1):
            ts = datetime.fromtimestamp(e.timestamp).strftime("%H:%M:%S")
            logger.info(
                "  %d. [%s] %s @ %.2f (conf=%.1f%%, reasons=%s)",
                i,
                ts,
                e.side.value,
                e.price,
                e.confidence * 100,
                ", ".join(e.reason_tags[:2]),
            )
    else:
        logger.warning("⚠ Keine Entries gefunden!")

    return entries


def example_2_with_optimizer():
    """Beispiel 2: Mit Fast Optimizer."""
    from src.analysis.entry_signals.entry_signal_engine import (
        OptimParams,
        calculate_features,
        detect_regime,
        generate_entries,
    )
    from src.analysis.indicator_optimization.optimizer import FastOptimizer

    logger.info("\n" + "=" * 80)
    logger.info("BEISPIEL 2: Mit Optimizer")
    logger.info("=" * 80)

    # Sample-Daten
    candles = create_sample_candles(200)
    logger.info("✓ %d Kerzen generiert", len(candles))

    # 1. Base Params
    base_params = OptimParams()

    # 2. Optimizer laufen lassen (1.2 Sekunden Budget)
    logger.info("⏳ Optimizer läuft (1200ms Budget)...")
    optimizer = FastOptimizer()
    optimized = optimizer.optimize(candles, base_params, budget_ms=1200, seed=42)
    logger.info("✓ Optimizer abgeschlossen")

    # 3. Zeige optimierte Params
    logger.info("\nOptimierte Parameter:")
    logger.info("  EMA Fast/Slow: %d / %d", optimized.ema_fast, optimized.ema_slow)
    logger.info("  ATR Period: %d", optimized.atr_period)
    logger.info("  RSI Period: %d", optimized.rsi_period)
    logger.info("  BB Period/Std: %d / %.1f", optimized.bb_period, optimized.bb_std)
    logger.info("  Min Confidence: %.2f", optimized.min_confidence)

    # 4. Entries mit optimierten Params
    features = calculate_features(candles, optimized)
    regime = detect_regime(features, optimized)
    entries = generate_entries(candles, features, regime, optimized)

    logger.info("\n✓ Entries mit optimierten Params: %d", len(entries))

    # 5. Vergleiche Confidence
    if entries:
        avg_conf = sum(e.confidence for e in entries) / len(entries)
        logger.info("  Durchschnittliche Confidence: %.1f%%", avg_conf * 100)

    return entries


def example_3_debug_mode():
    """Beispiel 3: Debug-Modus bei 0 Entries."""
    from src.analysis.entry_signals.entry_signal_engine import (
        OptimParams,
        calculate_features,
        detect_regime,
        generate_entries,
        debug_summary,
    )

    logger.info("\n" + "=" * 80)
    logger.info("BEISPIEL 3: Debug-Modus")
    logger.info("=" * 80)

    # Sample-Daten (weniger, um evtl. 0 Entries zu provozieren)
    candles = create_sample_candles(50)
    logger.info("✓ %d Kerzen generiert (wenig für Demo)", len(candles))

    # Features berechnen
    params = OptimParams()
    features = calculate_features(candles, params)

    # Debug Summary ausgeben
    summary = debug_summary(features)
    logger.info("\nDebug Summary:")
    for key, value in summary.items():
        if key == "ok":
            continue
        logger.info("  %-20s: %.4f", key, value)

    # Regime + Entries
    regime = detect_regime(features, params)
    entries = generate_entries(candles, features, regime, params)

    logger.info("\n✓ Regime: %s", regime.value)
    logger.info("✓ Entries: %d", len(entries))

    # Diagnose
    if not entries:
        logger.warning("\n⚠ DIAGNOSE: Keine Entries gefunden")
        logger.warning("Mögliche Ursachen:")

        if summary.get("n", 0) < 50:
            logger.warning("  - Zu wenige Kerzen (< 50)")

        if abs(summary.get("last_dist_ema_atr", 0)) < 0.1:
            logger.warning("  - Preis zu nah an EMA (dist_ema_atr zu klein)")

        if 45 < summary.get("last_rsi", 50) < 55:
            logger.warning("  - RSI zu neutral (nicht oversold/overbought)")

        if summary.get("last_bb_percent", 0.5) > 0.3 and summary.get("last_bb_percent", 0.5) < 0.7:
            logger.warning("  - BB% im Mittelbereich (nicht an Extremen)")

        logger.warning("\nEmpfehlung:")
        logger.warning("  - Mehr Kerzen laden (>= 100)")
        logger.warning("  - min_confidence reduzieren (z.B. 0.54)")
        logger.warning("  - bb_entry erhöhen (z.B. 0.20)")

    return entries


def example_4_analyzer_integration():
    """Beispiel 4: Integration mit VisibleChartAnalyzer."""
    from src.analysis.visible_chart.analyzer import VisibleChartAnalyzer
    from src.analysis.visible_chart.types import VisibleRange

    logger.info("\n" + "=" * 80)
    logger.info("BEISPIEL 4: VisibleChartAnalyzer Integration")
    logger.info("=" * 80)

    # Sample-Daten
    candles = create_sample_candles(200)
    logger.info("✓ %d Kerzen generiert", len(candles))

    # Visible Range
    visible_range = VisibleRange(
        from_ts=candles[0]["timestamp"],
        to_ts=candles[-1]["timestamp"],
    )

    # Analyzer mit Optimizer
    analyzer = VisibleChartAnalyzer(use_optimizer=True, use_cache=False)

    # Analyse durchführen
    logger.info("⏳ Analyzer läuft...")
    result = analyzer.analyze_with_candles(
        visible_range=visible_range,
        symbol="BTC/USD",
        timeframe="1m",
        candles=candles,
    )

    logger.info("✓ Analyse abgeschlossen in %.1fms", result.analysis_time_ms)
    logger.info("\nErgebnisse:")
    logger.info("  Regime: %s", result.regime.value if result.regime else "None")
    logger.info("  Entries: %d", len(result.entries) if result.entries else 0)
    logger.info("  Active Set: %s", result.active_set.name if result.active_set else "None")

    # Chart-Marker für TradingView
    if result.entries:
        logger.info("\nChart-Marker (erste 3):")
        for i, e in enumerate(result.entries[:3], 1):
            marker = e.to_chart_marker()
            ts = datetime.fromtimestamp(marker["time"]).strftime("%H:%M:%S")
            logger.info(
                "  %d. [%s] %s %s @ time=%d",
                i,
                ts,
                marker["shape"],
                marker["color"],
                marker["time"],
            )

    return result


def main():
    """Führe alle Beispiele aus."""
    logger.info("\n🚀 Entry Analyzer Quick Start\n")

    try:
        # Beispiel 1: Basic
        entries1 = example_1_basic_usage()

        # Beispiel 2: Optimizer
        entries2 = example_2_with_optimizer()

        # Beispiel 3: Debug
        entries3 = example_3_debug_mode()

        # Beispiel 4: Analyzer Integration
        result = example_4_analyzer_integration()

        # Zusammenfassung
        logger.info("\n" + "=" * 80)
        logger.info("ZUSAMMENFASSUNG")
        logger.info("=" * 80)
        logger.info("✓ Beispiel 1 (Basic):     %d Entries", len(entries1))
        logger.info("✓ Beispiel 2 (Optimizer): %d Entries", len(entries2))
        logger.info("✓ Beispiel 3 (Debug):     %d Entries", len(entries3))
        logger.info("✓ Beispiel 4 (Analyzer):  %d Entries", len(result.entries) if result.entries else 0)

        logger.info("\n✅ Alle Beispiele erfolgreich!")

    except Exception as e:
        logger.error("\n❌ Fehler: %s", e, exc_info=True)
        raise


if __name__ == "__main__":
    main()
