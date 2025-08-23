#!/bin/bash

# Copyright (c) 2024 Nordic Semiconductor ASA
# SPDX-License-Identifier: Apache-2.0

# Build script for Nordic Thingy91 Demo Application

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BOARD="thingy91_nrf9160_ns"
BUILD_DIR="build"
LOG_LEVEL="INF"
OPTIMIZATION="s"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    if ! command_exists "west"; then
        print_error "west command not found. Please install nRF Connect SDK."
        exit 1
    fi
    
    if ! command_exists "cmake"; then
        print_error "cmake not found. Please install CMake."
        exit 1
    fi
    
    if ! command_exists "ninja"; then
        print_warning "ninja not found. Using make instead."
        export CMAKE_GENERATOR="Unix Makefiles"
    else
        export CMAKE_GENERATOR="Ninja"
    fi
    
    print_success "Prerequisites check completed"
}

# Clean build directory
clean_build() {
    if [ -d "$BUILD_DIR" ]; then
        print_status "Cleaning previous build..."
        rm -rf "$BUILD_DIR"
        print_success "Build directory cleaned"
    fi
}

# Configure build
configure_build() {
    print_status "Configuring build for $BOARD..."
    
    # Set build configuration based on command line arguments
    local cmake_args=""
    
    case "$LOG_LEVEL" in
        DBG|DEBUG) cmake_args="$cmake_args -DCONFIG_LOG_DEFAULT_LEVEL=4" ;;
        INF|INFO)  cmake_args="$cmake_args -DCONFIG_LOG_DEFAULT_LEVEL=3" ;;
        WRN|WARN)  cmake_args="$cmake_args -DCONFIG_LOG_DEFAULT_LEVEL=2" ;;
        ERR|ERROR) cmake_args="$cmake_args -DCONFIG_LOG_DEFAULT_LEVEL=1" ;;
    esac
    
    case "$OPTIMIZATION" in
        0|none) cmake_args="$cmake_args -DCONFIG_COMPILER_OPT=\"-O0\"" ;;
        1)      cmake_args="$cmake_args -DCONFIG_COMPILER_OPT=\"-O1\"" ;;
        2)      cmake_args="$cmake_args -DCONFIG_COMPILER_OPT=\"-O2\"" ;;
        3|fast) cmake_args="$cmake_args -DCONFIG_COMPILER_OPT=\"-O3\"" ;;
        s|size) cmake_args="$cmake_args -DCONFIG_COMPILER_OPT=\"-Os\"" ;;
    esac
    
    # Run west build with configuration
    west build -b "$BOARD" -d "$BUILD_DIR" $cmake_args
    
    print_success "Build configuration completed"
}

# Build the project
build_project() {
    print_status "Building project..."
    
    # Build the application
    west build -d "$BUILD_DIR"
    
    if [ $? -eq 0 ]; then
        print_success "Build completed successfully"
        
        # Display build information
        print_status "Build information:"
        echo "  Board: $BOARD"
        echo "  Build directory: $BUILD_DIR"
        echo "  Log level: $LOG_LEVEL"
        echo "  Optimization: $OPTIMIZATION"
        
        # Display binary sizes
        if [ -f "$BUILD_DIR/zephyr/zephyr.elf" ]; then
            print_status "Binary size information:"
            arm-none-eabi-size "$BUILD_DIR/zephyr/zephyr.elf" 2>/dev/null || \
            size "$BUILD_DIR/zephyr/zephyr.elf" 2>/dev/null || \
            echo "  Size information not available"
        fi
    else
        print_error "Build failed"
        exit 1
    fi
}

# Flash the application
flash_application() {
    print_status "Flashing application to device..."
    
    west flash -d "$BUILD_DIR"
    
    if [ $? -eq 0 ]; then
        print_success "Application flashed successfully"
    else
        print_error "Flash failed"
        exit 1
    fi
}

# Generate documentation
generate_docs() {
    print_status "Generating documentation..."
    
    if command_exists "doxygen"; then
        doxygen Doxyfile 2>/dev/null || print_warning "Doxygen configuration not found"
    else
        print_warning "Doxygen not found, skipping documentation generation"
    fi
}

# Main build function
main() {
    print_status "Starting Nordic Thingy91 Demo build process"
    print_status "=========================================="
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -c|--clean)
                CLEAN=true
                shift
                ;;
            -f|--flash)
                FLASH=true
                shift
                ;;
            -d|--docs)
                DOCS=true
                shift
                ;;
            -l|--log-level)
                LOG_LEVEL="$2"
                shift 2
                ;;
            -o|--optimization)
                OPTIMIZATION="$2"
                shift 2
                ;;
            -b|--board)
                BOARD="$2"
                shift 2
                ;;
            -h|--help)
                echo "Usage: $0 [OPTIONS]"
                echo "Options:"
                echo "  -c, --clean         Clean build directory before building"
                echo "  -f, --flash         Flash application after building"
                echo "  -d, --docs          Generate documentation"
                echo "  -l, --log-level     Set log level (DBG, INF, WRN, ERR)"
                echo "  -o, --optimization  Set optimization level (0, 1, 2, 3, s)"
                echo "  -b, --board         Set target board (default: thingy91_nrf9160_ns)"
                echo "  -h, --help          Show this help message"
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done
    
    # Execute build steps
    check_prerequisites
    
    if [ "$CLEAN" = true ]; then
        clean_build
    fi
    
    configure_build
    build_project
    
    if [ "$DOCS" = true ]; then
        generate_docs
    fi
    
    if [ "$FLASH" = true ]; then
        flash_application
    fi
    
    print_success "Build process completed successfully!"
    print_status "To flash manually, run: west flash -d $BUILD_DIR"
    print_status "To monitor serial output, run: west espterm --port /dev/ttyACM0"
}

# Run main function with all arguments
main "$@"