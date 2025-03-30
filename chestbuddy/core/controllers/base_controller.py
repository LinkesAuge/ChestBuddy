"""
base_controller.py

Description: Base controller class with integrated SignalManager functionality
Usage:
    class MyController(BaseController):
        def __init__(self, signal_manager):
            super().__init__(signal_manager)
            self.connect_to_model(model)
"""

import logging
from typing import Optional, List, Dict, Any, Set

from PySide6.QtCore import QObject

# Set up logger
logger = logging.getLogger(__name__)


class BaseController(QObject):
    """
    Base controller class with integrated SignalManager functionality.

    Provides standardized signal connection management and cleanup.

    Attributes:
        _signal_manager: The signal manager instance for tracking connections
        _connected_views: Set of views this controller is connected to
        _connected_models: Set of models this controller is connected to
    """

    def __init__(self, signal_manager, parent=None):
        """
        Initialize the base controller with a signal manager.

        Args:
            signal_manager: SignalManager instance for connection tracking
            parent: Optional parent QObject
        """
        super().__init__(parent)
        self._signal_manager = signal_manager
        self._connected_views: Set[QObject] = set()
        self._connected_models: Set[QObject] = set()

        logger.debug(f"Initialized {self.__class__.__name__} with SignalManager")

    def connect_to_view(self, view: QObject) -> None:
        """
        Connect controller to a view's signals.

        Should be implemented by subclasses to establish view connections.

        Args:
            view: The view to connect to
        """
        self._connected_views.add(view)
        logger.debug(f"{self.__class__.__name__} connected to view: {view.__class__.__name__}")

    def connect_to_model(self, model: QObject) -> None:
        """
        Connect controller to a model's signals.

        Should be implemented by subclasses to establish model connections.

        Args:
            model: The model to connect to
        """
        self._connected_models.add(model)
        logger.debug(f"{self.__class__.__name__} connected to model: {model.__class__.__name__}")

    def disconnect_from_view(self, view: QObject) -> int:
        """
        Disconnect controller from a view's signals.

        Args:
            view: The view to disconnect from

        Returns:
            int: Number of disconnections made
        """
        # Get any connections where this controller is the receiver
        # and the view is the sender
        connections = self._signal_manager.get_connections(sender=view, receiver=self)

        # Count disconnections
        count = 0
        for sender, signal_name, receiver, slot_name in connections:
            self._signal_manager.disconnect(sender, signal_name, receiver, slot_name)
            count += 1

        # Remove from tracked views
        if view in self._connected_views:
            self._connected_views.remove(view)

        logger.debug(
            f"{self.__class__.__name__} disconnected from view: {view.__class__.__name__} ({count} connections)"
        )
        return count

    def disconnect_from_model(self, model: QObject) -> int:
        """
        Disconnect controller from a model's signals.

        Args:
            model: The model to disconnect from

        Returns:
            int: Number of disconnections made
        """
        # Get any connections where this controller is the receiver
        # and the model is the sender
        connections = self._signal_manager.get_connections(sender=model, receiver=self)

        # Count disconnections
        count = 0
        for sender, signal_name, receiver, slot_name in connections:
            self._signal_manager.disconnect(sender, signal_name, receiver, slot_name)
            count += 1

        # Remove from tracked models
        if model in self._connected_models:
            self._connected_models.remove(model)

        logger.debug(
            f"{self.__class__.__name__} disconnected from model: {model.__class__.__name__} ({count} connections)"
        )
        return count

    def disconnect_all(self) -> int:
        """
        Disconnect all controller connections.

        Returns:
            int: Number of disconnections made
        """
        count = 0

        # Disconnect from all views
        for view in list(self._connected_views):
            count += self.disconnect_from_view(view)

        # Disconnect from all models
        for model in list(self._connected_models):
            count += self.disconnect_from_model(model)

        # Disconnect any signals connected to this controller
        # This catches any connections not explicitly tracked
        receiver_count = self._signal_manager.disconnect_receiver(self)
        count += receiver_count

        logger.debug(f"{self.__class__.__name__} disconnected all connections ({count} total)")
        return count

    def __del__(self):
        """Clean up connections when controller is destroyed."""
        try:
            self.disconnect_all()
            logger.debug(f"{self.__class__.__name__} destroyed and connections cleaned up")
        except Exception as e:
            logger.error(f"Error cleaning up {self.__class__.__name__} connections: {e}")
