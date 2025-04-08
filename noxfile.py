import os
import tempfile
from pathlib import Path

import nox
from nox.project import dependency_groups, load_toml

temp_venv_dir = os.path.join(tempfile.gettempdir(), "nox_venvs")
os.makedirs(temp_venv_dir, exist_ok=True)
nox.options.envdir = temp_venv_dir
nox.options.default_venv_backend = "uv"


def install_dependencies_for_group(session: nox.Session, group_name: str) -> None:
    """Install dependencies for a specified group."""
    project = load_toml("pyproject.toml")
    
    if group_name in project.get("dependency-groups", {}):
        deps = dependency_groups(project, group_name)
        session.install(*deps)
        session.install("-e", ".")
    else:
        session.error(f"Dependency group '{group_name}' does not exist in pyproject.toml")


def setup_test_environment(session: nox.Session) -> None:
    """Set up the test environment variables."""
    db_path = Path(tempfile.gettempdir()) / "test_ymplanner.db"
    
    os.environ["PYTHONPATH"] = f"{os.getcwd()}:{os.path.join(os.getcwd(), 'src')}"
    os.environ["ASYNC_DATABASE_URI"] = f"sqlite+aiosqlite:///{db_path}"
    os.environ["TESTING"] = "True"
    os.environ["DEBUG"] = "True"
    
    session.log(f"Test database will be created at: {db_path}")
    session.log(f"PYTHONPATH set to: {os.environ['PYTHONPATH']}")


@nox.session(python=["3.13"])
def tests(session: nox.Session) -> None:
    """Run tests using pytest."""
    setup_test_environment(session)
    install_dependencies_for_group(session, "test")
    session.run(
        "pytest",
        "tests",
        "-v",
        "--log-cli-level=INFO",
        "--cov=src",
        "--cov-report=term-missing",
        "--cov-report=term",
        "-p", "no:cacheprovider",
        *session.posargs,
    )


@nox.session(python=["3.13"])
def lint(session: nox.Session) -> None:
    """Check code for styling errors."""
    install_dependencies_for_group(session, "lint")
    session.run("ruff", "check", "src", "tests")


@nox.session(python=["3.13"])
def typecheck(session: nox.Session) -> None:
    """Run type checking using mypy."""
    install_dependencies_for_group(session, "test")
    install_dependencies_for_group(session, "lint")
    session.run("mypy", "src", "tests")


@nox.session(python=["3.13"])
def unit(session: nox.Session) -> None:
    """Run only unit tests."""
    setup_test_environment(session)
    install_dependencies_for_group(session, "test")
    session.run(
        "pytest",
        "tests/unit",
        "-v",
        "--log-cli-level=INFO",
        "--cov=src",
        "--cov-report=term-missing",
        "--cov-report=term",
        "-p", "no:cacheprovider",
        *session.posargs,
    )


@nox.session(python=["3.13"])
def integration(session: nox.Session) -> None:
    """Run only integration tests."""
    setup_test_environment(session)
    install_dependencies_for_group(session, "test")
    session.run(
        "pytest",
        "tests/integration",
        "-v",
        "--log-cli-level=INFO",
        "--cov=src",
        "--cov-report=term-missing",
        "--cov-report=term",
        "-p", "no:cacheprovider",
        *session.posargs,
    )


@nox.session(python=["3.13"])
def e2e(session: nox.Session) -> None:
    """Run only end-to-end tests."""
    setup_test_environment(session)
    install_dependencies_for_group(session, "e2e")
    session.run(
        "pytest",
        "tests/e2e",
        "-v",
        "--log-cli-level=INFO",
        "--cov=src",
        "--cov-report=term-missing",
        "--cov-report=term",
        "-p", "no:cacheprovider",
        *session.posargs,
    ) 