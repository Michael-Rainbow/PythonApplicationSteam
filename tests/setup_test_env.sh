#!/bin/bash
# Script to set up the test environment for Steam Application

# Create directory structure
mkdir -p PythonApplicationSteam
mkdir -p tests

# Copy application files
cp /tmp/inputs/PythonApplicationSteam/Funcs.py PythonApplicationSteam/
cp /tmp/inputs/PythonApplicationSteam/PythonApplicationSteam.py PythonApplicationSteam/

# Copy test files
cp ./tests/test_*.py tests/

# Create image cache directory
mkdir -p image_cache

# Make the run_tests.py executable
chmod +x run_tests.py

echo "Test environment set up successfully."
echo "Run tests with: python run_tests.py"
echo "Note: Make sure to set the STEAM_API_KEY environment variable before running tests."
