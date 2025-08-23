/*
 * Copyright (c) 2024 Nordic Semiconductor ASA
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#ifndef POWER_MANAGER_H_
#define POWER_MANAGER_H_

#include <zephyr/kernel.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief Power modes
 */
enum power_mode {
    POWER_MODE_NORMAL,          /* Normal operation */
    POWER_MODE_LOW_POWER,       /* Low power mode */
    POWER_MODE_ULTRA_LOW_POWER, /* Ultra low power mode */
    POWER_MODE_SLEEP,           /* Sleep mode */
    POWER_MODE_DEEP_SLEEP       /* Deep sleep mode */
};

/**
 * @brief Power statistics
 */
struct power_stats {
    uint32_t total_uptime_ms;           /* Total uptime */
    uint32_t active_time_ms;            /* Time in active mode */
    uint32_t sleep_time_ms;             /* Time in sleep mode */
    uint32_t deep_sleep_time_ms;        /* Time in deep sleep */
    uint32_t power_mode_switches;       /* Number of mode switches */
    float avg_current_ma;               /* Average current consumption */
    float battery_voltage_v;            /* Battery voltage */
    uint8_t battery_level_percent;      /* Battery level percentage */
    uint32_t wake_events;               /* Number of wake events */
};

/**
 * @brief Power configuration
 */
struct power_config {
    uint32_t idle_timeout_ms;           /* Idle timeout for sleep */
    uint32_t deep_sleep_timeout_ms;     /* Timeout for deep sleep */
    bool enable_auto_sleep;             /* Enable automatic sleep */
    bool enable_wake_on_button;         /* Wake on button press */
    bool enable_wake_on_sensor;         /* Wake on sensor interrupt */
    bool enable_wake_on_timer;          /* Wake on timer */
    uint32_t wake_timer_interval_ms;    /* Wake timer interval */
    float low_battery_threshold_v;      /* Low battery threshold */
    bool enable_battery_monitoring;     /* Enable battery monitoring */
};

/**
 * @brief Power event callback function type
 */
typedef void (*power_event_cb_t)(enum power_mode old_mode, enum power_mode new_mode);

/**
 * @brief Initialize power manager
 * 
 * @return 0 on success, negative errno on failure
 */
int power_manager_init(void);

/**
 * @brief Configure power management
 * 
 * @param config Power configuration
 * @return 0 on success, negative errno on failure
 */
int power_manager_configure(const struct power_config *config);

/**
 * @brief Set power mode
 * 
 * @param mode Power mode to set
 * @return 0 on success, negative errno on failure
 */
int power_manager_set_mode(enum power_mode mode);

/**
 * @brief Get current power mode
 * 
 * @return Current power mode
 */
enum power_mode power_manager_get_mode(void);

/**
 * @brief Toggle between normal and low power mode
 * 
 * @return 0 on success, negative errno on failure
 */
int power_manager_toggle_power_mode(void);

/**
 * @brief Request sleep mode
 * 
 * @param duration_ms Sleep duration in milliseconds, 0 for indefinite
 * @return 0 on success, negative errno on failure
 */
int power_manager_request_sleep(uint32_t duration_ms);

/**
 * @brief Wake from sleep mode
 * 
 * @return 0 on success, negative errno on failure
 */
int power_manager_wake(void);

/**
 * @brief Get power statistics
 * 
 * @param stats Pointer to power statistics structure
 * @return 0 on success, negative errno on failure
 */
int power_manager_get_stats(struct power_stats *stats);

/**
 * @brief Reset power statistics
 * 
 * @return 0 on success, negative errno on failure
 */
int power_manager_reset_stats(void);

/**
 * @brief Set power event callback
 * 
 * @param callback Callback function for power events
 * @return 0 on success, negative errno on failure
 */
int power_manager_set_event_callback(power_event_cb_t callback);

/**
 * @brief Get battery voltage
 * 
 * @return Battery voltage in volts, or negative value on error
 */
float power_manager_get_battery_voltage(void);

/**
 * @brief Get battery level percentage
 * 
 * @return Battery level in percent (0-100), or negative value on error
 */
int power_manager_get_battery_level(void);

/**
 * @brief Check if battery is low
 * 
 * @return True if battery is low, false otherwise
 */
bool power_manager_is_battery_low(void);

/**
 * @brief Enable or disable power management
 * 
 * @param enable True to enable, false to disable
 * @return 0 on success, negative errno on failure
 */
int power_manager_enable(bool enable);

/**
 * @brief Force system reset
 * 
 * @return This function does not return
 */
void power_manager_system_reset(void);

/**
 * @brief Shutdown system
 * 
 * @return This function does not return
 */
void power_manager_system_shutdown(void);

#ifdef __cplusplus
}
#endif

#endif /* POWER_MANAGER_H_ */