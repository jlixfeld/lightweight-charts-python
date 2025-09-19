"""Development tasks for lightweight-charts-python using invoke."""

import shutil
from pathlib import Path

from invoke.tasks import task


@task
def install(ctx, dev=True):
    """Install dependencies with uv."""
    if dev:
        print("Installing development dependencies...")
        ctx.run("uv sync")
    else:
        print("Installing production dependencies...")
        ctx.run("uv sync --no-dev")


@task
def sync(ctx):
    """Sync dependencies with uv.lock."""
    print("Syncing dependencies...")
    ctx.run("uv sync")


@task
def lock(ctx, upgrade=False):
    """Update uv.lock file."""
    cmd = "uv lock"
    if upgrade:
        cmd += " --upgrade"
        print("Updating and locking dependencies...")
    else:
        print("Locking dependencies...")
    ctx.run(cmd)


@task
def format(ctx, check=False, js=False):
    """Format code with ruff (Python) and prettier (JS/HTML)."""
    if js:
        cmd = "npm run format"
        if check:
            cmd += ":check"
            print("Checking JS/HTML formatting...")
        else:
            print("Formatting JS/HTML...")
        ctx.run(cmd)
    else:
        cmd = "uv run ruff format"
        if check:
            cmd += " --check"
            print("Checking Python formatting...")
        else:
            print("Formatting Python...")
        ctx.run(f"{cmd} .")


@task
def lint(ctx, fix=False, js=False):
    """Run linting with ruff (Python) and ESLint (JS)."""
    if js:
        cmd = "npm run lint"
        if fix:
            cmd += ":fix"
            print("Running JS linter with auto-fix...")
        else:
            print("Running JS linter...")
        ctx.run(cmd)
    else:
        cmd = "uv run ruff check"
        if fix:
            cmd += " --fix"
            print("Running Python linter with auto-fix...")
        else:
            print("Running Python linter...")
        ctx.run(f"{cmd} .")


@task
def typecheck(ctx):
    """Run type checking with pyright."""
    print("Running type checker...")
    ctx.run("uv run pyright")


@task
def test(ctx, cov=False, fast=False, verbose=False):
    """Run tests."""
    cmd = "uv run pytest"

    if fast:
        cmd += " -x --ff"
        print("Running tests (fast mode)...")
    elif cov:
        cmd += " --cov=app --cov-report=term-missing --cov-report=html"
        print("Running tests with coverage...")
    else:
        print("Running tests...")

    if verbose:
        cmd += " -v"

    ctx.run(cmd)


@task
def dev(ctx, host="127.0.0.1", port=8000, db=False):
    """Run development server."""
    if db:
        print("Starting development server (database mode - ensure ohlcv.csv is removed)...")
    else:
        print(f"Starting development server on {host}:{port}...")

    ctx.run(f"uv run uvicorn app.main:app --reload --host {host} --port {port}")


@task
def clean(ctx):
    """Clean up cache files and build artifacts."""
    print("Cleaning up cache files...")

    patterns = [
        "**/__pycache__",
        "**/*.pyc",
        "**/*.pyo",
        "**/*.pyd",
        "**/.pytest_cache",
        "**/.mypy_cache",
        "**/.ruff_cache",
        "**/htmlcov",
        "build",
        "dist",
        "*.egg-info",
        ".coverage*",
    ]

    for pattern in patterns:
        for path in Path(".").glob(pattern):
            if path.is_file():
                path.unlink()
                print(f"Removed file: {path}")
            elif path.is_dir():
                shutil.rmtree(path)
                print(f"Removed directory: {path}")


@task
def precommit(ctx, install=False, all_files=False, update=False):
    """Manage pre-commit hooks."""
    if install:
        print("Installing pre-commit hooks...")
        ctx.run("uv run pre-commit install")
    elif update:
        print("Updating pre-commit hooks...")
        ctx.run("uv run pre-commit autoupdate")
    elif all_files:
        print("Running pre-commit on all files...")
        ctx.run("uv run pre-commit run --all-files")
    else:
        print("Running pre-commit...")
        ctx.run("uv run pre-commit run")


@task
def docker_build(ctx, tag="lightweight-charts:latest"):
    """Build Docker image."""
    print(f"Building Docker image: {tag}")
    ctx.run(f"docker build -f docker/Dockerfile -t {tag} .")


@task
def docker_up(ctx, build=True, detach=False):
    """Start services with docker-compose."""
    cmd = "docker compose -f docker/docker-compose.yml up"
    if build:
        cmd += " --build"
    if detach:
        cmd += " -d"

    print("Starting Docker services...")
    ctx.run(cmd)


@task
def docker_down(ctx):
    """Stop docker-compose services."""
    print("Stopping Docker services...")
    ctx.run("docker compose -f docker/docker-compose.yml down")


@task
def docker_logs(ctx, follow=True):
    """View docker-compose logs."""
    cmd = "docker compose -f docker/docker-compose.yml logs"
    if follow:
        cmd += " -f"
    ctx.run(cmd)


@task
def add(ctx, package, dev=False):
    """Add a dependency with uv."""
    cmd = f"uv add {package}"
    if dev:
        cmd += " --dev"
        print(f"Adding development dependency: {package}")
    else:
        print(f"Adding dependency: {package}")
    ctx.run(cmd)


@task
def remove(ctx, package):
    """Remove a dependency with uv."""
    print(f"Removing dependency: {package}")
    ctx.run(f"uv remove {package}")


@task
def export(ctx, dev=False, output=None):
    """Export requirements file."""
    cmd = "uv export --format requirements-txt"

    if not dev:
        cmd += " --no-dev"
        output = output or "requirements.txt"
        print("Exporting production requirements...")
    else:
        output = output or "dev-requirements.txt"
        print("Exporting development requirements...")

    if output:
        cmd += f" > {output}"

    ctx.run(cmd)


@task
def npm_install(ctx):
    """Install Node.js dependencies."""
    print("Installing Node.js dependencies...")
    ctx.run("npm install")


@task
def js_check(ctx):
    """Run all JavaScript checks."""
    print("Running JavaScript checks...")
    format(ctx, check=True, js=True)
    lint(ctx, js=True)
    print("JavaScript checks completed!")


@task
def js_fix(ctx):
    """Fix all JavaScript auto-fixable issues."""
    print("Fixing JavaScript issues...")
    format(ctx, js=True)
    lint(ctx, fix=True, js=True)
    print("JavaScript auto-fix completed!")


@task
def check_all(ctx):
    """Run all checks (Python and JavaScript)."""
    print("Running all checks...")

    # Python checks
    format(ctx, check=True)
    lint(ctx)
    typecheck(ctx)
    test(ctx)

    # JavaScript checks
    try:
        js_check(ctx)
    except Exception as e:
        print(f"JavaScript checks failed (run 'inv npm-install' first): {e}")

    print("All checks completed!")


@task
def fix_all(ctx):
    """Fix all auto-fixable issues (Python and JavaScript)."""
    print("Fixing all auto-fixable issues...")

    # Python fixes
    format(ctx)
    lint(ctx, fix=True)

    # JavaScript fixes
    try:
        js_fix(ctx)
    except Exception as e:
        print(f"JavaScript fixes failed (run 'inv npm-install' first): {e}")

    print("Auto-fix completed!")


@task
def setup(ctx):
    """Set up development environment."""
    print("Setting up development environment...")

    # Check if uv is installed
    try:
        ctx.run("uv --version", hide=True)
    except Exception:
        print("Error: uv is not installed. Please install uv first.")
        print("Visit: https://docs.astral.sh/uv/getting-started/installation/")
        return

    # Check if Node.js is installed
    try:
        ctx.run("node --version", hide=True)
        ctx.run("npm --version", hide=True)
        node_available = True
    except Exception:
        print("Warning: Node.js/npm not found. JavaScript linting/formatting will be unavailable.")
        print("Install Node.js from: https://nodejs.org/")
        node_available = False

    # Install Python dependencies
    install(ctx, dev=True)

    # Install Node.js dependencies
    if node_available:
        npm_install(ctx)

    # Install pre-commit hooks
    precommit(ctx, install=True)

    print("Development environment setup complete!")
    if node_available:
        print("Both Python and JavaScript tooling available.")
    else:
        print("Python tooling available. Install Node.js for JavaScript tools.")
    print("Run 'inv dev' to start the development server.")


@task
def venv(ctx, python="3.11"):
    """Create virtual environment with uv."""
    print(f"Creating virtual environment with Python {python}...")
    ctx.run(f"uv venv --python {python}")


@task
def help(ctx):
    """Show help information."""
    print("Lightweight Charts Development Tasks")
    print("===================================")
    print()
    print("Quick start:")
    print("  inv setup     - Set up development environment")
    print("  inv dev       - Start development server")
    print("  inv test      - Run tests")
    print("  inv check-all - Run all quality checks")
    print()
    print("Use 'inv --list' to see all available tasks")
    print("Use 'inv <task> --help' for help on specific tasks")
