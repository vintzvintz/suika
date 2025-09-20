#!/bin/bash

# Suika Game launcher script
# This script activates the virtual environment and launches the game

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check if virtual environment exists
if [ ! -d "$SCRIPT_DIR/venv" ]; then
    echo "Error: Virtual environment not found at $SCRIPT_DIR/venv"
    echo "Please run: python -m venv venv && source venv/bin/activate && pip install -e ."
    exit 1
fi

# Activate virtual environment and run the game
echo "Activating virtual environment and launching Suika Game..."
source "$SCRIPT_DIR/venv/bin/activate"

# Check if the package is installed
if ! command -v suika &> /dev/null; then
    echo "Suika game not found. Installing package..."
    pip install -e "$SCRIPT_DIR"
fi

# Launch the game
exec suika