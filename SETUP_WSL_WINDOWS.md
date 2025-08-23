# Nordic Thingy91 DK Setup Guide for WSL2 on Windows 11

This guide covers the complete setup for developing and programming the Nordic Thingy91 DK from WSL2 Ubuntu 22.04 with the device connected to Windows 11 host.

## Table of Contents
1. [Windows Host Setup](#windows-host-setup)
2. [WSL2 Ubuntu Setup](#wsl2-ubuntu-setup)
3. [USB Device Access from WSL2](#usb-device-access-from-wsl2)
4. [nRF Connect SDK Installation](#nrf-connect-sdk-installation)
5. [Programming the Thingy91 DK](#programming-the-thingy91-dk)
6. [Troubleshooting](#troubleshooting)

## Windows Host Setup

### 1. Install Required Windows Software

#### nRF Connect for Desktop (Windows)
Download and install from: https://www.nordicsemi.com/Products/Development-tools/nRF-Connect-for-desktop

This includes:
- **Programmer** - For flashing firmware
- **LTE Link Monitor** - For debugging cellular connectivity
- **Serial Terminal** - For UART communication

#### J-Link Software (Optional but Recommended)
Download from: https://www.segger.com/downloads/jlink/
- Install the J-Link Software and Documentation Pack
- This enables advanced debugging capabilities

#### USB Serial Drivers
The Thingy91 uses FTDI USB serial chips. Windows 11 typically has these pre-installed, but if needed:
- Download from: https://ftdichip.com/drivers/vcp-drivers/
- Install the VCP (Virtual COM Port) drivers

### 2. Verify Device Connection

1. Connect the Thingy91 DK to Windows via USB
2. Open Device Manager (`Win + X`, then `M`)
3. Look for:
   - **Ports (COM & LPT)**: Should show "USB Serial Port (COMx)"
   - **Universal Serial Bus devices**: Should show "Nordic Thingy:91"

Note the COM port number (e.g., COM3) - you'll need this later.

## WSL2 Ubuntu Setup

### 1. Update WSL2 and Ubuntu

```bash
# In PowerShell (as Administrator)
wsl --update
wsl --shutdown

# In WSL2 Ubuntu
sudo apt update && sudo apt upgrade -y
```

### 2. Install Development Dependencies

```bash
# Essential build tools
sudo apt install -y \
    git \
    cmake \
    ninja-build \
    gperf \
    ccache \
    dfu-util \
    device-tree-compiler \
    wget \
    python3-pip \
    python3-setuptools \
    python3-wheel \
    xz-utils \
    file \
    make \
    gcc \
    gcc-multilib \
    g++-multilib \
    libsdl2-dev \
    libmagic1

# Python dependencies
pip3 install --user -U west
echo 'export PATH=~/.local/bin:$PATH' >> ~/.bashrc
source ~/.bashrc
```

### 3. Install ARM GNU Toolchain

```bash
# Download and install ARM toolchain
cd ~
wget https://developer.arm.com/-/media/Files/downloads/gnu/13.2.rel1/binrel/arm-gnu-toolchain-13.2.rel1-x86_64-arm-none-eabi.tar.xz
sudo tar -xf arm-gnu-toolchain-13.2.rel1-x86_64-arm-none-eabi.tar.xz -C /opt/
echo 'export PATH=/opt/arm-gnu-toolchain-13.2.Rel1-x86_64-arm-none-eabi/bin:$PATH' >> ~/.bashrc
source ~/.bashrc
rm arm-gnu-toolchain-13.2.rel1-x86_64-arm-none-eabi.tar.xz
```

## USB Device Access from WSL2

### Option 1: Using USBIPD (Recommended)

This allows direct USB passthrough to WSL2.

#### Windows Side Setup

1. Install usbipd-win from PowerShell (Administrator):
```powershell
winget install --exact --id Microsoft.USBPCIProxy
```

2. List USB devices:
```powershell
usbipd list
```

3. Find your Thingy91 device (look for "Nordic" or the VID:PID)

4. Share the device (replace `<BUSID>` with actual value from list):
```powershell
usbipd bind --busid <BUSID>
```

5. Attach to WSL2:
```powershell
usbipd attach --wsl --busid <BUSID>
```

#### WSL Side Setup

1. Install USB support:
```bash
sudo apt install -y linux-tools-generic hwdata
sudo update-alternatives --install /usr/local/bin/usbip usbip /usr/lib/linux-tools/*-generic/usbip 20
```

2. Verify device is visible:
```bash
lsusb
# Should show Nordic Semiconductor device

ls -la /dev/ttyACM* /dev/ttyUSB*
# Should show the serial device
```

3. Add user to dialout group for serial access:
```bash
sudo usermod -a -G dialout $USER
# Log out and back in for this to take effect
```

### Option 2: Using Windows COM Port Mapping

If USBIPD doesn't work, you can map Windows COM ports to WSL2:

```bash
# In WSL2, create a symbolic link to Windows COM port
# Replace COM3 with your actual COM port number
sudo chmod 666 /dev/ttyS3  # For COM3
# COM1 = /dev/ttyS1, COM2 = /dev/ttyS2, etc.
```

## nRF Connect SDK Installation

### 1. Install nRF Connect SDK

```bash
# Create workspace directory
mkdir -p ~/nrf-workspace
cd ~/nrf-workspace

# Initialize west workspace with nRF Connect SDK
west init -m https://github.com/nrfconnect/sdk-nrf --mr v2.6.1
west update

# Install additional Python requirements
pip3 install --user -r nrf/scripts/requirements.txt
pip3 install --user -r zephyr/scripts/requirements.txt
pip3 install --user -r bootloader/mcuboot/scripts/requirements.txt
```

### 2. Install nRF Command Line Tools

```bash
# Download nRF Command Line Tools for Linux
cd ~/Downloads
wget https://nsscprodmedia.blob.core.windows.net/prod/software-and-other-downloads/desktop-software/nrf-command-line-tools/sw/versions-10-x-x/10-24-2/nrf-command-line-tools-10.24.2_linux-amd64.tar.gz

# Extract and install
sudo tar -xf nrf-command-line-tools-10.24.2_linux-amd64.tar.gz -C /opt/
echo 'export PATH=/opt/nrf-command-line-tools/bin:$PATH' >> ~/.bashrc
source ~/.bashrc

# Install nrfutil
pip3 install --user nrfutil

# Install device programming support
nrfutil install device
nrfutil install completion
```

### 3. Clone and Build the Demo Project

```bash
# Clone the repository
cd ~/projects
git clone https://github.com/murr2k/thingy91.git
cd thingy91

# Build the project
west build -b thingy91_nrf9160_ns
```

## Programming the Thingy91 DK

### Method 1: Using nrfutil (via WSL2 with USBIPD)

```bash
# List connected devices
nrfutil device list

# Program the device (device should be in MCUboot mode)
nrfutil device program --firmware build/zephyr/app_signed.hex --core Network
nrfutil device program --firmware build/zephyr/app_signed.hex --core Application

# Reset the device
nrfutil device reset
```

### Method 2: Using Windows nRF Connect Programmer

1. Build the firmware in WSL2:
```bash
cd ~/projects/thingy91
west build -b thingy91_nrf9160_ns
```

2. Copy hex file to Windows:
```bash
cp build/zephyr/app_signed.hex /mnt/c/Users/<YourUsername>/Desktop/
```

3. In Windows:
   - Open nRF Connect for Desktop
   - Launch the Programmer app
   - Select your Thingy91 device
   - Add the hex file
   - Click "Write" to program

### Method 3: Using MCUboot USB DFU

1. Put Thingy91 in MCUboot mode:
   - Press and hold the button on the Thingy91
   - While holding, press the reset button
   - Release the reset button, then release the other button
   - The LED should indicate MCUboot mode

2. In WSL2 (with USB access via USBIPD):
```bash
# Install mcumgr
pip3 install --user mcumgr

# Create connection
mcumgr conn add thingy91 type="serial" connstring="dev=/dev/ttyACM0,baud=115200"

# Upload firmware
mcumgr -c thingy91 image upload build/zephyr/app_update.bin

# List images to verify
mcumgr -c thingy91 image list

# Mark image for test (will boot once)
mcumgr -c thingy91 image test <hash>

# Reset device
mcumgr -c thingy91 reset
```

## Serial Output Monitoring

### From WSL2 (if USB passthrough is working)

```bash
# Install minicom
sudo apt install -y minicom

# Connect to serial port
minicom -D /dev/ttyACM0 -b 115200

# Or use screen
screen /dev/ttyACM0 115200

# Or use picocom
sudo apt install -y picocom
picocom -b 115200 /dev/ttyACM0
```

### From Windows (Alternative)

Use nRF Connect LTE Link Monitor or any serial terminal:
- PuTTY: Set to Serial, COM port, 115200 baud
- Tera Term: Similar settings
- nRF Connect LTE Link Monitor: Auto-detects settings

## Troubleshooting

### Common Issues and Solutions

#### 1. USB Device Not Detected in WSL2

```bash
# Check if USBIPD service is running (in Windows PowerShell)
sc query usbipd

# Restart the service if needed
Restart-Service usbipd

# Re-attach device
usbipd detach --busid <BUSID>
usbipd attach --wsl --busid <BUSID>
```

#### 2. Permission Denied on Serial Port

```bash
# Add user to dialout group
sudo usermod -a -G dialout $USER

# Set permissions temporarily
sudo chmod 666 /dev/ttyACM0

# Create udev rule for permanent fix
echo 'SUBSYSTEM=="usb", ATTRS{idVendor}=="1915", MODE="0666", GROUP="dialout"' | sudo tee /etc/udev/rules.d/99-nordic.rules
sudo udevadm control --reload-rules
```

#### 3. West Build Fails

```bash
# Clear build directory
rm -rf build

# Update west workspace
west update

# Ensure all Python packages are installed
pip3 install --user --upgrade west
pip3 install --user -r ~/nrf-workspace/nrf/scripts/requirements.txt
```

#### 4. Device Stuck in Bad State

1. Hardware Reset:
   - Disconnect USB
   - Hold reset button
   - Connect USB while holding reset
   - Release reset button

2. Recovery Mode:
   - Use nRF Connect Programmer in Windows
   - Select "Recover" option
   - This erases all flash and restores bootloader

#### 5. Build Path Issues

```bash
# Ensure paths are correct
export ZEPHYR_BASE=~/nrf-workspace/zephyr
export PATH=~/.local/bin:$PATH
export PATH=/opt/arm-gnu-toolchain-13.2.Rel1-x86_64-arm-none-eabi/bin:$PATH
```

## Useful Commands Reference

```bash
# Build for nRF9160 application core
west build -b thingy91_nrf9160_ns

# Build for nRF52840 (Bluetooth)
west build -b thingy91_nrf52840

# Clean build
west build -t clean

# Pristine build (complete rebuild)
west build -t pristine

# Build with specific configuration
west build -b thingy91_nrf9160_ns -- -DCONFIG_DEBUG=y

# Flash using west (requires J-Link)
west flash

# Debug using west (requires J-Link)
west debug

# Check device info
nrfutil device info

# Monitor RTT output (requires J-Link)
JLinkRTTClient
```

## VS Code Integration (Optional)

1. Install VS Code in Windows
2. Install nRF Connect Extension Pack
3. Open WSL2 folder in VS Code:
```bash
code ~/projects/thingy91
```
4. The extension will detect the project and provide IntelliSense, building, and debugging capabilities

## Next Steps

1. Test the connection by building and flashing the demo
2. Monitor serial output to verify the application is running
3. Connect to nRF Cloud to see data from your device
4. Modify the code and experiment with different features

For more information:
- [Nordic DevZone](https://devzone.nordicsemi.com)
- [nRF Connect SDK Documentation](https://docs.nordicsemi.com)
- [Thingy91 Hardware Documentation](https://docs.nordicsemi.com/bundle/ug_thingy91/page/UG/thingy91/intro/frontpage.html)