from chestbuddy.ui.data.menus.actions import (
    AbstractContextAction,
    CopyAction,
    PasteAction,
    CutAction,
    DeleteAction,
    EditCellAction,
    ShowEditDialogAction,
    ViewErrorAction,
    ApplyCorrectionAction,
    AddToCorrectionListAction,
    AddToValidationListAction,
    BatchCorrectionAction,
    BatchValidateAction,
    FormatNumberAction,
    ParseDateAction,
)
from chestbuddy.ui.data.models.data_view_model import DataViewModel
from chestbuddy.ui.data.menus.base_action import ActionContext
from chestbuddy.core.table_state_manager import TableStateManager

# Qt Imports
from PySide6.QtWidgets import QMenu, QWidget
from PySide6.QtGui import QAction
from PySide6.QtCore import QModelIndex

# Standard Imports
import typing
import logging

logger = logging.getLogger(__name__)


class ContextMenuFactory:
    """Factory for creating context-specific menu items."""

    # Register all available action classes
    REGISTERED_ACTION_CLASSES: typing.List[typing.Type[AbstractContextAction]] = [
        CopyAction,
        PasteAction,
        CutAction,
        DeleteAction,
        EditCellAction,
        ShowEditDialogAction,
        ViewErrorAction,
        ApplyCorrectionAction,
        AddToCorrectionListAction,
        AddToValidationListAction,
        BatchCorrectionAction,
        BatchValidateAction,
        FormatNumberAction,  # Register new action
        ParseDateAction,  # Register new action
    ]

    @staticmethod
    def create_context_menu(
        info: ActionContext,
    ) -> typing.Tuple[QMenu, typing.Dict[str, QAction]]:
        """Create a context menu based on selection and cell state."""
        menu = QMenu(info.parent_widget)
        created_qactions = {}
        applicable_actions = []

        # Instantiate and check applicability
        for ActionClass in ContextMenuFactory.REGISTERED_ACTION_CLASSES:
            try:
                action_instance = ActionClass()
                if action_instance.is_applicable(info):
                    applicable_actions.append(action_instance)
            except Exception as e:
                logger.error(f"Error instantiating or checking action {ActionClass.__name__}: {e}")

        # Sort actions (optional, could add an 'order' property to actions)
        # applicable_actions.sort(key=lambda x: getattr(x, 'order', 100))

        # Add actions to menu
        for action_instance in applicable_actions:
            try:
                qaction = QAction(
                    action_instance.text, menu
                )  # Assuming icon is handled later or is None
                if hasattr(action_instance, "icon") and action_instance.icon:
                    qaction.setIcon(action_instance.icon)

                qaction.setEnabled(action_instance.is_enabled(info))

                # Use a lambda with default argument binding to capture the correct action instance
                qaction.triggered.connect(
                    lambda checked=False, bound_action=action_instance: bound_action.execute(info)
                )
                menu.addAction(qaction)
                created_qactions[action_instance.id] = qaction
                logger.debug(
                    f"Added action '{action_instance.text}' (ID: {action_instance.id}), Enabled: {qaction.isEnabled()}"
                )

            except Exception as e:
                logger.error(f"Error adding action {action_instance.id} to menu: {e}")

        # Placeholder for adding separators or further customization
        # if some_condition:
        #     menu.addSeparator()

        logger.debug(f"ContextMenu created with {len(created_qactions)} actions.")
        return menu, created_qactions
