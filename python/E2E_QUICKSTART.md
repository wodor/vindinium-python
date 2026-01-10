# Quick Start: E2E Testing for Vindinium

This guide helps you quickly get started with End-to-End (E2E) testing.

## TL;DR - Run Tests Now

```bash
cd python
./run_e2e_tests.sh
```

That's it! The script handles everything:
- ✅ Checks prerequisites (Docker, Python, pytest)
- ✅ Starts MongoDB container
- ✅ Starts game server
- ✅ Runs all E2E tests
- ✅ Cleans up automatically

## What Gets Tested

The E2E test suite validates:

1. **Server Health** (`test_basic.py`)
   - Health endpoint responds correctly
   - Root endpoint serves HTML

2. **Game Creation** (`test_game_api.py`)
   - Create training games with default parameters
   - Create games with custom turn counts
   - Reject invalid parameters (400 errors)

3. **Game Movement** (`test_game_api.py`)
   - Make moves through API
   - Validate token authentication
   - Handle nonexistent games (404 errors)
   - Advance game turns correctly

4. **Game State** (`test_game_api.py`)
   - Retrieve game state by ID
   - Handle nonexistent games (404 errors)

## Common Commands

```bash
# Run all E2E tests
./run_e2e_tests.sh

# Run specific test
./run_e2e_tests.sh -k test_health

# Run with verbose output
./run_e2e_tests.sh -vv

# Stop on first failure
./run_e2e_tests.sh -x

# Run with debugger on failure
./run_e2e_tests.sh --pdb
```

## How It Works

### Architecture

```
┌─────────────────┐
│ Test Runner     │ ← You run this
└────────┬────────┘
         │
         ├─> 1. Check prerequisites (Docker, pytest, etc.)
         │
         ├─> 2. Start MongoDB container (docker-compose.test.yml)
         │      └─> Wait for health check (mongosh ping)
         │
         ├─> 3. Start game server (main.py)
         │      └─> Wait for health check (/health endpoint)
         │
         ├─> 4. Run pytest (tests/e2e/*.py)
         │      ├─> Each test gets clean database (fixture)
         │      └─> HTTP client makes requests to server
         │
         └─> 5. Cleanup
                ├─> Stop game server
                └─> Stop & remove MongoDB container
```

### Test Isolation

Each test function gets:
- Fresh database (all collections dropped)
- Shared MongoDB container (session-scoped)
- Shared game server (session-scoped)
- New HTTP client (function-scoped)

This means tests don't interfere with each other, but container startup only happens once per test session.

## Requirements

- **Docker**: Container runtime (Docker or Podman)
- **Python 3.10+**: Runtime for server and tests
- **Dependencies**: Installed via `pip install -r requirements.txt`

The test runner checks all requirements before starting.

## Troubleshooting

### Problem: Port already in use

```
Error: Port 27017 is already in use
```

**Solution**: Stop existing MongoDB container or change test port

```bash
# Check for existing MongoDB
docker ps | grep mongo

# Stop it
docker stop <container_id>

# Or clean up test containers
docker compose -f docker-compose.test.yml down -v
```

### Problem: Docker not found

```
Error: Docker is not installed or not in PATH
```

**Solution**: Install Docker

```bash
# Ubuntu/Debian
sudo apt-get install docker.io

# macOS
brew install --cask docker

# Or use Podman as alternative
sudo apt-get install podman
```

### Problem: Tests hang

**Solution**: Interrupt with Ctrl+C - cleanup runs automatically

The test fixtures have signal handlers that ensure cleanup even on interrupt.

### Problem: Containers not cleaned up

```bash
# Manual cleanup
cd python
docker compose -f docker-compose.test.yml down -v

# Force remove
docker rm -f vindinium-test-mongodb
```

## CI Integration

The E2E tests work seamlessly in CI environments. See `.github/workflows/python-e2e.yml` for GitHub Actions example.

Key points:
- Docker is available by default in GitHub Actions
- Tests run on Python 3.10, 3.11, and 3.12
- Timeout set to 10 minutes
- Cleanup happens even on failure

## Next Steps

- **Write new tests**: Copy pattern from `tests/e2e/test_game_api.py`
- **Add test tags**: Use `@pytest.mark.smoke` for important tests
- **Extend coverage**: Add tests for combat, mines, taverns
- **Performance tests**: Use `pytest-benchmark` for timing

## Success Metrics

The E2E test suite meets these targets:

| Metric | Target | Current |
|--------|--------|---------|
| Setup time | < 30s | ~4s ✅ |
| Full test run | < 2 min | ~4s ✅ |
| Cleanup rate | 100% | 100% ✅ |
| Tests passing | All | 11/11 ✅ |

## Resources

- [Full E2E Testing Guide](tests/e2e/README.md)
- [pytest documentation](https://docs.pytest.org/)
- [Docker Compose docs](https://docs.docker.com/compose/)
- [FastAPI testing](https://fastapi.tiangolo.com/tutorial/testing/)
