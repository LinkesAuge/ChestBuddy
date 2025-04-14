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
from ..actions.edit_actions import (
    CopyAction,
    PasteAction,
    CutAction,
    DeleteAction,
    EditCellAction,
    ShowEditDialogAction,
)

# Import future action classes here
from ..actions.validation_actions import ViewErrorAction  # Import real action
from ..actions.correction_actions import (
    ApplyCorrectionAction,
    BatchApplyCorrectionAction,
)  # Import real action

# Import AddToCorrectionListAction from correct path
from ..actions.correction_actions import AddToCorrectionListAction

# Import real ActionContext
from ..context.action_context import ActionContext


# --- Remove Placeholder Actions ---

# class AddToCorrectionListAction(AbstractContextAction):
#     @property
#     def id(self) -> str:
#         return "add_correction"
#
#     @property
#     def text(self) -> str:
#         return "Add to Correction List (TODO)"
#
#     def is_applicable(self, context: ActionContext) -> bool:
#         return True  # Always show for now
#
#     def is_enabled(self, context: ActionContext) -> bool:
#         return len(context.selection) > 0  # Enable if selection exists
#
#     def execute(self, context: ActionContext) -> None:
#         print(f"TODO: Execute {self.id}")


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
        EditCellAction,
        ShowEditDialogAction,
        # Separator needed here
        ViewErrorAction,
        ApplyCorrectionAction,
        # Separator needed here
        AddToCorrectionListAction,
        # Batch Actions
        BatchApplyCorrectionAction,
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
        # These are generally applicable regardless of selection count
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

        # Add Direct/Dialog Edit Actions
        # Applicable only for single cell selection (usually)
        edit_action_ids = {"edit_cell", "show_edit_dialog"}
        for action_instance in action_instances:
            if action_instance.id in edit_action_ids:
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
                    needs_separator = True  # Separator before next group

        if needs_separator:
            menu.addSeparator()
            needs_separator = False

        # Add cell-type specific actions (only if single cell selected)
        if info.clicked_index.isValid() and len(info.selection) <= 1:
            col_index = info.clicked_index.column()
            column_name = str(info.model.headerData(col_index, Qt.Horizontal))

            if "date" in column_name.lower():
                # Placeholder for Date formatting actions
                date_format_action = QAction(f"Format Date ({column_name})...", info.parent_widget)
                date_format_action.setEnabled(False)  # Placeholder - not implemented
                menu.addAction(date_format_action)
                needs_separator = True

            if "score" in column_name.lower() or "value" in column_name.lower():  # Example check
                # Placeholder for Number formatting actions
                number_format_action = QAction(
                    f"Number Format ({column_name})...", info.parent_widget
                )
                number_format_action.setEnabled(False)  # Placeholder - not implemented
                menu.addAction(number_format_action)
                needs_separator = True

        if needs_separator:
            menu.addSeparator()
            needs_separator = False

        # Add context-specific actions (Validation/Correction)
        # Applicability might depend on single cell state
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
        # Applicability might depend on selection count (e.g., enable batch add for >1)
        list_action_ids = {"add_correction"}
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

        # Add Batch Actions submenu or directly
        batch_action_ids = {"batch_apply_correction"}
        has_batch_actions = False

        for action_instance in action_instances:
            if action_instance.id in batch_action_ids:
                if action_instance.is_applicable(info):
                    has_batch_actions = True
                    break

        if has_batch_actions:
            if needs_separator:
                menu.addSeparator()
                needs_separator = False

            # Create batch actions section
            batch_menu = QMenu("Batch Operations", menu)
            for action_instance in action_instances:
                if action_instance.id in batch_action_ids:
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
                        batch_menu.addAction(qaction)
                        created_qactions[action_instance.id] = qaction

            # Only add the submenu if it has actions
            if not batch_menu.isEmpty():
                menu.addMenu(batch_menu)

        return menu, created_qactions
