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
│  ├─ test_build_app.py
│  ├─ test_safe_subprocess.py
│  └─ test_wifi_scan.py
├─ utils/
│  ├─ __init__.py
│  └─ subprocess_utils.py
├─ build_app.py
├─ main.py
├─ pyproject.toml
├─ README.md
├─ requirements.txt
├─ LICENSE
└─ .github/
   ├─ workflows/
   └─ dependabot.yml
```

## Build Process

The project requires Python 3.10 or newer. The normal development setup is:

```shell
python -m venv venv
venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

`build_app.py` is the canonical packaging entry point. It reads `APP_VERSION`
from `app/main.py`, removes a leading `v` if present, and invokes PyInstaller
with the following options:

```powershell
python build_app.py
```

The build creates a single-windowed executable with the application icon and a
versioned name such as `Goobs-WiFi-Scanner-0.5.4`. The equivalent PyInstaller
command is:

```powershell
pyinstaller --onefile --noconsole --icon "assets\icon.ico" --name "Goobs-WiFi-Scanner-0.5.4" main.py
```

The runtime version is defined in `app/main.py`; `pyproject.toml` must contain
the same value. `tests/test_build_app.py` verifies that these two values stay
aligned. The build script uses `main.py` at the project root as the PyInstaller
entry point, which delegates to the package application.

## Runtime Flow

1. The root `main.py` imports and calls `app.main.main()`.
2. `app/main.py` creates a 720x480 Tkinter window, builds the File and Help
   menus, and creates the network table, metadata fields, footer, and speed-test
   controls.
3. The first Wi-Fi scan and public-IP lookup start on daemon worker threads so
   the Tk event loop remains responsive.
4. Worker threads return results to Tk with `root.after(0, ...)`; widgets are
   updated only on the Tk thread.
5. Scan results are sorted by signal strength, rendered in the Treeview, and
   followed by another scan six seconds later.
6. The public IP is refreshed every 60 seconds and displayed beside the footer
   timestamp. The timestamp itself refreshes once per second.
7. The window remains active until the user selects File > Exit or closes it.

## Scan Logic

The Wi-Fi scan path is:

- `services/wifi_scan.py` builds `netsh wlan show networks mode=bssid` and sets
  a 15-second timeout.
- `utils/subprocess_utils.py` validates the argv list, runs with `shell=False`,
  redirects stdin, hides console windows on Windows, applies the timeout, and
  truncates captured output to 65,536 characters per stream.
- `parse_wifi_output()` walks the raw `netsh` output line by line. It identifies
  SSID, BSSID, signal percentage, and channel lines and creates one
  `NetworkRecord` for each BSSID. Blank SSIDs are represented as `Hidden SSID`.
- `models/network.py` stores `ssid`, `mac_address`, `signal_strength`, and
  `channel`. Missing signal or channel values remain `No Data`.
- `app/main.py` sorts records from strongest to weakest signal, inserts them
  into the Treeview, and applies strong, good, fair, or weak color tags.

If `netsh` returns a non-zero exit code, the scan is treated as failed, the
table is cleared, and the GUI shows the error in the timestamp area.

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

## Other Features

- **CSV export:** File > Export CSV opens a save dialog and writes the current
   Treeview rows with SSID, MAC Address, Signal Strength, and Channel columns.
- **Internet speed test:** The lower-right Speed Test control runs a compatible
   `speedtest-cli` executable in a daemon thread with a 35-second timeout. It
   supports JSON and text output, displays upload/download values in Mbps, and
   shows idle, running, success, or error status through the colored indicator.
- **Public IP status:** The footer fetches the public IP from ipify in the
   background and reports `unavailable` when the request fails.
- **Signal analysis:** Networks are displayed strongest first and receive
   visual Treeview tags for strong (80%+), good (65-79%), fair (50-64%), and
   weak (0-49%) signal levels.
- **Troubleshooting metadata:** Reference and Department fields provide
   placeholders for associating a scan with an incident or work area.
- **Help links:** Help > Check for Updates, Report an Issues, and Open Wiki
   open the corresponding project pages in the default browser.
- **Testing and maintenance:** The repository includes pytest coverage for build
   version helpers, Wi-Fi parsing, speed-test error propagation, and bounded
   subprocess behavior. Runtime dependencies and the optional development test
   dependency are declared in `pyproject.toml` and `requirements.txt`.

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
