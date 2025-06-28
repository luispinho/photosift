#!/usr/bin/env python3
"""
Test script to verify session resumption functionality
"""

import os
import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from photo_manager import PhotoManager, PhotoAction
from preferences import Preferences

def test_session_resumption():
    """Test that session resumption works correctly."""

    # Create a test folder and files
    test_folder = Path("test_session_resumption")
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
            }
            # IMG_003 and IMG_004 have no actions
        }
    }

    session_file = test_folder / ".photosift_session.json"
    with open(session_file, 'w') as f:
        json.dump(session_data, f, indent=2)

    # Test with session resumption enabled (default)
    print("=== Testing with session resumption ENABLED ===")
    preferences = Preferences()
    preferences.set_resume_session(True)

    manager = PhotoManager(preferences)

    print(f"Loading folder: {test_folder}")

    success = manager.load_folder(str(test_folder))
    if not success:
        print("Failed to load folder!")
        return False

    print(f"Loaded {len(manager.photo_pairs)} photos")

    # Check that current index points to first unprocessed photo (IMG_003)
    current_photo = manager.get_current_photo()
    print(f"Current photo: {current_photo.base_name}")
    print(f"Current index: {manager.current_index}")

    if current_photo.base_name != "IMG_003":
        print(f"ERROR: Expected current photo to be IMG_003, got {current_photo.base_name}")
        return False

    print("✅ Session resumption working correctly!\n")

    # Test with session resumption disabled
    print("=== Testing with session resumption DISABLED ===")
    preferences.set_resume_session(False)

    manager2 = PhotoManager(preferences)

    success = manager2.load_folder(str(test_folder))
    if not success:
        print("Failed to load folder!")
        return False

    current_photo2 = manager2.get_current_photo()
    print(f"Current photo: {current_photo2.base_name}")
    print(f"Current index: {manager2.current_index}")

    if current_photo2.base_name != "IMG_001":
        print(f"ERROR: Expected current photo to be IMG_001, got {current_photo2.base_name}")
        return False

    print("✅ Session resumption disabled working correctly!\n")

    # Get session progress
    processed, total, percentage = manager.get_session_progress()
    print(f"Session progress: {processed}/{total} ({percentage}%)")

    # Cleanup
    for file_name in test_files:
        (test_folder / file_name).unlink(missing_ok=True)
    session_file.unlink(missing_ok=True)
    test_folder.rmdir()

    print("All tests completed successfully!")
    return True

if __name__ == "__main__":
    test_session_resumption()
