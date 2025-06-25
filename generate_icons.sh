#!/bin/bash
# Icon Generation Script for PhotoSift
# This script generates proper macOS icons using iconutil

# Check if iconutil is available (macOS only)
if ! command -v iconutil &> /dev/null; then
    echo "iconutil not found. This script requires macOS."
    exit 1
fi

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
ASSETS_DIR="$SCRIPT_DIR/assets"
SOURCE_ICON="$ASSETS_DIR/icon-512.png"

# Check if source icon exists
if [ ! -f "$SOURCE_ICON" ]; then
    echo "Error: Source icon not found at $SOURCE_ICON"
    exit 1
fi

echo "Generating icons from $SOURCE_ICON..."

# Create iconset directory
ICONSET_DIR="$ASSETS_DIR/PhotoSift.iconset"
mkdir -p "$ICONSET_DIR"

# Generate all required icon sizes for macOS
# Standard sizes
sips -z 16 16     "$SOURCE_ICON" --out "$ICONSET_DIR/icon_16x16.png"
sips -z 32 32     "$SOURCE_ICON" --out "$ICONSET_DIR/icon_16x16@2x.png"
sips -z 32 32     "$SOURCE_ICON" --out "$ICONSET_DIR/icon_32x32.png"
sips -z 64 64     "$SOURCE_ICON" --out "$ICONSET_DIR/icon_32x32@2x.png"
sips -z 128 128   "$SOURCE_ICON" --out "$ICONSET_DIR/icon_128x128.png"
sips -z 256 256   "$SOURCE_ICON" --out "$ICONSET_DIR/icon_128x128@2x.png"
sips -z 256 256   "$SOURCE_ICON" --out "$ICONSET_DIR/icon_256x256.png"
sips -z 512 512   "$SOURCE_ICON" --out "$ICONSET_DIR/icon_256x256@2x.png"
sips -z 512 512   "$SOURCE_ICON" --out "$ICONSET_DIR/icon_512x512.png"
cp "$SOURCE_ICON" "$ICONSET_DIR/icon_512x512@2x.png"

# Generate .icns file using iconutil
iconutil -c icns "$ICONSET_DIR" --output "$ASSETS_DIR/PhotoSift.icns"

if [ $? -eq 0 ]; then
    echo "Successfully generated PhotoSift.icns"
    
    # Also create individual PNG files for other platforms
    echo "Creating individual PNG files..."
    sips -z 16 16     "$SOURCE_ICON" --out "$ASSETS_DIR/icon-16.png"
    sips -z 20 20     "$SOURCE_ICON" --out "$ASSETS_DIR/icon-20.png"
    sips -z 24 24     "$SOURCE_ICON" --out "$ASSETS_DIR/icon-24.png"
    sips -z 32 32     "$SOURCE_ICON" --out "$ASSETS_DIR/icon-32.png"
    sips -z 48 48     "$SOURCE_ICON" --out "$ASSETS_DIR/icon-48.png"
    sips -z 64 64     "$SOURCE_ICON" --out "$ASSETS_DIR/icon-64.png"
    sips -z 128 128   "$SOURCE_ICON" --out "$ASSETS_DIR/icon-128.png"
    sips -z 256 256   "$SOURCE_ICON" --out "$ASSETS_DIR/icon-256.png"
    
    echo "Individual PNG files created successfully"
    
    # Clean up iconset directory
    rm -rf "$ICONSET_DIR"
    echo "Cleaned up temporary iconset directory"
    
    echo ""
    echo "Icon generation complete! Generated files:"
    echo "  - PhotoSift.icns (for macOS)"
    echo "  - icon-16.png through icon-256.png (for all platforms)"
    echo "  - Original icon-512.png (preserved)"
else
    echo "Error: Failed to generate .icns file"
    rm -rf "$ICONSET_DIR"
    exit 1
fi
