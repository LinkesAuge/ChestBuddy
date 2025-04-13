"""
Initializes the adapters package.
"""

# Expose the adapter classes for easier importing
from .validation_adapter import ValidationAdapter
from .correction_adapter import CorrectionAdapter

__all__ = ["ValidationAdapter", "CorrectionAdapter"]
