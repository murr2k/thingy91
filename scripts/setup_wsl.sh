#!/bin/bash
# Nordic Thingy91 DK - WSL2 Development Environment Setup Script
# This script automates the installation of all required tools for Thingy91 development

set -e  # Exit on error

echo "═══════════════════════════════════════════════════════════════"
echo "   Nordic Thingy91 DK - WSL2 Development Environment Setup"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

# Check if running in WSL2
if ! grep -qi microsoft /proc/version; then
    print_error "This script is designed for WSL2. Please run it in WSL2 Ubuntu."
    exit 1
fi

print_status "Detected WSL2 environment"

# Update system packages
print_status "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install essential build tools
print_status "Installing essential build tools..."
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
    python3-venv \
    xz-utils \
    file \
    make \
    gcc \
    gcc-multilib \
    g++-multilib \
    libsdl2-dev \
    libmagic1 \
    libusb-1.0-0-dev \
    usbutils

# Install USB tools for USBIPD support
print_status "Installing USB support tools..."
sudo apt install -y linux-tools-generic hwdata
sudo update-alternatives --install /usr/local/bin/usbip usbip /usr/lib/linux-tools/*-generic/usbip 20

# Install serial communication tools
print_status "Installing serial communication tools..."
sudo apt install -y minicom picocom screen

# Add user to dialout group for serial port access
print_status "Adding user to dialout group..."
sudo usermod -a -G dialout $USER
print_warning "You'll need to log out and back in for group changes to take effect"

# Create udev rule for Nordic devices
print_status "Creating udev rules for Nordic devices..."
echo 'SUBSYSTEM=="usb", ATTRS{idVendor}=="1915", MODE="0666", GROUP="dialout"' | sudo tee /etc/udev/rules.d/99-nordic.rules
sudo udevadm control --reload-rules

# Install Python packages
print_status "Installing Python packages..."
pip3 install --user -U west
pip3 install --user nrfutil
pip3 install --user mcumgr

# Update PATH for local Python packages
if ! grep -q "/.local/bin" ~/.bashrc; then
    echo 'export PATH=~/.local/bin:$PATH' >> ~/.bashrc
    print_status "Added ~/.local/bin to PATH"
fi

# Download and install ARM GNU Toolchain
if [ ! -d "/opt/arm-gnu-toolchain-13.2.Rel1-x86_64-arm-none-eabi" ]; then
    print_status "Downloading ARM GNU Toolchain..."
    cd /tmp
    wget -q --show-progress https://developer.arm.com/-/media/Files/downloads/gnu/13.2.rel1/binrel/arm-gnu-toolchain-13.2.rel1-x86_64-arm-none-eabi.tar.xz
    
    print_status "Installing ARM GNU Toolchain..."
    sudo tar -xf arm-gnu-toolchain-13.2.rel1-x86_64-arm-none-eabi.tar.xz -C /opt/
    rm arm-gnu-toolchain-13.2.rel1-x86_64-arm-none-eabi.tar.xz
    
    # Add to PATH
    if ! grep -q "arm-gnu-toolchain" ~/.bashrc; then
        echo 'export PATH=/opt/arm-gnu-toolchain-13.2.Rel1-x86_64-arm-none-eabi/bin:$PATH' >> ~/.bashrc
        print_status "Added ARM toolchain to PATH"
    fi
else
    print_status "ARM GNU Toolchain already installed"
fi

# Download and install nRF Command Line Tools
if [ ! -d "/opt/nrf-command-line-tools" ]; then
    print_status "Downloading nRF Command Line Tools..."
    cd /tmp
    wget -q --show-progress https://nsscprodmedia.blob.core.windows.net/prod/software-and-other-downloads/desktop-software/nrf-command-line-tools/sw/versions-10-x-x/10-24-2/nrf-command-line-tools-10.24.2_linux-amd64.tar.gz
    
    print_status "Installing nRF Command Line Tools..."
    sudo tar -xf nrf-command-line-tools-10.24.2_linux-amd64.tar.gz -C /opt/
    rm nrf-command-line-tools-10.24.2_linux-amd64.tar.gz
    
    # Add to PATH
    if ! grep -q "nrf-command-line-tools" ~/.bashrc; then
        echo 'export PATH=/opt/nrf-command-line-tools/bin:$PATH' >> ~/.bashrc
        print_status "Added nRF tools to PATH"
    fi
    
    # Install segger JLink tools that come with nRF tools
    if [ -f "/opt/nrf-command-line-tools/bin/JLink_Linux_V794e_x86_64/JLinkExe" ]; then
        sudo ln -sf /opt/nrf-command-line-tools/bin/JLink_Linux_V794e_x86_64/* /usr/local/bin/
        print_status "Linked JLink tools to /usr/local/bin"
    fi
else
    print_status "nRF Command Line Tools already installed"
fi

# Create workspace directory
mkdir -p ~/nrf-workspace

# Check if nRF Connect SDK is already installed
if [ ! -d "$HOME/nrf-workspace/nrf" ]; then
    print_status "Installing nRF Connect SDK (this may take a while)..."
    cd ~/nrf-workspace
    
    # Initialize west workspace
    west init -m https://github.com/nrfconnect/sdk-nrf --mr v2.6.1
    
    print_status "Updating west workspace..."
    west update
    
    print_status "Installing SDK Python requirements..."
    pip3 install --user -r nrf/scripts/requirements.txt
    pip3 install --user -r zephyr/scripts/requirements.txt
    pip3 install --user -r bootloader/mcuboot/scripts/requirements.txt
    
    # Set Zephyr base
    if ! grep -q "ZEPHYR_BASE" ~/.bashrc; then
        echo 'export ZEPHYR_BASE=~/nrf-workspace/zephyr' >> ~/.bashrc
        print_status "Set ZEPHYR_BASE environment variable"
    fi
else
    print_status "nRF Connect SDK already installed"
fi

# Install nrfutil device support
print_status "Installing nrfutil device support..."
export PATH=~/.local/bin:$PATH
nrfutil install device || print_warning "nrfutil device support may already be installed"
nrfutil install completion || print_warning "nrfutil completion may already be installed"

# Create helper scripts
print_status "Creating helper scripts..."

# Create USB device attachment script
cat > ~/attach_thingy91.sh << 'EOF'
#!/bin/bash
# Helper script to attach Thingy91 to WSL2

echo "Listing available USB devices on Windows host..."
echo "Please run this in Windows PowerShell as Administrator:"
echo ""
echo "usbipd list"
echo ""
echo "Find your Thingy91 device and note the BUSID"
echo "Then run:"
echo "usbipd attach --wsl --busid <BUSID>"
echo ""
echo "After attaching, verify in WSL2 with:"
echo "lsusb"
echo "ls -la /dev/ttyACM* /dev/ttyUSB*"
EOF
chmod +x ~/attach_thingy91.sh

# Create build helper script
cat > ~/build_thingy91.sh << 'EOF'
#!/bin/bash
# Helper script to build Thingy91 project

set -e

if [ -z "$1" ]; then
    echo "Usage: $0 <project_directory>"
    exit 1
fi

cd "$1"

# Source environment
export PATH=~/.local/bin:/opt/arm-gnu-toolchain-13.2.Rel1-x86_64-arm-none-eabi/bin:/opt/nrf-command-line-tools/bin:$PATH
export ZEPHYR_BASE=~/nrf-workspace/zephyr

echo "Building for Thingy91 nRF9160..."
west build -b thingy91_nrf9160_ns

echo ""
echo "Build complete! Firmware available at:"
echo "  - build/zephyr/app_signed.hex (for nRF Programmer)"
echo "  - build/zephyr/app_update.bin (for MCUboot DFU)"
EOF
chmod +x ~/build_thingy91.sh

# Create flash helper script
cat > ~/flash_thingy91.sh << 'EOF'
#!/bin/bash
# Helper script to flash Thingy91

set -e

if [ ! -f "build/zephyr/app_signed.hex" ]; then
    echo "Error: No firmware found. Please build first."
    exit 1
fi

echo "Attempting to flash Thingy91..."

# Try nrfutil first
if command -v nrfutil &> /dev/null; then
    echo "Using nrfutil..."
    nrfutil device list
    echo ""
    echo "Programming device..."
    nrfutil device program --firmware build/zephyr/app_signed.hex --core Network
    nrfutil device program --firmware build/zephyr/app_signed.hex --core Application
    nrfutil device reset
    echo "Flash complete!"
elif [ -e /dev/ttyACM0 ]; then
    echo "Using mcumgr over USB..."
    echo "Please ensure device is in MCUboot mode:"
    echo "  1. Press and hold button SW3"
    echo "  2. Press reset button"
    echo "  3. Release reset, then release SW3"
    echo ""
    read -p "Press Enter when ready..."
    
    mcumgr conn add thingy91 type="serial" connstring="dev=/dev/ttyACM0,baud=115200"
    mcumgr -c thingy91 image upload build/zephyr/app_update.bin
    mcumgr -c thingy91 reset
    echo "Flash complete!"
else
    echo "Error: No programming method available"
    echo "Please ensure device is connected via USBIPD or copy hex file to Windows"
    exit 1
fi
EOF
chmod +x ~/flash_thingy91.sh

# Create serial monitor script
cat > ~/monitor_thingy91.sh << 'EOF'
#!/bin/bash
# Helper script to monitor Thingy91 serial output

DEVICE=""

# Find the device
for dev in /dev/ttyACM0 /dev/ttyUSB0 /dev/ttyS3; do
    if [ -e "$dev" ]; then
        DEVICE="$dev"
        break
    fi
done

if [ -z "$DEVICE" ]; then
    echo "Error: No serial device found"
    echo "Please ensure device is connected"
    exit 1
fi

echo "Connecting to $DEVICE..."
echo "Press Ctrl+A then K to exit"
echo ""

if command -v picocom &> /dev/null; then
    picocom -b 115200 "$DEVICE"
elif command -v minicom &> /dev/null; then
    minicom -D "$DEVICE" -b 115200
else
    screen "$DEVICE" 115200
fi
EOF
chmod +x ~/monitor_thingy91.sh

print_status "Helper scripts created in home directory:"
echo "  - ~/attach_thingy91.sh   : Instructions for USB attachment"
echo "  - ~/build_thingy91.sh    : Build project"
echo "  - ~/flash_thingy91.sh    : Flash firmware to device"
echo "  - ~/monitor_thingy91.sh  : Monitor serial output"

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "                    Setup Complete!"
echo "═══════════════════════════════════════════════════════════════"
echo ""
print_status "Environment is ready for Nordic Thingy91 development"
echo ""
print_warning "IMPORTANT: Please complete these steps:"
echo ""
echo "1. In Windows PowerShell (as Administrator), install USBIPD:"
echo "   ${YELLOW}winget install --exact --id Microsoft.USBPCIProxy${NC}"
echo ""
echo "2. Log out and back into WSL for group permissions to take effect"
echo ""
echo "3. Source your bashrc to update PATH:"
echo "   ${YELLOW}source ~/.bashrc${NC}"
echo ""
echo "4. Clone and build the demo project:"
echo "   ${YELLOW}cd ~/projects${NC}"
echo "   ${YELLOW}git clone https://github.com/murr2k/thingy91.git${NC}"
echo "   ${YELLOW}cd thingy91${NC}"
echo "   ${YELLOW}~/build_thingy91.sh .${NC}"
echo ""
echo "5. Connect your Thingy91 and attach it to WSL:"
echo "   ${YELLOW}~/attach_thingy91.sh${NC}"
echo ""
echo "For detailed instructions, see: SETUP_WSL_WINDOWS.md"
echo "═══════════════════════════════════════════════════════════════"