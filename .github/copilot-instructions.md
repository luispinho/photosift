<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

# PhotoSift - Photo Management Tool

This is a Python application using PyQt6 for creating a photo culling tool for Canon DSLR photographers.

## Project Context

- **Target Platform**: macOS (but cross-platform compatible)
- **Main Purpose**: Quick photo culling/management for Canon DSLR files (JPEG + CR2)
- **UI Framework**: PyQt6 for native look and feel
- **Image Processing**: Pillow (PIL) for fast image preview

## Code Guidelines

- Follow PEP 8 style guidelines
- Use type hints for better code clarity
- Implement proper error handling for file operations
- Keep UI responsive with proper threading for file operations
- Use PyQt6 signals and slots for event handling
- Implement keyboard shortcuts using QShortcut
- Structure code with clear separation of concerns:
  - UI logic in main_window.py
  - File operations in photo_manager.py
  - Settings in preferences.py

## Key Features to Implement

- Fast JPEG preview display
- Keyboard shortcuts (K, R, D for keep-all, raw-delete, delete-all)
- File counter and navigation
- Confirmation dialogs (configurable)
- Support for JPEG and CR2 file pairs
- Automatic next file progression
- Preferences/settings window

## Performance Considerations

- Use QPixmap for efficient image display
- Implement image caching for smooth navigation
- Use QThread for file operations to keep UI responsive
- Optimize image loading with appropriate scaling
