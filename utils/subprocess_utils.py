"""Safe subprocess helpers for bounded command execution."""

from __future__ import annotations

import os
import subprocess
from collections.abc import Sequence

DEFAULT_TIMEOUT_SECONDS = 15.0
DEFAULT_MAX_OUTPUT_CHARS = 65536


def _validate_command(command: Sequence[str] | str) -> list[str]:
    """Validate that a command is argv-based and not a shell command string.

    Args:
        command: The command to validate as a sequence of arguments.

    Returns:
        A normalized list of argument strings.

    Raises:
        ValueError: If the command is empty, blank, or passed as a shell string.
        TypeError: If the command is not a sequence of strings.
    """
    if isinstance(command, (str, bytes, bytearray)):
        raise ValueError("Unsafe command: pass a list of arguments instead of a shell string.")

    if not isinstance(command, Sequence):
        raise TypeError("Command must be a sequence of argument strings.")

    normalized_command = [str(part) for part in command]
    if not normalized_command or any(not part.strip() for part in normalized_command):
        raise ValueError("Command cannot be empty or contain blank arguments.")

    return normalized_command


def _truncate_output(output: str | None, limit: int) -> str:
    """Trim output to a safe maximum while preserving readability.

    Args:
        output: The raw subprocess output to sanitize.
        limit: Maximum number of characters to retain.

    Returns:
        The output with a truncation marker inserted if it exceeds the limit.
    """
    if output is None:
        return ""

    if len(output) <= limit:
        return output

    suffix = "... [truncated]"
    available = max(limit - len(suffix), 0)
    return output[:available] + suffix


def run_bounded_command(
    command: Sequence[str] | str,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    max_output_chars: int = DEFAULT_MAX_OUTPUT_CHARS,
) -> subprocess.CompletedProcess[str]:
    """Run a subprocess without a shell with strict time and output limits.

    Args:
        command: An argv-style command sequence.
        timeout_seconds: Maximum time in seconds allowed for the subprocess to run.
        max_output_chars: Maximum number of output characters captured from stdout and stderr.

    Returns:
        The completed subprocess result object.

    Raises:
        ValueError: If the command or limits are invalid.
        subprocess.TimeoutExpired: If the child process exceeds the timeout.
    """
    validated_command = _validate_command(command)

    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be greater than zero.")

    if max_output_chars <= 0:
        raise ValueError("max_output_chars must be greater than zero.")

    startupinfo = None
    creationflags = 0
    if os.name == "nt":
        # Hide console-based tools such as netsh so a GUI app does not flash a cmd window.
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)

    completed = subprocess.run(
        validated_command,
        capture_output=True,
        check=False,
        text=True,
        stdin=subprocess.DEVNULL,
        timeout=timeout_seconds,
        shell=False,
        startupinfo=startupinfo,
        creationflags=creationflags,
    )

    completed.stdout = _truncate_output(completed.stdout, max_output_chars)
    completed.stderr = _truncate_output(completed.stderr, max_output_chars)
    return completed
