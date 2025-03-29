"""
Test data factory for generating sample data for tests.

This module provides utilities to create test datasets of various sizes and characteristics.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta


class TestDataFactory:
    """Factory for creating test data for the ChestBuddy application."""

    # Expected column names in the ChestBuddy application
    EXPECTED_COLUMNS = ["DATE", "PLAYER", "SOURCE", "CHEST", "SCORE", "CLAN"]

    # Sample data values
    SAMPLE_PLAYERS = [
        "Player1",
        "Player2",
        "Player3",
        "Player4",
        "Player5",
        "Player6",
        "Player7",
        "Player8",
        "Player9",
        "Player10",
    ]
    SAMPLE_SOURCES = ["Source1", "Source2", "Source3", "Source4", "Source5"]
    SAMPLE_CHESTS = ["Chest1", "Chest2", "Chest3", "Chest4", "Chest5"]
    SAMPLE_CLANS = ["Clan1", "Clan2", "Clan3", "Clan4", "Clan5"]

    # Size constants
    SMALL_SIZE = 10
    MEDIUM_SIZE = 100
    LARGE_SIZE = 1000
    VERY_LARGE_SIZE = 10000

    @classmethod
    def create_empty_data(cls):
        """Create an empty DataFrame with the expected columns."""
        return pd.DataFrame(columns=cls.EXPECTED_COLUMNS)

    @classmethod
    def create_small_data(cls, with_errors=False, num_rows=10):
        """Create a small dataset (10 rows by default)."""
        return cls._create_data(num_rows, with_errors)

    @classmethod
    def create_medium_data(cls, with_errors=False):
        """Create a medium dataset (100 rows)."""
        return cls._create_data(cls.MEDIUM_SIZE, with_errors)

    @classmethod
    def create_large_data(cls, with_errors=False):
        """Create a large dataset (1000 rows)."""
        return cls._create_data(cls.LARGE_SIZE, with_errors)

    @classmethod
    def create_very_large_data(cls, with_errors=False):
        """Create a very large dataset (10,000 rows)."""
        return cls._create_data(cls.VERY_LARGE_SIZE, with_errors)

    @classmethod
    def create_custom_data(cls, num_rows, error_rate=0):
        """Create custom-sized dataset with specified error rate."""
        return cls._create_data(num_rows, error_rate > 0, error_rate)

    @classmethod
    def create_dataset_with_errors(cls, size=10, error_rate=0.1):
        """Create a dataset with errors for testing."""
        return cls._create_data(size, True, error_rate)

    @classmethod
    def _create_data(cls, num_rows, with_errors=False, error_rate=0.1):
        """Create a DataFrame with the specified number of rows."""
        # Set seed for reproducible results
        np.random.seed(42)

        # Generate base data
        start_date = datetime.now() - timedelta(days=num_rows)
        date_range = [start_date + timedelta(days=i) for i in range(num_rows)]

        data = {
            "DATE": date_range,
            "PLAYER": np.random.choice(cls.SAMPLE_PLAYERS, num_rows),
            "SOURCE": np.random.choice(cls.SAMPLE_SOURCES, num_rows),
            "CHEST": np.random.choice(cls.SAMPLE_CHESTS, num_rows),
            "SCORE": np.random.randint(1, 100, num_rows),
            "CLAN": np.random.choice(cls.SAMPLE_CLANS, num_rows),
        }

        # Create DataFrame
        df = pd.DataFrame(data)

        # Add errors if requested
        if with_errors:
            error_count = int(num_rows * error_rate)
            error_indices = np.random.choice(num_rows, error_count, replace=False)

            for idx in error_indices:
                error_type = np.random.choice(["player", "chest", "source"])
                if error_type == "player":
                    df.loc[idx, "PLAYER"] = f"Invalid{idx}"
                elif error_type == "chest":
                    df.loc[idx, "CHEST"] = f"InvalidChest{idx}"
                elif error_type == "source":
                    df.loc[idx, "SOURCE"] = f"InvalidSource{idx}"

        return df

    @classmethod
    def create_data_with_specific_errors(cls, error_types=None):
        """Create a dataset with specific error types.

        Args:
            error_types: Dictionary with keys 'player', 'chest', 'source' and values
                         indicating the number of errors to introduce for each type.

        Returns:
            DataFrame with specific errors.
        """
        if error_types is None:
            error_types = {"player": 2, "chest": 2, "source": 2}

        total_errors = sum(error_types.values())
        # Create a dataset with enough rows to hold all errors
        df = cls.create_small_data(False, 20 + total_errors)

        row_idx = 0
        for error_type, count in error_types.items():
            for i in range(count):
                if error_type == "player":
                    df.loc[row_idx, "PLAYER"] = f"InvalidPlayer{i}"
                elif error_type == "chest":
                    df.loc[row_idx, "CHEST"] = f"InvalidChest{i}"
                elif error_type == "source":
                    df.loc[row_idx, "SOURCE"] = f"InvalidSource{i}"
                row_idx += 1

        return df
