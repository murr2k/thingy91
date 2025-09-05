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

## Current Status (September 5, 2025)

### ✅ **Phase 1 Complete: Asset Tracker v2 Baseline**
- **SDK**: Nordic Connect SDK (NCS) v2.9.1 with compatible toolchain v2.8.0
- **Bootloader**: MCUBoot secure bootloader successfully integrated
- **Application**: Asset Tracker v2 with TF-M (Trusted Firmware-M) security
- **Build System**: Sysbuild multi-image compilation working
- **Flashing**: Successfully deployed to device via J-Link
- **Status**: **OPERATIONAL** - Asset Tracker application running successfully

### 🔧 **Phase 2 Ready: SoftSIM Integration**
- Baseline foundation established and verified
- Ready to integrate Onomondo SoftSIM module
- Build system prepared for external module inclusion

## Project Architecture

### Build System Organization
- **Project Repository**: `/home/murr2k/projects/thingy91/` (This repository)
- **NCS Workspace**: `/home/murr2k/ncs/v2.9.1/` (Nordic Connect SDK installation)
- **Build Output**: `/home/murr2k/ncs/v2.9.1/build/` (Compiled firmware)
- **Source Code**: `asset_tracker_v2_source/` (Modified Nordic Asset Tracker v2)

### Key Components
- **MCUBoot Bootloader**: Secure firmware updates capability
- **TF-M Security**: ARM TrustZone-M secure/non-secure partition
- **Asset Tracker v2**: Complete IoT application with cellular, GPS, and sensors
- **West Build System**: Nordic's multi-repository build and package manager

## Quick Start

### Prerequisites
- Nordic nRF Connect SDK v2.9.1
- Compatible toolchain v2.8.0 (use nRF Connect Toolchain Manager)
- SEGGER J-Link v8.64a+
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

## Documentation Index

### 📋 **Core Documentation**
- **[README.md](README.md)** - This file: Project overview and quick start guide
- **[CHANGELOG.md](CHANGELOG.md)** - Project version history and changes
- **[PROJECT_PLAN.md](PROJECT_PLAN.md)** - Development roadmap and milestones
- **[PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)** - Detailed project organization
- **[DEVELOPMENT_LOG.md](DEVELOPMENT_LOG.md)** - Development progress and decisions

### 🔧 **Build & Development**
- **[mcuboot_debug_resolution.md](mcuboot_debug_resolution.md)** - MCUBoot bootloader troubleshooting guide
- **[west_command_notes.md](west_command_notes.md)** - West build system usage and troubleshooting
- **[jlink_edu_mini_facts.md](jlink_edu_mini_facts.md)** - J-Link EDU Mini hardware limitations and setup
- **[vscode_installation_steps.md](vscode_installation_steps.md)** - Development environment setup

### 🌐 **SoftSIM Integration (Phase 2)**
- **[ONOMONDO_SOFTSIM_SETUP.md](ONOMONDO_SOFTSIM_SETUP.md)** - Onomondo SoftSIM integration guide
- **[nrf_connect_softsim_guide.md](nrf_connect_softsim_guide.md)** - NCS-specific SoftSIM implementation
- **[softsim_firmware_analysis.md](softsim_firmware_analysis.md)** - SoftSIM firmware architecture analysis
- **[softsim_options_comparison.md](softsim_options_comparison.md)** - SoftSIM vs physical SIM comparison
- **[softsim_status_report.md](softsim_status_report.md)** - Current SoftSIM implementation status

### 📊 **Status Reports & Analysis**
- **[success_report.md](success_report.md)** - Successful implementations summary
- **[cellular_connection_success.md](cellular_connection_success.md)** - Cellular connectivity achievements
- **[nrf_cloud_sim_report.md](nrf_cloud_sim_report.md)** - nRF Cloud integration status
- **[onomondo_account_report.md](onomondo_account_report.md)** - Onomondo service configuration

### 🔐 **Security & Credentials**
- **[SECRETS_MANAGEMENT.md](SECRETS_MANAGEMENT.md)** - Comprehensive credentials management
- **[SECRETS_QUICKSTART.md](SECRETS_QUICKSTART.md)** - Quick setup for credentials
- **[SECRETS_CUSTOM.md](SECRETS_CUSTOM.md)** - Custom credential configuration
- **[secrets_gui/](secrets_gui/)** - GUI-based secrets management system

### 🧪 **Testing Framework**
- **[test_plan.md](test_plan.md)** - Overall testing strategy
- **[tests/](tests/)** - Comprehensive testing documentation:
  - **[unit_tests.md](tests/unit_tests.md)** - Component-level testing
  - **[integration_tests.md](tests/integration_tests.md)** - System integration testing
  - **[system_tests.md](tests/system_tests.md)** - End-to-end system validation
  - **[performance_benchmarking.md](tests/performance_benchmarking.md)** - Performance metrics
  - **[power_consumption_tests.md](tests/power_consumption_tests.md)** - Battery life analysis

### 🛠️ **Environment Setup**
- **[SETUP_WSL_WINDOWS.md](SETUP_WSL_WINDOWS.md)** - Windows WSL development environment
- **[bootloader_recovery_guide.md](bootloader_recovery_guide.md)** - Device recovery procedures
- **[thingy91_troubleshooting.md](thingy91_troubleshooting.md)** - Hardware troubleshooting

### 📈 **Project History**
- **[DEMO_OVERVIEW.md](DEMO_OVERVIEW.md)** - Demonstration and proof-of-concept results
- **[sdk_compatibility_update.md](sdk_compatibility_update.md)** - SDK version compatibility matrix

## Project Structure
```
thingy91/                                    # This Git repository
├── asset_tracker_v2_source/                # Modified Nordic Asset Tracker v2 source
│   ├── src/                                 # Application source code
│   ├── sysbuild/                           # Multi-image build configuration
│   └── boards/                             # Board-specific configurations
├── modules/                                 # External modules (SoftSIM when integrated)
├── build/                                  # Local build artifacts
├── tests/                                  # Testing framework and scripts
├── secrets_gui/                            # Credential management system
├── scripts/                                # Utility scripts and automation
├── *.md                                    # Documentation (see index above)
├── west.yml                                # West workspace manifest
└── .gitignore                              # Git ignore rules

External Dependencies:
├── /home/murr2k/ncs/v2.9.1/               # Nordic Connect SDK workspace
│   ├── build/                              # Actual firmware build output
│   ├── nrf/                                # Nordic SDK modules
│   ├── zephyr/                             # Zephyr RTOS
│   └── ...                                 # Other NCS components
└── /home/murr2k/ncs/toolchains/           # NCS toolchain installations
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