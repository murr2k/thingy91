# Nordic Thingy91 IoT Development Project

## Overview
This project implements cellular IoT connectivity solutions for the Nordic Thingy91 multi-sensor prototyping platform, supporting both physical SIM (iBasis) and software-defined SIM (Onomondo SoftSIM) configurations.

## Hardware
- **Device**: Nordic Thingy91 (nRF9160 + nRF52840)
- **Debugger**: SEGGER J-Link EDU Mini
- **SIM Options**:
  - Physical: iBasis Global IoT SIM (ICCID: 8931080019073552599F)
  - Software: Onomondo SoftSIM (profile configured)
- **Battery**: Disconnected (degraded, running on USB power only)

## Current Status (September 3, 2025)

### ✅ Physical SIM (iBasis) - OPERATIONAL
- Connected via TELUS network (Canada) 
- Location: Surrey/Langley, BC (49.02874/-122.86633)
- Signal: -100 dBm RSRP
- Successfully transmitting to nRF Cloud:
  - GPS coordinates (±400m accuracy)
  - Temperature: 27.46°C
  - Humidity: 54.79%
  - Air Quality: 50 AQI
  - Pressure: 100688 Pa
- LED Status: Blue heartbeat (GPS tracking active)

### 🔧 SoftSIM (Onomondo) - IN DEVELOPMENT
- Firmware built with SDK v3.0.2
- Profile decrypted and integrated
- UART interface debugging pending

## Quick Start

### Prerequisites
- Nordic nRF Connect SDK v3.0.2
- SEGGER J-Link v8.66+
- Python 3.8+
- West build tool

### Flashing Prebuilt Firmware

#### Asset Tracker v2 (Full IoT Demo)
```bash
# Connect J-Link, SW2 in nRF91 position
JLink.exe -device nRF9160_xxAA -if SWD -speed 2000 -autoconnect 1 -CommandFile flash_asset_tracker.jlink

# After flashing:
# 1. Disconnect J-Link
# 2. Power cycle device
# 3. Monitor data at app.nrfcloud.com
```

#### Serial LTE Modem (AT Commands)
```bash
JLink.exe -device nRF9160_xxAA -if SWD -speed 2000 -autoconnect 1 -CommandFile flash_nrf9160_at_host.jlink
```

### Important Hardware Notes
- **SW2 Debug Switch**: Controls J-Link target
  - nRF91 position → Programs nRF9160 (main processor)
  - nRF52 position → Programs nRF52840 (USB bridge)
- **J-Link Interference**: Must disconnect J-Link for UART to work
- **Power Cycle**: Required after flashing

## Serial Communication

| Port   | Purpose           | Baud  | Settings      |
|--------|-------------------|-------|---------------|
| COM10  | Log/Trace Output  | 115200| 8N1, No flow  |
| COM11  | AT Commands       | 115200| 8N1, DTR/RTS  |

## LED Status Indicators
- 🔴 **Red Pulse**: Searching for network
- 🟢 **Green Heartbeat**: Connected to cellular network
- 🔵 **Blue Heartbeat**: GPS active and tracking
- 🟡 **Yellow**: Initializing
- ⚫ **Off**: Error or no power

## AT Command Examples
```bash
AT                  # Test communication
AT%XSIM?           # Check SIM status (0=physical, 1=eSIM)
AT+CIMI            # Get IMSI
AT+CGPADDR         # Get IP address
AT+CEREG?          # Network registration status
AT+COPS?           # Current operator
AT+CSQ             # Signal quality
```

## Project Structure
```
thingy91/
├── firmware/
│   ├── asset_tracker_v2.hex       # Full IoT application
│   ├── serial_lte_modem.hex       # AT command interface
│   └── connectivity_bridge.hex     # nRF52 USB bridge
├── softsim/
│   ├── profile.conf                # Onomondo configuration
│   └── build/                      # SoftSIM firmware builds
├── scripts/
│   ├── test_com.ps1                # UART testing
│   ├── monitor_asset_tracker.ps1   # Application monitor
│   └── flash_*.jlink               # J-Link scripts
├── docs/
│   └── status_reports/             # Project history
├── .gitignore
├── README.md
├── CHANGELOG.md
└── west.yml
```

## Troubleshooting

### No UART Response
1. **Disconnect J-Link** (critical!)
2. Power cycle device (unplug/replug USB)
3. Wait 10-15 seconds for initialization
4. Check Windows Device Manager for COM ports

### Network Connection Issues
- Verify physical SIM card seated properly
- Check antenna connections (both LTE and GPS)
- Confirm sufficient signal strength (>-110 dBm)
- For iBasis: APN is "ibasis.iot"

### GPS Issues
- Device needs clear sky view
- First fix can take 30-120 seconds
- Blue LED indicates GPS is active
- Check location updates on nRF Cloud

## Development Notes

### Building SoftSIM Firmware
```bash
# Initialize SoftSIM workspace
cd ~/softsim_workspace
west init -m https://github.com/onomondo/nrf-softsim.git
west update

# Configure profile in prj.conf
CONFIG_SOFTSIM_STATIC_PROFILE="<your_profile_hex>"

# Build
west build -b thingy91/nrf9160/ns samples/softsim_static_profile -p
```

### Known Issues
- Battery monitoring shows 0% (battery disconnected)
- SoftSIM AT interface not yet implemented in sample
- UART requires J-Link disconnection
- J-Link EDU Mini limited to 2000 kHz speed

## Resources
- [Nordic Thingy91 Docs](https://docs.nordicsemi.com/bundle/ug_thingy91)
- [nRF Connect SDK](https://developer.nordicsemi.com/nRF_Connect_SDK/)
- [Onomondo SoftSIM](https://github.com/onomondo/nrf-softsim)
- [nRF Cloud Dashboard](https://app.nrfcloud.com)
- [iBasis IoT Portal](https://portal.ibasis.com)

## License
Proprietary and third-party licenses apply. See individual source files.

## Author
Murray Kopit (murr2k@gmail.com)

## Acknowledgments
- Nordic Semiconductor for Thingy91 platform
- iBasis for global IoT connectivity
- Onomondo for SoftSIM technology
- SEGGER for J-Link tools