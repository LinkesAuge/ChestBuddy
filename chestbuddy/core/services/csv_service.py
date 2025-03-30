"""
CSVService module.

This module provides the CSVService class for handling CSV file operations.
"""

import csv
import logging
import io
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Any, Callable

import pandas as pd
import chardet
from charset_normalizer import detect
from ftfy import fix_text

from chestbuddy.utils.config import ConfigManager
from chestbuddy.utils.background_processing import BackgroundWorker, BackgroundTask

# Set up logger
logger = logging.getLogger(__name__)

# List of encodings to try when auto-detection fails
FALLBACK_ENCODINGS = [
    "utf-8",
    "utf-8-sig",  # UTF-8 with and without BOM
    "shift_jis",
    "cp932",  # Japanese (try these first for Japanese content)
    "latin-1",
    "iso-8859-1",  # Western European
    "cp1252",
    "windows-1252",  # Windows Western European
    "euc_jp",
    "euc-jp",  # Japanese
    "iso-2022-jp",  # Japanese
    "gbk",
    "gb2312",  # Chinese
    "euc-kr",  # Korean
    "iso-8859-15",  # Western European with Euro
]

# BOM markers
BOM_MARKERS = {
    b"\xef\xbb\xbf": "utf-8-sig",  # UTF-8 with BOM
    b"\xfe\xff": "utf-16be",  # UTF-16 Big Endian
    b"\xff\xfe": "utf-16le",  # UTF-16 Little Endian
    b"\x00\x00\xfe\xff": "utf-32be",  # UTF-32 Big Endian
    b"\xff\xfe\x00\x00": "utf-32le",  # UTF-32 Little Endian
}

# Japanese character sets for detection
JAPANESE_CHARS = {
    "hiragana": range(0x3040, 0x309F),
    "katakana": range(0x30A0, 0x30FF),
    "kanji": range(0x4E00, 0x9FBF),
}


class CSVReadTask(BackgroundTask):
    """
    Background task for reading CSV files.

    This task wraps the read_csv_chunked method of CSVService to enable
    reading CSV files in a background thread with progress reporting.
    """

    def __init__(
        self,
        file_path: Union[str, Path],
        chunk_size: int = 1000,
        encoding: Optional[str] = None,
        normalize_text: bool = True,
        robust_mode: bool = False,
    ) -> None:
        """
        Initialize the CSV read task.

        Args:
            file_path: Path to the CSV file
            chunk_size: Number of rows to read in each chunk
            encoding: Optional encoding to use (auto-detected if None)
            normalize_text: Whether to normalize text in the CSV
            robust_mode: Whether to use robust mode for reading
        """
        super().__init__()
        self.file_path = Path(file_path)
        self.chunk_size = chunk_size
        self.encoding = encoding
        self.normalize_text = normalize_text
        self.robust_mode = robust_mode

    def run(self) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
        """
        Run the CSV read task.

        Returns:
            A tuple containing the DataFrame and error message (if any)
        """
        try:
            if not self.file_path.exists():
                return None, f"File not found: {self.file_path}"

            # Create a CSV service instance
            csv_service = CSVService()

            # Define a progress callback that emits our progress signal
            def progress_callback(current: int, total: int) -> None:
                self.progress.emit(current, total)

                # Check for cancellation
                if self.is_cancelled:
                    raise InterruptedError("CSV read operation cancelled")

            # Read the CSV file with chunking (using the synchronous version to avoid recursion)
            return csv_service._read_csv_chunked_internal(
                file_path=self.file_path,
                chunk_size=self.chunk_size,
                encoding=self.encoding,
                normalize_text=self.normalize_text,
                robust_mode=self.robust_mode,
                progress_callback=progress_callback,
            )

        except InterruptedError:
            # Task was cancelled
            logger.info(f"CSV read task cancelled for file: {self.file_path}")
            return None, "Operation cancelled"

        except Exception as e:
            # Log and return the error
            logger.error(f"Error in CSV read task: {e}")
            return None, f"Error reading CSV file: {str(e)}"


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
        self,
        file_path: Union[str, Path],
        encoding: Optional[str] = None,
        normalize_text: bool = True,
        robust_mode: bool = False,
    ) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
        """
        Read a CSV file and return its contents as a pandas DataFrame.

        Args:
            file_path: The path to the CSV file.
            encoding: Optional encoding to use. If None, auto-detection is used.
            normalize_text: Whether to normalize text encoding issues.
            robust_mode: Whether to use robust mode for handling severely corrupted files.

        Returns:
            A tuple containing:
                - The DataFrame containing the CSV data, or None if an error occurred.
                - An error message, or None if the operation was successful.
        """
        logger.info(f"Reading CSV file: {file_path}")

        try:
            path = Path(file_path)
            encoding_used = None
            error_details = []

            # If we're in robust mode, set a flag to include a warning message
            # even if reading succeeds
            robust_warning = (
                "Note: Robust mode was used for reading this file. Some corrupted lines may have been skipped."
                if robust_mode
                else None
            )

            # First check if this might be a Japanese file
            if self._might_be_japanese_file(path) and not encoding:
                logger.debug(
                    "File appears to contain Japanese text, prioritizing Japanese encodings"
                )
                for jp_encoding in ["shift_jis", "cp932", "euc_jp", "iso-2022-jp"]:
                    try:
                        logger.debug(f"Trying Japanese encoding: {jp_encoding}")
                        df = pd.read_csv(path, encoding=jp_encoding)
                        encoding_used = jp_encoding

                        # Verify the content looks correct
                        if self._verify_japanese_content(df):
                            logger.info(
                                f"Successfully read Japanese CSV with encoding: {jp_encoding}"
                            )

                            # Handle text normalization if requested
                            if normalize_text:
                                df = self._normalize_dataframe_text(df)

                            return df, robust_warning
                    except Exception as e:
                        error_msg = f"Failed to read Japanese CSV with encoding {jp_encoding}: {e}"
                        logger.debug(error_msg)
                        error_details.append(error_msg)

            # Use the specified encoding if provided
            if encoding:
                try:
                    logger.debug(f"Using user-specified encoding: {encoding}")
                    df = pd.read_csv(path, encoding=encoding)
                    encoding_used = encoding

                    # Handle text normalization if requested
                    if normalize_text:
                        df = self._normalize_dataframe_text(df)

                    return df, robust_warning

                except Exception as e:
                    error_msg = f"Failed to read CSV with specified encoding {encoding}: {e}"
                    logger.warning(error_msg)
                    error_details.append(error_msg)
                    # Don't return here, try auto-detection instead

            # Try to detect BOM first (takes precedence over other detection methods)
            bom_encoding = self._detect_bom(path)
            if bom_encoding:
                try:
                    logger.debug(f"Detected BOM, using encoding: {bom_encoding}")
                    df = pd.read_csv(path, encoding=bom_encoding)
                    encoding_used = bom_encoding

                    # Handle text normalization if requested
                    if normalize_text:
                        df = self._normalize_dataframe_text(df)

                    return df, robust_warning

                except Exception as e:
                    error_msg = f"Failed to read CSV with BOM-detected encoding {bom_encoding}: {e}"
                    logger.warning(error_msg)
                    error_details.append(error_msg)
                    # Continue with other detection methods

            # Try with auto-detected encoding
            detected_encoding, confidence = self._detect_encoding(path)
            if detected_encoding:
                try:
                    logger.debug(f"Using auto-detected encoding: {detected_encoding}")
                    df = pd.read_csv(path, encoding=detected_encoding)
                    encoding_used = detected_encoding

                    # Handle text normalization if requested
                    if normalize_text:
                        df = self._normalize_dataframe_text(df)

                    return df, robust_warning

                except Exception as e:
                    error_msg = (
                        f"Failed to read CSV with detected encoding {detected_encoding}: {e}"
                    )
                    logger.warning(error_msg)
                    error_details.append(error_msg)
                    # Continue with fallback encodings

            # Try each fallback encoding
            for fallback_encoding in FALLBACK_ENCODINGS:
                # Skip if we've already tried this encoding
                if (
                    fallback_encoding == detected_encoding
                    or fallback_encoding == bom_encoding
                    or fallback_encoding == encoding
                ):
                    continue

                try:
                    logger.debug(f"Trying fallback encoding: {fallback_encoding}")
                    df = pd.read_csv(path, encoding=fallback_encoding)
                    encoding_used = fallback_encoding

                    # Special case for Japanese encodings - verify content
                    if fallback_encoding in ["shift_jis", "cp932", "euc_jp", "iso-2022-jp"]:
                        if not self._verify_japanese_content(df):
                            logger.debug(
                                f"Data read with {fallback_encoding} doesn't appear to be valid Japanese"
                            )
                            continue

                    # Handle text normalization if requested
                    if normalize_text:
                        df = self._normalize_dataframe_text(df)

                    logger.info(
                        f"Successfully read CSV with fallback encoding: {fallback_encoding}"
                    )
                    return df, robust_warning

                except Exception as e:
                    error_msg = (
                        f"Failed to read CSV with fallback encoding {fallback_encoding}: {e}"
                    )
                    logger.debug(error_msg)  # Use debug level here to avoid log spam
                    error_details.append(error_msg)
                    # Continue with next fallback encoding

            # If we're in robust mode, try to recover as much as possible
            if robust_mode:
                try:
                    logger.warning("Attempting robust CSV recovery...")
                    # Try with error_bad_lines=False (pandas <1.3) or on_bad_lines='skip' (pandas >=1.3)
                    try:
                        # For pandas >=1.3
                        df = pd.read_csv(path, encoding="latin-1", on_bad_lines="skip")
                    except TypeError:
                        # For pandas <1.3
                        df = pd.read_csv(path, encoding="latin-1", error_bad_lines=False)

                    logger.warning("Recovered partial data with robust mode")

                    if normalize_text:
                        df = self._normalize_dataframe_text(df)

                    # Always include warning about using robust mode
                    return (
                        df,
                        "Note: Some corrupted lines were skipped during import. Data may be incomplete.",
                    )

                except Exception as e:
                    error_msg = f"Failed to recover CSV even with robust mode: {e}"
                    logger.error(error_msg)
                    error_details.append(error_msg)

            # If we reach here, all attempts have failed
            err_summary = (
                "\n".join(error_details[:3]) + f"\n... and {len(error_details) - 3} more errors"
                if len(error_details) > 3
                else "\n".join(error_details)
            )
            logger.error(f"All encoding attempts failed for {path}")
            return None, f"Failed to read CSV file with multiple encodings. Details: {err_summary}"

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
        self, file_path: Union[str, Path], max_rows: int = 10, encoding: Optional[str] = None
    ) -> Tuple[Optional[List[Dict[str, Any]]], Optional[str]]:
        """
        Get a preview of a CSV file as a list of dictionaries.

        Args:
            file_path: The path to the CSV file.
            max_rows: The maximum number of rows to include in the preview.
            encoding: Optional encoding to use for reading the file.

        Returns:
            A tuple containing:
                - A list of dictionaries representing the rows, or None if an error occurred.
                - An error message, or None if the operation was successful.
        """
        df, error = self.read_csv(file_path, encoding=encoding)

        if df is None:
            return None, error

        # Get the first max_rows rows as dictionaries
        preview_rows = df.head(max_rows).to_dict("records")

        return preview_rows, None

    def get_supported_encodings(self) -> List[str]:
        """
        Get a list of supported encodings.

        Returns:
            A list of encoding names that can be used with read_csv and write_csv.
        """
        return FALLBACK_ENCODINGS.copy()

    def _detect_encoding(self, file_path: Path) -> Tuple[Optional[str], float]:
        """
        Detect the encoding of a file using multiple methods.

        Args:
            file_path: The path to the file.

        Returns:
            A tuple containing:
                - The detected encoding, or None if detection failed.
                - The confidence level (0.0 to 1.0)
        """
        try:
            # First check for BOM
            bom_encoding = self._detect_bom(file_path)
            if bom_encoding:
                logger.debug(f"BOM detected, encoding: {bom_encoding}")
                return bom_encoding, 1.0  # Full confidence for BOM detection

            # Read a sample of the file (first 10KB) to detect encoding
            with open(file_path, "rb") as f:
                raw_data = f.read(10240)  # Read first 10KB

            # Check for Japanese content first
            if self._contains_japanese_bytes(raw_data):
                logger.debug(
                    "File appears to contain Japanese text, will try Japanese encodings first"
                )
                # Try Japanese encodings directly
                for encoding in ["shift_jis", "cp932", "euc_jp", "iso-2022-jp"]:
                    try:
                        decoded = raw_data.decode(encoding)
                        if len(decoded) > 0 and not decoded.isascii():
                            logger.debug(f"Successfully decoded with Japanese encoding: {encoding}")
                            return encoding, 0.9  # High confidence for successful decoding

                    except UnicodeDecodeError:
                        continue

            # Try charset_normalizer first (better for international)
            result = detect(raw_data)
            if result and result.get("encoding"):
                confidence = result.get("confidence", 0)
                encoding = result["encoding"]
                logger.debug(
                    f"charset_normalizer detected encoding: {encoding} with confidence: {confidence}"
                )

                # Only trust high confidence results
                if confidence > 0.8:
                    return encoding, confidence

            # Try chardet as backup
            detection = chardet.detect(raw_data)
            if detection and detection.get("encoding"):
                confidence = detection.get("confidence", 0)
                encoding = detection["encoding"]
                logger.debug(f"chardet detected encoding: {encoding} with confidence: {confidence}")

                # Only trust high confidence results
                if confidence > 0.7:
                    return encoding, confidence

            # If we couldn't detect with high confidence, return None
            # and let the fallback mechanism handle it
            logger.warning("Encoding detection had low confidence, will use fallbacks")
            return None, 0.0

        except Exception as e:
            logger.error(f"Error detecting encoding: {e}")
            return None, 0.0

    def _detect_bom(self, file_path: Path) -> Optional[str]:
        """
        Detect Byte Order Mark (BOM) in a file and return the corresponding encoding.

        Args:
            file_path: The path to the file.

        Returns:
            The encoding corresponding to the BOM, or None if no BOM was detected.
        """
        try:
            with open(file_path, "rb") as f:
                raw_data = f.read(4)  # Read the first 4 bytes

            # Check for each known BOM
            for bom, encoding in BOM_MARKERS.items():
                if raw_data.startswith(bom):
                    logger.debug(f"BOM detected: {bom}, encoding: {encoding}")
                    return encoding

            return None

        except Exception as e:
            logger.error(f"Error detecting BOM: {e}")
            return None

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
                lambda x: self._normalize_text(x) if isinstance(x, str) else x
            )

        return normalized_df

    def _normalize_text(self, text: str) -> str:
        """
        Normalize a text string to fix encoding issues.

        Uses ftfy with additional handling for specific cases.

        Args:
            text: The text to normalize.

        Returns:
            The normalized text.
        """
        try:
            # Use ftfy for general text fixing
            fixed = fix_text(text)

            # Special handling for common issues not fully handled by ftfy
            # Replace common corruption patterns
            replacements = {
                # Add specific replacements if needed
                "": "",  # Replace the unicode replacement character
                "\ufffd": "",  # Another form of the replacement character
            }

            for char, replacement in replacements.items():
                fixed = fixed.replace(char, replacement)

            return fixed.strip()

        except Exception as e:
            logger.warning(f"Error normalizing text: {e}. Original text: {text[:20]}...")
            return text  # Return original if normalization fails

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

            # Detect encoding first
            encoding, confidence = self._detect_encoding(path)
            if not encoding:
                encoding = "utf-8"  # Default to UTF-8 if detection fails

            # Read a sample of the file
            with open(path, "r", newline="", encoding=encoding) as f:
                sample = f.read(4096)  # Read first 4KB

            # Detect the dialect
            dialect = csv.Sniffer().sniff(sample)

            return dialect, None

        except Exception as e:
            logger.error(f"Error detecting CSV dialect: {e}")
            return None, f"Error detecting CSV format. Error: {e}"

    def _might_be_japanese_file(self, file_path: Path) -> bool:
        """
        Check if a file might contain Japanese text.

        Args:
            file_path: The path to the file.

        Returns:
            True if the file likely contains Japanese text, False otherwise.
        """
        try:
            with open(file_path, "rb") as f:
                raw_data = f.read(8192)  # Read first 8KB

            return self._contains_japanese_bytes(raw_data)

        except Exception as e:
            logger.error(f"Error checking for Japanese content: {e}")
            return False

    def _contains_japanese_bytes(self, data: bytes) -> bool:
        """
        Check if byte data contains patterns typical for Japanese encodings.

        Args:
            data: The raw byte data to check.

        Returns:
            True if the data likely contains Japanese text, False otherwise.
        """
        # Shift-JIS specific byte patterns
        # These are common byte sequences in Shift-JIS encoded Japanese text
        common_sequences = [
            b"\x82\xa0",
            b"\x82\xa2",
            b"\x82\xa4",  # Hiragana あいう
            b"\x83\x40",
            b"\x83\x41",
            b"\x83\x42",  # Katakana アイウ
            b"\x93\xfa",
            b"\x96\x7b",  # Common Kanji 日本
        ]

        for seq in common_sequences:
            if seq in data:
                return True

        return False

    def _verify_japanese_content(self, df: pd.DataFrame) -> bool:
        """
        Verify that DataFrame content contains valid Japanese characters.

        Args:
            df: The DataFrame to check.

        Returns:
            True if the DataFrame contains valid Japanese text, False otherwise.
        """
        try:
            # Check string columns for Japanese characters
            for col in df.select_dtypes(include=["object"]).columns:
                for value in df[col].dropna():
                    if isinstance(value, str):
                        # Check for common Japanese Unicode ranges
                        for char in value:
                            code = ord(char)
                            # Check if in Japanese Unicode ranges
                            if any(code in char_range for char_range in JAPANESE_CHARS.values()):
                                return True

                        # Check for specific Japanese characters
                        if (
                            "東京" in value
                            or "大阪" in value
                            or "プレイヤー" in value
                            or "選手" in value
                        ):
                            return True

            return False

        except Exception as e:
            logger.error(f"Error verifying Japanese content: {e}")
            return False

    def _read_csv_chunked_internal(
        self,
        file_path: Union[str, Path],
        chunk_size: int = 1000,
        encoding: Optional[str] = None,
        normalize_text: bool = True,
        robust_mode: bool = False,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
        """
        Internal implementation to read a CSV file in chunks and return the combined DataFrame.

        This is the synchronous implementation that does the actual work.

        Args:
            file_path: Path to the CSV file
            chunk_size: Number of rows to read in each chunk
            encoding: Optional encoding to use (auto-detected if None)
            normalize_text: Whether to normalize text in the CSV
            robust_mode: Whether to use robust mode for reading
            progress_callback: Optional callback function for progress reporting

        Returns:
            A tuple containing (DataFrame, error_message)
            On success, DataFrame contains the data and error_message is None
            On failure, DataFrame is None and error_message contains the error
        """
        # Convert file path to Path object
        file_path = Path(file_path)

        # Check if file exists
        if not file_path.exists():
            return None, f"File not found: {file_path}"

        try:
            # Detect encoding if not provided
            if encoding is None:
                encoding, confidence = self._detect_encoding(file_path)
                logger.info(f"Detected encoding: {encoding} with confidence {confidence:.2f}")

                if not encoding:
                    encoding = "utf-8"  # Default to UTF-8 if detection fails

            # Get file size for progress tracking
            file_size = file_path.stat().st_size

            # Initialize variables
            chunks = []
            total_rows = 0
            processed_bytes = 0
            rows_processed = 0

            # Prepare keyword arguments for read_csv
            kwargs = {
                "encoding": encoding,
                "engine": "python" if robust_mode else "c",
                "on_bad_lines": "warn" if robust_mode else "error",
                "low_memory": True,
                "dtype": object,  # Use object type for all columns initially
            }

            # Initialize rows estimate based on a quick sample
            rows_estimate = self._estimate_rows(file_path, encoding)

            # Initial progress report
            if progress_callback:
                progress_callback(0, rows_estimate or 1000)  # Use estimate or default

            # Open the file to track reading progress more accurately
            with open(file_path, "r", encoding=encoding) as f:
                # Read file in chunks
                for chunk_index, chunk in enumerate(
                    pd.read_csv(file_path, chunksize=chunk_size, **kwargs)
                ):
                    # Update rows processed
                    rows_in_chunk = len(chunk)
                    rows_processed += rows_in_chunk

                    # Normalize text if requested
                    if normalize_text:
                        # Apply normalization to string columns
                        for col in chunk.select_dtypes(include=["object"]).columns:
                            chunk[col] = chunk[col].apply(
                                lambda x: self._normalize_text(x) if isinstance(x, str) else x
                            )

                    # Store chunk
                    chunks.append(chunk)

                    # Update processed data tracking
                    curr_pos = f.tell()
                    processed_bytes = curr_pos

                    # Update total row count
                    total_rows += rows_in_chunk

                    # Report progress
                    if progress_callback:
                        # Use file position for better progress tracking
                        progress_percent = min(99, int((processed_bytes / file_size) * 100))
                        if not progress_callback(progress_percent, 100):
                            # Callback returned False, indicating cancellation
                            return None, "CSV reading cancelled by progress callback"

            # Final progress report - 100%
            if progress_callback:
                progress_callback(100, 100)

            # Combine chunks
            if chunks:
                combined_df = pd.concat(chunks, ignore_index=True)
                return combined_df, None

            return pd.DataFrame(), None  # Empty DataFrame, no error

        except pd.errors.EmptyDataError:
            # Handle empty file
            return pd.DataFrame(), None

        except Exception as e:
            logger.error(f"Error reading CSV: {e}")
            return None, str(e)

    def read_csv_chunked(
        self,
        file_path: Union[str, Path],
        chunk_size: int = 1000,
        encoding: Optional[str] = None,
        normalize_text: bool = True,
        robust_mode: bool = False,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
        """
        Read a CSV file in chunks and return the combined DataFrame.

        This method reads the file in chunks to avoid memory issues with large files.
        It supports progress reporting and cancellation.

        Args:
            file_path: Path to the CSV file
            chunk_size: Number of rows to read in each chunk
            encoding: Optional encoding to use (auto-detected if None)
            normalize_text: Whether to normalize text in the CSV
            robust_mode: Whether to use robust mode for reading
            progress_callback: Optional callback function for progress reporting

        Returns:
            A tuple containing (DataFrame, error_message)
            On success, DataFrame contains the data and error_message is None
            On failure, DataFrame is None and error_message contains the error
        """
        # Ensure we're directly calling the internal implementation that returns a tuple
        # NOT the async version which returns a worker
        try:
            logger.debug(f"read_csv_chunked called for {file_path}")
            return self._read_csv_chunked_internal(
                file_path=file_path,
                chunk_size=chunk_size,
                encoding=encoding,
                normalize_text=normalize_text,
                robust_mode=robust_mode,
                progress_callback=progress_callback,
            )
        except Exception as e:
            logger.error(f"Error in read_csv_chunked: {str(e)}")
            return None, str(e)

    def read_csv_chunked_async(
        self,
        file_path: Union[str, Path],
        chunk_size: int = 1000,
        encoding: Optional[str] = None,
        normalize_text: bool = True,
        robust_mode: bool = False,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        finished_callback: Optional[Callable[[pd.DataFrame, str], None]] = None,
    ) -> BackgroundWorker:
        """
        Read a CSV file in chunks asynchronously and return a worker to track progress.

        This method creates a background task to read the file and returns a worker
        object that can be used to track progress and get the result.

        Args:
            file_path: Path to the CSV file
            chunk_size: Number of rows to read in each chunk
            encoding: Optional encoding to use (auto-detected if None)
            normalize_text: Whether to normalize text in the CSV
            robust_mode: Whether to use robust mode for reading
            progress_callback: Optional callback function for progress reporting
            finished_callback: Optional callback for when reading is complete

        Returns:
            A BackgroundWorker object that will execute the task
        """
        # Create a task
        task = CSVReadTask(
            file_path=file_path,
            chunk_size=chunk_size,
            encoding=encoding,
            normalize_text=normalize_text,
            robust_mode=robust_mode,
        )

        # Create a worker
        worker = BackgroundWorker()

        # Connect the task's progress signal to the callback if provided
        if progress_callback:
            worker.progress.connect(progress_callback)

        # Connect the finished signal to the callback if provided
        if finished_callback:
            worker.finished.connect(lambda result: finished_callback(result[0], result[1]))
            worker.error.connect(lambda error: finished_callback(None, str(error)))

        # Execute the task
        worker.execute_task(task)

        # Return the worker so the caller can connect to signals or cancel
        return worker

    def _estimate_rows(self, file_path: Path, encoding: str) -> int:
        """
        Estimate the number of rows in a CSV file by examining a small sample.

        Args:
            file_path: Path to the CSV file
            encoding: Encoding to use for reading the file

        Returns:
            Estimated number of rows
        """
        try:
            # Try to get a rough estimate by reading a small chunk and extrapolating
            sample = pd.read_csv(file_path, nrows=100, encoding=encoding)
            if len(sample) == 0:
                return 0

            # Calculate average row size in bytes
            file_size = file_path.stat().st_size
            avg_row_size = file_size / len(sample)

            # Estimate total rows, add 10% margin
            estimated_rows = int((file_size / avg_row_size) * 1.1)
            return max(estimated_rows, len(sample))  # At least return the sample size

        except Exception as e:
            logger.warning(f"Error estimating rows for {file_path}: {e}")
            return 1000  # Default fallback
