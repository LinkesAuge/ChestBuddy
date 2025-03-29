"""
ConfigManager module.

This module provides the ConfigManager class for managing application settings.
"""

import configparser
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


class ConfigManager:
    """
    Manages application configuration settings.

    The ConfigManager is implemented as a singleton to ensure consistent access to configuration
    settings throughout the application. It handles reading from and writing to a configuration
    file, manages file paths, and provides methods for accessing and updating settings.

    Attributes:
        _instance (ConfigManager): The singleton instance of the ConfigManager.
        _config_file (Path): Path to the configuration file.
        _config (configparser.ConfigParser): The configuration parser.
        _default_config (Dict[str, Dict[str, Any]]): Default configuration settings.
    """

    _instance = None

    def __new__(cls, config_dir: Optional[str] = None) -> "ConfigManager":
        """
        Create a new ConfigManager instance or return the existing one.

        Args:
            config_dir: Optional directory path for configuration files.
                       If not provided, uses the default app data directory.

        Returns:
            The singleton ConfigManager instance.
        """
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._init(config_dir)
        return cls._instance

    def _init(self, config_dir: Optional[str] = None) -> None:
        """
        Initialize the ConfigManager with the configuration directory.

        Args:
            config_dir: Optional directory path for configuration files.
        """
        # Set up configuration directory
        if config_dir:
            self._config_dir = Path(config_dir)
        else:
            # Default to user's app data directory
            app_data = os.getenv("APPDATA") or os.path.expanduser("~/.config")
            self._config_dir = Path(app_data) / "ChestBuddy"

        # Ensure the config directory exists
        self._config_dir.mkdir(parents=True, exist_ok=True)

        # Initialize config file path
        self._config_file = self._config_dir / "config.ini"

        # Set up default configuration
        self._default_config = {
            "General": {
                "theme": "dark",
                "language": "en",
            },
            "Files": {
                "recent_files": "",
                "last_import_dir": "",
                "last_export_dir": "",
            },
            "Validation": {
                "validation_lists_dir": str(self._config_dir / "validation_lists"),
                "validate_on_import": "True",
            },
            "Correction": {
                "auto_correct": "True",
                "correction_rules_file": str(self._config_dir / "correction_rules.csv"),
            },
            "UI": {
                "window_width": "1024",
                "window_height": "768",
                "table_page_size": "100",
            },
        }

        # Initialize the configuration parser
        self._config = configparser.ConfigParser()

        # Load or create the configuration file
        if self._config_file.exists():
            self._config.read(self._config_file)
        else:
            self._create_default_config()

    def _create_default_config(self) -> None:
        """Create the default configuration file."""
        for section, options in self._default_config.items():
            if not self._config.has_section(section):
                self._config.add_section(section)

            for option, value in options.items():
                self._config.set(section, option, str(value))

        # Create validation lists directory
        validation_lists_dir = Path(self._default_config["Validation"]["validation_lists_dir"])
        validation_lists_dir.mkdir(parents=True, exist_ok=True)

        # Save the configuration
        self.save()

    def save(self) -> None:
        """Save the current configuration to the config file."""
        with open(self._config_file, "w") as config_file:
            self._config.write(config_file)

    def get(self, section: str, option: str, fallback: Any = None) -> str:
        """
        Get a configuration value.

        Args:
            section: The configuration section.
            option: The configuration option.
            fallback: Fallback value if the option is not found.

        Returns:
            The configuration value as a string.
        """
        return self._config.get(section, option, fallback=fallback)

    def get_bool(self, section: str, option: str, fallback: bool = False) -> bool:
        """
        Get a boolean configuration value.

        Args:
            section: The configuration section.
            option: The configuration option.
            fallback: Fallback value if the option is not found.

        Returns:
            The configuration value as a boolean.
        """
        return self._config.getboolean(section, option, fallback=fallback)

    def get_int(self, section: str, option: str, fallback: int = 0) -> int:
        """
        Get an integer configuration value.

        Args:
            section: The configuration section.
            option: The configuration option.
            fallback: Fallback value if the option is not found.

        Returns:
            The configuration value as an integer.
        """
        return self._config.getint(section, option, fallback=fallback)

    def get_float(self, section: str, option: str, fallback: float = 0.0) -> float:
        """
        Get a float configuration value.

        Args:
            section: The configuration section.
            option: The configuration option.
            fallback: Fallback value if the option is not found.

        Returns:
            The configuration value as a float.
        """
        return self._config.getfloat(section, option, fallback=fallback)

    def get_list(self, section: str, option: str, fallback: List[str] = None) -> List[str]:
        """
        Get a list configuration value (stored as JSON).

        Args:
            section: The configuration section.
            option: The configuration option.
            fallback: Fallback value if the option is not found.

        Returns:
            The configuration value as a list.
        """
        if fallback is None:
            fallback = []

        value = self.get(section, option, "")
        if not value:
            return fallback

        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return fallback

    def set(self, section: str, option: str, value: Any) -> None:
        """
        Set a configuration value.

        Args:
            section: The configuration section.
            option: The configuration option.
            value: The value to set.
        """
        if not self._config.has_section(section):
            self._config.add_section(section)

        self._config.set(section, option, str(value))
        self.save()

    def set_list(self, section: str, option: str, value: List[Any]) -> None:
        """
        Set a list configuration value (stored as JSON).

        Args:
            section: The configuration section.
            option: The configuration option.
            value: The list value to set.
        """
        json_value = json.dumps(value)
        self.set(section, option, json_value)

    def get_path(self, section: str, option: str, fallback: Optional[str] = None) -> Path:
        """
        Get a path configuration value.

        Args:
            section: The configuration section.
            option: The configuration option.
            fallback: Fallback path if the option is not found.

        Returns:
            The configuration value as a Path object.
        """
        path_str = self.get(section, option, fallback)
        if path_str:
            return Path(path_str)
        return Path()

    def set_path(
        self, section: str, option: str, path: Union[str, Path], create_if_missing: bool = False
    ) -> None:
        """
        Set a path configuration value.

        Args:
            section: The configuration section.
            option: The configuration option.
            path: The path to set.
            create_if_missing: Whether to create the directory if it doesn't exist.
        """
        path_obj = Path(path)
        self.set(section, option, str(path_obj))

        if create_if_missing and not path_obj.exists():
            if path_obj.suffix:  # It's a file path
                path_obj.parent.mkdir(parents=True, exist_ok=True)
            else:  # It's a directory path
                path_obj.mkdir(parents=True, exist_ok=True)

    def add_recent_file(self, file_path: Union[str, Path]) -> None:
        """
        Add a file to the recent files list.

        Args:
            file_path: The path of the file to add.
        """
        recent_files = self.get_list("Files", "recent_files")
        path_str = str(Path(file_path))

        # Remove the file if it's already in the list
        if path_str in recent_files:
            recent_files.remove(path_str)

        # Add the file to the beginning of the list
        recent_files.insert(0, path_str)

        # Keep only the 10 most recent files
        recent_files = recent_files[:10]

        self.set_list("Files", "recent_files", recent_files)

    def get_recent_files(self) -> List[Path]:
        """
        Get the list of recent files.

        Returns:
            A list of Path objects representing recent files.
        """
        recent_files = self.get_list("Files", "recent_files")
        return [Path(file) for file in recent_files if Path(file).exists()]
