def _on_csv_load_success(self, data):
        """Handle successful CSV data loading."""
        self.logger.info(f"CSV load completed successfully with {len(data):,} rows")
        
        # FIRST show a "Processing data" message
        processing_message = f"Processing {len(data):,} rows of data..."
        self.load_progress.emit("", 100, 100)  # Keep progress at 100%
        self.load_finished.emit(processing_message)

        # Important - allow UI to update before heavy processing
        QApplication.processEvents()
        
        # THEN update the data model (potentially expensive operation)
        mapped_data = self._map_columns(data)
        self._data_model.update_data(mapped_data)

        # FINALLY emit the success signal with accurate count
        final_message = f"Successfully loaded {len(data):,} rows of data"
        self.load_success.emit(final_message)
        
        # Reset the background worker to free memory
        self._background_worker = None
