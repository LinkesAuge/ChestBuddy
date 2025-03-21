"""
ChestBuddy package initialization file.

This module initializes the ChestBuddy package and sets up logging.
"""

import logging
import os
from pathlib import Path
import sys


# Setup logging
def setup_logging():
    """Set up logging for the application."""
    log_dir = Path(__file__).parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)

    log_file = log_dir / "chestbuddy.log"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler(log_file), logging.StreamHandler(sys.stdout)],
    )

    # Set third-party loggers to WARNING level to reduce noise
    logging.getLogger("matplotlib").setLevel(logging.WARNING)
    logging.getLogger("PIL").setLevel(logging.WARNING)
    logging.getLogger("pandas").setLevel(logging.WARNING)
    logging.getLogger("PySide6").setLevel(logging.WARNING)


# Initialize logging
setup_logging()

# Import core components for easy access
from chestbuddy.core.models import BaseModel, ChestDataModel
from chestbuddy.core.services import CSVService, ValidationService, CorrectionService

# Set version
__version__ = "0.1.0"
