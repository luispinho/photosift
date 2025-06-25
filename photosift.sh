#!/bin/bash

# PhotoSift Launch Script
# This script activates the virtual environment and launches PhotoSift

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Change to the project directory
cd "$SCRIPT_DIR"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Creating one..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    # Activate virtual environment
    source venv/bin/activate
fi

# Launch PhotoSift
echo "Launching PhotoSift..."
python main.py

# Deactivate virtual environment when done
deactivate
