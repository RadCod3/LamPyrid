"""Script to run code formatting and linting."""

import subprocess
import sys


def main() -> int:
    """Run code formatting and linting fix."""
    print('Running ruff format...')
    try:
        subprocess.run(['ruff', 'format', '.'], check=True)
        print('Running ruff check --fix...')
        subprocess.run(['ruff', 'check', '--fix', '.'], check=True)
    except subprocess.CalledProcessError as e:
        print(f'Error during formatting: {e}')
        return 1
    except FileNotFoundError:
        print("Error: 'ruff' not found. Ensure it is installed in your environment.")
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
