"""
progress_bar.py

Description: A custom progress bar widget with state indicators
Usage:
    progress_bar = ProgressBar()
    progress_bar.setValue(50)
    progress_bar.setState(ProgressBar.State.SUCCESS)
"""

import logging
from enum import Enum, auto
from typing import Optional

from PySide6.QtCore import Qt, Property, Signal
from PySide6.QtGui import QPainter, QColor, QBrush, QPen, QGradient, QLinearGradient
from PySide6.QtWidgets import QProgressBar, QWidget, QStyleOptionProgressBar, QStyle

from chestbuddy.ui.resources.style import Colors

logger = logging.getLogger(__name__)


class ProgressBar(QProgressBar):
    """
    Custom progress bar with state indicators and visual enhancements.

    Attributes:
        state (State): Current state of the progress bar (NORMAL, SUCCESS, ERROR)

    Implementation Notes:
        - Uses custom painting for improved visual appearance
        - Supports different states with color indicators
        - Implements smooth transitions between states
    """

    class State(Enum):
        """State of the progress bar."""

        NORMAL = auto()
        SUCCESS = auto()
        ERROR = auto()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the progress bar.

        Args:
            parent: The parent widget
        """
        super().__init__(parent)

        # Initialize state and properties
        self._state = self.State.NORMAL
        self._border_radius = 6
        self._animation_step = 0

        # Set minimum size
        self.setMinimumHeight(20)

        # Set style
        self.setTextVisible(True)
        self.setAlignment(Qt.AlignCenter)
        self.setFormat("%p%")

        # Remove default styling
        self.setStyleSheet("""
            QProgressBar {
                background-color: #EBEEF2;
                border: none;
                border-radius: 6px;
                text-align: center;
            }
            
            QProgressBar::chunk {
                background-color: transparent;
            }
        """)

    def setState(self, state: State) -> None:
        """
        Set the state of the progress bar.

        Args:
            state: The new state (NORMAL, SUCCESS, ERROR)
        """
        if self._state != state:
            self._state = state
            self.update()  # Trigger repaint

    def state(self) -> State:
        """
        Get the current state of the progress bar.

        Returns:
            Current state
        """
        return self._state

    def paintEvent(self, event) -> None:
        """
        Custom paint event for the progress bar.

        Args:
            event: The paint event
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Get the current progress
        progress = self.value()
        total = self.maximum() - self.minimum()
        if total <= 0:
            percent = 0
        else:
            percent = progress / total

        # Determine color based on state
        if self._state == self.State.SUCCESS:
            color = QColor(Colors.SUCCESS)
        elif self._state == self.State.ERROR:
            color = QColor(Colors.ERROR)
        else:
            color = QColor(Colors.PRIMARY)

        # Draw background
        bg_color = QColor(Colors.BACKGROUND_LIGHT)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(bg_color))
        painter.drawRoundedRect(self.rect(), self._border_radius, self._border_radius)

        # Draw progress bar with gradient
        if percent > 0:
            gradient = QLinearGradient(0, 0, self.width(), 0)
            darker_color = QColor(color)
            darker_color.setAlpha(230)
            lighter_color = QColor(color)
            lighter_color.setAlpha(180)

            gradient.setColorAt(0, darker_color)
            gradient.setColorAt(1, lighter_color)

            painter.setBrush(QBrush(gradient))

            progress_width = int(self.width() * percent)
            painter.drawRoundedRect(
                0, 0, progress_width, self.height(), self._border_radius, self._border_radius
            )

        # Draw text
        text_option = QStyleOptionProgressBar()
        text_option.initFrom(self)
        text_option.minimum = self.minimum()
        text_option.maximum = self.maximum()
        text_option.progress = progress
        text_option.text = self.format().replace("%p", str(int(percent * 100)))
        text_option.textVisible = self.isTextVisible()
        text_option.rect = self.rect()

        # Use different text color based on progress
        if percent > 0.5:
            painter.setPen(QColor(Colors.TEXT_LIGHT))
        else:
            painter.setPen(QColor(Colors.TEXT_DARK))

        self.style().drawControl(QStyle.CE_ProgressBarLabel, text_option, painter, self)
