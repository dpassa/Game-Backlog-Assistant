"""
API Test Runner - Run all API exploration tests with proper error handling

This script runs the API exploration tests in sequence to understand
the data structures returned by Steam and GOG APIs.
"""

import sys
import subprocess
import os

def run_test(test_name, test_file):
    """Run a single test file and capture results"""
    print("\n" + "="*80)
    print(f"Running: {test_name}")
    print("="*80)

    try:
        result = subprocess.run(
            [sys.executable, test_file],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )

        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)

        if result.returncode == 0:
            print(f"\n✓ {test_name} completed successfully")
            return True
        else:
            print(f"\n✗ {test_name} failed with return code {result.returncode}")
            return False

    except subprocess.TimeoutExpired:
        print(f"\n⚠ {test_name} timed out (>30s)")
        return False
    except Exception as e:
        print(f"\n✗ {test_name} error: {e}")
        return False


def main():
    """Run all API exploration tests"""
    print("="*80)
    print("API Exploration Test Suite")
    print("="*80)
    print("\nThis will test actual Steam and GOG APIs to validate data structures.")
    print("Note: Tests may be slow due to rate limiting.\n")

    tests = [
        ("Steam - GetOwnedGames API", "test_steam_data.py"),
        ("Steam - appdetails API", "test_steam_detailed.py"),
        ("GOG - Public Profile API", "test_gog_data.py"),
    ]

    results = {}

    for test_name, test_file in tests:
        results[test_name] = run_test(test_name, test_file)

    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)

    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")

    total = len(results)
    passed = sum(1 for r in results.values() if r)
    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All API tests passed!")
        return 0
    else:
        print(f"\n⚠ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
