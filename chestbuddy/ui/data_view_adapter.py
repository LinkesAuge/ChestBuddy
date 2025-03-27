    def _connect_model_signals(self):
        """Connect to data model signals using signal manager."""
        try:
            # Connect to data_changed signal for automatic updates
            self._signal_manager.safe_connect(
                self._data_model, "data_changed", self, "_on_data_changed"
            )
            
            # Connect to validation_changed signal for validation updates
            self._signal_manager.safe_connect(
                self._data_model, "validation_changed", self, "_on_validation_changed"
            )
            
            logger.debug("DataViewAdapter: Connected to data model signals")
        except Exception as e:
            logger.error(f"Error connecting to data model signals: {e}")
            
    def _on_validation_changed(self):
        """Handle validation status changes in the data model."""
        # Make sure to update the underlying DataView with validation changes
        if hasattr(self._data_view, "_on_validation_changed"):
            self._data_view._on_validation_changed()
        
        # Request update from the UpdateManager
        self.request_update() 