import pytest
from unittest.mock import MagicMock, patch
from PySide6.QtWidgets import QApplication, QCheckBox, QComboBox, QLineEdit, QSpinBox

from chestbuddy.ui.views.settings_tab_view import SettingsTabView
from chestbuddy.utils.config import ConfigManager


@pytest.fixture
def mock_validation_service():
    """Create a mock validation service."""
    return MagicMock()


@pytest.fixture
def mock_correction_controller():
    """Create a mock correction controller."""
    return MagicMock()


@pytest.fixture
def settings_tab_view(qtbot, mock_validation_service, mock_correction_controller):
    """Create a settings tab view for testing."""
    with patch.object(ConfigManager, "_init", return_value=None):
        view = SettingsTabView(
            validation_service=mock_validation_service,
            correction_controller=mock_correction_controller,
        )
        qtbot.addWidget(view)
        return view


def test_settings_tab_view_init(qtbot, mock_controller):
    """Test SettingsTabView initialization."""
    view = SettingsTabView(controller=mock_controller)
    qtbot.addWidget(view)
    assert view._controller == mock_controller
    # Check if tab widget exists
    assert view._tab_widget is not None
    # Check if settings widgets dictionaries exist
    assert "General" in view._settings_widgets
    assert "Validation" in view._settings_widgets
    assert "Correction" in view._settings_widgets
    assert "UI" in view._settings_widgets


def test_general_tab(qtbot, mock_controller):
    """Test the General settings tab."""
    view = SettingsTabView(controller=mock_controller)
    qtbot.addWidget(view)
    general_widgets = view._settings_widgets["General"]
    assert "theme" in general_widgets
    assert "language" in general_widgets
    assert "config_version" in general_widgets
    assert isinstance(general_widgets["theme"], QComboBox)
    assert isinstance(general_widgets["language"], QComboBox)
    assert isinstance(general_widgets["config_version"], QLineEdit)


def test_validation_tab(qtbot, mock_controller):
    """Test the Validation settings tab."""
    view = SettingsTabView(controller=mock_controller)
    qtbot.addWidget(view)
    validation_widgets = view._settings_widgets["Validation"]
    assert "validate_on_import" in validation_widgets
    assert "case_sensitive" in validation_widgets
    assert "auto_save" in validation_widgets
    assert "validation_lists_dir" in validation_widgets
    assert isinstance(validation_widgets["validate_on_import"], QCheckBox)
    assert isinstance(validation_widgets["case_sensitive"], QCheckBox)
    assert isinstance(validation_widgets["auto_save"], QCheckBox)
    assert isinstance(validation_widgets["validation_lists_dir"], QLineEdit)


def test_correction_tab(qtbot, mock_controller):
    """Test the Correction settings tab."""
    view = SettingsTabView(controller=mock_controller)
    qtbot.addWidget(view)
    correction_widgets = view._settings_widgets["Correction"]
    assert "auto_correct_on_validation" in correction_widgets
    assert "auto_correct_on_import" in correction_widgets
    assert isinstance(correction_widgets["auto_correct_on_validation"], QCheckBox)
    assert isinstance(correction_widgets["auto_correct_on_import"], QCheckBox)


def test_ui_tab(qtbot, mock_controller):
    """Test the UI settings tab."""
    view = SettingsTabView(controller=mock_controller)
    qtbot.addWidget(view)
    ui_widgets = view._settings_widgets["UI"]
    assert "window_width" in ui_widgets
    assert "window_height" in ui_widgets
    assert "table_page_size" in ui_widgets
    assert isinstance(ui_widgets["window_width"], QSpinBox)
    assert isinstance(ui_widgets["window_height"], QSpinBox)
    assert isinstance(ui_widgets["table_page_size"], QSpinBox)


@patch("chestbuddy.ui.views.settings_tab_view.ConfigManager")
def test_settings_changed_updates_config(mock_config_manager_class, qtbot):
    """Test that settings changes update the config."""
    # Create a mock ConfigManager instance
    mock_config_manager = MagicMock()
    mock_config_manager_class.return_value = mock_config_manager

    # Create settings tab view
    settings_view = SettingsTabView()
    qtbot.addWidget(settings_view)

    # Simulate a setting change
    settings_view._on_setting_changed("General", "theme", "Dark")

    # Check that config was updated
    mock_config_manager.set.assert_called_with("General", "theme", "Dark")
    mock_config_manager.save.assert_called_once()


@patch("chestbuddy.ui.views.settings_tab_view.ConfigManager")
def test_validation_settings_update_service(mock_config_manager_class, qtbot):
    """Test that validation service is updated when settings change."""
    # Create a mock ConfigManager instance
    mock_config_manager = MagicMock()
    mock_config_manager_class.return_value = mock_config_manager

    # Create a mock validation service
    mock_validation_service = MagicMock()

    # Create settings tab view
    settings_view = SettingsTabView(validation_service=mock_validation_service)
    qtbot.addWidget(settings_view)

    # Simulate validation setting changes
    settings_view._on_setting_changed("Validation", "validate_on_import", "True")
    mock_validation_service.set_validate_on_import.assert_called_with(True)

    settings_view._on_setting_changed("Validation", "case_sensitive", "True")
    mock_validation_service.set_case_sensitive.assert_called_with(True)

    settings_view._on_setting_changed("Validation", "auto_save", "False")
    mock_validation_service.set_auto_save.assert_called_with(False)


@patch("chestbuddy.ui.views.settings_tab_view.ConfigManager")
def test_correction_settings(mock_config_manager_class, qtbot):
    """Test correction settings are properly handled."""
    # Create a mock ConfigManager instance
    mock_config_manager = MagicMock()
    mock_config_manager.get_auto_correct_on_validation.return_value = True
    mock_config_manager.get_auto_correct_on_import.return_value = False
    mock_config_manager_class.return_value = mock_config_manager

    # Create settings tab view
    settings_view = SettingsTabView()
    qtbot.addWidget(settings_view)

    # Access correction widgets
    correction_widgets = settings_view._settings_widgets["Correction"]
    auto_correct_validation_checkbox = correction_widgets["auto_correct_on_validation"]
    auto_correct_import_checkbox = correction_widgets["auto_correct_on_import"]

    # Simulate loading settings
    settings_view._load_settings()

    # Check that checkboxes reflect config values
    assert auto_correct_validation_checkbox.isChecked() == True
    assert auto_correct_import_checkbox.isChecked() == False

    # Simulate checkbox changes
    auto_correct_validation_checkbox.setChecked(False)
    mock_config_manager.set.assert_called_with("Correction", "auto_correct_on_validation", "False")

    auto_correct_import_checkbox.setChecked(True)
    mock_config_manager.set.assert_called_with("Correction", "auto_correct_on_import", "True")
