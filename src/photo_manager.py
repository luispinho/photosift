"""
Photo Manager - Handles file operations and photo metadata
"""

import os
import json
from pathlib import Path
from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
from PyQt6.QtCore import QObject, pyqtSignal


class PhotoAction(Enum):
    """Enum for different actions taken on photos."""
    NONE = "none"
    KEEP_ALL = "keep_all"
    DELETE_RAW = "delete_raw"
    DELETE_ALL = "delete_all"
    SKIPPED = "skipped"


@dataclass
class PhotoPair:
    """Represents a photo with its associated files."""
    base_name: str
    jpeg_path: Optional[Path] = None
    raw_path: Optional[Path] = None
    action: PhotoAction = PhotoAction.NONE
    action_timestamp: Optional[datetime] = None

    @property
    def has_jpeg(self) -> bool:
        """Check if JPEG file exists."""
        return self.jpeg_path is not None and self.jpeg_path.exists()

    @property
    def has_raw(self) -> bool:
        """Check if RAW file exists."""
        return self.raw_path is not None and self.raw_path.exists()

    @property
    def display_path(self) -> Optional[Path]:
        """Return the path for preview display (prefer JPEG)."""
        if self.has_jpeg:
            return self.jpeg_path
        if self.has_raw:
            return self.raw_path
        return None

    @property
    def file_status(self) -> str:
        """Return status string for UI display."""
        if self.has_jpeg and self.has_raw:
            return "JPEG + RAW"
        elif self.has_jpeg:
            return "JPEG only"
        elif self.has_raw:
            return "RAW only"
        return "No files"

    @property
    def has_action(self) -> bool:
        """Check if any action has been taken on this photo."""
        return self.action != PhotoAction.NONE

    def set_action(self, action: PhotoAction):
        """Set the action taken on this photo."""
        self.action = action
        self.action_timestamp = datetime.now()


class PhotoManager(QObject):
    """Manages photo files and operations."""

    # Signals
    photos_loaded = pyqtSignal(int)  # Emits number of photos loaded
    photo_deleted = pyqtSignal(str)  # Emits photo name that was deleted
    error_occurred = pyqtSignal(str)  # Emits error message
    session_updated = pyqtSignal()  # Emits when session data changes

    # Supported file extensions
    JPEG_EXTENSIONS = {'.jpg', '.jpeg', '.JPG', '.JPEG'}
    RAW_EXTENSIONS = {'.cr2', '.CR2', '.cr3', '.CR3'}
    SESSION_FILE = '.photosift_session.json'

    def __init__(self, preferences=None):
        super().__init__()
        self.preferences = preferences
        self.current_folder: Optional[Path] = None
        self.photo_pairs: List[PhotoPair] = []
        self.current_index = 0
        self.session_data: Dict = {}

    def load_folder(self, folder_path: str) -> bool:
        """Load photos from a folder."""
        try:
            self.current_folder = Path(folder_path)
            if not self.current_folder.exists() or not self.current_folder.is_dir():
                self.error_occurred.emit(f"Invalid folder: {folder_path}")
                return False

            # Load existing session data
            self._load_session_data()

            # Scan for photo files
            self._scan_photos()

            # Set current index to first unprocessed photo for session resumption
            self._set_resume_index()

            # Emit signal with count after resume index is set
            self.photos_loaded.emit(len(self.photo_pairs))

            return True

        except Exception as e:
            self.error_occurred.emit(f"Error loading folder: {str(e)}")
            return False

    def _scan_photos(self):
        """Scan folder for photo files and pair them."""
        if not self.current_folder:
            return

        # Dictionary to group files by base name
        file_groups: Dict[str, PhotoPair] = {}

        # Scan all files in the folder
        for file_path in self.current_folder.iterdir():
            if file_path.is_file():
                base_name = file_path.stem
                extension = file_path.suffix

                # Initialize photo pair if not exists
                if base_name not in file_groups:
                    file_groups[base_name] = PhotoPair(base_name=base_name)

                # Assign file to appropriate category
                if extension in self.JPEG_EXTENSIONS:
                    file_groups[base_name].jpeg_path = file_path
                elif extension in self.RAW_EXTENSIONS:
                    file_groups[base_name].raw_path = file_path

        # Filter out pairs with no supported files and sort by name
        self.photo_pairs = [
            pair for pair in file_groups.values()
            if pair.has_jpeg or pair.has_raw
        ]
        self.photo_pairs.sort(key=lambda x: x.base_name.lower())

        # Apply session data to restored photos
        self._apply_session_data()

        # Note: Signal emission moved to load_folder after _set_resume_index()

    def get_current_photo(self) -> Optional[PhotoPair]:
        """Get current photo pair."""
        if not self.photo_pairs or self.current_index >= len(self.photo_pairs):
            return None
        return self.photo_pairs[self.current_index]

    def get_photo_count(self) -> Tuple[int, int]:
        """Return (current_index + 1, total_count) for display."""
        if not self.photo_pairs:
            return (0, 0)
        return (self.current_index + 1, len(self.photo_pairs))

    def move_to_next(self) -> bool:
        """Move to next photo. Returns True if successful."""
        if self.current_index < len(self.photo_pairs) - 1:
            self.current_index += 1
            return True
        return False

    def move_to_previous(self) -> bool:
        """Move to previous photo. Returns True if successful."""
        if self.current_index > 0:
            self.current_index -= 1
            return True
        return False

    def delete_jpeg_only(self, photo_pair: PhotoPair) -> bool:
        """Delete only the JPEG file."""
        try:
            if photo_pair.has_jpeg:
                photo_pair.jpeg_path.unlink()
                photo_pair.jpeg_path = None
                return True
            return False
        except Exception as e:
            self.error_occurred.emit(f"Error deleting JPEG: {str(e)}")
            return False

    def delete_raw_only(self, photo_pair: PhotoPair) -> bool:
        """Delete only the RAW file."""
        try:
            if photo_pair.has_raw:
                photo_pair.raw_path.unlink()
                photo_pair.raw_path = None
                photo_pair.set_action(PhotoAction.DELETE_RAW)
                self._save_session_data()
                self.session_updated.emit()
                return True
            return False
        except Exception as e:
            self.error_occurred.emit(f"Error deleting RAW: {str(e)}")
            return False

    def delete_both_files(self, photo_pair: PhotoPair) -> bool:
        """Delete both JPEG and RAW files and remove from list."""
        success = True

        try:
            if photo_pair.has_jpeg:
                photo_pair.jpeg_path.unlink()
                photo_pair.jpeg_path = None

            if photo_pair.has_raw:
                photo_pair.raw_path.unlink()
                photo_pair.raw_path = None

            photo_pair.set_action(PhotoAction.DELETE_ALL)

            # Remove the photo from the list immediately after deletion
            if photo_pair in self.photo_pairs:
                index = self.photo_pairs.index(photo_pair)
                self.photo_pairs.remove(photo_pair)

                # Adjust current index if necessary
                if not self.photo_pairs:
                    # List is now empty
                    self.current_index = 0
                elif index < self.current_index:
                    # Removed photo was before current, decrease index
                    self.current_index -= 1
                elif index == self.current_index:
                    # Removed current photo, adjust to stay in bounds
                    if self.current_index >= len(self.photo_pairs):
                        self.current_index = len(self.photo_pairs) - 1

                self.photo_deleted.emit(photo_pair.base_name)

            self._save_session_data()
            self.session_updated.emit()

        except Exception as e:
            self.error_occurred.emit(f"Error deleting files: {str(e)}")
            success = False

        return success

    def keep_both_files(self, photo_pair: PhotoPair) -> bool:
        """Keep both files (mark as processed)."""
        photo_pair.set_action(PhotoAction.KEEP_ALL)
        self._save_session_data()
        self.session_updated.emit()
        return True

    def _load_session_data(self):
        """Load session data from JSON file."""
        session_file = self.current_folder / self.SESSION_FILE
        self.session_data = {}

        if session_file.exists():
            try:
                with open(session_file, 'r') as f:
                    data = json.load(f)
                    self.session_data = data.get('actions', {})
            except Exception as e:
                print(f"Warning: Could not load session data: {e}")

    def _save_session_data(self):
        """Save session data to JSON file."""
        if not self.current_folder:
            return

        session_file = self.current_folder / self.SESSION_FILE

        try:
            # Prepare session data
            session_info = {
                'folder_path': str(self.current_folder),
                'created': datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat(),
                'actions': {}
            }

            # Save actions for each photo
            for photo in self.photo_pairs:
                if photo.has_action:
                    session_info['actions'][photo.base_name] = {
                        'action': photo.action.value,
                        'timestamp': photo.action_timestamp.isoformat() if photo.action_timestamp else None
                    }

            with open(session_file, 'w') as f:
                json.dump(session_info, f, indent=2)

        except Exception as e:
            print(f"Warning: Could not save session data: {e}")

    def _apply_session_data(self):
        """Apply loaded session data to photo pairs."""
        for photo in self.photo_pairs:
            if photo.base_name in self.session_data:
                action_data = self.session_data[photo.base_name]
                try:
                    photo.action = PhotoAction(action_data['action'])
                    if action_data.get('timestamp'):
                        photo.action_timestamp = datetime.fromisoformat(action_data['timestamp'])
                except (ValueError, KeyError):
                    # Invalid action data, skip
                    pass

    def has_existing_session(self) -> bool:
        """Check if the current folder has an existing session file."""
        if not self.current_folder:
            return False
        session_file = self.current_folder / self.SESSION_FILE
        return session_file.exists()

    def get_resume_info(self) -> Optional[dict]:
        """Get information about session resumption."""
        if not self.photo_pairs:
            return None

        processed_count = sum(1 for photo in self.photo_pairs if photo.has_action)
        total_count = len(self.photo_pairs)
        current_photo = self.get_current_photo()

        if processed_count > 0 and current_photo and not current_photo.has_action:
            return {
                'processed': processed_count,
                'total': total_count,
                'current_photo': current_photo.base_name,
                'current_index': self.current_index + 1
            }
        return None

    def _set_resume_index(self):
        """Set current index to the first photo without an action for session resumption."""
        if not self.photo_pairs:
            self.current_index = 0
            return

        # Check if session resumption is enabled in preferences
        if self.preferences and not self.preferences.get_resume_session():
            self.current_index = 0
            return

        # Find the first photo without an action
        for i, photo in enumerate(self.photo_pairs):
            if not photo.has_action:
                self.current_index = i
                return

        # If all photos have actions, stay at the beginning
        self.current_index = 0

    def get_session_progress(self) -> Tuple[int, int, int]:
        """Get session progress: (processed, total, percentage)."""
        if not self.photo_pairs:
            return 0, 0, 0

        processed = sum(1 for photo in self.photo_pairs if photo.has_action)
        total = len(self.photo_pairs)
        percentage = int((processed / total) * 100) if total > 0 else 0

        return processed, total, percentage

    def get_photos_by_action(self, action: PhotoAction) -> List[PhotoPair]:
        """Get all photos with a specific action."""
        return [photo for photo in self.photo_pairs if photo.action == action]

    def get_unprocessed_photos(self) -> List[PhotoPair]:
        """Get all photos that haven't been processed yet."""
        return self.get_photos_by_action(PhotoAction.NONE)

    def get_next_unprocessed_index(self, from_index: int = None) -> Optional[int]:
        """Get the index of the next unprocessed photo from the given index."""
        if not self.photo_pairs:
            return None

        start_index = from_index if from_index is not None else self.current_index

        # Search from the given index forward
        for i in range(start_index, len(self.photo_pairs)):
            if not self.photo_pairs[i].has_action:
                return i

        # Search from the beginning to the given index
        for i in range(0, start_index):
            if not self.photo_pairs[i].has_action:
                return i

        return None  # No unprocessed photos found

    def jump_to_next_unprocessed(self) -> bool:
        """Jump to the next unprocessed photo. Returns True if found."""
        next_index = self.get_next_unprocessed_index(self.current_index + 1)
        if next_index is not None:
            self.current_index = next_index
            return True
        return False

    def get_action_summary(self) -> Dict[PhotoAction, int]:
        """Get summary of actions taken."""
        summary = {action: 0 for action in PhotoAction}
        for photo in self.photo_pairs:
            summary[photo.action] += 1
        return summary
