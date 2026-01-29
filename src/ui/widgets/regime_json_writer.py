"""Regime JSON Writer - Schreibt entry_expression in Regime JSON.

Fügt entry_expression-Feld zu existierenden Regime JSON hinzu.
Erstellt Backup der Original-Datei.

Author: Claude Code
Date: 2026-01-29
"""

from __future__ import annotations

import json
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class RegimeJsonWriter:
    """Schreibt entry_expression in Regime JSON Dateien."""

    @staticmethod
    def write_entry_expression(
        json_path: str | Path,
        entry_expression: str,
        create_backup: bool = True,
        add_comments: bool = True
    ) -> tuple[bool, str]:
        """Fügt entry_expression zu Regime JSON hinzu.

        Args:
            json_path: Pfad zur Regime JSON
            entry_expression: CEL Expression String
            create_backup: Erstellt Backup der Original-Datei
            add_comments: Fügt _comment Felder hinzu für Dokumentation

        Returns:
            (success, message) - success=True wenn erfolgreich, message=Fehler/Info

        Example:
            >>> writer = RegimeJsonWriter()
            >>> success, msg = writer.write_entry_expression(
            ...     "regime.json",
            ...     "trigger_regime_analysis() && side == 'long'"
            ... )
            >>> print(msg)
            ✅ entry_expression erfolgreich gespeichert
        """
        path = Path(json_path)
        if not path.exists():
            return False, f"❌ Datei nicht gefunden: {path}"

        try:
            # 1. Lade existierende JSON
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # 2. Erstelle Backup (optional)
            if create_backup:
                backup_path = RegimeJsonWriter._create_backup(path)
                logger.info(f"Backup erstellt: {backup_path.name}")

            # 3. Füge entry_expression hinzu
            old_expression = data.get("entry_expression")
            data["entry_expression"] = entry_expression

            # 4. Füge Kommentare hinzu (optional)
            if add_comments:
                data["_comment_entry_expression"] = (
                    "⚠️ WICHTIG: Die entry_expression wurde MANUELL im CEL-Editor hinzugefügt! "
                    "Entry Analyzer generiert JSON OHNE entry_expression. "
                    "Du musst sie selbst schreiben basierend auf den Regime-IDs aus regimes[].id"
                )
                data["_comment_entry_expression_edited"] = datetime.now().isoformat()

            # 5. Update metadata (optional)
            if "metadata" in data:
                data["metadata"]["updated_at"] = datetime.now().isoformat()
                if "tags" in data["metadata"]:
                    if "cel-entry" not in data["metadata"]["tags"]:
                        data["metadata"]["tags"].append("cel-entry")

            # 6. Schreibe zurück
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            # 7. Log und Return
            if old_expression:
                logger.info(
                    f"entry_expression überschrieben in {path.name}\n"
                    f"  Alt: {old_expression[:50]}...\n"
                    f"  Neu: {entry_expression[:50]}..."
                )
                return True, (
                    f"✅ entry_expression erfolgreich überschrieben\n"
                    f"📂 Backup: {backup_path.name if create_backup else 'None'}"
                )
            else:
                logger.info(
                    f"entry_expression hinzugefügt in {path.name}\n"
                    f"  Expression: {entry_expression[:50]}..."
                )
                return True, (
                    f"✅ entry_expression erfolgreich hinzugefügt\n"
                    f"📂 Backup: {backup_path.name if create_backup else 'None'}"
                )

        except json.JSONDecodeError as e:
            error_msg = f"❌ Ungültiges JSON: {e.msg}"
            logger.error(error_msg)
            return False, error_msg

        except Exception as e:
            error_msg = f"❌ Fehler beim Schreiben: {e}"
            logger.exception(error_msg)
            return False, error_msg

    @staticmethod
    def _create_backup(path: Path) -> Path:
        """Erstellt Backup der JSON-Datei.

        Args:
            path: Pfad zur Original-Datei

        Returns:
            Pfad zur Backup-Datei

        Example:
            regime.json → regime.json.backup.20260129_120530
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = path.with_suffix(f".json.backup.{timestamp}")

        shutil.copy2(path, backup_path)

        return backup_path

    @staticmethod
    def save_as_new(
        json_path: str | Path,
        entry_expression: str,
        new_name: Optional[str] = None
    ) -> tuple[bool, str, Optional[Path]]:
        """Speichert JSON mit entry_expression als neue Datei.

        Args:
            json_path: Pfad zur Original Regime JSON
            entry_expression: CEL Expression String
            new_name: Optionaler neuer Dateiname (sonst auto-generiert)

        Returns:
            (success, message, new_path) - new_path ist der Pfad zur neuen Datei

        Example:
            >>> writer = RegimeJsonWriter()
            >>> success, msg, new_path = writer.save_as_new(
            ...     "regime.json",
            ...     "trigger_regime_analysis() && ...",
            ...     "regime_with_entry.json"
            ... )
        """
        path = Path(json_path)
        if not path.exists():
            return False, f"❌ Datei nicht gefunden: {path}", None

        try:
            # 1. Lade existierende JSON
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # 2. Füge entry_expression hinzu
            data["entry_expression"] = entry_expression

            # 3. Füge Kommentare hinzu
            data["_comment_entry_expression"] = (
                "⚠️ Diese entry_expression wurde im CEL-Editor hinzugefügt."
            )
            data["_comment_entry_expression_created"] = datetime.now().isoformat()

            # 4. Update metadata
            if "metadata" in data:
                data["metadata"]["updated_at"] = datetime.now().isoformat()
                if "tags" in data["metadata"]:
                    if "cel-entry" not in data["metadata"]["tags"]:
                        data["metadata"]["tags"].append("cel-entry")

            # 5. Bestimme neuen Dateinamen
            if new_name:
                new_path = path.parent / new_name
            else:
                # Auto-generiere: regime.json → regime_with_entry.json
                stem = path.stem
                new_path = path.parent / f"{stem}_with_entry.json"

            # 6. Prüfe ob Datei existiert
            if new_path.exists():
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                new_path = path.parent / f"{new_path.stem}_{timestamp}.json"

            # 7. Schreibe neue Datei
            with open(new_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.info(
                f"Neue JSON mit entry_expression erstellt: {new_path.name}"
            )

            return True, f"✅ Neue Datei erstellt: {new_path.name}", new_path

        except Exception as e:
            error_msg = f"❌ Fehler beim Erstellen: {e}"
            logger.exception(error_msg)
            return False, error_msg, None

    @staticmethod
    def remove_entry_expression(
        json_path: str | Path,
        create_backup: bool = True
    ) -> tuple[bool, str]:
        """Entfernt entry_expression aus JSON.

        Args:
            json_path: Pfad zur Regime JSON
            create_backup: Erstellt Backup vor dem Entfernen

        Returns:
            (success, message)
        """
        path = Path(json_path)
        if not path.exists():
            return False, f"❌ Datei nicht gefunden: {path}"

        try:
            # 1. Lade JSON
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # 2. Prüfe ob entry_expression existiert
            if "entry_expression" not in data:
                return True, "ℹ️ Keine entry_expression vorhanden"

            # 3. Erstelle Backup
            if create_backup:
                backup_path = RegimeJsonWriter._create_backup(path)
                logger.info(f"Backup erstellt: {backup_path.name}")

            # 4. Entferne entry_expression
            removed_expr = data.pop("entry_expression")
            data.pop("_comment_entry_expression", None)
            data.pop("_comment_entry_expression_edited", None)
            data.pop("_comment_entry_expression_created", None)

            # 5. Schreibe zurück
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.info(f"entry_expression entfernt aus {path.name}")

            return True, f"✅ entry_expression entfernt\n📂 Backup: {backup_path.name}"

        except Exception as e:
            error_msg = f"❌ Fehler beim Entfernen: {e}"
            logger.exception(error_msg)
            return False, error_msg


# Convenience Functions

def quick_save(json_path: str | Path, entry_expression: str) -> bool:
    """Quick-Save mit Standard-Einstellungen."""
    success, _ = RegimeJsonWriter.write_entry_expression(
        json_path,
        entry_expression,
        create_backup=True,
        add_comments=True
    )
    return success
