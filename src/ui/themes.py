"""Theme Management for OrderPilot-AI Trading Application.

Provides Dark and Light themes for the PyQt6 application.
"""


class ThemeManager:
    """Manages application themes."""

    def __init__(self):
        """Initialize theme manager."""
        self.themes = {
            "dark": self._create_dark_theme(),
            "light": self._create_light_theme()
        }

    def _create_dark_theme(self) -> str:
        """Create dark theme stylesheet."""
        return """
        /* Dark Theme - Orange/Dark */
        QMainWindow {
            background-color: #0F1115;
        }

        QWidget {
            background-color: #1A1D23;
            color: #EAECEF;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 14px;
        }

        /* Tab Widget */
        QTabWidget::pane {
            background-color: #1A1D23;
            border: 1px solid #2A2D33;
        }

        QTabBar::tab {
            background-color: #2A2D33;
            color: #EAECEF;
            padding: 8px 16px;
            margin-right: 2px;
        }

        QTabBar::tab:selected {
            background-color: #F29F05;
            color: #0F1115;
        }

        QTabBar::tab:hover {
            background-color: #3A3D43;
        }

        /* Menu Bar */
        QMenuBar {
            background-color: #1A1D23;
            color: #EAECEF;
        }

        QMenuBar::item:selected {
            background-color: #F29F05;
            color: #0F1115;
        }

        QMenu {
            background-color: #1A1D23;
            color: #EAECEF;
            border: 1px solid #2A2D33;
        }

        QMenu::item:selected {
            background-color: #F29F05;
            color: #0F1115;
        }

        /* Buttons */
        QPushButton {
            background-color: #2A2D33;
            color: #EAECEF;
            border: 1px solid #3A3D43;
            padding: 6px 12px;
            border-radius: 4px;
        }

        QPushButton:hover {
            background-color: #3A3D43;
            border-color: #F29F05;
        }

        QPushButton:pressed {
            background-color: #F29F05;
            color: #0F1115;
        }

        /* Input Fields */
        QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox, QComboBox {
            background-color: #2A2D33;
            color: #EAECEF;
            border: 1px solid #3A3D43;
            padding: 4px;
            border-radius: 4px;
        }

        QLineEdit:focus, QTextEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {
            border-color: #F29F05;
        }

        /* Tables */
        QTableWidget {
            background-color: #1A1D23;
            color: #EAECEF;
            gridline-color: #2A2D33;
            selection-background-color: #F29F05;
            selection-color: #0F1115;
        }

        QHeaderView::section {
            background-color: #2A2D33;
            color: #EAECEF;
            padding: 4px;
            border: 1px solid #3A3D43;
        }

        /* Scrollbars */
        QScrollBar:vertical {
            background-color: #1A1D23;
            width: 12px;
        }

        QScrollBar::handle:vertical {
            background-color: #3A3D43;
            border-radius: 6px;
            min-height: 20px;
        }

        QScrollBar::handle:vertical:hover {
            background-color: #F29F05;
        }

        /* Status Bar */
        QStatusBar {
            background-color: #1A1D23;
            color: #EAECEF;
        }

        /* Tool Bar */
        QToolBar {
            background-color: #1A1D23;
            border: none;
            spacing: 8px;
        }

        /* Dock Widgets */
        QDockWidget {
            color: #EAECEF;
        }

        QDockWidget::title {
            background-color: #2A2D33;
            padding: 4px;
        }

        /* Labels */
        QLabel {
            color: #EAECEF;
        }

        /* Progress Bar */
        QProgressBar {
            background-color: #2A2D33;
            border: 1px solid #3A3D43;
            border-radius: 4px;
            text-align: center;
        }

        QProgressBar::chunk {
            background-color: #F29F05;
            border-radius: 3px;
        }
        """

    def _create_light_theme(self) -> str:
        """Create light theme stylesheet."""
        return """
        /* Light Theme */
        QMainWindow {
            background-color: #F7F8FA;
        }

        QWidget {
            background-color: #FFFFFF;
            color: #0F1115;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 14px;
        }

        /* Tab Widget */
        QTabWidget::pane {
            background-color: #FFFFFF;
            border: 1px solid #E0E0E0;
        }

        QTabBar::tab {
            background-color: #F0F0F0;
            color: #0F1115;
            padding: 8px 16px;
            margin-right: 2px;
        }

        QTabBar::tab:selected {
            background-color: #E07B00;
            color: #FFFFFF;
        }

        QTabBar::tab:hover {
            background-color: #E8E8E8;
        }

        /* Menu Bar */
        QMenuBar {
            background-color: #FFFFFF;
            color: #0F1115;
        }

        QMenuBar::item:selected {
            background-color: #E07B00;
            color: #FFFFFF;
        }

        QMenu {
            background-color: #FFFFFF;
            color: #0F1115;
            border: 1px solid #E0E0E0;
        }

        QMenu::item:selected {
            background-color: #E07B00;
            color: #FFFFFF;
        }

        /* Buttons */
        QPushButton {
            background-color: #F0F0F0;
            color: #0F1115;
            border: 1px solid #D0D0D0;
            padding: 6px 12px;
            border-radius: 4px;
        }

        QPushButton:hover {
            background-color: #E8E8E8;
            border-color: #E07B00;
        }

        QPushButton:pressed {
            background-color: #E07B00;
            color: #FFFFFF;
        }

        /* Input Fields */
        QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox, QComboBox {
            background-color: #FFFFFF;
            color: #0F1115;
            border: 1px solid #D0D0D0;
            padding: 4px;
            border-radius: 4px;
        }

        QLineEdit:focus, QTextEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {
            border-color: #E07B00;
        }

        /* Tables */
        QTableWidget {
            background-color: #FFFFFF;
            color: #0F1115;
            gridline-color: #E0E0E0;
            selection-background-color: #E07B00;
            selection-color: #FFFFFF;
        }

        QHeaderView::section {
            background-color: #F0F0F0;
            color: #0F1115;
            padding: 4px;
            border: 1px solid #E0E0E0;
        }

        /* Scrollbars */
        QScrollBar:vertical {
            background-color: #F7F8FA;
            width: 12px;
        }

        QScrollBar::handle:vertical {
            background-color: #D0D0D0;
            border-radius: 6px;
            min-height: 20px;
        }

        QScrollBar::handle:vertical:hover {
            background-color: #E07B00;
        }

        /* Status Bar */
        QStatusBar {
            background-color: #F7F8FA;
            color: #0F1115;
            border-top: 1px solid #E0E0E0;
        }

        /* Tool Bar */
        QToolBar {
            background-color: #FFFFFF;
            border: none;
            spacing: 8px;
            border-bottom: 1px solid #E0E0E0;
        }

        /* Dock Widgets */
        QDockWidget {
            color: #0F1115;
        }

        QDockWidget::title {
            background-color: #F0F0F0;
            padding: 4px;
        }

        /* Labels */
        QLabel {
            color: #0F1115;
        }

        /* Progress Bar */
        QProgressBar {
            background-color: #F0F0F0;
            border: 1px solid #D0D0D0;
            border-radius: 4px;
            text-align: center;
        }

        QProgressBar::chunk {
            background-color: #E07B00;
            border-radius: 3px;
        }
        """

    def get_dark_theme(self) -> str:
        """Get dark theme stylesheet."""
        return self.themes["dark"]

    def get_light_theme(self) -> str:
        """Get light theme stylesheet."""
        return self.themes["light"]

    def get_theme(self, theme_name: str) -> str:
        """Get theme by name."""
        return self.themes.get(theme_name, self.themes["dark"])