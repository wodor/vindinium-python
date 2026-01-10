#!/bin/bash
#
# E2E Test Runner Script
# 
# Simple wrapper that runs the Python-based E2E test runner
#

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Change to the script directory
cd "$SCRIPT_DIR"

# Run the Python test runner
python3 run_e2e_tests.py "$@"
