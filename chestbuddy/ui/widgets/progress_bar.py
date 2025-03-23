"""
progress_bar.py

Description: Custom progress bar widget with styling and state indicators
Usage:
    progress_bar = ProgressBar()
    progress_bar.setValue(50)
    progress_bar.setStatus("Processing...")
    progress_bar.setState(ProgressBar.State.SUCCESS)
"""

from typing import Optional
from enum import Enum

from PySide6.QtCore import Qt, Signal, Property, QRectF
from PySide6.QtGui import QPainter, QColor, QBrush, QPen, QPaintEvent, QLinearGradient
from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel

from chestbuddy.ui.resources.style import Colors


class ProgressBar(QWidget):
    """
    Custom progress bar with styling and state indicators.
    
    Attributes:
        value: Current progress value (0-100)
        maximum: Maximum value for calculating percentage
        status: Text status displayed below the progress bar
        
    Signals:
        valueChanged: Emitted when the progress value changes
        statusChanged: Emitted when the status text changes
        stateChanged: Emitted when the progress bar state changes
        
    Implementation Notes:
        - Custom drawn progress bar with rounded corners
        - Built-in percentage indicator
        - Color changes based on state (normal, success, error)
        - Optional status text display
    """
    
    # Signal definitions
    valueChanged = Signal(int)
    statusChanged = Signal(str)
    stateChanged = Signal(int)
    
    # State enum for progress bar
    class State(Enum):
        NORMAL = 0
        SUCCESS = 1
        ERROR = 2
    
    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize the progress bar.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        self._value = 0
        self._maximum = 100
        self._status = ""
        self._state = self.State.NORMAL
        
        # Set up the UI
        self._setup_ui()
        
    def _setup_ui(self):
        """Set up the user interface components."""
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # Progress percentage label
        self._percentage_label = QLabel("0%")
        self._percentage_label.setAlignment(Qt.AlignCenter)
        self._percentage_label.setStyleSheet(f"color: {Colors.TEXT_LIGHT}; font-weight: bold;")
        
        # Progress bar container (this will be custom painted)
        self._progress_container = QWidget()
        self._progress_container.setMinimumHeight(24)
        self._progress_container.setMaximumHeight(24)
        self._progress_container.paintEvent = self._paint_progress
        
        # Status label for displaying text status
        self._status_label = QLabel(self._status)
        self._status_label.setAlignment(Qt.AlignCenter)
        self._status_label.setStyleSheet(f"color: {Colors.TEXT_MUTED};")
        self._status_label.setVisible(False)  # Hide until we have a status
        
        # Add widgets to layout
        layout.addWidget(self._percentage_label)
        layout.addWidget(self._progress_container)
        layout.addWidget(self._status_label)
        
        # Set default size
        self.setMinimumWidth(300)
        
    def _paint_progress(self, event: QPaintEvent):
        """
        Custom paint method for the progress bar.
        
        Args:
            event: Paint event
        """
        painter = QPainter(self._progress_container)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Get the color for the current state
        if self._state == self.State.SUCCESS:
            color = QColor(Colors.SUCCESS)
        elif self._state == self.State.ERROR:
            color = QColor(Colors.ERROR)
        else:
            color = QColor(Colors.ACCENT)
        
        # Calculate progress width
        width = self._progress_container.width()
        height = self._progress_container.height()
        progress_width = (self._value / self._maximum) * width
        
        # Draw background (rounded rectangle)
        bg_rect = QRectF(0, 0, width, height)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(Colors.BG_MEDIUM)))
        painter.drawRoundedRect(bg_rect, 12, 12)
        
        # Draw progress (rounded rectangle with gradient)
        if progress_width > 0:
            progress_rect = QRectF(0, 0, progress_width, height)
            
            # Create gradient
            gradient = QLinearGradient(0, 0, 0, height)
            gradient.setColorAt(0, color.lighter(120))
            gradient.setColorAt(1, color)
            
            painter.setBrush(QBrush(gradient))
            
            # For very small progress values, adjust the corners to look nice
            if progress_width <= 24:
                painter.drawRoundedRect(progress_rect, 12, 12)
            else:
                # Create a path for left-rounded rectangle
                painter.drawRoundedRect(progress_rect, 12, 12)
        
        painter.end()
    
    def setValue(self, value: int):
        """
        Set the current progress value.
        
        Args:
            value: Progress value (0-100)
        """
        # Clamp value between 0 and maximum
        value = max(0, min(value, self._maximum))
        
        if self._value != value:
            self._value = value
            
            # Update percentage label
            percentage = int((value / self._maximum) * 100)
            self._percentage_label.setText(f"{percentage}%")
            
            # Repaint the progress bar
            self._progress_container.update()
            
            # Emit signal
            self.valueChanged.emit(value)
    
    def setMaximum(self, maximum: int):
        """
        Set the maximum progress value.
        
        Args:
            maximum: Maximum value
        """
        if maximum > 0 and self._maximum != maximum:
            self._maximum = maximum
            # Update display in case percentage changed
            self.setValue(self._value)
    
    def setStatus(self, status: str):
        """
        Set the status text.
        
        Args:
            status: Status text to display
        """
        if self._status != status:
            self._status = status
            self._status_label.setText(status)
            
            # Show/hide status label based on content
            self._status_label.setVisible(bool(status))
            
            # Emit signal
            self.statusChanged.emit(status)
    
    def setState(self, state: State):
        """
        Set the visual state of the progress bar.
        
        Args:
            state: The visual state (NORMAL, SUCCESS, ERROR)
        """
        if self._state != state:
            self._state = state
            
            # Update the progress bar
            self._progress_container.update()
            
            # Emit signal
            self.stateChanged.emit(state.value)
    
    # Property getters
    def value(self) -> int:
        """Get the current progress value."""
        return self._value
    
    def maximum(self) -> int:
        """Get the maximum progress value."""
        return self._maximum
    
    def status(self) -> str:
        """Get the current status text."""
        return self._status
    
    def state(self) -> State:
        """Get the current visual state."""
        return self._state
    
    # Define Qt properties
    progress = Property(int, value, setValue)
    maximum = Property(int, maximum, setMaximum)
    status = Property(str, status, setStatus)
