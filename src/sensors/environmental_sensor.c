/*
 * Copyright (c) 2024 Nordic Semiconductor ASA
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#include "environmental_sensor.h"

#include <zephyr/kernel.h>
#include <zephyr/device.h>
#include <zephyr/devicetree.h>
#include <zephyr/drivers/sensor.h>
#include <zephyr/logging/log.h>

LOG_MODULE_REGISTER(environmental_sensor, CONFIG_LOG_DEFAULT_LEVEL);

#if DT_NODE_HAS_STATUS(DT_ALIAS(bme680), okay)
#define BME680_NODE DT_ALIAS(bme680)
#else
#define BME680_NODE DT_NODELABEL(bme680)
#endif

static const struct device *bme680_dev;
static bool sensor_ready = false;

int environmental_sensor_init(void)
{
    LOG_INF("Initializing BME680 environmental sensor");
    
#if DT_NODE_EXISTS(BME680_NODE)
    bme680_dev = DEVICE_DT_GET(BME680_NODE);
    
    if (!device_is_ready(bme680_dev)) {
        LOG_ERR("BME680 device not ready");
        return -ENODEV;
    }
    
    /* Configure the sensor for optimal performance */
    struct sensor_value osr_temp = { .val1 = 2, .val2 = 0 };    /* 2x oversampling */
    struct sensor_value osr_hum = { .val1 = 2, .val2 = 0 };     /* 2x oversampling */
    struct sensor_value osr_press = { .val1 = 4, .val2 = 0 };   /* 4x oversampling */
    
    int ret = sensor_attr_set(bme680_dev, SENSOR_CHAN_AMBIENT_TEMP,
                             SENSOR_ATTR_OVERSAMPLING, &osr_temp);
    if (ret) {
        LOG_WRN("Failed to set temperature oversampling: %d", ret);
    }
    
    ret = sensor_attr_set(bme680_dev, SENSOR_CHAN_HUMIDITY,
                         SENSOR_ATTR_OVERSAMPLING, &osr_hum);
    if (ret) {
        LOG_WRN("Failed to set humidity oversampling: %d", ret);
    }
    
    ret = sensor_attr_set(bme680_dev, SENSOR_CHAN_PRESS,
                         SENSOR_ATTR_OVERSAMPLING, &osr_press);
    if (ret) {
        LOG_WRN("Failed to set pressure oversampling: %d", ret);
    }
    
    sensor_ready = true;
    LOG_INF("BME680 environmental sensor initialized successfully");
    return 0;
#else
    LOG_WRN("BME680 device not found in device tree, using simulated data");
    sensor_ready = false;
    return 0;
#endif
}

int environmental_sensor_read(struct environmental_data *data)
{
    if (!data) {
        return -EINVAL;
    }
    
    /* Initialize data structure */
    memset(data, 0, sizeof(*data));
    data->timestamp = k_uptime_get();
    data->valid = false;
    
#if DT_NODE_EXISTS(BME680_NODE)
    if (!sensor_ready || !bme680_dev) {
        goto simulate_data;
    }
    
    /* Trigger sensor sample */
    int ret = sensor_sample_fetch(bme680_dev);
    if (ret) {
        LOG_ERR("Failed to fetch sensor sample: %d", ret);
        goto simulate_data;
    }
    
    /* Read temperature */
    struct sensor_value temp_val;
    ret = sensor_channel_get(bme680_dev, SENSOR_CHAN_AMBIENT_TEMP, &temp_val);
    if (ret == 0) {
        data->temperature = sensor_value_to_double(&temp_val);
    } else {
        LOG_WRN("Failed to read temperature: %d", ret);
    }
    
    /* Read humidity */
    struct sensor_value hum_val;
    ret = sensor_channel_get(bme680_dev, SENSOR_CHAN_HUMIDITY, &hum_val);
    if (ret == 0) {
        data->humidity = sensor_value_to_double(&hum_val);
    } else {
        LOG_WRN("Failed to read humidity: %d", ret);
    }
    
    /* Read pressure */
    struct sensor_value press_val;
    ret = sensor_channel_get(bme680_dev, SENSOR_CHAN_PRESS, &press_val);
    if (ret == 0) {
        data->pressure = sensor_value_to_double(&press_val) / 100.0; /* Convert Pa to hPa */
    } else {
        LOG_WRN("Failed to read pressure: %d", ret);
    }
    
    /* Read gas resistance */
    struct sensor_value gas_val;
    ret = sensor_channel_get(bme680_dev, SENSOR_CHAN_GAS_RES, &gas_val);
    if (ret == 0) {
        data->gas_resistance = sensor_value_to_double(&gas_val);
    } else {
        LOG_DBG("Gas resistance not available: %d", ret);
        data->gas_resistance = 0.0;
    }
    
    data->valid = true;
    return 0;
    
simulate_data:
#endif
    /* Simulate environmental data for demo purposes */
    static float base_temp = 22.5f;
    static float base_humidity = 45.0f;
    static float base_pressure = 1013.25f;
    
    /* Add some variation to make it realistic */
    int32_t random_val = k_uptime_get() % 1000;
    
    data->temperature = base_temp + (float)(random_val % 50 - 25) / 10.0f;
    data->humidity = base_humidity + (float)(random_val % 30 - 15) / 5.0f;
    data->pressure = base_pressure + (float)(random_val % 20 - 10) / 10.0f;
    data->gas_resistance = 50000.0f + (float)(random_val % 10000);
    
    /* Ensure realistic ranges */
    if (data->humidity < 0) data->humidity = 0;
    if (data->humidity > 100) data->humidity = 100;
    if (data->pressure < 900) data->pressure = 900;
    if (data->pressure > 1100) data->pressure = 1100;
    
    data->valid = true;
    return 0;
}

int environmental_sensor_set_power_mode(bool low_power)
{
#if DT_NODE_EXISTS(BME680_NODE)
    if (!sensor_ready || !bme680_dev) {
        return 0; /* No-op for simulated sensors */
    }
    
    /* BME680 power mode configuration */
    struct sensor_value power_mode;
    if (low_power) {
        power_mode.val1 = 1; /* Force mode for single shot measurements */
        power_mode.val2 = 0;
    } else {
        power_mode.val1 = 3; /* Normal mode for continuous measurements */
        power_mode.val2 = 0;
    }
    
    int ret = sensor_attr_set(bme680_dev, SENSOR_CHAN_ALL,
                             SENSOR_ATTR_SAMPLING_FREQUENCY, &power_mode);
    if (ret) {
        LOG_WRN("Failed to set power mode: %d", ret);
        return ret;
    }
#endif
    
    LOG_INF("Environmental sensor power mode set to %s", 
            low_power ? "low power" : "normal");
    return 0;
}

int environmental_sensor_configure(uint8_t temp_oversample, 
                                  uint8_t humidity_oversample,
                                  uint8_t pressure_oversample)
{
#if DT_NODE_EXISTS(BME680_NODE)
    if (!sensor_ready || !bme680_dev) {
        return -ENODEV;
    }
    
    struct sensor_value osr_temp = { .val1 = temp_oversample, .val2 = 0 };
    struct sensor_value osr_hum = { .val1 = humidity_oversample, .val2 = 0 };
    struct sensor_value osr_press = { .val1 = pressure_oversample, .val2 = 0 };
    
    int ret = sensor_attr_set(bme680_dev, SENSOR_CHAN_AMBIENT_TEMP,
                             SENSOR_ATTR_OVERSAMPLING, &osr_temp);
    if (ret) {
        return ret;
    }
    
    ret = sensor_attr_set(bme680_dev, SENSOR_CHAN_HUMIDITY,
                         SENSOR_ATTR_OVERSAMPLING, &osr_hum);
    if (ret) {
        return ret;
    }
    
    ret = sensor_attr_set(bme680_dev, SENSOR_CHAN_PRESS,
                         SENSOR_ATTR_OVERSAMPLING, &osr_press);
    if (ret) {
        return ret;
    }
#endif
    
    LOG_INF("Environmental sensor configured: temp=%d, hum=%d, press=%d",
            temp_oversample, humidity_oversample, pressure_oversample);
    return 0;
}