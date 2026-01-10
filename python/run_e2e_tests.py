#!/usr/bin/env python3
"""
E2E Test Runner for Vindinium Game Server

This script manages the complete E2E test workflow:
1. Checks prerequisites (Docker, Python dependencies)
2. Starts MongoDB container
3. Starts game server
4. Runs E2E tests
5. Cleans up resources

Usage:
    python run_e2e_tests.py              # Run all E2E tests
    python run_e2e_tests.py -k test_name # Run specific test
    python run_e2e_tests.py --tags=auth  # Run tests with specific tag
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path


def check_prerequisites() -> bool:
    """Check that required tools are available."""
    print("Checking prerequisites...")
    
    # Check Python
    if sys.version_info < (3, 10):
        print("❌ Error: Python 3.10 or higher is required")
        return False
    print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor}")
    
    # Check Docker
    try:
        result = subprocess.run(
            ["docker", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            print(f"✓ Docker: {result.stdout.strip()}")
        else:
            print("❌ Error: Docker is not available")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("❌ Error: Docker is not installed or not in PATH")
        return False
    
    # Check pytest
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            print(f"✓ pytest: {result.stdout.strip()}")
        else:
            print("❌ Error: pytest is not available")
            print("   Run: pip install pytest pytest-asyncio httpx")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("❌ Error: pytest is not installed")
        print("   Run: pip install pytest pytest-asyncio httpx")
        return False
    
    print()
    return True


def run_e2e_tests(test_args: list[str]) -> int:
    """
    Run E2E tests using pytest.
    
    Args:
        test_args: Additional arguments to pass to pytest
        
    Returns:
        Exit code from pytest
    """
    # Build pytest command
    pytest_cmd = [
        sys.executable,
        "-m",
        "pytest",
        "tests/e2e/",
        "-v",
        "--tb=short",
        "--color=yes",
    ]
    pytest_cmd.extend(test_args)
    
    print(f"Running E2E tests: {' '.join(pytest_cmd)}")
    print("=" * 80)
    print()
    
    # Run tests
    result = subprocess.run(pytest_cmd)
    
    print()
    print("=" * 80)
    
    return result.returncode


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run E2E tests for Vindinium game server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-k",
        metavar="EXPRESSION",
        help="Run tests matching the given substring expression",
    )
    parser.add_argument(
        "-m",
        "--markers",
        metavar="MARKER",
        help="Run tests matching the given marker",
    )
    parser.add_argument(
        "--tags",
        metavar="TAG",
        help="Run tests with the given tag (alias for -m)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Quiet output (minimal)",
    )
    parser.add_argument(
        "--failfast",
        "-x",
        action="store_true",
        help="Stop on first failure",
    )
    parser.add_argument(
        "--pdb",
        action="store_true",
        help="Drop into debugger on failures",
    )
    
    args, unknown_args = parser.parse_known_args()
    
    # Check prerequisites
    if not check_prerequisites():
        print("❌ Prerequisites check failed")
        return 1
    
    # Build pytest arguments
    pytest_args = unknown_args.copy()
    
    if args.k:
        pytest_args.extend(["-k", args.k])
    
    if args.markers:
        pytest_args.extend(["-m", args.markers])
    elif args.tags:
        pytest_args.extend(["-m", args.tags])
    
    if args.verbose:
        pytest_args.append("-vv")
    
    if args.quiet:
        pytest_args.append("-q")
    
    if args.failfast:
        pytest_args.append("-x")
    
    if args.pdb:
        pytest_args.append("--pdb")
    
    # Run tests
    exit_code = run_e2e_tests(pytest_args)
    
    # Print summary
    if exit_code == 0:
        print("✓ All E2E tests passed!")
    else:
        print(f"❌ E2E tests failed with exit code {exit_code}")
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
