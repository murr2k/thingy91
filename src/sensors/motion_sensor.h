/*
 * Copyright (c) 2024 Nordic Semiconductor ASA
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#ifndef MOTION_SENSOR_H_
#define MOTION_SENSOR_H_

#include <zephyr/kernel.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief Motion sensor data structure
 */
struct motion_data {
    /* Accelerometer data (m/s²) */
    float accel_x;
    float accel_y;
    float accel_z;
    
    /* Gyroscope data (rad/s) */
    float gyro_x;
    float gyro_y;
    float gyro_z;
    
    /* Metadata */
    uint64_t timestamp;     /* Timestamp in ms */
    bool valid;             /* Data validity flag */
};

/**
 * @brief Motion event types
 */
enum motion_event {
    MOTION_EVENT_NONE,
    MOTION_EVENT_TAP,
    MOTION_EVENT_DOUBLE_TAP,
    MOTION_EVENT_FREEFALL,
    MOTION_EVENT_ACTIVITY,
    MOTION_EVENT_INACTIVITY
};

/**
 * @brief Motion event callback function type
 */
typedef void (*motion_event_cb_t)(enum motion_event event);

/**
 * @brief Initialize motion sensors (ADXL372, ADXL362)
 * 
 * @return 0 on success, negative errno on failure
 */
int motion_sensor_init(void);

/**
 * @brief Read motion sensor data
 * 
 * @param data Pointer to motion data structure to fill
 * @return 0 on success, negative errno on failure
 */
int motion_sensor_read(struct motion_data *data);

/**
 * @brief Set motion sensor power mode
 * 
 * @param low_power True to enable low power mode
 * @return 0 on success, negative errno on failure
 */
int motion_sensor_set_power_mode(bool low_power);

/**
 * @brief Configure motion event detection
 * 
 * @param events Bitmask of events to enable
 * @param callback Callback function for motion events
 * @return 0 on success, negative errno on failure
 */
int motion_sensor_configure_events(uint32_t events, motion_event_cb_t callback);

/**
 * @brief Calibrate motion sensors
 * 
 * @return 0 on success, negative errno on failure
 */
int motion_sensor_calibrate(void);

/**
 * @brief Set accelerometer range
 * 
 * @param range_g Accelerometer range in g (2, 4, 8, 16)
 * @return 0 on success, negative errno on failure
 */
int motion_sensor_set_accel_range(uint8_t range_g);

/**
 * @brief Set gyroscope range
 * 
 * @param range_dps Gyroscope range in degrees per second
 * @return 0 on success, negative errno on failure
 */
int motion_sensor_set_gyro_range(uint16_t range_dps);

#ifdef __cplusplus
}
#endif

#endif /* MOTION_SENSOR_H_ */