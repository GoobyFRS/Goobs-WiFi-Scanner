from pathlib import Path

from app.main import parse_public_ip_response
from models.network import NetworkRecord
from services.speedtest import _get_speedtest_commands, parse_speedtest_output
from services.wifi_scan import parse_wifi_output


def test_parse_public_ip_response_extracts_ip():
    result = parse_public_ip_response('{"ip": "203.0.113.42"}')

    assert result == "203.0.113.42"


def test_parse_speedtest_output_extracts_mbps_values():
    raw_output = """
    Ping: 12.45 ms
    Download: 95.76 Mbit/s
    Upload: 24.11 Mbit/s
    """

    result = parse_speedtest_output(raw_output)

    assert result.download_mbps == 95.76
    assert result.upload_mbps == 24.11


def test_parse_wifi_output_extracts_network_details():
    raw_output = """
    SSID 1 : Home WiFi
    BSSID 1 : AA:BB:CC:DD:EE:FF
    Signal: 82%
    Channel: 11
    SSID 2 : Guest
    BSSID 2 : 11:22:33:44:55:66
    Signal: 51%
    Channel: 6
    """

    result = parse_wifi_output(raw_output)

    assert result[0] == NetworkRecord(
        ssid="Home WiFi",
        mac_address="AA:BB:CC:DD:EE:FF",
        signal_strength="82%",
        channel="11",
    )
    assert result[1] == NetworkRecord(
        ssid="Guest",
        mac_address="11:22:33:44:55:66",
        signal_strength="51%",
        channel="6",
    )


def test_get_speedtest_commands_prefers_project_venv(monkeypatch):
    project_root = Path(__file__).resolve().parents[1]
    expected = [
        str(project_root / "venv" / "Scripts" / "speedtest.exe"),
        "--json",
    ]

    real_exists = Path.exists

    def fake_exists(path: Path) -> bool:
        if str(path) == expected[0]:
            return True
        return real_exists(path)

    monkeypatch.setattr(Path, "exists", fake_exists, raising=False)

    commands = _get_speedtest_commands()

    assert commands[0] == expected
