# End-to-End (E2E) Testing Guide

This directory contains end-to-end tests for the Vindinium game server. E2E tests validate the complete application stack, including the game server and MongoDB database.

## Overview

The E2E test suite:

- ✅ Automatically starts and manages a MongoDB container
- ✅ Automatically starts the game server
- ✅ Runs comprehensive API tests
- ✅ Automatically cleans up all resources
- ✅ Works in both local development and CI environments

## Quick Start

### Run All E2E Tests

```bash
cd python
./run_e2e_tests.sh
```

Or using Python directly:

```bash
cd python
python run_e2e_tests.py
```

### Run Specific Tests

```bash
# Run tests matching a pattern
./run_e2e_tests.sh -k test_health

# Run tests with specific marker
./run_e2e_tests.sh -m smoke

# Run a specific test file
pytest tests/e2e/test_basic.py -v
```

## Prerequisites

- **Docker**: Required for running MongoDB container
- **Python 3.10+**: Required for running the test suite
- **Dependencies**: Install with `pip install -r requirements.txt`

The test runner will check all prerequisites before running tests.

## Test Structure

```
tests/e2e/
├── __init__.py
├── conftest.py           # Pytest fixtures and configuration
├── test_basic.py         # Basic server health tests
└── test_game_api.py      # Game creation and gameplay tests
```

## Test Fixtures

The E2E test suite provides several pytest fixtures:

### Session-Scoped Fixtures

- **`mongodb_container`**: Manages MongoDB container lifecycle
  - Automatically starts MongoDB before tests
  - Waits for MongoDB to be ready
  - Cleans up container after all tests
  - Handles interrupt signals (Ctrl+C) gracefully

- **`game_server`**: Manages game server lifecycle
  - Automatically starts the game server
  - Waits for server to be ready
  - Terminates server after all tests

### Function-Scoped Fixtures

- **`http_client`**: Provides an async HTTP client for making requests
  - Configured with base URL pointing to test server
  - Automatically closed after each test

- **`clean_database`**: Provides a clean database for each test
  - Drops test collections before test runs
  - Cleans up after test completes
  - Ensures test isolation

## Example Test

```python
import pytest
import httpx

@pytest.mark.asyncio
async def test_create_game(http_client: httpx.AsyncClient, clean_database):
    """Test creating a new training game."""
    response = await http_client.post(
        "/api/training",
        data={"key": "test-api-key"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "game" in data
    assert "token" in data
```

## Configuration

E2E tests use environment variables for configuration:

- `TEST_MONGODB_URI`: MongoDB connection string (default: `mongodb://localhost:27017`)
- `TEST_DATABASE_NAME`: Database name for tests (default: `vindinium_test`)
- `TEST_SERVER_HOST`: Game server host (default: `localhost`)
- `TEST_SERVER_PORT`: Game server port (default: `9000`)

## CI Integration

### GitHub Actions Example

```yaml
name: E2E Tests

on: [push, pull_request]

jobs:
  e2e-tests:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          cd python
          pip install -r requirements.txt
      
      - name: Run E2E tests
        run: |
          cd python
          ./run_e2e_tests.sh
```

## Troubleshooting

### MongoDB Container Fails to Start

**Issue**: Error starting MongoDB container

**Solutions**:
- Ensure Docker is running: `docker ps`
- Check if port 27017 is already in use: `lsof -i :27017`
- Try cleaning up existing containers: `docker compose -f docker-compose.test.yml down -v`

### Game Server Fails to Start

**Issue**: Game server doesn't become ready

**Solutions**:
- Check if port 9000 is already in use: `lsof -i :9000`
- Verify MongoDB is running: `docker ps | grep mongo`
- Check server logs in test output

### Tests Hang or Timeout

**Issue**: Tests hang indefinitely

**Solutions**:
- Interrupt with Ctrl+C (cleanup will run automatically)
- Check for orphaned containers: `docker ps -a`
- Manually cleanup: `docker compose -f docker-compose.test.yml down -v`

### Cleanup Doesn't Work

**Issue**: Container not removed after tests

**Solutions**:
- Run cleanup manually: `cd python && docker compose -f docker-compose.test.yml down -v`
- Check for container: `docker ps -a | grep vindinium`
- Force remove: `docker rm -f vindinium-test-mongodb`

## Development Tips

### Run Tests in Watch Mode

```bash
# Install pytest-watch
pip install pytest-watch

# Run in watch mode
cd python
ptw tests/e2e/ -- -v
```

### Debug Tests

```bash
# Drop into debugger on failure
./run_e2e_tests.sh --pdb

# Run with verbose output
./run_e2e_tests.sh -vv

# Stop on first failure
./run_e2e_tests.sh -x
```

### Test Isolation

Each test gets a clean database via the `clean_database` fixture. To add additional cleanup:

```python
@pytest.fixture
async def my_fixture(clean_database):
    # Setup
    client = clean_database
    # ... setup code ...
    
    yield client
    
    # Teardown (automatic cleanup)
```

## Writing New E2E Tests

1. Create a new test file in `tests/e2e/` (e.g., `test_feature.py`)
2. Use async test functions with `@pytest.mark.asyncio`
3. Use provided fixtures: `http_client`, `clean_database`
4. Follow the pattern in existing test files
5. Run your test: `pytest tests/e2e/test_feature.py -v`

Example:

```python
"""E2E tests for new feature."""

import pytest
import httpx


@pytest.mark.asyncio
class TestNewFeature:
    """Test new feature via API."""
    
    async def test_feature(
        self, http_client: httpx.AsyncClient, clean_database
    ):
        """Test the feature works end-to-end."""
        response = await http_client.post("/api/new-endpoint", json={...})
        assert response.status_code == 200
```

## Success Criteria

The E2E test suite meets the following requirements:

- ✅ **SC-001**: Single command execution completes in under 2 minutes
- ✅ **SC-002**: Tests validate all critical game mechanics
- ✅ **SC-003**: 100% cleanup success rate (containers removed)
- ✅ **SC-004**: Environment setup completes in under 30 seconds
- ✅ **SC-005**: Zero manual intervention required
- ✅ **SC-006**: Works in local and CI environments

## Additional Resources

- [pytest documentation](https://docs.pytest.org/)
- [httpx documentation](https://www.python-httpx.org/)
- [Docker Compose documentation](https://docs.docker.com/compose/)
- [FastAPI testing](https://fastapi.tiangolo.com/tutorial/testing/)
