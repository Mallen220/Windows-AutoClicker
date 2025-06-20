#!/bin/bash
# This script sets up the Python environment

echo "Creating virtual environment..."
python3 -m venv venv

echo "Activating virtual environment..."
source venv/bin/activate

echo "Upgrading pip..."
pip install --upgrade pip

echo "Installing dependencies from requirements.txt..."
pip install -r requirements.txt

echo "Setup complete. Run your script with:"
echo "source venv/bin/activate && python AutoClicker_main.py"
