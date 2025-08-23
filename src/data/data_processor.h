/*
 * Copyright (c) 2024 Nordic Semiconductor ASA
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#ifndef DATA_PROCESSOR_H_
#define DATA_PROCESSOR_H_

#include <zephyr/kernel.h>
#include <stdint.h>
#include "sensors/sensor_manager.h"

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief Data processing statistics
 */
struct data_stats {
    uint32_t total_samples;
    uint32_t processed_samples;
    uint32_t buffered_samples;
    uint32_t transmitted_samples;
    uint32_t dropped_samples;
    uint32_t buffer_full_count;
    float avg_processing_time_ms;
    float avg_transmission_time_ms;
};

/**
 * @brief Data filter configuration
 */
struct data_filter_config {
    bool enable_smoothing;
    uint8_t smoothing_factor;    /* 1-10, higher = more smoothing */
    bool enable_outlier_detection;
    float outlier_threshold;     /* Standard deviations */
    bool enable_delta_compression;
    float delta_threshold;       /* Minimum change to trigger update */
};

/**
 * @brief Initialize data processor
 * 
 * @return 0 on success, negative errno on failure
 */
int data_processor_init(void);

/**
 * @brief Process raw sensor data
 * 
 * @param raw_data Raw sensor data from sensor manager
 * @param processed_data Processed sensor data output
 * @return 0 on success, negative errno on failure
 */
int data_processor_process(const struct sensor_data *raw_data, 
                          struct sensor_data *processed_data);

/**
 * @brief Format sensor data as JSON
 * 
 * @param data Sensor data to format
 * @param json_buffer Output JSON buffer
 * @param buffer_size Size of JSON buffer
 * @return Length of JSON string on success, negative errno on failure
 */
int data_processor_format_json(const struct sensor_data *data, 
                              char *json_buffer, size_t buffer_size);

/**
 * @brief Format sensor data as binary
 * 
 * @param data Sensor data to format
 * @param binary_buffer Output binary buffer
 * @param buffer_size Size of binary buffer
 * @return Length of binary data on success, negative errno on failure
 */
int data_processor_format_binary(const struct sensor_data *data,
                                uint8_t *binary_buffer, size_t buffer_size);

/**
 * @brief Buffer processed data for later transmission
 * 
 * @param json_data JSON data to buffer
 * @return 0 on success, negative errno on failure
 */
int data_processor_buffer_data(const char *json_data);

/**
 * @brief Get next buffered data entry
 * 
 * @param json_buffer Output buffer for JSON data
 * @param buffer_size Size of output buffer
 * @return Length of data on success, 0 if no data, negative errno on failure
 */
int data_processor_get_buffered_data(char *json_buffer, size_t buffer_size);

/**
 * @brief Clear all buffered data
 * 
 * @return Number of entries cleared
 */
int data_processor_clear_buffer(void);

/**
 * @brief Get data processing statistics
 * 
 * @param stats Pointer to statistics structure to fill
 * @return 0 on success, negative errno on failure
 */
int data_processor_get_stats(struct data_stats *stats);

/**
 * @brief Configure data filtering
 * 
 * @param config Filter configuration
 * @return 0 on success, negative errno on failure
 */
int data_processor_configure_filter(const struct data_filter_config *config);

/**
 * @brief Reset data processing statistics
 * 
 * @return 0 on success, negative errno on failure
 */
int data_processor_reset_stats(void);

/**
 * @brief Compress data for efficient transmission
 * 
 * @param input Input data buffer
 * @param input_len Length of input data
 * @param output Output compressed buffer
 * @param output_size Size of output buffer
 * @return Length of compressed data on success, negative errno on failure
 */
int data_processor_compress(const uint8_t *input, size_t input_len,
                           uint8_t *output, size_t output_size);

/**
 * @brief Decompress received data
 * 
 * @param input Compressed input data
 * @param input_len Length of compressed data
 * @param output Output decompressed buffer
 * @param output_size Size of output buffer
 * @return Length of decompressed data on success, negative errno on failure
 */
int data_processor_decompress(const uint8_t *input, size_t input_len,
                             uint8_t *output, size_t output_size);

#ifdef __cplusplus
}
#endif

#endif /* DATA_PROCESSOR_H_ */