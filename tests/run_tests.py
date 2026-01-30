"""
Test Runner for TaskTrail Backend

Runs all test suites with proper reporting and coverage.

Usage:
    python run_tests.py              # Run all tests
    python run_tests.py endpoints    # Run only endpoint tests
    python run_tests.py admin        # Run only admin auth tests
    python run_tests.py token        # Run only token tracking tests
    python run_tests.py --coverage   # Run with coverage report
"""

import subprocess
import sys
import argparse
from pathlib import Path


def run_command(cmd: list, description: str) -> int:
    """
    Run a command and return exit code.
    
    Args:
        cmd: Command to run as list
        description: Description to print
        
    Returns:
        Exit code
    """
    print(f"\n{'='*60}")
    print(f"[TEST] {description}")
    print(f"{'='*60}\n")
    
    # Use current Python interpreter (from venv)
    cmd_with_python = [sys.executable, "-m"] + cmd
    result = subprocess.run(cmd_with_python)
    return result.returncode


def main():
    """Run the tests."""
    parser = argparse.ArgumentParser(description="Run TaskTrail tests")
    parser.add_argument(
        "suite",
        nargs="?",
        choices=["all", "endpoints", "admin", "token"],
        default="all",
        help="Test suite to run"
    )
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Run with coverage report"
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output"
    )
    
    args = parser.parse_args()
    
    # Base pytest command
    base_cmd = ["pytest"]
    
    if args.verbose:
        base_cmd.append("-v")
    
    if args.coverage:
        base_cmd.extend(["--cov=app", "--cov-report=html", "--cov-report=term"])
    
    # Get current directory and determine test paths
    current_dir = Path.cwd()
    tests_dir = current_dir if current_dir.name == "tests" else current_dir / "tests"
    
    # Determine which tests to run
    test_files = {
        "all": ["."],
        "endpoints": ["test_endpoints.py"],
        "admin": ["test_admin_auth.py"],
        "token": ["test_token_tracking.py"]
    }
    
    test_path = test_files.get(args.suite, ["."])
    
    # Run the tests
    cmd = base_cmd + test_path + ["-s", "--tb=short"]
    
    exit_code = run_command(
        cmd,
        f"Running {args.suite.upper()} tests"
    )
    
    if exit_code == 0:
        print("\n[PASS] All tests passed!")
        if args.coverage:
            print("\n[REPORT] Coverage report generated in htmlcov/index.html")
    else:
        print(f"\n[FAIL] Tests failed with exit code {exit_code}")
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
