/*
 * Copyright (c) 2024 Nordic Semiconductor ASA
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#include "sensor_manager.h"
#include "environmental_sensor.h"
#include "motion_sensor.h"

#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>
#include <zephyr/sys/timeutil.h>

LOG_MODULE_REGISTER(sensor_manager, CONFIG_LOG_DEFAULT_LEVEL);

/* Sensor status flags */
#define SENSOR_STATUS_ENV_OK    BIT(0)
#define SENSOR_STATUS_MOTION_OK BIT(1)

static uint32_t sensor_status = 0;
static bool monitoring_active = false;
static sensor_event_cb_t event_callback = NULL;
static struct k_work_delayable monitoring_work;

/* Forward declarations */
static void monitoring_work_handler(struct k_work *work);
static uint64_t get_timestamp_ms(void);

static void monitoring_work_handler(struct k_work *work)
{
    struct sensor_data data;
    int ret;
    
    if (!monitoring_active || !event_callback) {
        return;
    }
    
    ret = sensor_manager_read_all(&data);
    if (ret == 0) {
        event_callback(&data);
    } else {
        LOG_WRN("Failed to read sensor data during monitoring: %d", ret);
    }
    
    /* Reschedule if monitoring is still active */
    if (monitoring_active) {
        k_work_reschedule(&monitoring_work, K_MSEC(CONFIG_THINGY91_DEMO_SENSOR_INTERVAL_MS));
    }
}

static uint64_t get_timestamp_ms(void)
{
    return k_uptime_get();
}

int sensor_manager_init(void)
{
    int ret;
    
    LOG_INF("Initializing sensor manager");
    
    /* Initialize environmental sensors */
    ret = environmental_sensor_init();
    if (ret == 0) {
        sensor_status |= SENSOR_STATUS_ENV_OK;
        LOG_INF("Environmental sensors initialized successfully");
    } else {
        LOG_WRN("Failed to initialize environmental sensors: %d", ret);
    }
    
    /* Initialize motion sensors */
    ret = motion_sensor_init();
    if (ret == 0) {
        sensor_status |= SENSOR_STATUS_MOTION_OK;
        LOG_INF("Motion sensors initialized successfully");
    } else {
        LOG_WRN("Failed to initialize motion sensors: %d", ret);
    }
    
    /* Initialize monitoring work */
    k_work_init_delayable(&monitoring_work, monitoring_work_handler);
    
    if (sensor_status == 0) {
        LOG_ERR("No sensors available");
        return -ENODEV;
    }
    
    LOG_INF("Sensor manager initialized with status: 0x%02x", sensor_status);
    return 0;
}

int sensor_manager_read_all(struct sensor_data *data)
{
    if (!data) {
        return -EINVAL;
    }
    
    /* Initialize data structure */
    memset(data, 0, sizeof(*data));
    data->timestamp = get_timestamp_ms();
    data->valid = false;
    data->data_quality = 0;
    
    /* Read environmental data */
    if (sensor_status & SENSOR_STATUS_ENV_OK) {
        struct environmental_data env_data;
        int ret = environmental_sensor_read(&env_data);
        if (ret == 0) {
            data->temperature = env_data.temperature;
            data->humidity = env_data.humidity;
            data->pressure = env_data.pressure;
            data->gas_resistance = env_data.gas_resistance;
            data->data_quality += 50;
            data->valid = true;
        } else {
            LOG_WRN("Failed to read environmental sensors: %d", ret);
        }
    }
    
    /* Read motion data */
    if (sensor_status & SENSOR_STATUS_MOTION_OK) {
        struct motion_data motion_data;
        int ret = motion_sensor_read(&motion_data);
        if (ret == 0) {
            data->accel_x = motion_data.accel_x;
            data->accel_y = motion_data.accel_y;
            data->accel_z = motion_data.accel_z;
            data->gyro_x = motion_data.gyro_x;
            data->gyro_y = motion_data.gyro_y;
            data->gyro_z = motion_data.gyro_z;
            data->data_quality += 50;
            data->valid = true;
        } else {
            LOG_WRN("Failed to read motion sensors: %d", ret);
        }
    }
    
    /* Clamp quality to 100 */
    if (data->data_quality > 100) {
        data->data_quality = 100;
    }
    
    return data->valid ? 0 : -EIO;
}

int sensor_manager_start_monitoring(uint32_t interval_ms, sensor_event_cb_t callback)
{
    if (!callback) {
        return -EINVAL;
    }
    
    if (monitoring_active) {
        sensor_manager_stop_monitoring();
    }
    
    event_callback = callback;
    monitoring_active = true;
    
    LOG_INF("Starting sensor monitoring with %d ms interval", interval_ms);
    k_work_schedule(&monitoring_work, K_MSEC(interval_ms));
    
    return 0;
}

int sensor_manager_stop_monitoring(void)
{
    if (!monitoring_active) {
        return 0;
    }
    
    monitoring_active = false;
    event_callback = NULL;
    k_work_cancel_delayable(&monitoring_work);
    
    LOG_INF("Sensor monitoring stopped");
    return 0;
}

int sensor_manager_set_power_mode(bool low_power)
{
    int ret = 0;
    
    LOG_INF("Setting sensor power mode: %s", low_power ? "low power" : "normal");
    
    if (sensor_status & SENSOR_STATUS_ENV_OK) {
        int env_ret = environmental_sensor_set_power_mode(low_power);
        if (env_ret != 0) {
            LOG_WRN("Failed to set environmental sensor power mode: %d", env_ret);
            ret = env_ret;
        }
    }
    
    if (sensor_status & SENSOR_STATUS_MOTION_OK) {
        int motion_ret = motion_sensor_set_power_mode(low_power);
        if (motion_ret != 0) {
            LOG_WRN("Failed to set motion sensor power mode: %d", motion_ret);
            ret = motion_ret;
        }
    }
    
    return ret;
}

uint32_t sensor_manager_get_status(void)
{
    return sensor_status;
}

int sensor_manager_calibrate(void)
{
    int ret = 0;
    
    LOG_INF("Starting sensor calibration");
    
    if (sensor_status & SENSOR_STATUS_MOTION_OK) {
        int motion_ret = motion_sensor_calibrate();
        if (motion_ret != 0) {
            LOG_WRN("Failed to calibrate motion sensors: %d", motion_ret);
            ret = motion_ret;
        }
    }
    
    LOG_INF("Sensor calibration completed with result: %d", ret);
    return ret;
}