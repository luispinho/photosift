# PhotoSift - Photo Management Tool

<img src="assets/icon-128.png" align="right"
     alt="Size Limit logo by Anton Lovchikov" width="128" height="128">

A fast and lightweight photo management application for Canon DSLR files, designed to help photographers quickly cull through their photos and decide which files to keep or delete.

## Features

- Preview JPEG images from Canon DSLR cameras
- Handle both JPEG and CR2 (RAW) files
- Quick keyboard shortcuts for file management:
  - `K` - Keep both JPEG and RAW files
  - `R` - Delete RAW file, keep JPEG
  - `D` - Delete both files
- File counter showing current position and total files
- Automatic progression to next file after action
- Confirmation dialogs for file deletion (configurable)
- Clean, intuitive interface optimized for macOS

## Requirements

- Python 3.8 or higher
- PyQt6
- Pillow (PIL)

## Installation

1. Clone this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Run the application:
   ```bash
   python main.py
   ```

2. Open a folder containing your Canon DSLR photos
3. Use keyboard shortcuts or click buttons to manage your photos

## Tech Stack

- **Python** - Core application logic
- **PyQt6** - GUI framework for native macOS interface
- **Pillow** - Image processing and preview generation

## Project Structure

```
photosift/
├── main.py              # Application entry point
├── src/
│   ├── __init__.py
│   ├── main_window.py   # Main application window
│   ├── photo_manager.py # Photo file management logic
│   └── preferences.py   # Settings and preferences
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## License

GNU General Public License v3.0 - See LICENSE file for details
