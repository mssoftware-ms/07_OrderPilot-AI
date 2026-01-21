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
            background-color: {p.button_background};
            color: {p.button_text};
            border: 1px solid {p.button_border};
            padding: 0 {s.lg};
            border-radius: {s.radius_sm};
            font-weight: 500;
            min-height: {s.button_height};
            max-height: {s.button_height};
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
        
        /* Toolbar Button Style */
        QPushButton[class="toolbar-button"] {{
            margin-right: 4px;
            font-weight: 600;
        }}
        
        /* Icon Button Style */
        QPushButton[class="icon-button"] {{
            padding: 2px;
            min-width: 26px;
        }}
        
        /* Semantic Button Styles */
        QPushButton[class="success"] {{
            background-color: {p.success};
            color: {p.text_inverse};
            border: none;
        }}
        QPushButton[class="success"]:hover {{
            background-color: {p.success}; /* TODO: lighten/darken */
            border: 1px solid {p.text_primary};
        }}
        
        QPushButton[class="danger"] {{
            background-color: {p.error};
            color: {p.text_inverse};
            border: none;
        }}
        QPushButton[class="danger"]:hover {{
            border: 1px solid {p.text_primary};
        }}
        
        QPushButton[class="warning"] {{
            background-color: {p.warning};
            color: {p.background_main}; /* Warning is usually bright */
            border: none;
        }}
        QPushButton[class="warning"]:hover {{
            border: 1px solid {p.text_primary};
        }}
        
        QPushButton[class="info"] {{
            background-color: {p.info};
            color: {p.text_inverse};
            border: none;
        }}
        QPushButton[class="info"]:hover {{
            border: 1px solid {p.text_primary};
        }}

        /* Small Button Style */
        QPushButton[class="small-button"] {{
            padding: 3px 8px;
            min-height: 24px;
            max-height: 24px;
            font-size: {t.size_sm};
        }}
        
        /* --- LABELS --- */
        QLabel[class="header"] {{
            font-size: {t.size_lg};
            font-weight: bold;
            color: {p.primary};
            padding: 5px 0;
        }}
        
        QLabel[class="label-bold"] {{
            font-weight: bold;
            color: {p.text_primary};
        }}
        
        QLabel[class="status-label"] {{
            color: {p.text_secondary};
            padding: 2px;
        }}
        
        QLabel[class="info-label"] {{
            color: {p.text_secondary};
            font-size: {t.size_xs};
            padding: 4px;
        }}
        
        QLabel[class="disclaimer"] {{
            color: {p.text_secondary};
            font-size: {t.size_xs};
            padding: 4px;
            background-color: {p.background_surface};
            border-radius: {s.radius_sm};
            border: 1px solid {p.border_main};
        }}
        
        /* Status Badges */
        QLabel[class="status-badge"] {{
            padding: 6px;
            border-radius: {s.radius_sm};
            font-weight: bold;
            qproperty-alignment: AlignCenter;
        }}
        QLabel[class="status-badge"][state="success"] {{
            background-color: {p.success};
            color: {p.text_inverse};
        }}
        QLabel[class="status-badge"][state="danger"] {{
            background-color: {p.error};
            color: {p.text_inverse};
        }}
        QLabel[class="status-badge"][state="warning"] {{
            background-color: {p.warning};
            color: {p.background_main};
        }}
        QLabel[class="status-badge"][state="neutral"] {{
            background-color: {p.background_input};
            color: {p.text_secondary};
            border: 1px solid {p.border_main};
        }}

        /* --- PROGRESS BAR --- */
        QTableWidget, QTableView, QTreeWidget, QTreeView {{
            background-color: {p.background_main};
            color: {p.text_primary};
            gridline-color: {p.border_main};
            selection-background-color: {p.selection_bg};
            selection-color: {p.selection_text};
            border: 1px solid {p.border_main};
            alternate-background-color: {p.background_input};
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
        
        QTableWidget::item, QTreeWidget::item {{
            padding: {s.xs};
        }}
        
        /* --- SPLITTERS --- */
        QSplitter::handle {{
            background-color: {p.border_main};
            width: 2px; /* Vertical splitter handle width */
            height: 2px; /* Horizontal splitter handle height */
        }}
        QSplitter::handle:hover {{
            background-color: {p.primary};
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

