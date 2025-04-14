# Placeholder type-specific actions
class FormatNumberAction(AbstractContextAction):
    """Action specific to numeric columns."""

    @property
    def id(self) -> str:
        return "format_number"

    @property
    def text(self) -> str:
        return "Format Number..."

    # Add icon property if desired

    def is_applicable(self, context: ActionContext) -> bool:
        # Only applicable if a single cell in a numeric column is clicked
        # Example: Check if column name suggests a number
        return (
            context.clicked_index is not None
            and context.column_name == "Amount"  # Example check
            and context.selection is not None
            and len(context.selection) == 1
        )

    def is_enabled(self, context: ActionContext) -> bool:
        # Could add more complex logic here if needed
        return True

    def execute(self, context: ActionContext) -> None:
        # Placeholder: Implement actual number formatting logic/dialog
        print(
            f"Executing Format Number for index: {context.clicked_index}, column: {context.column_name}"
        )
        pass


class ParseDateAction(AbstractContextAction):
    """Action specific to date columns."""

    @property
    def id(self) -> str:
        return "parse_date"

    @property
    def text(self) -> str:
        return "Parse Date..."

    # Add icon property if desired

    def is_applicable(self, context: ActionContext) -> bool:
        # Only applicable if a single cell in a date column is clicked
        # Example: Check if column name suggests a date
        return (
            context.clicked_index is not None
            and context.column_name == "Date"  # Example check
            and context.selection is not None
            and len(context.selection) == 1
        )

    def is_enabled(self, context: ActionContext) -> bool:
        return True

    def execute(self, context: ActionContext) -> None:
        # Placeholder: Implement actual date parsing logic/dialog
        print(
            f"Executing Parse Date for index: {context.clicked_index}, column: {context.column_name}"
        )
        pass


# Other actions (Copy, Paste, etc.) remain here...
