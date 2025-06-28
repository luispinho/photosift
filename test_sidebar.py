#!/usr/bin/env python3
"""
Test script to verify sidebar functionality
"""

import os
import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from photo_manager import PhotoManager, PhotoAction
from preferences import Preferences

def test_sidebar_data():
    """Test that sidebar has the correct data structure."""

    # Create a test folder and files
    test_folder = Path("test_sidebar")
    test_folder.mkdir(exist_ok=True)

    # Create some test files
    test_files = [
        "IMG_001.jpg", "IMG_001.CR2",
        "IMG_002.jpg", "IMG_002.CR2",
        "IMG_003.jpg", "IMG_003.CR2",
        "IMG_004.jpg", "IMG_004.CR2"
    ]

    for file_name in test_files:
        (test_folder / file_name).touch()

    # Create a session file with some actions
    session_data = {
        "folder_path": str(test_folder),
        "created": "2025-06-28T10:00:00",
        "last_updated": "2025-06-28T10:30:00",
        "actions": {
            "IMG_001": {
                "action": "keep_all",
                "timestamp": "2025-06-28T10:15:00"
            },
            "IMG_002": {
                "action": "delete_raw",
                "timestamp": "2025-06-28T10:20:00"
            },
            "IMG_003": {
                "action": "delete_all",
                "timestamp": "2025-06-28T10:25:00"
            }
            # IMG_004 has no action
        }
    }

    session_file = test_folder / ".photosift_session.json"
    with open(session_file, 'w') as f:
        json.dump(session_data, f, indent=2)

    # Test the photo manager data for sidebar
    preferences = Preferences()
    manager = PhotoManager(preferences)

    print("=== Testing Sidebar Data ===")
    print(f"Loading folder: {test_folder}")

    success = manager.load_folder(str(test_folder))
    if not success:
        print("Failed to load folder!")
        return False

    print(f"Loaded {len(manager.photo_pairs)} photos")

    # Test sidebar data requirements
    print("\n--- Photo List for Sidebar ---")
    for i, photo in enumerate(manager.photo_pairs):
        status = "JPEG+RAW" if photo.has_jpeg and photo.has_raw else "JPEG" if photo.has_jpeg else "RAW"
        print(f"{i+1}. {photo.base_name} [{status}] -> {photo.action.value}")

    # Test filtering functionality
    print("\n--- Filter Tests ---")

    # All photos
    all_photos = manager.photo_pairs
    print(f"All photos: {len(all_photos)}")

    # By action type
    unprocessed = manager.get_photos_by_action(PhotoAction.NONE)
    keep_all = manager.get_photos_by_action(PhotoAction.KEEP_ALL)
    delete_raw = manager.get_photos_by_action(PhotoAction.DELETE_RAW)
    delete_all = manager.get_photos_by_action(PhotoAction.DELETE_ALL)

    print(f"Unprocessed: {[p.base_name for p in unprocessed]}")
    print(f"Keep all: {[p.base_name for p in keep_all]}")
    print(f"Delete RAW: {[p.base_name for p in delete_raw]}")
    print(f"Delete all: {[p.base_name for p in delete_all]}")

    # Test current photo tracking
    print(f"\n--- Current Photo Tracking ---")
    current_photo = manager.get_current_photo()
    print(f"Current photo: {current_photo.base_name} (index {manager.current_index})")

    # Test navigation
    print("\n--- Navigation Test ---")
    for i in range(len(manager.photo_pairs)):
        manager.current_index = i
        current = manager.get_current_photo()
        print(f"Index {i}: {current.base_name} ({current.action.value})")

    # Test action summary
    summary = manager.get_action_summary()
    print(f"\n--- Action Summary ---")
    for action, count in summary.items():
        if count > 0:
            print(f"{action.value}: {count}")

    # Cleanup
    for file_name in test_files:
        (test_folder / file_name).unlink(missing_ok=True)
    session_file.unlink(missing_ok=True)
    test_folder.rmdir()

    print("\n✅ Sidebar data test completed successfully!")
    return True

if __name__ == "__main__":
    test_sidebar_data()
