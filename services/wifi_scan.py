"""Wi-Fi scanning and parsing logic for Windows networks."""

from __future__ import annotations

import re

from models.network import NetworkRecord
from utils.subprocess_utils import run_bounded_command

def parse_wifi_output(raw_output: str) -> list[NetworkRecord]:
    """Parse raw Windows netsh output into structured network records.
    Args:
        raw_output: The stdout content returned from the netsh Wi-Fi scan command.
    Returns:
        A list of parsed network records with SSID, BSSID, signal strength, and channel.
    """
    networks: list[NetworkRecord] = []
    current_ssid: str | None = None
    current_bssid: str | None = None

    for line in raw_output.split("\n"):
        cleaned = line.strip()
        ssid_match = re.match(r"SSID \d+ : (.+)", cleaned)
        bssid_match = re.match(r"BSSID \d+ *: ([0-9A-Fa-f:-]+)", cleaned)
        signal_match = re.match(r"Signal\s*:\s*(\d+)%", cleaned)
        channel_match = re.match(r"Channel\s*:\s*(\d+)", cleaned)

        if ssid_match:
            current_ssid = ssid_match.group(1).strip() or "Hidden SSID"
        elif bssid_match and current_ssid:
            current_bssid = bssid_match.group(1)
            networks.append(NetworkRecord(ssid=current_ssid, mac_address=current_bssid))
        elif signal_match and current_bssid:
            networks[-1].signal_strength = f"{signal_match.group(1)}%"
        elif channel_match and current_bssid:
            networks[-1].channel = channel_match.group(1)

    return networks

def scan_wifi_networks() -> list[NetworkRecord]:
    """Run the Windows Wi-Fi scan and return parsed network records.
    Returns:
        A list containing all discovered wireless networks.
    Raises:
        RuntimeError: If the netsh command returns a non-zero exit code.
    """
    command = ["netsh", "wlan", "show", "networks", "mode=bssid"]
    result = run_bounded_command(command, timeout_seconds=15)

    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "netsh returned a non-zero exit code.")

    return parse_wifi_output(result.stdout)
