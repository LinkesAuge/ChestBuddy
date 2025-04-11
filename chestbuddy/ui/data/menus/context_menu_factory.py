"""
context_menu_factory.py

Factory for creating context menus for the DataTableView.
"""

import typing
from dataclasses import dataclass

from PySide6.QtCore import QModelIndex, Qt
from PySide6.QtGui import QAction, QGuiApplication, QIcon
from PySide6.QtWidgets import QMenu, QWidget

# Placeholder imports - replace with actual paths
from ..models.data_view_model import DataViewModel  # Import real class
from chestbuddy.core.table_state_manager import CellState  # Import real enum
# DataViewModel = typing.NewType("DataViewModel", object)  # Placeholder type
# CellState = typing.NewType("CellState", object)


@dataclass
class ContextMenuInfo:
    """Information needed to build the context menu."""

    clicked_index: QModelIndex
    selection: typing.List[QModelIndex]
    model: typing.Optional[DataViewModel]
    parent_widget: QWidget
    # Add clipboard, table_state_manager if needed directly


class ContextMenuFactory:
    """
    Creates context menus for the DataTableView based on the provided context.
    """

    @staticmethod
    def create_context_menu(
        info: ContextMenuInfo,
    ) -> typing.Tuple[QMenu, typing.Dict[str, QAction]]:
        """
        Creates the appropriate QMenu based on the context information.

        Args:
            info: ContextMenuInfo containing details about the click and selection.

        Returns:
            A tuple containing the created QMenu and a dictionary of the created actions.
        """
        menu = QMenu(info.parent_widget)
        actions = {}

        if not info.model:
            return menu, actions  # Cannot build menu without model

        # --- Standard Edit Actions ---
        actions["copy"] = QAction(QIcon.fromTheme("edit-copy"), "Copy", info.parent_widget)
        actions["paste"] = QAction(QIcon.fromTheme("edit-paste"), "Paste", info.parent_widget)
        actions["cut"] = QAction(QIcon.fromTheme("edit-cut"), "Cut", info.parent_widget)
        actions["delete"] = QAction(QIcon.fromTheme("edit-delete"), "Delete", info.parent_widget)

        # --- Enable/Disable Logic ---
        clipboard = QGuiApplication.clipboard()
        has_selection = len(info.selection) > 0
        target_index = info.clicked_index  # Default target for paste/single actions
        if info.selection:
            # Use top-left of selection block if multiple items selected
            # Sorting might be needed if selection isn't guaranteed contiguous
            target_index = min(info.selection)

        paste_target_editable = False
        if target_index.isValid():
            paste_target_editable = bool(info.model.flags(target_index) & Qt.ItemIsEditable)

        selection_editable = False
        if has_selection:
            selection_editable = any(
                bool(info.model.flags(idx) & Qt.ItemIsEditable) for idx in info.selection
            )

        actions["copy"].setEnabled(has_selection)
        actions["paste"].setEnabled(clipboard and bool(clipboard.text()) and paste_target_editable)
        actions["cut"].setEnabled(has_selection and selection_editable)
        actions["delete"].setEnabled(has_selection and selection_editable)

        menu.addAction(actions["copy"])
        menu.addAction(actions["paste"])
        menu.addAction(actions["cut"])
        menu.addAction(actions["delete"])
        menu.addSeparator()

        # --- Context-Specific Actions (Validation/Correction) ---
        validation_state = None
        # correction_state = None # Placeholder
        if info.clicked_index.isValid():
            validation_state = info.model.data(
                info.clicked_index, DataViewModel.ValidationStateRole
            )
            print(
                f"Debug: Fetched validation_state for ({info.clicked_index.row()},{info.clicked_index.column()}): {validation_state} (Type: {type(validation_state)})"
            )  # Debug Print 1
            # correction_state = info.model.data(info.clicked_index, DataViewModel.CorrectionStateRole)

        # Compare with actual Enum values now
        if validation_state == CellState.INVALID:
            print("Debug: Condition validation_state == CellState.INVALID met.")  # Debug Print 2
            actions["view_error"] = QAction(
                QIcon.fromTheme("dialog-error"), "View Validation Error", info.parent_widget
            )
            menu.addAction(actions["view_error"])
            print(
                f"Debug: Added 'view_error' action. actions keys: {actions.keys()}"
            )  # Debug Print 3

        if validation_state == CellState.CORRECTABLE:
            print(
                "Debug: Condition validation_state == CellState.CORRECTABLE met."
            )  # Debug Print 4
            actions["apply_correction"] = QAction(
                QIcon.fromTheme("edit-fix"), "Apply Correction", info.parent_widget
            )
            menu.addAction(actions["apply_correction"])
            print(
                f"Debug: Added 'apply_correction' action. actions keys: {actions.keys()}"
            )  # Debug Print 5
            # TODO: Add submenu for multiple suggestions if needed

        # --- Add to List Actions ---
        menu.addSeparator()
        actions["add_correction"] = QAction("Add to Correction List (TODO)", info.parent_widget)
        actions["add_validation"] = QAction("Add to Validation List (TODO)", info.parent_widget)
        menu.addAction(actions["add_correction"])
        menu.addAction(actions["add_validation"])

        return menu, actions
