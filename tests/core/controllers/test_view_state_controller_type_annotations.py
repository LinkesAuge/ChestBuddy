"""
Tests for type annotations in the ViewStateController.

This test file specifically checks that type annotations in the ViewStateController
use correct types that are compatible with PySide6 signals, particularly that built-in
types like dict are used instead of typing.Dict.
"""

import inspect
import re
from typing import Dict, List, Set, Optional, Any, Callable, Tuple

import pytest
from PySide6.QtCore import Signal, Slot, QObject

from chestbuddy.core.controllers.view_state_controller import ViewStateController


class TestViewStateControllerTypeAnnotations:
    """Tests for type annotations in the ViewStateController."""

    def test_signal_type_annotations(self):
        """Test that signal type annotations use built-in types."""
        # Get the ViewStateController class
        controller_class = ViewStateController

        # Check each class attribute for Signal objects
        for attr_name, attr_value in controller_class.__dict__.items():
            if isinstance(attr_value, Signal):
                # Get the docstring for the class to check documentation of signals
                docstring = controller_class.__doc__ or ""

                # Check for signal documentation with 'Dict'
                signal_doc_pattern = f"{attr_name} \\(.*?Dict\\[.*?\\).*?:"
                match = re.search(signal_doc_pattern, docstring, re.DOTALL)

                # If the signal is documented with Dict, it should use dict in code
                if match:
                    error_message = (
                        f"Signal '{attr_name}' is documented with 'Dict' type but should use 'dict'. "
                        f"Found: {match.group(0)}"
                    )
                    assert "Dict[" not in match.group(0), error_message

    def test_slot_type_annotations(self):
        """Test that slot type annotations use built-in types."""
        # Get the ViewStateController class
        controller_class = ViewStateController

        # Get all methods
        for method_name, method in inspect.getmembers(controller_class, inspect.isfunction):
            # Check if method is a slot
            is_slot = False
            for decorator in getattr(method, "__decorators__", []):
                if isinstance(decorator, Slot):
                    is_slot = True

            # If this is a slot, check its type annotations
            if is_slot:
                # Get method signature
                sig = inspect.signature(method)

                # Check parameters
                for param_name, param in sig.parameters.items():
                    if param.annotation != inspect.Parameter.empty:
                        # Convert annotation to string to check for typing.Dict
                        annotation_str = str(param.annotation)
                        error_message = (
                            f"Slot method '{method_name}' parameter '{param_name}' uses 'typing.Dict' "
                            f"but should use built-in 'dict'. Found: {annotation_str}"
                        )
                        assert "typing.Dict" not in annotation_str, error_message

    def test_attribute_type_annotations(self):
        """Test that attribute type annotations use built-in types for PySide6 signals."""
        # Get the source code of the class
        source = inspect.getsource(ViewStateController)

        # Look for attribute annotations related to signals
        signal_related_attributes = [
            "_view_availability",
            "_last_states",
            "_view_dependencies",
            "_view_prerequisites",
        ]

        for attr in signal_related_attributes:
            # Look for attribute annotated with Dict
            annotation_pattern = f"{attr}: Dict\\["
            matches = re.findall(annotation_pattern, source)

            # If attribute is annotated with Dict, it should be dict
            if matches:
                error_message = (
                    f"Attribute '{attr}' uses 'Dict' annotation but should use "
                    f"built-in 'dict' for compatibility with PySide6 signals."
                )
                assert len(matches) == 0, error_message

    def test_method_parameter_type_annotations(self):
        """Test that method parameter type annotations use built-in types for PySide6 signals."""
        # Get the ViewStateController class
        controller_class = ViewStateController

        # Define methods that might use Dict and need to be checked
        methods_to_check = [
            "set_ui_components",
            "update_view_availability",
            "_on_data_filter_applied",
        ]

        # Check each method
        for method_name in methods_to_check:
            if hasattr(controller_class, method_name):
                method = getattr(controller_class, method_name)

                # Get method signature
                sig = inspect.signature(method)

                # Check parameters
                for param_name, param in sig.parameters.items():
                    if param.annotation != inspect.Parameter.empty:
                        # Convert annotation to string to check for typing.Dict
                        annotation_str = str(param.annotation)
                        error_message = (
                            f"Method '{method_name}' parameter '{param_name}' uses 'typing.Dict' "
                            f"but should use built-in 'dict'. Found: {annotation_str}"
                        )
                        assert "typing.Dict" not in annotation_str, error_message

    def test_emitted_signal_values(self):
        """Test that emitted signal values use built-in types, not typing types."""
        # Create a data model mock
        data_model = type(
            "MockDataModel",
            (QObject,),
            {"data_changed": Signal(), "data_cleared": Signal(), "is_empty": lambda self: True},
        )()

        # Create controller
        controller = ViewStateController(data_model)

        # Create a signal catcher
        signal_values = {}

        # Connect to the view_availability_changed signal
        def catch_view_availability(values):
            signal_values["view_availability"] = values

        controller.view_availability_changed.connect(catch_view_availability)

        # Update view availability with a test dict
        controller._view_availability = {"Test": True}
        controller.view_availability_changed.emit(controller._view_availability)

        # Check that the emitted value is a built-in dict, not a typing.Dict
        assert signal_values.get("view_availability") is not None
        assert isinstance(signal_values["view_availability"], dict)
        assert not str(type(signal_values["view_availability"])).startswith("<class 'typing.Dict")

        # Check navigation history signal
        def catch_navigation_history(can_back, can_forward):
            signal_values["navigation_history"] = (can_back, can_forward)

        controller.navigation_history_changed.connect(catch_navigation_history)

        # Emit navigation history signal
        controller.navigation_history_changed.emit(True, False)

        # Check values are correct
        assert signal_values.get("navigation_history") == (True, False)
