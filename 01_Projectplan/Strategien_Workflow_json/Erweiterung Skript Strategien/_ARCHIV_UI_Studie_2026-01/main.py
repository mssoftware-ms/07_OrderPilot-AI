#!/usr/bin/env python3
"""
CEL Editor - Main Entry Point
=============================

Interaktiver CEL-Regel-Editor mit KI-Unterstützung
für visuelle Trading-Pattern-Modellierung.

Design-Studie / UI-Prototyp
---------------------------
Diese Anwendung dient als Design-Studie und zeigt das UI-Layout
ohne vollständige Funktionalität.

Verwendung:
    python main.py                  # Standard Dark Theme
    python main.py --theme dark     # Dark Theme
    python main.py --theme light    # Dark-White Theme
    python main.py --demo           # Demo-Dialoge anzeigen

Anforderungen:
    - Python 3.10+
    - PySide6 >= 6.5.0

Autor: CEL Editor Team
Version: 2.0.0-beta
"""

import sys
import argparse
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QFontDatabase


def setup_application():
    """Anwendung initialisieren"""
    # High DPI Support - MUSS VOR QApplication-Erstellung aufgerufen werden
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)

    # Application Metadata
    app.setApplicationName("CEL Editor")
    app.setApplicationVersion("2.0.0-beta")
    app.setOrganizationName("OrderPilot-AI")
    app.setOrganizationDomain("orderpilot.ai")
    
    # Load custom fonts (if available)
    font_paths = [
        "/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-Regular.ttf",
        "C:/Windows/Fonts/jetbrainsmono-regular.ttf",
    ]
    
    for font_path in font_paths:
        if Path(font_path).exists():
            QFontDatabase.addApplicationFont(font_path)
            break
    
    # Set default font
    default_font = QFont("Segoe UI", 10)
    default_font.setStyleHint(QFont.SansSerif)
    app.setFont(default_font)
    
    return app


def parse_arguments():
    """Kommandozeilenargumente parsen"""
    parser = argparse.ArgumentParser(
        description="CEL Editor - Interaktiver Trading-Pattern-Editor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  python main.py                    Standard Dark Theme starten
  python main.py --theme light      Light Theme verwenden
  python main.py --demo             Demo-Dialoge anzeigen
        """
    )
    
    parser.add_argument(
        '--theme', '-t',
        choices=['dark', 'light'],
        default='dark',
        help='Theme auswählen (default: dark)'
    )
    
    parser.add_argument(
        '--demo', '-d',
        action='store_true',
        help='Demo-Modus: Zeigt alle Dialoge nacheinander'
    )
    
    parser.add_argument(
        '--fullscreen', '-f',
        action='store_true',
        help='Im Vollbildmodus starten'
    )
    
    return parser.parse_args()


def run_demo_dialogs(main_window):
    """Demo-Dialoge anzeigen"""
    from PySide6.QtWidgets import QMessageBox
    from PySide6.QtCore import QTimer
    
    # Info-Dialog
    QMessageBox.information(
        main_window,
        "Demo-Modus",
        "Die folgenden Dialoge werden nacheinander angezeigt:\n\n"
        "1. Export-Dialog\n"
        "2. Import-Dialog\n"
        "3. Einstellungen-Dialog\n"
        "4. Pattern-Details-Dialog\n"
        "5. Validierungs-Dialog (Erfolg)\n"
        "6. Validierungs-Dialog (Fehler)"
    )
    
    # Dialoge nacheinander anzeigen
    def show_dialogs():
        main_window.show_export_dialog()
        main_window.show_import_dialog()
        main_window.show_settings_dialog()
        main_window.show_pattern_details_dialog()
        main_window.show_validation_result_dialog(success=True)
        main_window.show_validation_result_dialog(
            success=False,
            errors=[
                "Zeile 3: Unbekannte Variable 'ema50.value'",
                "Zeile 7: Fehlende schließende Klammer",
                "Zeile 12: Ungültiger Operator '==' (verwenden Sie 'equals')"
            ]
        )
    
    QTimer.singleShot(500, show_dialogs)


def main():
    """Hauptfunktion"""
    args = parse_arguments()
    
    # Application Setup
    app = setup_application()
    
    # Import Main Window
    from main_window import CELEditorMainWindow
    
    # Create Main Window
    use_light_theme = args.theme == 'light'
    main_window = CELEditorMainWindow(use_dark_white_theme=use_light_theme)
    
    # Window Display
    if args.fullscreen:
        main_window.showFullScreen()
    else:
        main_window.show()
    
    # Demo Mode
    if args.demo:
        run_demo_dialogs(main_window)
    
    # Run Application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
