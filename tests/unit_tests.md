# Unit Test Specifications - Nordic Thingy91 DK Demo

## Overview
Unit tests validate individual components in isolation using mocks and stubs for dependencies. Tests use the Unity testing framework with Zephyr's testing infrastructure.

## Test Structure
```
tests/
├── unit/
│   ├── sensors/
│   │   ├── test_sensor_manager.c
│   │   ├── test_environmental_sensor.c
│   │   └── test_motion_sensor.c
│   ├── connectivity/
│   │   ├── test_cellular_manager.c
│   │   └── test_mqtt_client.c
│   ├── data/
│   │   ├── test_data_processor.c
│   │   └── test_data_buffer.c
│   ├── ui/
│   │   ├── test_led_controller.c
│   │   └── test_button_handler.c
│   ├── power/
│   │   └── test_power_manager.c
│   └── config/
│       └── test_config_manager.c
└── mocks/
    ├── mock_i2c.c
    ├── mock_spi.c
    ├── mock_gpio.c
    └── mock_network.c
```

## Sensor Interface Tests

### Environmental Sensor Tests (BME680)

#### test_environmental_sensor.c
```c
// Test Functions:
void test_bme680_initialization(void)
void test_bme680_temperature_reading(void)  
void test_bme680_humidity_reading(void)
void test_bme680_pressure_reading(void)
void test_bme680_gas_resistance_reading(void)
void test_bme680_calibration_data(void)
void test_bme680_error_conditions(void)
void test_bme680_power_modes(void)
```

**Test Cases:**
1. **Initialization Tests**
   - Verify I2C communication setup
   - Check device ID register read
   - Validate calibration data loading
   - Test sensor configuration parameters

2. **Reading Tests**  
   - Temperature: -40°C to +85°C range validation
   - Humidity: 0% to 100% RH range validation
   - Pressure: 300hPa to 1100hPa range validation
   - Gas resistance: 0 to 500kΩ range validation

3. **Error Condition Tests**
   - I2C communication failures
   - Invalid sensor responses  
   - Timeout conditions
   - Calibration data corruption

4. **Performance Tests**
   - Reading latency < 50ms
   - Power consumption in different modes
   - Measurement accuracy within ±1%

### Motion Sensor Tests (ADXL372/ADXL362)

#### test_motion_sensor.c
```c
// Test Functions:
void test_accelerometer_initialization(void)
void test_accelerometer_data_reading(void)
void test_accelerometer_threshold_detection(void)
void test_accelerometer_fifo_operation(void)
void test_accelerometer_interrupt_handling(void)
void test_accelerometer_power_management(void)
void test_accelerometer_self_test(void)
```

**Test Cases:**
1. **Initialization Tests**
   - SPI interface setup verification
   - Device ID validation
   - Register configuration check
   - Self-test execution

2. **Data Reading Tests**
   - X/Y/Z axis data acquisition
   - Data range: ±2g, ±4g, ±8g modes
   - Data resolution: 12-bit accuracy
   - Sample rate configuration

3. **Feature Tests**
   - Motion threshold detection
   - Tap detection algorithms
   - FIFO buffer management
   - Interrupt signal generation

4. **Power Management Tests**
   - Sleep mode transitions
   - Wake-on-motion functionality
   - Current consumption validation

### Sensor Manager Tests

#### test_sensor_manager.c
```c
// Test Functions:
void test_sensor_manager_initialization(void)
void test_sensor_polling_schedule(void)
void test_sensor_data_aggregation(void)
void test_sensor_error_recovery(void)
void test_sensor_power_optimization(void)
void test_sensor_calibration_management(void)
```

**Test Cases:**
1. **Manager Initialization**
   - All sensors initialized correctly
   - Polling threads created
   - Data structures allocated

2. **Polling and Scheduling**
   - Configurable polling intervals
   - Thread synchronization
   - Priority management

3. **Data Management**
   - Sensor data aggregation
   - Timestamp synchronization
   - Data validation and filtering

4. **Error Recovery**
   - Sensor failure detection
   - Automatic retry mechanisms
   - Graceful degradation

## Mock Objects and Stubs

### I2C Mock Implementation
```c
// mock_i2c.c
struct mock_i2c_transaction {
    uint16_t addr;
    uint8_t *tx_buf;
    uint8_t *rx_buf;
    size_t num_bytes;
    int expected_return;
};

void mock_i2c_expect_transaction(struct mock_i2c_transaction *trans);
void mock_i2c_verify_all_transactions(void);
```

### SPI Mock Implementation
```c  
// mock_spi.c
struct mock_spi_transaction {
    uint8_t *tx_buf;
    uint8_t *rx_buf;  
    size_t len;
    int expected_return;
};

void mock_spi_expect_transaction(struct mock_spi_transaction *trans);
void mock_spi_inject_error(int error_code);
```

## Test Execution Framework

### Test Runner Configuration
```c
// test_runner.c
void setUp(void) {
    // Initialize mocks and test environment
    mock_i2c_reset();
    mock_spi_reset();
    mock_gpio_reset();
}

void tearDown(void) {
    // Verify mocks and cleanup
    mock_i2c_verify_all_transactions();
    mock_spi_verify_all_transactions();
}

int main(void) {
    UNITY_BEGIN();
    
    // Sensor tests
    RUN_TEST(test_bme680_initialization);
    RUN_TEST(test_bme680_temperature_reading);
    // ... more tests
    
    return UNITY_END();
}
```

### Test Build Configuration
```cmake
# tests/CMakeLists.txt
find_package(Unity REQUIRED)

# Unit test executable
add_executable(unit_tests
    unit/sensors/test_sensor_manager.c
    unit/sensors/test_environmental_sensor.c
    unit/sensors/test_motion_sensor.c
    mocks/mock_i2c.c
    mocks/mock_spi.c
    mocks/mock_gpio.c
)

target_link_libraries(unit_tests Unity::Unity)
target_include_directories(unit_tests PRIVATE ../src/)
```

## Test Metrics and Coverage

### Coverage Requirements
- **Line Coverage**: >95% for sensor modules
- **Branch Coverage**: >90% for conditional logic  
- **Function Coverage**: 100% for public APIs
- **Path Coverage**: >80% for complex functions

### Performance Benchmarks
- Test execution time: <30 seconds for full suite
- Memory usage during tests: <50KB heap
- Test isolation: No test dependencies
- Deterministic results: 100% reproducible

### Continuous Integration
- Automated test execution on code commits
- Coverage report generation
- Performance regression detection
- Test result notifications and reporting