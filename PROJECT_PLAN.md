# Thingy91 SoftSIM Integration Project Plan

## Project Overview
**Goal**: Successfully integrate Onomondo SoftSIM functionality into Nordic Thingy91 with reliable cellular connectivity.

**Hardware**: Nordic Thingy91 development kit with nRF9160 cellular modem
**Target**: Replace hardware SIM with Onomondo SoftSIM (pure software SIM implementation)

## Current Status
- ✅ **Hardware Validation Complete**: Precompiled Asset Tracker v2 firmware connects successfully to nRF Cloud using iBasis hardware SIM
- ✅ **SoftSIM Profile Created**: ICCID 89457300000032481981 configured in Onomondo dashboard
- ❌ **SoftSIM Integration Failed**: Multiple attempts with Nordic SDK v3.1.0 resulted in build failures and connectivity issues

## Root Problem Analysis
Previous SoftSIM integration attempts failed because:
1. **Version Mismatch**: Used Nordic SDK v3.1.0 but Onomondo SoftSIM officially supports v2.9.1
2. **No Proven Baseline**: Jumped directly to SoftSIM without establishing reproducible working code
3. **Complex Debugging**: Tried to debug SoftSIM in isolation without working reference

## New Strategic Approach

### Phase 1: Establish Proven Software Baseline
**Objective**: Prove we can build and run the same firmware that works with hardware SIM

1. **Install Nordic SDK v2.9.1**
   - Matches Onomondo SoftSIM v5.0.0+ official support
   - Contains Asset Tracker v2 source code (matching working firmware)

2. **Build Asset Tracker v2 from Source**
   - Use exact same demo that works with precompiled version
   - Verify build system and dependencies work correctly

3. **Test Source-Built Firmware**
   - Flash to Thingy91 device
   - Verify connects to nRF Cloud with iBasis hardware SIM
   - Confirm identical behavior to precompiled version

**Success Criteria**: Source-built Asset Tracker v2 connects to nRF Cloud identically to precompiled version

### Phase 2: Incremental SoftSIM Integration
**Objective**: Add SoftSIM functionality to proven working baseline

1. **Integrate Onomondo SoftSIM Module**
   - Add SoftSIM to working Asset Tracker v2 project
   - Use officially supported Nordic SDK v2.9.1 + Onomondo SoftSIM v5.1.0

2. **Configure SoftSIM Profile**
   - ICCID: 89457300000032481981
   - Profile hex data from Onomondo dashboard
   - AT command: AT%CSUS=2 (switch to SoftSIM)

3. **Test SoftSIM Connectivity**
   - Monitor device logs for SoftSIM initialization
   - Verify network registration and data connectivity
   - Confirm SoftSIM shows as "online" in Onomondo dashboard

**Success Criteria**: SoftSIM-enabled firmware connects to cellular network and Onomondo dashboard shows device online

## Technical Details

### Working Reference Firmware
- **File**: `thingy91_asset_tracker_v2_2024-11-18_a2386bfc.hex`
- **SDK Version**: Nordic SDK v2.8.0 (compatible with target v2.9.1)
- **Connectivity**: iBasis hardware SIM → nRF Cloud
- **Status**: ✅ Verified working

### Target Software Versions
- **Nordic SDK**: v2.9.1 (Onomondo official support)
- **Onomondo SoftSIM**: v5.1.0 (latest, supports SDK v2.9.1)
- **Zephyr RTOS**: Included with Nordic SDK v2.9.1
- **Board Target**: thingy91/nrf9160/ns

### SoftSIM Configuration
```
ICCID: 89457300000032481981
Provider: Onomondo
Profile Type: Static profile with hex data
AT Commands: AT%CSUS=2 (select SoftSIM)
APN: onomondo (default)
```

### Previous Issues Resolved
1. **Module Integration**: Fixed by adding ZEPHYR_EXTRA_MODULES to CMakeLists.txt
2. **TF-M Memory**: Fixed by increasing partition from 48KB to 96KB
3. **Build System**: Fixed by using correct Nordic SDK version
4. **Kconfig Symbols**: Fixed by proper module discovery

## Success Metrics
- [ ] Asset Tracker v2 builds successfully from source in SDK v2.9.1
- [ ] Source-built firmware connects to nRF Cloud with hardware SIM
- [ ] SoftSIM integration builds without errors
- [ ] SoftSIM device registers on cellular network
- [ ] Onomondo dashboard shows device as "online"
- [ ] Data connectivity works through SoftSIM

## Risk Mitigation
1. **Incremental Approach**: Establish working baseline before SoftSIM integration
2. **Version Alignment**: Use officially supported Nordic SDK v2.9.1
3. **Reference Comparison**: Compare against known working precompiled firmware
4. **Systematic Testing**: Test each phase independently

## File Locations
- **Project Directory**: `/home/murr2k/projects/thingy91/`
- **Nordic SDK**: `/home/murr2k/ncs/v2.9.1/` (to be installed)
- **Current SDK**: `/home/murr2k/ncs/v3.1.0/` (incompatible)
- **Working Firmware**: `C:\Users\murr2\Downloads\thingy91_mfw-1.3.7_sdk-2.8.0\img_fota_dfu_hex\thingy91_asset_tracker_v2_2024-11-18_a2386bfc.hex`

## Next Immediate Action
Install Nordic SDK v2.9.1 to begin Phase 1 baseline establishment.