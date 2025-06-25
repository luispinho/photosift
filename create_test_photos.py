#!/usr/bin/env python3
"""
Test script to create sample photo files for testing the PhotoSift application.
"""

import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


def create_sample_photos(output_dir: str, count: int = 5):
    """Create sample JPEG and CR2 files for testing."""
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # Create sample JPEG files
    for i in range(1, count + 1):
        # Create a simple test image
        img = Image.new('RGB', (800, 600), color=(100 + i * 30, 150 + i * 20, 200 + i * 10))
        draw = ImageDraw.Draw(img)
        
        # Add some text to identify the image
        try:
            # Try to load a font, fallback to default if not available
            font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 36)
        except:
            font = ImageFont.load_default()
        
        text = f"Test Photo {i:03d}"
        
        # Calculate text position (center)
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (800 - text_width) // 2
        y = (600 - text_height) // 2
        
        draw.text((x, y), text, fill=(255, 255, 255), font=font)
        
        # Save JPEG file
        jpeg_name = f"IMG_{i:04d}.jpg"
        img.save(output_path / jpeg_name, 'JPEG', quality=95)
        
        # Create a dummy CR2 file (just a copy with different extension)
        # In real usage, these would be actual RAW files
        cr2_name = f"IMG_{i:04d}.CR2"
        with open(output_path / cr2_name, 'wb') as f:
            f.write(b"DUMMY_CR2_FILE_FOR_TESTING_" + str(i).encode() * 100)
        
        print(f"Created {jpeg_name} and {cr2_name}")
    
    # Create some JPEG-only files
    for i in range(count + 1, count + 3):
        img = Image.new('RGB', (800, 600), color=(200, 100, 150))
        draw = ImageDraw.Draw(img)
        
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 36)
        except:
            font = ImageFont.load_default()
        
        text = f"JPEG Only {i:03d}"
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (800 - text_width) // 2
        y = (600 - text_height) // 2
        
        draw.text((x, y), text, fill=(255, 255, 255), font=font)
        
        jpeg_name = f"IMG_{i:04d}.jpg"
        img.save(output_path / jpeg_name, 'JPEG', quality=95)
        print(f"Created {jpeg_name} (JPEG only)")
    
    print(f"\nCreated {count + 2} test photos in {output_path}")
    print(f"- {count} JPEG + CR2 pairs")
    print(f"- 2 JPEG-only files")
    print("\nYou can now test the PhotoSift application with these files!")


if __name__ == "__main__":
    # Create test photos in a 'test_photos' directory
    test_dir = Path(__file__).parent / "test_photos"
    create_sample_photos(str(test_dir))
