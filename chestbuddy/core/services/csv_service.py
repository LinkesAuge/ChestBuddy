"""
CSVService module.

This module provides the CSVService class for handling CSV file operations.
"""

import csv
import logging
import io
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import pandas as pd
from charset_normalizer import detect
from ftfy import fix_text

from chestbuddy.utils.config import ConfigManager

# Set up logger
logger = logging.getLogger(__name__)


class CSVService:
    """
    Service for handling CSV file operations.

    The CSVService is responsible for reading and writing CSV files,
    handling character encoding issues, and providing data in a format
    that can be used by the ChestDataModel.

    Implementation Notes:
        - Handles character encoding detection and normalization
        - Supports various CSV formats and dialects
        - Provides methods for reading and writing CSV files
        - Uses pandas for efficient CSV parsing
    """

    def __init__(self) -> None:
        """Initialize the CSVService."""
        self._config = ConfigManager()

    def read_csv(
        self, file_path: Union[str, Path], normalize_text: bool = True
    ) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
        """
        Read a CSV file and return its contents as a pandas DataFrame.

        Args:
            file_path: The path to the CSV file.
            normalize_text: Whether to normalize text encoding issues.

        Returns:
            A tuple containing:
                - The DataFrame containing the CSV data, or None if an error occurred.
                - An error message, or None if the operation was successful.
        """
        try:
            path = Path(file_path)

            # First try to detect the encoding
            encoding = self._detect_encoding(path)

            # Try to read the file with the detected encoding
            try:
                df = pd.read_csv(path, encoding=encoding)

                # Handle text normalization if requested
                if normalize_text:
                    df = self._normalize_dataframe_text(df)

                return df, None

            except UnicodeDecodeError:
                # If the detected encoding failed, try utf-8
                try:
                    df = pd.read_csv(path, encoding="utf-8")

                    # Handle text normalization if requested
                    if normalize_text:
                        df = self._normalize_dataframe_text(df)

                    return df, None

                except UnicodeDecodeError:
                    # If utf-8 failed, try latin-1 as a fallback
                    try:
                        df = pd.read_csv(path, encoding="latin-1")

                        # Handle text normalization if requested
                        if normalize_text:
                            df = self._normalize_dataframe_text(df)

                        return df, None

                    except Exception as e:
                        logger.error(f"Error reading CSV with latin-1 encoding: {e}")
                        return None, f"Failed to read CSV file with multiple encodings. Error: {e}"

            except Exception as e:
                logger.error(f"Error reading CSV with detected encoding: {e}")
                return None, f"Error reading CSV file. Error: {e}"

        except Exception as e:
            logger.error(f"Error in read_csv: {e}")
            return None, f"Error processing CSV file. Error: {e}"

    def write_csv(
        self, file_path: Union[str, Path], data: pd.DataFrame, encoding: str = "utf-8"
    ) -> Tuple[bool, Optional[str]]:
        """
        Write a pandas DataFrame to a CSV file.

        Args:
            file_path: The path to write the CSV file.
            data: The DataFrame to write.
            encoding: The encoding to use for the CSV file.

        Returns:
            A tuple containing:
                - True if the operation was successful, False otherwise.
                - An error message, or None if the operation was successful.
        """
        try:
            path = Path(file_path)

            # Create parent directory if it doesn't exist
            path.parent.mkdir(parents=True, exist_ok=True)

            # Write the DataFrame to CSV
            data.to_csv(path, index=False, encoding=encoding)

            return True, None

        except Exception as e:
            logger.error(f"Error writing CSV file: {e}")
            return False, f"Error writing CSV file. Error: {e}"

    def get_csv_preview(
        self, file_path: Union[str, Path], max_rows: int = 10
    ) -> Tuple[Optional[List[Dict[str, str]]], Optional[str]]:
        """
        Get a preview of a CSV file as a list of dictionaries.

        Args:
            file_path: The path to the CSV file.
            max_rows: The maximum number of rows to include in the preview.

        Returns:
            A tuple containing:
                - A list of dictionaries representing the rows, or None if an error occurred.
                - An error message, or None if the operation was successful.
        """
        df, error = self.read_csv(file_path)

        if df is None:
            return None, error

        # Get the first max_rows rows as dictionaries
        preview_rows = df.head(max_rows).to_dict("records")

        return preview_rows, None

    def _detect_encoding(self, file_path: Path) -> str:
        """
        Detect the encoding of a file.

        Args:
            file_path: The path to the file.

        Returns:
            The detected encoding, or 'utf-8' as a fallback.
        """
        try:
            # Read a sample of the file (first 10KB) to detect encoding
            with open(file_path, "rb") as f:
                raw_data = f.read(10240)  # Read first 10KB

            # Detect the encoding
            result = detect(raw_data)

            if result:
                encoding = result["encoding"]
                logger.debug(f"Detected encoding: {encoding}")
                return encoding

            return "utf-8"  # Default fallback

        except Exception as e:
            logger.error(f"Error detecting encoding: {e}")
            return "utf-8"  # Default fallback

    def _normalize_dataframe_text(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize text in a DataFrame to fix encoding issues.

        Args:
            df: The DataFrame to normalize.

        Returns:
            The normalized DataFrame.
        """
        # Create a copy to avoid modifying the original
        normalized_df = df.copy()

        # Apply text normalization to string columns
        for col in normalized_df.select_dtypes(include=["object"]).columns:
            normalized_df[col] = normalized_df[col].apply(
                lambda x: fix_text(str(x)) if isinstance(x, str) else x
            )

        return normalized_df

    def detect_csv_dialect(
        self, file_path: Union[str, Path]
    ) -> Tuple[Optional[csv.Dialect], Optional[str]]:
        """
        Detect the dialect of a CSV file.

        Args:
            file_path: The path to the CSV file.

        Returns:
            A tuple containing:
                - The detected dialect, or None if an error occurred.
                - An error message, or None if the operation was successful.
        """
        try:
            path = Path(file_path)

            # Read a sample of the file
            with open(path, "r", newline="", encoding=self._detect_encoding(path)) as f:
                sample = f.read(4096)  # Read first 4KB

            # Detect the dialect
            dialect = csv.Sniffer().sniff(sample)

            return dialect, None

        except Exception as e:
            logger.error(f"Error detecting CSV dialect: {e}")
            return None, f"Error detecting CSV format. Error: {e}"
