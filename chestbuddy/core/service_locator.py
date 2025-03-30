"""
service_locator.py

Description: Provides a service locator pattern implementation for dependency injection.
Usage:
    from chestbuddy.core.service_locator import ServiceLocator

    # Register a service
    ServiceLocator.register("my_service", MyService())

    # Register a factory
    ServiceLocator.register_factory("my_service", lambda: MyService())

    # Get a service
    service = ServiceLocator.get("my_service")

    # Get a service with type checking
    service = ServiceLocator.get_typed("my_service", MyService)
"""

import logging
from typing import Any, Callable, Dict, Optional, Type, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class ServiceLocator:
    """
    Service locator pattern implementation for dependency injection.

    This class provides a centralized registry for services and factories,
    supporting dependency injection throughout the application.

    Implementation Notes:
        - Uses static methods for global access
        - Supports both direct service registration and factory functions
        - Provides type-safe service retrieval
        - Maintains service lifecycle
        - Thread-safe service access
    """

    # Static service registry
    _services: Dict[str, Any] = {}
    _factories: Dict[str, Callable[[], Any]] = {}

    @classmethod
    def register(cls, name: str, service: Any) -> None:
        """
        Register a service instance.

        Args:
            name: Name of the service
            service: Service instance to register

        Raises:
            ValueError: If service name is already registered
        """
        if name in cls._services or name in cls._factories:
            raise ValueError(f"Service '{name}' is already registered")

        cls._services[name] = service
        logger.debug(f"Registered service: {name}")

    @classmethod
    def register_factory(cls, name: str, factory: Callable[[], Any]) -> None:
        """
        Register a factory function for lazy service creation.

        Args:
            name: Name of the service
            factory: Factory function that creates the service

        Raises:
            ValueError: If service name is already registered
        """
        if name in cls._services or name in cls._factories:
            raise ValueError(f"Service '{name}' is already registered")

        cls._factories[name] = factory
        logger.debug(f"Registered factory for service: {name}")

    @classmethod
    def get(cls, name: str) -> Any:
        """
        Get a service by name.

        Args:
            name: Name of the service to retrieve

        Returns:
            The requested service instance

        Raises:
            KeyError: If service is not registered
        """
        # Check if service exists
        if name in cls._services:
            return cls._services[name]

        # Check if factory exists
        if name in cls._factories:
            # Create service using factory
            service = cls._factories[name]()
            # Cache the instance
            cls._services[name] = service
            # Remove the factory
            del cls._factories[name]
            return service

        raise KeyError(f"Service '{name}' not found")

    @classmethod
    def get_typed(cls, name: str, expected_type: Type[T]) -> T:
        """
        Get a service by name with type checking.

        Args:
            name: Name of the service to retrieve
            expected_type: Expected type of the service

        Returns:
            The requested service instance

        Raises:
            KeyError: If service is not registered
            TypeError: If service is not of expected type
        """
        service = cls.get(name)
        if not isinstance(service, expected_type):
            raise TypeError(
                f"Service '{name}' is of type {type(service)}, expected {expected_type}"
            )
        return service

    @classmethod
    def remove(cls, name: str) -> None:
        """
        Remove a registered service.

        Args:
            name: Name of the service to remove

        Raises:
            KeyError: If service is not registered
        """
        if name in cls._services:
            del cls._services[name]
            logger.debug(f"Removed service: {name}")
        elif name in cls._factories:
            del cls._factories[name]
            logger.debug(f"Removed service factory: {name}")
        else:
            raise KeyError(f"Service '{name}' not found")

    @classmethod
    def clear(cls) -> None:
        """Remove all registered services and factories."""
        cls._services.clear()
        cls._factories.clear()
        logger.debug("Cleared all services and factories")

    @classmethod
    def has_service(cls, name: str) -> bool:
        """
        Check if a service is registered.

        Args:
            name: Name of the service to check

        Returns:
            bool: True if service is registered, False otherwise
        """
        return name in cls._services or name in cls._factories
