from __future__ import annotations

import logging
import sys
from pathlib import Path
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap, QColor
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar, QApplication, QGraphicsDropShadowEffect, QPushButton, QMessageBox

logger = logging.getLogger(__name__)

class SplashScreen(QWidget):
    """Frameless splash screen with logo and progress bar."""

    def __init__(self, icon_path: Path, title: str = "Initialisiere OrderPilot-AI..."):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setFixedSize(520, 480)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setStyleSheet("background: transparent;")

        # Outer layout for drop shadow space
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(15, 15, 15, 15)

        # Main container with white background
        self._container = QWidget()
        self._container.setObjectName("splashContainer")
        self._container.setStyleSheet(
            "QWidget#splashContainer { background-color: white; border-radius: 20px; }"
        )
        
        # Add drop shadow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setColor(Qt.GlobalColor.black)
        shadow.setOffset(0, 0)
        self._container.setGraphicsEffect(shadow)

        outer_layout.addWidget(self._container)

        # Close Button (smaller, tangential to corner radius)
        self._close_button = QPushButton("✕", self)
        self._close_button.setObjectName("closeButton")
        self._close_button.setFixedSize(30, 30)
        self._close_button.setToolTip("Anwendung beenden (Esc)")
        self._close_button.clicked.connect(self._terminate_application)
        self._close_button.setStyleSheet("""
            QPushButton {
                background-color: white;
                border: 2px solid #F29F05;
                border-radius: 15px;
                color: black;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #FFF5E6;
                border: 2px solid #D88504;
            }
            QPushButton:pressed {
                background-color: #FFE6C2;
            }
        """)
        # Position tangentially to top-right corner radius (20px radius + 15px margin + 30px button = 65px from right)
        button_offset_x = 15 + 20  # margin + radius alignment
        button_offset_y = 15 + 20  # margin + radius alignment
        self._close_button.move(self.width() - button_offset_x - self._close_button.width(), button_offset_y)

        # Add orange shadow to close button
        close_shadow = QGraphicsDropShadowEffect(self._close_button)
        close_shadow.setBlurRadius(8)
        close_shadow.setColor(QColor("#F29F05"))
        close_shadow.setOffset(0, 0)
        self._close_button.setGraphicsEffect(close_shadow)

        layout = QVBoxLayout(self._container)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(15)

        # App Name Header
        self._app_name_label = QLabel("OrderPilot-AI")
        self._app_name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._app_name_label.setStyleSheet("""
            color: #1e1e1e; 
            font-size: 32px; 
            font-weight: 800; 
            font-family: 'Segoe UI Variable Display', 'Segoe UI', 'Aptos', Arial;
            margin-bottom: 0px;
        """)
        layout.addWidget(self._app_name_label)

        # Copyright & Version
        from datetime import datetime
        current_year = datetime.now().year
        # Version from pyproject.toml is 0.1.0
        self._copyright_label = QLabel(f"© mssoftware - Maik Schmitz V0.1.0 {current_year}")
        self._copyright_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._copyright_label.setStyleSheet("""
            color: #666; 
            font-size: 11px; 
            font-weight: 400; 
            font-family: 'Segoe UI', Arial;
        """)
        layout.addWidget(self._copyright_label)

        # Spacer
        layout.addSpacing(10)

        # Logo
        self._logo_label = QLabel()
        self._logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pixmap = QPixmap(str(icon_path))
        if not pixmap.isNull():
            # Scale logo to be prominent but leave room for header
            pixmap = pixmap.scaled(180, 180, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self._logo_label.setPixmap(pixmap)
        else:
            logger.warning(f"Splash Logo not found: {icon_path}")
        layout.addWidget(self._logo_label)

        # Spacer
        layout.addSpacing(10)

        # Trading Joke Label
        self._joke_label = QLabel()
        self._joke_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._joke_label.setWordWrap(True)
        self._joke_label.setStyleSheet("""
            color: #666;
            font-size: 11px;
            font-style: italic;
            font-family: 'Segoe UI', Arial;
            padding: 5px 15px;
            background-color: #f8f8f8;
            border-radius: 8px;
            margin: 5px;
        """)
        self._load_random_joke()
        layout.addWidget(self._joke_label)

        layout.addStretch()

        # Status Label
        self._status_label = QLabel(title)
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status_label.setStyleSheet("color: #444; font-size: 13px; font-weight: 500; font-family: 'Segoe UI', Arial;")
        layout.addWidget(self._status_label)

        # Progress Bar
        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(5) # Start with a little progress
        self._progress_bar.setTextVisible(False)
        self._progress_bar.setFixedHeight(4)
        self._progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #eee;
                border: none;
                border-radius: 2px;
            }
            QProgressBar::chunk {
                background-color: #F29F05;
                border-radius: 2px;
            }
        """)
        layout.addWidget(self._progress_bar)
        
        # Center on screen
        self._center()

    def _center(self) -> None:
        screen = QApplication.primaryScreen()
        if screen:
            screen_geometry = screen.availableGeometry()
            x = (screen_geometry.width() - self.width()) // 2
            y = (screen_geometry.height() - self.height()) // 2
            self.move(x, y)

    def _load_random_joke(self) -> None:
        """Load a random trading joke into the joke label."""
        try:
            from src.core.jokes import get_random_trading_joke_simple
            joke = get_random_trading_joke_simple("de")
            # Truncate if too long for display
            if len(joke) > 150:
                joke = joke[:147] + "..."
            self._joke_label.setText(f'"{joke}"')
        except Exception as e:
            logger.warning(f"Could not load trading joke: {e}")
            self._joke_label.setText('"Buy low, sell high. Klingt einfach, oder?"')

    def set_progress(self, value: int, status: str = None) -> None:
        """Set progress bar value (0-100) and optional status text."""
        self._progress_bar.setValue(min(100, max(0, value)))
        if status:
            self._status_label.setText(status)
        # Force Qt to process events so the UI updates immediately
        QApplication.processEvents()

    def finish_and_close(self, delay_ms: int = 1500) -> None:
        """Finish progress, show terminal message, wait for delay and then close."""
        self.set_progress(100, "Bereit")
        QTimer.singleShot(delay_ms, self.close)

    def _terminate_application(self) -> None:
        """Terminate the complete OrderPilot application with confirmation dialog."""
        logger.info("User requested termination via splash screen close button")

        # Show confirmation dialog
        reply = QMessageBox.question(
            self,
            'Beenden bestätigen',
            'Möchten Sie OrderPilot-AI wirklich beenden?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            logger.info("User cancelled termination")
            return

        logger.info("User confirmed termination - shutting down")

        # Close splash screen
        self.close()

        # Get QApplication instance and quit gracefully
        app = QApplication.instance()
        if app:
            # Use QTimer to allow event loop to process pending events before quitting
            QTimer.singleShot(0, app.quit)
        else:
            # Fallback: force exit only if no QApplication instance
            sys.exit(0)

    def keyPressEvent(self, event) -> None:
        """Handle keyboard events - Escape key triggers termination."""
        if event.key() == Qt.Key.Key_Escape:
            self._terminate_application()
        else:
            super().keyPressEvent(event)
