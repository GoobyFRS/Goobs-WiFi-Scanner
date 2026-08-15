"""Data model for wireless network results."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class NetworkRecord:
    """Represents a single discovered Wi-Fi network."""

    ssid: str
    mac_address: str
    signal_strength: str = "No Data"
    channel: str = "No Data"
