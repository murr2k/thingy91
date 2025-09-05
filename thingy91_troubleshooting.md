# Thingy91 Troubleshooting Guide

## Power and Connection Issues

### Check Power Status
1. **LED Indicators**: 
   - Is the RGB LED showing any activity when powered?
   - Solid colors, blinking patterns, or completely off?

2. **Power Button (SW2)**:
   - Try holding SW2 for 3-5 seconds to power on
   - Try a quick press to wake from sleep
   - Try holding for 10 seconds to force reset

### USB Connection Modes

The Thingy91 can be in different modes:

#### Application Mode (Normal Operation)
- Device runs your application
- May not show up as USB serial device
- LED patterns indicate app status

#### Programming/Debug Mode  
- Press and HOLD SW4 while powering on
- OR hold SW4 while pressing SW2 (reset)
- Should appear as USB device for programming

#### Recovery Mode
- If completely unresponsive
- Hold SW2 + SW4 simultaneously for 10+ seconds

### USB Cable Check
- Try different USB cable (data cable, not just charging)
- Try different USB port
- Some cables are power-only

### Windows Device Manager Check
1. Open Device Manager (Windows + X → Device Manager)
2. Plug in Thingy91 while watching for:
   - "Unknown Device" appearing
   - "USB Serial Device"
   - "nRF Connect" entries
   - Any error indicators (yellow triangle)

## LED Status Meanings

Common LED patterns on Thingy91:
- **Off**: No power or deep sleep
- **Red**: Error state or low battery
- **Yellow/Orange**: Initializing or charging
- **Blue**: Connecting to network
- **Green**: Connected and operational
- **Purple**: Configuration mode

## Next Steps if Still No Recognition

1. **Install nRF Connect for Desktop** (Windows host)
   - Download from: https://www.nordicsemi.com/Products/Development-tools/nRF-Connect-for-Desktop
   - Includes proper USB drivers

2. **Check Battery**
   - Device might have dead battery
   - Try charging for 30+ minutes before testing

3. **Try Programming Mode**
   - Hold SW4 while connecting USB
   - Should force device into programmable state

4. **Factory Reset**
   - Hold SW2 + SW3 + SW4 for 15 seconds
   - Release and power cycle