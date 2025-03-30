"""
Test implementation for the ServiceLocator.

This module tests the functionality of the ServiceLocator class,
which provides a centralized registry for application services.
"""

import pytest
from unittest.mock import MagicMock

from chestbuddy.utils.service_locator import ServiceLocator


class TestServiceLocator:
    """Tests for the ServiceLocator class."""

    def setup_method(self):
        """Set up test environment before each test method."""
        # Clear any previously registered services
        ServiceLocator.clear()

    def teardown_method(self):
        """Clean up after each test method."""
        # Clear registered services
        ServiceLocator.clear()

    def test_register_and_get(self):
        """Test registering and retrieving a service."""
        # Create a mock service
        mock_service = MagicMock()
        mock_service.name = "MockService"

        # Register the service
        ServiceLocator.register("test_service", mock_service)

        # Retrieve the service
        retrieved_service = ServiceLocator.get("test_service")

        # Verify it's the same service
        assert retrieved_service is mock_service
        assert retrieved_service.name == "MockService"

    def test_register_factory(self):
        """Test registering and using a factory function."""
        # Create a factory function
        factory_called = False

        def factory():
            nonlocal factory_called
            factory_called = True
            mock = MagicMock()
            mock.name = "FactoryCreatedService"
            return mock

        # Register the factory
        ServiceLocator.register_factory("factory_service", factory)

        # Verify factory hasn't been called yet
        assert not factory_called

        # Get the service
        service = ServiceLocator.get("factory_service")

        # Verify factory was called
        assert factory_called
        assert service.name == "FactoryCreatedService"

        # Get the service again
        service2 = ServiceLocator.get("factory_service")

        # Verify it's the same instance
        assert service2 is service

    def test_get_nonexistent_service(self):
        """Test getting a service that doesn't exist."""
        with pytest.raises(KeyError):
            ServiceLocator.get("nonexistent_service")

    def test_get_typed(self):
        """Test getting a service with type checking."""
        # Register services of different types
        ServiceLocator.register("string_service", "string value")
        ServiceLocator.register("int_service", 42)
        ServiceLocator.register("dict_service", {"key": "value"})

        # Get with correct type expectation
        assert ServiceLocator.get_typed("string_service", str) == "string value"
        assert ServiceLocator.get_typed("int_service", int) == 42
        assert ServiceLocator.get_typed("dict_service", dict) == {"key": "value"}

        # Get with incorrect type expectation
        with pytest.raises(TypeError):
            ServiceLocator.get_typed("string_service", int)

    def test_has_service(self):
        """Test checking if a service exists."""
        # Register a service
        ServiceLocator.register("test_service", "test")

        # Register a factory
        ServiceLocator.register_factory("factory_service", lambda: "factory")

        # Check existence
        assert ServiceLocator.has_service("test_service")
        assert ServiceLocator.has_service("factory_service")
        assert not ServiceLocator.has_service("nonexistent_service")

    def test_remove(self):
        """Test removing a service."""
        # Register services
        ServiceLocator.register("service1", "value1")
        ServiceLocator.register_factory("service2", lambda: "value2")

        # Remove services
        assert ServiceLocator.remove("service1")
        assert ServiceLocator.remove("service2")

        # Verify they're gone
        assert not ServiceLocator.has_service("service1")
        assert not ServiceLocator.has_service("service2")

        # Try to remove nonexistent service
        assert not ServiceLocator.remove("nonexistent")

    def test_clear(self):
        """Test clearing all services."""
        # Register multiple services
        ServiceLocator.register("service1", "value1")
        ServiceLocator.register("service2", "value2")
        ServiceLocator.register_factory("service3", lambda: "value3")

        # Clear all services
        ServiceLocator.clear()

        # Verify all services are gone
        assert not ServiceLocator.has_service("service1")
        assert not ServiceLocator.has_service("service2")
        assert not ServiceLocator.has_service("service3")

    def test_overwrite_service(self):
        """Test overwriting a registered service."""
        # Register a service
        ServiceLocator.register("test_service", "original_value")

        # Overwrite the service
        ServiceLocator.register("test_service", "new_value")

        # Verify the new value is returned
        assert ServiceLocator.get("test_service") == "new_value"

    def test_overwrite_factory(self):
        """Test overwriting a registered factory."""
        # Register a factory
        ServiceLocator.register_factory("test_factory", lambda: "original_value")

        # Overwrite the factory
        ServiceLocator.register_factory("test_factory", lambda: "new_value")

        # Get the service
        assert ServiceLocator.get("test_factory") == "new_value"

    def test_service_persistence(self):
        """Test that services persist between gets."""
        # Create a stateful mock
        counter = MagicMock()
        counter.value = 0

        def increment_counter():
            counter.value += 1
            return counter

        # Register factory that modifies state
        ServiceLocator.register_factory("counter", increment_counter)

        # Get the service multiple times
        c1 = ServiceLocator.get("counter")
        assert c1.value == 1  # First call increments from 0 to 1

        c2 = ServiceLocator.get("counter")
        assert c2.value == 1  # Should be same instance, still 1
        assert c1 is c2  # Should be same instance
