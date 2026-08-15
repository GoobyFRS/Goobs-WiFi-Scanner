"""Utility helpers shared by the application."""

from .subprocess_utils import (
    DEFAULT_MAX_OUTPUT_CHARS,
    DEFAULT_TIMEOUT_SECONDS,
    run_bounded_command,
)

__all__ = [
    "DEFAULT_MAX_OUTPUT_CHARS",
    "DEFAULT_TIMEOUT_SECONDS",
    "run_bounded_command",
]

__version__ = "0.1.5"
