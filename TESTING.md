# Testing Guide for Ethoscopy

This document describes the testing infrastructure and guidelines for contributing to ethoscopy.

## Overview

Ethoscopy uses `pytest` as its testing framework with comprehensive unit tests, integration tests, and fixtures to ensure code reliability and prevent regressions.

## Running Tests

### Installation

First, install the testing dependencies:

```bash
pip install -e ".[dev]"
```

### Basic Test Execution

Run all tests:
```bash
pytest
```

Run with coverage reporting:
```bash
pytest --cov=ethoscopy --cov-report=term-missing
```

Use the convenience script:
```bash
python run_tests.py
```

### Test Categories

Tests are organized with markers:

- `@pytest.mark.unit` - Fast unit tests for individual functions
- `@pytest.mark.integration` - Integration tests for workflows
- `@pytest.mark.slow` - Tests that take longer to run
- `@pytest.mark.requires_data` - Tests needing actual ethoscope data

Run specific categories:
```bash
# Only unit tests (fast)
pytest -m unit

# Only integration tests
pytest -m integration

# Skip slow tests
pytest -m "not slow"

# Run specific test file
pytest tests/test_load.py
```

### Test Options

```bash
# Verbose output
pytest -v

# Stop on first failure
pytest -x

# Run tests in parallel
pytest -n auto

# Generate HTML coverage report
pytest --cov=ethoscopy --cov-report=html
```

## Test Structure

### Directory Layout

```
tests/
├── __init__.py              # Test package init
├── conftest.py              # Shared fixtures and configuration
├── test_load.py             # Tests for loading functions
├── test_analyse.py          # Tests for analysis functions
├── test_behavpy.py          # Tests for behavpy classes
└── test_integration.py      # Integration tests
```

### Fixtures

Key fixtures available in all tests:

- `sample_metadata_csv` - Temporary CSV metadata file
- `sample_ethoscope_data` - Mock ethoscope tracking data
- `mock_sqlite_db` - SQLite database with ethoscope structure
- `sample_behavpy_object` - Pre-created behavpy object
- `linked_metadata_sample` - Linked metadata for load testing

### Test Naming

- Test files: `test_*.py`
- Test classes: `Test*`
- Test functions: `test_*`

## Writing Tests

### Unit Test Example

```python
@pytest.mark.unit
def test_function_success(self, fixture_name):
    """Test successful function execution."""
    result = function_under_test(input_data)

    assert isinstance(result, expected_type)
    assert len(result) > 0
    assert 'expected_column' in result.columns
```

### Integration Test Example

```python
@pytest.mark.integration
def test_complete_workflow(self, sample_metadata_csv, tmp_path):
    """Test complete workflow from metadata to analysis."""
    # Setup test data structure
    setup_test_environment(tmp_path)

    # Execute workflow
    linked_data = link_meta_index(sample_metadata_csv, tmp_path)
    loaded_data = load_ethoscope(linked_data)
    analyzed_data = sleep_annotation(loaded_data)

    # Verify results
    assert len(analyzed_data) > 0
    assert 'asleep' in analyzed_data.columns
```

### Testing Guidelines

1. **Test Function Behavior**: Test expected behavior, edge cases, and error conditions
2. **Use Descriptive Names**: Test names should clearly describe what's being tested
3. **Keep Tests Isolated**: Each test should be independent and not rely on others
4. **Use Appropriate Markers**: Mark tests as unit/integration/slow as appropriate
5. **Mock External Dependencies**: Use mocks for file I/O, databases, web requests
6. **Test Error Conditions**: Ensure functions handle invalid inputs gracefully
7. **Verify State Changes**: Test that functions modify data as expected

### Testing Data Loading Functions

When testing data loading functions:

```python
def test_load_function_with_mock_db(self, mock_sqlite_db):
    \"\"\"Test loading with mocked database.\"\"\"
    file_info = create_file_info(mock_sqlite_db)
    result = read_single_roi(file_info)

    assert result is not None
    assert isinstance(result, pd.DataFrame)
```

### Testing Analysis Functions

When testing analysis functions:

```python
def test_analysis_function_edge_cases(self):
    \"\"\"Test analysis function with edge cases.\"\"\"
    # Test with empty data
    empty_result = analysis_function(pd.DataFrame())
    assert len(empty_result) == 0

    # Test with all-same values
    constant_data = create_constant_data()
    constant_result = analysis_function(constant_data)
    assert not constant_result['column'].any()
```

## Continuous Integration

### GitHub Actions

The project includes comprehensive CI/CD pipelines:

#### Main CI Pipeline (`.github/workflows/ci.yml`)
- **Triggers**: Push to main/develop, PRs to main, daily scheduled runs
- **Python versions**: 3.10, 3.11, 3.12
- **Jobs**:
  - **Test**: Unit tests, integration tests, linting, formatting
  - **Notebook Testing**: Validates Jupyter notebooks
  - **Build**: Package building and validation
  - **Security**: Bandit and safety scans

#### Release Pipeline (`.github/workflows/release.yml`)
- **Triggers**: GitHub releases and version tags
- **Automated PyPI publishing**: Test PyPI for tags, production PyPI for releases

### Pre-commit Hooks

Install pre-commit hooks for local development:

```bash
pip install pre-commit
pre-commit install
```

Configured hooks:
- Code formatting (Black)
- Linting (Ruff)
- Type checking (MyPy)
- Unit tests on commit
- Fast tests on push

## Coverage Requirements

- Minimum coverage target: 70% (configured in pytest.ini)
- All new functions must have tests
- Critical functions (load, analysis) require comprehensive test coverage
- View coverage reports: `pytest --cov=ethoscopy --cov-report=html`

## Performance Testing

Long-running tests are marked with `@pytest.mark.slow`:

```bash
# Run performance tests
pytest -m slow

# Skip performance tests for faster development
pytest -m "not slow"
```

## Debugging Tests

### Running Individual Tests

```bash
# Run specific test
pytest tests/test_load.py::TestLoadEthoscope::test_load_ethoscope_success

# Debug with pdb
pytest --pdb tests/test_load.py::test_specific_test

# Capture print statements
pytest -s tests/test_load.py
```

### Common Issues

1. **Import Errors**: Ensure ethoscopy is installed in development mode (`pip install -e .`)
2. **Missing Dependencies**: Install test dependencies (`pip install -e ".[dev]"`)
3. **Fixture Errors**: Check that fixtures are properly defined in `conftest.py`
4. **Path Issues**: Use `tmp_path` fixture for temporary files

## Contributing Tests

When contributing new features:

1. Write tests before or alongside implementation
2. Ensure new tests follow existing patterns
3. Add appropriate markers (`@pytest.mark.unit`, etc.)
4. Update this documentation if adding new testing patterns
5. Verify all tests pass: `pytest`

## Test Data

- Use fixtures for reusable test data
- Create minimal test data that exercises the function
- Use `tmp_path` for temporary files
- Mock external dependencies (databases, web services)
- Use random seeds for reproducible test data

For more information on pytest, see the [official documentation](https://docs.pytest.org/).
