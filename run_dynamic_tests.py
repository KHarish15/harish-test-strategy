import subprocess
import re
import sys
import os

def run_pytest_and_parse():
    # Get the test filename from environment or use default
    test_filename = os.getenv('TEST_FILENAME', 'input_file.py')
    
    print(f"🔍 Looking for tests in: {test_filename}")
    
    # Run pytest on the specific test file
    result = subprocess.run(
        ['pytest', test_filename, '--tb=short', '-q'],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    output = result.stdout

    # Parse test results
    passed = failed = 0
    # Look for lines like: "7 passed, 1 failed"
    summary_match = re.search(r'(\d+) passed', output)
    if summary_match:
        passed = int(summary_match.group(1))
    failed_match = re.search(r'(\d+) failed', output)
    if failed_match:
        failed = int(failed_match.group(1))
    total = passed + failed

    print(f"No of test cases: {total}")
    print(f"No of test cases passed: {passed}")
    print(f"No of test cases failed: {failed}")

if __name__ == "__main__":
    run_pytest_and_parse()