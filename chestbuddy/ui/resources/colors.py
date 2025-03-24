"""
colors.py

Description: Re-exports the Colors class from style.py for backwards compatibility
Usage:
    Import this module to access the application color scheme.
"""

from chestbuddy.ui.resources.style import Colors as StyleColors


class Colors(StyleColors):
    """
    Color palette for the application.
    This class re-exports colors from the style.py module for backward compatibility.
    """

    # Add aliases for newer names used in various components
    BACKGROUND_LIGHT = StyleColors.BG_LIGHT
    BACKGROUND_DARK = StyleColors.BG_DARK
    BACKGROUND = StyleColors.BG_DARK
    BACKGROUND_LIGHT_HOVER = "#F1F3F5"  # Light background for cards on hover
    BACKGROUND_CARD = "#FFFFFF"  # White for card backgrounds

    TEXT_DARK = StyleColors.PRIMARY
    TEXT_MEDIUM = StyleColors.BG_MEDIUM
    TEXT_SECONDARY = "#6C757D"  # Secondary text

    DANGER = StyleColors.ERROR
    DANGER_DARK = "#C82333"  # Darker variant of ERROR/DANGER
    DANGER_DARKER = "#BD2130"  # Even darker variant of ERROR/DANGER

    # For primary color variations
    PRIMARY_DARK = StyleColors.PRIMARY_ACTIVE
    PRIMARY_DARKER = StyleColors.PRIMARY_ACTIVE

    # Border variations
    BORDER_LIGHT = StyleColors.BORDER

    # Additional UI elements
    LINK = "#4A90E2"  # Link color
    LINK_HOVER = "#5AA0F2"  # Link hover color

    # Extended variations of SECONDARY
    SECONDARY_DARK = StyleColors.SECONDARY_ACTIVE
    SECONDARY_DARKER = "#B38F17"  # Even darker variant of SECONDARY


# Re-export Colors for backward compatibility
__all__ = ["Colors"]
