"""
Photo Manager - Handles file operations and photo metadata
"""

import os
from pathlib import Path
from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass
from PyQt6.QtCore import QObject, pyqtSignal


@dataclass
class PhotoPair:
    """Represents a photo with its associated files."""
    base_name: str
    jpeg_path: Optional[Path] = None
    raw_path: Optional[Path] = None
    
    @property
    def has_jpeg(self) -> bool:
        """Check if JPEG file exists."""
        return self.jpeg_path is not None and self.jpeg_path.exists()
    
    @property
    def has_raw(self) -> bool:
        """Check if RAW file exists."""
        return self.raw_path is not None and self.raw_path.exists()
    
    @property
    def display_path(self) -> Path:
        """Return the path for preview display (prefer JPEG)."""
        if self.has_jpeg:
            return self.jpeg_path
        return self.raw_path
    
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


class PhotoManager(QObject):
    """Manages photo files and operations."""
    
    # Signals
    photos_loaded = pyqtSignal(int)  # Emits number of photos loaded
    photo_deleted = pyqtSignal(str)  # Emits photo name that was deleted
    error_occurred = pyqtSignal(str)  # Emits error message
    
    # Supported file extensions
    JPEG_EXTENSIONS = {'.jpg', '.jpeg', '.JPG', '.JPEG'}
    RAW_EXTENSIONS = {'.cr2', '.CR2', '.cr3', '.CR3'}
    
    def __init__(self):
        super().__init__()
        self.current_folder: Optional[Path] = None
        self.photo_pairs: List[PhotoPair] = []
        self.current_index = 0
    
    def load_folder(self, folder_path: str) -> bool:
        """Load photos from a folder."""
        try:
            self.current_folder = Path(folder_path)
            if not self.current_folder.exists() or not self.current_folder.is_dir():
                self.error_occurred.emit(f"Invalid folder: {folder_path}")
                return False
            
            # Scan for photo files
            self._scan_photos()
            self.current_index = 0
            
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
                return True
            return False
        except Exception as e:
            self.error_occurred.emit(f"Error deleting RAW: {str(e)}")
            return False
    
    def delete_both_files(self, photo_pair: PhotoPair) -> bool:
        """Delete both JPEG and RAW files."""
        success = True
        
        try:
            if photo_pair.has_jpeg:
                photo_pair.jpeg_path.unlink()
                photo_pair.jpeg_path = None
            
            if photo_pair.has_raw:
                photo_pair.raw_path.unlink()
                photo_pair.raw_path = None
                
        except Exception as e:
            self.error_occurred.emit(f"Error deleting files: {str(e)}")
            success = False
        
        return success
    
    def keep_both_files(self, photo_pair: PhotoPair) -> bool:
        """Keep both files (no-op, just for completeness)."""
        return True
    
    def remove_current_photo_from_list(self):
        """Remove current photo from the list after deletion."""
        if self.photo_pairs and self.current_index < len(self.photo_pairs):
            removed_photo = self.photo_pairs.pop(self.current_index)
            
            # Adjust index if we're at the end
            if self.current_index >= len(self.photo_pairs) and self.photo_pairs:
                self.current_index = len(self.photo_pairs) - 1
            
            self.photo_deleted.emit(removed_photo.base_name)
