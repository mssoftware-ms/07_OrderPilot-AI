# Integration der AI-Konfiguration, Prompts & Schemas

## Module & Hooks
- **E4 – Order-Freigabe-Dialog:** Nutze `prompts/strategy_explain.yaml` → erwarte `schemas/AnalysisResult.json`. Zeige Begründung & Kontraindikatoren, Gebührenhinweis.
- **E5 – Watchlist & Alarme:** Nutze `prompts/alert_triage.yaml` → erwarte `schemas/AlertDecision.json`. Verwende das Ranking für Benachrichtigungs-Priorität.
- **D1 – Backtesting:** Nutze `prompts/backtest_review.yaml` → erwarte `schemas/BacktestSummary.json`. Zeige Empfehlungen & Risiken.
- **C2 – Strategy Engine (post_signal_analysis):** Gleich wie E4; das Ergebnis beeinflusst NICHT autonom Orders, sondern nur die Darstellung und Freigabe-UX.
- **F2 – Logs (JSON):** Ergänze KI-Felder (model, tokens, cost, promptVersion, schema).

## Profile-Ladepfad
- Lese `config/profiles/{profile}.yaml` und setze Defaults (Modell, Budget, Timeouts, RateLimits, Feature-Flags).
- Hole `OPENAI_API_KEY` via Credential Manager/`keyring`.

## Schema-Validierung
- Validiere **jedes** KI-Ergebnis gegen das jeweilige JSON-Schema.
- Bei Fehler: saubere UI-Meldung und Fallback (keine Blockade des Order-Flows).

## Kosten-/Limitsteuerung
- Erzwinge Budgetgrenzen (Warn/Block).  
- Backoff/Retry mit Jitter und Idempotenz.  
- Caching (Kontext-Hash + TTL) für wiederkehrende Fragen.

