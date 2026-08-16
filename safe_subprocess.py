"""Backward-compatible shim for the subprocess helper module."""

from utils.subprocess_utils import (
    DEFAULT_MAX_OUTPUT_CHARS,
    DEFAULT_TIMEOUT_SECONDS,
    _truncate_output,
    _validate_command,
    run_bounded_command,
)

__all__ = [
    "DEFAULT_MAX_OUTPUT_CHARS",
    "DEFAULT_TIMEOUT_SECONDS",
    "_truncate_output",
    "_validate_command",
    "run_bounded_command",
]
