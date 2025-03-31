"""
test_import_export_buttons.py

A manual test script for the Import/Export buttons in CorrectionRuleView.
"""

import sys
import os
import logging
from pathlib import Path
from unittest.mock import MagicMock

# Add the parent directory to sys.path
sys.path.append(str(Path(__file__).parent.parent.parent))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

from chestbuddy.core.controllers.correction_controller import CorrectionController
from chestbuddy.core.models.correction_rule_manager import CorrectionRuleManager
from chestbuddy.core.services.correction_service import CorrectionService
from chestbuddy.core.services.validation_service import ValidationService
from chestbuddy.ui.views.correction_rule_view import CorrectionRuleView

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def main():
    """Main test function."""
    app = QApplication(sys.argv)

    # Create mocks and dependencies
    data_model = MagicMock()
    config_manager = MagicMock()

    # Create real components with mock dependencies
    rule_manager = CorrectionRuleManager()
    validation_service = ValidationService(data_model=data_model)
    correction_service = CorrectionService(
        validation_service=validation_service, rule_manager=rule_manager, data_model=data_model
    )

    # Create controller with correct arguments
    controller = CorrectionController(
        correction_service=correction_service,
        rule_manager=rule_manager,
        config_manager=config_manager,
    )

    # Create view
    view = CorrectionRuleView(controller=controller)
    view.show()

    # Mock the _show_import_export_dialog method to log calls
    original_method = view._show_import_export_dialog

    def mock_dialog(export_mode=False):
        logger.info(f"_show_import_export_dialog called with export_mode={export_mode}")
        # Don't actually show the dialog for testing

    view._show_import_export_dialog = mock_dialog

    # Schedule button clicks after a delay
    def test_buttons():
        logger.info("Clicking Import button")
        view._import_button.click()

        logger.info("Clicking Export button")
        view._export_button.click()

        # Exit after tests
        app.quit()

    QTimer.singleShot(1000, test_buttons)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
