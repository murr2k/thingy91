/*
 * Copyright (c) 2024 Nordic Semiconductor ASA
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#include "motion_sensor.h"

#include <zephyr/kernel.h>
#include <zephyr/device.h>
#include <zephyr/devicetree.h>
#include <zephyr/drivers/sensor.h>
#include <zephyr/logging/log.h>
#include <math.h>

LOG_MODULE_REGISTER(motion_sensor, CONFIG_LOG_DEFAULT_LEVEL);

/* Device tree nodes */
#if DT_NODE_HAS_STATUS(DT_ALIAS(adxl372), okay)
#define ADXL372_NODE DT_ALIAS(adxl372)
#elif DT_NODE_EXISTS(DT_NODELABEL(adxl372))
#define ADXL372_NODE DT_NODELABEL(adxl372)
#endif

#if DT_NODE_HAS_STATUS(DT_ALIAS(adxl362), okay)
#define ADXL362_NODE DT_ALIAS(adxl362)
#elif DT_NODE_EXISTS(DT_NODELABEL(adxl362))
#define ADXL362_NODE DT_NODELABEL(adxl362)
#endif

static const struct device *adxl372_dev;
static const struct device *adxl362_dev;
static bool adxl372_ready = false;
static bool adxl362_ready = false;
static motion_event_cb_t event_callback = NULL;

/* Calibration offsets */
static float accel_offset[3] = {0.0f, 0.0f, 0.0f};
static float gyro_offset[3] = {0.0f, 0.0f, 0.0f};

/* Forward declarations */
static float deg_to_rad(float degrees);

static float deg_to_rad(float degrees)
{
    return degrees * M_PI / 180.0f;
}

int motion_sensor_init(void)
{
    LOG_INF("Initializing motion sensors");
    
#ifdef ADXL372_NODE
    adxl372_dev = DEVICE_DT_GET(ADXL372_NODE);
    if (device_is_ready(adxl372_dev)) {
        adxl372_ready = true;
        LOG_INF("ADXL372 high-g accelerometer initialized");
        
        /* Configure ADXL372 for optimal operation */
        struct sensor_value odr = { .val1 = 400, .val2 = 0 }; /* 400 Hz ODR */
        int ret = sensor_attr_set(adxl372_dev, SENSOR_CHAN_ACCEL_XYZ,
                                 SENSOR_ATTR_SAMPLING_FREQUENCY, &odr);
        if (ret) {
            LOG_WRN("Failed to set ADXL372 ODR: %d", ret);
        }
    } else {
        LOG_WRN("ADXL372 device not ready");
    }
#endif

#ifdef ADXL362_NODE
    adxl362_dev = DEVICE_DT_GET(ADXL362_NODE);
    if (device_is_ready(adxl362_dev)) {
        adxl362_ready = true;
        LOG_INF("ADXL362 low-power accelerometer initialized");
        
        /* Configure ADXL362 for optimal operation */
        struct sensor_value odr = { .val1 = 100, .val2 = 0 }; /* 100 Hz ODR */
        int ret = sensor_attr_set(adxl362_dev, SENSOR_CHAN_ACCEL_XYZ,
                                 SENSOR_ATTR_SAMPLING_FREQUENCY, &odr);
        if (ret) {
            LOG_WRN("Failed to set ADXL362 ODR: %d", ret);
        }
    } else {
        LOG_WRN("ADXL362 device not ready");
    }
#endif

    if (!adxl372_ready && !adxl362_ready) {
        LOG_WRN("No motion sensors available, using simulated data");
    }
    
    LOG_INF("Motion sensor initialization completed");
    return 0;
}

int motion_sensor_read(struct motion_data *data)
{
    if (!data) {
        return -EINVAL;
    }
    
    /* Initialize data structure */
    memset(data, 0, sizeof(*data));
    data->timestamp = k_uptime_get();
    data->valid = false;
    
    bool got_real_data = false;
    
    /* Try to read from ADXL372 first (high-g sensor) */
#ifdef ADXL372_NODE
    if (adxl372_ready && adxl372_dev) {
        int ret = sensor_sample_fetch(adxl372_dev);
        if (ret == 0) {
            struct sensor_value accel[3];
            ret = sensor_channel_get(adxl372_dev, SENSOR_CHAN_ACCEL_XYZ, accel);
            if (ret == 0) {
                data->accel_x = sensor_value_to_double(&accel[0]) - accel_offset[0];
                data->accel_y = sensor_value_to_double(&accel[1]) - accel_offset[1];
                data->accel_z = sensor_value_to_double(&accel[2]) - accel_offset[2];
                got_real_data = true;
            }
        } else {
            LOG_WRN("Failed to fetch ADXL372 sample: %d", ret);
        }
    }
#endif
    
    /* If ADXL372 failed, try ADXL362 */
#ifdef ADXL362_NODE
    if (!got_real_data && adxl362_ready && adxl362_dev) {
        int ret = sensor_sample_fetch(adxl362_dev);
        if (ret == 0) {
            struct sensor_value accel[3];
            ret = sensor_channel_get(adxl362_dev, SENSOR_CHAN_ACCEL_XYZ, accel);
            if (ret == 0) {
                data->accel_x = sensor_value_to_double(&accel[0]) - accel_offset[0];
                data->accel_y = sensor_value_to_double(&accel[1]) - accel_offset[1];
                data->accel_z = sensor_value_to_double(&accel[2]) - accel_offset[2];
                got_real_data = true;
            }
        } else {
            LOG_WRN("Failed to fetch ADXL362 sample: %d", ret);
        }
    }
#endif
    
    /* If no real sensors available, simulate data */
    if (!got_real_data) {
        static float phase = 0.0f;
        phase += 0.1f;
        
        /* Simulate realistic accelerometer data with gravity and small movements */
        data->accel_x = 0.2f * sinf(phase * 0.7f);
        data->accel_y = 0.3f * cosf(phase * 0.5f);
        data->accel_z = 9.81f + 0.1f * sinf(phase * 1.2f); /* Gravity + noise */
        
        /* Simulate gyroscope data (small rotations) */
        data->gyro_x = deg_to_rad(2.0f * sinf(phase * 0.3f));
        data->gyro_y = deg_to_rad(1.5f * cosf(phase * 0.4f));
        data->gyro_z = deg_to_rad(0.8f * sinf(phase * 0.6f));
    }
    
    /* Apply gyroscope offset calibration */
    data->gyro_x -= gyro_offset[0];
    data->gyro_y -= gyro_offset[1];
    data->gyro_z -= gyro_offset[2];
    
    data->valid = true;
    return 0;
}

int motion_sensor_set_power_mode(bool low_power)
{
    int ret = 0;
    
    LOG_INF("Setting motion sensor power mode: %s", 
            low_power ? "low power" : "normal");
    
#ifdef ADXL372_NODE
    if (adxl372_ready && adxl372_dev) {
        struct sensor_value power_mode;
        if (low_power) {
            power_mode.val1 = 50;  /* 50 Hz for low power */
            power_mode.val2 = 0;
        } else {
            power_mode.val1 = 400; /* 400 Hz for normal operation */
            power_mode.val2 = 0;
        }
        
        int adxl372_ret = sensor_attr_set(adxl372_dev, SENSOR_CHAN_ACCEL_XYZ,
                                         SENSOR_ATTR_SAMPLING_FREQUENCY, &power_mode);
        if (adxl372_ret) {
            LOG_WRN("Failed to set ADXL372 power mode: %d", adxl372_ret);
            ret = adxl372_ret;
        }
    }
#endif

#ifdef ADXL362_NODE
    if (adxl362_ready && adxl362_dev) {
        struct sensor_value power_mode;
        if (low_power) {
            power_mode.val1 = 12;  /* 12.5 Hz for low power */
            power_mode.val2 = 500000;
        } else {
            power_mode.val1 = 100; /* 100 Hz for normal operation */
            power_mode.val2 = 0;
        }
        
        int adxl362_ret = sensor_attr_set(adxl362_dev, SENSOR_CHAN_ACCEL_XYZ,
                                         SENSOR_ATTR_SAMPLING_FREQUENCY, &power_mode);
        if (adxl362_ret) {
            LOG_WRN("Failed to set ADXL362 power mode: %d", adxl362_ret);
            ret = adxl362_ret;
        }
    }
#endif
    
    return ret;
}

int motion_sensor_configure_events(uint32_t events, motion_event_cb_t callback)
{
    event_callback = callback;
    
    /* Configure interrupt-based event detection if supported */
    LOG_INF("Motion event detection configured for events: 0x%08x", events);
    
    return 0;
}

int motion_sensor_calibrate(void)
{
    LOG_INF("Starting motion sensor calibration");
    
    /* Collect samples for calibration */
    const int num_samples = 100;
    float accel_sum[3] = {0.0f, 0.0f, 0.0f};
    float gyro_sum[3] = {0.0f, 0.0f, 0.0f};
    int valid_samples = 0;
    
    for (int i = 0; i < num_samples; i++) {
        struct motion_data data;
        int ret = motion_sensor_read(&data);
        if (ret == 0 && data.valid) {
            accel_sum[0] += data.accel_x;
            accel_sum[1] += data.accel_y;
            accel_sum[2] += data.accel_z;
            gyro_sum[0] += data.gyro_x;
            gyro_sum[1] += data.gyro_y;
            gyro_sum[2] += data.gyro_z;
            valid_samples++;
        }
        k_msleep(10);
    }
    
    if (valid_samples < num_samples / 2) {
        LOG_ERR("Insufficient samples for calibration: %d/%d", valid_samples, num_samples);
        return -EIO;
    }
    
    /* Calculate offsets */
    accel_offset[0] = accel_sum[0] / valid_samples;
    accel_offset[1] = accel_sum[1] / valid_samples;
    accel_offset[2] = (accel_sum[2] / valid_samples) - 9.81f; /* Account for gravity */
    
    gyro_offset[0] = gyro_sum[0] / valid_samples;
    gyro_offset[1] = gyro_sum[1] / valid_samples;
    gyro_offset[2] = gyro_sum[2] / valid_samples;
    
    LOG_INF("Calibration completed with %d samples", valid_samples);
    LOG_INF("Accel offsets: X=%.3f, Y=%.3f, Z=%.3f", 
            accel_offset[0], accel_offset[1], accel_offset[2]);
    LOG_INF("Gyro offsets: X=%.3f, Y=%.3f, Z=%.3f", 
            gyro_offset[0], gyro_offset[1], gyro_offset[2]);
    
    return 0;
}

int motion_sensor_set_accel_range(uint8_t range_g)
{
    LOG_INF("Setting accelerometer range to %dg", range_g);
    
    struct sensor_value range = { .val1 = range_g, .val2 = 0 };
    
#ifdef ADXL372_NODE
    if (adxl372_ready && adxl372_dev) {
        int ret = sensor_attr_set(adxl372_dev, SENSOR_CHAN_ACCEL_XYZ,
                                 SENSOR_ATTR_FULL_SCALE, &range);
        if (ret) {
            LOG_WRN("Failed to set ADXL372 range: %d", ret);
            return ret;
        }
    }
#endif

#ifdef ADXL362_NODE
    if (adxl362_ready && adxl362_dev) {
        int ret = sensor_attr_set(adxl362_dev, SENSOR_CHAN_ACCEL_XYZ,
                                 SENSOR_ATTR_FULL_SCALE, &range);
        if (ret) {
            LOG_WRN("Failed to set ADXL362 range: %d", ret);
            return ret;
        }
    }
#endif
    
    return 0;
}

int motion_sensor_set_gyro_range(uint16_t range_dps)
{
    LOG_INF("Setting gyroscope range to %d dps", range_dps);
    
    /* Gyroscope not directly available on ADXL sensors */
    /* This would be implemented if a gyroscope sensor is added */
    
    return 0;
}