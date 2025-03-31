"""
Validation related enumeration types.

This module defines enumerations for validation statuses and modes.
"""

from enum import Enum, auto


class ValidationStatus(Enum):
    """
    Enumeration of possible validation statuses.

    Attributes:
        VALID: The data passed validation
        INVALID: The data failed validation
        WARNING: The data has potential issues but is not invalid
        INVALID_ROW: The entire row is invalid
        NOT_VALIDATED: The data has not been validated yet
        CORRECTABLE: The data is invalid but has corrections available
    """

    VALID = auto()
    INVALID = auto()
    WARNING = auto()
    INVALID_ROW = auto()
    NOT_VALIDATED = auto()
    CORRECTABLE = auto()


class ValidationMode(Enum):
    """
    Enumeration of validation modes.

    Attributes:
        STRICT: All validation rules are applied and all must pass
        PERMISSIVE: Non-critical validation rules can be ignored
        CUSTOM: User-defined validation rules are applied
    """

    STRICT = auto()
    PERMISSIVE = auto()
    CUSTOM = auto()
