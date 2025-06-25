#!/usr/bin/env python3
"""
PhotoSift Launcher
Cross-platform launcher script that handles virtual environment activation automatically.
"""

import os
import sys
import subprocess
from pathlib import Path


def main():
    # Get the directory where this script is located
    script_dir = Path(__file__).parent.absolute()
    
    # Change to the project directory
    os.chdir(script_dir)
    
    # Virtual environment paths
    venv_dir = script_dir / "venv"
    
    if sys.platform == "win32":
        venv_python = venv_dir / "Scripts" / "python.exe"
        activate_script = venv_dir / "Scripts" / "activate.bat"
    else:
        venv_python = venv_dir / "bin" / "python"
        activate_script = venv_dir / "bin" / "activate"
    
    # Check if virtual environment exists
    if not venv_dir.exists():
        print("Virtual environment not found. Creating one...")
        subprocess.run([sys.executable, "-m", "venv", "venv"])
        
        # Install requirements
        print("Installing requirements...")
        subprocess.run([str(venv_python), "-m", "pip", "install", "-r", "requirements.txt"])
    
    # Check if PhotoSift dependencies are installed
    try:
        result = subprocess.run([str(venv_python), "-c", "import PyQt6; import PIL"], 
                              capture_output=True, text=True)
        if result.returncode != 0:
            print("Installing/updating requirements...")
            subprocess.run([str(venv_python), "-m", "pip", "install", "-r", "requirements.txt"])
    except:
        print("Installing requirements...")
        subprocess.run([str(venv_python), "-m", "pip", "install", "-r", "requirements.txt"])
    
    # Launch PhotoSift
    print("Launching PhotoSift...")
    try:
        subprocess.run([str(venv_python), "main.py"])
    except KeyboardInterrupt:
        print("\nPhotoSift closed.")
    except Exception as e:
        print(f"Error launching PhotoSift: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
