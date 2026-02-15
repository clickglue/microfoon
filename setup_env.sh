#!/bin/bash

# Define the virtual environment directory
VENV_DIR="venv"

# Check if venv exists
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv $VENV_DIR
else
    echo "Virtual environment already exists."
fi

# Activate the virtual environment
source $VENV_DIR/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies from pyproject.toml
# We use pip to install the package in editable mode or just dependencies
echo "Installing dependencies..."
pip install -e .

echo "Setup complete. To activate the virtual environment, run: source venv/bin/activate"
