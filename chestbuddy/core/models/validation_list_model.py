"""
validation_list_model.py

Description: Model for managing validation lists
"""

import logging
from pathlib import Path
from typing import List, Set, Optional, Tuple

from PySide6.QtCore import QObject, Signal

logger = logging.getLogger(__name__)


class ValidationListModel(QObject):
    """
    Model for managing lists of valid entries for validation.

    Attributes:
        entries_changed (Signal): Signal emitted when entries are changed
        file_path (Path): Path to the file containing entries
        entries (Set[str]): Set of valid entries
        case_sensitive (bool): Whether validation is case sensitive
    """

    entries_changed = Signal()

    def __init__(self, file_path: str, case_sensitive: bool = False):
        """
        Initialize the validation list model.

        Args:
            file_path (str): Path to the file containing entries
            case_sensitive (bool, optional): Whether validation is case sensitive. Defaults to False.
        """
        super().__init__()
        self.file_path = Path(file_path)
        self.entries: Set[str] = set()
        self._case_sensitive = case_sensitive

        # Ensure parent directory exists
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

        # Create file if it doesn't exist
        if not self.file_path.exists():
            self.file_path.touch()
            logger.info(f"Created new validation file: {self.file_path}")
            # Try to initialize from default
            self._initialize_from_default()
        # If file exists but is empty, try to initialize from default
        elif self.file_path.exists() and self.file_path.stat().st_size == 0:
            logger.info(f"Validation file exists but is empty: {self.file_path}")
            self._initialize_from_default()

        # Load entries from file
        self._load_entries()
        logger.info(
            f"Initialized ValidationListModel with {len(self.entries)} entries from {self.file_path}"
        )

    def _initialize_from_default(self) -> bool:
        """
        Initialize an empty validation list file from default content.

        Returns:
            bool: True if successfully initialized from default, False otherwise
        """
        try:
            # Find the default file in the application's data directory
            filename = self.file_path.name
            default_path = Path(__file__).parents[2] / "data" / "validation" / filename

            # If default file exists, copy its content
            if default_path.exists() and default_path.is_file():
                try:
                    with (
                        open(default_path, "r", encoding="utf-8") as src,
                        open(self.file_path, "w", encoding="utf-8") as dst,
                    ):
                        content = src.read()
                        dst.write(content)

                    logger.info(
                        f"Initialized validation file from default: {default_path} -> {self.file_path}"
                    )
                    return True
                except Exception as e:
                    logger.error(f"Error copying default validation content: {e}")
                    return False
            else:
                logger.warning(f"No default validation file found at: {default_path}")
                return False
        except Exception as e:
            logger.error(f"Error initializing from default: {e}")
            return False

    def _load_entries(self) -> None:
        """Load entries from the file."""
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            # Strip whitespace and filter out empty lines
            self.entries = {line.strip() for line in lines if line.strip()}
            logger.debug(f"Loaded {len(self.entries)} entries from {self.file_path}")
        except Exception as e:
            logger.error(f"Error loading entries from {self.file_path}: {str(e)}")
            self.entries = set()

    def refresh(self) -> None:
        """Reload entries from the file and emit signal."""
        self._load_entries()
        self.entries_changed.emit()
        logger.debug(f"Refreshed entries from {self.file_path}")

    def save_entries(self) -> bool:
        """
        Save the current entries to the file.

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Sort entries alphabetically
            sorted_entries = sorted(self.entries)

            with open(self.file_path, "w", encoding="utf-8") as f:
                for entry in sorted_entries:
                    f.write(f"{entry}\n")

            logger.debug(f"Saved {len(self.entries)} entries to {self.file_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving entries to {self.file_path}: {str(e)}")
            return False

    def _is_duplicate_entry(self, entry: str) -> bool:
        """
        Check if an entry already exists in the list.

        Args:
            entry (str): Entry to check

        Returns:
            bool: True if entry exists, False otherwise
        """
        if not entry:
            return False

        entry = entry.strip()
        if not entry:
            return False

        if self._case_sensitive:
            return entry in self.entries
        else:
            return any(e.lower() == entry.lower() for e in self.entries)

    def add_entry(self, entry: str) -> bool:
        """
        Add a new entry to the list.

        Args:
            entry (str): Entry to add

        Returns:
            bool: True if added, False if already exists or invalid
        """
        entry = entry.strip()
        if not entry:
            logger.warning("Attempted to add empty entry, ignoring")
            return False

        # Check if entry already exists
        if self._is_duplicate_entry(entry):
            logger.debug(f"Entry '{entry}' already exists, not adding")
            return False

        # Add entry
        self.entries.add(entry)

        # Save changes
        result = self.save_entries()
        if result:
            self.entries_changed.emit()
            logger.info(f"Added entry '{entry}' to {self.file_path}")

        return result

    def remove_entry(self, entry: str) -> bool:
        """
        Remove an entry from the list.

        Args:
            entry (str): Entry to remove

        Returns:
            bool: True if removed, False if not found
        """
        # Check if entry exists
        if not self._is_duplicate_entry(entry):
            logger.debug(f"Entry '{entry}' not found, cannot remove")
            return False

        # Case-insensitive comparison requires finding the actual entry
        if not self._case_sensitive:
            for e in self.entries:
                if e.lower() == entry.lower():
                    entry = e
                    break

        # Remove entry
        self.entries.remove(entry)

        # Save changes
        result = self.save_entries()
        if result:
            self.entries_changed.emit()
            logger.info(f"Removed entry '{entry}' from {self.file_path}")

        return result

    def import_from_file(self, file_path: Path) -> Tuple[bool, List[str]]:
        """
        Import entries from a file, replacing all existing entries.

        Args:
            file_path (Path): Path to the file to import

        Returns:
            Tuple[bool, List[str]]: (Success, empty list - duplicates no longer checked)
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                entries = [line.strip() for line in f.readlines() if line.strip()]

            # Replace current entries with imported entries, regardless of duplicates
            self.entries = set(entries)
            if self.save_entries():
                self.entries_changed.emit()
                logger.info(
                    f"Successfully imported {len(entries)} entries from {file_path}, replacing all existing entries"
                )
                return True, []
            else:
                logger.error("Failed to save entries after import")
                return False, []

        except Exception as e:
            logger.error(f"Error importing entries from {file_path}: {e}")
            return False, []

    def export_to_file(self, file_path: Path) -> bool:
        """
        Export entries to a file.

        Args:
            file_path (Path): Path to save the entries to

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create parent directory if it doesn't exist
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Sort entries alphabetically
            sorted_entries = sorted(self.entries)

            # Write entries to file
            with open(file_path, "w", encoding="utf-8") as f:
                for entry in sorted_entries:
                    f.write(f"{entry}\n")

            logger.info(f"Successfully exported {len(self.entries)} entries to {file_path}")
            return True

        except Exception as e:
            logger.error(f"Error exporting entries to {file_path}: {e}")
            return False

    def contains(self, entry: str) -> bool:
        """
        Check if an entry exists in the list.

        Args:
            entry (str): Entry to check

        Returns:
            bool: True if entry exists, False otherwise
        """
        return self._is_duplicate_entry(entry)

    def get_entries(self) -> List[str]:
        """
        Get all entries as a sorted list.

        Returns:
            List[str]: Sorted list of entries
        """
        return sorted(self.entries)

    def find_matching_entries(self, query: str) -> List[str]:
        """
        Find entries that match a query string.

        Args:
            query (str): Query string

        Returns:
            List[str]: List of matching entries
        """
        if not query:
            return self.get_entries()

        if self._case_sensitive:
            matches = [entry for entry in self.entries if query in entry]
        else:
            query_lower = query.lower()
            matches = [entry for entry in self.entries if query_lower in entry.lower()]

        return sorted(matches)

    def clear(self) -> bool:
        """
        Clear all entries from the list.

        Returns:
            bool: True if successful, False otherwise
        """
        self.entries.clear()

        # Save changes
        result = self.save_entries()
        if result:
            self.entries_changed.emit()
            logger.info(f"Cleared all entries from {self.file_path}")

        return result

    def count(self) -> int:
        """
        Get the number of entries in the list.

        Returns:
            int: Number of entries
        """
        return len(self.entries)

    def set_case_sensitive(self, case_sensitive: bool) -> None:
        """
        Set whether validation is case sensitive.

        Args:
            case_sensitive (bool): Whether validation is case sensitive
        """
        if self._case_sensitive != case_sensitive:
            self._case_sensitive = case_sensitive
            logger.debug(f"Set case sensitivity to {case_sensitive} for {self.file_path}")

    def is_case_sensitive(self) -> bool:
        """
        Get whether validation is case sensitive.

        Returns:
            bool: Whether validation is case sensitive
        """
        return self._case_sensitive

    def reset(self) -> None:
        """Reset the validation list to its original state from the file."""
        self.entries.clear()
        self._load_entries()

    def has_unsaved_changes(self) -> bool:
        """
        Check if there are unsaved changes.

        Returns:
            bool: True if there are unsaved changes, False otherwise
        """
        # For now, we assume changes are saved immediately
        # This is a placeholder in case we implement a more sophisticated change tracking system
        return False
