/*
 * Copyright (c) 2024 Nordic Semiconductor ASA
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#ifndef SENSOR_MANAGER_H_
#define SENSOR_MANAGER_H_

#include <zephyr/kernel.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief Sensor data structure
 */
struct sensor_data {
    /* Environmental sensors */
    float temperature;      /* Celsius */
    float humidity;         /* Percent */
    float pressure;         /* hPa */
    float gas_resistance;   /* Ohms */
    
    /* Motion sensors */
    float accel_x;          /* m/s² */
    float accel_y;          /* m/s² */
    float accel_z;          /* m/s² */
    float gyro_x;           /* rad/s */
    float gyro_y;           /* rad/s */
    float gyro_z;           /* rad/s */
    
    /* Metadata */
    uint64_t timestamp;     /* Timestamp in ms */
    uint8_t data_quality;   /* Quality indicator (0-100) */
    bool valid;             /* Data validity flag */
};

/**
 * @brief Sensor event callback function type
 */
typedef void (*sensor_event_cb_t)(const struct sensor_data *data);

/**
 * @brief Initialize the sensor manager
 * 
 * @return 0 on success, negative errno on failure
 */
int sensor_manager_init(void);

/**
 * @brief Read all sensor data
 * 
 * @param data Pointer to sensor data structure to fill
 * @return 0 on success, negative errno on failure
 */
int sensor_manager_read_all(struct sensor_data *data);

/**
 * @brief Start continuous sensor monitoring
 * 
 * @param interval_ms Sampling interval in milliseconds
 * @param callback Callback function for sensor events
 * @return 0 on success, negative errno on failure
 */
int sensor_manager_start_monitoring(uint32_t interval_ms, sensor_event_cb_t callback);

/**
 * @brief Stop continuous sensor monitoring
 * 
 * @return 0 on success, negative errno on failure
 */
int sensor_manager_stop_monitoring(void);

/**
 * @brief Set sensor power mode
 * 
 * @param low_power True to enable low power mode
 * @return 0 on success, negative errno on failure
 */
int sensor_manager_set_power_mode(bool low_power);

/**
 * @brief Get sensor status
 * 
 * @return Bitmask of available sensors
 */
uint32_t sensor_manager_get_status(void);

/**
 * @brief Calibrate sensors
 * 
 * @return 0 on success, negative errno on failure
 */
int sensor_manager_calibrate(void);

#ifdef __cplusplus
}
#endif

#endif /* SENSOR_MANAGER_H_ */