# Goobs WiFi Scanner

A lightweight 802.11 Wireless Network Scanner and Analysis Tool for Windows devices. Goobs WiFi Scanner is designed as a modern replacement for Homedale, providing a user-friendly GUI for wireless network analysis.

Goobs WiFi Scanner helps IT Technicians perform simple analysis of retail wireless networks. It's particularly useful for:

- Locating dead-zones and areas of poor coverage.
- Identifying co-channel interference.
- Optimizing wireless network placement and configuration.
- Troubleshooting connectivity issues.

**Current Version:** 0.5.1

**Relase Date:** 2026.08.15

| **SSID** | **Broadcast MAC** | **Signal Strength** | **Channel** |
| --- | --- | --- | --- |
| Data | a1:b2:c3:e4:f6:78 | Percentage/100 | Data |

## Quick Start

```shell
python -m venv venv
venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python main.py
```

## Build Process

```powershell
python -m venv venv
venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
$version = python -c "import tomllib; print(tomllib.load(open('pyproject.toml','rb'))['project']['version'])"
pyinstaller --onefile --noconsole --icon "assets\icon.ico" --name "Goobs-WiFi-Scanner-$version" main.py
```

The packaged app entry point remains `main.py`, which forwards to the package entry point in `app/main.py`.

## Version Bump Flow

The project version is managed centrally in `pyproject.toml`. Update the `project.version` value there, then keep the runtime app metadata in sync.

```toml
[project]
version = "0.5.1"
```

If you need to bump the app version for the UI title, update the matching value in `app/__init__.py` and `app/main.py` to the same value.

```text
pyproject.toml           -> project.version
app/__init__.py          -> __version__
app/main.py              -> APP_VERSION
```

This keeps a single source of truth for release metadata while preserving the GUI display version.

## Project Layout

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
├─ safe_subprocess.py
├─ README.md
├─ requirements.txt
└─ LICENSE
```

### Screenshots

![GWS_Image](https://github.com/user-attachments/assets/f7a82210-8c43-47f5-90b8-c1bf56cf6e3f)

```txt
----------------------------------------
| File | Help |
----------------------------------------
| SSID          | MAC Address  | Signal | Channel |  ⬆⬇ Scrollbar
|--------------|--------------|--------|--------|
| WiFi-Home    | a1:b2:c3:e4:f6:68  | 67%    | 6      |
| Guest-Network| a1:b2:c3:e4:f6:69  | 45%    | 11     |
----------------------------------------
Reference:   [ INC000012345 ]
Department:  [ Mens Shoes   ]
[ Scan Wi-Fi ]
----------------------------------------
Last Updated: 14:35:21
```
