#!/bin/bash
# Setup script for Package-Filter isolated environment

echo "Setting up Package-Filter environment..."
echo "=========================================="

# Check if venv exists
if [ -d "venv" ]; then
    echo "Warning: venv directory already exists."
    read -p "Do you want to recreate it? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Removing existing venv..."
        rm -rf venv
    else
        echo "Keeping existing venv. Skipping creation."
        exit 0
    fi
fi

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

if [ $? -ne 0 ]; then
    echo "Error: Failed to create virtual environment."
    exit 1
fi

echo "Virtual environment created successfully!"

# Install packages
echo "Installing required packages..."
venv/bin/pip install --upgrade pip
venv/bin/pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "Error: Failed to install packages."
    exit 1
fi

echo ""
echo "=========================================="
echo "Setup complete!"
echo "=========================================="
echo ""
echo "To activate the environment, run:"
echo "  source venv/bin/activate"
echo ""
echo "To run the script, use either:"
echo "  python find_cross_ecosystem_packages.py  (with activated environment)"
echo "  venv/bin/python find_cross_ecosystem_packages.py  (without activation)"
echo ""
