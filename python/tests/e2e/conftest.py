"""Pytest configuration and fixtures for E2E tests."""

import asyncio
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import AsyncGenerator, Generator

import httpx
import pytest
from motor.motor_asyncio import AsyncIOMotorClient


# Test configuration
TEST_MONGODB_URI = os.getenv("TEST_MONGODB_URI", "mongodb://localhost:27017")
TEST_DATABASE_NAME = os.getenv("TEST_DATABASE_NAME", "vindinium_test")
TEST_SERVER_HOST = os.getenv("TEST_SERVER_HOST", "localhost")
TEST_SERVER_PORT = int(os.getenv("TEST_SERVER_PORT", "9000"))
TEST_SERVER_URL = f"http://{TEST_SERVER_HOST}:{TEST_SERVER_PORT}"


def check_docker_available() -> bool:
    """Check if Docker or Podman is available."""
    try:
        result = subprocess.run(
            ["docker", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        try:
            result = subprocess.run(
                ["podman", "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False


def start_mongodb_container() -> subprocess.Popen:
    """Start MongoDB container using Docker Compose."""
    if not check_docker_available():
        pytest.skip("Docker/Podman not available")
    
    # Get the path to docker-compose.test.yml
    test_dir = Path(__file__).parent.parent.parent
    compose_file = test_dir / "docker-compose.test.yml"
    
    if not compose_file.exists():
        raise FileNotFoundError(f"Docker Compose file not found: {compose_file}")
    
    print("Starting MongoDB container...")
    
    # Start the container
    subprocess.run(
        ["docker", "compose", "-f", str(compose_file), "up", "-d"],
        check=True,
        capture_output=True,
    )
    
    # Wait for MongoDB to be ready
    max_retries = 30
    for i in range(max_retries):
        try:
            result = subprocess.run(
                ["docker", "exec", "vindinium-test-mongodb", "mongosh", "--eval", "db.adminCommand('ping')"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                print("MongoDB container is ready!")
                return None
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
            pass
        
        if i < max_retries - 1:
            time.sleep(1)
    
    raise RuntimeError("MongoDB container failed to become ready")


def stop_mongodb_container() -> None:
    """Stop and remove MongoDB container."""
    test_dir = Path(__file__).parent.parent.parent
    compose_file = test_dir / "docker-compose.test.yml"
    
    print("Stopping MongoDB container...")
    
    try:
        subprocess.run(
            ["docker", "compose", "-f", str(compose_file), "down", "-v"],
            check=True,
            capture_output=True,
            timeout=30,
        )
        print("MongoDB container stopped and removed")
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError) as e:
        print(f"Warning: Error stopping container: {e}")


def start_game_server() -> subprocess.Popen:
    """Start the game server process."""
    # Set environment variables for test mode
    env = os.environ.copy()
    env["MONGODB_URI"] = TEST_MONGODB_URI
    env["DATABASE_NAME"] = TEST_DATABASE_NAME
    env["HOST"] = TEST_SERVER_HOST
    env["PORT"] = str(TEST_SERVER_PORT)
    
    # Get the path to main.py
    test_dir = Path(__file__).parent.parent.parent
    main_py = test_dir / "main.py"
    
    if not main_py.exists():
        raise FileNotFoundError(f"main.py not found: {main_py}")
    
    print(f"Starting game server on {TEST_SERVER_URL}...")
    
    # Start the server process
    process = subprocess.Popen(
        [sys.executable, str(main_py)],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=test_dir,
    )
    
    # Wait for the server to be ready
    max_retries = 30
    for i in range(max_retries):
        try:
            response = httpx.get(f"{TEST_SERVER_URL}/health", timeout=2)
            if response.status_code == 200:
                print("Game server is ready!")
                return process
        except (httpx.ConnectError, httpx.TimeoutException):
            pass
        
        # Check if process is still running
        if process.poll() is not None:
            stdout, stderr = process.communicate()
            raise RuntimeError(
                f"Game server process terminated unexpectedly.\n"
                f"STDOUT: {stdout.decode()}\n"
                f"STDERR: {stderr.decode()}"
            )
        
        if i < max_retries - 1:
            time.sleep(1)
    
    process.terminate()
    raise RuntimeError("Game server failed to become ready")


def stop_game_server(process: subprocess.Popen) -> None:
    """Stop the game server process."""
    if process and process.poll() is None:
        print("Stopping game server...")
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
        print("Game server stopped")


@pytest.fixture(scope="session")
def mongodb_container():
    """Session-scoped fixture to manage MongoDB container lifecycle."""
    # Start MongoDB container
    start_mongodb_container()
    
    # Setup cleanup handler for interrupts
    def cleanup_handler(signum, frame):
        print("\nReceived interrupt signal, cleaning up...")
        stop_mongodb_container()
        sys.exit(1)
    
    old_sigint_handler = signal.signal(signal.SIGINT, cleanup_handler)
    old_sigterm_handler = signal.signal(signal.SIGTERM, cleanup_handler)
    
    try:
        yield
    finally:
        # Restore signal handlers
        signal.signal(signal.SIGINT, old_sigint_handler)
        signal.signal(signal.SIGTERM, old_sigterm_handler)
        
        # Stop MongoDB container
        stop_mongodb_container()


@pytest.fixture(scope="session")
def game_server(mongodb_container):
    """Session-scoped fixture to manage game server lifecycle."""
    process = start_game_server()
    
    try:
        yield process
    finally:
        stop_game_server(process)


@pytest.fixture
async def http_client(game_server) -> AsyncGenerator[httpx.AsyncClient, None]:
    """Provide an async HTTP client for making requests to the game server."""
    async with httpx.AsyncClient(base_url=TEST_SERVER_URL, timeout=10.0) as client:
        yield client


@pytest.fixture
async def clean_database(mongodb_container) -> AsyncGenerator[AsyncIOMotorClient, None]:
    """Provide a clean database for each test."""
    client = AsyncIOMotorClient(TEST_MONGODB_URI)
    db = client[TEST_DATABASE_NAME]
    
    # Clean the database before the test
    await db.drop_collection("games")
    
    yield client
    
    # Clean the database after the test
    await db.drop_collection("games")
    client.close()
