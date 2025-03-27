"""
style.py

Description: Defines the application's color scheme and style constants.
Usage:
    Import this module to access application style definitions.
"""

from PySide6.QtGui import QColor, QPalette, QFont
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication


# Color palette definitions
class Colors:
    """Color palette for the application."""

    # Main colors
    PRIMARY = "#1A2C42"  # Dark blue
    PRIMARY_DARK = "#0F1A2A"  # Darker version of primary
    PRIMARY_LIGHT = "#263D5A"  # Lighter version of primary
    PRIMARY_HOVER = "#263D5A"  # Hover state for primary
    PRIMARY_ACTIVE = "#0F1A2A"  # Active/pressed state for primary
    SECONDARY = "#D4AF37"  # Gold
    ACCENT = "#4A90E2"  # Light blue

    # State colors
    SUCCESS = "#28A745"  # Green
    ERROR = "#DC3545"  # Red
    WARNING = "#FFC107"  # Amber/Yellow
    INFO = "#17A2B8"  # Cyan
    DISABLED = "#4A5568"  # Disabled state

    # Background colors
    BG_DARK = "#2D3748"  # Dark gray
    BG_MEDIUM = "#4A5568"  # Medium gray
    BG_LIGHT = "#718096"  # Light gray

    # CHANGED: Replace light background colors with dark theme equivalents
    # Original light theme colors:
    # BACKGROUND_PRIMARY = "#F7FAFC"  # Light background for containers
    # BACKGROUND_SECONDARY = "#F1F5F9"  # Slightly darker background for secondary elements
    # BACKGROUND_INPUT = "#FFFFFF"  # Background for input fields

    # Dark theme replacements:
    BACKGROUND_PRIMARY = "#2D3748"  # Dark background for containers (same as BG_DARK)
    BACKGROUND_SECONDARY = "#263D5A"  # Secondary background (same as PRIMARY_LIGHT)
    BACKGROUND_INPUT = "#1A2C42"  # Background for input fields (same as PRIMARY)

    # Dark theme background colors
    DARK_BG_PRIMARY = "#1A2C42"  # Main dark background (same as PRIMARY)
    DARK_BG_SECONDARY = "#263D5A"  # Secondary dark background (same as PRIMARY_LIGHT)
    DARK_BG_TERTIARY = "#0F1A2A"  # Tertiary dark background (same as PRIMARY_DARK)
    DARK_CONTENT_BG = "#2D3748"  # Content area background (same as BG_DARK)

    # Text colors
    TEXT_LIGHT = "#FFFFFF"  # White
    TEXT_MUTED = "#E2E8F0"  # Light gray
    TEXT_DISABLED = "#889EB8"  # Muted blue-gray
    TEXT_PRIMARY = "#2D3748"  # Main text color
    TEXT_PRIMARY_DARK = "#1A202C"  # Darker text for emphasis
    TEXT_SECONDARY = "#718096"  # Secondary text color
    TEXT_PLACEHOLDER = "#A0AEC0"  # Placeholder text color
    TEXT_ON_PRIMARY = "#FFFFFF"  # Text on primary colored backgrounds

    # Border colors
    BORDER = "#CBD5E0"  # Standard border
    BORDER_LIGHT = "#E2E8F0"  # Light border
    BORDER_DARK = "#2D3748"  # Dark gray border
    DARK_BORDER = "#4A5568"  # Border for dark theme elements


def get_sidebar_style():
    """
    Get the stylesheet for the sidebar navigation.

    Returns:
        str: The stylesheet for the sidebar.
    """
    return f"""
        QListWidget {{
            background-color: {Colors.PRIMARY_DARK};
            color: {Colors.TEXT_LIGHT};
            border: none;
            border-radius: 0px;
            outline: none;
        }}
        
        QListWidget::item {{
            padding: 10px;
            padding-left: 15px;
            border-bottom: 1px solid {Colors.BORDER_DARK};
        }}
        
        QListWidget::item:selected {{
            background-color: {Colors.PRIMARY};
            color: {Colors.SECONDARY};
            border-left: 3px solid {Colors.SECONDARY};
        }}
        
        QListWidget::item:hover:!selected {{
            background-color: {Colors.PRIMARY_LIGHT};
        }}
    """


def apply_application_style(app):
    """
    Apply the application style to the given QApplication instance.

    Args:
        app (QApplication): The application instance to style.
    """
    # Set fusion style as base
    app.setStyle("Fusion")

    # Create a dark palette
    palette = QPalette()

    # Set colors for different roles
    palette.setColor(QPalette.Window, QColor(Colors.BG_DARK))
    palette.setColor(QPalette.WindowText, QColor(Colors.TEXT_LIGHT))
    palette.setColor(QPalette.Base, QColor(Colors.PRIMARY))
    palette.setColor(QPalette.AlternateBase, QColor(Colors.BG_MEDIUM))
    palette.setColor(QPalette.ToolTipBase, QColor(Colors.PRIMARY))
    palette.setColor(QPalette.ToolTipText, QColor(Colors.TEXT_LIGHT))
    palette.setColor(QPalette.Text, QColor(Colors.TEXT_LIGHT))
    palette.setColor(QPalette.Button, QColor(Colors.PRIMARY))
    palette.setColor(QPalette.ButtonText, QColor(Colors.TEXT_LIGHT))
    palette.setColor(QPalette.BrightText, Qt.red)
    palette.setColor(QPalette.Link, QColor(Colors.ACCENT))
    palette.setColor(QPalette.Highlight, QColor(Colors.SECONDARY))
    palette.setColor(QPalette.HighlightedText, QColor(Colors.PRIMARY))

    # Disabled colors
    palette.setColor(QPalette.Disabled, QPalette.WindowText, QColor(Colors.BG_LIGHT))
    palette.setColor(QPalette.Disabled, QPalette.Text, QColor(Colors.BG_LIGHT))
    palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(Colors.BG_LIGHT))

    # Set the palette
    app.setPalette(palette)

    # Set application font
    font = QFont("Segoe UI", 9)  # Default font
    app.setFont(font)

    # Set stylesheet for customized widgets
    app.setStyleSheet(f"""
        /* Main window and dialogs */
        QMainWindow, QDialog {{
            background-color: {Colors.BG_DARK};
        }}
        
        /* Content views - Dark Theme (Note: We're keeping the lightContentView name to avoid breaking existing code) */
        .LightContentView, QWidget[lightContentView="true"] {{
            background-color: {Colors.DARK_CONTENT_BG};
            color: {Colors.TEXT_LIGHT};
        }}
        
        /* Container widgets for consistent background */
        .Container, QWidget[container="true"] {{
            background-color: {Colors.DARK_CONTENT_BG};
            color: {Colors.TEXT_LIGHT};
        }}
        
        /* Validation views - we explicitly set these to ensure consistency */
        ValidationTabView, ValidationListView {{
            background-color: {Colors.DARK_CONTENT_BG};
            color: {Colors.TEXT_LIGHT};
        }}
        
        /* Tab widgets */
        QTabWidget::pane {{
            border: 1px solid {Colors.DARK_BORDER};
            background-color: {Colors.PRIMARY};
        }}
        
        QTabBar::tab {{
            background-color: {Colors.BG_DARK};
            color: {Colors.TEXT_MUTED};
            padding: 8px 12px;
            border: 1px solid {Colors.DARK_BORDER};
            border-bottom: none;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
        }}
        
        QTabBar::tab:selected {{
            background-color: {Colors.PRIMARY};
            border-bottom: 2px solid {Colors.SECONDARY};
            color: {Colors.TEXT_LIGHT};
        }}
        
        QTabBar::tab:hover:!selected {{
            background-color: {Colors.BG_MEDIUM};
        }}
        
        /* Buttons */
        QPushButton {{
            background-color: {Colors.PRIMARY};
            color: {Colors.TEXT_LIGHT};
            border: 1px solid {Colors.SECONDARY};
            padding: 6px 12px;
            border-radius: 4px;
        }}
        
        QPushButton:hover {{
            background-color: {Colors.PRIMARY_LIGHT};
            border: 1px solid {Colors.SECONDARY};
        }}
        
        QPushButton:pressed {{
            background-color: {Colors.PRIMARY_DARK};
            border: 1px solid {Colors.SECONDARY};
        }}
        
        QPushButton:disabled {{
            background-color: {Colors.DISABLED};
            color: {Colors.TEXT_DISABLED};
            border: 1px solid {Colors.DISABLED};
        }}
        
        QPushButton.primary {{
            background-color: {Colors.SECONDARY};
            border: 1px solid {Colors.SECONDARY};
            color: {Colors.TEXT_LIGHT};
        }}
        
        QPushButton.primary:hover {{
            background-color: {Colors.SECONDARY};
            opacity: 0.9;
        }}
        
        QPushButton.secondary {{
            background-color: {Colors.PRIMARY_LIGHT};
            border: 1px solid {Colors.SECONDARY};
            color: {Colors.TEXT_LIGHT};
        }}
        
        QPushButton.secondary:hover {{
            background-color: {Colors.PRIMARY_HOVER};
            opacity: 0.9;
        }}
        
        QPushButton.success {{
            background-color: {Colors.SUCCESS};
            border: 1px solid {Colors.SUCCESS};
            color: white;
        }}
        
        QPushButton.success:hover {{
            background-color: {Colors.SUCCESS};
            opacity: 0.9;
        }}
        
        QPushButton.danger {{
            background-color: {Colors.ERROR};
            border: 1px solid {Colors.ERROR};
            color: white;
        }}
        
        QPushButton.danger:hover {{
            background-color: {Colors.ERROR};
            opacity: 0.9;
        }}
        
        /* Form Controls */
        QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
            background-color: {Colors.PRIMARY_LIGHT};
            color: {Colors.TEXT_LIGHT};
            border: 1px solid {Colors.DARK_BORDER};
            border-radius: 4px;
            padding: 4px 8px;
        }}
        
        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {{
            border: 1px solid {Colors.SECONDARY};
            background-color: {Colors.PRIMARY_LIGHT};
        }}
        
        QLineEdit:disabled, QTextEdit:disabled, QPlainTextEdit:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled, QComboBox:disabled {{
            background-color: {Colors.BG_MEDIUM};
            color: {Colors.TEXT_DISABLED};
        }}
        
        /* Combo box */
        QComboBox::drop-down {{
            border: none;
            padding-right: 10px;
        }}
        
        QComboBox QAbstractItemView {{
            background-color: {Colors.PRIMARY_LIGHT};
            color: {Colors.TEXT_LIGHT};
            border: 1px solid {Colors.DARK_BORDER};
            selection-background-color: {Colors.PRIMARY};
            selection-color: {Colors.SECONDARY};
        }}
        
        /* List, Table, and Tree Views */
        QTableView, QTreeView, QListView {{
            background-color: {Colors.PRIMARY_LIGHT};
            color: {Colors.TEXT_LIGHT};
            border: 1px solid {Colors.DARK_BORDER};
            gridline-color: {Colors.DARK_BORDER};
            selection-background-color: {Colors.PRIMARY};
            selection-color: {Colors.SECONDARY};
            alternate-background-color: {Colors.PRIMARY_DARK};
        }}
        
        QTableView::item, QTreeView::item, QListView::item {{
            padding: 4px;
            border-bottom: 1px solid {Colors.DARK_BORDER};
        }}
        
        QTableView::item:selected, QTreeView::item:selected, QListView::item:selected {{
            background-color: {Colors.PRIMARY};
            color: {Colors.SECONDARY};
        }}
        
        QHeaderView::section {{
            background-color: {Colors.PRIMARY_DARK};
            color: {Colors.TEXT_LIGHT};
            padding: 5px;
            border: 1px solid {Colors.DARK_BORDER};
        }}
        
        /* Splitters */
        QSplitter {{
            background-color: {Colors.DARK_CONTENT_BG};
        }}
        
        QSplitter::handle {{
            background-color: {Colors.DARK_BORDER};
        }}
        
        /* Status Bar */
        QStatusBar {{
            background-color: {Colors.PRIMARY_DARK};
            color: {Colors.TEXT_LIGHT};
        }}
        
        /* Scroll bars */
        QScrollBar:vertical {{
            background-color: {Colors.PRIMARY_DARK};
            width: 12px;
            margin: 0px;
        }}
        
        QScrollBar::handle:vertical {{
            background-color: {Colors.PRIMARY_LIGHT};
            min-height: 20px;
            border-radius: 6px;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background-color: {Colors.SECONDARY};
        }}
        
        QScrollBar:horizontal {{
            background-color: {Colors.PRIMARY_DARK};
            height: 12px;
            margin: 0px;
        }}
        
        QScrollBar::handle:horizontal {{
            background-color: {Colors.PRIMARY_LIGHT};
            min-width: 20px;
            border-radius: 6px;
        }}
        
        QScrollBar::handle:horizontal:hover {{
            background-color: {Colors.SECONDARY};
        }}
        
        /* ViewHeader from base_view.py */
        ViewHeader {{
            background-color: {Colors.PRIMARY_DARK};
            color: {Colors.TEXT_LIGHT};
            border-bottom: 1px solid {Colors.DARK_BORDER};
        }}
        
        /* Search inputs and buttons in the validation view */
        QWidget#searchContainer {{
            background-color: {Colors.PRIMARY_LIGHT};
            border-radius: 4px;
            border: 1px solid {Colors.DARK_BORDER};
        }}
        
        QLineEdit#searchInput {{
            background-color: transparent;
            border: none;
            color: {Colors.TEXT_LIGHT};
            padding-left: 5px;
        }}
        
        /* Make context menus consistent with dark theme */
        QMenu {{
            background-color: {Colors.PRIMARY};
            color: {Colors.TEXT_LIGHT};
            border: 1px solid {Colors.DARK_BORDER};
        }}
        
        QMenu::item {{
            padding: 6px 24px 6px 8px;
        }}
        
        QMenu::item:selected {{
            background-color: {Colors.PRIMARY_LIGHT};
            color: {Colors.SECONDARY};
        }}
        
        QMenu::separator {{
            height: 1px;
            background-color: {Colors.DARK_BORDER};
            margin: 4px 8px;
        }}
        
        /* Tooltips */
        QToolTip {{
            background-color: {Colors.PRIMARY};
            color: {Colors.TEXT_LIGHT};
            border: 1px solid {Colors.DARK_BORDER};
            padding: 4px;
        }}
        
        /* Labels should use light text on dark backgrounds */
        QLabel {{
            color: {Colors.TEXT_LIGHT};
        }}
        
        /* Group boxes */
        QGroupBox {{
            background-color: {Colors.DARK_CONTENT_BG};
            color: {Colors.TEXT_LIGHT};
            border: 1px solid {Colors.DARK_BORDER};
            border-radius: 4px;
            margin-top: 20px;
            padding-top: 10px;
        }}
        
        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 0 5px;
            color: {Colors.SECONDARY};
        }}
    """)
