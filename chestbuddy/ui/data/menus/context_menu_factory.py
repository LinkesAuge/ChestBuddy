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
    AddToCorrectionListAction,
    PreviewCorrectionAction,
)

# Import AddToCorrectionListAction from correct path
# from ..actions.correction_actions import AddToCorrectionListAction # Already imported above

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
        PreviewCorrectionAction,
        # Separator needed here
        AddToCorrectionListAction,
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
                        lambda checked=False, bound_action=action_instance: bound_action.execute(
                            info
                        )
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
                        lambda checked=False, bound_action=action_instance: bound_action.execute(
                            info
                        )
                    )
                    menu.addAction(qaction)
                    created_qactions[action_instance.id] = qaction
                    needs_separator = True  # Separator before next group

        if needs_separator:
            menu.addSeparator()
            needs_separator = False

        # --- Add Cell-Type Specific Actions (Refined) --- #
        # Add these actions only if a single cell is clicked/selected
        if info.clicked_index.isValid() and len(info.selection) <= 1:
            # Try getting data with DisplayRole as fallback if EditRole is None
            clicked_data = info.clicked_index.data(Qt.EditRole)
            if clicked_data is None:
                clicked_data = info.clicked_index.data(Qt.DisplayRole)

            col_index = info.clicked_index.column()
            # Ensure model and headerData are valid before calling
            column_name = "Unknown Column"
            if info.model and hasattr(info.model, "headerData"):
                header_result = info.model.headerData(col_index, Qt.Horizontal, Qt.DisplayRole)
                if header_result is not None:
                    column_name = str(header_result)

            data_type_detected = False

            # --- DEBUG --- #
            print(
                f"ContextMenuFactory: Clicked Data='{clicked_data}', Type={type(clicked_data)}, ColName='{column_name}'"
            )
            # ------------- #

            # 1. Check for Numeric Types
            if isinstance(clicked_data, (int, float)):
                numeric_action = QAction(
                    f"Numeric Options for '{column_name}'...", info.parent_widget
                )
                numeric_action.setToolTip(
                    "Actions specific to numeric cells (e.g., formatting, range check) - Not Implemented"
                )
                numeric_action.setEnabled(False)
                menu.addAction(numeric_action)
                needs_separator = True
                data_type_detected = True

            # 2. Check for potential Date/Time (heuristic based on column name for now)
            # TODO: Improve date detection (check type if data model uses QDateTime/datetime)
            elif "date" in column_name.lower():
                date_action = QAction(f"Date Options for '{column_name}'...", info.parent_widget)
                date_action.setToolTip(
                    "Actions specific to date cells (e.g., formatting, calendar popup) - Not Implemented"
                )
                date_action.setEnabled(False)
                menu.addAction(date_action)
                needs_separator = True
                data_type_detected = True

            # 3. Default to String Type Actions (or add more specific checks)
            elif isinstance(clicked_data, str) or not data_type_detected:
                string_action = QAction(f"Text Options for '{column_name}'...", info.parent_widget)
                string_action.setToolTip(
                    "Actions specific to text cells (e.g., case change, length check) - Not Implemented"
                )
                string_action.setEnabled(False)
                menu.addAction(string_action)
                needs_separator = True
                data_type_detected = True  # Assume string if nothing else matches

            # Add separator if type-specific actions were added
            if needs_separator:
                menu.addSeparator()
                needs_separator = False
        # --- End Cell-Type Specific Actions --- #

        # Add context-specific actions (Validation/Correction)
        # Applicability might depend on single cell state
        context_action_ids = {"view_error", "apply_correction", "preview_correction"}
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
                        lambda checked=False, bound_action=action_instance: bound_action.execute(
                            info
                        )
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
                        lambda checked=False, bound_action=action_instance: bound_action.execute(
                            info
                        )
                    )
                    menu.addAction(qaction)
                    created_qactions[action_instance.id] = qaction
                    needs_separator = True

        return menu, created_qactions
