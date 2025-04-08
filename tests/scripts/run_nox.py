import argparse
import os
import subprocess
import sys
import tempfile


def main() -> int:
    """Run Nox session with appropriate arguments.
    
    Returns:
        int: Exit code (0 means success, other values indicate error)
    """
    parser = argparse.ArgumentParser(description="Run Nox session.")
    parser.add_argument(
        "--session",
        "-s",
        default="tests",
        help="Nox session to run (default: tests)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Display detailed information",
    )
    parser.add_argument(
        "--env-dir",
        help="Directory for virtual environments (defaults to a temporary directory)",
    )
    parser.add_argument(
        "pytest_args",
        nargs="*",
        help="Additional arguments passed to pytest",
    )

    args = parser.parse_args()

    temp_venv_dir = args.env_dir
    if not temp_venv_dir:
        temp_venv_dir = os.path.join(tempfile.gettempdir(), "nox_venvs")
        os.makedirs(temp_venv_dir, exist_ok=True)

    cmd: list[str] = [
        "nox",
        "--session", args.session,
        "--envdir", temp_venv_dir,
    ]

    if args.verbose:
        cmd.append("-v")

    if args.pytest_args:
        cmd.append("--")
        cmd.extend(args.pytest_args)

    print(f"Running: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, check=True)
        return result.returncode
    except subprocess.CalledProcessError as e:
        print(f"Nox session ended with error: {e}", file=sys.stderr)
        return e.returncode
    except KeyboardInterrupt:
        print("\nInterrupted by user", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main()) 