#!/usr/bin/env python3
"""Compatibility wrapper for the packaged application entry point."""

from app.main import main

__all__ = ["main"]

if __name__ == "__main__":
    main()
