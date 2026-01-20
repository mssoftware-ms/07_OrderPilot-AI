"""Theme Management for OrderPilot-AI Trading Application.

Provides Modern Dark themes (Orange/White) using the Design System.
"""
import logging
from .design_system import THEMES, ColorPalette, Typography, Spacing

logger = logging.getLogger(__name__)

class ThemeManager:
    """Manages application themes using the central Design System."""

    def __init__(self):
        """Initialize theme manager."""
        self.typography = Typography()
        self.spacing = Spacing()
        
    def get_theme(self, theme_name: str) -> str:
        """Get the stylesheet for the specified theme name.
        
        Args:
            theme_name: 'Dark Orange', 'Dark White', 'dark', etc.
            
        Returns:
            str: Compiled QSS stylesheet.
        """
        # Normalize: "Dark Orange" -> "dark_orange"
        key = theme_name.lower().replace(" ", "_")
        
        palette = THEMES.get(key)
        if not palette:
            # Try mapping aliases
            if key == "dark":
                palette = THEMES["dark_orange"]
            elif key == "light":
                palette = THEMES["dark_white"] # Map legacy light to Dark White for now
            else:
                logger.warning(f"Theme '{theme_name}' (key: {key}) not found, falling back to Dark Orange.")
                palette = THEMES["dark_orange"]
            
        return self._generate_stylesheet(palette)

    def _generate_stylesheet(self, p: ColorPalette) -> str:
        """Generates the QSS string from the given palette."""
        t = self.typography
        s = self.spacing
        
        qss = f"""
        /* {p.name} Theme - Auto Generated */
        
        /* --- GLOBAL --- */
        QMainWindow {{
            background-color: {p.background_main};
        }}
        
        QWidget {{
            background-color: {p.background_main};
            color: {p.text_primary};
            font-family: {t.font_family};
            font-size: {t.size_md};
            selection-background-color: {p.primary};
            selection-color: {p.text_inverse};
        }}
        
        /* --- CONTAINERS & PANELS --- */
        QDockWidget {{
            color: {p.text_primary};
            border: 1px solid {p.border_main};
        }}
        QDockWidget::title {{
            background-color: {p.background_surface};
            padding: {s.sm};
            border-bottom: 1px solid {p.border_main};
        }}
        
        QTabWidget::pane {{
            background-color: {p.background_main};
            border: 1px solid {p.border_main};
            border-top: none;
        }}
        
        QTabBar::tab {{
            background-color: {p.background_surface};
            color: {p.text_secondary};
            padding: {s.md} {s.lg};
            margin-right: {s.xs};
            border-top-left-radius: {s.radius_sm};
            border-top-right-radius: {s.radius_sm};
            border: 1px solid {p.background_surface}; 
        }}
        
        QTabBar::tab:selected {{
            background-color: {p.background_main};
            color: {p.primary};
            border: 1px solid {p.border_main};
            border-bottom: none; 
            font-weight: bold;
        }}
        
        QTabBar::tab:hover {{
            background-color: {p.background_input};
            color: {p.text_primary};
        }}

        /* --- MENUS --- */
        QMenuBar {{
            background-color: {p.background_surface};
            color: {p.text_primary};
            border-bottom: 1px solid {p.border_main};
        }}
        QMenuBar::item {{
            padding: {s.sm} {s.md};
            background: transparent;
        }}
        QMenuBar::item:selected {{
            background-color: {p.background_input};
        }}
        
        QMenu {{
            background-color: {p.background_surface};
            color: {p.text_primary};
            border: 1px solid {p.border_main};
            padding: {s.sm};
        }}
        QMenu::item {{
            padding: {s.sm} {s.xl};
            border-radius: {s.radius_sm};
        }}
        QMenu::item:selected {{
            background-color: {p.primary};
            color: {p.text_inverse};
        }}

        /* --- INPUTS --- */
        QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
            background-color: {p.background_input};
            color: {p.text_primary};
            border: 1px solid {p.border_main};
            padding: {s.sm};
            border-radius: {s.radius_sm};
        }}
        
        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QSpinBox:focus {{
            border: 1px solid {p.border_focus};
            background-color: {p.background_input};
        }}
        
        /* --- BUTTONS --- */
        QPushButton {{
            background-color: {p.background_surface};
            color: {p.text_primary};
            border: 1px solid {p.border_main};
            padding: {s.md} {s.lg};
            border-radius: {s.radius_sm};
            font-weight: 500;
        }}
        QPushButton:hover {{
            background-color: {p.background_input};
            border-color: {p.primary};
            color: {p.primary};
        }}
        QPushButton:pressed {{
            background-color: {p.primary_pressed};
            color: {p.text_inverse};
            border-color: {p.primary_pressed};
        }}
        
        /* Primary Button Style (use setProperty("class", "primary")) */
        QPushButton[class="primary"] {{
            background-color: {p.primary};
            color: {p.text_inverse};
            border: none;
        }}
        QPushButton[class="primary"]:hover {{
            background-color: {p.primary_hover};
        }}
        
        /* --- TABLES --- */
        QTableWidget, QTableView {{
            background-color: {p.background_main};
            color: {p.text_primary};
            gridline-color: {p.border_main};
            selection-background-color: {p.selection_bg};
            selection-color: {p.selection_text};
            border: 1px solid {p.border_main};
        }}
        
        QHeaderView::section {{
            background-color: {p.background_surface};
            color: {p.text_secondary};
            padding: {s.sm};
            border: none;
            border-bottom: 1px solid {p.border_main};
            border-right: 1px solid {p.border_main};
            font-weight: 600;
        }}
        
        QTableWidget::item {{
            padding: {s.xs};
        }}
        
        /* --- SCROLLBARS --- */
        QScrollBar:vertical {{
            background-color: {p.background_main};
            width: 12px;
            margin: 0px;
        }}
        QScrollBar::handle:vertical {{
            background-color: {p.border_main};
            min-height: 20px;
            border-radius: 6px;
            margin: 2px;
        }}
        QScrollBar::handle:vertical:hover {{
            background-color: {p.text_secondary};
        }}
        QScrollBar:horizontal {{
            background-color: {p.background_main};
            height: 12px;
            margin: 0px;
        }}
        QScrollBar::handle:horizontal {{
            background-color: {p.border_main};
            min-width: 20px;
            border-radius: 6px;
            margin: 2px;
        }}

        /* --- STATUS BAR --- */
        QStatusBar {{
            background-color: {p.background_surface};
            color: {p.text_secondary};
            border-top: 1px solid {p.border_main};
        }}
        
        /* --- PROGRESS BAR --- */
        QProgressBar {{
            background-color: {p.background_input};
            border: 1px solid {p.border_main};
            border-radius: {s.radius_sm};
            text-align: center;
            color: {p.text_primary};
        }}
        QProgressBar::chunk {{
            background-color: {p.primary};
            border-radius: {s.radius_xs if hasattr(s, 'radius_xs') else '2px'};
        }}
        
        /* --- TOOLTIPS --- */
        QToolTip {{
            background-color: {p.background_surface};
            color: {p.text_primary};
            border: 1px solid {p.border_main};
            padding: {s.sm};
        }}
        """
        return qss

    # Legacy method support
    def get_dark_theme(self) -> str:
        return self.get_theme("dark_orange")

    def get_light_theme(self) -> str:
        # We don't have a light theme yet, map to white-accent dark or orange
        return self.get_theme("dark_white") 

