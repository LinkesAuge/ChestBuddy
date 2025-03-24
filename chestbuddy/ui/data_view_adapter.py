def needs_refresh(self) -> bool:
    """
    Check if the view needs refreshing based on data state.

    Returns:
        bool: True if the view needs to be refreshed, False otherwise
    """
    # Check if data has changed by comparing with our tracked state
    current_state = {"row_count": 0, "column_count": 0}

    if not self._data_model.is_empty:
        current_state = {
            "row_count": len(self._data_model.data),
            "column_count": len(self._data_model.column_names),
        }

    needs_refresh = (
        current_state["row_count"] != self._last_data_state["row_count"]
        or current_state["column_count"] != self._last_data_state["column_count"]
    )

    if needs_refresh:
        print(
            f"DataViewAdapter.needs_refresh: TRUE - Data changed. Old: {self._last_data_state}, New: {current_state}"
        )
    else:
        print(f"DataViewAdapter.needs_refresh: FALSE - No data changes detected")

    return needs_refresh


def refresh(self):
    """
    Refresh the data view only if the data has changed since the last refresh.
    This prevents unnecessary table repopulation when switching views.
    """
    # Use the needs_refresh method to check if we need to update
    if self.needs_refresh():
        print(f"DataViewAdapter.refresh: Data changed, updating view.")
        if hasattr(self._data_view, "_update_view"):
            self._data_view._update_view()

        # Update our state tracking
        self._update_data_state()
    else:
        print("DataViewAdapter.refresh: No data changes, skipping view update")
