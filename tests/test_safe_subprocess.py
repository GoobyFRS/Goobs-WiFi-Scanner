import subprocess

import pytest

from safe_subprocess import run_bounded_command


def test_run_bounded_command_rejects_shell_style_input():
    with pytest.raises(ValueError, match="Unsafe command"):
        run_bounded_command("echo hello && whoami")


def test_run_bounded_command_executes_without_shell():
    result = run_bounded_command(
        ["python", "-c", "print('ok')"],
        timeout_seconds=10,
    )

    assert result.returncode == 0
    assert result.stdout.strip() == "ok"
    assert result.stderr == ""


def test_run_bounded_command_enforces_timeout_cap():
    with pytest.raises(subprocess.TimeoutExpired):
        run_bounded_command(
            ["python", "-c", "import time; time.sleep(30)"],
            timeout_seconds=0.1,
        )


def test_run_bounded_command_uses_windows_no_console_flags(monkeypatch):
    seen = {}

    class FakeStartupInfo:
        def __init__(self):
            self.dwFlags = 0
            self.wShowWindow = 0

    def fake_run(*args, **kwargs):
        seen["creationflags"] = kwargs.get("creationflags")
        seen["startupinfo"] = kwargs.get("startupinfo")

        class CompletedResult:
            stdout = ""
            stderr = ""
            returncode = 0

        return CompletedResult()

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(
        subprocess,
        "CREATE_NO_WINDOW",
        0x08000000,
        raising=False,
    )
    monkeypatch.setattr(
        subprocess,
        "STARTUPINFO",
        FakeStartupInfo,
        raising=False,
    )
    monkeypatch.setattr(
        subprocess,
        "STARTF_USESHOWWINDOW",
        0x00000001,
        raising=False,
    )
    monkeypatch.setattr(subprocess, "SW_HIDE", 0, raising=False)

    run_bounded_command(["echo", "ok"], timeout_seconds=1)

    assert seen["creationflags"] == subprocess.CREATE_NO_WINDOW
    assert seen["startupinfo"] is not None
