#!/usr/bin/env python3
"""
DealFlow AI Copilot - Setup Validation Script

Validates that the project is properly configured and all dependencies are available.
Run this script after installation to verify everything is set up correctly.

Usage:
    python scripts/test_setup.py
"""

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class Colors:
    """ANSI color codes for terminal output."""

    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    BOLD = "\033[1m"
    RESET = "\033[0m"


def print_header(text: str) -> None:
    """Print a formatted header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 60}")
    print(f" {text}")
    print(f"{'=' * 60}{Colors.RESET}\n")


def print_check(name: str, passed: bool, details: str = "") -> None:
    """Print a check result."""
    status = f"{Colors.GREEN}PASS{Colors.RESET}" if passed else f"{Colors.RED}FAIL{Colors.RESET}"
    print(f"  [{status}] {name}")
    if details and not passed:
        print(f"         {Colors.YELLOW}{details}{Colors.RESET}")


def check_directories() -> tuple[int, int]:
    """Check that all required directories exist."""
    print_header("Checking Directories")

    required_dirs = [
        "app",
        "app/api",
        "app/agents",
        "app/core",
        "app/integrations",
        "app/models",
        "app/services",
        "app/utils",
        "tests",
        "scripts",
        "docs",
        "data",
        "data/uploads",
        "data/processed",
        "data/outputs",
        "prompts",
    ]

    passed = 0
    failed = 0

    for dir_name in required_dirs:
        dir_path = project_root / dir_name
        exists = dir_path.exists() and dir_path.is_dir()
        print_check(f"Directory: {dir_name}/", exists)
        if exists:
            passed += 1
        else:
            failed += 1

    return passed, failed


def check_files() -> tuple[int, int]:
    """Check that all required files exist."""
    print_header("Checking Files")

    required_files = [
        "requirements.txt",
        "pyproject.toml",
        ".gitignore",
        "Dockerfile",
        "docker-compose.yml",
        "app/__init__.py",
        "app/main.py",
        "app/config.py",
        "app/api/__init__.py",
        "app/api/health.py",
        "app/api/deals.py",
        "app/utils/__init__.py",
        "app/utils/logger.py",
        "app/utils/exceptions.py",
    ]

    passed = 0
    failed = 0

    for file_name in required_files:
        file_path = project_root / file_name
        exists = file_path.exists() and file_path.is_file()
        print_check(f"File: {file_name}", exists)
        if exists:
            passed += 1
        else:
            failed += 1

    return passed, failed


def check_env_file() -> tuple[int, int]:
    """Check environment file configuration."""
    print_header("Checking Environment Configuration")

    passed = 0
    failed = 0

    # Check .env.example exists
    env_example = project_root / ".env.example"
    exists = env_example.exists()
    print_check("File: .env.example", exists)
    if exists:
        passed += 1
    else:
        failed += 1

    # Check .env exists (warn if not)
    env_file = project_root / ".env"
    exists = env_file.exists()
    print_check(
        "File: .env",
        exists,
        "Copy .env.example to .env and configure" if not exists else "",
    )
    if exists:
        passed += 1
    else:
        # This is a warning, not a failure
        print(f"         {Colors.YELLOW}(Warning: .env not found, using defaults){Colors.RESET}")
        passed += 1  # Count as passed since .env.example exists

    return passed, failed


def check_dependencies() -> tuple[int, int]:
    """Check that required Python packages are importable."""
    print_header("Checking Python Dependencies")

    dependencies = [
        ("fastapi", "FastAPI framework"),
        ("uvicorn", "ASGI server"),
        ("pydantic", "Data validation"),
        ("pydantic_settings", "Settings management"),
        ("loguru", "Logging"),
        ("httpx", "HTTP client"),
        ("aiofiles", "Async file I/O"),
        ("pandas", "Data processing"),
        ("PyPDF2", "PDF processing"),
        ("PIL", "Image processing (Pillow)"),
        ("docx", "Word document processing"),
    ]

    passed = 0
    failed = 0

    for module_name, description in dependencies:
        try:
            __import__(module_name)
            print_check(f"{description} ({module_name})", True)
            passed += 1
        except ImportError as e:
            print_check(f"{description} ({module_name})", False, str(e))
            failed += 1

    return passed, failed


def check_app_import() -> tuple[int, int]:
    """Check that the FastAPI app can be imported."""
    print_header("Checking Application Import")

    passed = 0
    failed = 0

    # Check app package import
    try:
        import app

        print_check("Import: app package", True)
        print(f"         Version: {app.__version__}")
        passed += 1
    except Exception as e:
        print_check("Import: app package", False, str(e))
        failed += 1

    # Check config import
    try:
        from app.config import settings

        print_check("Import: app.config.settings", True)
        print(f"         App name: {settings.app_name}")
        passed += 1
    except Exception as e:
        print_check("Import: app.config.settings", False, str(e))
        failed += 1

    # Check main app import
    try:
        from app.main import app as fastapi_app

        print_check("Import: app.main.app (FastAPI)", True)
        print(f"         Title: {fastapi_app.title}")
        passed += 1
    except Exception as e:
        print_check("Import: app.main.app (FastAPI)", False, str(e))
        failed += 1

    # Check utils import
    try:
        from app.utils import logger

        print_check("Import: app.utils.logger", True)
        passed += 1
    except Exception as e:
        print_check("Import: app.utils.logger", False, str(e))
        failed += 1

    # Check exceptions import
    try:
        from app.utils.exceptions import (
            AnalysisError,
            APIError,
            DealFlowBaseException,
            ExtractionError,
            ValidationError,
        )

        print_check("Import: app.utils.exceptions", True)
        passed += 1
    except Exception as e:
        print_check("Import: app.utils.exceptions", False, str(e))
        failed += 1

    return passed, failed


def check_google_ai() -> tuple[int, int]:
    """Check Google Generative AI package."""
    print_header("Checking Google AI Integration")

    passed = 0
    failed = 0

    try:
        import google.generativeai as genai

        print_check("Import: google.generativeai", True)
        passed += 1
    except ImportError as e:
        print_check("Import: google.generativeai", False, str(e))
        failed += 1

    return passed, failed


def main() -> int:
    """Run all setup validation checks."""
    print(f"\n{Colors.BOLD}DealFlow AI Copilot - Setup Validation{Colors.RESET}")
    print(f"Project root: {project_root}")

    total_passed = 0
    total_failed = 0

    # Run all checks
    checks = [
        check_directories,
        check_files,
        check_env_file,
        check_dependencies,
        check_app_import,
        check_google_ai,
    ]

    for check_func in checks:
        passed, failed = check_func()
        total_passed += passed
        total_failed += failed

    # Print summary
    print_header("Summary")
    print(f"  Total checks: {total_passed + total_failed}")
    print(f"  {Colors.GREEN}Passed: {total_passed}{Colors.RESET}")
    print(f"  {Colors.RED}Failed: {total_failed}{Colors.RESET}")

    if total_failed == 0:
        print(f"\n{Colors.GREEN}{Colors.BOLD}All checks passed! Setup is complete.{Colors.RESET}")
        print("\nTo start the server, run:")
        print(f"  {Colors.BLUE}uvicorn app.main:app --reload{Colors.RESET}")
        return 0
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}Some checks failed. Please fix the issues above.{Colors.RESET}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
