#!/usr/bin/env python3
"""
Test runner script for the Steam Application
Executes all tests and generates coverage report
"""

import unittest
import coverage
import os
import sys
import importlib.util

# Define paths
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(PROJECT_ROOT, 'PythonApplicationSteam')
TEST_DIR = os.path.join(PROJECT_ROOT, 'tests')

# Make sure we can import from our project directory
sys.path.insert(0, PROJECT_ROOT)

# Set up coverage
cov = coverage.Coverage(
    source=[SRC_DIR],
    omit=['*/__pycache__/*', '*/tests/*'],
    branch=True
)

def run_tests():
    """Run all tests and generate coverage report"""
    # Start coverage tracking
    cov.start()
    
    # Find and load all test files
    loader = unittest.TestLoader()
    suite = loader.discover(TEST_DIR, pattern='test_*.py')
    
    # Run tests
    print("Running tests...")
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Stop coverage tracking
    cov.stop()
    
    # Generate report
    print("\nCoverage Report:")
    cov.report()
    
    # Generate HTML report
    html_dir = os.path.join(PROJECT_ROOT, 'coverage_html')
    cov.html_report(directory=html_dir)
    print(f"Detailed HTML coverage report generated at: {html_dir}")
    
    return result

if __name__ == "__main__":
    # Make sure STEAM_API_KEY is set for testing
    if not os.environ.get('STEAM_API_KEY'):
        os.environ['STEAM_API_KEY'] = 'test_api_key'
    
    # Run tests
    result = run_tests()
    
    # Exit with appropriate code
    sys.exit(not result.wasSuccessful())
