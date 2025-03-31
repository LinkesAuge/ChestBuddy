"""
Tests for the ValidationStatus enum.

Verifies that the ValidationStatus enum includes all required states.
"""

import pytest
from chestbuddy.core.enums.validation_enums import ValidationStatus


def test_validation_status_has_correctable():
    """Test that ValidationStatus enum has CORRECTABLE state."""
    assert hasattr(ValidationStatus, "CORRECTABLE"), (
        "ValidationStatus should have CORRECTABLE state"
    )

    # Check that the CORRECTABLE state is distinct from other states
    assert ValidationStatus.CORRECTABLE != ValidationStatus.VALID
    assert ValidationStatus.CORRECTABLE != ValidationStatus.INVALID
    assert ValidationStatus.CORRECTABLE != ValidationStatus.WARNING
    assert ValidationStatus.CORRECTABLE != ValidationStatus.INVALID_ROW
    assert ValidationStatus.CORRECTABLE != ValidationStatus.NOT_VALIDATED


def test_validation_status_values():
    """Test all ValidationStatus values are present and distinct."""
    # Check all states exist
    expected_states = ["VALID", "INVALID", "WARNING", "INVALID_ROW", "NOT_VALIDATED", "CORRECTABLE"]

    for state in expected_states:
        assert hasattr(ValidationStatus, state), f"ValidationStatus should have {state} state"

    # Check all states have unique values
    seen_values = set()
    for state in expected_states:
        value = getattr(ValidationStatus, state)
        assert value not in seen_values, f"Value for {state} should be unique"
        seen_values.add(value)
