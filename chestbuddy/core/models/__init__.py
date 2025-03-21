"""
Models package initialization file.

This module imports and re-exports the model classes.
"""

from chestbuddy.core.models.base_model import BaseModel
from chestbuddy.core.models.chest_data_model import ChestDataModel

__all__ = ["BaseModel", "ChestDataModel"]
