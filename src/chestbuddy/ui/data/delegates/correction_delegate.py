    def helpEvent(
        self,
        event: QHelpEvent,
        view,  # QAbstractItemView
        option: QStyleOptionViewItem,
        index: QModelIndex,
    ):
        """Handles tooltip events to show detailed correction suggestions or validation errors."""
        handled = False # Flag to track if we showed a tooltip
        if event.type() == QHelpEvent.Type.ToolTip and index.isValid():
            suggestions = index.data(DataViewModel.CorrectionSuggestionsRole)
            if suggestions:
                tooltip_lines = ["Suggestions:"]
                for suggestion in suggestions:
                    # Check for attribute first, then dict, then fallback
                    if hasattr(suggestion, 'corrected_value'):
                        corrected_value = suggestion.corrected_value
                    elif isinstance(suggestion, dict):
                        corrected_value = suggestion.get('corrected_value', str(suggestion))
                    else:
                        corrected_value = str(suggestion) # Fallback
                    tooltip_lines.append(f"- {corrected_value}")
                
                tooltip_text = "\n".join(tooltip_lines)
                QToolTip.showText(event.globalPos(), tooltip_text, view)
                handled = True # We handled the event by showing a suggestion tooltip
            # else: 
                # No suggestions, fall through to let ValidationDelegate handle potential error tooltips below
                # We don't hide text here, as the base class might show an error tooltip
        
        # If we showed a suggestion tooltip, return True. 
        # Otherwise, let the base (ValidationDelegate) handle the event.
        if handled:
            return True
        else:
            # This allows ValidationDelegate's helpEvent to show error tooltips
            return super().helpEvent(event, view, option, index) 