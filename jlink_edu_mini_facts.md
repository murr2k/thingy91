# J-Link EDU Mini V1 Hardware Facts

## Hardware Information
- **Model**: J-Link EDU Mini V1
- **Serial Number**: 801040036
- **Firmware**: J-Link EDU Mini V1 compiled Jul 8 2025 10:06:04
- **Hardware Version**: V1.00
- **USB Speed**: Full speed (12 MBit/s)

## License Limitations
- **Available Licenses**: FlashBP, GDB
- **Missing License**: RTT (Real Time Transfer)
- **Implication**: Cannot use J-Link RTT Logger for real-time debugging output

## SWD Debugging Capabilities
- **Interface**: SWD (Serial Wire Debug)
- **Speed**: Auto-reduced from 4000 kHz to 2025 kHz for stability
- **Target Support**: Successfully connects to nRF9160_xxAA
- **Core Detection**: Correctly identifies Cortex-M23 r0p2
- **Security**: Security extension implemented, secure debug enabled

## Connection Details
- **VTref**: 1.786V
- **DPIDR**: 0x6BA02477
- **Device ID**: NRF9160_XXAA
- **ROM Base**: 0xE00FF000

## Functional Limitations
- ✅ **Flashing**: Full support for programming firmware
- ✅ **GDB Debugging**: Breakpoint debugging supported
- ❌ **RTT Logging**: Not available (requires commercial license)
- ✅ **SWD Connection**: Reliable connection to Nordic nRF9160

## WSL/USBIPD Status
- **USBIPD Status**: Device 2-13 (1915:9100) is already attached to WSL
- **COM Ports Available**: /dev/ttyACM0 and /dev/ttyACM1 visible in WSL
- **Device State**: Thingy91 may not be running firmware after flash
- **Issue**: Device appears attached but may not be executing SoftSIM firmware

## Alternative Debugging Methods
Since RTT is not available and UART ports have WSL access issues:
1. **Windows Host Serial**: Access COM ports directly from Windows host side
2. **LED Indicators**: Visual status from Thingy91 RGB LED patterns  
3. **Breakpoint Debugging**: Use GDB for code-level debugging
4. **Network Testing**: Monitor Onomondo dashboard for SoftSIM online status
5. **Windows Python Scripts**: Run serial communication scripts on Windows host

## Potential WSL Workarounds
1. **USBIPD Attach**: Try `usbipd wsl attach --busid X-Y` for specific USB device
2. **Windows Serial Bridge**: Use Windows-side scripts to bridge serial data
3. **Network-based Logging**: Configure firmware to send logs via cellular/network
4. **Dual Boot Testing**: Test on native Linux installation if available

This information is critical for future debugging sessions with this hardware.