def _init_defaults(self) -> None:
    """Initialize default configuration settings."""
    # Logging defaults
    self.set("Logging", "level", "DEBUG")  # Changed from INFO to DEBUG

    # Autosave defaults
    self.set("Autosave", "enabled", "True")
    self.set("Autosave", "interval_minutes", "5")

    # User preference defaults
    self.set("Preferences", "theme", "Light")
    self.set("Preferences", "font_size", "10")
    self.set("Preferences", "date_format", "%Y-%m-%d")

    # Chart defaults
    self.set("Charts", "default_chart_type", "line")
    self.set("Charts", "color_palette", "default")

    # CSV import defaults
    self.set("Import", "normalize_text", "True")
    self.set("Import", "robust_mode", "True")
    self.set("Import", "chunk_size", "100")
