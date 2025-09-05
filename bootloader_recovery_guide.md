# Thingy91 Bootloader Recovery via SWD

## Problem
Bootloader was erased during J-Link debugging, device no longer responds to USB.

## Solution
Flash new bootloader + application via SWD.

## Step 1: Download Required Files

### MCUboot Bootloader for Thingy91:
Download from: https://developer.nordicsemi.com/nRF_Connect_SDK/doc/latest/nrf/samples/bootloader/index.html

Or build from nRF Connect SDK:
```bash
cd ~/ncs/bootloader/mcuboot/boot/zephyr
west build -b thingy91_nrf9160_ns
```

### Pre-built Files Locations:
- **Bootloader**: `nrf/samples/bootloader/mcuboot/build/zephyr/zephyr.hex`
- **Application**: Your built application hex file
- **Combined**: Merged hex with bootloader + app

## Step 2: SWD Connection

### Pin Connections (Thingy91 to J-Link):
```
J-Link    | Thingy91 SWD Header
----------|------------------
Pin 1 VDD | VDD (3.3V)
Pin 7 TMS | SWDIO  
Pin 9 TCK | SWCLK
Pin 15 GND| GND
Pin 19 RST| RESET (optional)
```

## Step 3: Recovery via nRF Connect Programmer

### Using nRF Connect for Desktop:

1. **Launch nRF Connect for Desktop**
2. **Install/Open Programmer app**
3. **Connect J-Link**:
   - Select your J-Link device
   - Target: nRF9160 (not auto-detect)
   
4. **Erase Device** (if needed):
   - Click "Erase all"
   - This clears any corrupted state

5. **Program Bootloader**:
   - Click "Add file"
   - Select MCUboot hex file
   - Address should be 0x00000000
   - Click "Write"

6. **Program Application**:
   - Click "Add file" 
   - Select your application hex
   - Address should be 0x10000 (or as specified)
   - Click "Write"

## Step 4: Command Line Alternative

### Using nrfjprog:

```bash
# Erase device
nrfjprog --family NRF91 --eraseall

# Program bootloader at address 0x0
nrfjprog --family NRF91 --program mcuboot.hex --sectorerase

# Program application 
nrfjprog --family NRF91 --program app.hex --sectorerase

# Reset device
nrfjprog --family NRF91 --reset
```

### Using JLinkExe directly:

```bash
JLinkExe -device nRF9160_xxAA -if SWD -speed 4000

# In J-Link console:
erase
loadfile mcuboot.hex
loadfile app.hex 0x10000
r
g
exit
```

## Step 5: Verification

After programming:
1. **Disconnect J-Link**
2. **Connect USB to Thingy91**  
3. **Power ON**
4. **Should appear in Device Manager** as Nordic device

## Files You Need

### Option 1: Use Pre-built Nordic Files
Download Nordic's official Thingy91 firmware from:
https://www.nordicsemi.com/Products/Development-hardware/Nordic-Thingy-91

### Option 2: Build Your Own
```bash
# Build MCUboot bootloader
cd nrf/samples/bootloader/mcuboot
west build -b thingy91_nrf9160_ns

# Build your application  
cd your_project
west build -b thingy91_nrf9160_ns

# Create combined hex
mergehex -m bootloader.hex app.hex -o combined.hex
```

## Common Issues

### "Cannot connect to target"
- Check SWD wiring
- Verify power (3.3V)
- Try slower speed (1000 kHz)
- Hold RESET while connecting

### "Programming failed"
- Erase all first
- Check hex file addresses
- Verify target is nRF9160

### "Device still not recognized"
- Verify bootloader was programmed at 0x0
- Check application entry point
- May need to program soft device separately

## Recovery Success Indicators
- Device appears in Windows Device Manager
- LED shows activity when powered
- Can enter MCUboot mode with SW3 + power cycle