from chestbuddy.core.table_state_manager import TableStateManager


@dataclasses.dataclass
class ActionContext:
    """Dataclass holding context for menu creation/action execution."""

    clicked_index: QModelIndex | None = None
    selection: typing.List[QModelIndex] | None = None
    model: DataViewModel | None = None
    parent_widget: QWidget | None = None
    state_manager: TableStateManager | None = None
    clipboard_text: str | None = None
    column_name: str | None = None


class AbstractContextAction:
    """Base class for all context menu actions."""
