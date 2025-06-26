#!/usr/bin/env python3
"""
Test script to verify deletion behavior
"""

import sys
from pathlib import Path
import tempfile
import shutil

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from photo_manager import PhotoManager, PhotoPair, PhotoAction


def create_test_files(temp_dir):
    """Create test files for testing deletion logic."""
    test_files = []

    # Create test JPEG and RAW pairs
    for i in range(3):
        jpeg_path = temp_dir / f"IMG_{i:04d}.jpg"
        raw_path = temp_dir / f"IMG_{i:04d}.CR2"

        # Create dummy files
        jpeg_path.write_text("dummy jpeg content")
        raw_path.write_text("dummy raw content")

        test_files.append((jpeg_path, raw_path))

    return test_files


def test_delete_both_files():
    """Test that deleting all files removes photo from list."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create test files
        test_files = create_test_files(temp_path)

        # Initialize photo manager
        pm = PhotoManager()
        success = pm.load_folder(str(temp_path))

        print(f"Folder loaded successfully: {success}")
        print(f"Initial photo count: {len(pm.photo_pairs)}")

        # Verify initial state
        assert len(pm.photo_pairs) == 3, f"Expected 3 photos, got {len(pm.photo_pairs)}"

        # Get the first photo and delete all files
        first_photo = pm.get_current_photo()
        print(f"First photo: {first_photo.base_name}")
        print(f"Has JPEG: {first_photo.has_jpeg}, Has RAW: {first_photo.has_raw}")

        # Delete all files for the first photo
        delete_success = pm.delete_both_files(first_photo)
        print(f"Delete operation successful: {delete_success}")

        # Verify photo was removed from list
        print(f"Photo count after deletion: {len(pm.photo_pairs)}")
        assert len(pm.photo_pairs) == 2, f"Expected 2 photos after deletion, got {len(pm.photo_pairs)}"

        # Verify current index is still valid
        current_photo = pm.get_current_photo()
        if current_photo:
            print(f"Current photo after deletion: {current_photo.base_name}")
            assert current_photo.has_jpeg or current_photo.has_raw, "Current photo should have files"
        else:
            print("No current photo (this is OK if list is empty)")

        print("✅ Test passed: Photo removed from list after deletion")


def test_delete_last_photo():
    """Test deleting the last photo in the list."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create only one test file pair
        jpeg_path = temp_path / "IMG_0001.jpg"
        raw_path = temp_path / "IMG_0001.CR2"
        jpeg_path.write_text("dummy jpeg content")
        raw_path.write_text("dummy raw content")

        # Initialize photo manager
        pm = PhotoManager()
        success = pm.load_folder(str(temp_path))

        print(f"Single photo loaded: {success}")
        print(f"Photo count: {len(pm.photo_pairs)}")

        # Delete the only photo
        photo = pm.get_current_photo()
        delete_success = pm.delete_both_files(photo)

        print(f"Delete last photo successful: {delete_success}")
        print(f"Photo count after deletion: {len(pm.photo_pairs)}")

        # Verify list is empty
        assert len(pm.photo_pairs) == 0, f"Expected empty list, got {len(pm.photo_pairs)}"

        # Verify current photo is None
        current_photo = pm.get_current_photo()
        assert current_photo is None, "Current photo should be None when list is empty"

        print("✅ Test passed: Last photo deletion handled correctly")


if __name__ == "__main__":
    print("Testing deletion logic...")
    test_delete_both_files()
    test_delete_last_photo()
    print("All tests passed! 🎉")
