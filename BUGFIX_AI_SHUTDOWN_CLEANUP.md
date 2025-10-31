# Bugfix: AI Service Shutdown Error

## Problem
Beim Beenden der Anwendung trat der Fehler auf:
```
ai has no timeout
```

## Ursache
Die `closeEvent()` Methode verwendete `asyncio.create_task()` zum Schließen des AI-Service und Trennen des Brokers. Dies führte zu mehreren Problemen:

1. **Fehlende Attribut-Prüfung**: Es wurde nicht geprüft, ob `ai_service.close()` existiert
2. **Async/Sync Handling**: Keine Unterscheidung zwischen async und sync close-Methoden
3. **Event Loop Status**: Der Event Loop könnte bereits beendet sein
4. **Timer nicht gestoppt**: Update-Timer liefen während des Shutdowns weiter
5. **Fehlende Stream-Cleanup**: Real-time Streams wurden nicht gestoppt

## Lösung

### 1. Robuste Close-Event Implementierung

```python
def closeEvent(self, event):
    """Handle application close event."""
    logger.info("Application closing...")

    # 1. Save settings (error-safe)
    try:
        self.save_settings()
    except Exception as e:
        logger.error(f"Error saving settings: {e}")

    # 2. Stop all timers
    try:
        if hasattr(self, 'time_timer'):
            self.time_timer.stop()
        if hasattr(self, 'dashboard_timer'):
            self.dashboard_timer.stop()
    except Exception as e:
        logger.error(f"Error stopping timers: {e}")

    # 3. Disconnect broker (with event loop check)
    if self.broker:
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.ensure_future(self.disconnect_broker())
            else:
                loop.run_until_complete(self.disconnect_broker())
        except Exception as e:
            logger.error(f"Error disconnecting broker: {e}")

    # 4. Close AI service (with attribute check)
    if self.ai_service:
        try:
            if hasattr(self.ai_service, 'close'):
                if asyncio.iscoroutinefunction(self.ai_service.close):
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        asyncio.ensure_future(self.ai_service.close())
                    else:
                        loop.run_until_complete(self.ai_service.close())
                else:
                    self.ai_service.close()
            logger.info("AI service closed")
        except Exception as e:
            logger.error(f"Error closing AI service: {e}")

    # 5. Stop real-time streams
    try:
        if hasattr(self.history_manager, 'stream_client') and self.history_manager.stream_client:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.ensure_future(self.history_manager.stop_realtime_stream())
    except Exception as e:
        logger.error(f"Error stopping stream: {e}")

    logger.info("Application closed successfully")
    event.accept()
```

### 2. Verbesserungen

**Fehler-Sicherheit:**
- Jeder Cleanup-Schritt ist in try-except gewrappt
- Fehler werden geloggt, stoppen aber nicht den weiteren Cleanup

**Async-Handling:**
- Prüfung ob Event Loop läuft
- Unterscheidung zwischen async und sync Methoden
- Verwendung von `asyncio.ensure_future()` für laufende Loops
- Verwendung von `run_until_complete()` für gestoppte Loops

**Vollständiger Cleanup:**
- Timer werden gestoppt
- Broker wird getrennt
- AI Service wird geschlossen
- Real-time Streams werden gestoppt
- Settings werden gespeichert

## Testing

Teste den Shutdown durch:

```bash
# 1. Starte die Anwendung
python start_orderpilot.py

# 2. Verbinde mit Mock Broker
# 3. Öffne Settings und konfiguriere AI
# 4. Schließe die Anwendung (X-Button oder Ctrl+Q)

# Erwartetes Ergebnis:
# - Keine Fehler im Log
# - "Application closed successfully" im Log
# - Sauberer Exit
```

## Geänderte Dateien

- `src/ui/app.py`: `closeEvent()` Methode komplett überarbeitet

## Weitere Empfehlungen

1. **Context Manager Pattern**: Erwäge, Services als Context Manager zu implementieren
2. **Signal Handler**: Füge Signal Handler für SIGTERM/SIGINT hinzu
3. **Graceful Shutdown**: Implementiere einen Shutdown-Timer für langsame Services
4. **Connection Pool Cleanup**: Stelle sicher, dass DB-Connections geschlossen werden

## Datum
2025-10-31
