# West Command Reference and Status

## Key Discovery: West Workspace Not Properly Initialized

### Current Status (Critical Issue)
- **Problem**: All SDK modules are on `init_placeholder` branches with "No commits yet"
- **Root Cause**: `west update` was never run after `west init`
- **Impact**: No build commands available because SDK components don't exist

### West Commands Available
```bash
# Built-in commands (repository management)
west init         # Create workspace
west update       # Download/update all projects ⭐ NEEDED
west list         # Show projects
west status       # Show git status
west manifest     # Manage manifest

# Extension commands (available after west update)
west build        # Build applications (requires SDK)
west flash        # Flash to device (requires SDK)
west debug        # Debug applications (requires SDK)
```

### Current Workspace State
```
Workspace: /home/murr2k/projects/thingy91/
Manifest: west.yml (custom with SoftSIM module)

Projects Status:
❌ sdk-nrf: init_placeholder (empty)
❌ sdk-zephyr: init_placeholder (empty)  
❌ sdk-mcuboot: init_placeholder (empty)
❌ sdk-mbedtls: init_placeholder (empty)
❌ sdk-trusted-firmware-m: init_placeholder (empty)
❌ onomondo-softsim: init_placeholder (empty)
✅ nrfxlib: properly checked out
```

### Required Next Steps
1. **CRITICAL**: Run `west update` to download all SDK components
2. **After update**: `west build` and other commands will become available
3. **Then**: Can proceed with MCUBoot debugging

### West Update Process
```bash
cd /home/murr2k/projects/thingy91
west update  # This will download ~GB of SDK components
```

**This explains why "west build" was unknown - the build system extensions aren't available until the SDK is properly downloaded.**