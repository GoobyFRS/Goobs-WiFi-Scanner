# Goobs WiFi Scanner

A lightweight 802.11 Wireless Network Scanner and Analysis Tool for Windows 10/ Windows 11 devices. Goobs WiFi Scanner is designed as a modern replacement for Homedale, providing a user-friendly GUI for wireless network analysis.

Goobs WiFi Scanner helps IT Technicians perform simple analysis of retail wireless networks. It's particularly useful for:

- Locating dead-zones and areas of poor coverage.
- Identifying co-channel interference.
- Optimizing wireless network placement and configuration.
- Troubleshooting connectivity issues.

**Current Version:** 0.1.4

**Relase Date:** 2026.01.06

| **SSID** | **Broadcast MAC** | **Signal Strength**| **Channel** |
| --- | --- | --- | --- |
| Data | a1:b2:c3:e4:f6:78 | Percentage/100 | Data |

## Build Process

```shell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
pyinstaller --onefile --noconsole --name Goobs-WiFi-Scanner main.py
deactivate
```

### Screenshots

![GWS_Image](https://github.com/user-attachments/assets/0f1abe02-76d6-4750-b330-80fed9ae0d0b)

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
