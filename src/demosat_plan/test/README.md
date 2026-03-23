# DemoSat Plan Unit Tests

This directory contains unit tests for the `demosat_plan` package.

## Test Structure

The tests are organized as follows:

- `conftest.py`: Contains shared pytest fixtures used across multiple test files
- `test_demosat_scheduler.py`: Tests for DemosatScheduler initialization and general methods
- `test_comm_windows.py`: Tests for scheduling communication windows
- `test_orbit_events.py`: Tests for scheduling orbit events and shadow events
- `test_science_activities.py`: Tests for scheduling science activities
- `test_calibration_activities.py`: Tests for scheduling calibration activities
- `test_adcs_yaw_activities.py`: Tests for scheduling ADCS yaw activities

## Running the Tests

### Prerequisites

Make sure you have pytest installed:

```bash
pip install pytest pytest-cov
```

### Running All Tests

From the root directory of the `demosat_plan` package, run:

```bash
pytest
```

### Running Specific Test Files

To run tests from a specific file:

```bash
pytest test/test_demosat_scheduler.py
```

### Running Tests with Coverage

To run tests with coverage reporting:

```bash
pytest --cov=demosat_plan
```

For a detailed HTML coverage report:

```bash
pytest --cov=demosat_plan --cov-report=html
```

This will create a `htmlcov` directory with an HTML report that you can open in a browser.

## Test Fixtures

The test fixtures in `conftest.py` include:

- `scheduler`: A basic DemosatScheduler instance with start and end times
- `scheduler_with_containers`: A DemosatScheduler with mock containers for ephemeris, comm windows, and orbit events
- `mock_ephemeris_container`: A mock ephemeris container with sample data
- `mock_comm_window_container`: A mock comm window container with sample windows
- `mock_orbit_event_container`: A mock orbit event container with sample events

These fixtures can be used in any test function by adding them as parameters.

## Adding New Tests

When adding new tests:

1. Consider whether they fit into an existing test file or if a new file is needed
2. Use the appropriate fixtures from `conftest.py`
3. Follow the naming convention of `test_*` for test functions
4. Group related tests in classes with names like `TestClassName`
