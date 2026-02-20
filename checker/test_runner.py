#!/usr/bin/env python3
# *************************************************************************** #
#                                                                             #
#                                                        :::      ::::::::    #
#   test_runner.py                                     :+:      :+:    :+:    #
#                                                    +:+ +:+         +:+      #
#   By: iberegsz <iberegsz@student.42vienna.com>   +#+  +:+       +#+         #
#                                                +#+#+#+#+#+   +#+            #
#   Created: 2025/10/22 11:20:50 by iberegsz          #+#    #+#              #
#   Updated: 2026/01/19 19:17:43 by iberegsz         ###   ########.fr        #
#                                                                             #
# *************************************************************************** #

"""
Expert System Test Runner
Runs all tests and shows summary
"""

import sys
import subprocess
from pathlib import Path


def run_test(test_file):
    """Run a single test file and return success status."""
    try:
        result = subprocess.run(
            ['python3', 'expert_system.py', test_file],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Timeout"
    except Exception as e:
        return False, "", str(e)


def main():
    """Run all tests and show summary."""
    test_files = sorted(Path('.').glob('test/*.txt'))

    if not test_files:
        print("No test files found!")
        return 1

    print("=" * 70)
    print("EXPERT SYSTEM - TEST SUITE")
    print("=" * 70)
    print()

    results = []
    for test_file in test_files:
        test_path = str(test_file)
        test_name = test_file.name
        success, stdout, stderr = run_test(test_path)

        status = "OK PASS" if success else "KO FAIL"
        results.append((test_name, success))

        print(f"{status} - {test_name}")

        if not success and stderr:
            print(f"  Error: {stderr[:100]}")

    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)

    passed = sum(1 for _, success in results if success)
    total = len(results)
    percentage = (passed / total * 100) if total > 0 else 0

    print(f"Tests passed: {passed}/{total} ({percentage:.1f}%)")

    if passed == total:
        print("OK All tests passed!")
        return 0
    else:
        print("KO Some tests failed")
        print("\nFailed tests:")
        for name, success in results:
            if not success:
                print(f"  - {name}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
