"""Tests for build metadata helpers."""

import tomllib
from pathlib import Path

import pytest

import build_app


def test_project_version_matches_app_version():
    """The project metadata must stay aligned with the runtime APP_VERSION."""
    app_version = build_app.extract_version_from_app_main()
    pyproject_path = Path(__file__).resolve().parents[1] / "pyproject.toml"
    project_version = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))["project"]["version"]

    assert project_version == app_version


def test_extract_app_version_uses_main_module_value():
    """The build helper should read the app's runtime version constant."""
    version = build_app.extract_version_from_app_main()

    assert version == "0.5.4"


@pytest.mark.parametrize(
    ("value", "expected"),
    [("v0.5.4", "0.5.4"), ("0.5.4", "0.5.4"), ("  v0.5.4  ", "0.5.4")],
)
def test_normalize_version_strips_v_prefix(value, expected):
    """Version normalization should remove a leading v and trim whitespace."""
    assert build_app.normalize_version(value) == expected


def test_normalize_version_rejects_invalid_input():
    """Invalid version values should fail fast instead of producing bad names."""
    with pytest.raises((TypeError, ValueError)):
        build_app.normalize_version("")
    with pytest.raises(TypeError):
        build_app.normalize_version(None)
