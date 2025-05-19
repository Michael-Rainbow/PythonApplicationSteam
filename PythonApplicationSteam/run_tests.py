import unittest
import coverage
import os
import sys
import importlib.util

# Define paths - fix the directory structure issue
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# If run_tests.py is placed in the tests directory
if os.path.basename(CURRENT_DIR) == 'tests':
    PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
    TEST_DIR = CURRENT_DIR  # This directory itself contains the tests
else:
    # If run_tests.py is placed in the project root
    PROJECT_ROOT = CURRENT_DIR
    TEST_DIR = os.path.join(PROJECT_ROOT, 'tests')

SRC_DIR = os.path.join(PROJECT_ROOT, 'PythonApplicationSteam')

# Print directory info for debugging
print(f"Current Directory: {CURRENT_DIR}")
print(f"Project Root: {PROJECT_ROOT}")
print(f"Test Directory: {TEST_DIR}")
print(f"Source Directory: {SRC_DIR}")

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
    
    # Check if the test directory exists
    if not os.path.exists(TEST_DIR):
        print(f"ERROR: Test directory does not exist: {TEST_DIR}")
        return unittest.TestResult()
        
    # List test files for debugging
    print("\nTest files found:")
    for root, dirs, files in os.walk(TEST_DIR):
        for file in files:
            if file.startswith('test_') and file.endswith('.py'):
                print(f"  {os.path.join(root, file)}")
                
    suite = loader.discover(TEST_DIR, pattern='test_*.py')
    
    # Run tests
    print("\nRunning tests...")
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
