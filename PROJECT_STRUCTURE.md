# Nordic Thingy91 Demo - Project Structure

## Directory Structure

```
thingy91/
├── CMakeLists.txt                      # Main CMake build configuration
├── prj.conf                           # Zephyr project configuration
├── Kconfig                            # Custom Kconfig options
├── west.yml                           # West manifest for dependencies
├── build.sh                           # Build automation script
├── README.md                          # Project documentation
├── PROJECT_STRUCTURE.md               # This file
├── boards/
│   └── thingy91_nrf9160_ns.overlay   # Device tree overlay
└── src/
    ├── main.c                         # Main application entry point
    ├── sensors/                       # Sensor management modules
    │   ├── sensor_manager.h/.c        # Central sensor coordinator
    │   ├── environmental_sensor.h/.c  # BME680 environmental sensor
    │   └── motion_sensor.h/.c         # ADXL372/362 motion sensors
    ├── connectivity/                  # Network connectivity modules
    │   ├── cellular_manager.h/.c      # LTE-M/NB-IoT cellular management
    │   └── mqtt_client.h/.c           # MQTT client with TLS
    ├── data/                          # Data processing pipeline
    │   ├── data_processor.h/.c        # Data filtering and formatting
    │   └── data_buffer.h/.c           # Circular buffer with NVS
    ├── ui/                            # User interface components
    │   ├── led_controller.h/.c        # RGB LED status indicators
    │   └── button_handler.h/.c        # Button input processing
    ├── power/                         # Power management
    │   └── power_manager.h/.c         # Battery and sleep management
    └── config/                        # Configuration management
        └── config_manager.h/.c        # NVS-based configuration
```

## Module Overview

### Core Application (`src/main.c`)
- Application state machine
- Module initialization and coordination
- Work queue management
- Button callback handling
- Main application loop

### Sensor Management (`src/sensors/`)

#### `sensor_manager.h/.c`
- Unified sensor interface
- Data quality assessment
- Sensor calibration
- Power mode management
- Event-driven sensor monitoring

#### `environmental_sensor.h/.c`
- BME680 sensor driver wrapper
- Temperature, humidity, pressure, gas readings
- Oversampling configuration
- Power mode control
- Simulated data for testing

#### `motion_sensor.h/.c`
- ADXL372/ADXL362 sensor drivers
- Accelerometer and gyroscope data
- Motion event detection
- Calibration with offset compensation
- Configurable sensitivity ranges

### Connectivity (`src/connectivity/`)

#### `cellular_manager.h/.c`
- LTE Link Controller integration
- Network registration management
- Signal strength monitoring
- Power saving modes (PSM, eDRX)
- APN and network mode configuration

#### `mqtt_client.h/.c`
- Secure MQTT over TLS
- Bi-directional messaging
- Auto-reconnection logic
- Command processing
- Connection statistics

### Data Processing (`src/data/`)

#### `data_processor.h/.c`
- Real-time data filtering
- Outlier detection and correction
- JSON/binary formatting
- Data compression (RLE)
- Processing statistics

#### `data_buffer.h/.c`
- Thread-safe circular buffer
- NVS persistence
- Configurable retention
- Memory management
- Data integrity (CRC)

### User Interface (`src/ui/`)

#### `led_controller.h/.c`
- RGB LED control with PWM
- Animated status patterns
- Brightness control
- Power-aware operation
- Visual feedback system

#### `button_handler.h/.c`
- Multi-button input handling
- Debouncing and state tracking
- Long press and multi-click detection
- Configurable timing
- Event callback system

### Power Management (`src/power/`)

#### `power_manager.h/.c`
- Battery voltage monitoring
- Multiple power modes
- Automatic sleep management
- Wake event handling
- Power consumption tracking

### Configuration (`src/config/`)

#### `config_manager.h/.c`
- NVS-based persistence
- JSON import/export
- Configuration validation
- Version migration
- Runtime parameter updates

## Key Features

### Modular Architecture
- Clear separation of concerns
- Standardized interfaces
- Minimal coupling between modules
- Easy to extend and modify

### Professional Error Handling
- Comprehensive error checking
- Graceful failure recovery
- Detailed logging and diagnostics
- Robust state management

### Power Optimization
- Configurable power modes
- Sensor power gating
- Cellular power saving
- Battery monitoring
- Sleep mode management

### Data Integrity
- CRC validation
- Persistent storage
- Data buffering during outages
- Quality assessment
- Filtering and validation

### Production Ready
- Comprehensive logging
- Configuration management
- Over-the-air updates ready
- Diagnostic capabilities
- Performance monitoring

## Build System

### CMakeLists.txt
- Modular source file organization
- Proper include path management
- Conditional compilation support
- Optimization settings

### prj.conf
- Zephyr subsystem configuration
- Network stack setup
- Sensor driver enablement
- Memory optimization
- Debug settings

### Kconfig
- Custom configuration options
- Parameter validation
- Default value management
- Feature toggles

### Device Tree Overlay
- Hardware-specific configuration
- Sensor pin assignments
- PWM and ADC setup
- Flash partitioning

## Testing and Validation

### Simulation Support
- Sensor data simulation
- Network simulation
- Power mode testing
- Configuration testing

### Debug Features
- Comprehensive logging
- Runtime diagnostics
- Memory usage tracking
- Performance metrics

### Hardware Validation
- Real sensor integration
- Cellular connectivity
- Power consumption measurement
- Environmental testing

## Deployment

### Build Process
- Automated build script
- Multiple build configurations
- Size optimization
- Documentation generation

### Configuration
- Factory defaults
- Runtime configuration
- Persistent storage
- Migration support

### Monitoring
- Real-time status
- Performance metrics
- Error reporting
- Health monitoring

This architecture provides a solid foundation for IoT applications with the Nordic Thingy91, demonstrating professional-grade embedded software development practices.