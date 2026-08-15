# Goobs WiFi Scanner Wiki

## Overview

Goobs WiFi Scanner is a lightweight Windows desktop application for inspecting nearby wireless networks. It is designed for IT technicians, MSP teams, and field installers who need a fast view of SSIDs, signal strength, BSSID information, and channel data.

The app is intentionally simple: a Tkinter interface, a bounded Windows `netsh` scan, and a small set of utilities for parsing and exporting results.

## Goals

- Provide a quick, readable Wi-Fi summary
- Work on Windows without heavy dependencies
- Keep subprocess execution safe and bounded
- Remain easy to test and maintain
- Support small operational troubleshooting use cases

## Project Structure

```text
Goobs-WiFi-Scanner/
├─ app/
│  ├─ __init__.py
│  └─ main.py
├─ models/
│  ├─ __init__.py
│  └─ network.py
├─ services/
│  ├─ __init__.py
│  └─ wifi_scan.py
├─ tests/
│  ├─ test_wifi_scan.py
│  └─ test_safe_subprocess.py
├─ utils/
│  ├─ __init__.py
│  └─ subprocess_utils.py
├─ main.py
├─ pyproject.toml
├─ README.md
├─ requirements.txt
├─ LICENSE
└─ .github/
   ├─ workflows/
   └─ dependabot.yml
```

## Runtime Flow

1. The app starts from `main.py`.
2. `main.py` loads the package entry point in `app/main.py`.
3. The GUI initializes and schedules an initial Wi-Fi scan.
4. The scan runs in a background thread.
5. The Windows `netsh wlan show networks mode=bssid` command is executed using a bounded subprocess helper.
6. Raw output is parsed into `NetworkRecord` objects.
7. Results are rendered in the Tkinter Treeview and can be exported to CSV.

## Wi-Fi Scan Logic

The scan path is:

- `services/wifi_scan.py` -> executes the Windows command
- `utils/subprocess_utils.py` -> enforces shell-free execution, timeout, and bounded output
- `models/network.py` -> stores the structured network data

This keeps the Wi‑Fi parsing and OS interaction separate from the GUI logic.

## Safety Notes

The subprocess helper intentionally avoids shell execution and validates command inputs before launch. It also:

- disables shell usage with `shell=False`
- enforces a timeout
- prevents unbounded output capture
- discards stdin to avoid interactive hangs

## Local Development

### Create the environment

```shell
python -m venv venv
venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### Run the app

```shell
python main.py
```

### Run tests

```shell
python -m pytest -q
```

## Build

```powershell
$version = python -c "import tomllib; print(tomllib.load(open('pyproject.toml','rb'))['project']['version'])"
pyinstaller --onefile --noconsole --icon "assets\icon.ico" --name "Goobs-WiFi-Scanner-$version" main.py
```

## Versioning

The project version is managed centrally in `pyproject.toml`.

```toml
[project]
version = "0.5.1"
```

For the UI title and package metadata, keep the matching values aligned in:

- `app/__init__.py`
- `app/main.py`

## Roadmap Highlights

The repository roadmap includes items such as:

- ping tool
- export improvements
- CodeQL support
- build artifact and release pipeline
- pyproject-based packaging improvements

## Future Ideas

Potential areas for expansion include:

- richer Wi-Fi diagnostics
- signal trend history
- filtering and sorting options
- CSV/JSON export improvements
- better packaging and installer workflows

## Related Files

- [README.md](../README.md)
- [docs/roadmap.md](roadmap.md)
- [pyproject.toml](../pyproject.toml)
