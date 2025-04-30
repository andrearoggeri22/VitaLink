"""
Script to run all tests for the VitaLink application.
"""
import os
import sys
import pytest


def main():
    """
    Run all tests for the VitaLink application.
    
    This script uses pytest to run all tests in the tests directory.
    It configures the test environment and generates a coverage report.
    """
    # Change to the project root directory
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # Configure test environment
    os.environ["TESTING"] = "True"
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"
    
    # Define pytest arguments
    pytest_args = [
        "-v",                       # Verbose output
        "--tb=short",               # Shorter traceback format
        "--cov=app",                # Coverage for the app package
        "--cov-report=term",        # Coverage report in terminal
        "--cov-report=html:coverage_html",  # HTML coverage report
        "tests/"                    # Test directory
    ]
    
    # Run pytest with the specified arguments
    exit_code = pytest.main(pytest_args)
    
    # Print a summary message
    if exit_code == 0:
        print("\n🎉 All tests passed successfully!")
        print("\nCoverage report has been generated in the 'coverage_html' directory.")
    else:
        print("\n❌ Some tests failed. Please check the output above.")
    
    # Return the exit code
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
