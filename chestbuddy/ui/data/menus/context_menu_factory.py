"""
context_menu_factory.py

Factory for creating context menus for the DataTableView.
"""

import typing
from dataclasses import dataclass

from PySide6.QtCore import QModelIndex, Qt
from PySide6.QtGui import QAction, QGuiApplication, QIcon, QKeySequence
from PySide6.QtWidgets import QMenu, QWidget

# Placeholder imports - replace with actual paths
from ..models.data_view_model import DataViewModel  # Import real class
from chestbuddy.core.table_state_manager import CellState  # Import real enum
# DataViewModel = typing.NewType("DataViewModel", object)  # Placeholder type
# CellState = typing.NewType("CellState", object)

# Import Action classes (adjust path as needed)
from ..actions.base_action import AbstractContextAction
from ..actions.edit_actions import CopyAction, PasteAction, CutAction, DeleteAction

# Import future action classes here
from ..actions.validation_actions import ViewErrorAction  # Import real action
# from ..actions.correction_actions import ApplyCorrectionAction

# Import real ActionContext
from ..context.action_context import ActionContext


@dataclass
class ActionContext:
    """Information needed to build the context menu and execute actions."""

    clicked_index: QModelIndex
    selection: typing.List[QModelIndex]
    model: typing.Optional[DataViewModel]
    parent_widget: QWidget  # Needed for QMenu parent and potentially for action execution
    # Add other context if needed by actions (e.g., view object, state manager)


# --- Placeholder Actions for now ---
# Keep placeholders for actions not yet implemented
class ApplyCorrectionAction(AbstractContextAction):
    @property
    def id(self) -> str:
        return "apply_correction"

    @property
    def text(self) -> str:
        return "Apply Correction"

    @property
    def icon(self) -> QIcon:
        return QIcon.fromTheme("edit-fix")

    def is_applicable(self, context: ActionContext) -> bool:
        state = (
            context.model.data(context.clicked_index, DataViewModel.ValidationStateRole)
            if context.clicked_index.isValid()
            else None
        )
        return state == CellState.CORRECTABLE

    def is_enabled(self, context: ActionContext) -> bool:
        return True

    def execute(self, context: ActionContext) -> None:
        print(f"TODO: Execute {self.id}")


class AddToCorrectionListAction(AbstractContextAction):
    @property
    def id(self) -> str:
        return "add_correction"

    @property
    def text(self) -> str:
        return "Add to Correction List (TODO)"

    def is_applicable(self, context: ActionContext) -> bool:
        return True  # Always show for now

    def is_enabled(self, context: ActionContext) -> bool:
        return len(context.selection) > 0  # Enable if selection exists

    def execute(self, context: ActionContext) -> None:
        print(f"TODO: Execute {self.id}")


class AddToValidationListAction(AbstractContextAction):
    @property
    def id(self) -> str:
        return "add_validation"

    @property
    def text(self) -> str:
        return "Add to Validation List (TODO)"

    def is_applicable(self, context: ActionContext) -> bool:
        return True  # Always show for now

    def is_enabled(self, context: ActionContext) -> bool:
        return len(context.selection) > 0  # Enable if selection exists

    def execute(self, context: ActionContext) -> None:
        print(f"TODO: Execute {self.id}")


# --- End Placeholder Actions ---


class ContextMenuFactory:
    """
    Creates context menus for the DataTableView based on the provided context.
    Uses an extensible action framework.
    """

    # Register known action classes
    # TODO: Consider making this dynamic or configurable
    REGISTERED_ACTION_CLASSES: typing.List[typing.Type[AbstractContextAction]] = [
        CopyAction,
        PasteAction,
        CutAction,
        DeleteAction,
        # Separator needed here
        ViewErrorAction,
        ApplyCorrectionAction,
        # Separator needed here
        AddToCorrectionListAction,
        AddToValidationListAction,
    ]

    @staticmethod
    def create_context_menu(info: ActionContext) -> typing.Tuple[QMenu, typing.Dict[str, QAction]]:
        """
        Creates the appropriate QMenu based on the context information.

        Args:
            info: ActionContext containing details about the click and selection.

        Returns:
            A tuple containing the created QMenu and a dictionary mapping action IDs
            to the created QAction widgets.
        """
        menu = QMenu(info.parent_widget)
        created_qactions: typing.Dict[str, QAction] = {}

        if not info.model:
            return menu, created_qactions  # Cannot build menu without model

        needs_separator = False
        action_instances: typing.List[AbstractContextAction] = []

        # Instantiate registered actions
        for ActionClass in ContextMenuFactory.REGISTERED_ACTION_CLASSES:
            try:
                action_instances.append(ActionClass())
            except Exception as e:
                print(f"Error instantiating action {ActionClass.__name__}: {e}")

        # Add standard edit actions first
        edit_action_ids = {"copy", "paste", "cut", "delete"}
        for action_instance in action_instances:
            if action_instance.id in edit_action_ids:
                if action_instance.is_applicable(info):
                    qaction = QAction(
                        action_instance.icon, action_instance.text, info.parent_widget
                    )
                    qaction.setShortcut(action_instance.shortcut or QKeySequence())
                    qaction.setToolTip(action_instance.tooltip)
                    qaction.setEnabled(action_instance.is_enabled(info))
                    # Connect triggered signal to the action's execute method
                    qaction.triggered.connect(
                        lambda bound_action=action_instance: bound_action.execute(info)
                    )
                    menu.addAction(qaction)
                    created_qactions[action_instance.id] = qaction
                    needs_separator = True

        if needs_separator:
            menu.addSeparator()
            needs_separator = False

        # Add context-specific actions (Validation/Correction)
        context_action_ids = {"view_error", "apply_correction"}
        for action_instance in action_instances:
            if action_instance.id in context_action_ids:
                if action_instance.is_applicable(info):
                    qaction = QAction(
                        action_instance.icon, action_instance.text, info.parent_widget
                    )
                    qaction.setShortcut(action_instance.shortcut or QKeySequence())
                    qaction.setToolTip(action_instance.tooltip)
                    qaction.setEnabled(action_instance.is_enabled(info))
                    qaction.triggered.connect(
                        lambda bound_action=action_instance: bound_action.execute(info)
                    )
                    menu.addAction(qaction)
                    created_qactions[action_instance.id] = qaction
                    needs_separator = True  # Assume separator needed before next group

        # Add 'Add to List' actions
        # This grouping logic could be improved (e.g., define groups in actions)
        if needs_separator:
            menu.addSeparator()
            needs_separator = False

        list_action_ids = {"add_correction", "add_validation"}
        for action_instance in action_instances:
            if action_instance.id in list_action_ids:
                if action_instance.is_applicable(info):
                    qaction = QAction(
                        action_instance.icon, action_instance.text, info.parent_widget
                    )
                    qaction.setShortcut(action_instance.shortcut or QKeySequence())
                    qaction.setToolTip(action_instance.tooltip)
                    qaction.setEnabled(action_instance.is_enabled(info))
                    qaction.triggered.connect(
                        lambda bound_action=action_instance: bound_action.execute(info)
                    )
                    menu.addAction(qaction)
                    created_qactions[action_instance.id] = qaction
                    needs_separator = True

        return menu, created_qactions
