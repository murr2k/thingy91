# Memory Optimization Notes - nrf-softsim PR #50 Analysis

**Date**: September 5, 2025  
**Source**: https://github.com/onomondo/nrf-softsim/pull/50  
**Context**: Thingy91 + Asset Tracker v2 + SoftSIM integration  

## Critical Findings

### Problem Statement
- **Issue #49**: TFM (Trusted Firmware-M) partition overflow when using Nordic Asset Tracker v2 with SoftSIM on Thingy91
- **Symptom**: Build failures due to memory region overflows
- **Impact**: Out-of-the-box compilation prevented for Thingy91 + Asset Tracker v2 combination

### Solution Implemented (PR #50)
- **TFM Partition Resize**: Expanded `tfm` partition to accommodate SoftSIM memory requirements
- **Factory Layout Update**: Modified static partition layout specifically for Thingy91
- **Address Adjustment**: Updated related memory addresses and partition sizes
- **Validation**: Confirmed working on actual Thingy:91 hardware by Benjamin Bruun

### Technical Details
- **Root Cause**: SoftSIM library increased memory footprint beyond original TFM partition allocation
- **Fix**: Proactive partition size adjustment in factory configuration
- **Target**: Specifically addresses Thingy91 platform constraints
- **Status**: Merged July 9, 2024 (Available in current nrf-softsim repository)

## Impact on Our Implementation

### Memory Constraint Risk Assessment
- **Previous Risk Level**: HIGH ⚠️
- **Updated Risk Level**: MEDIUM-LOW ✅ (Addressed upstream)
- **Mitigation**: PR #50 provides tested solution for our exact use case

### Implementation Implications
1. **TFM Memory Layout**: 
   - Use updated partition layout from nrf-softsim repository
   - Leverage tested memory configuration for Thingy91
   - No need for custom memory optimization initially

2. **Asset Tracker Compatibility**:
   - PR #50 specifically tested with Asset Tracker v2
   - Memory allocation conflict already resolved
   - Direct compatibility with our baseline

3. **Build System**:
   - Factory static partition layout updated upstream
   - Should work out-of-the-box with latest nrf-softsim
   - Reduces Stage 2 complexity significantly

## Updated Stage 2 Strategy

### Original Plan (BEFORE PR #50 analysis)
- Complex memory analysis and optimization
- Custom partition layout design
- Risk of memory allocation conflicts
- Estimated 2 days complexity

### Revised Plan (AFTER PR #50 analysis)
- Use proven upstream memory configuration
- Validate existing partition layout
- Monitor for any additional optimization needs
- Reduced complexity, potentially 1 day

## Validation Requirements

### Must Verify
1. **nrf-softsim Version**: Ensure we're using repository version that includes PR #50
2. **TFM Partition**: Confirm updated partition layout is applied
3. **Build Success**: Verify Asset Tracker v2 + SoftSIM compiles without memory errors
4. **Runtime Testing**: Confirm memory allocation works in practice

### Success Indicators
- [ ] Clean compilation without TFM partition overflow errors
- [ ] SoftSIM + Asset Tracker + TF-M coexistence
- [ ] Stable runtime operation without memory exhaustion
- [ ] Partition layout matches PR #50 specifications

## Key Takeaway

**Excellent news**: The memory constraint challenge we identified as HIGH RISK has been directly addressed by Onomondo for our exact use case (Thingy91 + Asset Tracker v2). This significantly reduces our implementation risk and complexity.

The upstream community has already solved the primary technical challenge we anticipated, validating our approach and providing confidence for Stage 1 implementation.

---

**Next Action**: Proceed with Stage 1 using confidence that memory constraints have been addressed upstream.