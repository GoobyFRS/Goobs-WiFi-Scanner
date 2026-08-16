"""Build the packaged app using the runtime APP_VERSION from app/main.py."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
APP_MAIN_PATH = PROJECT_ROOT / "app" / "main.py"


def extract_version_from_app_main(path: Path = APP_MAIN_PATH) -> str:
    """Read the APP_VERSION constant from the app entry point.
    Args:
        path: Path to the Python file containing the APP_VERSION constant.
    Returns:
        The raw version string from the app entry point.
    Raises:
        ValueError: If the APP_VERSION constant is not found.
    """
    if not path.exists():
        raise FileNotFoundError(f"App file not found: {path}")

    content = path.read_text(encoding="utf-8")
    match = re.search(r"^APP_VERSION\s*=\s*[\"\']([^\"\']+)[\"\']", content, re.MULTILINE)
    if match is None:
        raise ValueError(f"Could not find APP_VERSION in {path}")
    return match.group(1).strip()


def normalize_version(version: str) -> str:
    """Remove a leading 'v' for PyInstaller naming compatibility.
    Args:
        version: Version string to normalize.
    Returns:
        The normalized version string.
    Raises:
        TypeError: If the input is not a string.
        ValueError: If the input is blank after trimming.
    """
    if not isinstance(version, str):
        raise TypeError("version must be a string.")

    normalized = version.strip()
    if not normalized:
        raise ValueError("version cannot be empty.")

    return normalized.lstrip("vV")


def main() -> int:
    """Build the packaged Windows executable using the app APP_VERSION value."""
    version = normalize_version(extract_version_from_app_main())
    executable_name = f"Goobs-WiFi-Scanner-{version}"
    command = [
        "pyinstaller",
        "--onefile",
        "--noconsole",
        "--icon",
        "assets\\icon.ico",
        "--name",
        executable_name,
        "main.py",
    ]

    print(f"Building {executable_name} from app/main.py APP_VERSION={version}")
    result = subprocess.run(command, cwd=str(PROJECT_ROOT), check=False)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
