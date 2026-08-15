from models.network import NetworkRecord
from services.wifi_scan import parse_wifi_output


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

    assert result[0] == NetworkRecord(ssid="Home WiFi", mac_address="AA:BB:CC:DD:EE:FF", signal_strength="82%", channel="11")
    assert result[1] == NetworkRecord(ssid="Guest", mac_address="11:22:33:44:55:66", signal_strength="51%", channel="6")
