# Power Consumption Testing Methodology - Nordic Thingy91 DK Demo

## Overview
Power consumption testing is critical for battery-operated IoT devices. This methodology provides comprehensive testing approaches to validate battery life, optimize power efficiency, and ensure the device meets deployment requirements for extended autonomous operation.

## Power Testing Objectives

### Primary Goals
1. **Battery Life Validation** - Confirm >7 days operational life with standard usage
2. **Power Profile Optimization** - Minimize current consumption in all operating modes
3. **Power State Management** - Validate efficient sleep/wake transitions
4. **Thermal Management** - Ensure safe operation under various power loads
5. **Regulatory Compliance** - Meet power consumption standards for cellular devices

### Key Power Metrics
```c
// power_metrics.h
struct power_consumption_profile {
    // Active Mode Consumption
    uint32_t active_mode_current_ma;          // Target: <50mA
    uint32_t sensor_reading_current_ma;       // Target: <30mA
    uint32_t data_processing_current_ma;      // Target: <25mA
    uint32_t network_idle_current_ma;         // Target: <15mA
    uint32_t network_transmit_current_ma;     // Target: <200mA (peak)
    
    // Sleep Mode Consumption
    uint32_t deep_sleep_current_ua;           // Target: <10µA
    uint32_t light_sleep_current_ua;          // Target: <100µA
    uint32_t retention_sleep_current_ua;      // Target: <50µA
    
    // Dynamic Power Characteristics
    uint32_t startup_current_ma;              // Cold boot current
    uint32_t wake_up_time_ms;                 // Sleep to active transition
    uint32_t sleep_enter_time_ms;             // Active to sleep transition
    uint32_t power_on_reset_current_ma;       // POR current spike
    
    // Battery Characteristics
    uint32_t battery_capacity_mah;            // 1000mAh typical
    uint32_t battery_life_estimate_hours;     // Target: >168 hours (7 days)
    uint32_t charging_current_ma;             // USB charging current
    uint32_t battery_discharge_curve;         // Voltage vs capacity
};
```

## Power Measurement Infrastructure

### Hardware Test Setup

#### Power Measurement Equipment
```
[Battery Simulator] → [Power Monitor] → [Thingy91 DK] → [Test Controller]
        ↓                    ↓                ↓                ↓
[DC Supply Control] → [Current/Voltage] → [Device Under] → [Automated Test]
                        Measurement         Test (DUT)        Framework
```

**Required Equipment:**
- **Precision Power Analyzer**: Keysight N6705C or similar (nA resolution)
- **Battery Simulator**: Programmable voltage source (2.7V-4.2V)
- **Environmental Chamber**: Temperature/humidity control
- **RF Shield Box**: Controlled cellular signal environment
- **Oscilloscope**: Tektronix MSO for transient analysis
- **Thermal Camera**: FLIR for thermal profiling

#### DUT Power Interface Modification
```c
// Power measurement shunt configuration
#define POWER_SHUNT_RESISTANCE_OHMS     0.1    // 100mΩ precision shunt
#define CURRENT_MEASUREMENT_GAIN        100    // Instrumentation amplifier
#define ADC_VOLTAGE_REFERENCE           3.3    // V
#define ADC_RESOLUTION_BITS             16     // 16-bit ADC

// Power measurement calibration
struct power_measurement_calibration {
    float shunt_resistance_ohms;
    float amplifier_gain;
    float adc_reference_voltage;
    float offset_compensation_mv;
    float temperature_coefficient;
};
```

### Software Power Profiling

#### Real-Time Power Monitoring
```c
// power_profiler.c
struct power_measurement {
    uint32_t timestamp_ms;
    uint32_t voltage_mv;              // Battery voltage
    uint32_t current_ua;              // Instantaneous current
    uint32_t power_uw;               // Instantaneous power
    enum system_state state;          // Device operational state
    uint32_t temperature_celsius;     // Die temperature
};

enum system_state {
    STATE_BOOT,
    STATE_SENSOR_INIT,
    STATE_NETWORK_CONNECT,
    STATE_ACTIVE_SENSING,
    STATE_DATA_PROCESSING,
    STATE_NETWORK_TRANSMIT,
    STATE_LIGHT_SLEEP,
    STATE_DEEP_SLEEP,
    STATE_ERROR_RECOVERY
};

void power_profiler_init(void);
void power_profiler_log_measurement(struct power_measurement *measurement);
void power_profiler_set_state(enum system_state state);
float power_profiler_calculate_average_current(uint32_t duration_ms);
```

## Power Consumption Test Scenarios

### Scenario 1: Baseline Power Profile

#### test_baseline_power_profile.c
```c
struct baseline_power_config {
    uint32_t measurement_duration_minutes;    // 60 minutes
    uint32_t sampling_rate_hz;                // 1000 Hz
    uint32_t sensor_polling_interval_ms;      // 5000ms (normal operation)
    uint32_t network_transmission_interval_ms; // 60000ms (every minute)
    bool enable_power_optimization;           // true
    bool log_state_transitions;               // true
};

void test_baseline_power_consumption(struct baseline_power_config *config);
```

**Test Execution:**
1. **System Initialization** (0-30s)
   - Monitor cold boot current profile
   - Measure sensor initialization power
   - Track network registration power

2. **Steady State Operation** (30s-60min)
   - Continuous power monitoring
   - State transition analysis
   - Average current calculation

3. **Power State Analysis** (Real-time)
   - Active mode power breakdown
   - Sleep mode current validation
   - Transition efficiency measurement

**Expected Power Profile:**
```
Boot: 0-30s     → 50-150mA (initialization)
Active: 30s-5s  → 25-40mA (sensor reading + processing)
TX: 5s burst    → 150-250mA (network transmission)  
Sleep: 55s      → <50µA (deep sleep)
Average: 60min  → <8mA (overall system)
```

### Scenario 2: Extended Battery Life Test

#### test_battery_life_validation.c
```c
struct battery_life_config {
    uint32_t test_duration_hours;             // 168 hours (7 days)
    uint32_t battery_capacity_mah;            // 1000mAh
    uint32_t cutoff_voltage_mv;               // 2700mV
    uint32_t monitoring_interval_minutes;     // 15 minutes
    bool simulate_battery_aging;              // true
    bool temperature_cycling;                 // true
};

void test_extended_battery_life(struct battery_life_config *config);
```

**Battery Life Calculation:**
```c
// Battery life estimation algorithm
float calculate_battery_life_hours(float average_current_ma, 
                                   float battery_capacity_mah,
                                   float efficiency_factor) {
    // Peukert's equation for battery discharge
    float peukert_exponent = 1.3;  // Typical for Li-ion
    float effective_capacity = battery_capacity_mah * 
                              pow(efficiency_factor, peukert_exponent);
    
    return effective_capacity / average_current_ma;
}

// Battery discharge curve modeling
float battery_voltage_from_capacity(float remaining_capacity_percent) {
    // Li-ion discharge curve approximation
    if (remaining_capacity_percent > 80) {
        return 4.2 - (100 - remaining_capacity_percent) * 0.003;
    } else if (remaining_capacity_percent > 20) {
        return 3.8 - (80 - remaining_capacity_percent) * 0.0033;
    } else {
        return 3.4 - (20 - remaining_capacity_percent) * 0.035;
    }
}
```

### Scenario 3: Power State Transition Testing

#### test_power_state_transitions.c
```c
struct power_transition_config {
    uint32_t transition_cycles;               // 1000 cycles
    uint32_t sleep_duration_ms;               // 1000ms
    uint32_t active_duration_ms;              // 100ms
    bool measure_transition_time;             // true
    bool validate_wake_up_sources;            // true
};

void test_power_state_transitions(struct power_transition_config *config);
```

**Power State Machine Testing:**
```
Active → Light Sleep → Deep Sleep → Active
  ↓         ↓            ↓           ↓
Measure   Measure      Measure    Measure
Entry     Current      Current    Wake-up
Time      <100µA       <10µA      Time
```

**Transition Metrics:**
- **Sleep Entry Time**: <5ms (active to deep sleep)
- **Wake-up Time**: <10ms (deep sleep to active)
- **Current Settling Time**: <100ms to steady state
- **State Retention**: RAM contents preserved during sleep

### Scenario 4: Network Power Optimization

#### test_network_power_optimization.c
```c
struct network_power_config {
    uint32_t psm_active_timer_seconds;        // 10 seconds
    uint32_t psm_periodic_tau_minutes;        // 30 minutes
    uint32_t edrx_cycle_length_seconds;       // 20.48 seconds
    bool enable_psm_mode;                     // true
    bool enable_edrx_mode;                    // true
    bool optimize_connection_intervals;       // true
};

void test_network_power_optimization(struct network_power_config *config);
```

**Network Power Features:**
1. **Power Saving Mode (PSM)**
   - Negotiated sleep periods with network
   - Modem power-down during inactive periods
   - Wake-up for scheduled data transmission

2. **Extended Discontinuous Reception (eDRX)**
   - Extended sleep between paging occasions
   - Network synchronization maintenance
   - Reduced idle power consumption

3. **Connection Management**
   - Efficient MQTT keep-alive intervals
   - TCP connection reuse
   - TLS session resumption

### Scenario 5: Sensor Power Management

#### test_sensor_power_management.c
```c
struct sensor_power_config {
    uint32_t sensor_active_time_ms;           // 50ms per reading
    uint32_t sensor_sleep_time_ms;            // 4950ms between readings
    bool enable_sensor_power_down;            // true
    bool stagger_sensor_readings;             // true
    bool use_interrupt_based_sampling;        // true
};

void test_sensor_power_management(struct sensor_power_config *config);
```

**Sensor Power Optimization:**
- **BME680 Power Management**
  - Forced mode for single measurements
  - Sensor sleep between readings
  - Heater optimization for gas sensing

- **ADXL372/ADXL362 Power Management**
  - Motion-triggered wake-up
  - FIFO-based data collection
  - Activity/inactivity detection

- **I2C/SPI Bus Power**
  - Bus power-down when idle
  - Pull-up resistor optimization
  - Clock gating for unused peripherals

## Advanced Power Analysis

### Power Spectral Analysis

#### power_spectral_analyzer.py
```python
import numpy as np
import matplotlib.pyplot as plt
from scipy import signal

class PowerSpectralAnalyzer:
    def __init__(self, sampling_rate):
        self.fs = sampling_rate
        
    def analyze_power_spectrum(self, current_data):
        # Compute power spectral density
        frequencies, psd = signal.welch(current_data, self.fs, nperseg=1024)
        
        # Identify dominant frequency components
        dominant_freqs = frequencies[np.argsort(psd)[-5:]]
        
        # Correlate with system activity
        return {
            'frequencies': frequencies,
            'power_spectral_density': psd,
            'dominant_frequencies': dominant_freqs,
            'total_power': np.sum(psd)
        }
    
    def detect_power_anomalies(self, baseline_psd, current_psd):
        # Statistical analysis for anomaly detection
        difference = np.abs(current_psd - baseline_psd)
        threshold = 3 * np.std(baseline_psd)
        anomalies = np.where(difference > threshold)[0]
        
        return {
            'anomaly_frequencies': anomalies,
            'anomaly_magnitude': difference[anomalies],
            'anomaly_count': len(anomalies)
        }
```

### Thermal Power Analysis

#### thermal_power_analyzer.c
```c
struct thermal_power_data {
    uint32_t ambient_temperature_celsius;
    uint32_t die_temperature_celsius;
    uint32_t case_temperature_celsius;
    uint32_t thermal_resistance_c_per_w;
    uint32_t power_dissipation_mw;
    uint32_t thermal_time_constant_seconds;
};

void analyze_thermal_power_relationship(struct thermal_power_data *data);
void validate_thermal_shutdown_protection(void);
void measure_thermal_time_constants(void);
```

**Thermal Analysis:**
- **Power vs Temperature**: Characterize power consumption across temperature range
- **Thermal Shutdown**: Validate protection mechanisms at >85°C
- **Thermal Time Constants**: Measure thermal response to power changes
- **Heat Dissipation**: Calculate thermal resistance and heat paths

## Power Optimization Strategies

### Algorithmic Power Optimization

#### power_optimizer.c
```c
struct power_optimization_config {
    // Sensor optimization
    bool adaptive_sampling_rate;              // Adjust based on activity
    bool predictive_sensor_wake_up;           // ML-based wake prediction
    bool sensor_data_fusion;                  // Reduce redundant sampling
    
    // Network optimization  
    bool adaptive_transmission_interval;      // Based on data priority
    bool connection_keep_alive_optimization;  // Dynamic MQTT intervals
    bool data_compression_for_power;          // CPU vs transmission trade-off
    
    // CPU optimization
    bool dynamic_frequency_scaling;           // Scale CPU based on load
    bool task_scheduling_optimization;        // Power-aware task scheduling
    bool peripheral_power_gating;             // Disable unused peripherals
};

void apply_power_optimizations(struct power_optimization_config *config);
float measure_optimization_effectiveness(void);
```

### Machine Learning Power Optimization

#### ml_power_optimizer.py
```python
class MLPowerOptimizer:
    def __init__(self):
        self.power_model = None
        self.usage_pattern_classifier = None
        
    def train_power_model(self, historical_data):
        # Train predictive model for power consumption
        # Based on sensor activity, network usage, environmental factors
        pass
        
    def predict_optimal_sampling_rate(self, context):
        # Predict minimum sampling rate for required accuracy
        # Balance power consumption with data quality
        pass
        
    def optimize_sleep_schedule(self, usage_patterns):
        # Predict idle periods for aggressive power saving
        # Optimize wake-up timing for network synchronization
        pass
        
    def adaptive_power_management(self, real_time_data):
        # Real-time power optimization decisions
        # Dynamic adjustment of system parameters
        pass
```

## Power Test Automation Framework

### Automated Power Test Suite

#### power_test_orchestrator.py
```python
class PowerTestOrchestrator:
    def __init__(self, power_analyzer, device_controller):
        self.power_analyzer = power_analyzer
        self.device = device_controller
        self.test_results = []
        
    def run_power_test_suite(self, test_configurations):
        for config in test_configurations:
            # Setup test environment
            self.setup_power_measurement(config)
            
            # Execute power test
            result = self.execute_power_test(config)
            
            # Analyze power data
            analysis = self.analyze_power_consumption(result)
            
            # Validate against requirements
            validation = self.validate_power_requirements(analysis)
            
            self.test_results.append({
                'config': config,
                'measurements': result,
                'analysis': analysis,
                'validation': validation
            })
            
        return self.generate_power_test_report()
    
    def generate_power_test_report(self):
        # Create comprehensive power analysis report
        # Include power profiles, efficiency metrics, optimization recommendations
        pass
```

### Continuous Power Monitoring

#### continuous_power_monitor.c
```c
struct continuous_power_monitor {
    bool enable_real_time_monitoring;
    uint32_t monitoring_interval_ms;
    uint32_t alert_threshold_ma;
    bool log_to_flash_storage;
    bool enable_cloud_reporting;
};

void continuous_power_monitor_init(struct continuous_power_monitor *config);
void continuous_power_monitor_task(void);
void power_consumption_alert_handler(uint32_t current_ma);
void generate_power_consumption_report(void);
```

## Power Test Acceptance Criteria

### Power Consumption Targets

| Operating Mode | Target Current | Maximum Acceptable |
|---------------|----------------|-------------------|
| Deep Sleep | <10µA | <20µA |
| Light Sleep | <100µA | <200µA |
| Sensor Reading | <30mA | <50mA |
| Data Processing | <25mA | <40mA |
| Network Idle | <15mA | <25mA |
| Network TX (Peak) | <250mA | <300mA |
| Average (5min cycle) | <8mA | <12mA |

### Battery Life Requirements

| Scenario | Target Battery Life | Minimum Acceptable |
|----------|-------------------|------------------|
| Normal Operation | >7 days | >5 days |
| Power Save Mode | >14 days | >10 days |
| Emergency Mode | >30 days | >21 days |
| Standby Mode | >90 days | >60 days |

### Power Efficiency Metrics

```yaml
power_efficiency_kpis:
  energy_per_sensor_reading:
    target: "<50µJ"
    maximum: "<100µJ"
  energy_per_data_transmission:
    target: "<500mJ"  
    maximum: "<1J"
  sleep_mode_efficiency:
    target: ">99.9%"
    minimum: ">99.5%"
  power_management_overhead:
    target: "<5%"
    maximum: "<10%"
```

## Power Optimization Recommendations

### Immediate Optimizations
1. **Sensor Power Management**
   - Implement sensor-specific sleep modes
   - Use interrupt-driven sampling where possible
   - Optimize I2C/SPI bus usage

2. **Network Optimization**
   - Enable PSM and eDRX features
   - Optimize MQTT keep-alive intervals
   - Implement connection pooling

3. **CPU Power Management**
   - Use lowest possible clock frequencies
   - Implement dynamic voltage/frequency scaling
   - Optimize task scheduling for power

### Advanced Optimizations
1. **Machine Learning Integration**
   - Predictive power management
   - Usage pattern optimization
   - Adaptive sampling strategies

2. **Hardware Optimizations**
   - Custom power management circuits
   - Ultra-low power wake-up triggers
   - Energy harvesting integration

The power consumption testing methodology ensures the Nordic Thingy91 DK demo achieves optimal battery life while maintaining full functionality and performance requirements.