#!/bin/bash

# Build SoftSIM firmware for Thingy91 using Nordic SDK v3.1.0
set -e

echo "Building SoftSIM Firmware for Nordic Thingy91..."

# Check if we're in the right directory
if [[ ! -f "prj.conf" ]]; then
    echo "Error: prj.conf not found. Run this script from the project directory."
    exit 1
fi

# Set up Nordic SDK environment
export ZEPHYR_BASE=$HOME/ncs/v3.1.0/zephyr
export ZEPHYR_TOOLCHAIN_VARIANT=gnuarmemb
export GNUARMEMB_TOOLCHAIN_PATH=$HOME/ncs/toolchains/c5be9c56c7

# Source the environment
if [[ -f "$ZEPHYR_BASE/zephyr-env.sh" ]]; then
    source $ZEPHYR_BASE/zephyr-env.sh
fi

# Add toolchain to PATH
export PATH=$GNUARMEMB_TOOLCHAIN_PATH/bin:$PATH

echo "Found Nordic SDK and SoftSIM configuration"
echo "SoftSIM profile configured in prj.conf"

# Clean and create build directory
echo "Preparing build directory..."
rm -rf build_softsim
mkdir -p build_softsim
cd build_softsim

# Use cmake from SDK
echo "Configuring build with cmake..."
CMAKE_BIN=$HOME/ncs/toolchains/c5be9c56c7/usr/bin/cmake
NINJA_BIN=$HOME/ncs/toolchains/c5be9c56c7/usr/bin/ninja

if [[ ! -f "$CMAKE_BIN" ]]; then
    # Try system cmake
    CMAKE_BIN=cmake
    NINJA_BIN=ninja
fi

# Configure the build
$CMAKE_BIN -GNinja \
    -DBOARD=thingy91/nrf9160/ns \
    -DZEPHYR_BASE=$ZEPHYR_BASE \
    -DGNUARMEMB_TOOLCHAIN_PATH=$GNUARMEMB_TOOLCHAIN_PATH \
    ..

# Build the firmware
echo "Building firmware..."
$NINJA_BIN

cd ..

echo ""
echo "BUILD COMPLETE!"
echo "Firmware location: build_softsim/zephyr/zephyr.hex"
echo ""
echo "To flash to device:"
echo "1. Move SW2 to nRF91 position"
echo "2. Use J-Link to flash: build_softsim/zephyr/zephyr.hex"