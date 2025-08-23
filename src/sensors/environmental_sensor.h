/*
 * Copyright (c) 2024 Nordic Semiconductor ASA
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#ifndef ENVIRONMENTAL_SENSOR_H_
#define ENVIRONMENTAL_SENSOR_H_

#include <zephyr/kernel.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief Environmental sensor data structure
 */
struct environmental_data {
    float temperature;      /* Temperature in Celsius */
    float humidity;         /* Relative humidity in % */
    float pressure;         /* Atmospheric pressure in hPa */
    float gas_resistance;   /* Gas resistance in Ohms */
    uint64_t timestamp;     /* Timestamp in ms */
    bool valid;             /* Data validity flag */
};

/**
 * @brief Initialize environmental sensors (BME680)
 * 
 * @return 0 on success, negative errno on failure
 */
int environmental_sensor_init(void);

/**
 * @brief Read environmental sensor data
 * 
 * @param data Pointer to environmental data structure to fill
 * @return 0 on success, negative errno on failure
 */
int environmental_sensor_read(struct environmental_data *data);

/**
 * @brief Set environmental sensor power mode
 * 
 * @param low_power True to enable low power mode
 * @return 0 on success, negative errno on failure
 */
int environmental_sensor_set_power_mode(bool low_power);

/**
 * @brief Configure environmental sensor sampling
 * 
 * @param temp_oversample Temperature oversampling factor
 * @param humidity_oversample Humidity oversampling factor
 * @param pressure_oversample Pressure oversampling factor
 * @return 0 on success, negative errno on failure
 */
int environmental_sensor_configure(uint8_t temp_oversample, 
                                  uint8_t humidity_oversample,
                                  uint8_t pressure_oversample);

#ifdef __cplusplus
}
#endif

#endif /* ENVIRONMENTAL_SENSOR_H_ */