"""Utility helpers shared by the application."""
__version__ = "1.0.0"
__all__ = [
    "DEFAULT_MAX_OUTPUT_CHARS",
    "DEFAULT_TIMEOUT_SECONDS",
    "run_bounded_command",]

from .subprocess_utils import (
    DEFAULT_MAX_OUTPUT_CHARS,
    DEFAULT_TIMEOUT_SECONDS,
    run_bounded_command,)
