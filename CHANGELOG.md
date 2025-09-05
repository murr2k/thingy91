# Changelog

All notable changes to the Nordic Thingy91 IoT Development Project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Git project structure with comprehensive documentation
- .gitignore file for Nordic SDK projects
- README.md with current project status and quick start guides
- CHANGELOG.md for project history tracking

### Changed
- Migrated development from WSL Ubuntu to Windows host for native USB access
- Updated documentation to reflect current operational status

## [1.1.0] - 2025-09-03

### Added
- Asset Tracker v2 firmware deployment
- nRF Cloud integration for real-time telemetry
- GPS location tracking (±400m accuracy)
- Environmental sensor monitoring (temperature, humidity, pressure, air quality)
- LED status indicators for network and GPS states
- PowerShell monitoring scripts for asset tracker

### Fixed
- USB device descriptor issues by reflashing nRF52840 connectivity bridge
- UART communication by disconnecting J-Link during operation

### Changed
- Primary firmware from Serial LTE Modem to Asset Tracker v2
- Debugging approach to include J-Link disconnection requirement

## [1.0.2] - 2025-09-02

### Added
- SoftSIM firmware build with Nordic SDK v3.0.2
- Onomondo profile integration in prj.conf
- West workspace initialization scripts

### Fixed
- SDK version compatibility (v3.0.2 required, not v3.1.0)
- Build configuration for Thingy91 board target

### Known Issues
- SoftSIM UART interface not responding
- AT%SOFTSIM commands returning ERROR

## [1.0.1] - 2025-09-01

### Added
- Windows host development environment setup
- J-Link EDU Mini debugging configuration
- PowerShell scripts for COM port testing
- Flash scripts for both nRF52840 and nRF9160

### Changed
- Development environment from WSL to Windows native
- J-Link speed limited to 2000 kHz for EDU Mini

### Fixed
- USB connectivity by flashing connectivity bridge firmware
- COM port detection in Windows Device Manager

## [1.0.0] - 2025-08-30

### Added
- Initial project setup with Nordic Thingy91
- iBasis physical SIM configuration (ICCID: 8931080019073552599F)
- Serial LTE Modem firmware for AT command interface
- Basic AT command testing scripts
- Connection to TELUS network in Canada

### Changed
- Battery removed due to degradation (USB power only)

### Known Issues
- Onomondo SoftSIM not detecting (returns %XSIM: 0,9)
- Battery monitoring shows 0% (battery disconnected)

## [0.2.0] - 2025-08-25

### Added
- Onomondo SoftSIM profile decryption
- SoftSIM integration attempts with Serial LTE Modem
- Research documentation on SoftSIM requirements

### Known Issues
- SoftSIM not recognized by modem firmware
- AT%SOFTSIM commands not available

## [0.1.0] - 2025-08-20

### Added
- Initial hardware setup
- Nordic Thingy91 device configuration
- SEGGER J-Link EDU Mini integration
- Ubuntu 22.04 WSL development environment
- Basic project structure

### Notes
- Project inception with dual SIM approach (physical + software)
- Research phase for Onomondo SoftSIM technology

---

## Version History Summary

- **v1.1.0**: Asset Tracker v2 operational with nRF Cloud
- **v1.0.x**: SoftSIM development and debugging phase
- **v0.x.x**: Initial setup and research phase

## Key Milestones

- ✅ 2025-09-03: Successfully deployed Asset Tracker v2 with full telemetry
- ✅ 2025-09-03: GPS fix achieved, accurate location tracking
- ✅ 2025-09-02: Built SoftSIM firmware with SDK v3.0.2
- ✅ 2025-09-01: Recovered USB functionality on Windows host
- ✅ 2025-08-30: iBasis SIM connected to cellular network
- 🔧 Ongoing: SoftSIM UART debugging and AT interface implementation