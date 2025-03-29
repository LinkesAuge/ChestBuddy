"""
__main__.py

Description: Main entry point for the ChestBuddy application when run as a module.
Usage:
    python -m chestbuddy
"""

import sys
from chestbuddy.app import main

if __name__ == "__main__":
    sys.exit(main())
