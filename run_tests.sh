#!/bin/bash

# Run all tests for the Budget Management System
# Usage: ./run_tests.sh [test_label]
# If no argument is given, runs all tests.

set -e

# Activate virtual environment
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
else
    echo "[ERROR] venv not found. Please create and install dependencies first."
    exit 1
fi

# Run tests
if [ -z "$1" ]; then
    echo "[INFO] Running ALL tests (unit, integration, API)..."
    python3 manage.py test
else
    echo "[INFO] Running tests for: $1"
    python3 manage.py test "$1"
fi

status=$?

if [ $status -eq 0 ]; then
    echo "\n✅ ALL TESTS PASSED!"
else
    echo "\n❌ SOME TESTS FAILED! Check the output above."
fi

exit $status 