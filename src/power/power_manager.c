/*
 * Copyright (c) 2024 Nordic Semiconductor ASA
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#include "power_manager.h"

#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>
#include <zephyr/device.h>
#include <zephyr/devicetree.h>
#include <zephyr/drivers/adc.h>
#include <zephyr/pm/pm.h>
#include <zephyr/pm/device.h>
#include <zephyr/sys/reboot.h>
#include <hal/nrf_power.h>

LOG_MODULE_REGISTER(power_manager, CONFIG_LOG_DEFAULT_LEVEL);

/* Power configuration defaults */
static struct power_config config = {
    .idle_timeout_ms = 60000,           /* 1 minute idle timeout */
    .deep_sleep_timeout_ms = 300000,    /* 5 minutes for deep sleep */
    .enable_auto_sleep = true,
    .enable_wake_on_button = true,
    .enable_wake_on_sensor = true,
    .enable_wake_on_timer = true,
    .wake_timer_interval_ms = 30000,    /* Wake every 30 seconds */
    .low_battery_threshold_v = 3.2f,    /* 3.2V low battery threshold */
    .enable_battery_monitoring = true
};

/* Power manager state */
static enum power_mode current_mode = POWER_MODE_NORMAL;
static power_event_cb_t event_callback = NULL;
static bool manager_enabled = true;
static bool initialized = false;

/* Power statistics */
static struct power_stats stats = {0};
static uint64_t mode_start_time = 0;
static uint64_t last_update_time = 0;

/* ADC for battery monitoring */
#if DT_NODE_EXISTS(DT_PATH(zephyr_user)) && DT_NODE_HAS_PROP(DT_PATH(zephyr_user), io_channels)
static const struct adc_dt_spec adc_channel = ADC_DT_SPEC_GET(DT_PATH(zephyr_user));
#else
/* Fallback ADC configuration for battery monitoring */
#define ADC_NODE DT_NODELABEL(adc)
static const struct device *adc_dev;
static struct adc_channel_cfg adc_cfg = {
    .gain = ADC_GAIN_1_6,
    .reference = ADC_REF_INTERNAL,
    .acquisition_time = ADC_ACQ_TIME(ADC_ACQ_TIME_MICROSECONDS, 10),
    .channel_id = 0,
    .input_positive = NRF_SAADC_INPUT_VDD
};
#endif

/* Work items */
static struct k_work_delayable power_monitor_work;
static struct k_work_delayable sleep_timeout_work;

/* Forward declarations */
static void power_monitor_work_handler(struct k_work *work);
static void sleep_timeout_work_handler(struct k_work *work);
static void update_power_stats(void);
static float read_battery_voltage(void);
static int calculate_battery_level(float voltage);
static void set_power_mode_internal(enum power_mode new_mode);
static int init_battery_monitoring(void);

static void power_monitor_work_handler(struct k_work *work)
{
    if (!manager_enabled || !config.enable_battery_monitoring) {
        return;
    }
    
    /* Update power statistics */
    update_power_stats();
    
    /* Read battery voltage */
    float battery_voltage = read_battery_voltage();
    if (battery_voltage > 0) {
        stats.battery_voltage_v = battery_voltage;
        stats.battery_level_percent = calculate_battery_level(battery_voltage);
        
        /* Check for low battery */
        if (battery_voltage < config.low_battery_threshold_v) {
            LOG_WRN("Low battery detected: %.2fV", battery_voltage);
            
            /* Switch to low power mode automatically */
            if (current_mode == POWER_MODE_NORMAL) {
                power_manager_set_mode(POWER_MODE_LOW_POWER);
            }
        }
    }
    
    /* Schedule next monitoring cycle */
    k_work_schedule(&power_monitor_work, K_SECONDS(30));
}

static void sleep_timeout_work_handler(struct k_work *work)
{
    if (!manager_enabled || !config.enable_auto_sleep) {
        return;
    }
    
    LOG_INF("Sleep timeout reached, entering sleep mode");
    power_manager_set_mode(POWER_MODE_SLEEP);
}

static void update_power_stats(void)
{
    uint64_t current_time = k_uptime_get();
    uint64_t time_in_mode = current_time - mode_start_time;
    
    /* Update time spent in current mode */
    switch (current_mode) {
    case POWER_MODE_NORMAL:
        stats.active_time_ms += time_in_mode;
        break;
    case POWER_MODE_LOW_POWER:
    case POWER_MODE_ULTRA_LOW_POWER:
        stats.active_time_ms += time_in_mode;
        break;
    case POWER_MODE_SLEEP:
        stats.sleep_time_ms += time_in_mode;
        break;
    case POWER_MODE_DEEP_SLEEP:
        stats.deep_sleep_time_ms += time_in_mode;
        break;
    }
    
    stats.total_uptime_ms = current_time;
    last_update_time = current_time;
}

static float read_battery_voltage(void)
{
#if DT_NODE_EXISTS(DT_PATH(zephyr_user)) && DT_NODE_HAS_PROP(DT_PATH(zephyr_user), io_channels)
    int16_t buf;
    struct adc_sequence sequence = {
        .buffer = &buf,
        .buffer_size = sizeof(buf)
    };
    
    int ret = adc_sequence_init_dt(&adc_channel, &sequence);
    if (ret < 0) {
        LOG_ERR("Could not initalize sequnce");
        return -1.0f;
    }
    
    ret = adc_read(adc_channel.dev, &sequence);
    if (ret < 0) {
        LOG_ERR("Could not read ADC (%d)", ret);
        return -1.0f;
    }
    
    int32_t val_mv = buf;
    ret = adc_raw_to_millivolts_dt(&adc_channel, &val_mv);
    if (ret < 0) {
        LOG_ERR("Buffer cannot hold channels");
        return -1.0f;
    }
    
    /* Convert to actual battery voltage (accounting for voltage divider) */
    float voltage = (float)val_mv / 1000.0f * 2.0f;  /* Assuming 1:2 voltage divider */
    return voltage;
#else
    if (!adc_dev) {
        return 3.6f;  /* Simulated battery voltage */
    }
    
    int16_t buf;
    struct adc_sequence sequence = {
        .buffer = &buf,
        .buffer_size = sizeof(buf),
        .resolution = 12,
    };
    
    adc_sequence_init_dt(&adc_cfg, &sequence);
    
    int ret = adc_read(adc_dev, &sequence);
    if (ret < 0) {
        LOG_WRN("ADC read failed: %d", ret);
        return 3.6f;  /* Return simulated value */
    }
    
    /* Convert ADC value to voltage */
    float voltage = (float)buf * 3.6f / 4096.0f * 6.0f;  /* VDD with 1/6 gain */
    return voltage;
#endif
}

static int calculate_battery_level(float voltage)
{
    /* Simple battery level calculation for Li-ion battery */
    if (voltage >= 4.1f) return 100;
    if (voltage >= 4.0f) return 90;
    if (voltage >= 3.9f) return 80;
    if (voltage >= 3.8f) return 70;
    if (voltage >= 3.7f) return 60;
    if (voltage >= 3.6f) return 50;
    if (voltage >= 3.5f) return 40;
    if (voltage >= 3.4f) return 30;
    if (voltage >= 3.3f) return 20;
    if (voltage >= 3.2f) return 10;
    return 0;
}

static void set_power_mode_internal(enum power_mode new_mode)
{
    if (new_mode == current_mode) {
        return;
    }
    
    enum power_mode old_mode = current_mode;
    
    /* Update statistics before mode change */
    update_power_stats();
    
    /* Configure hardware for new power mode */
    switch (new_mode) {
    case POWER_MODE_NORMAL:
        /* Enable all peripherals */
        LOG_INF("Switching to normal power mode");
        break;
        
    case POWER_MODE_LOW_POWER:
        /* Reduce peripheral activity */
        LOG_INF("Switching to low power mode");
        break;
        
    case POWER_MODE_ULTRA_LOW_POWER:
        /* Minimize peripheral activity */
        LOG_INF("Switching to ultra low power mode");
        break;
        
    case POWER_MODE_SLEEP:
        /* Enter sleep mode */
        LOG_INF("Entering sleep mode");
        break;
        
    case POWER_MODE_DEEP_SLEEP:
        /* Enter deep sleep mode */
        LOG_INF("Entering deep sleep mode");
        break;
    }
    
    current_mode = new_mode;
    mode_start_time = k_uptime_get();
    stats.power_mode_switches++;
    
    /* Trigger callback */
    if (event_callback) {
        event_callback(old_mode, new_mode);
    }
    
    /* Schedule sleep timeout if in active mode */
    if (config.enable_auto_sleep && 
        (new_mode == POWER_MODE_NORMAL || new_mode == POWER_MODE_LOW_POWER)) {
        k_work_schedule(&sleep_timeout_work, K_MSEC(config.idle_timeout_ms));
    } else {
        k_work_cancel_delayable(&sleep_timeout_work);
    }
}

static int init_battery_monitoring(void)
{
#if DT_NODE_EXISTS(DT_PATH(zephyr_user)) && DT_NODE_HAS_PROP(DT_PATH(zephyr_user), io_channels)
    if (!adc_is_ready_dt(&adc_channel)) {
        LOG_ERR("ADC controller device not ready");
        return -ENODEV;
    }
    
    int ret = adc_channel_setup_dt(&adc_channel);
    if (ret < 0) {
        LOG_ERR("Could not setup channel (%d)", ret);
        return ret;
    }
    
    LOG_INF("Battery monitoring initialized with ADC");
    return 0;
#else
    adc_dev = DEVICE_DT_GET(ADC_NODE);
    if (!device_is_ready(adc_dev)) {
        LOG_WRN("ADC device not ready, battery monitoring disabled");
        config.enable_battery_monitoring = false;
        return -ENODEV;
    }
    
    int ret = adc_channel_setup(adc_dev, &adc_cfg);
    if (ret < 0) {
        LOG_WRN("ADC channel setup failed: %d", ret);
        config.enable_battery_monitoring = false;
        return ret;
    }
    
    LOG_INF("Battery monitoring initialized");
    return 0;
#endif
}

int power_manager_init(void)
{
    LOG_INF("Initializing power manager");
    
    /* Initialize work items */
    k_work_init_delayable(&power_monitor_work, power_monitor_work_handler);
    k_work_init_delayable(&sleep_timeout_work, sleep_timeout_work_handler);
    
    /* Initialize battery monitoring */
    if (config.enable_battery_monitoring) {
        init_battery_monitoring();
    }
    
    /* Initialize statistics */
    memset(&stats, 0, sizeof(stats));
    current_mode = POWER_MODE_NORMAL;
    mode_start_time = k_uptime_get();
    last_update_time = mode_start_time;
    
    /* Start power monitoring */
    k_work_schedule(&power_monitor_work, K_SECONDS(5));
    
    /* Enable auto sleep timeout */
    if (config.enable_auto_sleep) {
        k_work_schedule(&sleep_timeout_work, K_MSEC(config.idle_timeout_ms));
    }
    
    initialized = true;
    LOG_INF("Power manager initialized successfully");
    
    return 0;
}

int power_manager_configure(const struct power_config *new_config)
{
    if (!new_config) {
        return -EINVAL;
    }
    
    memcpy(&config, new_config, sizeof(config));
    
    LOG_INF("Power manager configured - Auto sleep: %s, Battery monitoring: %s, "
            "Low battery threshold: %.2fV",
            config.enable_auto_sleep ? "enabled" : "disabled",
            config.enable_battery_monitoring ? "enabled" : "disabled",
            config.low_battery_threshold_v);
    
    /* Restart battery monitoring if configuration changed */
    if (initialized && config.enable_battery_monitoring) {
        k_work_reschedule(&power_monitor_work, K_SECONDS(1));
    }
    
    return 0;
}

int power_manager_set_mode(enum power_mode mode)
{
    if (!manager_enabled) {
        return -ENODEV;
    }
    
    set_power_mode_internal(mode);
    return 0;
}

enum power_mode power_manager_get_mode(void)
{
    return current_mode;
}

int power_manager_toggle_power_mode(void)
{
    enum power_mode new_mode;
    
    switch (current_mode) {
    case POWER_MODE_NORMAL:
        new_mode = POWER_MODE_LOW_POWER;
        break;
    case POWER_MODE_LOW_POWER:
        new_mode = POWER_MODE_NORMAL;
        break;
    default:
        new_mode = POWER_MODE_NORMAL;
        break;
    }
    
    return power_manager_set_mode(new_mode);
}

int power_manager_request_sleep(uint32_t duration_ms)
{
    if (!manager_enabled) {
        return -ENODEV;
    }
    
    LOG_INF("Sleep requested for %d ms", duration_ms);
    
    set_power_mode_internal(POWER_MODE_SLEEP);
    
    /* Schedule wake-up if duration is specified */
    if (duration_ms > 0) {
        k_work_schedule(&power_monitor_work, K_MSEC(duration_ms));
    }
    
    return 0;
}

int power_manager_wake(void)
{
    if (current_mode == POWER_MODE_SLEEP || current_mode == POWER_MODE_DEEP_SLEEP) {
        stats.wake_events++;
        set_power_mode_internal(POWER_MODE_NORMAL);
        LOG_INF("System woken from sleep");
    }
    
    return 0;
}

int power_manager_get_stats(struct power_stats *stats_out)
{
    if (!stats_out) {
        return -EINVAL;
    }
    
    /* Update current statistics */
    update_power_stats();
    
    memcpy(stats_out, &stats, sizeof(*stats_out));
    return 0;
}

int power_manager_reset_stats(void)
{
    memset(&stats, 0, sizeof(stats));
    mode_start_time = k_uptime_get();
    last_update_time = mode_start_time;
    
    LOG_INF("Power statistics reset");
    return 0;
}

int power_manager_set_event_callback(power_event_cb_t callback)
{
    event_callback = callback;
    return 0;
}

float power_manager_get_battery_voltage(void)
{
    if (!config.enable_battery_monitoring) {
        return -1.0f;
    }
    
    return read_battery_voltage();
}

int power_manager_get_battery_level(void)
{
    float voltage = power_manager_get_battery_voltage();
    if (voltage < 0) {
        return -1;
    }
    
    return calculate_battery_level(voltage);
}

bool power_manager_is_battery_low(void)
{
    float voltage = power_manager_get_battery_voltage();
    return (voltage > 0 && voltage < config.low_battery_threshold_v);
}

int power_manager_enable(bool enable)
{
    manager_enabled = enable;
    
    if (!enable) {
        /* Cancel all work items */
        k_work_cancel_delayable(&power_monitor_work);
        k_work_cancel_delayable(&sleep_timeout_work);
    } else if (initialized) {
        /* Restart monitoring */
        k_work_schedule(&power_monitor_work, K_SECONDS(1));
        if (config.enable_auto_sleep) {
            k_work_schedule(&sleep_timeout_work, K_MSEC(config.idle_timeout_ms));
        }
    }
    
    LOG_INF("Power manager %s", enable ? "enabled" : "disabled");
    return 0;
}

void power_manager_system_reset(void)
{
    LOG_WRN("System reset requested");
    sys_reboot(SYS_REBOOT_COLD);
}

void power_manager_system_shutdown(void)
{
    LOG_WRN("System shutdown requested");
    
    /* Enter deep sleep mode */
    set_power_mode_internal(POWER_MODE_DEEP_SLEEP);
    
    /* Configure for minimal power consumption */
    nrf_power_system_off(NRF_POWER);
}