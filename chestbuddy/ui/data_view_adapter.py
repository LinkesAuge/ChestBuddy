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
        logger.debug("DataViewAdapter._on_validation_changed called")
        
        # Get the validation status from the model to pass to the data view
        validation_status = None
        if hasattr(self._data_model, "get_validation_status"):
            try:
                validation_status = self._data_model.get_validation_status()
                logger.debug(f"DataViewAdapter got validation status of type: {type(validation_status)}")
                
                # If validation_status is a DataFrame, convert it to a more compatible format
                if isinstance(validation_status, pd.DataFrame) and not validation_status.empty:
                    logger.debug(f"Converting DataFrame to dictionary. Columns: {validation_status.columns.tolist()}")
                    
                    # Convert validation DataFrame to dictionary with proper structure
                    dict_status = {}
                    validation_columns = [col for col in validation_status.columns if col.endswith("_valid")]
                    
                    if validation_columns:
                        for idx in range(len(validation_status)):
                            row_dict = {}
                            row_has_validation = False
                            
                            for col in validation_columns:
                                if pd.notna(validation_status.iloc[idx].get(col, None)):
                                    row_dict[col] = bool(validation_status.iloc[idx][col])
                                    row_has_validation = True
                            
                            if row_has_validation:
                                dict_status[idx] = row_dict
                        
                        logger.debug(f"Converted validation status to dictionary with {len(dict_status)} rows")
                        validation_status = dict_status
            except Exception as e:
                logger.error(f"Error getting validation status: {e}", exc_info=True)
        
        # Make sure to update the underlying DataView with validation changes
        if hasattr(self._data_view, "_on_validation_changed"):
            try:
                logger.debug(f"Passing validation status to DataView: {type(validation_status)}")
                self._data_view._on_validation_changed(validation_status)
            except Exception as e:
                logger.error(f"Error updating DataView with validation status: {e}", exc_info=True)
        else:
            logger.warning("DataView does not have _on_validation_changed method")
        
        # Request update from the UpdateManager
        self.request_update()