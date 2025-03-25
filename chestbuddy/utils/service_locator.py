"""
service_locator.py

Description: Service locator pattern implementation for accessing application-wide services.
Usage:
    from chestbuddy.utils.service_locator import ServiceLocator

    # Register a service
    ServiceLocator.register('update_manager', update_manager_instance)

    # Get a service
    update_manager = ServiceLocator.get('update_manager')
"""

from typing import Any, Dict, Optional, TypeVar, Type, cast

import logging

logger = logging.getLogger(__name__)

T = TypeVar("T")


class ServiceLocator:
    """
    Service locator pattern implementation for accessing application-wide services.

    This class provides centralized access to various services throughout the application,
    reducing direct dependencies between components.

    Implementation Notes:
        - Uses a class-level dictionary to store service instances
        - Provides type-safe access to registered services
        - Supports lazy initialization of services
    """

    # Class-level storage for services
    _services: Dict[str, Any] = {}
    _factories: Dict[str, callable] = {}

    @classmethod
    def register(cls, name: str, service: Any) -> None:
        """
        Register a service instance with the given name.

        Args:
            name: Unique identifier for the service
            service: Service instance to register
        """
        if name in cls._services:
            logger.warning(f"Service '{name}' is already registered and will be overwritten")

        cls._services[name] = service
        logger.debug(f"Service '{name}' registered: {type(service).__name__}")

    @classmethod
    def register_factory(cls, name: str, factory: callable) -> None:
        """
        Register a factory function for lazy service creation.

        Args:
            name: Unique identifier for the service
            factory: Function that creates the service when needed
        """
        if name in cls._factories:
            logger.warning(
                f"Factory for service '{name}' is already registered and will be overwritten"
            )

        cls._factories[name] = factory
        logger.debug(f"Factory for service '{name}' registered")

    @classmethod
    def get(cls, name: str) -> Any:
        """
        Get a service by name.

        Args:
            name: Name of the service to retrieve

        Returns:
            The requested service instance

        Raises:
            KeyError: If the service is not registered
        """
        # Check if service is already instantiated
        if name in cls._services:
            return cls._services[name]

        # Check if we have a factory for this service
        if name in cls._factories:
            # Create the service using its factory
            service = cls._factories[name]()
            # Register the created service
            cls._services[name] = service
            logger.debug(f"Service '{name}' created using factory: {type(service).__name__}")
            return service

        # Service not found
        raise KeyError(f"Service '{name}' not registered")

    @classmethod
    def get_typed(cls, name: str, expected_type: Type[T]) -> T:
        """
        Get a service by name with type checking.

        Args:
            name: Name of the service to retrieve
            expected_type: Expected type of the service

        Returns:
            The requested service instance, cast to the expected type

        Raises:
            KeyError: If the service is not registered
            TypeError: If the service is not of the expected type
        """
        service = cls.get(name)

        if not isinstance(service, expected_type):
            raise TypeError(f"Service '{name}' is not of expected type {expected_type.__name__}")

        return cast(expected_type, service)

    @classmethod
    def has_service(cls, name: str) -> bool:
        """
        Check if a service is registered.

        Args:
            name: Name of the service to check

        Returns:
            bool: True if the service is registered, False otherwise
        """
        return name in cls._services or name in cls._factories

    @classmethod
    def remove(cls, name: str) -> bool:
        """
        Remove a service from the registry.

        Args:
            name: Name of the service to remove

        Returns:
            bool: True if the service was removed, False if it wasn't registered
        """
        if name in cls._services:
            del cls._services[name]
            logger.debug(f"Service '{name}' removed")
            return True

        if name in cls._factories:
            del cls._factories[name]
            logger.debug(f"Factory for service '{name}' removed")
            return True

        return False

    @classmethod
    def clear(cls) -> None:
        """Clear all registered services and factories."""
        cls._services.clear()
        cls._factories.clear()
        logger.debug("All services and factories cleared")
