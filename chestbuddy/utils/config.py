"""
Configuration manager for the ChestBuddy application.

This module provides the ConfigManager class for managing application configuration.
"""

import configparser
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Set up logger
logger = logging.getLogger(__name__)


class ConfigManager:
    """
    Configuration manager for the ChestBuddy application.

    This class manages application configuration, including reading and writing
    configuration files, managing recent files, and providing default values.

    Implementation Notes:
        - Uses configparser for INI file handling
        - Implements singleton pattern
        - Provides typed getters (get_bool, get_int, get_float)
        - Handles file paths with platform-independence
    """

    _instance = None

    def __new__(cls, config_dir: Optional[str] = None) -> "ConfigManager":
        """
        Create a new ConfigManager instance (singleton pattern).

        Args:
            config_dir: Optional directory to store configuration files
        """
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._initialized = False

        # Re-initialize if config_dir is provided and different from the current one
        if (
            config_dir is not None
            and hasattr(cls._instance, "_config_dir")
            and cls._instance._config_dir != config_dir
        ):
            cls._instance._initialized = False

        # Initialize if needed
        if not cls._instance._initialized:
            cls._instance._init(config_dir)

        return cls._instance

    def _init(self, config_dir: Optional[str] = None) -> None:
        """
        Initialize the ConfigManager instance.

        This is separated from __init__ to allow reinitializing the singleton instance
        with a different config directory if needed.

        Args:
            config_dir: Optional directory to store configuration files
        """
        self._config_dir = config_dir or os.path.expanduser("~/.chestbuddy")
        self._config_file = os.path.join(self._config_dir, "config.ini")
        self._config = configparser.ConfigParser()

        # Create config directory if it doesn't exist
        os.makedirs(self._config_dir, exist_ok=True)

        # Load configuration
        self._load_config()

        # Initialize defaults if needed
        self._init_defaults()

        self._initialized = True
        logger.info(f"ConfigManager initialized with config directory: {self._config_dir}")

    def __init__(self, config_dir: Optional[str] = None) -> None:
        """
        Initialize the ConfigManager.

        Args:
            config_dir: Optional directory to store configuration files
        """
        # Initialization is handled in __new__ and _init
        pass

    def _init_defaults(self) -> None:
        """Initialize default configuration settings."""
        # Logging defaults
        self.set("Logging", "level", "DEBUG")  # Changed from INFO to DEBUG

        # Autosave defaults
        self.set("Autosave", "enabled", "True")
        self.set("Autosave", "interval_minutes", "5")

        # User preference defaults
        self.set("General", "theme", "Light")
        self.set("General", "language", "English")
        self.set("Preferences", "font_size", "10")
        self.set("Preferences", "date_format", "%Y-%m-%d")

        # Chart defaults
        self.set("Charts", "default_chart_type", "line")
        self.set("Charts", "color_palette", "default")

        # CSV import defaults
        self.set("Import", "normalize_text", "True")
        self.set("Import", "robust_mode", "True")
        self.set("Import", "chunk_size", "100")

        # Validation defaults
        self.set("Validation", "case_sensitive", "False")
        self.set("Validation", "validate_on_import", "True")

        # UI defaults
        self.set("UI", "window_width", "1024")
        self.set("UI", "window_height", "768")
        self.set("UI", "table_page_size", "100")

    def _load_config(self) -> None:
        """Load the configuration from file."""
        try:
            # Check if config file exists
            if os.path.exists(self._config_file):
                try:
                    # Try to read the config file with encoding
                    self._config.read(self._config_file, encoding="utf-8")
                    logger.info(f"Configuration loaded from {self._config_file}")
                except Exception as e:
                    # Handle ANY error reading the config file
                    logger.error(f"Error reading configuration file: {e}")
                    logger.warning("Corrupted configuration file detected, using defaults")
                    # Do NOT attempt to read the file again - just use defaults
            else:
                logger.info(f"No configuration file found at {self._config_file}, creating new one")
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            # Fall back to defaults if loading fails

    def save(self) -> None:
        """Save the configuration to file."""
        try:
            with open(self._config_file, "w", encoding="utf-8") as f:
                self._config.write(f)
            logger.info(f"Configuration saved to {self._config_file}")
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")

    def get(self, section: str, option: str, fallback: str = "") -> str:
        """
        Get a configuration value as a string.

        Args:
            section: Configuration section
            option: Configuration option
            fallback: Default value if not found

        Returns:
            str: Configuration value
        """
        try:
            return self._config.get(section, option, fallback=fallback)
        except (configparser.NoSectionError, configparser.NoOptionError):
            logger.debug(
                f"No configuration value for [{section}]{option}, using fallback: {fallback}"
            )
            return fallback

    def get_int(self, section: str, option: str, fallback: int = 0) -> int:
        """
        Get a configuration value as an integer.

        Args:
            section: Configuration section
            option: Configuration option
            fallback: Default value if not found

        Returns:
            int: Configuration value
        """
        try:
            return self._config.getint(section, option, fallback=fallback)
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            logger.debug(f"No valid integer for [{section}]{option}, using fallback: {fallback}")
            return fallback

    def get_float(self, section: str, option: str, fallback: float = 0.0) -> float:
        """
        Get a configuration value as a float.

        Args:
            section: Configuration section
            option: Configuration option
            fallback: Default value if not found

        Returns:
            float: Configuration value
        """
        try:
            return self._config.getfloat(section, option, fallback=fallback)
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            logger.debug(f"No valid float for [{section}]{option}, using fallback: {fallback}")
            return fallback

    def get_bool(self, section: str, option: str, fallback: bool = False) -> bool:
        """
        Get a configuration value as a boolean.

        Args:
            section: Configuration section
            option: Configuration option
            fallback: Default value if not found

        Returns:
            bool: Configuration value
        """
        try:
            value = self._config.get(section, option, fallback=str(fallback))
            # Handle string values explicitly for better error recovery
            if value.lower() in ("true", "yes", "1", "on"):
                return True
            elif value.lower() in ("false", "no", "0", "off"):
                return False
            else:
                logger.warning(
                    f"Invalid boolean value for [{section}]{option}: {value}, using fallback: {fallback}"
                )
                return fallback
        except (configparser.NoSectionError, configparser.NoOptionError):
            logger.debug(
                f"No configuration value for [{section}]{option}, using fallback: {fallback}"
            )
            return fallback

    def set(self, section: str, option: str, value: Any) -> None:
        """
        Set a configuration value.

        Args:
            section: Configuration section
            option: Configuration option
            value: Value to set
        """
        # Ensure section exists
        if not self._config.has_section(section):
            self._config.add_section(section)

        # Convert value to string
        str_value = str(value)

        # Set value
        self._config.set(section, option, str_value)
        logger.debug(f"Configuration value set: [{section}]{option} = {str_value}")

    def get_list(
        self, section: str, option: str, fallback: Optional[List[str]] = None
    ) -> List[str]:
        """
        Get a configuration value as a list.

        Lists are stored as comma-separated values.

        Args:
            section: Configuration section
            option: Configuration option
            fallback: Default value if not found

        Returns:
            List[str]: Configuration value as list
        """
        if fallback is None:
            fallback = []

        try:
            value = self._config.get(section, option, fallback="")
            if not value:
                return fallback

            # Split by comma and strip whitespace
            return [item.strip() for item in value.split(",")]
        except (configparser.NoSectionError, configparser.NoOptionError):
            logger.debug(
                f"No configuration value for [{section}]{option}, using fallback: {fallback}"
            )
            return fallback

    def set_list(self, section: str, option: str, value: List[str]) -> None:
        """
        Set a configuration value as a list.

        Lists are stored as comma-separated values.

        Args:
            section: Configuration section
            option: Configuration option
            value: List to set
        """
        # Convert list to comma-separated string
        str_value = ",".join(str(item) for item in value)
        self.set(section, option, str_value)

    def get_path(
        self, section: str, option: str, fallback: str = "", create_if_missing: bool = False
    ) -> Path:
        """
        Get a configuration value as a Path.

        Args:
            section: Configuration section
            option: Configuration option
            fallback: Default value if not found
            create_if_missing: Create directory if it doesn't exist

        Returns:
            Path: Configuration value as Path
        """
        path_str = self.get(section, option, fallback)

        # Get application root directory for resolving relative paths
        app_root = Path(__file__).parent.parent.parent

        # Resolve path - if it's already absolute, Path will keep it that way
        # If it's relative, it will be relative to the app root
        path = app_root / path_str

        # Create directory if requested
        if create_if_missing and path_str:
            path.parent.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Created directory: {path.parent}")

        return path

    def set_path(
        self, section: str, option: str, value: Union[str, Path], create_if_missing: bool = False
    ) -> None:
        """
        Set a configuration value as a Path.

        Args:
            section: Configuration section
            option: Configuration option
            value: Path to set (will be stored as relative path if possible)
            create_if_missing: Create directory if it doesn't exist
        """
        path = Path(value)

        # Get application root directory
        app_root = Path(__file__).parent.parent.parent

        # Try to make the path relative to the app root
        try:
            # Use relative_to to convert absolute paths to relative paths when possible
            if path.is_absolute():
                try:
                    # This will only work if the path is under the app_root
                    relative_path = path.relative_to(app_root)
                    path = relative_path
                except ValueError:
                    # If it's not under app_root, keep it absolute
                    pass
        except Exception as e:
            logger.warning(f"Could not convert path to relative: {e}")

        self.set(section, option, str(path))

        # Create directory if requested
        if create_if_missing:
            # Use the original path for directory creation
            orig_path = Path(value)
            orig_path.parent.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Created directory: {orig_path.parent}")

    def add_recent_file(self, file_path: str) -> None:
        """
        Add a file to the recent files list.

        Args:
            file_path: Path to the file
        """
        # Get current recent files
        recent_files = self.get_list("Files", "recent_files", [])

        # Convert to Path for platform independence
        path = Path(file_path)

        # Get application root directory
        app_root = Path(__file__).parent.parent.parent

        # Try to make the path relative to the app root
        try:
            if path.is_absolute():
                try:
                    # This will only work if the path is under the app_root
                    relative_path = path.relative_to(app_root)
                    path = relative_path
                except ValueError:
                    # If it's not under app_root, keep it absolute
                    pass
        except Exception as e:
            logger.warning(f"Could not convert path to relative: {e}")

        normalized_path = str(path)

        # Remove the file if it's already in the list
        if normalized_path in recent_files:
            recent_files.remove(normalized_path)

        # Add the file to the beginning of the list
        recent_files.insert(0, normalized_path)

        # Keep only the 10 most recent files
        recent_files = recent_files[:10]

        # Save the list
        self.set_list("Files", "recent_files", recent_files)
        logger.debug(f"Added to recent files: {normalized_path}")

    def get_recent_files(self, max_files: int = 10) -> List[str]:
        """
        Get the list of recent files.

        Only includes files that still exist.

        Args:
            max_files: Maximum number of files to return

        Returns:
            List[str]: Recent files
        """
        # Get all recent files
        all_files = self.get_list("Files", "recent_files", [])

        # Get application root directory
        app_root = Path(__file__).parent.parent.parent

        # Convert paths and filter out files that don't exist
        existing_files = []
        for file_str in all_files:
            # Create path object
            file_path = Path(file_str)

            # If it's a relative path, resolve it against app_root
            if not file_path.is_absolute():
                file_path = app_root / file_path

            # Check if file exists
            if file_path.exists():
                existing_files.append(str(file_path))

            # Only collect up to max_files
            if len(existing_files) >= max_files:
                break

        return existing_files

    def reset_to_defaults(self, section: Optional[str] = None) -> None:
        """
        Reset configuration to default values.

        Args:
            section: Optional section to reset. If None, reset all sections.
        """
        logger.info(
            f"Resetting configuration to defaults: {'all sections' if section is None else section}"
        )

        # Define default values for each section with specific capitalizations
        default_values = {
            "General": {
                "theme": "Light",  # Notice the exact capitalization
                "language": "English",
            },
            "Validation": {"case_sensitive": "False", "validate_on_import": "True"},
            "UI": {"window_width": "1024", "window_height": "768", "table_page_size": "100"},
            "Logging": {"level": "DEBUG"},
            "Import": {"normalize_text": "True", "robust_mode": "True", "chunk_size": "100"},
            "Autosave": {"enabled": "True", "interval_minutes": "5"},
            "Preferences": {"font_size": "10", "date_format": "%Y-%m-%d"},
            "Charts": {"default_chart_type": "line", "color_palette": "default"},
        }

        if section is None:
            # Reset all sections by creating a new config
            self._config = configparser.ConfigParser()

            # Set default values for all sections
            for section_name, options in default_values.items():
                if not self._config.has_section(section_name):
                    self._config.add_section(section_name)

                for option, value in options.items():
                    self._config.set(section_name, option, value)
        else:
            # Reset only the specified section
            if section in self._config.sections():
                self._config.remove_section(section)

            # Add section and set default values
            self._config.add_section(section)

            if section in default_values:
                for option, value in default_values[section].items():
                    self._config.set(section, option, value)

        # Save changes
        self.save()
        logger.info(
            f"Configuration reset completed for {'all sections' if section is None else section}"
        )

    def validate_config(self) -> bool:
        """
        Validate the configuration file.

        Returns:
            bool: True if the configuration is valid, False otherwise.
        """
        try:
            # Check if each section has the expected options
            required_sections = ["General", "Validation", "UI", "Logging", "Import"]

            for section in required_sections:
                if not self._config.has_section(section):
                    logger.warning(f"Missing required section: {section}")
                    return False

            # Check specific important options
            if not self._config.has_option("Validation", "validate_on_import"):
                logger.warning("Missing required option: [Validation]validate_on_import")
                return False

            if not self._config.has_option("General", "theme"):
                logger.warning("Missing required option: [General]theme")
                return False

            # Add more validation as needed

            return True
        except Exception as e:
            logger.error(f"Error validating configuration: {e}")
            return False

    def get_validation_list_path(self, list_name: str) -> Path:
        """
        Get the path to a validation list file.

        Args:
            list_name: Name of the validation list

        Returns:
            Path: Path to the validation list file
        """
        # Normalize list name
        if not list_name.endswith(".txt"):
            list_name = f"{list_name}.txt"

        # Get application root directory
        app_root = Path(__file__).parent.parent.parent

        # Create validation lists directory within the application
        validation_dir = app_root / "chestbuddy" / "validation_lists"
        validation_dir.mkdir(parents=True, exist_ok=True)

        # List path
        list_path = validation_dir / list_name

        return list_path

    def export_config(self, file_path: Union[str, Path]) -> None:
        """
        Export the configuration to a JSON file.

        Args:
            file_path: Path to export to
        """
        try:
            # Convert config to dictionary
            config_dict = {}
            for section in self._config.sections():
                config_dict[section] = dict(self._config[section])

            # Write to JSON file
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(config_dict, f, indent=4)

            logger.info(f"Configuration exported to {file_path}")
        except Exception as e:
            logger.error(f"Error exporting configuration: {e}")
            raise

    def import_config(self, file_path: Union[str, Path]) -> None:
        """
        Import configuration from a JSON file.

        Args:
            file_path: Path to import from
        """
        try:
            # Read JSON file
            with open(file_path, "r", encoding="utf-8") as f:
                config_dict = json.load(f)

            # Update config
            for section, options in config_dict.items():
                if not self._config.has_section(section):
                    self._config.add_section(section)

                for option, value in options.items():
                    self._config.set(section, option, value)

            # Save changes
            self.save()
            logger.info(f"Configuration imported from {file_path}")
        except Exception as e:
            logger.error(f"Error importing configuration: {e}")
            raise
