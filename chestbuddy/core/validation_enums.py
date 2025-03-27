"""
validation_enums.py

Description: Enumerations for validation status and related constants.
Usage:
    from chestbuddy.core.validation_enums import ValidationStatus
    status = ValidationStatus.VALID
"""

from enum import Enum, auto


class ValidationStatus(Enum):
    """
    Enum for validation status values.

    Used to indicate the validation status of data entries.

    Attributes:
        VALID: The entry is valid
        WARNING: The entry has potential issues but is not invalid
        INVALID: The entry is invalid or missing from validation lists
        INVALID_ROW: Row has an invalid entry, but this cell itself is not invalid
        NOT_VALIDATED: Entry has not been validated
    """

    VALID = auto()
    WARNING = auto()
    INVALID = auto()
    INVALID_ROW = auto()
    NOT_VALIDATED = auto()
