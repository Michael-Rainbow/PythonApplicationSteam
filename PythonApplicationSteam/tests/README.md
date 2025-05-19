# Steam Application Test Suite

This test suite provides comprehensive test coverage for the Steam Application. It includes various types of tests:

1. Unit Tests - For validating individual functions and methods
2. Integration Tests - For validating component interactions
3. Coverage Reporting - For assessing test coverage

## Test Files

- **test_funcs.py** - Tests for API interaction functions in `Funcs.py`
- **test_app.py** - Tests for the main application and UI components in `PythonApplicationSteam.py`
- **test_integration.py** - Tests for interactions between components
- **run_tests.py** - Script to run all tests and generate coverage reports

## Setup Instructions

1. Copy the test files to your project structure:

```
YourProject/
├── PythonApplicationSteam/
│   ├── Funcs.py
│   └── PythonApplicationSteam.py
├── tests/
│   ├── test_funcs.py
│   ├── test_app.py
│   └── test_integration.py
└── run_tests.py
```

2. Install dependencies:

```bash
pip install coverage unittest-xml-reporting
```

3. Set the Steam API key environment variable:

```bash
export STEAM_API_KEY="your_api_key_here"
```

## Running Tests

### Run all tests with coverage:

```bash
python run_tests.py
```

This will:
- Execute all tests
- Display test results in the console
- Show a coverage summary in the console
- Generate a detailed HTML coverage report

### Run individual test files:

```bash
python -m unittest tests/test_funcs.py
python -m unittest tests/test_app.py
python -m unittest tests/test_integration.py
```

## Test Coverage

The test suite aims to provide thorough coverage of:

- API interaction functions in `Funcs.py`
- Application initialization and UI setup
- User input validation
- Game and achievement data handling
- Error handling and edge cases
- Thread management and asynchronous operations
- Image downloading and caching

## Extending the Test Suite

To add more tests:

1. Create new test methods in existing test classes
2. Create new test classes for specific functionality
3. Create additional test files for new components

Follow the pattern of existing tests, using appropriate mocking for external dependencies.
