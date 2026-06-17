"""Entry point for MySQL Runner."""

import sys

from mysql_runner.app import run

if __name__ == "__main__":
    sys.exit(run())
