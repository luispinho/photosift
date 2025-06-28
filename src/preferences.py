"""
Preferences - Application settings and configuration
"""

import json
from pathlib import Path
from typing import Dict, Any
from PyQt6.QtCore import QObject, pyqtSignal


class Preferences(QObject):
    """Manages application preferences and settings."""

    # Signals
    preferences_changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.settings_file = Path.home() / ".photosift_settings.json"
        self._settings: Dict[str, Any] = {}
        self._load_default_settings()
        self.load_settings()

    def _load_default_settings(self):
        """Load default application settings."""
        self._settings = {
            "confirm_deletions": True,
            "auto_advance": True,
            "resume_session": True,  # Auto-resume from first unprocessed photo
            "window_width": 1200,
            "window_height": 800,
            "last_folder": str(Path.home()),
            "image_quality": "high",  # high, medium, low
            "show_file_info": True,
            "keyboard_shortcuts": {
                "keep_all": "K",
                "delete_raw": "R",
                "delete_all": "D",
                "next_photo": "Right",
                "previous_photo": "Left"
            }
        }

    def load_settings(self):
        """Load settings from file."""
        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r') as f:
                    loaded_settings = json.load(f)
                    self._settings.update(loaded_settings)
        except Exception as e:
            print(f"Error loading settings: {e}")
            # Use defaults if loading fails

    def save_settings(self):
        """Save settings to file."""
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(self._settings, f, indent=2)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting value."""
        return self._settings.get(key, default)

    def set(self, key: str, value: Any):
        """Set a setting value."""
        if self._settings.get(key) != value:
            self._settings[key] = value
            self.save_settings()
            self.preferences_changed.emit()

    def get_confirm_deletions(self) -> bool:
        """Get deletion confirmation setting."""
        return self.get("confirm_deletions", True)

    def set_confirm_deletions(self, confirm: bool):
        """Set deletion confirmation setting."""
        self.set("confirm_deletions", confirm)

    def get_window_size(self) -> tuple:
        """Get window size setting."""
        return (
            self.get("window_width", 1200),
            self.get("window_height", 800)
        )

    def set_window_size(self, width: int, height: int):
        """Set window size setting."""
        self.set("window_width", width)
        self.set("window_height", height)

    def get_last_folder(self) -> str:
        """Get last opened folder."""
        return self.get("last_folder", str(Path.home()))

    def set_last_folder(self, folder: str):
        """Set last opened folder."""
        self.set("last_folder", folder)

    def get_resume_session(self) -> bool:
        """Get session resumption setting."""
        return self.get("resume_session", True)

    def set_resume_session(self, resume: bool):
        """Set session resumption setting."""
        self.set("resume_session", resume)
