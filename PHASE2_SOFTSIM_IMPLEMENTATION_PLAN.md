# Phase 2: Onomondo SoftSIM Integration Implementation Plan

**Project**: Nordic Thingy91 SoftSIM Integration  
**Phase**: 2 (SoftSIM Integration)  
**Branch**: `softsim`  
**Base**: v1.0.0 Asset Tracker v2 Baseline  
**Date**: September 5, 2025  

## Executive Summary

Phase 2 focuses on integrating Onomondo SoftSIM technology with our established Asset Tracker v2 baseline. This will enable software-defined cellular connectivity, eliminating the need for physical SIM cards while maintaining full IoT functionality.

## Technical Foundation

### Current Baseline (v1.0.0)
- ✅ **Nordic Connect SDK (NCS)**: v2.9.1
- ✅ **Toolchain**: v2.8.0 (compatible)
- ✅ **MCUBoot Bootloader**: Secure firmware updates
- ✅ **Asset Tracker v2**: Complete IoT application
- ✅ **TF-M Security**: ARM TrustZone-M implementation
- ✅ **Build System**: West with sysbuild multi-image support

### Target Platform
- **Hardware**: Nordic Thingy91 (nRF9160 + nRF52840)
- **Modem**: nRF9160 SiP with firmware v1.3.4+
- **Security**: PSA Certified Crypto API + TF-M
- **Storage**: Non-Volatile Storage (NVS) for profile management

## Onomondo SoftSIM Integration Guide Summary

### Key Technical Requirements
Based on [Onomondo's nRF91 Integration Guide](https://help.onomondo.com/en/articles/208415-how-to-integrate-the-onomondo-softsim-with-the-nrf91-series-from-nordic-semiconductor):

#### Prerequisites
- **SDK**: nRF Connect SDK v2.9.1 ✅ (Already configured)
- **Modem Firmware**: nRF91 SiP v1.3.4+ (Need to verify)
- **Security Framework**: TF-M ✅ (Already integrated)
- **Crypto API**: PSA Certified Crypto API ✅ (Available via TF-M)

#### Integration Components
- **SoftSIM Module**: Onomondo's open-source C-based UICC implementation
- **Profile Management**: Static or external profile provisioning
- **Key Management**: Hardware-backed key storage via KMU (Key Management Unit)
- **UART Interface**: For external profile transfer during development

### nrf-softsim Repository Analysis

Based on [https://github.com/onomondo/nrf-softsim](https://github.com/onomondo/nrf-softsim):

#### Repository Structure
```
nrf-softsim/
├── samples/
│   ├── softsim_external_profile/    # UART-based profile transfer
│   └── softsim_static_profile/      # Compiled-in profile
├── modules/lib/onomondo-softsim/    # Core SoftSIM library
├── west.yml                         # West manifest
└── README.md                        # Integration documentation
```

#### Key Configuration Requirements
- **Memory**: Minimum heap pool size of 30,000 bytes
- **Storage**: Cannot coexist with NVS backend settings (conflict resolution needed)
- **Partitioning**: Requires appropriate partition table configuration
- **Initialization**: Must call `nrf_softsim_init()` or use kernel boot configuration

#### Profile Provisioning Options

##### Option 1: Static Profile
```kconfig
CONFIG_SOFTSIM_STATIC_PROFILE_ENABLE=y
CONFIG_SOFTSIM_STATIC_PROFILE="011208091..."
```

##### Option 2: External Profile
- Profile transferred via UART during initialization
- More flexible for development and testing
- Requires secure profile delivery mechanism

## Phase 2 Implementation Strategy

### Stage 1: Environment Setup and Validation
**Timeline**: Days 1-2  
**Branch**: `softsim`

#### Tasks
1. **Verify Modem Firmware**
   - Check current nRF9160 modem firmware version
   - Update to v1.3.4+ if necessary
   - Document firmware update process

2. **West Workspace Integration**
   - Add Onomondo nrf-softsim repository to west.yml
   - Update workspace with `west update`
   - Resolve any dependency conflicts

3. **Build System Compatibility**
   - Test sysbuild with SoftSIM modules
   - Resolve any CMake configuration conflicts
   - Ensure MCUBoot compatibility

### Stage 2: Memory and Storage Configuration
**Timeline**: Days 3-4

#### Memory Optimization
1. **Heap Configuration**
   - Increase heap pool size to minimum 30,000 bytes
   - Analyze current Asset Tracker memory usage
   - Optimize memory allocation for SoftSIM + Asset Tracker

2. **Storage Backend Resolution**
   - Resolve NVS backend conflict with existing settings
   - Design partition layout for SoftSIM profile storage
   - Update memory map documentation

3. **TF-M Memory Layout**
   - Ensure TF-M secure/non-secure partition compatibility
   - Verify PSA crypto API accessibility for SoftSIM
   - Test key management unit (KMU) integration

### Stage 3: SoftSIM Module Integration
**Timeline**: Days 5-7

#### Core Integration
1. **Initialize SoftSIM Library**
   - Add `nrf_softsim_init()` to Asset Tracker initialization
   - Configure kernel boot integration
   - Implement error handling and fallback mechanisms

2. **Profile Management**
   - Start with external profile method for flexibility
   - Implement UART-based profile transfer
   - Add profile validation and error recovery

3. **API Integration**
   - Integrate SoftSIM filesystem operations
   - Connect SIM selection via AT commands
   - Ensure compatibility with existing Asset Tracker features

### Stage 4: Testing and Validation
**Timeline**: Days 8-10

#### Functional Testing
1. **SoftSIM Activation**
   - Test profile loading and key provisioning
   - Verify SIM registration with Onomondo platform
   - Validate cellular network connectivity

2. **Asset Tracker Integration**
   - Ensure GPS, sensors, and cloud connectivity work
   - Test data transmission with SoftSIM
   - Verify power management and sleep modes

3. **Reliability Testing**
   - Test modem power cycling
   - Verify profile persistence across reboots
   - Test recovery from network disconnections

### Stage 5: Documentation and Release Preparation
**Timeline**: Days 11-12

#### Documentation Updates
1. **Integration Guide**
   - Document SoftSIM setup process
   - Create troubleshooting guide
   - Update build instructions

2. **Configuration Reference**
   - Document all new Kconfig options
   - Create memory/storage configuration guide
   - Update west.yml documentation

## Technical Challenges and Mitigations

### Challenge 1: Memory Constraints
**Risk**: SoftSIM + Asset Tracker may exceed available memory
**Mitigation**: 
- Analyze and optimize current memory usage
- Implement conditional compilation for optional features
- Consider staged loading of SoftSIM components

### Challenge 2: NVS Backend Conflicts
**Risk**: SoftSIM NVS requirements conflict with existing settings
**Mitigation**:
- Design separate partition for SoftSIM storage
- Implement namespace isolation
- Test compatibility with existing Asset Tracker settings

### Challenge 3: Security Integration
**Risk**: TF-M integration complexity with SoftSIM crypto requirements
**Mitigation**:
- Leverage existing TF-M implementation from v1.0.0
- Test PSA crypto API compatibility
- Implement fallback security mechanisms

### Challenge 4: Build System Complexity
**Risk**: Sysbuild with MCUBoot + TF-M + SoftSIM integration complexity
**Mitigation**:
- Use proven v1.0.0 build system as foundation
- Incremental integration approach
- Maintain rollback capability to v1.0.0 baseline

## Success Criteria

### Functional Requirements
- [ ] SoftSIM successfully registers with Onomondo platform
- [ ] Cellular connectivity established via software SIM
- [ ] Asset Tracker functionality preserved (GPS, sensors, cloud)
- [ ] Secure profile provisioning working
- [ ] Power management and sleep modes functional

### Performance Requirements
- [ ] Network registration time ≤ 30 seconds
- [ ] Data transmission latency comparable to physical SIM
- [ ] Memory usage within available constraints
- [ ] Power consumption within 10% of baseline

### Quality Requirements
- [ ] Stable operation for 24+ hours continuous testing
- [ ] Recovery from network disconnections
- [ ] Profile persistence across power cycles
- [ ] Comprehensive error handling and logging

## Development Tools and Resources

### Required Tools
- **Onomondo CLI**: Profile generation and management
- **API Key**: Onomondo platform access
- **J-Link**: Hardware debugging and flashing
- **Serial Monitor**: UART profile transfer and debugging

### Useful Links
- **Onomondo Integration Guide**: https://help.onomondo.com/en/articles/208415-how-to-integrate-the-onomondo-softsim-with-the-nrf91-series-from-nordic-semiconductor
- **nrf-softsim Repository**: https://github.com/onomondo/nrf-softsim
- **Onomondo Platform**: https://app.onomondo.com
- **Nordic nRF Connect SDK**: https://developer.nordicsemi.com/nRF_Connect_SDK/
- **Support Contact**: support@onomondo.com

## Risk Assessment

### High Risk
- **Memory/Storage Integration**: Complex interaction between SoftSIM, Asset Tracker, and system storage
- **Security Framework**: TF-M + PSA crypto + SoftSIM integration complexity

### Medium Risk
- **Build System**: West + sysbuild + MCUBoot + SoftSIM complexity
- **Profile Management**: Secure and reliable profile provisioning

### Low Risk
- **Basic Connectivity**: SoftSIM cellular functionality (well-documented)
- **Platform Integration**: Onomondo platform compatibility (established APIs)

## Timeline Summary

| Stage | Duration | Key Deliverables |
|-------|----------|------------------|
| 1. Environment Setup | 2 days | Verified environment, updated dependencies |
| 2. Memory/Storage | 2 days | Optimized memory layout, resolved conflicts |
| 3. SoftSIM Integration | 3 days | Working SoftSIM + Asset Tracker |
| 4. Testing/Validation | 3 days | Validated functionality and reliability |
| 5. Documentation | 2 days | Complete documentation and release prep |

**Total Estimated Duration**: 12 days

## Deliverables

### Code Deliverables
- [ ] Updated `west.yml` with SoftSIM repository
- [ ] Modified Asset Tracker source with SoftSIM integration
- [ ] Updated memory and partition configurations
- [ ] SoftSIM initialization and profile management code
- [ ] Updated build system configuration

### Documentation Deliverables
- [ ] SoftSIM integration guide
- [ ] Updated configuration documentation
- [ ] Troubleshooting guide
- [ ] Memory layout documentation
- [ ] Testing results and validation report

### Release Deliverables
- [ ] Working firmware with SoftSIM + Asset Tracker
- [ ] Complete build and flash instructions
- [ ] Configuration examples and templates
- [ ] Validation test results
- [ ] v2.0.0 release candidate

## Next Steps

1. **Immediate Actions**:
   - Verify current nRF9160 modem firmware version
   - Set up Onomondo API access and generate test profiles
   - Begin Stage 1 environment setup

2. **First Week Goals**:
   - Complete Stages 1-2 (environment setup and memory configuration)
   - Begin basic SoftSIM integration testing
   - Resolve any critical compatibility issues

3. **Second Week Goals**:
   - Complete SoftSIM integration and testing
   - Prepare documentation and release materials
   - Prepare for merge back to main branch and v2.0.0 release

## Phase 2 Progress Updates

### v1.0.0 Baseline Analysis (September 5, 2025)

**Critical Discovery**: The v1.0.0 build had:

1. **MCUBoot ENABLED**: `CONFIG_BOOTLOADER_MCUBOOT=y` and all related secure boot configs were active
2. **Sysbuild ENABLED**: `Kconfig.sysbuild` file existed (not disabled)

This means the successful v1.0.0 build was achieved with the **full production configuration** including:
- MCUBoot secure bootloader
- Sysbuild multi-image compilation  
- TF-M security framework
- All production security features

The current disabled state must have happened during our Phase 2 troubleshooting when we were trying to isolate SoftSIM integration issues. The key insight is that **the baseline Asset Tracker v2 with full MCUBoot/sysbuild DOES build successfully** - the build problems we encountered were specifically related to adding SoftSIM configuration on top of this working baseline.

This is actually very good news - it means the production-ready configuration works, and we just need to solve the SoftSIM integration challenge without breaking the proven baseline.

**Strategic Implications**:
- Revert to v1.0.0 configuration as integration starting point
- Focus troubleshooting on SoftSIM-specific build issues  
- Maintain full production security framework throughout integration
- No need to compromise on MCUBoot or sysbuild functionality

## Conclusion

Phase 2 represents a significant technical advancement, building upon the solid v1.0.0 foundation to integrate cutting-edge SoftSIM technology. The structured approach ensures systematic integration while maintaining the stability and functionality of the Asset Tracker baseline.

Success in Phase 2 will demonstrate a complete, production-ready IoT solution combining Nordic's hardware excellence with Onomondo's innovative software-defined SIM technology.

---

**Author**: Murray Kopit (murr2k@gmail.com)  
**Project**: Nordic Thingy91 SoftSIM Integration  
**Repository**: https://github.com/murr2k/thingy91 (softsim branch)  
**Created**: September 5, 2025