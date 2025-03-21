#!/usr/bin/env python
"""Pomocniczy skrypt do uruchamiania testów z użyciem Nox."""

import argparse
import subprocess
import sys


def main() -> int:
    """Uruchom testy z użyciem Nox."""
    parser = argparse.ArgumentParser(description="Uruchom testy z użyciem Nox.")
    parser.add_argument(
        "--session",
        "-s",
        choices=["tests", "lint", "typecheck", "unit", "integration", "e2e"],
        default="tests",
        help="Sesja Nox do uruchomienia (domyślnie: tests)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Wyświetl szczegółowe informacje",
    )
    parser.add_argument(
        "pytest_args",
        nargs="*",
        help="Dodatkowe argumenty przekazywane do pytest",
    )

    args = parser.parse_args()

    cmd = ["nox", "--session", args.session]
    
    if args.verbose:
        cmd.append("-v")
    
    if args.pytest_args:
        cmd.append("--")
        cmd.extend(args.pytest_args)

    try:
        result = subprocess.run(cmd, check=True)
        return result.returncode
    except subprocess.CalledProcessError as e:
        return e.returncode


if __name__ == "__main__":
    sys.exit(main()) 