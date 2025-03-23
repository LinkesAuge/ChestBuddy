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
    PRIMARY_LIGHTER = "#1D324A"  # Slightly lighter variant of PRIMARY
    SECONDARY = "#D4AF37"  # Gold
    ACCENT = "#4A90E2"  # Light blue

    # State colors
    SUCCESS = "#28A745"  # Green
    ERROR = "#DC3545"  # Red
    WARNING = "#FFC107"  # Amber/Yellow
    INFO = "#17A2B8"  # Cyan

    # Background colors
    BG_DARK = "#2D3748"  # Dark gray
    BG_MEDIUM = "#4A5568"  # Medium gray
    BG_LIGHT = "#718096"  # Light gray

    # Text colors
    TEXT_LIGHT = "#FFFFFF"  # White
    TEXT_MUTED = "#E2E8F0"  # Light gray

    # Border colors
    BORDER = "#4A5568"  # Medium gray


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
    app.setStyleSheet("""
        QMainWindow, QDialog {
            background-color: #2D3748;
        }
        
        QTabWidget::pane {
            border: 1px solid #4A5568;
            background-color: #1A2C42;
        }
        
        QTabBar::tab {
            background-color: #2D3748;
            color: #E2E8F0;
            padding: 8px 12px;
            border: 1px solid #4A5568;
            border-bottom: none;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
        }
        
        QTabBar::tab:selected {
            background-color: #1A2C42;
            border-bottom: 2px solid #D4AF37;
        }
        
        QTabBar::tab:hover:!selected {
            background-color: #4A5568;
        }
        
        QPushButton {
            background-color: #1A2C42;
            color: #E2E8F0;
            border: 1px solid #4A5568;
            padding: 6px 12px;
            border-radius: 4px;
        }
        
        QPushButton:hover {
            background-color: #4A90E2;
            border: 1px solid #4A90E2;
        }
        
        QPushButton:pressed {
            background-color: #3A7EC5;
        }
        
        QPushButton:disabled {
            background-color: #4A5568;
            color: #718096;
            border: 1px solid #4A5568;
        }
        
        QPushButton.primary {
            background-color: #4A90E2;
            border: 1px solid #4A90E2;
            color: white;
        }
        
        QPushButton.primary:hover {
            background-color: #3A7EC5;
        }
        
        QPushButton.secondary {
            background-color: #D4AF37;
            border: 1px solid #D4AF37;
            color: #1A2C42;
        }
        
        QPushButton.secondary:hover {
            background-color: #C4A030;
        }
        
        QPushButton.success {
            background-color: #28A745;
            border: 1px solid #28A745;
            color: white;
        }
        
        QPushButton.success:hover {
            background-color: #218838;
        }
        
        QPushButton.danger {
            background-color: #DC3545;
            border: 1px solid #DC3545;
            color: white;
        }
        
        QPushButton.danger:hover {
            background-color: #C82333;
        }
        
        QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox, QComboBox {
            background-color: #1A2C42;
            color: #E2E8F0;
            border: 1px solid #4A5568;
            border-radius: 4px;
            padding: 4px 8px;
        }
        
        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
            border: 1px solid #D4AF37;
        }
        
        QComboBox::drop-down {
            border: none;
            padding-right: 10px;
        }
        
        QComboBox::down-arrow {
            image: url(:/down-arrow.png);
        }
        
        QComboBox QAbstractItemView {
            background-color: #1A2C42;
            color: #E2E8F0;
            border: 1px solid #4A5568;
            selection-background-color: #D4AF37;
            selection-color: #1A2C42;
        }
        
        QTableView, QTreeView, QListView {
            background-color: #1A2C42;
            color: #E2E8F0;
            border: 1px solid #4A5568;
            gridline-color: #4A5568;
            selection-background-color: #D4AF37;
            selection-color: #1A2C42;
        }
        
        QHeaderView::section {
            background-color: #2D3748;
            color: #E2E8F0;
            padding: 6px;
            border: 1px solid #4A5568;
        }
        
        QScrollBar:vertical {
            border: none;
            background-color: #2D3748;
            width: 12px;
            margin: 0px;
        }
        
        QScrollBar::handle:vertical {
            background-color: #4A5568;
            min-height: 20px;
            border-radius: 6px;
        }
        
        QScrollBar::handle:vertical:hover {
            background-color: #D4AF37;
        }
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
        }
        
        QScrollBar:horizontal {
            border: none;
            background-color: #2D3748;
            height: 12px;
            margin: 0px;
        }
        
        QScrollBar::handle:horizontal {
            background-color: #4A5568;
            min-width: 20px;
            border-radius: 6px;
        }
        
        QScrollBar::handle:horizontal:hover {
            background-color: #D4AF37;
        }
        
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
            width: 0px;
        }
        
        QProgressBar {
            border: 1px solid #4A5568;
            border-radius: 4px;
            background-color: #2D3748;
            text-align: center;
            color: #E2E8F0;
        }
        
        QProgressBar::chunk {
            background-color: #D4AF37;
            width: 1px;
        }
        
        QStatusBar {
            background-color: #1A2C42;
            color: #E2E8F0;
            border-top: 1px solid #4A5568;
        }
        
        QMenuBar {
            background-color: #1A2C42;
            color: #E2E8F0;
        }
        
        QMenuBar::item {
            background: transparent;
            padding: 6px 12px;
        }
        
        QMenuBar::item:selected {
            background-color: #4A5568;
        }
        
        QMenu {
            background-color: #1A2C42;
            color: #E2E8F0;
            border: 1px solid #4A5568;
        }
        
        QMenu::item {
            padding: 6px 24px 6px 20px;
        }
        
        QMenu::item:selected {
            background-color: #4A5568;
        }
    """)
