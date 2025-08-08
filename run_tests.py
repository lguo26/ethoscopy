#!/usr/bin/env python3
"""
Simple test runner script for ethoscopy.

This script provides an easy way to run the test suite with different options.
"""

import subprocess
import sys
from pathlib import Path


def run_tests(test_type="all", coverage=True, verbose=True):
    """
    Run the ethoscopy test suite.

    Args:
        test_type (str): Type of tests to run ('all', 'unit', 'integration', 'slow')
        coverage (bool): Whether to include coverage reporting
        verbose (bool): Whether to run in verbose mode
    """
    cmd = ["python", "-m", "pytest"]

    if verbose:
        cmd.append("-v")

    if coverage:
        cmd.extend(["--cov=ethoscopy", "--cov-report=term-missing"])

    # Add test type markers
    if test_type == "unit":
        cmd.extend(["-m", "unit"])
    elif test_type == "integration":
        cmd.extend(["-m", "integration"])
    elif test_type == "slow":
        cmd.extend(["-m", "slow"])
    elif test_type == "fast":
        cmd.extend(["-m", "not slow"])

    # Add test directory
    cmd.append("tests/")

    print(f"Running command: {' '.join(cmd)}")
    return subprocess.run(cmd)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run ethoscopy tests")
    parser.add_argument(
        "--type",
        choices=["all", "unit", "integration", "slow", "fast"],
        default="all",
        help="Type of tests to run"
    )
    parser.add_argument(
        "--no-coverage",
        action="store_true",
        help="Disable coverage reporting"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Run in quiet mode"
    )

    args = parser.parse_args()

    result = run_tests(
        test_type=args.type,
        coverage=not args.no_coverage,
        verbose=not args.quiet
    )

    sys.exit(result.returncode)
