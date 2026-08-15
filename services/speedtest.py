"""Simple speedtest result parsing and execution helpers."""

from __future__ import annotations

import json
import re
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

from utils.subprocess_utils import run_bounded_command


@dataclass(frozen=True)
class SpeedtestResult:
    """Structured speedtest result data in megabits per second."""

    download_mbps: float
    upload_mbps: float


def parse_speedtest_output(raw_output: str) -> SpeedtestResult:
    """Parse a speedtest CLI response and extract download/upload in Mbps.
    Args:
        raw_output: Text returned by a speedtest-compatible CLI.
    Returns:
        A structured result with the upload and download speeds.
    Raises:
        ValueError: If the output does not contain parseable upload or download
            values.
    """
    download_match = re.search(
        "Download\\s*:\\s*(\\d+(?:\\.\\d+)?)\\s*"
        "(?:Mbit/s|Mbps|Mb/s)",
        raw_output,
        re.IGNORECASE,
    )
    upload_match = re.search(
        r"Upload\s*:\s*(\d+(?:\.\d+)?)\s*(?:Mbit/s|Mbps|Mb/s)",
        raw_output,
        re.IGNORECASE,
    )

    if not download_match or not upload_match:
        raise ValueError("Could not parse speedtest output.")

    download_mbps = float(download_match.group(1))
    upload_mbps = float(upload_match.group(1))
    return SpeedtestResult(
        download_mbps=download_mbps,
        upload_mbps=upload_mbps,
    )


def _extract_result_from_json(raw_output: str) -> SpeedtestResult:
    """Parse JSON output returned by speedtest endpoints or adapters."""
    payload = json.loads(raw_output)
    download_mbps = float(payload["download"])
    upload_mbps = float(payload["upload"])
    return SpeedtestResult(
        download_mbps=download_mbps / 1_000_000,
        upload_mbps=upload_mbps / 1_000_000,
    )


def _get_speedtest_commands() -> list[list[str]]:
    """Build the preferred command list for local speedtest execution.

    The resolver prefers locally installed executables in the active runtime,
    then the project venv when present, then generic PATH names and a bash shim.
    This keeps the app working both from source and from a frozen PyInstaller
    executable, where the repo layout is not always available.
    """
    project_root = Path(__file__).resolve().parents[1]
    candidates: list[list[str]] = []

    executable_names = ("speedtest.exe", "speedtest-cli.exe")

    if project_root.exists():
        venv_scripts = project_root / "venv" / "Scripts"
        for executable_name in executable_names:
            executable_path = venv_scripts / executable_name
            candidates.append([str(executable_path), "--json"])

    for executable_name in executable_names:
        resolved_path = shutil.which(executable_name)
        if resolved_path:
            candidates.append([resolved_path, "--json"])

    if sys.platform.startswith("win"):
        candidate_roots = [
            Path.home() / "AppData" / "Local" / "Programs" / "Python",
            Path.home() / "AppData" / "Local" / "Programs" / "Python" / "Python*",
        ]
        for root in candidate_roots:
            if not root.exists():
                continue
            for executable_name in executable_names:
                for match in root.glob(f"**/{executable_name}"):
                    if match.exists():
                        candidates.append([str(match), "--json"])

    candidates.extend(
        [
            ["speedtest-cli", "--json"],
            ["speedtest", "--json"],
            ["C:\\Windows\\System32\\bash.exe", "-lc", "speedtest --json"],
        ],
    )

    unique_commands: list[list[str]] = []
    seen: set[tuple[str, ...]] = set()
    for command in candidates:
        key = tuple(command)
        if key not in seen:
            unique_commands.append(command)
            seen.add(key)
    return unique_commands


def run_speedtest() -> SpeedtestResult:
    """Run a bounded internet speedtest and return download/upload numbers.
    Returns:
        The measured speeds in Mbps.
    Raises:
        RuntimeError: If no supported speedtest command is available or parsing
            fails.
    """
    commands = _get_speedtest_commands()

    last_error: Exception | None = None

    for command in commands:
        try:
            result = run_bounded_command(command, timeout_seconds=35)
            if result.returncode != 0:
                last_error = RuntimeError(
                    result.stderr.strip()
                    or "speedtest command returned a non-zero exit code.",
                )
                continue

            cleaned_output = result.stdout.strip()
            if not cleaned_output:
                continue

            if cleaned_output.startswith("{"):
                return _extract_result_from_json(cleaned_output)

            return parse_speedtest_output(cleaned_output)
        except (
            FileNotFoundError,
            OSError,
            ValueError,
            json.JSONDecodeError,
        ) as exc:
            last_error = exc

    if last_error is not None:
        raise RuntimeError(f"Speedtest failed: {last_error}")

    raise RuntimeError(
        "No supported speedtest command is available on this system.",
    )
