#!/usr/bin/env python3
"""
PhotoSift - Photo Management Tool
Entry point for the application.
"""

import sys
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from src.main_window import MainWindow


def main():
    """Main application entry point."""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("PhotoSift")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("PhotoSift")
    
    # Enable high DPI support for crisp images on retina displays
    # Note: High DPI scaling is enabled by default in PyQt6
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Start the application event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
