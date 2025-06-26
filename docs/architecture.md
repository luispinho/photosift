# Architecture & Development

## Tech Stack

- **Python** - Core application logic and file management
- **PyQt6** - Native GUI framework optimized for macOS
- **Pillow (PIL)** - Fast image processing and preview generation

## Project Structure

```
photosift/
├── main.py                    # Application entry point and launcher
├── launch.py                  # Alternative launcher script
├── src/
│   ├── __init__.py
│   ├── main_window.py         # Main UI, countdown system, action handling
│   ├── photo_manager.py       # Photo pairing, session persistence, file ops
│   └── preferences.py         # Settings and configuration
├── assets/                    # Application icons and resources
├── test_photos/              # Sample photos for testing
├── docs/                     # Documentation
├── requirements.txt          # Python dependencies
├── create_test_photos.py     # Utility to generate test photos
├── generate_icons.sh         # Icon generation script
└── README.md                # This documentation
```

## Key Components

**PhotoManager** - Handles photo file discovery, pairing (JPEG+RAW), and persistent session tracking. Manages file operations and maintains action history.

**MainWindow** - Core UI with modern dark theme, keyboard shortcuts, status indicators, and the integrated countdown confirmation system.

**CountdownWidget** - Smart confirmation system that provides safety for destructive actions without interrupting workflow. Includes progress bar and undo functionality.

**Session Persistence** - Actions and progress are automatically saved to `.photosift_session.json`, allowing photographers to resume culling sessions across application restarts.
