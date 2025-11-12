#!/usr/bin/env python3
"""
Test Runner
Runs all tests with proper configuration
"""

import sys
import subprocess


def run_tests(args=None):
    """
    Run pytest with common options
    
    Args:
        args: Additional pytest arguments
    """
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/",
        "-v",  # Verbose
        "--tb=short",  # Shorter traceback
        "--color=yes",  # Colored output
    ]
    
    if args:
        cmd.extend(args)
    
    print("=" * 60)
    print("Running RiftboundOCR Test Suite")
    print("=" * 60)
    print()
    
    result = subprocess.run(cmd)
    
    return result.returncode


if __name__ == "__main__":
    # Pass any command line args to pytest
    additional_args = sys.argv[1:]
    sys.exit(run_tests(additional_args))




