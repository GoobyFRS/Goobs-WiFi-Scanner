import types

from app import main as app_main
from models.network import NetworkRecord
from services.wifi_scan import parse_wifi_output


def test_apply_speedtest_result_uses_the_underlying_error_message(monkeypatch):
    """The UI should surface the real speedtest error instead of hiding it behind a generic failure."""
    captured = {}

    class FakeRoot:
        _speedtest_in_progress = False
        _last_speedtest_result = None

    app_main.root = FakeRoot()

    def fake_set_state(state, result=None, error_message=None):
        captured["state"] = state
        captured["result"] = result
        captured["error_message"] = error_message

    monkeypatch.setattr(app_main, "_set_speedtest_state", fake_set_state)

    app_main._apply_speedtest_result(None, "No internet connection")

    assert captured["state"] == "error"
    assert captured["error_message"] == "No internet connection"


def test_parse_wifi_output_extracts_network_details():
    """Ensure each Wi-Fi block is converted into a network record."""
    raw_output = """\
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
